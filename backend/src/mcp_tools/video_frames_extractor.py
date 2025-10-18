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
import logging

logger = logging.getLogger(__name__)

def extract_video_frames(video_file: str, frame_rate: float = 2.0, output_root: str = "data/frames", group_seconds: int = 5) -> str:
    """
    Extract frames from video at specified rate and group by time intervals
    
    Args:
        video_file: Path to the video file
        frame_rate: Frames to extract per second (e.g., 2.0 = one every 0.5s)
        output_root: Root directory for extracted frames
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

        video_name = os.path.splitext(os.path.basename(video_file))[0]
        output_directory = os.path.join(output_root, f"{video_name}_frames")

        if os.path.exists(output_directory):
            logger.info(f"Cleaning existing folder: {output_directory}")
            shutil.rmtree(output_directory)
        os.makedirs(output_directory, exist_ok=True)
        logger.info(f"Output folder: {output_directory}")

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
                    output_directory, 
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

        logger.info(f"Extracted {saved_count} frames from {video_name}")
        logger.info(f"Grouped every {group_seconds}s in: {output_directory}")
        return output_directory

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