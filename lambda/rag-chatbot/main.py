"""
RAG Chatbot Cloud Function — BM25 + Gemini 2.0 Flash version
------------------
Triggered by: HTTP POST request from the CV website
Purpose:      Given a user question, find the most relevant chunks using
              BM25 scoring, then ask Gemini 2.0 Flash to answer using
              only that context.

Environment variables:
  BUCKET_NAME  — Cloud Storage bucket name
  INDEX_KEY    — path to index.json  (default: "knowledge-base/index.json")
  TOP_K        — number of chunks to retrieve  (default: 3)
  OWNER_NAME   — your name, used in the system prompt
  GCP_PROJECT  — your GCP project ID
  GCP_REGION   — Vertex AI region (default: "europe-west8")


"""

import json
import os
import re
import math
import time
import functions_framework
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part

# ── GCP clients ───────────────────────────────────────────────────────────────
# Initialized outside the handler so they are reused across warm invocations.
storage_client = storage.Client()

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_REGION  = os.environ.get("GCP_REGION", "europe-west8")

# Initialize Vertex AI once at module level
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

# ── Configuration ─────────────────────────────────────────────────────────────
BUCKET_NAME = os.environ["BUCKET_NAME"]
INDEX_KEY   = os.environ.get("INDEX_KEY",   "knowledge-base/index.json")
TOP_K       = int(os.environ.get("TOP_K",   "3"))
OWNER_NAME  = os.environ.get("OWNER_NAME",  "Alessandro Silvestrin")
MODEL_ID    = os.environ.get("MODEL_ID",    "gemini-2.0-flash-001")

# BM25 hyperparameters — standard values that work well in most cases
BM25_K1 = 1.5   # term frequency saturation
BM25_B  = 0.75  # length normalization

# In-memory cache for the index — persists across warm invocations
_index_cache = None

# ── Per-IP rate limiting ───────────────────────────────────────────────────────
# Stored per container instance (best-effort for a personal site).
# Limit: 10 requests per IP per 60 seconds.
_rate_limit_window = 60       # seconds
_rate_limit_max    = 10       # requests per window
_rate_store: dict[str, list[float]] = {}

# ── Input limits ──────────────────────────────────────────────────────────────
MAX_MESSAGES    = 20    # max entries in the history array
MAX_MSG_LENGTH  = 1000  # max chars per message
VALID_ROLES     = {"user", "assistant"}


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - _rate_limit_window
    timestamps = [t for t in _rate_store.get(ip, []) if t > window_start]
    if len(timestamps) >= _rate_limit_max:
        _rate_store[ip] = timestamps
        return True
    timestamps.append(now)
    _rate_store[ip] = timestamps
    return False

# CORS headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type":                 "application/json",
}


# ── Helper: tokenize query ────────────────────────────────────────────────────
def tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())


# ── Helper: load index from Cloud Storage ────────────────────────────────────
def load_index() -> dict:
    """
    Downloads and caches the BM25 index from Cloud Storage.
    The cache persists for the lifetime of the container instance,
    avoiding repeated downloads on warm invocations.
    """
    global _index_cache
    if _index_cache is None:
        print("Loading index from Cloud Storage...")
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(INDEX_KEY)
        _index_cache = json.loads(blob.download_as_text())
        print(f"Index loaded: {_index_cache['total_chunks']} chunks")
    return _index_cache


# ── Helper: BM25 scoring ──────────────────────────────────────────────────────
def bm25_score(query_tokens: list[str], chunk: dict, index: dict) -> float:
    """
    Computes the BM25 relevance score between a query and a chunk.
    Logic is identical to the AWS version — BM25 is pure Python,
    no cloud-specific dependencies.
    """
    score      = 0.0
    n_chunks   = index["total_chunks"]
    avg_length = index["avg_length"]
    chunk_len  = chunk["length"]
    tf_map     = chunk["tf"]

    for token in set(query_tokens):
        if token not in tf_map:
            continue

        df  = sum(1 for c in index["chunks"] if token in c["tf"])
        idf = math.log((n_chunks - df + 0.5) / (df + 0.5) + 1)

        tf          = tf_map[token]
        numerator   = tf * (BM25_K1 + 1)
        denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * chunk_len / avg_length)

        score += idf * (numerator / denominator)

    return score


# ── Helper: translate query to English for BM25 retrieval ────────────────────
def translate_to_english(text: str, lang: str) -> str:
    """
    Translates the user query to English before BM25 retrieval.
    BM25 is a lexical algorithm — it matches exact tokens. Since all
    source documents are in English, non-English queries score 0.000
    against every chunk. Translating the query first ensures correct matching.
    If the query is already in English, Gemini returns it unchanged.
    Uses a fast, cheap call with max_output_tokens=100.
    """
    if lang == "en":
        return text

    model = GenerativeModel(model_name=MODEL_ID)
    response = model.generate_content(
        f"Translate this text to English. Return only the translation, nothing else:\n\n{text}",
        generation_config={"max_output_tokens": 256, "temperature": 0.0},
    )
    translated = response.text.strip()
    print(f"  Query translated: '{text}' → '{translated}'")
    return translated


