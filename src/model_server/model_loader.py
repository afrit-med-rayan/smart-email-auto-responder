"""
Centralized Model Loader

Handles lazy loading, caching, and management of all models.
Supports quantized model variants and device selection.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from functools import lru_cache
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    AutoModel,
    T5ForConditionalGeneration
)

logger = logging.getLogger(__name__)

DeviceType = Literal["cpu", "cuda", "auto"]
QuantizationLevel = Literal["none", "8bit", "4bit"]


class ModelLoader:
    """Centralized model loading with caching and optimization."""
    
    def __init__(
        self,
        models_dir: str = "models",
        device: DeviceType = "auto",
        quantization: QuantizationLevel = "none"
    ):
        self.models_dir = Path(models_dir)
        self.device = self._get_device(device)
        self.quantization = quantization
        self._model_cache: Dict[str, Any] = {}
        self._tokenizer_cache: Dict[str, Any] = {}
        
        logger.info(f"ModelLoader initialized - Device: {self.device}, Quantization: {quantization}")
    
    def _get_device(self, device: DeviceType) -> str:
        """Determine the device to use for inference."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _get_model_path(self, model_name: str) -> Path:
        """Get the path for a model, considering quantization."""
        if self.quantization != "none":
            quantized_path = self.models_dir / f"{model_name}_{self.quantization}"
            if quantized_path.exists():
                logger.info(f"Using {self.quantization} quantized model: {quantized_path}")
                return quantized_path
            else:
                logger.warning(f"Quantized model not found, falling back to original: {model_name}")
        
        return self.models_dir / model_name
    
    def load_classification_model(
        self,
        model_name: str,
        num_labels: Optional[int] = None
    ) -> tuple:
        """
        Load a classification model and tokenizer.
        
        Args:
            model_name: Name of the model directory
            num_labels: Number of classification labels (optional)
            
        Returns:
            Tuple of (model, tokenizer)
        """
        cache_key = f"{model_name}_{self.quantization}"
        
        # Check cache
        if cache_key in self._model_cache:
            logger.info(f"Loading {model_name} from cache")
            return self._model_cache[cache_key], self._tokenizer_cache[cache_key]
        
        model_path = self._get_model_path(model_name)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            logger.info(f"Loading classification model: {model_path}")
            
            # Load with quantization if specified
            load_kwargs = {"device_map": "auto"} if self.device == "cuda" else {}
            
            if self.quantization == "8bit":
                load_kwargs["load_in_8bit"] = True
            elif self.quantization == "4bit":
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                **load_kwargs
            )
            
            if self.quantization == "none" and self.device == "cpu":
                model = model.to(self.device)
            
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            
            # Cache the model and tokenizer
            self._model_cache[cache_key] = model
            self._tokenizer_cache[cache_key] = tokenizer
            
            logger.info(f"Successfully loaded {model_name}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
            raise
    
    def load_generation_model(
        self,
        model_name: str = "text_generator"
    ) -> tuple:
        """
        Load a text generation model (T5).
        
        Args:
            model_name: Name of the model directory
            
        Returns:
            Tuple of (model, tokenizer)
        """
        cache_key = f"{model_name}_gen_{self.quantization}"
        
        if cache_key in self._model_cache:
            logger.info(f"Loading {model_name} from cache")
            return self._model_cache[cache_key], self._tokenizer_cache[cache_key]
        
        model_path = self._get_model_path(model_name)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            logger.info(f"Loading generation model: {model_path}")
            
            load_kwargs = {}
            if self.device == "cuda":
                load_kwargs["device_map"] = "auto"
            
            model = T5ForConditionalGeneration.from_pretrained(
                str(model_path),
                **load_kwargs
            )
            
            if self.device == "cpu":
                model = model.to(self.device)
            
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            
            self._model_cache[cache_key] = model
            self._tokenizer_cache[cache_key] = tokenizer
            
            logger.info(f"Successfully loaded {model_name}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load generation model: {e}", exc_info=True)
            raise
    
    def load_embedding_model(
        self,
        model_name: str = "embeddings"
    ) -> tuple:
        """
        Load an embedding model (sentence-transformers).
        
        Args:
            model_name: Name of the model directory
            
        Returns:
            Tuple of (model, tokenizer)
        """
        cache_key = f"{model_name}_emb"
        
        if cache_key in self._model_cache:
            return self._model_cache[cache_key], self._tokenizer_cache[cache_key]
        
        model_path = self._get_model_path(model_name)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            logger.info(f"Loading embedding model: {model_path}")
            
            model = AutoModel.from_pretrained(str(model_path))
            model = model.to(self.device)
            
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            
            self._model_cache[cache_key] = model
            self._tokenizer_cache[cache_key] = tokenizer
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            raise
    
    def preload_all_models(self):
        """Preload all models to warm up the cache."""
        logger.info("Preloading all models...")
        
        models_to_load = [
            ("intent_classifier", "classification"),
            ("urgency_detector", "classification"),
            ("sentiment_analyzer", "classification"),
            ("text_generator", "generation"),
            ("embeddings", "embedding")
        ]
        
        for model_name, model_type in models_to_load:
            try:
                if model_type == "classification":
                    self.load_classification_model(model_name)
                elif model_type == "generation":
                    self.load_generation_model(model_name)
                elif model_type == "embedding":
                    self.load_embedding_model(model_name)
            except Exception as e:
                logger.warning(f"Could not preload {model_name}: {e}")
        
        logger.info(f"Preloaded {len(self._model_cache)} models")
    
    def clear_cache(self):
        """Clear the model cache to free memory."""
        logger.info("Clearing model cache")
        self._model_cache.clear()
        self._tokenizer_cache.clear()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_cache_info(self) -> dict:
        """Get information about cached models."""
        return {
            "cached_models": list(self._model_cache.keys()),
            "cache_size": len(self._model_cache),
            "device": self.device,
            "quantization": self.quantization
        }


# Global model loader instance
_global_loader: Optional[ModelLoader] = None


def get_model_loader(
    models_dir: str = "models",
    device: DeviceType = "auto",
    quantization: QuantizationLevel = "none"
) -> ModelLoader:
    """Get or create the global model loader instance."""
    global _global_loader
    
    # Load defaults from config if not specified/overridden
    if _global_loader is None:
        from src.config_loader import config
        
        # Use config defaults if arguments match the default function signature (which are effectively placeholders here)
        # Note: In a cleaner design, we might pass None as defaults to distinguish.
        # Here we'll just check if the global config has values and use them if we are creating the loader.
        
        cfg_device = config.inference.device if config.inference else "auto"
        cfg_quant = config.inference.quantization if config.inference else "none"
        
        # Priority: Argument > Config > Default
        final_device = device if device != "auto" else (cfg_device or "auto")
        final_quant = quantization if quantization != "none" else (cfg_quant or "none")
        
        _global_loader = ModelLoader(models_dir, final_device, final_quant)
    
    return _global_loader


if __name__ == "__main__":
    # Example usage
    loader = ModelLoader(device="cpu", quantization="none")
    
    # Load a classification model
    model, tokenizer = loader.load_classification_model("intent_classifier")
    print(f"Loaded model on device: {next(model.parameters()).device}")
    
    # Get cache info
    print("Cache info:", loader.get_cache_info())
