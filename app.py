import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import create_payload, model_req   # project‑local helpers

app = Flask(__name__)

# Allow requests from your GitHub‑Pages domain in prod; fall back to * for local dev
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*"))

# ──────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    history    = data.get("history", [])
    message    = data.get("message", "")
    model_name = data.get("modelName", "llava:latest")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Re‑create the dialogue context for the model
    context = "\n".join(f"{m['sender']}: {m['text']}" for m in history)
    full_prompt = f"{context}\nuser: {message}"

    # Talk to the external model endpoint
    payload        = create_payload(model=model_name,
                                    prompt=full_prompt,
                                    target="open-webui")
    delta, result  = model_req(payload=payload)

    if delta < 0:
        return jsonify({"error": result}), 500

    return jsonify({"reply": result})

# ──────────────────────────────────────────────────────────────────────
# Entry‑point  (Cloud Run listens on $PORT and 0.0.0.0)
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
