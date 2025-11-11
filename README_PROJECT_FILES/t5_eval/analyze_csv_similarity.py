#!/usr/bin/env python3
"""
Script to analyze similarity of prompts in before_ft.csv against prompts_update.jsonl
and add similarity count columns to the CSV
"""

import pandas as pd
import numpy as np
from t5_similarity_finder import T5SimilarityFinder
from typing import Dict
import os
from tqdm import tqdm

class CSVSimilarityAnalyzer:
    """
    Analyzes similarity of prompts in a CSV file against a reference JSONL file
    """
    
    def __init__(self, reference_jsonl: str = "prompts_update.jsonl"):
        """
        Initialize the analyzer
        
        Args:
            reference_jsonl: Path to the reference JSONL file
        """
        self.reference_jsonl = reference_jsonl
        self.finder = T5SimilarityFinder()
        self.similarity_thresholds = {
            'very_high_similarity': 0.9,
            'high_similarity': 0.8,
            'medium_similarity': 0.7,
            'low_similarity': 0.6
        }
        
    def initialize_similarity_finder(self):
        """
        Initialize and prepare the T5 similarity finder
        """
        print("Initializing T5 similarity finder...")
        self.finder.load_prompts(self.reference_jsonl)
        self.finder.generate_embeddings()
        print("T5 similarity finder ready!")
    
    def count_similarities_by_threshold(self, input_text: str) -> Dict[str, int]:
        """
        Count similarities for different threshold ranges
        
        Args:
            input_text: The text to analyze
            
        Returns:
            Dictionary with counts for each similarity range
        """
        if self.finder.embeddings is None:
            raise ValueError("Similarity finder not initialized")
        
        # Generate embedding for input text
        input_embedding = self.finder.model.encode([input_text])
        
        # Calculate similarities with all reference prompts
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(input_embedding, self.finder.embeddings)[0]
        
        # Count similarities in different ranges
        counts = {}
        prev_threshold = 1.0
        
        for label, threshold in self.similarity_thresholds.items():
            count = np.sum((similarities >= threshold) & (similarities < prev_threshold))
            counts[label] = int(count)
            prev_threshold = threshold
        
        return counts
    
    def process_csv(self, csv_file: str, output_file: str = None) -> pd.DataFrame:
        """
        Process the CSV file and add similarity count columns
        
        Args:
            csv_file: Path to the input CSV file
            output_file: Path to the output CSV file (if None, overwrites input)
            
        Returns:
            DataFrame with added similarity columns
        """
        print(f"Loading CSV file: {csv_file}")
        
        # Load CSV file
        df = pd.read_csv(csv_file)
        
        # Check if the prompt column exists
        if 'プロンプト' not in df.columns:
            raise ValueError("Column 'プロンプト' not found in CSV file")
        
        print(f"Found {len(df)} rows to process")
        
        # Initialize similarity finder
        self.initialize_similarity_finder()
        
        # Initialize new columns
        for column_name in self.similarity_thresholds.keys():
            df[column_name] = 0
        
        # Process each row
        print("Analyzing similarities for each prompt...")
        
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing prompts"):
            prompt = row['プロンプト']
            
            # Skip if prompt is empty or NaN
            if pd.isna(prompt) or prompt.strip() == '':
                continue
            
            try:
                # Get similarity counts for this prompt
                similarity_counts = self.count_similarities_by_threshold(str(prompt))
                
                # Update the DataFrame
                for column_name, count in similarity_counts.items():
                    df.at[index, column_name] = count
                    
            except Exception as e:
                print(f"Error processing row {index} (prompt: '{prompt}'): {e}")
                continue
        
        # Save the updated CSV
        if output_file is None:
            output_file = csv_file
        
        df.to_csv(output_file, index=False)
        print(f"Updated CSV saved to: {output_file}")
        
        return df
    
    def print_summary(self, df: pd.DataFrame):
        """
        Print a summary of the similarity analysis
        
        Args:
            df: The processed DataFrame
        """
        print("\n" + "="*60)
        print("SIMILARITY ANALYSIS SUMMARY")
        print("="*60)
        
        total_prompts = len(df)
        print(f"Total prompts analyzed: {total_prompts}")
        
        # Calculate statistics for each similarity column
        for column_name in self.similarity_thresholds.keys():
            if column_name in df.columns:
                total_count = df[column_name].sum()
                avg_count = df[column_name].mean()
                max_count = df[column_name].max()
                
                print(f"\n{column_name.replace('_', ' ').title()}:")
                print(f"  Total matches: {total_count}")
                print(f"  Average per prompt: {avg_count:.2f}")
                print(f"  Maximum matches: {max_count}")
        
        # Show prompts with highest similarities
        print(f"\nTop 5 prompts with most high similarities:")
        top_high_sim = df.nlargest(5, 'high_similarity')[['プロンプト', 'high_similarity']]
        for index, row in top_high_sim.iterrows():
            print(f"  '{row['プロンプト']}' - {row['high_similarity']} matches")
        
        print(f"\nTop 5 prompts with most medium similarities:")
        top_medium_sim = df.nlargest(5, 'medium_similarity')[['プロンプト', 'medium_similarity']]
        for index, row in top_medium_sim.iterrows():
            print(f"  '{row['プロンプト']}' - {row['medium_similarity']} matches")

def main():
    """
    Main function to run the CSV similarity analysis
    """
    # Configuration
    input_csv = "before_ft.csv"
    output_csv = "before_ft_with_similarities.csv"
    reference_jsonl = "prompts_update.jsonl"
    
    # Check if input files exist
    if not os.path.exists(input_csv):
        print(f"Error: Input CSV file '{input_csv}' not found")
        return
    
    if not os.path.exists(reference_jsonl):
        print(f"Error: Reference JSONL file '{reference_jsonl}' not found")
        return
    
    # Create analyzer
    analyzer = CSVSimilarityAnalyzer(reference_jsonl)
    
    try:
        # Process the CSV
        df = analyzer.process_csv(input_csv, output_csv)
        
        # Print summary
        analyzer.print_summary(df)
        
        print(f"\n✅ Analysis complete! Results saved to: {output_csv}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return

if __name__ == "__main__":
    main() 