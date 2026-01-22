"""
Configuration Loader

Handles loading and validation of configuration from YAML files and environment variables.
"""

import os
import json
from typing import Dict, List, Optional, Any

# Try to import external deps
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SimpleConfig:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                setattr(self, k, SimpleConfig(**v))
            else:
                setattr(self, k, v)
    
    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key):
        return getattr(self, key)

    def __getattr__(self, name):
        # Allow accessing missing attributes as None or empty dict if needed,
        # but for config strictness usually we want failures or defaults.
        # For this simple mock, let's return None or empty dict for nested
        return None

# Default Configuration Dictionary
DEFAULT_CONFIG = {
    "models": {
        "intent_classifier": {
            "name": "distilbert-base-uncased",
            "path": "models/intent_classifier", 
            "use_rules_fallback": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_length": 300
        },
        "sentiment_analyzer": {
            "name": "distilbert-base-uncased",
            "use_rules_fallback": True
        },
        "text_generator": {
            "name": "t5-small",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_length": 300
        },
        "embeddings": {
            "name": "all-MiniLM-L6-v2"
        }
    },
    "thresholds": {
        "confidence": {
            "academic": 0.80,
            "internship": 0.75,
            "meeting": 0.70,
            "support": 0.85, 
            "spam": 0.90,
            "default": 0.75
        },
        "urgency": {
            "critical": 0.90,
            "high": 0.80,
            "medium": 0.70, 
            "low": 0.60
        }
    },
    "generation": {
        "strategy": "auto",
        "fallback_chain": ["rag+llm", "llm", "template"]
    },
    "paths": {
        "data_dir": "data",
        "models_dir": "models",
        "logs_dir": "logs", 
        "templates_dir": "src/templates"
    },
    "inference": {
        "device": "auto",  # auto, cpu, cuda
        "quantization": "none",  # none, 8bit, 4bit
        "onnx_enabled": False
    }
}

def load_config(config_path: str = "config.yaml") -> Any:
    """
    Load configuration from YAML file and environment variables.
    Fallback to defaults if dependencies missing.
    """
    yaml_config = {}
    
    if HAS_YAML and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to parse config file: {e}")
            
    # Load env vars
    env_config = {
        "gmail_client_id": os.getenv("GMAIL_CLIENT_ID"),
        "gmail_client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "user_name": os.getenv("USER_NAME", "Rayan"),
        "user_email": os.getenv("USER_EMAIL"),
        "user_signature": os.getenv("USER_SIGNATURE", "Best regards,\nRayan").replace("\\n", "\n")
    }
    
    # Merge with default config (deep merge simplified)
    config_data = DEFAULT_CONFIG.copy()
    
    # Update with yaml/env
    # Note: proper deep merge needed for production, for now overwriting top keys
    # or just using defaults if YAML missing
    if yaml_config:
        config_data.update(yaml_config)
    
    # Append env vars as top level attributes
    config_data.update(env_config)
    
    return SimpleConfig(**config_data)

# Global config instance
try:
    config = load_config()
except Exception as e:
    print(f"Error loading config: {e}")
    config = SimpleConfig(**DEFAULT_CONFIG)
