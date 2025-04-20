import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from pipeline import create_payload, model_req
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)

# ─── CORS ───────────────────────────────────────────────────────────────
# Always reply with these headers (preflight & actual)
CORS(
    app,
    origins=os.getenv("ALLOWED_ORIGINS", "*"),
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)

# ─── Token Validation ────────────────────────────────────────────────────
@app.before_request
def validate_id_token():
    # Let OPTIONS through so CORS can happen
    if request.method == "OPTIONS":
        return

    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        abort(401, description="Missing or malformed Authorization header")

    token = auth.split(" ", 1)[1]
    try:
        # Verify the Google ID token
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=os.getenv("VITE_CLOUD_RUN_AUDIENCE"),
        )
        # Optionally: store id_info in flask.g if you need user info
    except ValueError:
        abort(401, description="Invalid ID token")

# ─── Your Chat Endpoint ─────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    history    = data.get("history", [])
    message    = data.get("message", "")
    model_name = data.get("modelName", "llava:latest")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    context     = "\n".join(f"{m['sender']}: {m['text']}" for m in history)
    full_prompt = f"{context}\nuser: {message}"

    payload, result = None, None
    payload = create_payload(model=model_name,
                             prompt=full_prompt,
                             target="open-webui")
    delta, result = model_req(payload=payload)

    if delta < 0:
        return jsonify({"error": result}), 500

    return jsonify({"reply": result})

# ─── Entrypoint ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
