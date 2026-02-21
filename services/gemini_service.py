"""
Google Gemini Service – FREE tier available
Models: gemini-1.5-flash (free), gemini-1.5-pro (free limited), gemini-2.0-flash-lite
Sign up at: https://aistudio.google.com/app/apikey
"""
import requests
from config import Config

GEMINI_MODELS = [
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite (Fastest) – FREE"},
    {"id": "gemini-1.5-flash",      "name": "Gemini 1.5 Flash – FREE"},
    {"id": "gemini-1.5-pro",        "name": "Gemini 1.5 Pro – FREE (limited)"},
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GEMINI_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_available_models(self):
        return GEMINI_MODELS

    def _call(self, parts: list, model: str, temperature: float, system_prompt: str = ""):
        if not self.is_configured():
            return {
                "success": False,
                "error": "Gemini API key not configured. Get a FREE key at https://aistudio.google.com/app/apikey",
            }
        url = BASE_URL.format(model=model or "gemini-1.5-flash")
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            resp = requests.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"success": True, "response": text, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Gemini API error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat(self, message: str, system_prompt: str = "", model: str = "", temperature: float = 0.7):
        return self._call([{"text": message}], model or "gemini-1.5-flash", temperature, system_prompt)

    def chat_with_history(self, history: list, system_prompt: str = "",
                          model: str = "", temperature: float = 0.7):
        # Build multi-turn contents list
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        if not self.is_configured():
            return {
                "success": False,
                "error": "Gemini API key not configured.",
            }
        url = BASE_URL.format(model=model or "gemini-1.5-flash")
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 8192},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        try:
            resp = requests.post(url, params={"key": self.api_key}, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"success": True, "response": text, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Gemini API error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def code_assist(self, code: str, task: str = "explain", language: str = "python",
                    model: str = ""):
        task_prompts = {
            "explain": f"Explain this {language} code in detail:\n\n```{language}\n{code}\n```",
            "debug":   f"Find and fix bugs in this {language} code:\n\n```{language}\n{code}\n```\n\nProvide corrected code with explanations.",
            "generate":f"Generate {language} code for:\n\n{code}",
            "review":  f"Review this {language} code for quality, security and best practices:\n\n```{language}\n{code}\n```",
        }
        prompt = task_prompts.get(task, task_prompts["explain"])
        sys_p  = f"You are an expert {language} developer."
        return self.chat(prompt, sys_p, model or "gemini-1.5-flash", 0.3)
