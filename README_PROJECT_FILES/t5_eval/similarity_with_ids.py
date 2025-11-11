#!/usr/bin/env python3
"""
Enhanced similarity calculator that returns the actual IDs of similar prompts
"""

import pandas as pd
import numpy as np
from t5_similarity_finder import T5SimilarityFinder
from tqdm import tqdm
import os
import json
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityWithIDs:
    """
    Similarity calculator that returns actual IDs of similar prompts
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
        
    def get_similar_prompt_ids(self, input_text: str) -> dict:
        """Get IDs of similar prompts for different similarity thresholds"""
        if self.finder.embeddings is None:
            raise ValueError("Embeddings not loaded")
        
        # Generate embedding for input
        input_embedding = self.finder.model.encode([input_text])
        
        # Calculate similarities with all reference prompts
        similarities = cosine_similarity(input_embedding, self.finder.embeddings)[0]
        
        # Define thresholds
        similarity_thresholds = {
            'very_high_similarity': 0.9,
            'high_similarity': 0.8,
            'medium_similarity': 0.7,
            'low_similarity': 0.6
        }
        
        # Collect IDs for each threshold
        results = {}
        prev_threshold = 1.0
        
        for label, threshold in similarity_thresholds.items():
            # Find indices where similarity is in this range
            mask = (similarities >= threshold) & (similarities < prev_threshold)
            indices = np.where(mask)[0]
            
            # Get the IDs and similarity scores for these indices
            ids_and_scores = []
            for idx in indices:
                prompt_id = self.finder.prompts_data[idx]['id']
                score = similarities[idx]
                ids_and_scores.append({'id': prompt_id, 'similarity': float(score)})
            
            # Sort by similarity (descending)
            ids_and_scores.sort(key=lambda x: x['similarity'], reverse=True)
            
            results[label] = {
                'count': len(ids_and_scores),
                'ids': [item['id'] for item in ids_and_scores],
                'scores': [item['similarity'] for item in ids_and_scores]
            }
            
            prev_threshold = threshold
        
        return results
        
    def process_all_prompts(self):
        """Process all prompts and collect similar IDs"""
        print("\n🔍 Finding similar prompt IDs for all prompts...")
        
        # Initialize columns
        similarity_columns = ['very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']
        id_columns = ['very_high_ids', 'high_similarity_ids', 'medium_similarity_ids', 'low_similarity_ids']
        
        for col in similarity_columns:
            self.df[col] = 0
        for col in id_columns:
            self.df[col] = ""
        
        # Process each row
        for index, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Processing prompts"):
            english_prompt = row['prompt_english']
            
            if pd.isna(english_prompt) or english_prompt.strip() == '':
                continue
            
            try:
                # Get similarity results with IDs
                results = self.get_similar_prompt_ids(str(english_prompt))
                
                # Update counts
                for similarity_label, data in results.items():
                    self.df.at[index, similarity_label] = data['count']
                
                # Update ID lists (store as JSON strings)
                self.df.at[index, 'very_high_ids'] = json.dumps(results['very_high_similarity']['ids'])
                self.df.at[index, 'high_similarity_ids'] = json.dumps(results['high_similarity']['ids'])
                self.df.at[index, 'medium_similarity_ids'] = json.dumps(results['medium_similarity']['ids'])
                self.df.at[index, 'low_similarity_ids'] = json.dumps(results['low_similarity']['ids'])
                
                # Log progress for some prompts
                if index < 3 or index % 20 == 0:
                    high_count = results['high_similarity']['count']
                    high_ids = results['high_similarity']['ids'][:5]  # Show first 5 IDs
                    print(f"   Row {index}: '{english_prompt}' -> {high_count} high similarity matches")
                    print(f"     First few high similarity IDs: {high_ids}")
                
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        print("✅ ID collection complete!")
        
    def save_results(self, output_file: str = None):
        """Save results with IDs"""
        if output_file is None:
            output_file = "before_ft_with_similarity_ids.csv"
        
        self.df.to_csv(output_file, index=False)
        print(f"📁 Results with IDs saved to: {output_file}")
        
    def print_analysis(self):
        """Print analysis with ID information"""
        print("\n" + "="*70)
        print("SIMILARITY ANALYSIS WITH IDs")
        print("="*70)
        
        print(f"Reference dataset size: {len(self.finder.prompts_data):,} prompts")
        print(f"CSV prompts processed: {len(self.df)}")
        
        # Show examples of high similarity matches
        print(f"\n🔥 Examples of high similarity matches:")
        
        for index, row in self.df.head(5).iterrows():
            english_prompt = row['prompt_english']
            high_count = row['high_similarity']
            
            if high_count > 0:
                high_ids = json.loads(row['high_similarity_ids'])
                print(f"\n{index+1}. '{english_prompt}'")
                print(f"   High similarity count: {high_count}")
                print(f"   High similarity IDs: {high_ids[:10]}")  # Show first 10 IDs
                if len(high_ids) > 10:
                    print(f"   ... and {len(high_ids) - 10} more")
        
        # Statistics
        print(f"\nStatistics:")
        print(f"  Average high similarity matches per prompt: {self.df['high_similarity'].mean():.1f}")
        print(f"  Max high similarity matches: {self.df['high_similarity'].max()}")
        print(f"  Min high similarity matches: {self.df['high_similarity'].min()}")
        
    def export_high_similarity_details(self, output_file: str = "high_similarity_details.jsonl"):
        """Export detailed high similarity information"""
        print(f"\n📤 Exporting high similarity details to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for index, row in self.df.iterrows():
                if row['high_similarity'] > 0:
                    high_ids = json.loads(row['high_similarity_ids'])
                    
                    detail = {
                        'row_index': index,
                        'japanese_prompt': row['プロンプト'],
                        'english_prompt': row['prompt_english'],
                        'high_similarity_count': row['high_similarity'],
                        'high_similarity_ids': high_ids
                    }
                    
                    f.write(json.dumps(detail, ensure_ascii=False) + '\n')
        
        print(f"✅ High similarity details exported to {output_file}")

def main():
    """Main function"""
    print("🚀 SIMILARITY ANALYSIS WITH IDs")
    print("Collecting actual IDs of similar prompts")
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
    processor = SimilarityWithIDs(csv_file, reference_jsonl)
    
    try:
        # Step 1: Load CSV
        processor.load_csv()
        
        # Step 2: Load similarity finder with cached embeddings
        processor.load_similarity_finder()
        
        # Step 3: Process all prompts and collect IDs
        processor.process_all_prompts()
        
        # Step 4: Save results
        processor.save_results()
        
        # Step 5: Export detailed high similarity information
        processor.export_high_similarity_details()
        
        # Step 6: Print analysis
        processor.print_analysis()
        
        print(f"\n✅ Complete! IDs of similar prompts collected and saved!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 