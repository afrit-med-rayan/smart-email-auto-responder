"""
Script to Benchmark Model Performance
"""

import argparse
import logging
import time
import torch
import numpy as np
from typing import List
from src.model_server.model_loader import get_model_loader
from src.model_server.inference import InferenceEngine, ONNXInferenceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BenchmarkModels")

def benchmark_model(model_name: str, quantization: str, device: str, batch_size: int):
    logger.info(f"Benchmarking {model_name} | {quantization} | {device}")
    
    try:
        # Load model
        if quantization == "onnx-int8":
             # Special handling for ONNX
             from src.config_loader import config
             models_dir = config.paths.models_dir
             import os
             onnx_path = os.path.join(models_dir, f"{model_name}_{quantization}", "model_quantized.onnx")
             
             if not os.path.exists(onnx_path):
                 logger.error(f"ONNX model not found at {onnx_path}")
                 return None
                 
             from transformers import AutoTokenizer
             # Assume tokenizer is in the same dir
             tokenizer = AutoTokenizer.from_pretrained(os.path.dirname(onnx_path))
             
             engine = ONNXInferenceEngine(onnx_path, tokenizer, device="cpu") # ONNX often faster on CPU for small batches
        
        else:
            loader = get_model_loader(quantization=quantization, device=device)
            # Force reload to ensure cleanliness
            loader.clear_cache() 
            # We need to manually set the loader's quantization if we are iterating
            loader.quantization = quantization
            loader.device = device
            
            model, tokenizer = loader.load_classification_model(model_name)
            engine = InferenceEngine(model, tokenizer, device=device, batch_size=batch_size)
        
        # Test Data
        texts = [
            "Can we reschedule our meeting?",
            "Urgent: Server down!",
            "Thank you for the update.",
            "Please remove me from this list.",
            "Meeting at 3 PM confirmed."
        ] * 10 # 50 samples
        
        # Warmup
        engine.predict_single(texts[0])
        
        # Latency Test
        start_time = time.time()
        for text in texts:
            engine.predict_single(text)
        total_time = time.time() - start_time
        avg_latency = (total_time * 1000) / len(texts)
        
        logger.info(f"Avg Latency: {avg_latency:.2f} ms")
        
        return avg_latency
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Benchmark models")
    parser.add_argument("--models", type=str, default="intent_classifier", help="Comma separated models")
    parser.add_argument("--device", type=str, default="cpu", help="Device to test (cpu/cuda)")
    args = parser.parse_args()
    
    models = args.models.split(",")
    quantizations = ["none", "8bit", "onnx-int8"]
    
    results = {}
    
    for model_name in models:
        print(f"\n--- Benchmarking {model_name} ---")
        results[model_name] = {}
        for q in quantizations:
            lat = benchmark_model(model_name, q, args.device, batch_size=1)
            results[model_name][q] = lat
            
    print("\n=== Final Results (Avg Latency ms) ===")
    print(f"{'Model':<20} {'Original':<10} {'8-bit':<10} {'ONNX-Int8':<10}")
    for m, res in results.items():
        orig = f"{res.get('none', 'N/A'):.2f}" if res.get('none') else "N/A"
        bit8 = f"{res.get('8bit', 'N/A'):.2f}" if res.get('8bit') else "N/A"
        onnx = f"{res.get('onnx-int8', 'N/A'):.2f}" if res.get('onnx-int8') else "N/A"
        print(f"{m:<20} {orig:<10} {bit8:<10} {onnx:<10}")

if __name__ == "__main__":
    main()
