"""
Model Quantization Utilities

Provides 8-bit and 4-bit quantization for model optimization.
Reduces model size and improves inference speed with minimal accuracy loss.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Literal
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

QuantizationLevel = Literal["none", "8bit", "4bit"]


class ModelQuantizer:
    """Handles model quantization for deployment optimization."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        
    def quantize_model(
        self,
        model_path: str,
        output_path: str,
        quantization: QuantizationLevel = "8bit"
    ) -> bool:
        """
        Quantize a model to reduce size and improve inference speed.
        
        Args:
            model_path: Path to the original model
            output_path: Path to save quantized model
            quantization: Quantization level ("8bit" or "4bit")
            
        Returns:
            True if quantization successful, False otherwise
        """
        if quantization == "none":
            logger.info("No quantization requested")
            return False
            
        try:
            logger.info(f"Loading model from {model_path} for {quantization} quantization")
            
            # Load model with quantization config
            if quantization == "8bit":
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_path,
                    load_in_8bit=True,
                    device_map="auto"
                )
            elif quantization == "4bit":
                from transformers import BitsAndBytesConfig
                
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_path,
                    quantization_config=quantization_config,
                    device_map="auto"
                )
            else:
                raise ValueError(f"Unsupported quantization level: {quantization}")
            
            # Save quantized model
            os.makedirs(output_path, exist_ok=True)
            model.save_pretrained(output_path)
            
            # Copy tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            tokenizer.save_pretrained(output_path)
            
            logger.info(f"Successfully quantized model to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Quantization failed: {e}", exc_info=True)
            return False
    
    def quantize_all_models(
        self,
        quantization: QuantizationLevel = "8bit"
    ) -> dict:
        """
        Quantize all classification models.
        
        Args:
            quantization: Quantization level to apply
            
        Returns:
            Dictionary with quantization results
        """
        results = {}
        
        models_to_quantize = [
            "intent_classifier",
            "urgency_detector",
            "sentiment_analyzer"
        ]
        
        for model_name in models_to_quantize:
            model_path = self.models_dir / model_name
            output_path = self.models_dir / f"{model_name}_{quantization}"
            
            if not model_path.exists():
                logger.warning(f"Model not found: {model_path}")
                results[model_name] = "not_found"
                continue
            
            success = self.quantize_model(
                str(model_path),
                str(output_path),
                quantization
            )
            
            results[model_name] = "success" if success else "failed"
        
        return results
    
    def get_model_size(self, model_path: str) -> float:
        """
        Calculate total size of model directory in MB.
        
        Args:
            model_path: Path to model directory
            
        Returns:
            Size in megabytes
        """
        total_size = 0
        model_dir = Path(model_path)
        
        if not model_dir.exists():
            return 0.0
        
        for file in model_dir.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def compare_model_sizes(self, model_name: str) -> dict:
        """
        Compare sizes of original and quantized models.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with size comparisons
        """
        original_path = self.models_dir / model_name
        quantized_8bit_path = self.models_dir / f"{model_name}_8bit"
        quantized_4bit_path = self.models_dir / f"{model_name}_4bit"
        
        original_size = self.get_model_size(str(original_path))
        size_8bit = self.get_model_size(str(quantized_8bit_path))
        size_4bit = self.get_model_size(str(quantized_4bit_path))
        
        return {
            "original": f"{original_size:.2f} MB",
            "8bit": f"{size_8bit:.2f} MB" if size_8bit > 0 else "N/A",
            "4bit": f"{size_4bit:.2f} MB" if size_4bit > 0 else "N/A",
            "8bit_reduction": f"{((original_size - size_8bit) / original_size * 100):.1f}%" if size_8bit > 0 else "N/A",
            "4bit_reduction": f"{((original_size - size_4bit) / original_size * 100):.1f}%" if size_4bit > 0 else "N/A"
        }


if __name__ == "__main__":
    # Example usage
    quantizer = ModelQuantizer()
    
    # Quantize all models to 8-bit
    results = quantizer.quantize_all_models("8bit")
    print("8-bit Quantization Results:", results)
    
    # Compare sizes
    for model in ["intent_classifier", "urgency_detector", "sentiment_analyzer"]:
        sizes = quantizer.compare_model_sizes(model)
        print(f"\n{model} sizes:", sizes)