# ── Helper: retrieve top-K chunks ────────────────────────────────────────────
def retrieve_top_chunks(question: str, index: dict) -> list[dict]:
    query_tokens = tokenize(question)
    scored = []
    for chunk in index["chunks"]:
        score = bm25_score(query_tokens, chunk, index)
        scored.append({
            "text":   chunk["text"],
            "source": chunk["source"],
            "score":  score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:TOP_K]
    for c in top:
        print(f"  Retrieved [{c['source']}] score={c['score']:.3f}")
    return top


# ── Helper: call Gemini 2.0 Flash on Vertex AI ───────────────────────────────
def generate_answer(question: str, context_chunks: list[dict], history: list[dict], lang: str) -> str:
    """
    Builds a prompt with context and conversation history,
    then calls Gemini 2.0 Flash via Vertex AI.

    Migration note: Bedrock used a raw JSON body with a custom Llama prompt
    format. Vertex AI GenerativeModel accepts structured Content objects
    with roles (user/model) — equivalent to Llama's user/assistant roles.
    The system prompt is passed separately via system_instruction.
    """
    context_text = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
    )

    lang_instruction = "Rispondi in italiano." if lang == "it" else "Reply in English."

    system_prompt = f"""You are Silvio, a helpful AI assistant for {OWNER_NAME}'s personal CV website.
Answer visitors' questions about {OWNER_NAME}'s background, skills, experience, and projects.

RULES:
1. Answer ONLY using the CONTEXT below.
2. If the answer is not in the context, say: "I don't have that information, but you can contact {OWNER_NAME} at alessandro.silvestrin.as@gmail.com"
3. Be concise, friendly and professional. Keep answers under 150 words.
4. Never invent information not present in the context.
5. Refer to {OWNER_NAME} in third person.
6. If asked for more details, expand but stay under 250 words.
7. {lang_instruction}

CONTEXT:
{context_text}"""

    # Convert conversation history to Vertex AI Content objects.
    # Bedrock used "assistant" as the role name — Vertex AI uses "model".
    vertex_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        vertex_history.append(
            Content(role=role, parts=[Part.from_text(msg["content"])])
        )

    model = GenerativeModel(
        model_name=MODEL_ID,
        system_instruction=system_prompt,
    )

    # Start a chat session with the conversation history
    chat = model.start_chat(history=vertex_history)

    response = chat.send_message(
        question,
        generation_config={
            "max_output_tokens": 512,
            "temperature":       0.3,
        },
    )

    return response.text.strip()


# ── Main handler ──────────────────────────────────────────────────────────────
@functions_framework.http
def rag_chatbot(request):
    """
    HTTP Cloud Function entry point.

    Migration note: on Lambda the request body arrived as event["body"]
    (a JSON string to parse manually). On Cloud Functions the request
    is a standard Flask Request object — use request.get_json() directly.
    """
    if request.method == "OPTIONS":
        return ("", 204, CORS_HEADERS)

    # ── Rate limiting ──────────────────────────────────────────────────────────
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if is_rate_limited(client_ip):
        return (
            json.dumps({"error": "Too many requests. Please wait a moment."}),
            429,
            CORS_HEADERS,
        )

    try:
        body     = request.get_json(silent=True) or {}
        messages = body.get("messages", [])
        lang     = body.get("lang", "en")

        # ── Input validation ───────────────────────────────────────────────────
        if not isinstance(messages, list):
            return (json.dumps({"error": "Invalid request."}), 400, CORS_HEADERS)

        if len(messages) > MAX_MESSAGES:
            return (json.dumps({"error": "Too many messages in history."}), 400, CORS_HEADERS)

        for msg in messages:
            if not isinstance(msg, dict):
                return (json.dumps({"error": "Invalid message format."}), 400, CORS_HEADERS)
            if msg.get("role") not in VALID_ROLES:
                return (json.dumps({"error": "Invalid message role."}), 400, CORS_HEADERS)
            if not isinstance(msg.get("content", ""), str) or len(msg["content"]) > MAX_MSG_LENGTH:
                return (json.dumps({"error": "Message too long."}), 400, CORS_HEADERS)

        if not messages or messages[-1]["role"] != "user":
            return (
                json.dumps({"error": "Last message must be from the user."}),
                400,
                CORS_HEADERS,
            )

        current_question = messages[-1]["content"]
        history          = messages[:-1]

        print(f"Question ({lang}): {current_question}")

        # Step 1: load index from Cloud Storage
        index = load_index()

        # Step 2: translate query to English for BM25 retrieval.
        # Source documents are in English — Italian queries score 0.000
        # against every chunk without this step.
        retrieval_query = translate_to_english(current_question, lang)

        # Step 3: BM25 retrieval using the translated query
        top_chunks = retrieve_top_chunks(retrieval_query, index)

        # Step 3: generate answer with Gemini
        answer = generate_answer(current_question, top_chunks, history, lang)

        print(f"Answer generated ({len(answer)} chars)")
        return (
            json.dumps({"reply": answer}),
            200,
            CORS_HEADERS,
        )

    except Exception as e:
        print(f"ERROR: {e}")
        return (
            json.dumps({"error": "Internal server error."}),
            500,
            CORS_HEADERS,
        )