from unittest.mock import MagicMock, patch

import orchestrator.synthesizer as synth_mod
from orchestrator.synthesizer import synthesize


def test_synthesize_calls_pipeline():
    fake_pipe = MagicMock(return_value=[{"generated_text": "PROMPT_PREFIXfinal answer"}])
    with patch.object(synth_mod, "_pipeline", fake_pipe):
        synthesize("what is the policy?", "public summary", ["private chunk"])
    assert fake_pipe.called


def test_synthesize_includes_query_and_both_contexts():
    captured = {}

    def fake_pipe(prompt):
        captured["prompt"] = prompt
        return [{"generated_text": prompt + "answer"}]

    with patch.object(synth_mod, "_pipeline", fake_pipe):
        synthesize("my question", "public info", ["private data"])

    prompt = captured["prompt"]
    assert "my question" in prompt
    assert "public info" in prompt
    assert "private data" in prompt


def test_synthesize_strips_prompt_prefix():
    def fake_pipe(prompt):
        return [{"generated_text": prompt + "clean answer"}]

    with patch.object(synth_mod, "_pipeline", fake_pipe):
        result = synthesize("q", "pub", ["priv"])

    assert result == "clean answer"


def test_synthesize_handles_empty_contexts():
    def fake_pipe(prompt):
        return [{"generated_text": prompt + "answer without context"}]

    with patch.object(synth_mod, "_pipeline", fake_pipe):
        result = synthesize("q", "", [])

    assert result == "answer without context"
