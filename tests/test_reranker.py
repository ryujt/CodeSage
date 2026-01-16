import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SageLibs.reranker import rerank_documents, clear_model_cache, _get_reranker_model


class TestReranker:

    def setup_method(self):
        clear_model_cache()

    def teardown_method(self):
        clear_model_cache()

    def test_rerank_empty_documents(self):
        result = rerank_documents("test query", [])
        assert result == []

    def test_rerank_documents_preserves_original_data(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            mock_instance = MagicMock()
            mock_instance.predict.return_value = [0.9, 0.5, 0.7]
            mock_model.return_value = mock_instance

            documents = [
                {'filename': 'file1.py', 'content': 'def hello(): pass', 'original_score': 0.8},
                {'filename': 'file2.py', 'content': 'def world(): pass', 'original_score': 0.6},
                {'filename': 'file3.py', 'content': 'def test(): pass', 'original_score': 0.4}
            ]

            result = rerank_documents("hello function", documents, top_k=3)

            assert len(result) == 3
            for doc in result:
                assert 'filename' in doc
                assert 'content' in doc
                assert 'original_score' in doc
                assert 'rerank_score' in doc

    def test_rerank_documents_sorts_by_rerank_score(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            mock_instance = MagicMock()
            mock_instance.predict.return_value = [0.3, 0.9, 0.6]
            mock_model.return_value = mock_instance

            documents = [
                {'filename': 'file1.py', 'content': 'content1'},
                {'filename': 'file2.py', 'content': 'content2'},
                {'filename': 'file3.py', 'content': 'content3'}
            ]

            result = rerank_documents("query", documents, top_k=3)

            assert result[0]['filename'] == 'file2.py'
            assert result[0]['rerank_score'] == 0.9
            assert result[1]['filename'] == 'file3.py'
            assert result[1]['rerank_score'] == 0.6
            assert result[2]['filename'] == 'file1.py'
            assert result[2]['rerank_score'] == 0.3

    def test_rerank_documents_respects_top_k(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            mock_instance = MagicMock()
            mock_instance.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
            mock_model.return_value = mock_instance

            documents = [
                {'filename': f'file{i}.py', 'content': f'content{i}'}
                for i in range(5)
            ]

            result = rerank_documents("query", documents, top_k=2)

            assert len(result) == 2

    def test_rerank_documents_uses_default_top_k(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            with patch('SageLibs.config.RERANKER_TOP_K', 3):
                mock_instance = MagicMock()
                mock_instance.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
                mock_model.return_value = mock_instance

                documents = [
                    {'filename': f'file{i}.py', 'content': f'content{i}'}
                    for i in range(5)
                ]

                result = rerank_documents("query", documents)

                assert len(result) <= 5

    def test_rerank_documents_handles_missing_content(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            mock_instance = MagicMock()
            mock_instance.predict.return_value = [0.9, 0.5]
            mock_model.return_value = mock_instance

            documents = [
                {'filename': 'file1.py'},
                {'filename': 'file2.py', 'content': 'some content'}
            ]

            result = rerank_documents("query", documents, top_k=2)

            mock_instance.predict.assert_called_once()
            call_args = mock_instance.predict.call_args[0][0]
            assert call_args[0] == ("query", "")
            assert call_args[1] == ("query", "some content")

    def test_rerank_documents_creates_document_copies(self):
        with patch('SageLibs.reranker._get_reranker_model') as mock_model:
            mock_instance = MagicMock()
            mock_instance.predict.return_value = [0.9]
            mock_model.return_value = mock_instance

            original_doc = {'filename': 'file1.py', 'content': 'test'}
            documents = [original_doc]

            result = rerank_documents("query", documents, top_k=1)

            assert 'rerank_score' not in original_doc
            assert 'rerank_score' in result[0]

    def test_clear_model_cache(self):
        import SageLibs.reranker as reranker_module

        reranker_module._reranker_model = "fake_model"

        clear_model_cache()

        assert reranker_module._reranker_model is None


class TestRerankerModelLoading:

    def setup_method(self):
        clear_model_cache()

    def teardown_method(self):
        clear_model_cache()

    def test_lazy_model_loading(self):
        import SageLibs.reranker as reranker_module

        assert reranker_module._reranker_model is None

        with patch('sentence_transformers.CrossEncoder') as mock_cross_encoder:
            mock_instance = MagicMock()
            mock_cross_encoder.return_value = mock_instance

            with patch('SageLibs.config.RERANKER_MODEL', 'test-model'):
                model = _get_reranker_model()

                mock_cross_encoder.assert_called_once_with('test-model')
                assert model == mock_instance

    def test_model_caching(self):
        with patch('sentence_transformers.CrossEncoder') as mock_cross_encoder:
            mock_instance = MagicMock()
            mock_cross_encoder.return_value = mock_instance

            model1 = _get_reranker_model()
            model2 = _get_reranker_model()

            mock_cross_encoder.assert_called_once()
            assert model1 is model2
