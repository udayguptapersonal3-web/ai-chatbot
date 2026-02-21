import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Free-tier API Keys ──────────────────────────────────────────────────
    # Google Gemini  → FREE tier available at https://aistudio.google.com/app/apikey
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # Groq  → 100 % FREE at https://console.groq.com/  (LLaMA-3, Mixtral, Gemma …)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    # HuggingFace Inference API  → FREE tier at https://huggingface.co/settings/tokens
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

    # ── Paid-tier API Keys (optional, leave blank if unused) ────────────────
    OPENAI_API_KEY    = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

    # ── Flask settings ──────────────────────────────────────────────────────
    SECRET_KEY         = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024          # 16 MB max upload
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif'}


class ModelConfig:
    # ── Groq (FREE) ─────────────────────────────────────────────────────────
    GROQ_LLAMA3_70B   = "llama3-70b-8192"
    GROQ_LLAMA3_8B    = "llama3-8b-8192"
    GROQ_MIXTRAL      = "mixtral-8x7b-32768"
    GROQ_GEMMA2_9B    = "gemma2-9b-it"

    # ── Google Gemini (FREE tier) ────────────────────────────────────────────
    GEMINI_FLASH      = "gemini-1.5-flash"
    GEMINI_PRO        = "gemini-1.5-pro"
    GEMINI_FLASH_LITE = "gemini-2.0-flash-lite"

    # ── OpenAI (paid, optional) ─────────────────────────────────────────────
    GPT_4O            = "gpt-4o"
    GPT_4_TURBO       = "gpt-4-turbo-preview"
    GPT_3_5_TURBO     = "gpt-3.5-turbo"

    # ── Anthropic (paid, optional) ──────────────────────────────────────────
    CLAUDE_3_OPUS     = "claude-3-opus-20240229"
    CLAUDE_3_SONNET   = "claude-3-sonnet-20240229"

    DEFAULT_MODEL = GROQ_LLAMA3_70B
