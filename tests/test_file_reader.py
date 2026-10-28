
import pytest

from tools.file_reader import read_text_file


def test_reads_sample_notes():
    content = read_text_file("notes.txt")

    assert "Multi-Tool Autonomous AI Agent" in content
    assert "30 October 2026" in content


def test_blocks_path_traversal():
    with pytest.raises(PermissionError):
        read_text_file("../../.env")


def test_blocks_unsupported_file_type():
    with pytest.raises(ValueError):
        read_text_file("notes.pdf")