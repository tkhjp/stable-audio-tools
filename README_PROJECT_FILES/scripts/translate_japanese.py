#!/usr/bin/env python3
"""
Japanese to English DataFrame Translation Script

Translates Japanese onomatopoeia and names to English using OpenAI API
"""

import pandas as pd
import time
import logging
from typing import List, Dict
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Assuming you already have client set up
# client = OpenAI(api_key='your-key-here')

def translate_onomatopoeia_batch(client: OpenAI, japanese_words: List[str]) -> List[str]:
    """
    Translate Japanese onomatopoeia to English in batches
    """
    
    # Create a single prompt for batch translation
    words_list = "\n".join([f"{i+1}. {word}" for i, word in enumerate(japanese_words)])
    
    prompt = f"""
Translate these Japanese onomatopoeia (sound words) to English. Provide the English equivalent sound or onomatopoeia that best represents the same sound.

Guidelines:
- Translate to English onomatopoeia when possible (e.g., チーン → "ding", ポン → "pop")
- If no direct English onomatopoeia exists, provide a brief description of the sound
- Keep translations concise (1-3 words maximum)
- Maintain the same numbering

Japanese onomatopoeia to translate:
{words_list}

Provide the translations in the exact same numbered format:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in Japanese onomatopoeia and sound words."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse the response
        response_text = response.choices[0].message.content.strip()
        translations = []
        
        # Extract translations from numbered list
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and any(char.isdigit() for char in line[:5]):  # Check if line starts with number
                # Extract text after the number and period/dot
                parts = line.split('.', 1)
                if len(parts) > 1:
                    translation = parts[1].strip()
                    translations.append(translation)
        
        return translations
        
    except Exception as e:
        logger.error(f"Error in batch translation: {e}")
        return [f"Translation error: {word}" for word in japanese_words]

def translate_names_batch(client: OpenAI, japanese_names: List[str]) -> List[str]:
    """
    Translate Japanese sound/object names to English in batches
    """
    
    # Create a single prompt for batch translation
    names_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(japanese_names)])
    
    prompt = f"""
Translate these Japanese sound descriptions and object names to English. These are descriptions of sounds or musical instruments/objects.

Guidelines:
- Provide clear, concise English translations
- For sound descriptions, focus on what makes the sound (e.g., "sound of something falling into a pot")
- For instrument/object names, provide the standard English name
- Keep translations natural and descriptive
- Maintain the same numbering

Japanese names/descriptions to translate:
{names_list}

Provide the translations in the exact same numbered format:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in Japanese sound descriptions and musical instruments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        # Parse the response
        response_text = response.choices[0].message.content.strip()
        translations = []
        
        # Extract translations from numbered list
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and any(char.isdigit() for char in line[:5]):  # Check if line starts with number
                # Extract text after the number and period/dot
                parts = line.split('.', 1)
                if len(parts) > 1:
                    translation = parts[1].strip()
                    translations.append(translation)
        
        return translations
        
    except Exception as e:
        logger.error(f"Error in batch translation: {e}")
        return [f"Translation error: {name}" for name in japanese_names]

def translate_dataframe_column(client: OpenAI, df: pd.DataFrame, column_name: str, 
                             translation_type: str = "onomatopoeia", batch_size: int = 20) -> pd.DataFrame:
    """
    Translate a dataframe column from Japanese to English
    
    Args:
        client: OpenAI client
        df: DataFrame to translate
        column_name: Name of the column to translate
        translation_type: "onomatopoeia" or "names"
        batch_size: Number of items to translate in each batch
    
    Returns:
        DataFrame with added English translation column
    """
    
    df_copy = df.copy()
    japanese_values = df_copy[column_name].tolist()
    all_translations = []
    
    logger.info(f"Translating {len(japanese_values)} {translation_type} in batches of {batch_size}")
    
    # Process in batches
    for i in range(0, len(japanese_values), batch_size):
        batch = japanese_values[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(japanese_values) + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        if translation_type == "onomatopoeia":
            translations = translate_onomatopoeia_batch(client, batch)
        else:
            translations = translate_names_batch(client, batch)
        
        all_translations.extend(translations)
        
        # Rate limiting
        time.sleep(1)
    
    # Ensure we have the right number of translations
    if len(all_translations) != len(japanese_values):
        logger.warning(f"Translation count mismatch: {len(all_translations)} vs {len(japanese_values)}")
        # Pad with fallback translations if needed
        while len(all_translations) < len(japanese_values):
            all_translations.append("Translation pending")
    
    # Add English column
    english_column_name = f"{column_name}_english"
    df_copy[english_column_name] = all_translations[:len(japanese_values)]
    
    return df_copy

def translate_both_dataframes(client: OpenAI, onomatopoeia_df: pd.DataFrame, 
                            japanese_name_df: pd.DataFrame) -> tuple:
    """
    Translate both dataframes and return the results
    """
    
    logger.info("🚀 Starting translation of both dataframes")
    
    # Translate onomatopoeia dataframe
    logger.info("📝 Translating onomatopoeia dataframe...")
    translated_onomatopoeia = translate_dataframe_column(
        client, onomatopoeia_df, "onomatopoeia", "onomatopoeia"
    )
    
    # Translate names dataframe
    logger.info("📝 Translating names dataframe...")
    translated_names = translate_dataframe_column(
        client, japanese_name_df, "name", "names"
    )
    
    logger.info("✅ Translation complete!")
    
    # Show preview of results
    logger.info("\n📋 Onomatopoeia Translation Preview:")
    print(translated_onomatopoeia.head(10))
    
    logger.info("\n📋 Names Translation Preview:")
    print(translated_names.head(10))
    
    return translated_onomatopoeia, translated_names

def save_translated_dataframes(translated_onomatopoeia: pd.DataFrame, 
                             translated_names: pd.DataFrame,
                             output_dir: str = "translated_dataframes"):
    """
    Save the translated dataframes to files
    """
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as CSV
    onomatopoeia_path = os.path.join(output_dir, "translated_onomatopoeia.csv")
    names_path = os.path.join(output_dir, "translated_names.csv")
    
    translated_onomatopoeia.to_csv(onomatopoeia_path, index=False, encoding='utf-8')
    translated_names.to_csv(names_path, index=False, encoding='utf-8')
    
    logger.info(f"💾 Saved translated dataframes:")
    logger.info(f"  - Onomatopoeia: {onomatopoeia_path}")
    logger.info(f"  - Names: {names_path}")

# Example usage function
def example_usage():
    """
    Example of how to use the translation functions
    """
    
    # Initialize your OpenAI client (replace with your actual key)
    client = OpenAI(api_key='your-openai-key-here')
    
    # Create sample dataframes (replace with your actual dataframes)
    onomatopoeia_df = pd.DataFrame({
        'onomatopoeia': ['チーン', 'カラカラ', 'ポン', 'チキチキ', 'ピーン']
    })
    
    japanese_name_df = pd.DataFrame({
        'name': ['チャイム', '何かが伸びる音', '鍋に何かが落ちる音', 'トライアングル', '錫']
    })
    
    # Translate both dataframes
    translated_onomatopoeia, translated_names = translate_both_dataframes(
        client, onomatopoeia_df, japanese_name_df
    )
    
    # Save the results
    save_translated_dataframes(translated_onomatopoeia, translated_names)
    
    return translated_onomatopoeia, translated_names

if __name__ == "__main__":
    # Run example (uncomment and modify as needed)
    # example_usage()
    print("Translation script loaded. Use the functions with your actual dataframes and OpenAI client.") 