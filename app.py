"""
Unified AI Chatbot – Main Flask Application
Providers: Groq (FREE), Gemini (FREE), HuggingFace (FREE), OpenAI (paid), Anthropic (paid)
Image: Pollinations.ai (FREE) + DALL-E (paid)
"""
from flask import Flask, render_template, request, jsonify, session
from config import Config
from services import (
    GroqService, GeminiService, OpenAIService,
    AnthropicService, ImageService, HuggingFaceService,
)
import os

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# ── Service singletons ─────────────────────────────────────────────────────
groq_service        = GroqService()
gemini_service      = GeminiService()
openai_service      = OpenAIService()
anthropic_service   = AnthropicService()
image_service       = ImageService()
huggingface_service = HuggingFaceService()

# Per-session conversation history (keyed by session id)
_histories: dict = {}


# ── Helpers ────────────────────────────────────────────────────────────────
def _payload():
    return request.get_json(silent=True) or {}


def _parse_temperature(raw, default=0.7):
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(v, 2.0))


def _get_history():
    sid = session.get("sid")
    if not sid:
        import uuid
        sid = str(uuid.uuid4())
        session["sid"] = sid
    return _histories.setdefault(sid, [])


def _clear_history():
    sid = session.get("sid", "")
    if sid in _histories:
        _histories[sid] = []


# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/providers", methods=["GET"])
def get_providers():
    """Return all providers with availability status."""
    providers = []

    # FREE providers first
    providers.append({
        "id": "groq", "name": "Groq – LLaMA/Mixtral", "tier": "free",
        "configured": groq_service.is_configured(),
        "models": groq_service.get_available_models(),
    })
    providers.append({
        "id": "gemini", "name": "Google Gemini", "tier": "free",
        "configured": gemini_service.is_configured(),
        "models": gemini_service.get_available_models(),
    })
    providers.append({
        "id": "huggingface", "name": "HuggingFace Inference", "tier": "free",
        "configured": huggingface_service.is_configured(),
        "models": huggingface_service.get_available_models(),
    })
    # Image (always available via Pollinations)
    providers.append({
        "id": "image", "name": "Image Generation", "tier": "free",
        "configured": True,
        "models": image_service.get_available_models(),
    })
    # Paid optional
    providers.append({
        "id": "openai", "name": "OpenAI – ChatGPT", "tier": "paid",
        "configured": openai_service.is_configured(),
        "models": openai_service.get_available_models(),
    })
    providers.append({
        "id": "anthropic", "name": "Anthropic – Claude", "tier": "paid",
        "configured": anthropic_service.is_configured(),
        "models": anthropic_service.get_available_models(),
    })

    return jsonify(providers)


@app.route("/api/chat", methods=["POST"])
def chat():
    data        = _payload()
    message     = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Message is required"})

    provider      = data.get("provider", "groq")
    model         = data.get("model", "")
    system_prompt = data.get("system_prompt", "")
    temperature   = _parse_temperature(data.get("temperature", 0.7))
    use_history   = data.get("use_history", True)

    history = _get_history() if use_history else []
    history.append({"role": "user", "content": message})

    if provider == "groq":
        response = groq_service.chat_with_history(history, system_prompt, model, temperature)
    elif provider == "gemini":
        response = gemini_service.chat_with_history(history, system_prompt, model, temperature)
    elif provider == "openai":
        response = openai_service.chat_with_history(history, system_prompt, model, temperature)
    elif provider == "anthropic":
        response = anthropic_service.chat_with_history(history, system_prompt, model, temperature)
    elif provider == "huggingface":
        response = huggingface_service.chat(message, system_prompt, model, temperature)
    else:
        response = {"error": f"Unknown provider: {provider}"}

    if response.get("success"):
        history.append({"role": "assistant", "content": response["response"]})

    return jsonify(response)


@app.route("/api/code", methods=["POST"])
def code_assist():
    data     = _payload()
    code     = str(data.get("code", "")).strip()
    if not code:
        return jsonify({"error": "Code input is required"})

    task     = data.get("task", "explain")
    language = data.get("language", "python")
    provider = data.get("provider", "groq")
    model    = data.get("model", "")

    if provider == "groq":
        response = groq_service.code_assist(code, task, language, model)
    elif provider == "gemini":
        response = gemini_service.code_assist(code, task, language, model)
    elif provider == "openai":
        response = openai_service.code_assist(code, task, language, model)
    elif provider == "anthropic":
        response = anthropic_service.code_assist(code, task, language, model)
    elif provider == "huggingface":
        response = huggingface_service.code_assist(code, task, language, model)
    else:
        response = {"error": f"Unknown provider: {provider}"}

    return jsonify(response)


@app.route("/api/image", methods=["POST"])
def generate_image():
    data    = _payload()
    prompt  = str(data.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"})

    model   = data.get("model", "pollinations")
    size    = data.get("size", "1024x1024")
    quality = data.get("quality", "standard")

    response = image_service.generate_image(prompt, model, size, quality)
    return jsonify(response)


@app.route("/api/clear", methods=["POST"])
def clear_history():
    _clear_history()
    return jsonify({"success": True, "message": "Conversation cleared"})


@app.route("/api/configure", methods=["POST"])
def configure_api():
    """Allow runtime API-key injection from the UI."""
    global groq_service, gemini_service, openai_service, anthropic_service
    global image_service, huggingface_service

    data = _payload()

    if data.get("groq_key"):
        groq_service = GroqService(data["groq_key"])
    if data.get("gemini_key"):
        gemini_service = GeminiService(data["gemini_key"])
    if data.get("openai_key"):
        openai_service = OpenAIService(data["openai_key"])
        image_service  = ImageService(data["openai_key"])
    if data.get("anthropic_key"):
        anthropic_service = AnthropicService(data["anthropic_key"])
    if data.get("huggingface_key"):
        huggingface_service = HuggingFaceService(data["huggingface_key"])

    return jsonify({"success": True, "message": "API keys updated successfully!"})


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify(_get_history())


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)

    print("=" * 55)
    print("  Unified AI Chatbot  –  http://localhost:5000")
    print("=" * 55)
    print("  FREE providers:")
    print("    Groq   → https://console.groq.com/")
    print("    Gemini → https://aistudio.google.com/app/apikey")
    print("    HuggingFace → https://huggingface.co/settings/tokens")
    print("    Images → Pollinations.ai (no key needed!)")
    print("=" * 55)

    app.run(debug=True, port=5000, host="0.0.0.0")
