"""
Anthropic Claude Service (paid – optional)
Requires an Anthropic API key: https://console.anthropic.com/
"""
import requests
from config import Config

ANTHROPIC_MODELS = [
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Best)"},
    {"id": "claude-3-opus-20240229",     "name": "Claude 3 Opus"},
    {"id": "claude-3-haiku-20240307",    "name": "Claude 3 Haiku (Fastest)"},
]

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_available_models(self):
        return ANTHROPIC_MODELS

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _call(self, messages, system_prompt, model, temperature, max_tokens=4096):
        if not self.is_configured():
            return {"success": False, "error": "Anthropic API key not configured. Add it in ⚙️ Settings."}
        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            r = requests.post(ANTHROPIC_API_URL, headers=self._headers(), json=payload, timeout=60)
            r.raise_for_status()
            content = r.json()["content"][0]["text"]
            return {"success": True, "response": content, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Anthropic error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat(self, message, system_prompt="", model="", temperature=0.7):
        return self._call([{"role": "user", "content": message}],
                          system_prompt, model or "claude-3-5-sonnet-20241022", temperature)

    def chat_with_history(self, history, system_prompt="", model="", temperature=0.7):
        return self._call(history, system_prompt,
                          model or "claude-3-5-sonnet-20241022", temperature)

    def code_assist(self, code, task="explain", language="python", model=""):
        task_prompts = {
            "explain": f"Explain this {language} code:\n\n```{language}\n{code}\n```",
            "debug":   f"Find and fix bugs:\n\n```{language}\n{code}\n```",
            "generate":f"Generate {language} code for:\n\n{code}",
            "review":  f"Review this {language} code:\n\n```{language}\n{code}\n```",
        }
        return self.chat(task_prompts.get(task, task_prompts["explain"]),
                         f"You are an expert {language} developer.",
                         model or "claude-3-5-sonnet-20241022", 0.3)
