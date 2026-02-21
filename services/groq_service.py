"""
Groq Service – 100% FREE tier
Supports: LLaMA-3 70B/8B, Mixtral-8x7B, Gemma2-9B
Sign up at: https://console.groq.com/
"""
import requests
from config import Config


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODELS = [
    {"id": "llama3-70b-8192",    "name": "LLaMA-3 70B (Fast & Smart) – FREE"},
    {"id": "llama3-8b-8192",     "name": "LLaMA-3 8B (Fastest) – FREE"},
    {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B 32K context – FREE"},
    {"id": "gemma2-9b-it",       "name": "Gemma2 9B (Google) – FREE"},
]


class GroqService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GROQ_API_KEY

    # ── helpers ────────────────────────────────────────────────────────────
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_available_models(self):
        return GROQ_MODELS

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _call(self, messages, model: str, temperature: float, max_tokens: int = 4096):
        if not self.is_configured():
            return {
                "success": False,
                "error": "Groq API key not configured. Get a FREE key at https://console.groq.com/",
            }
        payload = {
            "model": model or "llama3-70b-8192",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(GROQ_API_URL, headers=self._headers(), json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"success": True, "response": content, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Groq API error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── public methods ─────────────────────────────────────────────────────
    def chat(self, message: str, system_prompt: str = "", model: str = "", temperature: float = 0.7):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        return self._call(messages, model or "llama3-70b-8192", temperature)

    def chat_with_history(self, history: list, system_prompt: str = "",
                          model: str = "", temperature: float = 0.7):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        return self._call(messages, model or "llama3-70b-8192", temperature)

    def code_assist(self, code: str, task: str = "explain", language: str = "python",
                    model: str = ""):
        task_prompts = {
            "explain": f"Explain this {language} code in detail:\n\n```{language}\n{code}\n```",
            "debug":   f"Find and fix bugs in this {language} code:\n\n```{language}\n{code}\n```\n\nProvide the corrected code with explanations.",
            "generate":f"Generate {language} code for:\n\n{code}\n\nProvide clean, well-commented code.",
            "review":  f"Review this {language} code for quality, security, and best practices:\n\n```{language}\n{code}\n```",
        }
        prompt = task_prompts.get(task, task_prompts["explain"])
        sys_prompt = f"You are an expert {language} developer. Provide clear, accurate, and helpful code assistance."
        return self.chat(prompt, sys_prompt, model or "llama3-70b-8192", 0.3)
