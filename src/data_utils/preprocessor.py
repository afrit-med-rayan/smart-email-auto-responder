"""
Data Preprocessor for Training

Prepares raw dataset files for ML model training.
- Splitting (Train/Val/Test)
- Cleaning
- Tokenization preparation (saving texts handling)
"""

import json
import os
import random
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class TrainingDataPreprocessor:
    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def load_data(self, filename: str) -> List[Dict]:
        """Load raw JSON data."""
        path = os.path.join(self.input_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return []

    def split_data(self, data: List[Dict], split_ratio: Tuple[float, float, float] = (0.8, 0.1, 0.1)):
        """Split data into train, validation, and test sets."""
        random.shuffle(data)
        n = len(data)
        train_end = int(n * split_ratio[0])
        val_end = train_end + int(n * split_ratio[1])
        
        train = data[:train_end]
        val = data[train_end:val_end]
        test = data[val_end:]
        
        return train, val, test

    def save_split(self, data: List[Dict], split_name: str):
        """Save a data split to processed directory."""
        path = os.path.join(self.output_dir, f"{split_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} samples to {path}")

    def process_pipeline(self, filename: str):
        """Run full preprocessing pipeline."""
        print(f"Processing {filename}...")
        raw_data = self.load_data(filename)
        
        if not raw_data:
            print("No data found.")
            return

        # Simple cleaning (example)
        clean_data = []
        for entry in raw_data:
            if entry.get("text") and len(entry["text"]) > 5:
                # Add any specific cleaning logic here
                clean_data.append(entry)
        
        train, val, test = self.split_data(clean_data)
        
        self.save_split(train, "train")
        self.save_split(val, "validation")
        self.save_split(test, "test")
        
        print("Preprocessing complete.")

if __name__ == "__main__":
    processor = TrainingDataPreprocessor()
    # success if file exists, else it will print error
    processor.process_pipeline("synthetic_dataset.json")
