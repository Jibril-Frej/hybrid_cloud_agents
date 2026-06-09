"""Local answer synthesizer powered by a Qwen model.

Synthesis **always** runs on the private cluster because the prompt contains
private chunks.  The public worker is never involved in synthesis.
"""

import logging
import os
from functools import lru_cache

from transformers import pipeline as hf_pipeline

log = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("SYNTHESIS_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


@lru_cache(maxsize=1)
def _get_pipeline():
    """Lazily load and return the HuggingFace text-generation pipeline.

    The result is cached so the model is loaded only once per process.
    Override ``SYNTHESIS_MODEL`` env var to use a different checkpoint.
    """
    log.info("Loading synthesis model: %s", MODEL_NAME)
    pipe = hf_pipeline(
        "text-generation",
        model=MODEL_NAME,
        device="cpu",
        max_new_tokens=512,
        do_sample=False,
    )
    log.info("Synthesis model loaded")
    return pipe


def synthesize(query: str, public_summary: str, private_chunks: list[str]) -> str:
    """Generate a final answer using both public and private context.

    Builds a prompt that concatenates the public summary and private chunks,
    then runs the local model.  Because the prompt contains private text this
    function must **never** be called from the public cluster.

    Args:
        query: The original user question.
        public_summary: Summarized public-cluster context returned by the
            public worker.  May be an empty string when the public worker is
            unavailable.
        private_chunks: Relevant private document chunks retrieved locally.
            May be an empty list when the private index has no matching docs.

    Returns:
        The generated answer string with the prompt prefix stripped.
    """
    private_ctx = "\n\n".join(private_chunks) if private_chunks else "No private context available."
    public_ctx = public_summary if public_summary else "No public context available."
    prompt = (
        "Answer the question using only the provided context. Be concise and accurate.\n\n"
        f"Public context:\n{public_ctx}\n\n"
        f"Private context:\n{private_ctx}\n\n"
        f"Question: {query}\n\nAnswer:"
    )
    pipe = _get_pipeline()
    result = pipe(prompt)[0]["generated_text"]
    return result[len(prompt) :].strip()
