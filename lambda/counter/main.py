import time
import functions_framework
from google.cloud import firestore

# Initialize the Firestore client outside the function handler.
# This way it is reused across multiple invocations (warm starts),
# avoiding the overhead of creating a new connection every time.
db = firestore.Client()

# ── Per-IP rate limiting ───────────────────────────────────────────────────────
# Allows max 1 counter increment per IP per hour (per container instance).
_rate_limit_window = 3600  # 1 hour in seconds
_rate_store: dict[str, float] = {}


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    last_seen = _rate_store.get(ip, 0)
    if now - last_seen < _rate_limit_window:
        return True
    _rate_store[ip] = now
    return False


@functions_framework.http
def visit_counter(request):
    """
    HTTP Cloud Function that increments a visit counter in Firestore
    and returns the updated count.

    Args:
        request: The HTTP request object provided by the Functions Framework.

    Returns:
        A tuple of (response_body, status_code, headers).
    """
    # CORS headers allow the browser to call this function
    # from a different origin (your CV website domain).
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    # OPTIONS is a preflight request sent automatically by the browser
    # before the actual request — we just return 204 No Content.
    if request.method == "OPTIONS":
        return ("", 204, headers)

    # ── Rate limiting: one increment per IP per hour ───────────────────────────
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    doc_ref = db.collection("stats").document("visit_counter")
    if is_rate_limited(client_ip):
        # Return current count without incrementing
        doc = doc_ref.get()
        count = doc.to_dict().get("count", 0) if doc.exists else 0
        return ({"count": count}, 200, headers)

    # INCREMENT operation — Firestore's atomic increment ensures
    # that concurrent requests don't overwrite each other's counts.
    # This is equivalent to DynamoDB's ADD UpdateExpression.
    doc_ref.update({"count": firestore.Increment(1)})

    # Read the updated document to return the current count.
    doc = doc_ref.get()
    count = doc.to_dict().get("count", 0)

    return ({"count": count}, 200, headers)
