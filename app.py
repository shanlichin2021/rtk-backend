from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import create_payload, model_req  # Use functions from pipeline.py

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    history = data.get("history", [])
    message = data.get("message", "")
    model_name = data.get("modelName", "llava:latest")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Combine chat history and the current message into a full prompt
    context = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in history])
    full_prompt = f"{context}\nuser: {message}"

    # Create the payload using the pipeline functions (target is set to open-webui)
    payload = create_payload(model=model_name, prompt=full_prompt, target="open-webui")
    delta, result = model_req(payload=payload)
    
    if delta < 0:
        return jsonify({"error": result}), 500
    
    return jsonify({"reply": result})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

