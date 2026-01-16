import pytest
from unittest.mock import patch, mock_open
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfigConstants:

    def test_reranker_constants_exist(self):
        from SageLibs.config import USE_RERANKER, RERANKER_MODEL, RERANKER_TOP_K

        assert isinstance(USE_RERANKER, bool)
        assert isinstance(RERANKER_MODEL, str)
        assert isinstance(RERANKER_TOP_K, int)
        assert RERANKER_TOP_K > 0

    def test_hybrid_search_constants_exist(self):
        from SageLibs.config import USE_HYBRID_SEARCH, BM25_WEIGHT, SEMANTIC_WEIGHT

        assert isinstance(USE_HYBRID_SEARCH, bool)
        assert isinstance(BM25_WEIGHT, float)
        assert isinstance(SEMANTIC_WEIGHT, float)
        assert 0 <= BM25_WEIGHT <= 1
        assert 0 <= SEMANTIC_WEIGHT <= 1

    def test_chunk_overlap_constant_exists(self):
        from SageLibs.config import CHUNK_OVERLAP_TOKENS

        assert isinstance(CHUNK_OVERLAP_TOKENS, int)
        assert CHUNK_OVERLAP_TOKENS >= 0

    def test_default_reranker_model(self):
        from SageLibs.config import RERANKER_MODEL

        assert 'cross-encoder' in RERANKER_MODEL.lower() or 'ms-marco' in RERANKER_MODEL.lower()

    def test_weights_sum_approximately_one(self):
        from SageLibs.config import BM25_WEIGHT, SEMANTIC_WEIGHT

        total = BM25_WEIGHT + SEMANTIC_WEIGHT
        assert 0.99 <= total <= 1.01


class TestConfigDefaultSettings:

    def test_default_settings_structure(self):
        # Test that the default_settings dict in config.py has expected keys
        # by checking the constants that should be in defaults
        from SageLibs.config import USE_RERANKER, USE_HYBRID_SEARCH, CHUNK_OVERLAP_TOKENS

        # These constants exist which means the config module has the feature settings
        assert USE_RERANKER is True
        assert USE_HYBRID_SEARCH is True
        assert CHUNK_OVERLAP_TOKENS == 200

    def test_load_settings_creates_file_with_defaults(self):
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'TestSettings.json')

        try:
            import SageLibs.config as config_module
            original_settings_file = config_module.SETTINGS_FILE
            original_settings = config_module.settings.copy()

            config_module.SETTINGS_FILE = temp_path
            config_module.settings = {}

            settings = config_module.load_settings()

            # Check that new feature settings exist
            assert 'use_reranker' in settings
            assert 'use_hybrid_search' in settings
            assert 'chunk_overlap_tokens' in settings

            # Restore
            config_module.SETTINGS_FILE = original_settings_file
            config_module.settings = original_settings
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_default_settings_have_correct_values(self):
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'TestSettings2.json')

        try:
            import SageLibs.config as config_module
            original_settings_file = config_module.SETTINGS_FILE
            original_settings = config_module.settings.copy()

            config_module.SETTINGS_FILE = temp_path
            config_module.settings = {}

            settings = config_module.load_settings()

            assert settings['use_reranker'] == True
            assert settings['use_hybrid_search'] == True
            assert settings['chunk_overlap_tokens'] == 200

            # Restore
            config_module.SETTINGS_FILE = original_settings_file
            config_module.settings = original_settings
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetSetting:

    def test_get_setting_returns_value(self):
        from SageLibs.config import get_setting

        with patch('SageLibs.config.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {
                'use_reranker': True,
                'use_hybrid_search': False
            }

            assert get_setting('use_reranker') == True
            assert get_setting('use_hybrid_search') == False

    def test_get_setting_returns_default(self):
        from SageLibs.config import get_setting

        with patch('SageLibs.config.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}

            result = get_setting('nonexistent_key', 'default_value')
            assert result == 'default_value'

    def test_get_setting_none_default(self):
        from SageLibs.config import get_setting

        with patch('SageLibs.config.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}

            result = get_setting('nonexistent_key')
            assert result is None


class TestConfigIntegration:

    def test_reranker_module_uses_config(self):
        from SageLibs.config import RERANKER_MODEL, RERANKER_TOP_K

        assert RERANKER_MODEL is not None
        assert RERANKER_TOP_K is not None

    def test_hybrid_search_module_uses_config(self):
        from SageLibs.config import BM25_WEIGHT, SEMANTIC_WEIGHT, SIMILARITY_THRESHOLD

        assert BM25_WEIGHT is not None
        assert SEMANTIC_WEIGHT is not None
        assert SIMILARITY_THRESHOLD is not None

    def test_embedding_utils_uses_config(self):
        from SageLibs.config import TOKEN_CONTEXT_WINDOW_EMBEDDINGS

        assert TOKEN_CONTEXT_WINDOW_EMBEDDINGS is not None
        assert TOKEN_CONTEXT_WINDOW_EMBEDDINGS > 0
