import os

from transformers import pipeline as hf_pipeline

MODEL_NAME = os.environ.get("SUMMARIZER_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = hf_pipeline(
            "text-generation",
            model=MODEL_NAME,
            device="cpu",
            max_new_tokens=256,
            do_sample=False,
        )
    return _pipeline


def summarize(query: str, chunks: list[str]) -> str:
    if not chunks:
        return ""
    combined = "\n\n".join(chunks)
    prompt = (
        f"Summarize the following documents to help answer: {query}\n\n"
        f"{combined}\n\nSummary:"
    )
    pipe = _get_pipeline()
    result = pipe(prompt)[0]["generated_text"]
    return result[len(prompt) :].strip()
