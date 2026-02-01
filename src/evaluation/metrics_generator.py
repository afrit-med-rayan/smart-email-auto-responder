"""
Generation Metrics Evaluation
"""
import json
import os
import argparse
import logging
from evaluate import load
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(data_file: str):
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_generation_metrics(predictions, references):
    """
    Compute BLEU, ROUGE, BERTScore.
    """
    # Load metrics
    try:
        bertscore = load("bertscore")
        rouge = load("rouge")
        bleu = load("bleu")
        
        # Compute BERTScore
        logger.info("Computing BERTScore...")
        bert_results = bertscore.compute(predictions=predictions, references=references, lang="en")
        
        # Compute ROUGE
        logger.info("Computing ROUGE...")
        rouge_results = rouge.compute(predictions=predictions, references=references)
        
        # Compute BLEU
        logger.info("Computing BLEU...")
        bleu_results = bleu.compute(predictions=predictions, references=references)
        
        return {
            "bertscore_f1": np.mean(bert_results['f1']),
            "rouge1": rouge_results['rouge1'],
            "rouge2": rouge_results['rouge2'],
            "rougeL": rouge_results['rougeL'],
            "bleu": bleu_results['bleu']
        }
    except Exception as e:
        logger.error(f"Failed to load or compute metrics: {e}")
        return {
            "bertscore_f1": 0.0,
            "rouge1": 0.0,
            "rouge2": 0.0,
            "rougeL": 0.0,
            "bleu": 0.0
        }

def main():
    parser = argparse.ArgumentParser(description="Evaluate Generator")
    parser.add_argument("--data_path", type=str, default="data/processed/test.json", help="Path to test data")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory to save results")
    parser.add_argument("--mock", action="store_true", help="Use mock predictions")
    args = parser.parse_args()

    os.makedirs(args.results_dir, exist_ok=True)
    
    logger.info(f"Loading data from {args.data_path}")
    if not os.path.exists(args.data_path):
        logger.error("Data file not found!")
        return

    data = load_data(args.data_path)
    
    # Expected text (references)
    references = [item["text"] for item in data]
    
    # Predictions
    if args.mock:
        # Simulate predictions by slightly modifying references
        predictions = [ref + " [generated]" for ref in references]
    else:
        logger.warning("Actual inference not implemented. Using mock predictions.")
        predictions = [ref + "." for ref in references] # Dummy modification

    metrics = compute_generation_metrics(predictions, references)
    
    logger.info(f"Generation Metrics: {metrics}")

    output_file = os.path.join(args.results_dir, "generation_metrics.json")
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
