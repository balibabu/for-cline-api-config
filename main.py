# app.py
from flask import Flask, request, jsonify, Response
from providers.gemini_provider import GeminiProvider

app = Flask(__name__)

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Returns a dummy list of models to satisfy Cline's initial connection check."""
    return jsonify({
        "object": "list",
        "data": [
            {"id": "gemini-2.5-flash", "object": "model", "created": 1686935002, "owned_by": "google"},
            {"id": "gemini-2.5-pro", "object": "model", "created": 1686935002, "owned_by": "google"},
            {"id": "gemma-4-31b-it", "object": "model", "created": 1686935002, "owned_by": "google"}
        ]
    })

def get_provider(model_name: str, api_key: str):
    """Plug-and-play factory for model providers."""
    model_lower = model_name.lower()
    
    if "gemini" in model_lower:
        return GeminiProvider(api_key)
    # In the future:
    # elif "claude" in model_lower:
    #     return ClaudeProvider(api_key)
    
    # Fallback default
    return GeminiProvider(api_key)

@app.route('/v1/chat/completions', methods=['POST'])
def completions():
    # 1. Extract the API Key that Cline sends
    auth_header = request.headers.get('Authorization', '')
    api_key = auth_header.replace('Bearer ', '').strip()
    
    if not api_key:
        return jsonify({"error": "No API key provided"}), 401

    # 2. Parse the request payload
    data = request.json.copy() if request.json else {}
    # Use .pop() to remove these keys so they aren't passed twice via **data
    model = data.pop('model', 'gemini-2.5-flash')
    messages = data.pop('messages', [])
    stream = data.pop('stream', False)

    # 3. Instantiate the correct class dynamically
    provider = get_provider(model, api_key)

    # 4. Route to streaming or standard completion
    if stream:
        return Response(
            provider.stream_completion(messages, model, **data),
            mimetype='text/event-stream'
        )
    return jsonify(provider.chat_completion(messages, model, **data))

if __name__ == '__main__':
    app.run(port=5000, debug=True)