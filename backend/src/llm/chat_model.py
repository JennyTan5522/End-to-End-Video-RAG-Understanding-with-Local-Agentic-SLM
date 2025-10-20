"""
Qwen Vision-Language Model Loader
Handles loading and configuration of Qwen2.5-VL models with optional 4-bit quantization
"""
import torch
import os
import logging
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, AutoModelForSpeechSeq2Seq, pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline

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


def build_hf_chat_model(*, deterministic: bool, use_4bit: bool = True) -> ChatHuggingFace:
    """
    Create a ChatHuggingFace model backed by a HuggingFace pipeline.
    
    Args:
        deterministic: If True, uses greedy decoding (router mode). If False, uses sampling (worker mode).
        use_4bit: If True, loads quantized model with bitsandbytes (default: True).
        
    Returns:
        ChatHuggingFace: Configured chat model wrapped in LangChain interface.
        
    Note:
        - deterministic=True  -> router (greedy)
        - deterministic=False -> workers (sampled)
        - use_4bit=True       -> load quantized version with bitsandbytes
    """
    MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
    logger.info(f"Building chat model: {MODEL_ID} (deterministic={deterministic}, use_4bit={use_4bit})")

    try:
        # --- Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.debug("Set pad_token to eos_token")

        # --- Model (quantized or full precision)
        model_kwargs = dict(trust_remote_code=True, device_map="auto")

        if use_4bit and torch.cuda.is_available():
            logger.info("Loading 4-bit quantized model")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                quantization_config=bnb_config,
                **model_kwargs,
            )
        else:
            logger.info("Loading full precision model")
            dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                **model_kwargs,
            )

        # Ensure generation config has proper tokens
        model.generation_config.pad_token_id = tokenizer.pad_token_id
        model.generation_config.eos_token_id = getattr(
            tokenizer, "eos_token_id", tokenizer.pad_token_id
        )

        # --- Generation settings
        gen_kwargs = {
            "max_new_tokens": 256 if deterministic else 2048,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": model.generation_config.eos_token_id,
            "return_full_text": False,
        }

        if deterministic:
            # Router mode (no randomness)
            gen_kwargs.update(dict(temperature=0.0, do_sample=False))
            logger.debug("Configured for deterministic generation (router mode)")
        else:
            # Worker mode (some randomness)
            gen_kwargs.update(dict(temperature=0.2, top_p=0.9, do_sample=True))
            logger.debug("Configured for sampled generation (worker mode)")

        # --- HF pipeline
        gen_pipe = pipeline(
            task="text-generation",
            model=model,
            tokenizer=tokenizer,
            **gen_kwargs,
        )

        # --- LangChain wrapper
        hf_llm = HuggingFacePipeline(pipeline=gen_pipe, model_id=MODEL_ID)
        logger.info("Chat model built successfully")
        return ChatHuggingFace(llm=hf_llm)
        
    except Exception as e:
        logger.error(f"Failed to build chat model: {str(e)}", exc_info=True)
        raise