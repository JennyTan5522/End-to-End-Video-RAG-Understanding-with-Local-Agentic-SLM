"""
Qwen Vision-Language Model Inference
Handles text generation with Qwen2.5-VL models for chat and vision tasks
"""
import torch

@torch.inference_mode()
def generate_qwen_response(processor, model, messages: list, images=None, max_new_tokens: int = 512, temperature: float = 0.0, top_p: float = 1.0) -> str:
    """
    Generate response using Qwen2.5-VL model
    
    Args:
        processor: Qwen AutoProcessor for input/output handling
        model: Loaded Qwen2.5-VL model
        messages: List of chat messages in OpenAI format
        images: Optional list of PIL Images or image paths for vision tasks
        max_new_tokens: Maximum tokens to generate (default: 512)
        temperature: Sampling temperature, 0 for greedy (default: 0.0)
        top_p: Nucleus sampling parameter (default: 1.0)
        
    Returns:
        str: Generated response text
        
    Example:
        >>> messages = [{"role": "user", "content": "Describe this image"}]
        >>> response = generate_qwen_response(processor, model, messages, images=[img])
    """
    # Build chat input with template
    chat_text = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )

    # Process text and images
    inputs = processor(
        text=[chat_text], 
        images=images, 
        return_tensors="pt"
    ).to(model.device)

    # Generate response
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=temperature > 0,
        pad_token_id=getattr(processor.tokenizer, "pad_token_id", None),
        eos_token_id=getattr(processor.tokenizer, "eos_token_id", None),
    )

    # Decode new tokens only
    prompt_len = inputs["input_ids"].shape[-1]
    new_tokens = generated_ids[:, prompt_len:]
    response = processor.batch_decode(
        new_tokens, 
        skip_special_tokens=True
    )[0].strip()
    
    return response