import pandas as pd
import os
from sentence_transformers import SentenceTransformer, util
import numpy as np
from tqdm import tqdm

def combine_datasets():
    """Combine test.csv, train.csv, and val.csv into one DataFrame."""
    print("Reading CSV files...")
    
    dataframes = []
    sources = []
    
    for filename in ['test.csv', 'train.csv', 'val.csv']:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            dataframes.append(df)
            sources.extend([filename.replace('.csv', '')] * len(df))
            print(f"✓ Loaded {filename}: {len(df)} rows")
        else:
            print(f"✗ File not found: {filename}")
    
    if not dataframes:
        print("No CSV files found!")
        return None
    
    # Combine all DataFrames
    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df['dataset_source'] = sources
    
    print(f"\n✓ Combined dataset: {len(combined_df)} total rows")
    print(f"Dataset distribution:")
    print(combined_df['dataset_source'].value_counts())
    
    # Save combined dataset
    combined_df.to_csv('combined_dataset.csv', index=False)
    print(f"✓ Saved to combined_dataset.csv")
    
    return combined_df

def find_similar_captions_for_prompts(prompts_file='prompts.csv', combined_file='combined_dataset.csv'):
    """Find the most similar caption for each prompt using sentence transformers."""
    
    # Load datasets
    print(f"\nLoading {prompts_file}...")
    if not os.path.exists(prompts_file):
        print(f"Error: {prompts_file} not found!")
        return None
    
    print(f"Loading {combined_file}...")
    if not os.path.exists(combined_file):
        print(f"Error: {combined_file} not found!")
        return None
    
    prompts_df = pd.read_csv(prompts_file)
    combined_df = pd.read_csv(combined_file)
    
    print(f"✓ Loaded {len(prompts_df)} prompts")
    print(f"✓ Loaded {len(combined_df)} captions")
    
    # Initialize sentence transformer model
    print("\nLoading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✓ Model loaded")
    
    # Encode prompts and captions
    print("\nEncoding prompts...")
    prompt_embeddings = model.encode(prompts_df['Prompt_EN'].tolist(), show_progress_bar=True)
    
    print("Encoding captions...")
    caption_embeddings = model.encode(combined_df['caption'].tolist(), show_progress_bar=True)
    
    # Find most similar caption for each prompt
    print("\nFinding most similar captions...")
    results = []
    
    for i, prompt_embedding in enumerate(tqdm(prompt_embeddings, desc="Processing prompts")):
        # Compute cosine similarities
        similarities = util.cos_sim(prompt_embedding, caption_embeddings)[0]
        
        # Find best match
        best_idx = similarities.argmax().item()
        best_score = similarities[best_idx].item()
        
        # Get prompt and caption info
        prompt_row = prompts_df.iloc[i]
        caption_row = combined_df.iloc[best_idx]
        
        result = {
            'Prompt_ID': prompt_row['ID'],
            'Category': prompt_row['Category'],
            'Prompt_EN': prompt_row['Prompt_EN'],
            'Prompt_JP': prompt_row['Prompt_JP'],
            'Tag': prompt_row['Tag'],
            'Most_Similar_Caption': caption_row['caption'],
            'Similarity_Score': best_score,
            'audiocap_id': caption_row['audiocap_id'],
            'youtube_id': caption_row['youtube_id'],
            'start_time': caption_row['start_time'],
            'dataset_source': caption_row.get('dataset_source', 'unknown')
        }
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    output_file = 'eval_prompts.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved results to {output_file}")
    
    # Display summary
    print(f"\nSummary:")
    print(f"- Average similarity score: {results_df['Similarity_Score'].mean():.4f}")
    print(f"- Min similarity score: {results_df['Similarity_Score'].min():.4f}")
    print(f"- Max similarity score: {results_df['Similarity_Score'].max():.4f}")
    print(f"- Source distribution:")
    print(results_df['dataset_source'].value_counts())
    
    # Show top 5 matches
    print(f"\nTop 5 most similar matches:")
    top_matches = results_df.nlargest(5, 'Similarity_Score')[['Prompt_ID', 'Prompt_EN', 'Most_Similar_Caption', 'Similarity_Score']]
    for _, row in top_matches.iterrows():
        print(f"ID {row['Prompt_ID']}: {row['Similarity_Score']:.4f}")
        print(f"  Prompt: {row['Prompt_EN']}")
        print(f"  Caption: {row['Most_Similar_Caption']}")
        print()
    
    return results_df

def main():
    """Main function to combine datasets and find similar captions."""
    print("=== Audio Dataset Processing ===")
    
    # Step 1: Combine datasets
    print("\n1. Combining datasets...")
    combined_df = combine_datasets()
    
    if combined_df is None:
        print("Failed to combine datasets. Exiting.")
        return
    
    # Step 2: Find similar captions
    print("\n2. Finding similar captions for prompts...")
    results_df = find_similar_captions_for_prompts()
    
    if results_df is not None:
        print("\n✓ Process completed successfully!")
        print("Files created:")
        print("- combined_dataset.csv: All audio captions combined")
        print("- eval_prompts.csv: Prompts matched with most similar captions")
    else:
        print("\n✗ Process failed!")

if __name__ == "__main__":
    main() 