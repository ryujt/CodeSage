import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SageLibs.utilities import find_most_similar, get_relevant_documents, load_embeddings


class TestFindMostSimilar:

    def setup_method(self):
        self.mock_settings = {
            'essential_files': ['essential.md'],
            'extensions': ['.py', '.js', '.md'],
            'ignore_files': ['ignore_me.py'],
            'ignore_folders': ['node_modules'],
            'use_hybrid_search': False,
            'use_reranker': False
        }

    def get_setting(self, key, default=None):
        return self.mock_settings.get(key, default)

    def test_find_most_similar_basic(self):
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'content1'},
            'file2.py': {'embedding': [0.9, 0.1, 0.0], 'content': 'content2'},
            'file3.py': {'embedding': [0.0, 1.0, 0.0], 'content': 'content3'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings)

        assert len(results) > 0
        filenames = [r[0] for r in results]
        assert 'essential.md' in filenames

    def test_find_most_similar_excludes_essential_files_from_search(self):
        embeddings = {
            'essential.md': {'embedding': [1.0, 0.0, 0.0], 'content': 'essential'},
            'file1.py': {'embedding': [0.9, 0.1, 0.0], 'content': 'content1'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings)

        filenames = [r[0] for r in results]
        assert 'essential.md' in filenames
        assert 'file1.py' in filenames

    def test_find_most_similar_filters_by_extension(self):
        self.mock_settings['extensions'] = ['.py']
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'python'},
            'file2.js': {'embedding': [1.0, 0.0, 0.0], 'content': 'javascript'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings)

        non_essential = [r[0] for r in results if r[0] != 'essential.md']
        assert 'file1.py' in non_essential
        assert 'file2.js' not in non_essential

    def test_find_most_similar_filters_ignore_files(self):
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'content'},
            'ignore_me.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'ignored'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings)

        filenames = [r[0] for r in results]
        assert 'ignore_me.py' not in filenames

    def test_find_most_similar_filters_ignore_folders(self):
        embeddings = {
            'src/file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'content'},
            'node_modules/pkg/file.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'ignored'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings)

        filenames = [r[0] for r in results]
        assert 'node_modules/pkg/file.py' not in filenames

    def test_find_most_similar_with_hybrid_search(self):
        self.mock_settings['use_hybrid_search'] = True
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'python code'},
            'file2.py': {'embedding': [0.5, 0.5, 0.0], 'content': 'java code'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        mock_hybrid_results = [('file1.py', 0.9), ('file2.py', 0.5)]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.hybrid_search.hybrid_search', return_value=mock_hybrid_results):
                results = find_most_similar(
                    query_embedding,
                    embeddings,
                    query_text="python code"
                )

        assert len(results) > 0

    def test_find_most_similar_with_reranker(self):
        self.mock_settings['use_hybrid_search'] = False
        self.mock_settings['use_reranker'] = True
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'def hello(): pass'},
            'file2.py': {'embedding': [0.9, 0.1, 0.0], 'content': 'def world(): pass'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        mock_reranked = [
            {'filename': 'file2.py', 'rerank_score': 0.95},
            {'filename': 'file1.py', 'rerank_score': 0.85}
        ]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.reranker.rerank_documents', return_value=mock_reranked):
                results = find_most_similar(
                    query_embedding,
                    embeddings,
                    query_text="hello function"
                )

        filenames = [r[0] for r in results if r[0] != 'essential.md']
        if filenames:
            assert filenames[0] == 'file2.py'

    def test_find_most_similar_without_query_text_skips_reranker(self):
        self.mock_settings['use_reranker'] = True
        embeddings = {
            'file1.py': {'embedding': [1.0, 0.0, 0.0], 'content': 'content'}
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.reranker.rerank_documents') as mock_rerank:
                results = find_most_similar(query_embedding, embeddings)
                mock_rerank.assert_not_called()

    def test_find_most_similar_respects_top_k(self):
        embeddings = {
            f'file{i}.py': {'embedding': [1.0, 0.0, 0.0], 'content': f'content{i}'}
            for i in range(50)
        }
        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = find_most_similar(query_embedding, embeddings, top_k=10)

        assert len(results) <= 10


class TestGetRelevantDocuments:

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_settings = {
            'essential_files': [],
            'extensions': ['.py'],
            'ignore_files': [],
            'ignore_folders': [],
            'use_hybrid_search': False,
            'use_reranker': False
        }

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_setting(self, key, default=None):
        return self.mock_settings.get(key, default)

    def create_embeddings_file(self, embeddings_data):
        filepath = os.path.join(self.temp_dir, 'embeddings.jsonl')
        with open(filepath, 'w') as f:
            for data in embeddings_data:
                f.write(json.dumps(data) + '\n')
        return filepath

    def test_get_relevant_documents_basic(self):
        embeddings_data = [
            {
                'filename': 'file1.py',
                'embedding': [1.0, 0.0, 0.0],
                'content': 'def hello(): print("Hello")'
            }
        ]
        self.create_embeddings_file(embeddings_data)

        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            results = get_relevant_documents(
                [self.temp_dir],
                query_embedding,
                max_tokens=80000
            )

        assert len(results) == 1
        assert results[0]['filename'] == 'file1.py'
        assert 'content' in results[0]
        assert 'tokens' in results[0]
        assert 'similarity' in results[0]

    def test_get_relevant_documents_passes_query_text(self):
        embeddings_data = [
            {
                'filename': 'file1.py',
                'embedding': [1.0, 0.0, 0.0],
                'content': 'python code'
            }
        ]
        self.create_embeddings_file(embeddings_data)

        query_embedding = [1.0, 0.0, 0.0]
        query_text = "find python code"

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.utilities.find_most_similar') as mock_find:
                mock_find.return_value = [('file1.py', 0.9)]
                results = get_relevant_documents(
                    [self.temp_dir],
                    query_embedding,
                    query_text=query_text
                )

                mock_find.assert_called_once()
                call_kwargs = mock_find.call_args[1]
                assert call_kwargs.get('query_text') == query_text

    def test_get_relevant_documents_respects_max_tokens(self):
        embeddings_data = [
            {
                'filename': f'file{i}.py',
                'embedding': [1.0, 0.0, 0.0],
                'content': 'x' * 1000
            }
            for i in range(10)
        ]
        self.create_embeddings_file(embeddings_data)

        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.utilities.count_tokens') as mock_count:
                mock_count.return_value = 5000
                results = get_relevant_documents(
                    [self.temp_dir],
                    query_embedding,
                    max_tokens=10000
                )

        assert len(results) <= 2

    def test_get_relevant_documents_handles_missing_file(self):
        embeddings_data = [
            {
                'filename': 'file1.py',
                'embedding': [1.0, 0.0, 0.0],
                'content': 'content1'
            }
        ]
        self.create_embeddings_file(embeddings_data)

        query_embedding = [1.0, 0.0, 0.0]

        with patch('SageLibs.utilities.get_setting', side_effect=self.get_setting):
            with patch('SageLibs.utilities.find_most_similar') as mock_find:
                mock_find.return_value = [('nonexistent.py', 0.9)]
                results = get_relevant_documents(
                    [self.temp_dir],
                    query_embedding
                )

        assert len(results) == 0


class TestLoadEmbeddings:

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_embeddings_basic(self):
        filepath = os.path.join(self.temp_dir, 'embeddings.jsonl')
        data = [
            {'filename': 'file1.py', 'embedding': [1, 2, 3], 'content': 'content1'},
            {'filename': 'file2.py', 'embedding': [4, 5, 6], 'content': 'content2'}
        ]
        with open(filepath, 'w') as f:
            for d in data:
                f.write(json.dumps(d) + '\n')

        embeddings = load_embeddings(filepath)

        assert len(embeddings) == 2
        assert 'file1.py' in embeddings
        assert 'file2.py' in embeddings

    def test_load_embeddings_handles_chunks(self):
        filepath = os.path.join(self.temp_dir, 'embeddings.jsonl')
        data = [
            {'filename': 'file1.py', 'embedding': [1, 2, 3], 'content': 'chunk1'},
            {'filename': 'file1.py', 'embedding': [4, 5, 6], 'content': 'chunk2'},
            {'filename': 'file1.py', 'embedding': [7, 8, 9], 'content': 'chunk3'}
        ]
        with open(filepath, 'w') as f:
            for d in data:
                f.write(json.dumps(d) + '\n')

        embeddings = load_embeddings(filepath)

        assert len(embeddings) == 3
        assert 'file1.py' in embeddings
        assert 'file1.py#1' in embeddings
        assert 'file1.py#2' in embeddings

    def test_load_embeddings_nonexistent_file(self):
        filepath = os.path.join(self.temp_dir, 'nonexistent.jsonl')

        embeddings = load_embeddings(filepath)

        assert embeddings == {}

    def test_load_embeddings_invalid_json(self):
        filepath = os.path.join(self.temp_dir, 'embeddings.jsonl')
        with open(filepath, 'w') as f:
            f.write('{"filename": "file1.py", "embedding": [1, 2, 3]}\n')
            f.write('not valid json\n')
            f.write('{"filename": "file2.py", "embedding": [4, 5, 6]}\n')

        embeddings = load_embeddings(filepath)

        assert len(embeddings) == 2

    def test_load_embeddings_missing_filename(self):
        filepath = os.path.join(self.temp_dir, 'embeddings.jsonl')
        data = [
            {'embedding': [1, 2, 3], 'content': 'no filename'},
            {'filename': 'file1.py', 'embedding': [4, 5, 6], 'content': 'has filename'}
        ]
        with open(filepath, 'w') as f:
            for d in data:
                f.write(json.dumps(d) + '\n')

        embeddings = load_embeddings(filepath)

        assert len(embeddings) == 1
        assert 'file1.py' in embeddings
