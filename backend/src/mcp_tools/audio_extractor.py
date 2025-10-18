"""
Audio Extraction and Transcription Utilities
Extracts audio from video files and transcribes using Whisper model with text transcript chunking
"""
import logging
import os
import librosa
import torch
import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from moviepy import VideoFileClip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

def extract_audio_from_video(video_file: str, output_folder: str = "data/audio") -> str:
    """
    Extract audio from video file and save as MP3
    
    Args:
        video_file: Path to the input video file
        output_folder: Directory to save extracted audio file (default: "data/audio")
    
    Returns:
        str: Path to the generated audio file
    """
    try:
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file not found: {video_file}")

        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Output directory: {output_folder}")

        video_name = os.path.splitext(os.path.basename(video_file))[0]
        output_path = os.path.join(output_folder, f"{video_name}_audio.mp3")

        logger.info(f"Starting audio extraction from: {video_file}")
        logger.info(f"Output audio will be saved to: {output_path}")

        video = VideoFileClip(video_file)
        video.audio.write_audiofile(output_path, codec='mp3')
        video.close()

        logger.info(f"Audio extraction completed: {output_path}")
        return output_path

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")
        raise

def transcribe_audio_whisper(audio_path: str, model_name: str, output_dir: str = "data/transcript", chunk_length_s: int = 5, batch_size: int = 32) -> str:
    """
    Transcribe audio using Distil-Whisper model with time-based chunking
    
    Args:
        audio_path: Path to the input audio file (MP3 or WAV)
        model_name: Hugging Face model name for Whisper (e.g., "distil-whisper/distil-small.en")
        output_dir: Directory to save transcription YAML file (default: "data/transcript")
        chunk_length_s: Length in seconds of each audio chunk for grouping (default: 5)
        batch_size: Number of audio chunks to process in one batch (default: 32)
    
    Returns:
        str: Path to the saved transcription YAML file
    """
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info("Initializing Whisper model and processor...")
        
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        transcribe_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        processor = AutoProcessor.from_pretrained(model_name)

        transcribe_pipeline = pipeline(
            "automatic-speech-recognition",
            model=transcribe_model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device="cuda:0" if torch.cuda.is_available() else "cpu"
        )

        logger.info(f"Loading audio from: {audio_path}")
        audio, sr = librosa.load(audio_path, sr=16000)

        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        os.makedirs(output_dir, exist_ok=True)
        transcription_path = os.path.join(output_dir, f"{audio_name}_transcript.yaml")

        logger.info("Starting transcription process...")
        transcriptions = transcribe_pipeline(
            audio,
            chunk_length_s=chunk_length_s,
            batch_size=batch_size,
            return_timestamps=True
        )

        logger.debug(f"Raw transcription result: {transcriptions}")

        transcript_dict = {}
        for chunk in transcriptions.get("chunks", []):
            start, end = chunk.get("timestamp", (0, 0))
            text = chunk.get("text", "").strip()
            if start is not None and end is not None:
                key = f"{int(start)}-{int(end)}s"
                transcript_dict[key] = text

        with open(transcription_path, "w", encoding="utf-8") as f:
            yaml.dump(transcript_dict, f, allow_unicode=True, sort_keys=False)

        logger.info("Transcription completed successfully")
        logger.info("Grouped transcript:")
        for k, v in transcript_dict.items():
            logger.info(f"{k}: {v}")

        logger.info(f"Transcription saved to: {transcription_path}")
        return transcription_path

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}")
        raise


