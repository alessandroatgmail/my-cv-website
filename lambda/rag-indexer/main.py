"""
RAG Indexer Cloud Function — BM25 version
------------------
Triggered by: HTTP request (manual or via CI/CD pipeline)
Purpose:      Read all .txt documents from Cloud Storage, split them into
              chunks and save the BM25 index back to Cloud Storage.

Environment variables:
  BUCKET_NAME  — name of your Cloud Storage bucket
  DOCS_PREFIX  — folder with source docs  (default: "knowledge-base/docs/")
  INDEX_KEY    — output file path in bucket (default: "knowledge-base/index.json")

Migration notes (AWS → GCP):
  - boto3 s3 client         → google-cloud-storage Client
  - s3.get_paginator()      → bucket.list_blobs(prefix=...)
  - s3.get_object()         → blob.download_as_text()
  - s3.put_object()         → blob.upload_from_string()
  - lambda_handler()        → HTTP Cloud Function with functions_framework
"""

import json
import os
import re
import functions_framework
from google.cloud import storage

# ── GCP client ────────────────────────────────────────────────────────────────
# Initialized outside the handler so it is reused across warm invocations.
storage_client = storage.Client()

# ── Configuration ─────────────────────────────────────────────────────────────
BUCKET_NAME   = os.environ["BUCKET_NAME"]
DOCS_PREFIX   = os.environ.get("DOCS_PREFIX", "knowledge-base/docs/")
INDEX_KEY     = os.environ.get("INDEX_KEY",   "knowledge-base/index.json")
CHUNK_SIZE    = 200   # target words per chunk
CHUNK_OVERLAP = 30    # words shared between consecutive chunks


# ── Helper: tokenize text into lowercase words ────────────────────────────────
def tokenize(text: str) -> list[str]:
    """
    Converts text to a list of lowercase words, removing punctuation.
    BM25 works on tokens — consistent tokenization ensures accurate matching.
    """
    return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())


# ── Helper: split text into overlapping chunks ────────────────────────────────
def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Splits a long text into chunks of `size` words with `overlap` word overlap.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += size - overlap
    return chunks


# ── Helper: compute BM25 term frequencies for a chunk ────────────────────────
def compute_term_freq(tokens: list[str]) -> dict[str, int]:
    """
    Counts how many times each token appears in the chunk.
    This is the term frequency (TF) component of BM25.
    """
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    return tf


# ── Helper: load all .txt files from Cloud Storage ───────────────────────────
def load_documents() -> list[dict]:
    """
    Lists all .txt blobs under DOCS_PREFIX and downloads their content.
    Equivalent to the S3 paginator + get_object pattern.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=DOCS_PREFIX)

    docs = []
    for blob in blobs:
        if not blob.name.endswith(".txt"):
            continue
        text = blob.download_as_text(encoding="utf-8")
        docs.append({
            "source": blob.name.split("/")[-1],
            "text":   text,
        })
    return docs


# ── Main handler ──────────────────────────────────────────────────────────────
@functions_framework.http
def rag_indexer(request):
    """
    HTTP Cloud Function entry point.
    1. Load all documents from Cloud Storage
    2. Chunk each document
    3. Tokenize each chunk and compute term frequencies
    4. Save the index as JSON back to Cloud Storage

    CORS headers are included so this function can also be triggered
    directly from a browser if needed.
    """
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return ("", 204, headers)

    print("Starting BM25 indexing...")

    documents = load_documents()
    if not documents:
        print("No .txt documents found in", DOCS_PREFIX)
        return ({"message": "No documents to index."}, 200, headers)

    all_chunks = []

    for doc in documents:
        print(f"Processing: {doc['source']}")
        chunks = split_into_chunks(doc["text"])

        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.split()) < 10:
                continue

            tokens = tokenize(chunk_text)
            tf     = compute_term_freq(tokens)

            all_chunks.append({
                "id":     f"{doc['source']}_{i}",
                "source": doc["source"],
                "text":   chunk_text,
                "tokens": tokens,
                "tf":     tf,
                "length": len(tokens),
            })
            print(f"  Chunk {i}: {len(tokens)} tokens ✓")

    avg_length = sum(c["length"] for c in all_chunks) / len(all_chunks) if all_chunks else 0

    index = {
        "total_chunks": len(all_chunks),
        "avg_length":   avg_length,
        "chunks":       all_chunks,
    }

    # Upload the index JSON to Cloud Storage
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(INDEX_KEY)
    blob.upload_from_string(
        data=json.dumps(index),
        content_type="application/json",
    )

    msg = f"Indexed {len(all_chunks)} chunks from {len(documents)} documents."
    print(msg)
    return ({"message": msg}, 200, headers)