"""
Export Model to ONNX

Converts a fine-tuned PyTorch model to ONNX format for efficient inference.
"""

import argparse
import logging
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import onnx
import onnxruntime as ort
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_to_onnx(model_path: str, output_path: str):
    """Export PyTorch model to ONNX."""
    logger.info(f"Loading model from {model_path}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    
    # Dummy input for tracing
    dummy_text = "This is a sample email to trace the graph."
    inputs = tokenizer(dummy_text, return_tensors="pt")
    
    # Export
    logger.info(f"Exporting to {output_path}...")
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"]),
        output_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size"}
        },
        opset_version=14
    )
    
    logger.info("Export complete.")

def verify_onnx(model_path: str, onnx_path: str):
    """Verify ONNX model outputs match PyTorch."""
    logger.info("Verifying export...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    pt_model = AutoModelForSequenceClassification.from_pretrained(model_path)
    pt_model.eval()
    
    text = "Verification test sentence."
    inputs = tokenizer(text, return_tensors="pt")
    
    # PyTorch Inference
    with torch.no_grad():
        pt_outputs = pt_model(**inputs).logits.numpy()
        
    # ONNX Inference
    ort_session = ort.InferenceSession(onnx_path)
    onnx_inputs = {
        "input_ids": inputs["input_ids"].numpy(),
        "attention_mask": inputs["attention_mask"].numpy()
    }
    onnx_outputs = ort_session.run(None, onnx_inputs)[0]
    
    # Compare
    if np.allclose(pt_outputs, onnx_outputs, atol=1e-5):
        logger.info("✅ Verification SUCCESS: Outputs match.")
    else:
        logger.error("❌ Verification FAILED: Outputs differ.")

def main():
    parser = argparse.ArgumentParser(description="Export Model to ONNX")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model directory")
    parser.add_argument("--output_file", type=str, default="model.onnx", help="Output ONNX filename")
    args = parser.parse_args()
    
    output_full_path = os.path.join(args.model_path, args.output_file)
    
    export_to_onnx(args.model_path, output_full_path)
    verify_onnx(args.model_path, output_full_path)

if __name__ == "__main__":
    main()
