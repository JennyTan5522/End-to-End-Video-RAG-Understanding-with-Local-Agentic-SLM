"""
Qwen Vision-Language Model Loader
Handles loading and configuration of Qwen2.5-VL models with optional 4-bit quantization
"""
import torch
import os
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

# Configure Hugging Face cache directories
os.environ["HF_HOME"] = "/workspace/hf_cache"
os.environ["HF_HUB_CACHE"] = "/workspace/hf_cache"

def load_qwen_vl_model(model_name: str, use_4bit: bool = True):
    """
    Load Qwen2.5-VL model with processor with 4-bit quantization
    
    Args:
        model_name: Hugging Face chat model (e.g., 'Qwen/Qwen2.5-VL-7B-Instruct')
        use_4bit: Whether to use 4-bit quantization for memory efficiency (default: True)
        
    Returns:
        tuple: (processor, model) - AutoProcessor and loaded Qwen2.5-VL model
    """
    # Load processor for handling inputs/outputs
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)

    if use_4bit:
        # 4-bit quantization for reduced memory footprint
        quant_kwargs = dict(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True, 
            bnb_4bit_quant_type="nf4",       
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",  
        )
    else:
        # Full precision (fp16/fp32) without quantization
        quant_kwargs = dict(
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )

    # Load the vision-language model
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        **quant_kwargs,
    )
    
    return processor, model


# Example usage (uncomment when config is available):
# from config import settings
# processor, model = load_qwen_vl_model(settings.QWEN_VL_MODEL_NAME, settings.QWEN_VL_USE_4BIT)