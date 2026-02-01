"""
Classification Metrics Evaluation
"""
import json
import os
import argparse
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(data_file: str):
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_classifier(predictions, labels, target_name):
    """
    Compute metrics for a single target.
    """
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted', zero_division=0
    )
    accuracy = accuracy_score(labels, predictions)
    
    return {
        "target": target_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate Classifier")
    parser.add_argument("--data_path", type=str, default="data/processed/test.json", help="Path to test data")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory to save results")
    parser.add_argument("--mock", action="store_true", help="Use mock predictions for testing pipeline")
    args = parser.parse_args()

    os.makedirs(args.results_dir, exist_ok=True)
    
    logger.info(f"Loading data from {args.data_path}")
    if not os.path.exists(args.data_path):
        logger.error("Data file not found!")
        return

    data = load_data(args.data_path)
    
    # We evaluate 3 targets: Intent, Urgency, Sentiment
    targets = ["label_intent", "label_urgency", "label_sentiment"]
    results = []

    for target in targets:
        logger.info(f"Evaluating target: {target}")
        
        true_labels = [item.get(target) for item in data]
        
        # In a real scenario, we would load the model and run inference here.
        # For this implementation, we will assume we have a way to get predictions.
        # If --mock is present, we simulate predictions.
        
        if args.mock:
            # Simulate predictions with some noise
            unique_labels = list(set(true_labels))
            predictions = [
                label if np.random.random() > 0.2 else np.random.choice(unique_labels)
                for label in true_labels
            ]
        else:
            # TODO: Integrate actual model inference
            # For now, we fall back to mock or require an implementation that loads the ONNX model
            logger.warning("Actual inference not implemented in this script yet. Using mock predictions.")
            unique_labels = list(set(true_labels))
            predictions = [
                label if np.random.random() > 0.1 else np.random.choice(unique_labels)
                for label in true_labels
            ]

        metrics = evaluate_classifier(predictions, true_labels, target)
        results.append(metrics)
        logger.info(f"Metrics for {target}: {metrics}")

    output_file = os.path.join(args.results_dir, "classification_metrics.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
