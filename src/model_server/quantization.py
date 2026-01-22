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
                # Save quantized model
                os.makedirs(output_path, exist_ok=True)
                model.save_pretrained(output_path)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                tokenizer.save_pretrained(output_path)
                
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
                # Save quantized model
                os.makedirs(output_path, exist_ok=True)
                model.save_pretrained(output_path)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                tokenizer.save_pretrained(output_path)

            elif quantization == "onnx-int8":
                from onnxruntime.quantization import quantize_dynamic, QuantType
                
                # First ensure base ONNX exists, if not, export it
                # For simplicity, we assume we need to export it first or it exists
                # This basic implementation exports it first using optimum or torch
                
                logger.info("Exporting to ONNX before quantization...")
                try:
                    from optimum.onnxruntime import ORTModelForSequenceClassification
                    # Load model and export
                    ort_model = ORTModelForSequenceClassification.from_pretrained(
                        model_path,
                        export=True
                    )
                    
                    # Save full precision ONNX temporarily
                    temp_onnx_dir = Path(output_path) / "temp_full_precision"
                    ort_model.save_pretrained(temp_onnx_dir)
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                    tokenizer.save_pretrained(temp_onnx_dir)
                    
                    # Quantize
                    logger.info("Quantizing ONNX model to INT8...")
                    model_file = temp_onnx_dir / "model.onnx"
                    output_model_file = Path(output_path) / "model_quantized.onnx"
                    os.makedirs(output_path, exist_ok=True)
                    
                    quantize_dynamic(
                        model_input=model_file,
                        model_output=output_model_file,
                        weight_type=QuantType.QUInt8
                    )
                    
                    tokenizer.save_pretrained(output_path)
                    
                    # Cleanup temp
                    import shutil
                    shutil.rmtree(temp_onnx_dir, ignore_errors=True)
                    
                except ImportError:
                     logger.error("optimum or onnxruntime not installed. Please install optimum[onnxruntime].")
                     raise
                
            else:
                raise ValueError(f"Unsupported quantization level: {quantization}")
            
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
        quantized_onnx_path = self.models_dir / f"{model_name}_onnx-int8"
        
        original_size = self.get_model_size(str(original_path))
        size_8bit = self.get_model_size(str(quantized_8bit_path))
        size_4bit = self.get_model_size(str(quantized_4bit_path))
        size_onnx = self.get_model_size(str(quantized_onnx_path))
        
        return {
            "original": f"{original_size:.2f} MB",
            "8bit": f"{size_8bit:.2f} MB" if size_8bit > 0 else "N/A",
            "4bit": f"{size_4bit:.2f} MB" if size_4bit > 0 else "N/A",
            "onnx-int8": f"{size_onnx:.2f} MB" if size_onnx > 0 else "N/A", 
            "8bit_reduction": f"{((original_size - size_8bit) / original_size * 100):.1f}%" if size_8bit > 0 else "N/A",
            "onnx_reduction": f"{((original_size - size_onnx) / original_size * 100):.1f}%" if size_onnx > 0 else "N/A"
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
