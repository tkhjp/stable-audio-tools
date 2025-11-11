import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PromptSimilarity:
    """Data class to store similarity results"""
    id: int
    prompt: str
    similarity: float

class T5SimilarityFinder:
    """
    A class to find similar prompts using T5 embeddings
    """
    
    def __init__(self, model_name: str = "sentence-transformers/sentence-t5-base"):
        """
        Initialize the T5 similarity finder
        
        Args:
            model_name: Name of the T5 model to use for embeddings
        """
        print(f"Loading T5 model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.prompts_data = []
        self.embeddings = None
        self.embeddings_cache_file = "prompt_embeddings.pkl"
    
    def load_prompts(self, jsonl_file: str) -> None:
        """
        Load prompts from JSONL file
        
        Args:
            jsonl_file: Path to the JSONL file containing prompts
        """
        print(f"Loading prompts from: {jsonl_file}")
        self.prompts_data = []
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    self.prompts_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {line.strip()}")
                    continue
        
        print(f"Loaded {len(self.prompts_data)} prompts")
    
    def generate_embeddings(self, force_regenerate: bool = False) -> None:
        """
        Generate embeddings for all prompts
        
        Args:
            force_regenerate: Whether to force regeneration of embeddings
        """
        if not force_regenerate and os.path.exists(self.embeddings_cache_file):
            print("Loading cached embeddings...")
            with open(self.embeddings_cache_file, 'rb') as f:
                self.embeddings = pickle.load(f)
            print("Cached embeddings loaded successfully")
            return
        
        if not self.prompts_data:
            raise ValueError("No prompts loaded. Call load_prompts() first.")
        
        print("Generating embeddings for all prompts...")
        prompts_text = [item['prompt'] for item in self.prompts_data]
        
        # Generate embeddings in batches for efficiency
        self.embeddings = self.model.encode(prompts_text, show_progress_bar=True)
        
        # Cache embeddings for future use
        print("Caching embeddings...")
        with open(self.embeddings_cache_file, 'wb') as f:
            pickle.dump(self.embeddings, f)
        print("Embeddings generated and cached successfully")
    
    def find_similar_prompts(self, 
                           input_text: str, 
                           similarity_threshold: float = 0.7, 
                           top_k: Optional[int] = None) -> List[PromptSimilarity]:
        """
        Find similar prompts to the input text
        
        Args:
            input_text: The text to find similar prompts for
            similarity_threshold: Minimum similarity score (0-1)
            top_k: Maximum number of results to return (None for all above threshold)
            
        Returns:
            List of PromptSimilarity objects sorted by similarity (descending)
        """
        if self.embeddings is None:
            raise ValueError("Embeddings not generated. Call generate_embeddings() first.")
        
        # Generate embedding for input text
        input_embedding = self.model.encode([input_text])
        
        # Calculate similarities
        similarities = cosine_similarity(input_embedding, self.embeddings)[0]
        
        # Create results
        results = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                results.append(PromptSimilarity(
                    id=self.prompts_data[i]['id'],
                    prompt=self.prompts_data[i]['prompt'],
                    similarity=float(similarity)
                ))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Apply top_k limit if specified
        if top_k is not None:
            results = results[:top_k]
        
        return results
    
    def count_similar_prompts(self, 
                            input_text: str, 
                            similarity_threshold: float = 0.7) -> int:
        """
        Count the number of similar prompts above the threshold
        
        Args:
            input_text: The text to find similar prompts for
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Number of similar prompts found
        """
        similar_prompts = self.find_similar_prompts(input_text, similarity_threshold)
        return len(similar_prompts)
    
    def get_similarity_distribution(self, input_text: str) -> Dict[str, int]:
        """
        Get distribution of similarities across different thresholds
        
        Args:
            input_text: The text to analyze
            
        Returns:
            Dictionary with threshold ranges and counts
        """
        if self.embeddings is None:
            raise ValueError("Embeddings not generated. Call generate_embeddings() first.")
        
        # Generate embedding for input text
        input_embedding = self.model.encode([input_text])
        similarities = cosine_similarity(input_embedding, self.embeddings)[0]
        
        # Define threshold ranges
        thresholds = {
            'very_high (>0.9)': 0.9,
            'high (0.8-0.9)': 0.8,
            'medium (0.7-0.8)': 0.7,
            'low (0.6-0.7)': 0.6,
            'very_low (0.5-0.6)': 0.5
        }
        
        distribution = {}
        prev_threshold = 1.0
        
        for label, threshold in thresholds.items():
            count = np.sum((similarities >= threshold) & (similarities < prev_threshold))
            distribution[label] = int(count)
            prev_threshold = threshold
        
        return distribution

def main():
    """
    Example usage of the T5SimilarityFinder
    """
    # Initialize the finder
    finder = T5SimilarityFinder()
    
    # Load prompts from JSONL file
    finder.load_prompts("prompts_update.jsonl")
    
    # Generate embeddings
    finder.generate_embeddings()
    
    # Example searches
    test_queries = [
        "snare drum hits",
        "electronic claps",
        "rimshot sounds",
        "percussion instruments",
        "CVLTIV8R production"
    ]
    
    print("\n" + "="*50)
    print("SIMILARITY SEARCH RESULTS")
    print("="*50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        # Count similar prompts
        count = finder.count_similar_prompts(query, similarity_threshold=0.7)
        print(f"Number of similar prompts (threshold 0.7): {count}")
        
        # Get detailed results
        similar_prompts = finder.find_similar_prompts(query, similarity_threshold=0.6, top_k=3)
        
        print("\nTop similar prompts:")
        for i, result in enumerate(similar_prompts, 1):
            print(f"{i}. ID: {result.id}, Similarity: {result.similarity:.3f}")
            print(f"   Prompt: {result.prompt[:80]}...")
        
        # Get distribution
        distribution = finder.get_similarity_distribution(query)
        print(f"\nSimilarity distribution: {distribution}")
        print()

if __name__ == "__main__":
    main() 