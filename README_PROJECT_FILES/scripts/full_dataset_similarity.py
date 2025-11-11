#!/usr/bin/env python3
"""
Improved similarity calculator that properly handles the full 425K dataset
"""

import pandas as pd
import numpy as np
from t5_similarity_finder import T5SimilarityFinder
from tqdm import tqdm
import os
import json
from sklearn.metrics.pairwise import cosine_similarity

class FullDatasetSimilarity:
    """
    Similarity calculator that ensures all 425K prompts are used
    """
    
    def __init__(self, csv_file: str, reference_jsonl: str):
        self.csv_file = csv_file
        self.reference_jsonl = reference_jsonl
        self.df = None
        self.finder = None
        
    def verify_reference_dataset(self):
        """Verify and report on the reference dataset"""
        print("🔍 Verifying reference dataset...")
        
        # Count total lines
        with open(self.reference_jsonl, 'r') as f:
            total_lines = sum(1 for line in f)
        
        print(f"Total lines in {self.reference_jsonl}: {total_lines:,}")
        
        # Sample some prompts to show diversity
        print("\nSample prompts from different parts of the file:")
        sample_indices = [0, total_lines//4, total_lines//2, 3*total_lines//4, total_lines-1]
        
        with open(self.reference_jsonl, 'r') as f:
            lines = f.readlines()
            
        for i, idx in enumerate(sample_indices):
            try:
                data = json.loads(lines[idx].strip())
                print(f"  {idx:,}: {data['prompt'][:80]}...")
            except:
                print(f"  {idx:,}: Error parsing line")
        
        return total_lines
    
    def load_csv(self):
        """Load the CSV file"""
        print(f"📁 Loading CSV: {self.csv_file}")
        self.df = pd.read_csv(self.csv_file)
        print(f"Loaded {len(self.df)} rows")
        
        if 'prompt_english' not in self.df.columns:
            raise ValueError("Column 'prompt_english' not found in CSV")
        
        english_count = self.df['prompt_english'].notna().sum()
        print(f"Found {english_count} English translations")
        
    def initialize_similarity_finder(self):
        """Initialize the T5 similarity finder with detailed logging"""
        print("\n🚀 Initializing T5 similarity finder...")
        
        self.finder = T5SimilarityFinder()
        
        # Load prompts with progress tracking
        print(f"Loading prompts from: {self.reference_jsonl}")
        self.finder.prompts_data = []
        
        with open(self.reference_jsonl, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(tqdm(f, desc="Loading prompts")):
                if line_num % 100000 == 0 and line_num > 0:
                    print(f"   Loaded {line_num:,} prompts...")
                
                try:
                    data = json.loads(line.strip())
                    self.finder.prompts_data.append(data)
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ Loaded {len(self.finder.prompts_data):,} prompts")
        
        # Generate embeddings with progress tracking
        print("\n📊 Generating embeddings for all prompts...")
        prompts_text = [item['prompt'] for item in self.finder.prompts_data]
        
        # Generate embeddings in batches to manage memory
        batch_size = 1000
        all_embeddings = []
        
        for i in tqdm(range(0, len(prompts_text), batch_size), desc="Generating embeddings"):
            batch = prompts_text[i:i+batch_size]
            batch_embeddings = self.finder.model.encode(batch, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
            
            if i % 50000 == 0 and i > 0:
                print(f"   Generated embeddings for {i:,} prompts...")
        
        # Combine all embeddings
        self.finder.embeddings = np.vstack(all_embeddings)
        
        print(f"✅ Generated embeddings: {self.finder.embeddings.shape}")
        print(f"   Embeddings shape: {self.finder.embeddings.shape[0]:,} prompts × {self.finder.embeddings.shape[1]} dimensions")
        
        # Save embeddings for future use
        print("💾 Caching embeddings...")
        import pickle
        with open("prompt_embeddings_full.pkl", 'wb') as f:
            pickle.dump(self.finder.embeddings, f)
        print("✅ Embeddings cached successfully")
        
    def calculate_similarity_counts(self, input_text: str) -> dict:
        """Calculate similarity counts for a single input text"""
        if self.finder.embeddings is None:
            raise ValueError("Embeddings not generated")
        
        # Generate embedding for input
        input_embedding = self.finder.model.encode([input_text])
        
        # Calculate similarities with all reference prompts
        similarities = cosine_similarity(input_embedding, self.finder.embeddings)[0]
        
        # Count by thresholds
        similarity_thresholds = {
            'very_high_similarity': 0.9,
            'high_similarity': 0.8,
            'medium_similarity': 0.7,
            'low_similarity': 0.6
        }
        
        counts = {}
        prev_threshold = 1.0
        
        for label, threshold in similarity_thresholds.items():
            count = np.sum((similarities >= threshold) & (similarities < prev_threshold))
            counts[label] = int(count)
            prev_threshold = threshold
        
        return counts, similarities
    
    def process_all_prompts(self):
        """Process all prompts and calculate similarities"""
        print("\n🔍 Calculating similarities for all prompts...")
        
        # Initialize similarity columns
        similarity_columns = ['very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']
        for col in similarity_columns:
            self.df[col] = 0
        
        # Process each row
        for index, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Processing prompts"):
            english_prompt = row['prompt_english']
            
            if pd.isna(english_prompt) or english_prompt.strip() == '':
                continue
            
            try:
                # Calculate similarity
                similarity_counts, similarities = self.calculate_similarity_counts(str(english_prompt))
                
                # Update DataFrame
                for column_name, count in similarity_counts.items():
                    self.df.at[index, column_name] = count
                
                # Log progress for some prompts
                if index < 5 or index % 20 == 0:
                    total_matches = sum(similarity_counts.values())
                    max_sim = similarities.max()
                    print(f"   Row {index}: '{english_prompt}' -> {total_matches} total matches (max sim: {max_sim:.3f})")
                
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        print("✅ Similarity calculation complete!")
        
    def save_results(self, output_file: str = None):
        """Save results"""
        if output_file is None:
            output_file = self.csv_file
        
        self.df.to_csv(output_file, index=False)
        print(f"📁 Results saved to: {output_file}")
        
    def print_analysis(self):
        """Print detailed analysis"""
        print("\n" + "="*70)
        print("FULL DATASET SIMILARITY ANALYSIS")
        print("="*70)
        
        # Basic stats
        similarity_columns = ['very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']
        
        print(f"Reference dataset size: {len(self.finder.prompts_data):,} prompts")
        print(f"CSV prompts processed: {len(self.df)}")
        
        # Show total matches distribution
        self.df['total_matches'] = self.df[similarity_columns].sum(axis=1)
        
        print(f"\nTotal matches per prompt:")
        total_dist = self.df['total_matches'].value_counts().sort_index()
        for total, count in total_dist.items():
            print(f"  {total} matches: {count} prompts")
        
        # Show similarity statistics
        for col in similarity_columns:
            total_count = self.df[col].sum()
            avg_count = self.df[col].mean()
            max_count = self.df[col].max()
            
            print(f"\n{col.replace('_', ' ').title()}:")
            print(f"  Total: {total_count}, Average: {avg_count:.1f}, Max: {max_count}")
        
        # Show top matches
        print(f"\n🔥 Top prompts with most matches:")
        top_matches = self.df.nlargest(10, 'total_matches')[['プロンプト', 'prompt_english', 'total_matches', 'high_similarity']]
        for i, (idx, row) in enumerate(top_matches.iterrows(), 1):
            print(f"{i:2d}. Total: {row['total_matches']}, High: {row['high_similarity']}")
            print(f"    EN: {row['prompt_english']}")
            print()

def main():
    """Main function"""
    print("🚀 FULL DATASET SIMILARITY ANALYSIS")
    print("Using all 425,294 prompts from the reference dataset")
    print("=" * 60)
    
    # Configuration
    csv_file = "before_ft_with_english_similarity.csv"
    reference_jsonl = "prompts_update.jsonl"
    
    # Check files exist
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file '{csv_file}' not found")
        return
    
    if not os.path.exists(reference_jsonl):
        print(f"❌ Error: Reference JSONL '{reference_jsonl}' not found")
        return
    
    # Create processor
    processor = FullDatasetSimilarity(csv_file, reference_jsonl)
    
    try:
        # Step 1: Verify reference dataset
        total_prompts = processor.verify_reference_dataset()
        
        # Step 2: Load CSV
        processor.load_csv()
        
        # Step 3: Initialize similarity finder
        processor.initialize_similarity_finder()
        
        # Step 4: Process all prompts
        processor.process_all_prompts()
        
        # Step 5: Save results
        processor.save_results()
        
        # Step 6: Print analysis
        processor.print_analysis()
        
        print(f"\n✅ Complete! Now using all {total_prompts:,} reference prompts!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 