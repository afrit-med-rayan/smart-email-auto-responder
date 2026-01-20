"""
Model Quantization Script

Generates quantized versions of all classification models.
Supports 8-bit and 4-bit quantization for deployment optimization.

Usage:
    python scripts/quantize_models.py --quantization 8bit
    python scripts/quantize_models.py --quantization 4bit --models intent_classifier urgency_detector
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model_server.quantization import ModelQuantizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Quantize models for deployment")
    parser.add_argument(
        "--quantization",
        type=str,
        choices=["8bit", "4bit"],
        default="8bit",
        help="Quantization level (default: 8bit)"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["intent_classifier", "urgency_detector", "sentiment_analyzer"],
        help="Models to quantize (default: all classification models)"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models",
        help="Directory containing models (default: models)"
    )
    parser.add_argument(
        "--compare-sizes",
        action="store_true",
        help="Compare sizes after quantization"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting {args.quantization} quantization")
    logger.info(f"Models to quantize: {args.models}")
    
    # Initialize quantizer
    quantizer = ModelQuantizer(models_dir=args.models_dir)
    
    # Quantize each model
    results = {}
    for model_name in args.models:
        logger.info(f"\n{'='*60}")
        logger.info(f"Quantizing {model_name}...")
        logger.info(f"{'='*60}")
        
        model_path = Path(args.models_dir) / model_name
        output_path = Path(args.models_dir) / f"{model_name}_{args.quantization}"
        
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            results[model_name] = "not_found"
            continue
        
        success = quantizer.quantize_model(
            str(model_path),
            str(output_path),
            args.quantization
        )
        
        results[model_name] = "success" if success else "failed"
        
        if success and args.compare_sizes:
            sizes = quantizer.compare_model_sizes(model_name)
            logger.info(f"\nSize comparison for {model_name}:")
            logger.info(f"  Original: {sizes['original']}")
            logger.info(f"  {args.quantization}: {sizes[args.quantization]}")
            logger.info(f"  Reduction: {sizes[f'{args.quantization}_reduction']}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("Quantization Summary")
    logger.info(f"{'='*60}")
    
    for model_name, status in results.items():
        status_symbol = "✓" if status == "success" else "✗"
        logger.info(f"{status_symbol} {model_name}: {status}")
    
    # Overall statistics
    success_count = sum(1 for s in results.values() if s == "success")
    total_count = len(results)
    
    logger.info(f"\nTotal: {success_count}/{total_count} models quantized successfully")
    
    if success_count < total_count:
        logger.warning("Some models failed to quantize. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All models quantized successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
