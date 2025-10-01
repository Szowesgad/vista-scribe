#!/usr/bin/env python3
"""
format_benchmark.py

Compare three local MLX-LM models (Bielik 1.5B, 4.5B, 11B) on a Polish
formatting task: add punctuation, fix capitalization, keep meaning, and lightly
handle typos.

Usage:
  uv run python format_benchmark.py

Environment overrides:
  MODEL_1P5_PATH  -> path to 1.5B model (default: ./models/bielik-1.5b-mxfp4-mlx)
  MODEL_4P5_PATH  -> path to 4.5B model (default: ./models/bielik-4.5b-mxfp4-mlx)
  MODEL_11B_PATH  -> path to 11B model (default: ./models/bielik-11b-mxfp4-mlx)
  BENCH_TEXT      -> custom test text (Polish). If unset, uses a built-in sample.
  TEMPERATURE     -> generation temperature (default: 0.2)
  TOP_P           -> default 0.0
  TOP_K           -> default 0
  MAX_NEW_TOKENS  -> default 128

Notes:
- MLX can be picky about uppercase in absolute paths on macOS. We normalize
  '/Users' -> '/users' when possible via path_utils.normalize_model_path.
- Results are saved to outputs/bench/format_benchmark.{md,json}.
"""
from __future__ import annotations

import os
import time
import json
import sys
import logging
from pathlib import Path

from mlx_lm import load as load_lm, generate as lm_generate
from mlx_lm.generate import make_sampler

from path_utils import normalize_model_path
from llm import SYSTEM_PROMPT  # reuse the same instruction as the app

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("format_benchmark")

REPO_ROOT = Path(__file__).resolve().parent
OUT_DIR = REPO_ROOT / "outputs" / "bench"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Defaults (can be overridden by env)
DEFAULT_MODELS = {
    "Bielik-1.5B": str(REPO_ROOT / "models" / "bielik-1.5b-mxfp4-mlx"),
    "Bielik-4.5B": str(REPO_ROOT / "models" / "bielik-4.5b-mxfp4-mlx"),
    "Bielik-11B": str(REPO_ROOT / "models" / "bielik-11b-mxfp4-mlx"),
}
ENV_OVERRIDES = {
    "Bielik-1.5B": os.environ.get("MODEL_1P5_PATH"),
    "Bielik-4.5B": os.environ.get("MODEL_4P5_PATH"),
    "Bielik-11B": os.environ.get("MODEL_11B_PATH"),
}

# Test text (errors + typos); can be overridden by BENCH_TEXT
DEFAULT_TEXT = (
    "to jest szybka notatka bez kropek i bez wielkich liter mam tu pare literuwek "
    "pacjent z choroba nerek byl wczoraj na badaniu krwii wyniki sa dobre ale trzeba "
    "powtorzyc za tydzien bo byl lekki katar i kaszel"
)
TEST_TEXT = os.environ.get("BENCH_TEXT", DEFAULT_TEXT)

# Gen params (align with app defaults)
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.2"))
TOP_P = float(os.environ.get("TOP_P", "0.0"))
TOP_K = int(os.environ.get("TOP_K", "0"))
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "128"))


def build_prompt(tokenizer, user_text: str) -> str:
    """Build a prompt using chat template when available, otherwise fallback."""
    try:
        if hasattr(tokenizer, "apply_chat_template"):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            return tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    except Exception as e:
        logger.debug(f"apply_chat_template failed, falling back: {e}")
    return f"System: {SYSTEM_PROMPT}\nUser: {user_text}\nAssistant:"


def bench_model(model_name: str, model_path: str, text: str) -> dict:
    logger.info(f"\n=== {model_name} ===")
    # Normalize path for MLX quirks
    norm = normalize_model_path(model_path) or model_path

    # Load
    t0 = time.perf_counter()
    model, tok = load_lm(norm)
    load_s = time.perf_counter() - t0
    logger.info(f"Loaded {model_name} from: {norm} (load {load_s:.2f}s)")

    # Build prompt
    prompt = build_prompt(tok, text)
    sampler = make_sampler(temp=TEMPERATURE, top_p=TOP_P, top_k=TOP_K)

    # Generate
    t1 = time.perf_counter()
    out = lm_generate(model, tok, prompt, max_tokens=MAX_NEW_TOKENS, sampler=sampler)
    gen_s = time.perf_counter() - t1

    out = (out or "").strip()
    logger.info(f"Generation time: {gen_s:.2f}s | Output length: {len(out)} chars")

    return {
        "model": model_name,
        "path": norm,
        "load_seconds": round(load_s, 3),
        "gen_seconds": round(gen_s, 3),
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "max_new_tokens": MAX_NEW_TOKENS,
        "input": text,
        "output": out,
    }


def main() -> int:
    # Compose model list with env overrides when provided
    models = []
    for name, default_path in DEFAULT_MODELS.items():
        override = ENV_OVERRIDES.get(name)
        path = override if override else default_path
        # If the directory does not exist, warn but still attempt to load (in case it's an HF repo id)
        if not (path.startswith("/") and os.path.isdir(path)):
            logger.warning(f"Model path not found as local dir (may still be HF repo id): {path}")
        models.append((name, path))

    logger.info("Starting benchmark for models: " + ", ".join(n for n, _ in models))

    results = []
    for name, path in models:
        try:
            res = bench_model(name, path, TEST_TEXT)
            results.append(res)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Benchmark failed for {name}: {e}", exc_info=True)
            results.append({
                "model": name,
                "path": path,
                "error": str(e),
                "input": TEST_TEXT,
            })

    # Save JSON
    json_path = OUT_DIR / "format_benchmark.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON results to {json_path}")

    # Save Markdown comparison
    md_path = OUT_DIR / "format_benchmark.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Format Benchmark (Polish PnC)\n\n")
        f.write(f"System prompt: `{SYSTEM_PROMPT}`\n\n")
        f.write("Input:\n\n")
        f.write("> " + TEST_TEXT.replace("\n", " ") + "\n\n")
        for r in results:
            f.write(f"## {r.get('model')}\n\n")
            if "error" in r:
                f.write(f"- Error: {r['error']}\n\n")
                continue
            f.write(f"- Path: `{r.get('path','')}`\n")
            f.write(f"- Load: {r.get('load_seconds','?')} s\n")
            f.write(f"- Generate: {r.get('gen_seconds','?')} s\n")
            f.write(f"- Max new tokens: {r.get('max_new_tokens')} | T={r.get('temperature')} | top_p={r.get('top_p')} | top_k={r.get('top_k')}\n\n")
            f.write("Output:\n\n")
            f.write(r.get("output", "").strip() + "\n\n")
    logger.info(f"Saved Markdown comparison to {md_path}")

    # Also print a compact console summary
    print("\n=== Summary ===")
    for r in results:
        if "error" in r:
            print(f"- {r['model']}: ERROR -> {r['error']}")
        else:
            print(f"- {r['model']}: load {r['load_seconds']}s | gen {r['gen_seconds']}s | len {len(r['output'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
