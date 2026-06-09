"""Unit tests for the public summarizer."""

from unittest.mock import MagicMock, patch

import public.summarizer as summarizer_mod
from public.summarizer import summarize


def test_summarize_empty_chunks_returns_empty():
    """summarize() returns an empty string immediately when chunks is empty."""
    assert summarize("any query", []) == ""


def test_summarize_calls_pipeline_with_prompt():
    """summarize() builds a prompt containing the query and each chunk, then calls the pipeline."""
    fake_pipe = MagicMock(return_value=[{"generated_text": "PROMPT_PREFIXsummary text"}])
    with patch.object(summarizer_mod, "_get_pipeline", return_value=fake_pipe):
        summarize("what is BM25?", ["BM25 is a ranking function."])
    assert fake_pipe.called
    prompt_used = fake_pipe.call_args[0][0]
    assert "what is BM25?" in prompt_used
    assert "BM25 is a ranking function." in prompt_used


def test_summarize_strips_prompt_prefix():
    """summarize() returns only the generated text after the prompt prefix."""
    prompt_prefix = None

    def fake_pipe(prompt):
        """Capture the prompt and simulate HuggingFace pipeline output."""
        nonlocal prompt_prefix
        prompt_prefix = prompt
        return [{"generated_text": prompt + "this is the summary"}]

    with patch.object(summarizer_mod, "_get_pipeline", return_value=fake_pipe):
        result = summarize("query", ["chunk one"])

    assert result == "this is the summary"


def test_summarize_multiple_chunks_joined():
    """summarize() joins multiple chunks so all appear in the prompt."""
    fake_pipe = MagicMock(return_value=[{"generated_text": "PREFIX_summary"}])
    with patch.object(summarizer_mod, "_get_pipeline", return_value=fake_pipe):
        summarize("query", ["chunk A", "chunk B"])
    prompt = fake_pipe.call_args[0][0]
    assert "chunk A" in prompt
    assert "chunk B" in prompt
