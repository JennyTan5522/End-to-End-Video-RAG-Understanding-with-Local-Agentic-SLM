"""
Audio Extraction and Transcription Utilities
Extracts audio from video files and transcribes using Whisper model with text transcript chunking
"""
import logging
import os
import librosa
import torch
import yaml
from transformers import AutoTokenizer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from moviepy import VideoFileClip
from config.service_config import settings
from src.llm.inference import generate_qwen_response
from src.prompt_engineering.templates import TRANSCRIPT_TEXT_SUMMARIZER_PROMPT, transcript_summary_parser
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("Audio Processing MCP Tools", port = settings.AUDIO_MCP_PORT)

@mcp.tool()
async def extract_audio_from_video(video_file: str, output_folder: str) -> str:
    """
    Extract audio track from a video file and save it as an MP3 file.
    
    This function processes a video file, extracts its audio track, and saves it as an MP3
    file in the specified output folder. The output file is named using the original video
    filename with '_audio.mp3' suffix.
    
    Args:
        video_file (str): Path to the input video file (e.g., 'meeting.mp4', '../data/video.avi').
                          Can be absolute or relative path. Supported formats include MP4, AVI, MOV, etc.
        output_folder (str): Directory path where the extracted audio file will be saved.
                            Will be created if it doesn't exist.
    
    Returns:
        str: Absolute path to the generated MP3 audio file.
             Example: '/absolute/path/to/output_folder/video_name_audio.mp3'
    
    Raises:
        FileNotFoundError: If the specified video file does not exist.
        RuntimeError: If the video file contains no audio track.
        Exception: For other errors during video processing or audio extraction.
    
    Example:
        >>> audio_path = await extract_audio_from_video(
        ...     video_file="../videos/meeting.mp4",
        ...     output_folder="../audio_output"
        ... )
        >>> print(audio_path)
        '/home/user/audio_output/meeting_audio.mp3'
    
    Note:
        - The output folder is created automatically if it doesn't exist
        - Video file is properly closed after processing to free resources
        - Output MP3 uses standard MP3 codec for compatibility
    """
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file not found: {video_file}")

    os.makedirs(output_folder, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_file))[0]
    out_path = os.path.abspath(os.path.join(output_folder, f"{base}_audio.mp3"))

    video = VideoFileClip(video_file)
    try:
        if video.audio is None:
            raise RuntimeError("No audio track found in the video.")
        video.audio.write_audiofile(out_path, codec="mp3")
        return out_path
    finally:
        video.close()

from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, AutoModelForSpeechSeq2Seq, pipeline
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

@mcp.tool()
async def transcribe_audio_whisper(audio_path: str, output_folder: str, chunk_length_s: int = 5, batch_size: int = 32) -> str:
    """
    Transcribe audio using Distil-Whisper model with time-based chunking
    
    Args:
        audio_path: Path to the input audio file (MP3 or WAV)
        output_folder: Path to the saved folder
        chunk_length_s: Length in seconds of each audio chunk for grouping (default: 5)
        batch_size: Number of audio chunks to process in one batch (default: 32)
    
    Returns:
        str: Path to the saved transcription YAML file
    """
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Loading audio from: {audio_path}")
        audio, sr = librosa.load(audio_path, sr=16000)

        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        transcription_path = os.path.join(output_folder, f"{audio_name}_transcript.yaml")

        logger.info("Starting transcription process...")
        transcribe_pipeline = load_transcription_pipeline("distil-whisper/distil-small.en")
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

def build_user_prompt_for_text_chunk(text: str, start_s: float, end_s: float) -> str:
    return (
        f"Timeframe: {start_s:.2f}s to {end_s:.2f}s\n\n"
        f"Transcript:\n{text}\n\n"
    )

def summarize_transcript_chunks(chunks: list, processor, model) -> list:
    """
    Summarize a list of transcript chunks and extract key topics for each segment.
    
    Uses a vision-language model to generate summaries and extract topics from each
    transcript chunk. Results are structured for vector database indexing.

    Args:
        chunks: List of dictionaries, each containing:
            - 'text': Transcript text content
            - 'start': Start time in seconds
            - 'end': End time in seconds
            - 'groups': List of timeframe group identifiers

    Returns:
        list: List of structured dictionaries ready for indexing, each containing:
            - 'text': Original transcript text
            - 'summary': AI-generated summary of the segment
            - 'topics': List of extracted topic keywords
            - 'type': Always "txt" to indicate text-based content
    """
    summary_chunks = []

    for i, data in enumerate(chunks, start=1):
        try:
            text = data["text"]
            start_s = data['start']
            end_s = data['end']

            logger.info(f"Processing chunk {i}/{len(chunks)} ({start_s:.2f}s - {end_s:.2f}s)")
            logger.debug(f"Chunk {i} text preview: {text[:100]}...")

            # Run summarization model on this chunk
            messages = [
                {"role": "system", "content": [{"type": "text", "text": TRANSCRIPT_TEXT_SUMMARIZER_PROMPT}]},
                {"role": "user",   "content": [{"type": "text", "text": build_user_prompt_for_text_chunk(text, start_s, end_s)}]},
            ]
            
            summary_output = generate_qwen_response(processor, model, messages)
            summary_info = transcript_summary_parser.parse(summary_output)

            summary = ""
            topics = []
            try:
                summary = summary_info.summary
                topics = summary_info.topics
            except Exception as e:
                logger.error(f"Error extracting summary or topics in chunk {i}: {e}")
                logger.debug(f"Raw model output for chunk {i}: {summary_output}")

            # Log structured output for verification
            logger.info(f"Chunk {i} processed successfully")
            logger.info(f"  Timeframe: {start_s:.2f}s - {end_s:.2f}s")
            logger.info(f"  Text: {text}")
            logger.info(f"  Summary: {summary}")
            logger.info(f"  Topics: {topics}")
            logger.info("-" * 80)

            # Store structured result
            summary_chunks.append({
                "text": text,
                "summary": summary,
                "topics": topics,
                "type": "txt"
            })
            
        except Exception as e:
            logger.error(f"Failed to process chunk {i}/{len(chunks)}: {e}")
            logger.debug(f"Chunk data: {data}")
            continue

    logger.info(f"Successfully summarized {len(summary_chunks)}/{len(chunks)} chunks")
    return summary_chunks

if __name__ == "__main__":
    # Exposes Streamable HTTP endpoint at http://127.0.0.1:8000/mcp
    mcp.run(transport="streamable-http")