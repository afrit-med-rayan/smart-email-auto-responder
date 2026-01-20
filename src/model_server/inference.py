"""
Optimized Inference Engine

Provides fast, batched inference with ONNX Runtime support.
Handles concurrent requests and performance optimization.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import torch
from transformers import pipeline

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Optimized inference engine for model predictions."""
    
    def __init__(
        self,
        model,
        tokenizer,
        device: str = "cpu",
        max_workers: int = 4,
        batch_size: int = 8
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Set model to eval mode
        self.model.eval()
        
        logger.info(
            f"InferenceEngine initialized - Device: {device}, "
            f"Batch size: {batch_size}, Workers: {max_workers}"
        )
    
    def predict_single(
        self,
        text: str,
        return_probabilities: bool = False
    ) -> Dict[str, Any]:
        """
        Make a prediction for a single text input.
        
        Args:
            text: Input text
            return_probabilities: Whether to return class probabilities
            
        Returns:
            Prediction result with label and optional probabilities
        """
        start_time = time.time()
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get predictions
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
            
            inference_time = time.time() - start_time
            
            result = {
                "predicted_class": predicted_class,
                "confidence": confidence,
                "inference_time_ms": inference_time * 1000
            }
            
            if return_probabilities:
                result["probabilities"] = probabilities[0].cpu().numpy().tolist()
            
            return result
            
        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            return {
                "error": str(e),
                "predicted_class": -1,
                "confidence": 0.0
            }
    
    def predict_batch(
        self,
        texts: List[str],
        return_probabilities: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of texts.
        
        Args:
            texts: List of input texts
            return_probabilities: Whether to return class probabilities
            
        Returns:
            List of prediction results
        """
        start_time = time.time()
        
        try:
            # Tokenize batch
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Batch inference
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get predictions
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_classes = torch.argmax(probabilities, dim=-1)
            
            # Build results
            results = []
            for i in range(len(texts)):
                result = {
                    "predicted_class": predicted_classes[i].item(),
                    "confidence": probabilities[i][predicted_classes[i]].item()
                }
                
                if return_probabilities:
                    result["probabilities"] = probabilities[i].cpu().numpy().tolist()
                
                results.append(result)
            
            inference_time = time.time() - start_time
            logger.info(
                f"Batch inference completed - Size: {len(texts)}, "
                f"Time: {inference_time*1000:.2f}ms, "
                f"Avg: {inference_time*1000/len(texts):.2f}ms/item"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch inference error: {e}", exc_info=True)
            return [{"error": str(e), "predicted_class": -1, "confidence": 0.0}] * len(texts)
    
    def predict_concurrent(
        self,
        texts: List[str],
        return_probabilities: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Make predictions concurrently using thread pool.
        
        Args:
            texts: List of input texts
            return_probabilities: Whether to return class probabilities
            
        Returns:
            List of prediction results
        """
        # Split into batches
        batches = [
            texts[i:i + self.batch_size]
            for i in range(0, len(texts), self.batch_size)
        ]
        
        # Process batches concurrently
        futures = [
            self.executor.submit(self.predict_batch, batch, return_probabilities)
            for batch in batches
        ]
        
        # Collect results
        results = []
        for future in futures:
            batch_results = future.result()
            results.extend(batch_results)
        
        return results
    
    def warm_up(self, num_samples: int = 5):
        """
        Warm up the model with dummy predictions.
        
        Args:
            num_samples: Number of warm-up samples
        """
        logger.info(f"Warming up model with {num_samples} samples")
        
        dummy_texts = [
            "This is a test email for warm-up purposes."
        ] * num_samples
        
        self.predict_batch(dummy_texts)
        logger.info("Model warm-up completed")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "device": self.device,
            "batch_size": self.batch_size,
            "max_workers": self.max_workers,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "model_size_mb": sum(
                p.numel() * p.element_size() for p in self.model.parameters()
            ) / (1024 * 1024)
        }
    
    def shutdown(self):
        """Shutdown the thread pool executor."""
        logger.info("Shutting down inference engine")
        self.executor.shutdown(wait=True)


class ONNXInferenceEngine:
    """ONNX Runtime-based inference engine for maximum performance."""
    
    def __init__(
        self,
        onnx_model_path: str,
        tokenizer,
        device: str = "cpu"
    ):
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError("onnxruntime is required for ONNX inference")
        
        self.tokenizer = tokenizer
        self.device = device
        
        # Create ONNX session
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if device == "cuda" else ['CPUExecutionProvider']
        self.session = ort.InferenceSession(onnx_model_path, providers=providers)
        
        logger.info(f"ONNX InferenceEngine initialized - Model: {onnx_model_path}")
    
    def predict_single(self, text: str) -> Dict[str, Any]:
        """Make prediction using ONNX Runtime."""
        start_time = time.time()
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="np",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Prepare ONNX inputs
            onnx_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }
            
            # Run inference
            outputs = self.session.run(None, onnx_inputs)
            logits = outputs[0]
            
            # Get predictions
            probabilities = self._softmax(logits[0])
            predicted_class = np.argmax(probabilities)
            confidence = probabilities[predicted_class]
            
            inference_time = time.time() - start_time
            
            return {
                "predicted_class": int(predicted_class),
                "confidence": float(confidence),
                "inference_time_ms": inference_time * 1000
            }
            
        except Exception as e:
            logger.error(f"ONNX inference error: {e}", exc_info=True)
            return {"error": str(e), "predicted_class": -1, "confidence": 0.0}
    
    @staticmethod
    def _softmax(x):
        """Compute softmax values."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()


if __name__ == "__main__":
    # Example usage
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    engine = InferenceEngine(model, tokenizer, device="cpu", batch_size=4)
    
    # Single prediction
    result = engine.predict_single("This is a test email")
    print("Single prediction:", result)
    
    # Batch prediction
    texts = ["Email 1", "Email 2", "Email 3"]
    results = engine.predict_batch(texts)
    print("Batch predictions:", results)
    
    # Performance stats
    print("Performance stats:", engine.get_performance_stats())
