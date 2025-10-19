"""
Qwen Vision-Language Model Loader
Handles loading and configuration of Qwen2.5-VL models with optional 4-bit quantization
"""
import torch
import os
import logging
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, AutoModelForSpeechSeq2Seq, pipeline

logger = logging.getLogger(__name__)

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
    try:
        logger.info(f"Loading Qwen VL model: {model_name}")
        logger.info(f"Quantization mode: {'4-bit' if use_4bit else 'full precision'}")
        
        # Load processor for handling inputs/outputs
        logger.info("Loading processor...")
        try:
            processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            logger.info("Processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load processor: {e}")
            raise

        # Determine device and dtype
        device_available = torch.cuda.is_available()
        logger.info(f"CUDA available: {device_available}")
        
        if use_4bit:
            # 4-bit quantization for reduced memory footprint
            compute_dtype = torch.bfloat16 if device_available else torch.float32
            logger.info(f"Using 4-bit quantization with compute dtype: {compute_dtype}")
            
            quant_kwargs = dict(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True, 
                bnb_4bit_quant_type="nf4",       
                bnb_4bit_compute_dtype=compute_dtype,
                device_map="auto",  
            )
        else:
            # Full precision (fp16/fp32) without quantization
            torch_dtype = torch.float16 if device_available else torch.float32
            logger.info(f"Using full precision with dtype: {torch_dtype}")
            
            quant_kwargs = dict(
                torch_dtype=torch_dtype,
                device_map="auto",
            )

        # Load the vision-language model
        logger.info("Loading vision-language model...")
        try:
            model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                model_name,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                **quant_kwargs,
            )
            logger.info("Vision-language model loaded successfully")
            logger.info(f"Model device: {model.device if hasattr(model, 'device') else 'distributed'}")
        except Exception as e:
            logger.error(f"Failed to load vision-language model: {e}")
            raise
        
        logger.info("Qwen VL model initialization complete")
        return processor, model
        
    except Exception as e:
        logger.error(f"Failed to load Qwen VL model '{model_name}': {e}")
        raise

def load_transcription_pipeline(model_name: str):
    """
    Initialize automatic speech recognition model and pipeline.
    
    Args:
        model_name: HuggingFace model transcript model (whisper)
    
    Returns:
        tuple: (transcribe_pipeline, processor, transcribe_model) where:
            - transcribe_pipeline: Configured ASR pipeline ready for transcription
            - processor: Audio processor with tokenizer and feature extractor
            - transcribe_model: Loaded speech-to-text model
    """
    try:
        logger.info(f"Initializing transcription pipeline with model: {model_name}")
        
        # Determine dtype based on GPU availability
        device_available = torch.cuda.is_available()
        torch_dtype = torch.float16 if device_available else torch.float32
        device = "cuda:0" if device_available else "cpu"
        
        logger.info(f"Using device: {device}, dtype: {torch_dtype}")
        
        # Load model
        logger.info("Loading transcription model...")
        try:
            transcribe_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            logger.info("Transcription model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load transcription model: {e}")
            raise
        
        # Load processor
        logger.info("Loading audio processor...")
        try:
            processor = AutoProcessor.from_pretrained(model_name)
            logger.info("Audio processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load audio processor: {e}")
            raise
        
        # Create pipeline
        logger.info("Creating transcription pipeline...")
        try:
            transcribe_pipeline = pipeline(
                "automatic-speech-recognition",
                model=transcribe_model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=torch_dtype,
                device=device
            )
            logger.info("Transcription pipeline created successfully")
        except Exception as e:
            logger.error(f"Failed to create transcription pipeline: {e}")
            raise
        
        logger.info("Transcription pipeline initialization complete")
        return transcribe_pipeline
        
    except Exception as e:
        logger.error(f"Failed to initialize transcription pipeline '{model_name}': {e}")
        raise