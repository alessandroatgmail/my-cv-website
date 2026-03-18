"""
RAG Indexer Lambda
------------------
Triggered by: S3 ObjectCreated / ObjectRemoved events on knowledge-base/docs/
Purpose:      Read all .txt documents, split them into chunks, generate
              embeddings via Bedrock Titan, and save the index to S3.

Environment variables (set in Lambda console):
  BUCKET_NAME  — name of your S3 bucket  (e.g. "cv-alessandro-silvestrin")
  DOCS_PREFIX  — folder with source docs  (default: "knowledge-base/docs/")
  INDEX_KEY    — output file path in S3   (default: "knowledge-base/index.json")
"""

import json
import os
import boto3

# ── AWS clients ───────────────────────────────────────────────────────────────
s3      = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "eu-central-1"))

# ── Configuration (from environment variables) ────────────────────────────────
BUCKET_NAME   = os.environ["BUCKET_NAME"]
DOCS_PREFIX   = os.environ.get("DOCS_PREFIX", "knowledge-base/docs/")
INDEX_KEY     = os.environ.get("INDEX_KEY",   "knowledge-base/index.json")
CHUNK_SIZE    = 200   # target words per chunk
CHUNK_OVERLAP = 30    # words shared between consecutive chunks


# ── Helper: split text into overlapping word chunks ───────────────────────────
def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Splits a long text into chunks of `size` words with `overlap` word overlap.
    Overlap ensures sentences near chunk boundaries are represented in both
    adjacent chunks, preventing important context from being lost.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        # Move forward by (size - overlap) so the next chunk re-includes
        # the last `overlap` words of the current chunk
        start += size - overlap
    return chunks


# ── Helper: call Bedrock Titan Embeddings to get a float vector ───────────────
def get_embedding(text: str) -> list[float]:
    """
    Sends text to Amazon Titan Text Embeddings V2 and returns a list of floats.
    The model returns a 1024-dimensional vector encoding the semantic
    meaning of the input text.
    """
    body = json.dumps({
        "inputText": text,
        "dimensions": 1024,   # vector size — keep consistent across all calls
        "normalize":  True,   # normalize to unit length (needed for cosine similarity)
    })
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["embedding"]   # list of 1024 floats


# ── Helper: load all .txt files from S3 docs folder ──────────────────────────
def load_documents() -> list[dict]:
    """
    Lists all .txt objects under DOCS_PREFIX in S3, downloads each one,
    and returns a list of { source, text } dicts.
    """
    docs = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=DOCS_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # Skip folder placeholder objects and non-.txt files
            if not key.endswith(".txt"):
                continue
            body = s3.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
            docs.append({
                "source": key.split("/")[-1],   # e.g. "bio.txt"
                "text":   body.decode("utf-8"),
            })
    return docs


# ── Main handler ──────────────────────────────────────────────────────────────
def lambda_handler(event, context):
    """
    Entry point called by AWS Lambda.
    1. Load all documents from S3
    2. Chunk each document
    3. Generate an embedding for every chunk
    4. Save the full index as JSON back to S3
    """
    print("Starting RAG indexing...")

    documents = load_documents()
    if not documents:
        print("No .txt documents found in", DOCS_PREFIX)
        return {"statusCode": 200, "body": "No documents to index."}

    all_chunks = []

    for doc in documents:
        print(f"Processing: {doc['source']}")
        chunks = split_into_chunks(doc["text"])

        for i, chunk_text in enumerate(chunks):
            # Skip chunks that are too short to be meaningful
            if len(chunk_text.split()) < 10:
                continue

            embedding = get_embedding(chunk_text)

            all_chunks.append({
                "id":        f"{doc['source']}_{i}",   # unique identifier
                "source":    doc["source"],              # which file it came from
                "text":      chunk_text,                 # raw text (returned to LLM)
                "embedding": embedding,                  # 1024-dim float vector
            })
            print(f"  Chunk {i}: {len(chunk_text.split())} words → embedded ✓")

    # Build the final index object
    index = {
        "total_chunks":  len(all_chunks),
        "embedding_dim": 1024,
        "chunks":        all_chunks,
    }

    # Save the index to S3 as a JSON file
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=INDEX_KEY,
        Body=json.dumps(index),
        ContentType="application/json",
    )

    print(f"Index saved: {len(all_chunks)} chunks → s3://{BUCKET_NAME}/{INDEX_KEY}")
    return {
        "statusCode": 200,
        "body": f"Indexed {len(all_chunks)} chunks from {len(documents)} documents.",
    }