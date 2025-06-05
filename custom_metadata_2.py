import os
import json
import threading

# Global cache for metadata (initialized on first use)
_metadata_cache = None
_cache_lock = threading.Lock()

# Path to the metadata JSONL file (adjust this to your actual path)
METADATA_FILE_PATH = "/home/casio/localssd/prompts.jsonl"

def get_custom_metadata(info, audio):
    """
    Retrieves custom metadata for a given audio sample.
    This function reads and caches the entire metadata file on first call 
    for fast lookup in subsequent calls.
    
    Args:
        info (dict): Information about the audio file (e.g., file path, relative path, etc.).
        audio (object): The audio data (not used for metadata lookup).
        
    Returns:
        dict or None: The metadata dictionary corresponding to this audio file, or None if not found.
    """
    global _metadata_cache
    # Load and cache the metadata on the first call
    if _metadata_cache is None:
        with _cache_lock:  # ensure only one thread loads the file at a time
            if _metadata_cache is None:  # double-check locking
                # Initialize the cache dictionary
                _metadata_cache = {}
                try:
                    with open(METADATA_FILE_PATH, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue  # skip empty lines
                            try:
                                meta = json.loads(line)
                            except json.JSONDecodeError:
                                continue  # skip malformed JSON lines
                            # Each line is expected to have an 'id' field that corresponds to the audio filename
                            if 'id' in meta:
                                # Use the ID as the key (convert to string for consistency)
                                key = str(meta['id'])
                                _metadata_cache[key] = meta
                            # (Optional) If the JSONL uses a different key for filename, handle it here.
                except Exception as e:
                    # If there's an issue reading the file, print debug info (could also use logging)
                    print(f"Warning: Failed to load metadata file {METADATA_FILE_PATH}: {e}")
                    _metadata_cache = {}  # ensure cache is at least an empty dict
    # At this point, _metadata_cache is loaded and ready for lookups.
    # Determine the audio file's ID or key to lookup in the cache.
    # Assume audio files are named as <id>_hq.mp3 (per Stable Audio convention).
    audio_path = info.get("path") or info.get("relpath") or ""  # using .get in case keys differ
    filename = os.path.basename(audio_path)  # e.g., "12345_hq.mp3"
    # Remove the suffix to get the ID (assuming the suffix is "_hq.mp3")
    audio_id = filename
    if audio_id.endswith("_hq.mp3"):
        audio_id = audio_id[:-len("_hq.mp3")]  # remove the 7 characters "_hq.mp3"
    else:
        # If filename doesn’t follow the expected pattern, strip extension as fallback
        audio_id = os.path.splitext(filename)[0]
    # Now audio_id should match the 'id' field in our metadata (e.g., "12345").

    # Retrieve the metadata from the cache
    metadata = _metadata_cache.get(audio_id)
    if metadata is None:
        # If not found, you might handle it (e.g., log a warning). For now, return None.
        return None

    # (Optional) You can transform or filter the metadata here if needed before returning.
    return metadata
