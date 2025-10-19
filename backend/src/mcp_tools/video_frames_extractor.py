"""
Video Frame Extraction Utilities
Extracts frames from videos at specified intervals and groups them by time segments
"""
import os
import cv2
import re
import shutil
from glob import glob
from PIL import Image
from typing import List, Dict
from src.llm.inference import generate_qwen_response
from src.prompt_engineering.templates import TRANSCRIPT_IMG_SUMMARIZER_PROMPT, transcript_summary_parser
import logging

logger = logging.getLogger(__name__)

def extract_video_frames(video_file: str, output_folder: str, frame_rate: float = 2.0, group_seconds: int = 5) -> str:
    """
    Extract frames from video at specified rate and group by time intervals
    
    Args:
        video_file: Path to the video file
        output_folder: Path to the saved folder
        frame_rate: Frames to extract per second (e.g., 2.0 = one every 0.5s)
        group_seconds: Duration of each group in seconds (e.g., 5 = group every 5s)
    
    Returns:
        str: Path to folder containing extracted frames
    """
    try:
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file not found: {video_file}")

        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_file}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"Video opened: {video_file}")
        logger.info(f"FPS: {fps:.2f}, Total Frames: {total_frames}")

        if os.path.exists(output_folder):
            logger.info(f"Cleaning existing folder: {output_folder}")
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Output folder: {output_folder}")

        frame_count = 0
        saved_count = 0
        save_interval = int(fps / frame_rate)
        logger.info(f"Extracting {frame_rate} frames/sec (every {save_interval}th frame)")
        logger.info(f"Grouping every {group_seconds} seconds")

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("Finished reading all frames")
                break

            frame_count += 1

            if frame_count % save_interval == 0:
                time_sec = frame_count / fps
                start_sec = time_sec - (1 / frame_rate)
                end_sec = time_sec

                group_index = int(time_sec // group_seconds)
                start_group = group_index * group_seconds
                end_group = start_group + group_seconds

                group_folder = os.path.join(
                    output_folder, 
                    f"group_{start_group:03d}s_{end_group:03d}s"
                )
                os.makedirs(group_folder, exist_ok=True)

                output_file = os.path.join(group_folder, f"frame_{frame_count}.jpg")
                cv2.imwrite(output_file, frame)

                saved_count += 1
                logger.debug(
                    f"Saved frame {frame_count:>5} ({time_sec:>6.2f}s) "
                    f"covers {start_sec:.2f}s-{end_sec:.2f}s → {output_file}"
                )

        cap.release()
        cv2.destroyAllWindows()

        logger.info(f"Extracted {saved_count} frames from {video_file}")
        logger.info(f"Grouped every {group_seconds}s in: {output_folder}")
        return output_folder

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Video error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during frame extraction: {e}")
        raise

def build_user_prompt_for_img_chunk(start_s: float, end_s: float, text: str) -> str:
    """
    Build user prompt for image chunk with timeframe information
    
    Args:
        start_s: Start time in seconds
        end_s: End time in seconds
        text: Image summary text
    
    Returns:
        str: Formatted prompt with timeframe and summaries
    """
    return f"Timeframe: {start_s:.2f}s to {end_s:.2f}s\n\nImage Summaries: {text}"


def extract_time_from_group_path(folder_path: str) -> tuple[float, float]:
    """
    Extract start and end time from group folder name
    
    Args:
        folder_path: Path to group folder (e.g., 'group_005s_010s')
    
    Returns:
        tuple[float, float]: (start_time, end_time) in seconds, or (0.0, 0.0) if pattern not found
    
    Example:
        >>> extract_time_from_group_path("data/frames/group_005s_010s")
        (5.0, 10.0)
    """
    name = os.path.basename(os.path.normpath(folder_path))
    match = re.search(r"(\d+)s_(\d+)s", name)
    if not match:
        logger.warning(f"Could not extract time from folder name: {name}")
        return 0.0, 0.0
    return float(match.group(1)), float(match.group(2))

def list_images(folder: str) -> list[str]:
    """
    List all image files in folder
    
    Args:
        folder: Path to folder containing images
    
    Returns:
        list[str]: Sorted list of image file paths
    """
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
    files = []
    for ext in exts:
        files.extend(glob(os.path.join(folder, ext)))
    return sorted(files)

def load_and_resize(image_path: str, max_edge: int = 768) -> Image.Image:
    """
    Load image as RGB and resize if necessary
    
    Args:
        image_path: Path to image file
        max_edge: Maximum edge length in pixels (default: 768)
    
    Returns:
        Image.Image: Loaded and resized PIL Image in RGB mode
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        scale = min(max_edge / max(w, h), 1.0)
        
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            logger.debug(f"Resized image from {w}x{h} to {new_w}x{new_h}")
        
        return img
    except FileNotFoundError as e:
        logger.error(f"Image not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {e}")
        raise

def summarize_frames(processor, model, folder: str, max_edge: int = 768) -> List[Dict]:
    """
    Summarize all frames in a folder by processing each image individually,
    then generating an overall summary for the time segment.
    
    Args:
        processor: Model processor for handling images and text
        model: Vision-language model for generating summaries
        folder: Path to folder containing grouped frames (e.g., 'group_005s_010s')
        max_edge: Maximum edge length for image resizing in pixels (default: 768)
    
    Returns:
        List[Dict]: Dictionary containing:
            - text: Concatenated individual frame descriptions
            - summary: Overall summary of the time segment
            - topics: List of topics extracted from the segment
            - type: Always "img" to indicate image-based content
    """
    start_s, end_s = extract_time_from_group_path(folder)
    paths = list_images(folder)
    if not paths:
        logger.warning(f"No images found in: {folder}")
        return {}

    logger.info("=" * 80)
    logger.info(f"Processing group folder: {os.path.basename(folder)}")
    logger.info(f"  Timeframe: {start_s:.2f}s → {end_s:.2f}s")
    logger.info(f"  Found {len(paths)} image(s) in folder: {folder}")
    logger.info("=" * 80)

    img_descriptions = []
    for i, p in enumerate(paths, 1):
        img = load_and_resize(p, max_edge=max_edge)

        messages = [
            {"role": "system", "content": [{"type": "text", "text": "Summarize this image clearly and concisely."}]},
            {"role": "user", "content": [{"type": "image", "image": img},]},
        ]
        
        img_description = generate_qwen_response(processor, model, messages, images=[img])
        img_descriptions.append(img_description)
        logger.info(f"[{i}/{len(paths)}] Frame: {os.path.basename(p)}")
        logger.info(f"    ➜ Summary: {img_description}")

    # generate image summary
    text = '\n\n'.join(img_descriptions)
    img_user_prompt = build_user_prompt_for_img_chunk(start_s, end_s, text)
    summary_messages = [
            {"role": "system", "content": [{"type": "text", "text": TRANSCRIPT_IMG_SUMMARIZER_PROMPT}]},
            {"role": "user", "content": [{"type": "text", "text": img_user_prompt},]},
    ]
    summary_output = generate_qwen_response(processor, model, summary_messages)
    summary_info = transcript_summary_parser.parse(summary_output)

    # Extract summary and topics safely
    summary = ""
    topics = []
    try:
        summary = summary_info.summary
        topics = summary_info.topics
    except Exception as e:
        logger.error(f"Failed to extract summary or topics: {e}")
        logger.debug(f"Raw model output: {summary_output}")

    # log for summary
    logger.info("-" * 80)
    logger.info(f"Group Summary for {os.path.basename(folder)} ({start_s:.2f}s → {end_s:.2f}s):")
    logger.info(summary)
    logger.info(f"Topics: {topics}")
    logger.info("-" * 80)

    # return structured result
    summary_chunk = ({
        "text": text,
        "summary": summary,
        "topics": topics,
        "type": "img"
    })

    return summary_chunk

def summarize_frame_groups(frame_groups: list[str], processor, model) -> list[dict]:
    """
    Process multiple frame groups and generate summaries for each time segment.
    
    Iterates through frame group folders, processes frames in each group using
    the vision-language model, and returns structured summaries ready for indexing.
    
    Args:
        frame_groups: List of paths to frame group folders (e.g., ['group_000s_005s', 'group_005s_010s'])
                     Each folder should contain video frames for a specific time segment.
        processor: Model processor for handling images and text
        model: Vision-language model for generating summaries
    
    Returns:
        list[dict]: List of summary dictionaries, each containing:
            - 'text': Concatenated individual frame descriptions
            - 'summary': Overall summary of the time segment
            - 'topics': List of extracted topic keywords
            - 'type': Always "img" to indicate image-based content
    
    Example:
        >>> frame_groups = get_frame_groups("data/frames/video_frames")
        >>> img_summaries = summarize_frame_groups(frame_groups, qwen_processor, qwen_chat_model)
        >>> print(img_summaries[0]['summary'])
        "The presenter demonstrates data visualization techniques..."
        >>> print(len(img_summaries))
        10
    """
    img_summary_chunks = []
    total_groups = len(frame_groups)
    failed_groups = 0
    
    logger.info(f"Starting processing of {total_groups} frame groups")
    logger.info("=" * 80)
    
    for i, group in enumerate(frame_groups, start=1):
        try:
            logger.info(f"Processing group {i}/{total_groups}: {os.path.basename(group)}")
            
            group_summary = summarize_frames(processor, model, group)
            
            if group_summary:
                img_summary_chunks.append(group_summary)
                logger.info(f"Successfully processed {os.path.basename(group)}")
            else:
                logger.warning(f"Empty summary returned for {os.path.basename(group)}")
                failed_groups += 1
                
        except Exception as e:
            logger.error(f"Failed to process group {i}/{total_groups} ({os.path.basename(group)}): {e}")
            failed_groups += 1
            continue
        
        logger.info("-" * 80)
    
    # Final summary
    logger.info("=" * 80)
    logger.info(f"Frame group processing completed:")
    logger.info(f"  Successful: {len(img_summary_chunks)}/{total_groups}")
    logger.info(f"  Failed: {failed_groups}/{total_groups}")
    logger.info("=" * 80)
    
    return img_summary_chunks
    
def get_frame_groups(parent_folder: str) -> List[Dict]:
    """
    Get all subfolders under parent_folder that match the 'group_*' naming pattern.
    
    These subfolders are expected to be created by extract_video_frames() and contain
    frames grouped by time intervals (e.g., 'group_005s_010s' for 5-10 second segment).
    
    Args:
        parent_folder: Path to parent directory containing group subfolders
    
    Returns:
        List[Dict]: Sorted list of paths to group folders. Empty list if no groups found.
    """
    # find subfolders named group_*
    groups = [p for p in glob(os.path.join(parent_folder, "group_*")) if os.path.isdir(p)]
    groups = sorted(groups)

    if not groups:
        logger.warning(f"No 'group_*' subfolders under: {parent_folder}")
        return []
    return groups