"""
Unit tests for config_loader module.

Tests configuration loading, environment variable handling, and fallback behavior.
"""

import os
import pytest
from unittest.mock import patch, mock_open
from src.config_loader import SimpleConfig, load_config, DEFAULT_CONFIG


class TestSimpleConfig:
    """Test SimpleConfig class functionality."""
    
    def test_init_with_flat_dict(self) -> None:
        """Test initialization with flat dictionary."""
        config = SimpleConfig(key1="value1", key2="value2")
        assert config.key1 == "value1"
        assert config.key2 == "value2"
    
    def test_init_with_nested_dict(self) -> None:
        """Test initialization with nested dictionary."""
        config = SimpleConfig(
            level1={
                "level2": {
                    "key": "value"
                }
            }
        )
        assert isinstance(config.level1, SimpleConfig)
        assert isinstance(config.level1.level2, SimpleConfig)
        assert config.level1.level2.key == "value"
    
    def test_get_method_existing_key(self) -> None:
        """Test get method with existing key."""
        config = SimpleConfig(existing="value")
        assert config.get("existing") == "value"
    
    def test_get_method_missing_key_with_default(self) -> None:
        """Test get method with missing key and default value."""
        config = SimpleConfig(existing="value")
        assert config.get("missing", "default") == "default"
    
    def test_get_method_missing_key_no_default(self) -> None:
        """Test get method with missing key and no default."""
        config = SimpleConfig(existing="value")
        assert config.get("missing") is None
    
    def test_getitem_method(self) -> None:
        """Test __getitem__ method."""
        config = SimpleConfig(key="value")
        assert config["key"] == "value"
    
    def test_getattr_missing_attribute(self) -> None:
        """Test __getattr__ with missing attribute returns None."""
        config = SimpleConfig(existing="value")
        assert config.missing is None


class TestLoadConfig:
    """Test load_config function."""
    
    @patch("src.config_loader.HAS_YAML", True)
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="models:\n  intent_classifier:\n    name: custom-model\n")
    @patch("yaml.safe_load")
    def test_load_config_from_yaml(
        self, 
        mock_yaml_load: pytest.Mock,
        mock_file: pytest.Mock,
        mock_exists: pytest.Mock
    ) -> None:
        """Test loading configuration from YAML file."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "models": {
                "intent_classifier": {
                    "name": "custom-model"
                }
            }
        }
        
        config = load_config("test_config.yaml")
        
        assert isinstance(config, SimpleConfig)
        mock_exists.assert_called_once_with("test_config.yaml")
        mock_yaml_load.assert_called_once()
    
    @patch("src.config_loader.HAS_YAML", True)
    @patch("os.path.exists")
    def test_load_config_file_not_found(self, mock_exists: pytest.Mock) -> None:
        """Test loading configuration when file doesn't exist."""
        mock_exists.return_value = False
        
        config = load_config("nonexistent.yaml")
        
        assert isinstance(config, SimpleConfig)
        # Should fall back to defaults
        assert hasattr(config, "models")
    
    @patch("src.config_loader.HAS_YAML", False)
    def test_load_config_without_yaml_library(self) -> None:
        """Test loading configuration when YAML library is not available."""
        config = load_config()
        
        assert isinstance(config, SimpleConfig)
        # Should use defaults
        assert hasattr(config, "models")
    
    @patch.dict(os.environ, {
        "GMAIL_CLIENT_ID": "test_client_id",
        "GMAIL_CLIENT_SECRET": "test_secret",
        "USER_NAME": "TestUser",
        "USER_EMAIL": "test@example.com"
    })
    @patch("src.config_loader.HAS_YAML", False)
    def test_load_config_with_env_vars(self) -> None:
        """Test loading configuration with environment variables."""
        config = load_config()
        
        assert config.gmail_client_id == "test_client_id"
        assert config.gmail_client_secret == "test_secret"
        assert config.user_name == "TestUser"
        assert config.user_email == "test@example.com"
    
    @patch("src.config_loader.HAS_YAML", False)
    def test_load_config_default_values(self) -> None:
        """Test that default configuration values are present."""
        config = load_config()
        
        # Check models configuration
        assert hasattr(config, "models")
        assert hasattr(config.models, "intent_classifier")
        assert config.models.intent_classifier.name == "distilbert-base-uncased"
        
        # Check thresholds
        assert hasattr(config, "thresholds")
        assert hasattr(config.thresholds, "confidence")
        assert config.thresholds.confidence.default == 0.75
        
        # Check paths
        assert hasattr(config, "paths")
        assert config.paths.data_dir == "data"
        assert config.paths.models_dir == "models"
    
    @patch("src.config_loader.HAS_YAML", True)
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_config_yaml_parse_error(
        self,
        mock_yaml_load: pytest.Mock,
        mock_file: pytest.Mock,
        mock_exists: pytest.Mock,
        capsys: pytest.CaptureFixture
    ) -> None:
        """Test handling of YAML parse errors."""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = Exception("YAML parse error")
        
        config = load_config("bad_config.yaml")
        
        # Should still return a config object with defaults
        assert isinstance(config, SimpleConfig)
        
        # Check that warning was printed
        captured = capsys.readouterr()
        assert "Warning: Failed to parse config file" in captured.out
    
    @patch("src.config_loader.HAS_YAML", True)
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_config_yaml_returns_none(
        self,
        mock_yaml_load: pytest.Mock,
        mock_file: pytest.Mock,
        mock_exists: pytest.Mock
    ) -> None:
        """Test handling when YAML returns None."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = None
        
        config = load_config("empty_config.yaml")
        
        # Should handle None gracefully and use defaults
        assert isinstance(config, SimpleConfig)
        assert hasattr(config, "models")


class TestDefaultConfig:
    """Test DEFAULT_CONFIG dictionary."""
    
    def test_default_config_structure(self) -> None:
        """Test that DEFAULT_CONFIG has expected structure."""
        assert "models" in DEFAULT_CONFIG
        assert "thresholds" in DEFAULT_CONFIG
        assert "generation" in DEFAULT_CONFIG
        assert "paths" in DEFAULT_CONFIG
        assert "inference" in DEFAULT_CONFIG
    
    def test_default_config_models(self) -> None:
        """Test models configuration in DEFAULT_CONFIG."""
        models = DEFAULT_CONFIG["models"]
        assert "intent_classifier" in models
        assert "sentiment_analyzer" in models
        assert "text_generator" in models
        assert "embeddings" in models
    
    def test_default_config_thresholds(self) -> None:
        """Test thresholds configuration in DEFAULT_CONFIG."""
        thresholds = DEFAULT_CONFIG["thresholds"]
        assert "confidence" in thresholds
        assert "urgency" in thresholds
        
        # Check confidence thresholds
        confidence = thresholds["confidence"]
        assert confidence["academic"] == 0.80
        assert confidence["default"] == 0.75
        
        # Check urgency thresholds
        urgency = thresholds["urgency"]
        assert urgency["critical"] == 0.90
        assert urgency["low"] == 0.60
