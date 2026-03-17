"""
View Counter Lambda
-------------------
Triggered by: API Gateway POST /counter
Purpose:      Increment the page view counter in DynamoDB
              and return the updated count to the browser.

Environment variables (set in Lambda console):
  TABLE_NAME — DynamoDB table name (e.g. "cv-view-counter")
"""

import json
import os
import boto3

# ── AWS client ────────────────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ.get("TABLE_NAME", "cv-view-counter"))

# ── CORS headers — required for browser-to-API calls ─────────────────────────
# These headers tell the browser it is allowed to call this API
# from a different domain (e.g. your CloudFront URL calling API Gateway)
CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",   # restrict to your domain in production
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type":                 "application/json",
}


def lambda_handler(event, context):
    """
    Entry point called by AWS Lambda.

    DynamoDB UpdateItem with ADD action:
    - If the item exists: atomically adds 1 to count
    - If the item does not exist: creates it with count = 1
    - Atomic operation: safe even with many concurrent visitors
    """

    # Handle CORS preflight — browsers send OPTIONS before the real POST
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        response = table.update_item(
            Key={"id": "pageviews"},   # the single item we created manually
            # ADD atomically increments a Number attribute
            # If the attribute does not exist yet, ADD creates it starting from 0
            UpdateExpression="ADD #c :inc",
            ExpressionAttributeNames={"#c": "count"},   # alias because "count" is a reserved word
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",   # return the new value after the update
        )

        # Extract the updated count from the response
        new_count = int(response["Attributes"]["count"])

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"count": new_count}),
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Could not update counter."}),
        }