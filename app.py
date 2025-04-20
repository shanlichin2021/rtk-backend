import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from pipeline import create_payload, model_req
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)

# Always send CORS headers on OPTIONS and actual requests
CORS(
    app,
    origins=os.getenv("ALLOWED_ORIGINS", "*"),
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)

@app.before_request
def validate_id_token():
    # Let preflight go through
    if request.method == "OPTIONS":
        return

    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        abort(401, description="Missing or malformed Authorization header")

    token = auth.split(" ", 1)[1]

    # Hard‑coded fallback audience (your Cloud Run URL)
    expected_aud = os.getenv(
        "VITE_CLOUD_RUN_AUDIENCE",
        "https://rtk-backend-1054015385247.us-central1.run.app"
    )

    try:
        # Verify the Google ID token against the expected audience
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=expected_aud,
        )
        # (Optionally: store id_info in flask.g if you need user info)
    except ValueError:
        abort(401, description="Invalid ID token")

@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    history    = data.get("history", [])
    message    = data.get("message", "")
    model_name = data.get("modelName", "llava:latest")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Reconstruct dialogue context
    context     = "\n".join(f"{m['sender']}: {m['text']}" for m in history)
    full_prompt = f"{context}\nuser: {message}"

    # Talk to the model
    payload, result = None, None
    payload = create_payload(model=model_name,
                             prompt=full_prompt,
                             target="open-webui")
    delta, result = model_req(payload=payload)

    if delta < 0:
        return jsonify({"error": result}), 500

    return jsonify({"reply": result})

# Entry point for local dev; Cloud Run uses $PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
