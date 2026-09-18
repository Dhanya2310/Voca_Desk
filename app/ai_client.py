"""
ai_client.py - Optional AI backend.

Supports:
  - Google Gemini  (VOCADESK_GEMINI_API_KEY)
  - OpenAI         (VOCADESK_OPENAI_API_KEY)

Falls back gracefully if neither is configured.
"""

import os
from app.utils import get_logger

logger = get_logger(__name__)

# Try to load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AIClient:
    """Wraps multiple AI backends, selecting based on available env vars."""

    def __init__(self):
        self._backend = None
        self._model_name = None
        self._setup()

    def _setup(self):
        gemini_key = os.environ.get("VOCADESK_GEMINI_API_KEY", "").strip()
        openai_key = os.environ.get("VOCADESK_OPENAI_API_KEY", "").strip()

        if gemini_key:
            self._setup_gemini(gemini_key)
        elif openai_key:
            self._setup_openai(openai_key)
        else:
            logger.info("No AI API key found — AI mode disabled.")

    def _setup_gemini(self, key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            self._backend = genai.GenerativeModel("gemini-1.5-flash")
            self._model_name = "Gemini 1.5 Flash"
            logger.info("AI backend: %s", self._model_name)
        except ImportError:
            logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
        except Exception as e:
            logger.error("Gemini setup failed: %s", e)

    def _setup_openai(self, key: str):
        try:
            from openai import OpenAI
            self._backend = OpenAI(api_key=key)
            self._model_name = "gpt-4o-mini"
            self._backend_type = "openai"
            logger.info("AI backend: OpenAI")
        except ImportError:
            logger.warning("openai package not installed. Run: pip install openai")
        except Exception as e:
            logger.error("OpenAI setup failed: %s", e)

    @property
    def is_available(self) -> bool:
        return self._backend is not None

    @property
    def model_name(self) -> str | None:
        return self._model_name

    def ask(self, question: str) -> str:
        """Send a question and return the AI's text response."""
        if not self.is_available:
            return (
                "AI mode is not configured. "
                "Add your API key to a .env file or as an environment variable "
                "(VOCADESK_GEMINI_API_KEY or VOCADESK_OPENAI_API_KEY) to enable it."
            )

        system_prompt = (
            "You are VocaDesk, a helpful desktop voice assistant. "
            "Give concise, clear answers suitable to be spoken aloud. "
            "Avoid markdown formatting — use plain text. "
            "Keep responses under 150 words unless the user asks for detail."
        )

        try:
            # Gemini
            try:
                import google.generativeai as genai
                if isinstance(self._backend, genai.GenerativeModel):
                    response = self._backend.generate_content(
                        f"{system_prompt}\n\nUser: {question}"
                    )
                    return response.text.strip()
            except (ImportError, AttributeError):
                pass

            # OpenAI
            try:
                from openai import OpenAI
                if isinstance(self._backend, OpenAI):
                    completion = self._backend.chat.completions.create(
                        model=self._model_name or "gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": question},
                        ],
                        max_tokens=300,
                    )
                    return completion.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                pass

        except Exception as e:
            logger.error("AI query failed: %s", e)
            return f"I couldn't get an answer right now. ({e})"

        return "AI backend not properly configured."
