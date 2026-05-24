# Cline OpenAI Router 🔄

A lightweight, local Flask proxy that translates OpenAI-compatible API requests into native Google Gemini API calls. 

This bridge allows you to use the latest, most powerful Gemini models (like `gemma 4` or `gemini-3.5-flash`) directly inside [Cline](https://github.com/cline/cline) using your own API key. By bypassing the built-in free-tier gateways, you avoid rate limits and context caps while retaining full autonomous coding capabilities.

## 🚀 Features

*   **100% OpenAI Compatible:** Acts as a drop-in local server for Cline (or any tool expecting the OpenAI API format).
*   **Full Tool Calling Support:** Perfectly translates OpenAI tool schemas to Gemini Function Declarations. This allows Cline to read files, write code, and execute terminal commands autonomously.
*   **Stream Zipping:** Automatically solves the notorious Gemini `500 INTERNAL` error by intelligently zipping consecutive user/tool messages to enforce Google's strict "User -> Model -> User" conversation pattern.
*   **Plug-and-Play Architecture:** Built using the Factory Pattern. You can easily add support for other providers (like Claude or DeepSeek) in the future without rewriting the core routing logic.

## 📋 Prerequisites

*   Python 3.8+
*   A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)
*   The [Cline VS Code Extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)

## 🛠️ Installation & Setup

1. **Clone the repository:**
```bash
   git clone https://github.com/balibabu/openai-compatible-bridge.git
   cd openai-compatible-bridge
```

2. **Install the required dependencies:**

```bash
   pip install flask google-genai
```

3. **Start the local proxy:**

```bash
   python main.py
```

*The server will start running on `http://127.0.0.1:5000`*

## 🔌 Connecting to Cline

Once the Flask server is running, open your VS Code and configure Cline:

1. Click the **Settings (⚙️)** icon in the Cline panel.
2. **API Provider:** Select `OpenAI Compatible`
3. **Base URL:** Enter `http://127.0.0.1:5000/v1` *(The `/v1` is required)*
4. **API Key:** Paste your real Google Gemini API Key.
5. **Model:** Check "Use custom model" and type the exact Gemini model ID you want to use (e.g., `gemini-2.5-flash` or `gemini-3.5-flash`).

You're done! Cline will now communicate with your local proxy, which will handle all the complex translations to Google's backend.

## 🏗️ Adding New Models (Future Proofing)

The proxy uses an abstract `BaseProvider` class. If you want to add a new AI provider in the future:

1. Create a new file (e.g., `claude_provider.py`) in the `providers/` directory that inherits from `BaseProvider`.
2. Implement the `chat_completion` and `stream_completion` methods.
3. Add a simple `elif` statement to the `get_provider()` factory function in `main.py` to route requests to your new class.

## 📄 License

MIT — do whatever you want with it.