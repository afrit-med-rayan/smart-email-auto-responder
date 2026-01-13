"""
Train Generative Model (T5/FLAN-T5)

Fine-tunes a Seq2Seq model for email response generation.
Input: <urgency> <intent> <context (optional)> Email Body
Target: Reply Draft
"""

import argparse
import logging
import json
import os
import nltk
import numpy as np
from typing import Dict, List
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
import evaluate

# Ensure nltk resources
try:
    nltk.data.find("tokenizers/punkt")
except (LookupError, OSError):
    nltk.download("punkt", quiet=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(data_file: str) -> List[Dict]:
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_metrics(eval_pred, tokenizer):
    metric = evaluate.load("rouge")
    
    predictions, labels = eval_pred
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    
    # Replace -100 in the labels as we can't decode them.
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # Rouge expects a newline after each sentence (Simple split by period for robustness)
    decoded_preds = ["\n".join(pred.strip().split('.')) for pred in decoded_preds]
    decoded_labels = ["\n".join(label.strip().split('.')) for label in decoded_labels]
    
    result = metric.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
    
    return {k: round(v * 100, 4) for k, v in result.items()}

def main():
    parser = argparse.ArgumentParser(description="Train T5 Generator")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Data directory")
    parser.add_argument("--output_dir", type=str, default="models/generator", help="Output directory")
    parser.add_argument("--model_name", type=str, default="google/flan-t5-small", help="Base model")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    args = parser.parse_args()

    logger.info(f"Starting T5 training from {args.model_name}")

    # 1. Load Data
    train_data = load_data(os.path.join(args.data_dir, "train.json"))
    val_data = load_data(os.path.join(args.data_dir, "validation.json"))

    # 2. Prepare Inputs
    # We construct a prompt-like input string for T5
    def preprocess_function(examples):
        inputs = []
        targets = []
        
        for doc in examples["data"]:
            # Input Format: "write email: <intent> <urgency> Context: <body>"
            # Note: In a real scenario, body is the received email, target is the reply.
            # Our synthetic generator produced ONE text. 
            # For Training purposes, if we only have the 'text' (the generated email), 
            # we might want to train the model to Generate the email given the Intent/Metadata.
            # OR if we had pairs (Received -> Reply).
            # Current Synthetic Data: Text IS the generated email.
            # Task: Generate this email given the metadata.
            
            prompt = f"write email: {doc['label_intent']} urgency: {doc['label_urgency']}"
            inputs.append(prompt)
            targets.append(doc["text"])
            
        model_inputs = tokenizer(inputs, max_length=512, truncation=True)
        labels = tokenizer(targets, max_length=512, truncation=True)

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    # Convert to HF Dataset (trick to pass list of dicts)
    hf_train = Dataset.from_dict({"data": train_data})
    hf_val = Dataset.from_dict({"data": val_data})
    
    dataset = DatasetDict({"train": hf_train, "validation": hf_val})

    # 3. Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    tokenized_datasets = dataset.map(
        preprocess_function, 
        batched=True, 
        remove_columns=["data"]
    )

    # 4. Model
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name)
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # 5. Trainer
    save_path = args.output_dir
    
    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(save_path, "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        weight_decay=0.01,
        save_total_limit=2,
        num_train_epochs=args.epochs,
        predict_with_generate=True,
        fp16=False, # Set True if GPU available
        logging_dir=os.path.join(save_path, "logs"),
        logging_steps=10,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda eval_pred: compute_metrics(eval_pred, tokenizer),
    )

    # 6. Train
    logger.info("Starting training...")
    trainer.train()

    # 7. Save
    logger.info(f"Saving model to {save_path}")
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)

if __name__ == "__main__":
    main()
