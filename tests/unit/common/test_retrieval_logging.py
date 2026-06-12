"""Unit tests for common.retrieval_logging."""

import logging

import pytest

from common.retrieval_logging import log_retrieval_results

LOGGER_NAME = "test_logger"


class TestLogRetrievalResults:
    """Test the log_retrieval_results function."""

    def test_logs_one_info_record_per_result_with_all_fields(self, caplog):
        """Each result is logged at INFO with its rank, id, distance, and text."""
        logger = logging.getLogger(LOGGER_NAME)
        query = "test query"
        ids = ["id1", "id2"]
        distances = [0.1, 0.123456789]
        documents = ["doc1", "doc2"]

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            log_retrieval_results(logger, query, ids, distances, documents)

        assert len(caplog.records) == 2
        for rank, record in enumerate(caplog.records, start=1):
            assert record.levelno == logging.INFO
            message = record.getMessage()
            assert f"query={query!r}" in message
            assert f"rank={rank}" in message
            assert f"id={ids[rank - 1]!r}" in message
            assert f"text={documents[rank - 1]!r}" in message
        assert "distance=0.1000" in caplog.records[0].getMessage()
        assert "distance=0.1235" in caplog.records[1].getMessage()

    def test_empty_results_logs_nothing(self, caplog):
        """log_retrieval_results logs nothing when given empty lists."""
        logger = logging.getLogger(LOGGER_NAME)

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            log_retrieval_results(logger, "query", [], [], [])

        assert len(caplog.records) == 0

    @pytest.mark.parametrize(
        ("ids", "distances", "documents"),
        [
            (["id1", "id2"], [0.1], ["doc1", "doc2"]),
            (["id1", "id2"], [0.1, 0.2], ["doc1"]),
            (["id1"], [0.1, 0.2], ["doc1", "doc2"]),
        ],
    )
    def test_mismatched_lengths_raise_value_error(self, ids, distances, documents):
        """log_retrieval_results raises ValueError if the inputs have different lengths."""
        logger = logging.getLogger(LOGGER_NAME)

        with pytest.raises(ValueError):
            log_retrieval_results(logger, "query", ids, distances, documents)
