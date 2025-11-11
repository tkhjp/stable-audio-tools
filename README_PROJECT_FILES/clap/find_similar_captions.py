import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os

def find_similar_captions(prompts_file, combined_file):
    """
    For each prompt in prompts_file, find the most similar caption in combined_file.
    """
    # Load the models
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Load the datasets
    try:
        prompts_df = pd.read_csv(prompts_file)
        print(f"✓ Loaded prompts: {len(prompts_df)} rows")
    except Exception as e:
        print(f"✗ Error loading prompts file: {e}")
        return

    try:
        combined_df = pd.read_csv(combined_file)
        print(f"✓ Loaded combined dataset: {len(combined_df)} rows")
    except Exception as e:
        print(f"✗ Error loading combined dataset file: {e}")
        return

    # Encode the prompts and captions
    print("\nEncoding prompts and captions...")
    prompt_embeddings = model.encode(prompts_df['Prompt_EN'].tolist(), convert_to_tensor=True)
    caption_embeddings = model.encode(combined_df['caption'].tolist(), convert_to_tensor=True)
    print("✓ Encoding complete.")

    # Find the most similar caption for each prompt
    print("\nFinding most similar captions...")
    results = []
    for i, prompt_embedding in enumerate(prompt_embeddings):
        similarities = util.pytorch_cos_sim(prompt_embedding, caption_embeddings)[0]
        most_similar_idx = similarities.argmax().item()
        
        results.append({
            'Prompt_ID': prompts_df.iloc[i]['ID'],
            'Prompt_EN': prompts_df.iloc[i]['Prompt_EN'],
            'Most_Similar_Caption': combined_df.iloc[most_similar_idx]['caption'],
            'Similarity_Score': similarities[most_similar_idx].item(),
            'audiocap_id': combined_df.iloc[most_similar_idx]['audiocap_id'],
            'youtube_id': combined_df.iloc[most_similar_idx]['youtube_id'],
            'start_time': combined_df.iloc[most_similar_idx]['start_time']
        })
    print("✓ Similarity search complete.")

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Save the results
    output_path = 'similar_captions.csv'
    results_df.to_csv(output_path, index=False)
    print(f"\n✓ Saved results to: {output_path}")

    # Display the results
    print(f"\nTop 10 most similar captions:")
    print(results_df.head(10))

if __name__ == "__main__":
    prompts_path = 'prompts.csv'
    combined_path = 'combined_dataset.csv'
    
    # First, run the script to combine the datasets
    # This assumes combine_datasets.py is in the same directory
    try:
        # Before running the similarity finder, we need to ensure the combined dataset exists.
        # Running the combine_datasets script first.
        import combine_datasets
        combine_datasets.combine_datasets()
    except ImportError:
        print("Could not import combine_datasets. Please make sure the file is in the same directory.")
    except Exception as e:
        print(f"An error occurred while combining datasets: {e}")

    # Now, find the similar captions
    find_similar_captions(prompts_path, combined_path) 