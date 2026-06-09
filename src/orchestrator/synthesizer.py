import os

from transformers import pipeline as hf_pipeline

MODEL_NAME = os.environ.get("SYNTHESIS_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = hf_pipeline(
            "text-generation",
            model=MODEL_NAME,
            device="cpu",
            max_new_tokens=512,
            do_sample=False,
        )
    return _pipeline


def synthesize(query: str, public_summary: str, private_chunks: list[str]) -> str:
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
