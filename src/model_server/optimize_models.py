"""
Script to Create Quantized Model Variants
"""

import argparse
import logging
from src.model_server.quantization import ModelQuantizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OptimizeModels")

def main():
    parser = argparse.ArgumentParser(description="Create quantized model variants")
    parser.add_argument("--quantization", type=str, default="all", 
                        choices=["8bit", "4bit", "onnx-int8", "all"],
                        help="Quantization level")
    parser.add_argument("--models", type=str, default="all",
                        help="Comma-separated list of models (or 'all')")
    args = parser.parse_args()
    
    quantizer = ModelQuantizer()
    
    levels = []
    if args.quantization == "all":
        levels = ["8bit", "4bit", "onnx-int8"]
    else:
        levels = [args.quantization]
        
    for level in levels:
        logger.info(f"Starting {level} quantization...")
        results = quantizer.quantize_all_models(level)
        logger.info(f"Results for {level}: {results}")
        
    # Print size comparison
    logger.info("\n--- Size Comparison ---")
    models = ["intent_classifier", "urgency_detector", "sentiment_analyzer"]
    for model in models:
        try:
            sizes = quantizer.compare_model_sizes(model)
            logger.info(f"{model}: {sizes}")
        except Exception as e:
            logger.warning(f"Could not get sizes for {model}: {e}")

if __name__ == "__main__":
    main()