def count_tokens(text: str, model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct") -> int:
    """
    Count tokens in text using Qwen tokenizer
    
    Args:
        text: Input text to tokenize
        model_name: Hugging Face model name (default: "Qwen/Qwen2.5-VL-7B-Instruct")
    
    Returns:
        int: Number of tokens, or 0 if tokenization fails
    """
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        tokens = tokenizer.encode(text)
        token_count = len(tokens)
        return token_count
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return 0


def parse_timeframe(timeframe: str) -> tuple[float, float]:
    """
    Convert timeframe string to numeric start and end seconds
    
    Args:
        timeframe: Timeframe range string (e.g., '0-5s' or '0-5s')
    
    Returns:
        tuple[float, float]: (start_seconds, end_seconds)
        
    Example:
        >>> parse_timeframe('0-5s')
        (0.0, 5.0)
        >>> parse_timeframe('10-15s')
        (10.0, 15.0)
    """
    timeframe = timeframe.replace("-", "-").replace("s", "")
    start, end = timeframe.split("-")
    return float(start), float(end)

def read_transcript_yaml(transcript_path: str) -> dict:
    """
    Read YAML transcript file into dictionary
    
    Args:
        transcript_path: Path to YAML file with timeframe keys (e.g., '0–5s')
    
    Returns:
        dict: Mapping of timeframe key to transcript text
        
    Example:
        >>> transcript = read_transcript_yaml('transcript.yaml')
        {'0-5s': 'Hello world', '5-10s': 'This is a test'}
    """
    try:
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
            
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = yaml.safe_load(f)
        
        return transcript_data
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading transcript YAML: {e}")
        raise

def chunk_transcript_text(transcript_path: str, max_chunk_token_size: int = 300, tokenizer_model: str = "Qwen/Qwen2.5-VL-7B-Instruct") -> list[dict]:
    """
    Chunk transcript text into token-size-limited segments
    
    Combines consecutive transcript groups until adding another would exceed max_chunk_token_size.
    If a single group exceeds the limit, splits it using RecursiveCharacterTextSplitter.
    
    Args:
        transcript_path: Path to YAML transcript file
        max_chunk_token_size: Maximum tokens per chunk (default: 300)
        tokenizer_model: Model name for tokenizer (default: "Qwen/Qwen2.5-VL-7B-Instruct")
    
    Returns:
        list[dict]: List of chunks with 'start', 'end', 'groups', 'text' keys
        
    Example:
        >>> chunks = chunk_transcript_text('transcript.yaml', max_chunk_token_size=300)
        [
            {
                'start': 0.0, 
                'end': 10.0, 
                'groups': ['0–5s', '5–10s'], 
                'text': 'Combined text...'
            },
            ...
        ]
    """
    try:
        transcript_data = read_transcript_yaml(transcript_path)
        
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_model, trust_remote_code=True)
        splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=tokenizer,
            chunk_size=max_chunk_token_size,
            chunk_overlap=100,
        )
        
        transcript_text = []
        for timeframe, text in transcript_data.items():
            start, end = parse_timeframe(timeframe)
            if text.strip():
                transcript_text.append((timeframe, start, end, text.strip()))
        
        transcript_text.sort(key=lambda x: x[1])

        chunks = []
        current_chunk = {
            "text": "",
            "groups": [],
            "start": None,
            "end": None
        }
        
        for key, start, end, text in transcript_text:
            text = text.strip()
            text_token_len = count_tokens(text, tokenizer_model)
        
            if text_token_len > max_chunk_token_size:
                if current_chunk["text"]:
                    chunks.append({
                        "start": current_chunk["start"],
                        "end": current_chunk["end"],
                        "groups": current_chunk["groups"],
                        "text": current_chunk["text"].strip()
                    })
                    current_chunk = {"text": "", "groups": [], "start": None, "end": None}
        
                sub_texts = splitter.split_text(text)
                for i, sub in enumerate(sub_texts):
                    chunks.append({
                        "start": start,
                        "end": end,
                        "groups": [f"{key}#part{i+1}"],
                        "text": sub.strip()
                    })
                continue
        
            if len(current_chunk["text"]) + text_token_len + 1 > max_chunk_token_size:
                chunks.append({
                    "start": current_chunk["start"],
                    "end": current_chunk["end"],
                    "groups": current_chunk["groups"],
                    "text": current_chunk["text"].strip()
                })
                current_chunk = {"text": "", "groups": [], "start": None, "end": None}
        
            if not current_chunk["text"]:
                current_chunk["start"] = start
            current_chunk["end"] = end
            current_chunk["groups"].append(key)
            current_chunk["text"] += (" " if current_chunk["text"] else "") + text
        
        if current_chunk["text"]:
            chunks.append({
                "start": current_chunk["start"],
                "end": current_chunk["end"],
                "groups": current_chunk["groups"],
                "text": current_chunk["text"].strip()
            })

        logger.info(f"Created {len(chunks)} chunks from transcript")
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking transcript: {e}")
        raise