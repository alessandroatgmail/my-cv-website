"""
RAG Chatbot Lambda
------------------
Triggered by: API Gateway POST /chat
Purpose:      Given a user question and conversation history, find the most
              relevant chunks from the knowledge base index, then ask Claude
              Haiku to answer using only that context.

Environment variables:
  BUCKET_NAME      — S3 bucket name
  INDEX_KEY        — path to index.json  (default: "knowledge-base/index.json")
  TOP_K            — number of chunks to retrieve  (default: 3)
  OWNER_NAME       — your name, used in the system prompt
"""

import json
import os
import math
import boto3

# ── AWS clients ───────────────────────────────────────────────────────────────
s3      = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "eu-central-1"))

# ── Configuration ─────────────────────────────────────────────────────────────
BUCKET_NAME = os.environ["BUCKET_NAME"]
INDEX_KEY   = os.environ.get("INDEX_KEY",   "knowledge-base/index.json")
TOP_K       = int(os.environ.get("TOP_K",   "3"))
OWNER_NAME  = os.environ.get("OWNER_NAME",  "Alessandro Silvestrin")

# Cache the index in Lambda memory between warm invocations.
# Lambda instances are reused for subsequent calls ("warm start"),
# so caching avoids repeated S3 reads and speeds up responses.
_index_cache = None


# ── Helper: cosine similarity between two float vectors ──────────────────────
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Computes the cosine similarity between two vectors.
    Since Titan normalizes vectors to unit length, this reduces
    to a simple dot product.
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


# ── Helper: load index from S3 (with in-memory cache) ────────────────────────
def load_index() -> dict:
    global _index_cache
    if _index_cache is None:
        print("Loading index from S3 (cold start or cache miss)...")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=INDEX_KEY)
        _index_cache = json.loads(obj["Body"].read())
        print(f"Index loaded: {_index_cache['total_chunks']} chunks")
    return _index_cache


# ── Helper: embed the user's question ────────────────────────────────────────
def embed_query(text: str) -> list[float]:
    """Converts the user question into a vector using Titan Embeddings."""
    body = json.dumps({
        "inputText": text,
        "dimensions": 1024,
        "normalize":  True,
    })
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    return json.loads(response["body"].read())["embedding"]


# ── Helper: retrieve the top-K most relevant chunks ──────────────────────────
def retrieve_top_chunks(query_embedding: list[float], index: dict) -> list[dict]:
    """
    Scores every chunk by cosine similarity to the query embedding,
    then returns the top-K chunks sorted by descending relevance score.
    """
    scored = []
    for chunk in index["chunks"]:
        score = cosine_similarity(query_embedding, chunk["embedding"])
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


# ── Helper: build the prompt and call Claude Haiku ───────────────────────────
def generate_answer(question: str, context_chunks: list[dict], history: list[dict], lang: str) -> str:
    """
    Builds a prompt with the retrieved context chunks and conversation
    history, then calls Claude Haiku to generate an answer.
    The lang parameter instructs Claude to reply in the correct language.
    """
    context_text = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
    )

    # Instruct Claude to reply in the same language as the user
    lang_instruction = "Reply in Italian." if lang == "it" else "Reply in English."

    system_prompt = f"""You are Silvio, a helpful AI assistant for {OWNER_NAME}'s personal CV website.
Your job is to answer visitors' questions about {OWNER_NAME}'s background, skills, experience, and projects.

IMPORTANT RULES:
1. Answer ONLY using the information provided in the CONTEXT section below.
2. If the answer is not in the context, say: "I don't have that information, but you can contact {OWNER_NAME} directly at alessandro.silvestrin.as@gmail.com"
3. Be concise, friendly, and professional.
4. Never invent or assume information not present in the context.
5. Refer to {OWNER_NAME} in third person (e.g. "He has experience in...").
6. {lang_instruction}

CONTEXT:
{context_text}
"""

    messages = history + [{"role": "user", "content": question}]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "system":     system_prompt,
        "messages":   messages,
    })

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


# ── CORS headers ──────────────────────────────────────────────────────────────
CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type":                 "application/json",
}


# ── Main handler ──────────────────────────────────────────────────────────────
def lambda_handler(event, context):
    """
    Expected request body:
    {
      "messages": [
        {"role": "user",      "content": "What stack do you use?"},
        {"role": "assistant", "content": "Alessandro mainly uses Python..."},
        {"role": "user",      "content": "And for frontend?"}
      ],
      "lang": "en"   optional, defaults to "en"
    }
    The last message must always be role=user.
    """
    # Handle CORS preflight
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        body     = json.loads(event.get("body", "{}"))
        messages = body.get("messages", [])
        lang     = body.get("lang", "en")   # language passed from frontend

        if not messages or messages[-1]["role"] != "user":
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Last message must be from the user."}),
            }

        current_question = messages[-1]["content"]
        history          = messages[:-1]

        print(f"Question ({lang}): {current_question}")

        # Step 1: embed the question
        query_embedding = embed_query(current_question)

        # Step 2: load the index (cached after first call)
        index = load_index()

        # Step 3: find the most relevant chunks
        top_chunks = retrieve_top_chunks(query_embedding, index)

        # Step 4: generate the answer with Claude Haiku
        answer = generate_answer(current_question, top_chunks, history, lang)

        print(f"Answer generated ({len(answer)} chars)")
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"reply": answer}),
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Internal server error."}),
        }