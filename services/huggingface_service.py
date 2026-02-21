"""
HuggingFace Inference API – FREE tier
Sign up at https://huggingface.co/settings/tokens
Uses: Mistral-7B, Zephyr, etc. via the free Inference API
"""
import requests
from config import Config

HF_MODELS = [
    {"id": "mistralai/Mistral-7B-Instruct-v0.3",  "name": "Mistral 7B Instruct – FREE"},
    {"id": "HuggingFaceH4/zephyr-7b-beta",         "name": "Zephyr 7B Beta – FREE"},
    {"id": "microsoft/Phi-3-mini-4k-instruct",     "name": "Phi-3 Mini 4K – FREE"},
]

HF_BASE = "https://api-inference.huggingface.co/models/{model}"


class HuggingFaceService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.HUGGINGFACE_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_available_models(self):
        return HF_MODELS

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _call(self, prompt: str, model: str, temperature: float, max_tokens: int = 1024):
        if not self.is_configured():
            return {
                "success": False,
                "error": "HuggingFace API key not set. Get a FREE token at https://huggingface.co/settings/tokens",
            }
        url = HF_BASE.format(model=model or "mistralai/Mistral-7B-Instruct-v0.3")
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": max(temperature, 0.01),
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }
        try:
            r = requests.post(url, headers=self._headers(), json=payload, timeout=90)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                text = data[0].get("generated_text", "")
            else:
                text = data.get("generated_text", str(data))
            return {"success": True, "response": text, "model": model}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HuggingFace error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_prompt(self, message: str, system_prompt: str = "") -> str:
        sys = system_prompt or "You are a helpful AI assistant."
        return f"<s>[INST] <<SYS>>\n{sys}\n<</SYS>>\n\n{message} [/INST]"

    def chat(self, message: str, system_prompt: str = "", model: str = "", temperature: float = 0.7):
        prompt = self._build_prompt(message, system_prompt)
        return self._call(prompt, model or "mistralai/Mistral-7B-Instruct-v0.3", temperature)

    def code_assist(self, code: str, task: str = "explain", language: str = "python", model: str = ""):
        task_prompts = {
            "explain": f"Explain this {language} code:\n\n```{language}\n{code}\n```",
            "debug":   f"Find and fix bugs:\n\n```{language}\n{code}\n```",
            "generate":f"Generate {language} code for:\n\n{code}",
            "review":  f"Review this {language} code:\n\n```{language}\n{code}\n```",
        }
        prompt = self._build_prompt(task_prompts.get(task, task_prompts["explain"]),
                                    f"You are an expert {language} developer.")
        return self._call(prompt, model or "mistralai/Mistral-7B-Instruct-v0.3", 0.3)
