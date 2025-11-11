#!/usr/bin/env python3
"""
Script to translate Japanese prompts to English using GPT-4.1 and then calculate similarity
"""

import pandas as pd
import json
from openai import OpenAI
from tqdm import tqdm
import time
from analyze_csv_similarity import CSVSimilarityAnalyzer
import os

# OpenAI API key from generate_prompt.py
openai_key = 

client = OpenAI(api_key=openai_key)

def translate_to_english(japanese_prompt: str) -> str:
    """
    Translate Japanese audio prompt to English using GPT-4.1
    
    Args:
        japanese_prompt: Japanese text to translate
        
    Returns:
        English translation
    """
    
    prompt = '''
You are an expert translator specializing in audio and sound descriptions.

## Goal
Translate the given Japanese audio prompt to English. The translation should be:
- Natural and concise English
- Preserve the specific audio/sound meaning
- Use common English terms for audio production and sound effects
- Keep technical terms accurate (e.g., "808のキック" -> "808 kick")

## Instructions
- Translate the Japanese text to English
- Keep it short and descriptive
- Focus on the audio/sound aspect
- Use standard English audio terminology
- If the input is not a valid audio description, return exactly: "invalid audio prompt"

## Examples
Input: "電車が走る音"
Output: "train running sound"

Input: "海の波の音"
Output: "ocean wave sound"

Input: "808のキック"
Output: "808 kick"

Input: "スネアドラムの音"
Output: "snare drum sound"

Input: "ピアノのドの音"
Output: "piano C note"

Now translate this Japanese audio prompt to English:
'''
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini as it's more cost-effective and available
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": japanese_prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent translations
            max_completion_tokens=100,  # Short translations
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        translation = response.choices[0].message.content.strip()
        
        # Handle edge cases
        if translation.lower() == "invalid audio prompt":
            return japanese_prompt  # Keep original if invalid
        
        return translation
        
    except Exception as e:
        print(f"Error translating '{japanese_prompt}': {e}")
        return japanese_prompt  # Return original on error

class TranslateAndAnalyze:
    """
    Class to handle translation and similarity analysis
    """
    
    def __init__(self, input_csv: str, reference_jsonl: str):
        self.input_csv = input_csv
        self.reference_jsonl = reference_jsonl
        self.df = None
        
    def load_csv(self):
        """Load the CSV file"""
        print(f"Loading CSV: {self.input_csv}")
        self.df = pd.read_csv(self.input_csv)
        print(f"Loaded {len(self.df)} rows")
        
    def add_english_translations(self):
        """Add English translations for Japanese prompts"""
        print("🌐 Translating Japanese prompts to English...")
        
        # Initialize English prompt column
        self.df['prompt_english'] = ""
        
        # Process each row
        for index, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Translating prompts"):
            japanese_prompt = row['プロンプト']
            
            # Skip if prompt is empty or NaN
            if pd.isna(japanese_prompt) or japanese_prompt.strip() == '':
                continue
                
            try:
                # Translate to English
                english_prompt = translate_to_english(str(japanese_prompt))
                self.df.at[index, 'prompt_english'] = english_prompt
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                self.df.at[index, 'prompt_english'] = str(japanese_prompt)
                continue
        
        print("✅ Translation complete!")
        
    def calculate_similarity_with_english(self):
        """Calculate similarity using English prompts"""
        print("🔍 Calculating similarity using English prompts...")
        
        # Create a custom analyzer that uses English prompts
        analyzer = CSVSimilarityAnalyzer(self.reference_jsonl)
        
        # Initialize similarity finder
        analyzer.initialize_similarity_finder()
        
        # Initialize similarity columns
        similarity_columns = ['very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']
        for col in similarity_columns:
            self.df[col] = 0
        
        # Process each row using English prompts
        for index, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Analyzing similarity"):
            english_prompt = row['prompt_english']
            
            # Skip if English prompt is empty
            if pd.isna(english_prompt) or english_prompt.strip() == '':
                continue
                
            try:
                # Get similarity counts for English prompt
                similarity_counts = analyzer.count_similarities_by_threshold(str(english_prompt))
                
                # Update the DataFrame
                for column_name, count in similarity_counts.items():
                    self.df.at[index, column_name] = count
                    
            except Exception as e:
                print(f"Error processing similarity for row {index}: {e}")
                continue
        
        print("✅ Similarity analysis complete!")
        
    def save_results(self, output_file: str):
        """Save results to CSV"""
        self.df.to_csv(output_file, index=False)
        print(f"📁 Results saved to: {output_file}")
        
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("TRANSLATION & SIMILARITY ANALYSIS SUMMARY")
        print("="*60)
        
        # Translation summary
        translated_count = self.df['prompt_english'].notna().sum()
        print(f"Total prompts translated: {translated_count}")
        
        # Show some examples
        print("\nTranslation examples:")
        sample_translations = self.df[['プロンプト', 'prompt_english']].head(5)
        for index, row in sample_translations.iterrows():
            print(f"  JP: {row['プロンプト']}")
            print(f"  EN: {row['prompt_english']}")
            print()
        
        # Similarity summary
        similarity_columns = ['very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']
        for col in similarity_columns:
            if col in self.df.columns:
                total_count = self.df[col].sum()
                avg_count = self.df[col].mean()
                max_count = self.df[col].max()
                
                print(f"\n{col.replace('_', ' ').title()}:")
                print(f"  Total matches: {total_count}")
                print(f"  Average per prompt: {avg_count:.2f}")
                print(f"  Maximum matches: {max_count}")
        
        # Show top prompts with most similarities
        print(f"\nTop 5 prompts with most high similarities:")
        top_sim = self.df.nlargest(5, 'high_similarity')[['プロンプト', 'prompt_english', 'high_similarity']]
        for index, row in top_sim.iterrows():
            print(f"  JP: {row['プロンプト']}")
            print(f"  EN: {row['prompt_english']}")
            print(f"  High similarity matches: {row['high_similarity']}")
            print()

def main():
    """Main function"""
    print("🚀 Starting Translation and Similarity Analysis")
    print("=" * 50)
    
    # Configuration
    input_csv = "before_ft.csv"
    output_csv = "before_ft_with_english_similarity.csv"
    reference_jsonl = "prompts_update.jsonl"
    
    # Check if files exist
    if not os.path.exists(input_csv):
        print(f"❌ Error: Input CSV '{input_csv}' not found")
        return
        
    if not os.path.exists(reference_jsonl):
        print(f"❌ Error: Reference JSONL '{reference_jsonl}' not found")
        return
    
    # Create analyzer
    analyzer = TranslateAndAnalyze(input_csv, reference_jsonl)
    
    try:
        # Step 1: Load CSV
        analyzer.load_csv()
        
        # Step 2: Add English translations
        analyzer.add_english_translations()
        
        # Step 3: Calculate similarity using English prompts
        analyzer.calculate_similarity_with_english()
        
        # Step 4: Save results
        analyzer.save_results(output_csv)
        
        # Step 5: Print summary
        analyzer.print_summary()
        
        print(f"\n✅ Complete! Results saved to: {output_csv}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return

if __name__ == "__main__":
    main() 