"""Public-cluster chunk summarizer powered by a local Qwen model.

Summarizes retrieved public chunks into a single string that is safe to return
to the orchestrator.  The summarizer never performs final synthesis — it only
condenses public context.
"""

import os
from functools import lru_cache

from transformers import pipeline as hf_pipeline

MODEL_NAME = os.environ.get("SUMMARIZER_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


@lru_cache(maxsize=1)
def _get_pipeline():
    """Lazily load and return the HuggingFace text-generation pipeline.

    The result is cached so the model is loaded only once per process.
    Override ``SUMMARIZER_MODEL`` env var to use a different checkpoint.
    """
    return hf_pipeline(
        "text-generation",
        model=MODEL_NAME,
        device="cpu",
        max_new_tokens=256,
        do_sample=False,
    )


def summarize(query: str, chunks: list[str]) -> str:
    """Summarize *chunks* into a single string relevant to *query*.

    Args:
        query: The user query — used to focus the summary on relevant content.
        chunks: Retrieved public document chunks to summarize.

    Returns:
        A summarized string of the public context, or an empty string when
        *chunks* is empty.
    """
    if not chunks:
        return ""
    combined = "\n\n".join(chunks)
    prompt = f"Summarize the following documents to help answer: {query}\n\n{combined}\n\nSummary:"
    pipe = _get_pipeline()
    result = pipe(prompt)[0]["generated_text"]
    return result[len(prompt) :].strip()
