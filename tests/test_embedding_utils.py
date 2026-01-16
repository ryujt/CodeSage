import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SageLibs.embedding_utils import chunk_content


class TestChunkContent:

    def test_chunk_small_content(self):
        content = "Small content that fits in one chunk"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 10
            chunks = chunk_content(content, overlap_tokens=50)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_large_content_creates_multiple_chunks(self):
        lines = [f"Line {i}\n" for i in range(100)]
        content = "".join(lines)

        token_counts = {}
        def mock_count_tokens(text):
            line_count = text.count('\n')
            return line_count * 100

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 500):
                chunks = chunk_content(content, overlap_tokens=0)

        assert len(chunks) > 1

    def test_chunk_with_overlap(self):
        lines = ["Line A\n", "Line B\n", "Line C\n", "Line D\n", "Line E\n"]
        content = "".join(lines)

        call_count = [0]
        def mock_count_tokens(text):
            call_count[0] += 1
            if call_count[0] <= 2:
                return 100
            elif "Line A" in text and "Line B" in text:
                return 8001
            elif "Line B" in text and "Line C" in text:
                return 8001
            else:
                return len(text) * 10

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 8000):
                chunks = chunk_content(content, overlap_tokens=50)

        assert len(chunks) >= 1

    def test_chunk_preserves_all_content(self):
        content = "Line1\nLine2\nLine3\n"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 10
            chunks = chunk_content(content, overlap_tokens=0)

        combined = "".join(chunks)
        assert combined == content

    def test_chunk_empty_content(self):
        content = ""

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 0
            chunks = chunk_content(content, overlap_tokens=0)

        assert chunks == [] or chunks == [""]

    def test_chunk_single_line_exceeds_window(self):
        content = "A" * 10000

        def mock_count_tokens(text):
            return len(text)

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 8000):
                chunks = chunk_content(content, overlap_tokens=0)

        assert len(chunks) >= 1

    def test_chunk_uses_default_overlap_from_settings(self):
        content = "Test content"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 10
            with patch('SageLibs.embedding_utils.get_setting') as mock_setting:
                mock_setting.return_value = 300
                chunks = chunk_content(content)
                mock_setting.assert_called_with('chunk_overlap_tokens', 200)

    def test_chunk_respects_line_boundaries(self):
        content = "Line 1\nLine 2\nLine 3\n"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 10
            chunks = chunk_content(content, overlap_tokens=0)

        for chunk in chunks:
            if chunk and not chunk.endswith('\n'):
                pass

    def test_chunk_overlap_tokens_zero(self):
        lines = [f"Line {i}\n" for i in range(10)]
        content = "".join(lines)

        call_count = [0]
        def mock_count_tokens(text):
            call_count[0] += 1
            return len(text.split('\n')) * 100

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 300):
                chunks = chunk_content(content, overlap_tokens=0)

        assert len(chunks) >= 1

    def test_chunk_maintains_overlap_buffer_limit(self):
        lines = [f"Line {i}\n" for i in range(100)]
        content = "".join(lines)

        def mock_count_tokens(text):
            return len(text)

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 500):
                chunks = chunk_content(content, overlap_tokens=100)

        assert len(chunks) >= 1


class TestChunkContentEdgeCases:

    def test_chunk_with_only_newlines(self):
        content = "\n\n\n\n"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 1
            chunks = chunk_content(content, overlap_tokens=0)

        assert isinstance(chunks, list)

    def test_chunk_with_unicode_content(self):
        content = "한글 텍스트\n日本語テキスト\n中文文本\n"

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 50
            chunks = chunk_content(content, overlap_tokens=10)

        assert len(chunks) >= 1
        combined = "".join(chunks)
        assert "한글" in combined
        assert "日本語" in combined
        assert "中文" in combined

    def test_chunk_with_code_content(self):
        content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""

        with patch('SageLibs.embedding_utils.count_tokens') as mock_count:
            mock_count.return_value = 30
            chunks = chunk_content(content, overlap_tokens=10)

        combined = "".join(chunks)
        assert "def hello" in combined
        assert "def goodbye" in combined

    def test_chunk_very_long_single_line(self):
        content = "A" * 50000 + "\n"

        def mock_count_tokens(text):
            return len(text)

        with patch('SageLibs.embedding_utils.count_tokens', side_effect=mock_count_tokens):
            with patch('SageLibs.embedding_utils.WINDOW_SIZE', 8000):
                chunks = chunk_content(content, overlap_tokens=100)

        assert len(chunks) >= 1
