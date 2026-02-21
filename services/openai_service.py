"""
OpenAI Service (paid – optional)
Requires an OpenAI API key: https://platform.openai.com/api-keys
"""
import requests
from config import Config

OPENAI_MODELS = [
    {"id": "gpt-4o",               "name": "GPT-4o (Best)"},
    {"id": "gpt-4-turbo-preview",  "name": "GPT-4 Turbo"},
    {"id": "gpt-3.5-turbo",        "name": "GPT-3.5 Turbo (Cheapest)"},
]

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.OPENAI_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_available_models(self):
        return OPENAI_MODELS

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call(self, messages, model, temperature, max_tokens=4096):
        if not self.is_configured():
            return {"success": False, "error": "OpenAI API key not configured. Add it in ⚙️ Settings."}
        payload = {"model": model or "gpt-4o", "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        try:
            r = requests.post(OPENAI_API_URL, headers=self._headers(), json=payload, timeout=60)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            return {"success": True, "response": content, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"OpenAI error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat(self, message, system_prompt="", model="", temperature=0.7):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        return self._call(messages, model or "gpt-4o", temperature)

    def chat_with_history(self, history, system_prompt="", model="", temperature=0.7):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        return self._call(messages, model or "gpt-4o", temperature)

    def code_assist(self, code, task="explain", language="python", model=""):
        task_prompts = {
            "explain": f"Explain this {language} code:\n\n```{language}\n{code}\n```",
            "debug":   f"Find and fix bugs:\n\n```{language}\n{code}\n```",
            "generate":f"Generate {language} code for:\n\n{code}",
            "review":  f"Review this {language} code:\n\n```{language}\n{code}\n```",
        }
        return self.chat(task_prompts.get(task, task_prompts["explain"]),
                         f"You are an expert {language} developer.", model or "gpt-4o", 0.3)
