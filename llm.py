# llm.py (formatting)
#
# Local formatting using MLX-LM by default (no API key). Optional OpenAI fallback.
#
# Env vars:
# - FORMAT_BACKEND: 'local' (default) or 'openai'.
# - LLM_ID: path to local MLX model dir or HF repo id (default tries local Bielik paths).
# - TEMPERATURE, MAX_NEW_TOKENS: generation params for local backend.
#
from __future__ import annotations
import asyncio
import functools
import logging
import os
from dotenv import load_dotenv

# Local MLX-LM
from mlx_lm import load as load_lm, generate as lm_generate
from mlx_lm.generate import make_sampler
from path_utils import normalize_model_path

# Optional OpenAI fallback
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover
    openai = None  # not required in local mode

# --- setup ---
load_dotenv()
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s - %(levelname)s - %(message)s")

FORMAT_BACKEND = os.environ.get("FORMAT_BACKEND", "local").lower()
FORMAT_ENABLED = os.environ.get("FORMAT_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}

# --- model load (local) ---
_model = None
_tok = None
_llm_id = None


def _choose_default_llm_path() -> str:
    """Pick a sensible default model path present in this repo."""
    repo_root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(repo_root, "models", "bielik-1.5b-mxfp4-mlx"),
        os.path.join(repo_root, "bielik-1.5b-mxfp4-mlx"),  # if stored at root
        os.path.join(repo_root, "models", "bielik-4.5b-mxfp4-mlx"),
        os.path.join(repo_root, "bielik-4.5b-mxfp4-mlx"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    # Fallback to a known HF MLX repo (download-on-first-use)
    return "mlx-community/Llama-3.2-3B-Instruct-4bit"


def _init_local_model():
    global _model, _tok, _llm_id
    if _model is not None:
        return
    raw_llm_id = os.environ.get("LLM_ID", _choose_default_llm_path())
    llm_id = normalize_model_path(raw_llm_id)
    _model, _tok = load_lm(llm_id)
    _llm_id = llm_id
    logging.info(f"MLX-LM model loaded: {llm_id}")


def _build_prompt(user_text: str) -> str:
    """Build a prompt using the tokenizer's chat template when available."""
    try:
        if hasattr(_tok, "apply_chat_template"):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            return _tok.apply_chat_template(messages, add_generation_prompt=True)
    except Exception as e:  # fallback
        logging.debug(f"apply_chat_template failed, falling back: {e}")
    # Fallback minimal instruction-style prompt
    return f"System: {SYSTEM_PROMPT}\nUser: {user_text}\nAssistant:"


# --- constants ---
SYSTEM_PROMPT = (
    "Sformatuj polski transkrypt: dodaj interpunkcję, popraw wielkie litery, "
    "nie zmieniaj sensu ani słów, nie dodawaj komentarza."
)
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.2"))
TOP_P = float(os.environ.get("TOP_P", "0.0"))
TOP_K = int(os.environ.get("TOP_K", "0"))
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "128"))
OPENAI_MODEL = os.environ.get("OPENAI_FORMAT_MODEL", "gpt-4o-mini")


async def format_text(raw_text: str) -> str | None:
    """Format raw text using the configured backend.

    Returns cleaned text or the original on empty input.
    """
    # Allow disabling formatting entirely (LLM optional)
    if not FORMAT_ENABLED:
        return raw_text

    if not raw_text or raw_text.isspace():
        logging.warning("Received empty or whitespace-only text for formatting.")
        return raw_text

    if FORMAT_BACKEND == "openai":
        if openai is None:
            logging.error("OpenAI backend requested but openai package not available.")
            return raw_text
        try:
            client = openai.OpenAI()
        except Exception as e:
            logging.error(f"Failed to init OpenAI client: {e}")
            return raw_text

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ]
        loop = asyncio.get_event_loop()
        func = functools.partial(
            client.chat.completions.create,
            model=OPENAI_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
        )
        try:
            logging.info(f"Sending text to OpenAI {OPENAI_MODEL} API…")
            response = await loop.run_in_executor(None, func)
            if response.choices:
                return (response.choices[0].message.content or "").strip()
            return None
        except Exception as e:
            logging.error(f"OpenAI formatting error: {e}")
            return None

    # Local backend (default)
    try:
        _init_local_model()
        prompt = _build_prompt(raw_text)
        loop = asyncio.get_event_loop()
        sampler = make_sampler(temp=TEMPERATURE, top_p=TOP_P, top_k=TOP_K)
        func = functools.partial(
            lm_generate,
            _model,
            _tok,
            prompt,
            max_tokens=MAX_NEW_TOKENS,
            sampler=sampler,
        )
        out = await loop.run_in_executor(None, func)
        out = (out or "").strip()
        if out:
            return out
        # Fallback to CLI if model produced empty output
        import subprocess, sys
        cmd = [sys.executable, '-m', 'mlx_lm.generate', '--model', _llm_id or 'models/bielik-1.5b-mxfp4-mlx', '--system-prompt', SYSTEM_PROMPT, '--prompt', '-', '--max-tokens', str(MAX_NEW_TOKENS), '--temp', str(TEMPERATURE)]
        logging.info("Falling back to CLI: python -m mlx_lm.generate …")
        proc = await loop.run_in_executor(None, lambda: subprocess.run(cmd, input=raw_text.encode('utf-8'), capture_output=True))
        txt = proc.stdout.decode('utf-8').strip()
        return txt or None
    except Exception as e:
        logging.error(f"Local formatting error: {e}", exc_info=True)
        return None
