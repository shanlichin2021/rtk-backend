import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import create_payload, model_req

app = Flask(__name__)

# Enable CORS for your GH‑Pages origin (or * if you prefer)
CORS(
    app,
    origins=os.getenv("ALLOWED_ORIGINS", "https://shanlichin2021.github.io"),
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)

@app.route("/api/chat", methods=["OPTIONS", "POST"])
def chat():
    # OPTIONS automatically returns 200 with CORS headers
    if request.method == "OPTIONS":
        return "", 204

    data       = request.get_json() or {}
    history    = data.get("history", [])
    message    = data.get("message", "")
    model_name = data.get("modelName", "llava:latest")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Reconstruct conversation
    context     = "\n".join(f"{m['sender']}: {m['text']}" for m in history)
    full_prompt = f"{context}\nuser: {message}"

    # Call your GenAI pipeline
    payload = create_payload(model=model_name, prompt=full_prompt, target="open-webui")
    delta, result = model_req(payload=payload)

    if delta < 0:
        return jsonify({"error": result}), 500

    return jsonify({"reply": result})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
