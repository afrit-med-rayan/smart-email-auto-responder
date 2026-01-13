"""
Unified Training Script for Email Classification

Fine-tunes a transformer model (DistilBERT) for a specific classification task.
Label targets: 'label_intent', 'label_urgency', 'label_sentiment'.

Usage:
    python src/training/train_classifier.py --target label_intent --epochs 3
"""

import argparse
import logging
import json
import os
import numpy as np
from typing import Dict, List, Any
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding
)
import evaluate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(data_file: str) -> List[Dict]:
    """Load JSON data."""
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_metrics(eval_pred):
    """Compute accuracy and f1."""
    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")
    
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    accuracy = accuracy_metric.compute(predictions=predictions, references=labels)
    f1 = f1_metric.compute(predictions=predictions, references=labels, average="weighted")
    
    return {**accuracy, **f1}

def main():
    parser = argparse.ArgumentParser(description="Train Email Classifier")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Directory containing train/val/test.json")
    parser.add_argument("--output_dir", type=str, default="models", help="Output directory for saved models")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base model")
    parser.add_argument("--target", type=str, required=True, choices=["label_intent", "label_urgency", "label_sentiment"], help="Target label to train on")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    args = parser.parse_args()

    logger.info(f"Starting training for target: {args.target}")
    
    # 1. Load Data
    train_data = load_data(os.path.join(args.data_dir, "train.json"))
    val_data = load_data(os.path.join(args.data_dir, "validation.json"))
    
    # 2. Extract Labels and Create Mappings
    all_labels = set(item[args.target] for item in train_data)
    label2id = {label: i for i, label in enumerate(sorted(all_labels))}
    id2label = {i: label for label, i in label2id.items()}
    
    logger.info(f"Found {len(all_labels)} labels: {all_labels}")
    
    # 3. Create HuggingFace Datasets
    # Filter only necessary columns
    def format_dataset(data):
        return [
            {"text": item["text"], "label": label2id[item[args.target]]} 
            for item in data
        ]

    hf_train = Dataset.from_list(format_dataset(train_data))
    hf_val = Dataset.from_list(format_dataset(val_data))
    
    dataset = DatasetDict({"train": hf_train, "validation": hf_val})

    # 4. Tokenization
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
    
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # 5. Initialize Model
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, 
        num_labels=len(all_labels),
        id2label=id2label,
        label2id=label2id
    )

    # 6. Setup Trainer
    save_path = os.path.join(args.output_dir, args.target.replace("label_", ""))
    
    training_args = TrainingArguments(
        output_dir=os.path.join(save_path, "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        logging_dir=os.path.join(save_path, "logs"),
        logging_steps=10,
        use_cpu=False # Auto-detects GPU
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # 7. Train
    logger.info("Starting training loop...")
    trainer.train()
    
    # 8. Save Final Model
    logger.info(f"Saving model to {save_path}")
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)
    
    # Save metrics
    metrics = trainer.evaluate()
    with open(os.path.join(save_path, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    main()
