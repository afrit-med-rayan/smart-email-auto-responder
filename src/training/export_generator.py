"""
Export Seq2Seq Model (T5) to ONNX

Exports Encoder and Decoder components for T5 models.
Uses `optimum` if available, or manual export via `onnx`.
For simplicity in this phase, we use `optimum-cli` wrapper if installed, 
otherwise we provide a simplified script using `torch.onnx`.

Note: T5 export is complex. This script attempts basic export.
Recommended: `pip install optimum[onnxruntime]`
"""

import argparse
import logging
import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_t5(model_path: str, output_dir: str):
    """
    Export T5 using torch.onnx (Basic / Naive approach).
    For production, 'optimum' is highly recommended.
    """
    logger.warning("Using basic torch.onnx export. For best results, use 'optimum-cli export onnx ...'")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    model.eval()

    # 1. Export Encoder
    encoder_path = os.path.join(output_dir, "encoder.onnx")
    logger.info(f"Exporting Encoder to {encoder_path}")
    
    dummy_input = tokenizer("translate English to German: Hello world", return_tensors="pt")
    input_ids = dummy_input.input_ids
    attention_mask = dummy_input.attention_mask

    torch.onnx.export(
        model.encoder,
        (input_ids, attention_mask),
        encoder_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "last_hidden_state": {0: "batch", 1: "seq"}
        },
        opset_version=14
    )

    # 2. Export Decoder (Simplified - No Past Key Values)
    # Note: Full T5 Decoder export with past_key_values is very complex to write manually.
    # We will export a simplified version that takes encoder_outputs and decoder_input_ids.
    decoder_path = os.path.join(output_dir, "decoder_no_past.onnx")
    logger.info(f"Exporting Decoder (Simple) to {decoder_path}")
    
    # Get encoder output
    with torch.no_grad():
        encoder_outputs = model.encoder(input_ids=input_ids, attention_mask=attention_mask)
    
    dummy_decoder_input_ids = torch.tensor([[model.config.decoder_start_token_id]], dtype=torch.long)
    
    # Wrap decoder to handle separated inputs
    class DecoderWrapper(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.decoder = model.decoder
            self.lm_head = model.lm_head
            self.config = model.config

        def forward(self, input_ids, encoder_hidden_states, encoder_attention_mask):
            decoder_outputs = self.decoder(
                input_ids=input_ids,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask
            )
            logits = self.lm_head(decoder_outputs[0])
            return logits

    decoder_wrapper = DecoderWrapper(model)
    decoder_wrapper.eval()

    torch.onnx.export(
        decoder_wrapper,
        (dummy_decoder_input_ids, encoder_outputs.last_hidden_state, attention_mask),
        decoder_path,
        input_names=["decoder_input_ids", "encoder_last_hidden_state", "encoder_attention_mask"],
        output_names=["logits"],
         dynamic_axes={
            "decoder_input_ids": {0: "batch", 1: "seq_dec"},
            "encoder_last_hidden_state": {0: "batch", 1: "seq_enc"},
            "encoder_attention_mask": {0: "batch", 1: "seq_enc"},
            "logits": {0: "batch", 1: "seq_dec"}
        },
        opset_version=14
    )
    
    logger.info("Export complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    
    export_t5(args.model_path, args.output_dir)
