#!/usr/bin/env python3
"""
Focused script to get only very high similarity IDs (>0.9) for each prompt
"""

import pandas as pd
import numpy as np
from t5_similarity_finder import T5SimilarityFinder
from tqdm import tqdm
import os
import json
from sklearn.metrics.pairwise import cosine_similarity

class VeryHighSimilarityIDs:
    """
    Get only very high similarity IDs (>0.9) for each prompt
    """
    
    def __init__(self, csv_file: str, reference_jsonl: str):
        self.csv_file = csv_file
        self.reference_jsonl = reference_jsonl
        self.df = None
        self.finder = None
        
    def load_csv(self):
        """Load the CSV file"""
        print(f"📁 Loading CSV: {self.csv_file}")
        self.df = pd.read_csv(self.csv_file)
        print(f"Loaded {len(self.df)} rows")
        
        if 'prompt_english' not in self.df.columns:
            raise ValueError("Column 'prompt_english' not found in CSV")
        
        english_count = self.df['prompt_english'].notna().sum()
        print(f"Found {english_count} English translations")
        
    def load_similarity_finder(self):
        """Load the similarity finder with cached embeddings"""
        print("\n🚀 Loading T5 similarity finder...")
        
        self.finder = T5SimilarityFinder()
        
        # Check if we have cached embeddings from the previous run
        if os.path.exists("prompt_embeddings_full.pkl"):
            print("Loading cached embeddings...")
            import pickle
            with open("prompt_embeddings_full.pkl", 'rb') as f:
                self.finder.embeddings = pickle.load(f)
            
            # Load the prompts data
            print("Loading prompts data...")
            self.finder.prompts_data = []
            with open(self.reference_jsonl, 'r', encoding='utf-8') as f:
                for line in tqdm(f, desc="Loading prompts"):
                    try:
                        data = json.loads(line.strip())
                        self.finder.prompts_data.append(data)
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Loaded {len(self.finder.prompts_data):,} prompts")
            print(f"✅ Loaded embeddings: {self.finder.embeddings.shape}")
        else:
            print("❌ No cached embeddings found. Please run full_dataset_similarity.py first.")
            raise FileNotFoundError("Cached embeddings not found")
        
    def get_very_high_similarity_ids(self, input_text: str) -> dict:
        """Get IDs of prompts with very high similarity (>0.9)"""
        if self.finder.embeddings is None:
            raise ValueError("Embeddings not loaded")
        
        # Generate embedding for input
        input_embedding = self.finder.model.encode([input_text])
        
        # Calculate similarities with all reference prompts
        similarities = cosine_similarity(input_embedding, self.finder.embeddings)[0]
        
        # Find indices where similarity is >= 0.9
        very_high_mask = similarities >= 0.9
        very_high_indices = np.where(very_high_mask)[0]
        
        # Get the IDs and similarity scores for very high matches
        very_high_results = []
        for idx in very_high_indices:
            prompt_id = self.finder.prompts_data[idx]['id']
            score = similarities[idx]
            prompt_text = self.finder.prompts_data[idx]['prompt']
            very_high_results.append({
                'id': prompt_id, 
                'similarity': float(score),
                'prompt': prompt_text
            })
        
        # Sort by similarity (descending)
        very_high_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'count': len(very_high_results),
            'results': very_high_results
        }
        
    def process_all_prompts(self):
        """Process all prompts and collect very high similarity IDs"""
        print("\n🔍 Finding very high similarity IDs (>0.9) for all prompts...")
        
        # Initialize columns
        self.df['very_high_similarity_count'] = 0
        self.df['very_high_similarity_ids'] = ""
        
        # Results for detailed export
        all_results = []
        
        # Process each row
        for index, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Processing prompts"):
            english_prompt = row['prompt_english']
            
            if pd.isna(english_prompt) or english_prompt.strip() == '':
                continue
            
            try:
                # Get very high similarity results
                results = self.get_very_high_similarity_ids(str(english_prompt))
                
                # Update count
                self.df.at[index, 'very_high_similarity_count'] = results['count']
                
                # Store IDs as JSON string
                ids_only = [item['id'] for item in results['results']]
                self.df.at[index, 'very_high_similarity_ids'] = json.dumps(ids_only)
                
                # Collect for detailed export
                if results['count'] > 0:
                    detailed_result = {
                        'row_index': index,
                        'japanese_prompt': row['プロンプト'],
                        'english_prompt': row['prompt_english'],
                        'very_high_count': results['count'],
                        'very_high_matches': results['results']
                    }
                    all_results.append(detailed_result)
                
                # Log progress
                if index < 5 or index % 20 == 0:
                    print(f"   Row {index}: '{english_prompt}' -> {results['count']} very high matches")
                    if results['count'] > 0:
                        top_ids = [item['id'] for item in results['results'][:3]]
                        top_scores = [f"{item['similarity']:.3f}" for item in results['results'][:3]]
                        print(f"     Top matches: {list(zip(top_ids, top_scores))}")
                
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        # Save detailed results
        self.save_detailed_results(all_results)
        
        print("✅ Very high similarity ID collection complete!")
        
    def save_detailed_results(self, all_results):
        """Save detailed very high similarity results"""
        output_file = "very_high_similarity_details.jsonl"
        print(f"\n📤 Saving detailed results to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in all_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"✅ Detailed results saved to {output_file}")
        
    def save_csv_results(self, output_file: str = None):
        """Save CSV with very high similarity IDs"""
        if output_file is None:
            output_file = "before_ft_with_very_high_ids.csv"
        
        self.df.to_csv(output_file, index=False)
        print(f"📁 CSV with very high similarity IDs saved to: {output_file}")
        
    def print_analysis(self):
        """Print analysis of very high similarity results"""
        print("\n" + "="*60)
        print("VERY HIGH SIMILARITY ANALYSIS (>0.9)")
        print("="*60)
        
        print(f"Reference dataset size: {len(self.finder.prompts_data):,} prompts")
        print(f"CSV prompts processed: {len(self.df)}")
        
        # Statistics
        total_very_high = self.df['very_high_similarity_count'].sum()
        avg_very_high = self.df['very_high_similarity_count'].mean()
        max_very_high = self.df['very_high_similarity_count'].max()
        prompts_with_matches = (self.df['very_high_similarity_count'] > 0).sum()
        
        print(f"\nVery High Similarity Statistics:")
        print(f"  Total very high matches across all prompts: {total_very_high:,}")
        print(f"  Average very high matches per prompt: {avg_very_high:.1f}")
        print(f"  Maximum very high matches for one prompt: {max_very_high:,}")
        print(f"  Prompts with very high matches: {prompts_with_matches}/{len(self.df)}")
        
        # Show top prompts with most very high matches
        print(f"\n🔥 Top prompts with most very high similarity matches:")
        top_prompts = self.df.nlargest(10, 'very_high_similarity_count')[
            ['プロンプト', 'prompt_english', 'very_high_similarity_count']
        ]
        
        for i, (index, row) in enumerate(top_prompts.iterrows(), 1):
            print(f"{i:2d}. {row['very_high_similarity_count']:,} matches")
            print(f"    JP: {row['プロンプト']}")
            print(f"    EN: {row['prompt_english']}")
            
            # Show first few IDs
            if row['very_high_similarity_count'] > 0:
                ids = json.loads(row['very_high_similarity_ids'])
                print(f"    First few IDs: {ids[:5]}")
            print()

def main():
    """Main function"""
    print("🚀 VERY HIGH SIMILARITY ID COLLECTION")
    print("Collecting IDs of prompts with >0.9 similarity")
    print("=" * 50)
    
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
    processor = VeryHighSimilarityIDs(csv_file, reference_jsonl)
    
    try:
        # Step 1: Load CSV
        processor.load_csv()
        
        # Step 2: Load similarity finder with cached embeddings
        processor.load_similarity_finder()
        
        # Step 3: Process all prompts and collect very high IDs
        processor.process_all_prompts()
        
        # Step 4: Save CSV results
        processor.save_csv_results()
        
        # Step 5: Print analysis
        processor.print_analysis()
        
        print(f"\n✅ Complete! Very high similarity IDs collected!")
        print(f"📁 Check 'before_ft_with_very_high_ids.csv' for the results")
        print(f"📁 Check 'very_high_similarity_details.jsonl' for detailed information")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 