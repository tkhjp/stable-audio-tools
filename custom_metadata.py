# my_custom_metadata.py
import json
import os

# --- Global Data Store ---
# This dictionary will store your prompts, keyed by audio ID.
# It's loaded once when the Python module is first imported by a DataLoader worker process,
# making lookups efficient during training.
PROMPTS_BY_ID = {}
METADATA_LOADED_SUCCESSFULLY = False

# --- Helper Function to Load Prompts (Called Once) ---
def _load_all_prompts(any_audio_file_path_from_dataset):
    """
    Loads prompts from prompts.jsonl.
    It assumes prompts.jsonl is located in the parent directory of the 'audio' folder.
    Example:
        - /your_dataset_root/
            - audio/ (contains {id}_hq.mp3 files)
            - prompts.jsonl
    The any_audio_file_path_from_dataset will be like '/your_dataset_root/audio/some_id_hq.mp3'.
    """
    global PROMPTS_BY_ID, METADATA_LOADED_SUCCESSFULLY

    if METADATA_LOADED_SUCCESSFULLY: # Avoid reloading if already done
        return

    try:
        # Derive the path to prompts.jsonl based on the path of an audio file
        audio_directory = os.path.dirname(any_audio_file_path_from_dataset) # e.g., /your_dataset_root/audio
        dataset_root = os.path.dirname(audio_directory) # e.g., /your_dataset_root/
        prompts_file_location = "/home/casio/localssd/prompts.jsonl"

        if not os.path.exists(prompts_file_location):
            print(f"CRITICAL WARNING: prompts.jsonl not found at expected location: {prompts_file_location}")
            print("Prompts will not be available for training.")
            # METADATA_LOADED_SUCCESSFULLY remains False or you can set it to True but with an empty PROMPTS_BY_ID
            # to prevent repeated attempts if the file is genuinely missing.
            METADATA_LOADED_SUCCESSFULLY = True # Mark as attempted
            PROMPTS_BY_ID = {}
            return

        print(f"Loading prompts from: {prompts_file_location}")
        with open(prompts_file_location, 'r') as f:
            for line_number, line in enumerate(f, 1):
                try:
                    record = json.loads(line)
                    if 'id' in record and 'prompt' in record:
                        PROMPTS_BY_ID[record['id']] = record['prompt']
                    else:
                        print(f"Warning: Record in prompts.jsonl at line {line_number} is missing 'id' or 'prompt'. Skipping.")
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from prompts.jsonl at line {line_number}. Skipping.")
        
        print(f"Successfully loaded {len(PROMPTS_BY_ID)} prompts.")
        METADATA_LOADED_SUCCESSFULLY = True

    except Exception as e:
        print(f"CRITICAL ERROR during prompt loading: {e}")
        # METADATA_LOADED_SUCCESSFULLY remains False, or handle as above
        METADATA_LOADED_SUCCESSFULLY = True # Mark as attempted
        PROMPTS_BY_ID = {}

# --- The Required Function for stable-audio-tools ---
def get_custom_metadata(info, audio):
    """
    This function is called by stable-audio-tools for each audio sample.
    'info' is a dictionary containing metadata about the audio file, including 'path'.
    'audio' is the loaded audio tensor.
    """
    audio_file_path = info.get("path")

    if not audio_file_path:
        print("Warning: 'path' key not found in info object. Cannot determine audio ID.")
        return {"prompt": "Error: Missing file path"} # Default/error prompt

    # Ensure prompts are loaded (this logic runs only once per worker process)
    if not METADATA_LOADED_SUCCESSFULLY and not PROMPTS_BY_ID: # Check if loading was attempted and failed or not attempted
        _load_all_prompts(audio_file_path)

    try:
        # Extract filename: e.g., "42_hq.mp3"
        filename = os.path.basename(audio_file_path)
        
        # Extract ID from filename: "42_hq.mp3" -> 42
        # This assumes the format "{id}_hq.mp3"
        id_str = filename.split('_')[0]
        if not id_str.isdigit():
            print(f"Warning: Could not parse numeric ID from filename '{filename}'. Expected format '{{id}}_hq.mp3'.")
            return {"prompt": f"Error: Non-numeric ID in {filename}"}
        
        audio_id = int(id_str)

        # Look up the prompt
        if audio_id in PROMPTS_BY_ID:
            fetched_prompt = PROMPTS_BY_ID[audio_id]
            return {"prompt": fetched_prompt}
        else:
            print(f"Warning: Prompt not found for ID {audio_id} (from file '{filename}'). Using a default prompt.")
            return {"prompt": "default sound effect"} # Fallback prompt

    except Exception as e:
        print(f"Error processing metadata for {audio_file_path}: {e}")
        return {"prompt": "Error during metadata processing"} # General fallback
