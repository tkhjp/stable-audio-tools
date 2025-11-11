#!/usr/bin/env python3
"""
Simple usage example for T5 Similarity Finder
"""

from t5_similarity_finder import T5SimilarityFinder

def simple_example():
    """
    Simple example of how to use the T5 similarity finder
    """
    print("T5 Similarity Finder - Simple Example")
    print("=" * 40)
    
    # Step 1: Initialize the finder
    finder = T5SimilarityFinder()
    
    # Step 2: Load your prompts
    finder.load_prompts("prompts_update.jsonl")
    
    # Step 3: Generate embeddings (this will be cached for future use)
    finder.generate_embeddings()
    
    # Step 4: Test with different inputs
    test_inputs = [
        "snare drum sound",
        "electronic clap sound",
        "rimshot percussion",
        "audio sample by producer"
    ]
    
    for input_text in test_inputs:
        print(f"\nInput: '{input_text}'")
        print("-" * 30)
        
        # Count similar prompts with default threshold (0.7)
        count = finder.count_similar_prompts(input_text)
        print(f"Similar prompts found: {count}")
        
        # Get the most similar prompts
        similar_prompts = finder.find_similar_prompts(
            input_text, 
            similarity_threshold=0.6, 
            top_k=2
        )
        
        print("Most similar prompts:")
        for i, result in enumerate(similar_prompts, 1):
            print(f"  {i}. Similarity: {result.similarity:.3f}")
            print(f"     ID: {result.id}")
            print(f"     Prompt: {result.prompt}")
            print()

def interactive_example():
    """
    Interactive example where user can input their own text
    """
    print("\nInteractive Mode")
    print("=" * 20)
    
    # Initialize finder
    finder = T5SimilarityFinder()
    finder.load_prompts("prompts_update.jsonl")
    finder.generate_embeddings()
    
    while True:
        user_input = input("\nEnter text to find similar prompts (or 'quit' to exit): ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
        
        # Find similar prompts
        similar_prompts = finder.find_similar_prompts(
            user_input, 
            similarity_threshold=0.5,  # Lower threshold for more results
            top_k=3
        )
        
        print(f"\nFound {len(similar_prompts)} similar prompts:")
        for i, result in enumerate(similar_prompts, 1):
            print(f"{i}. Similarity: {result.similarity:.3f}")
            print(f"   ID: {result.id}")
            print(f"   Prompt: {result.prompt}")
            print()

if __name__ == "__main__":
    # Run simple example
    simple_example()
    
    # Optionally run interactive example
    print("\n" + "="*50)
    choice = input("Do you want to try the interactive mode? (y/n): ").strip().lower()
    if choice == 'y':
        interactive_example()
    
    print("\nDone!") 