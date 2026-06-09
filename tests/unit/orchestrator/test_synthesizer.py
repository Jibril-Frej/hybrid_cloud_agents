"""Unit tests for the orchestrator synthesizer."""

from unittest.mock import MagicMock, patch

import orchestrator.synthesizer as synth_mod
from orchestrator.synthesizer import synthesize


def test_synthesize_calls_pipeline():
    """synthesize() invokes the HuggingFace pipeline at least once."""
    fake_pipe = MagicMock(return_value=[{"generated_text": "PROMPT_PREFIXfinal answer"}])
    with patch.object(synth_mod, "_get_pipeline", return_value=fake_pipe):
        synthesize("what is the policy?", "public summary", ["private chunk"])
    assert fake_pipe.called


def test_synthesize_includes_query_and_both_contexts():
    """synthesize() builds a prompt containing the query, public summary, and private chunks."""
    captured = {}

    def fake_pipe(prompt):
        """Capture the prompt passed to the pipeline."""
        captured["prompt"] = prompt
        return [{"generated_text": prompt + "answer"}]

    with patch.object(synth_mod, "_get_pipeline", return_value=fake_pipe):
        synthesize("my question", "public info", ["private data"])

    prompt = captured["prompt"]
    assert "my question" in prompt
    assert "public info" in prompt
    assert "private data" in prompt


def test_synthesize_strips_prompt_prefix():
    """synthesize() returns only the generated portion after the prompt prefix."""

    def fake_pipe(prompt):
        """Return the prompt followed by new text, simulating HuggingFace output."""
        return [{"generated_text": prompt + "clean answer"}]

    with patch.object(synth_mod, "_get_pipeline", return_value=fake_pipe):
        result = synthesize("q", "pub", ["priv"])

    assert result == "clean answer"


def test_synthesize_handles_empty_contexts():
    """synthesize() does not crash when public_summary is empty and private_chunks is empty."""

    def fake_pipe(prompt):
        """Return the prompt followed by new text, simulating HuggingFace output."""
        return [{"generated_text": prompt + "answer without context"}]

    with patch.object(synth_mod, "_get_pipeline", return_value=fake_pipe):
        result = synthesize("q", "", [])

    assert result == "answer without context"
