# T5 Similarity Finder

A Python tool that uses T5 embeddings to find similar prompts in your dataset. This tool is particularly useful for finding semantically similar text content, even when the exact words differ.

## Features

- **T5 Embeddings**: Uses state-of-the-art T5 model for generating semantic embeddings
- **Similarity Search**: Find prompts similar to your input text
- **Flexible Thresholds**: Adjustable similarity thresholds (0.0 to 1.0)
- **Caching**: Embeddings are cached for faster subsequent searches
- **Multiple Search Options**: Count similar prompts, get top-k results, or analyze similarity distributions
- **CSV Analysis**: Bulk analysis of CSV files with prompt similarity counts

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from t5_similarity_finder import T5SimilarityFinder

# Initialize the finder
finder = T5SimilarityFinder()

# Load your prompts from JSONL file
finder.load_prompts("prompts_update.jsonl")

# Generate embeddings (cached for future use)
finder.generate_embeddings()

# Count similar prompts
count = finder.count_similar_prompts("snare drum sound", similarity_threshold=0.7)
print(f"Found {count} similar prompts")

# Get detailed results
similar_prompts = finder.find_similar_prompts("snare drum sound", similarity_threshold=0.6, top_k=3)
for result in similar_prompts:
    print(f"ID: {result.id}, Similarity: {result.similarity:.3f}")
    print(f"Prompt: {result.prompt}")
```

### Run Examples

```bash
# Simple example with predefined test cases
python simple_usage_example.py

# Full example with comprehensive analysis
python t5_similarity_finder.py
```

## CSV Analysis Feature

### Analyze Similarity for CSV Files

You can now analyze similarity counts for prompts in CSV files:

```bash
# Basic usage - analyze before_ft.csv
python analyze_csv_similarity.py

# With custom parameters
python run_csv_analysis.py --input your_file.csv --output results.csv --reference prompts_update.jsonl
```

This will add the following columns to your CSV:
- `very_high_similarity`: Count of prompts with >0.9 similarity
- `high_similarity`: Count of prompts with 0.8-0.9 similarity  
- `medium_similarity`: Count of prompts with 0.7-0.8 similarity
- `low_similarity`: Count of prompts with 0.6-0.7 similarity

### CSV Format Requirements

Your CSV should have a column named `プロンプト` containing the text prompts to analyze.

## Key Methods

### `count_similar_prompts(input_text, similarity_threshold=0.7)`
Returns the number of prompts that are similar to the input text above the threshold.

### `find_similar_prompts(input_text, similarity_threshold=0.7, top_k=None)`
Returns a list of similar prompts with their IDs and similarity scores.

### `get_similarity_distribution(input_text)`
Returns a distribution of similarities across different threshold ranges.

## Configuration

### Similarity Thresholds
- **0.9+**: Very high similarity (near-identical meaning)
- **0.8-0.9**: High similarity (very similar concepts)
- **0.7-0.8**: Medium similarity (related concepts)
- **0.6-0.7**: Low similarity (somewhat related)
- **0.5-0.6**: Very low similarity (loosely related)

### Model Options
You can use different T5 models by specifying them during initialization:

```python
# Default model
finder = T5SimilarityFinder()

# Alternative models
finder = T5SimilarityFinder("sentence-transformers/sentence-t5-large")
finder = T5SimilarityFinder("sentence-transformers/sentence-t5-xl")
```

## Data Format

Your JSONL file should contain entries like:
```json
{"id": 123, "prompt": "Your text content here"}
{"id": 124, "prompt": "Another text entry"}
```

## Performance Tips

1. **Caching**: Embeddings are automatically cached. The first run will be slower as embeddings are generated.
2. **Batch Processing**: The tool processes all prompts at once for efficiency.
3. **Model Selection**: Larger models (t5-large, t5-xl) are more accurate but slower.

## Files Created

- `prompt_embeddings.pkl`: Cached embeddings file (automatically created)
- `t5_similarity_finder.py`: Main implementation
- `simple_usage_example.py`: Example usage script
- `analyze_csv_similarity.py`: CSV analysis script
- `run_csv_analysis.py`: Command-line CSV analysis tool
- `requirements.txt`: Dependencies

## Troubleshooting

1. **Memory Issues**: If you have a large dataset, consider using a smaller T5 model or processing in chunks.
2. **Slow First Run**: The first run downloads the model and generates embeddings. Subsequent runs are much faster.
3. **No Results**: Try lowering the similarity threshold if you're not getting results.

## Example Output

### Basic Usage Output

```
Query: 'snare drum sound'
Number of similar prompts (threshold 0.7): 3

Top similar prompts:
1. ID: 793814, Similarity: 0.842
   Prompt: snare hits cracks claps rimshots all original produced by CVLTIV8R...

2. ID: 793836, Similarity: 0.798
   Prompt: Sound effects electronic / design, snare hi claps rim rimshot...
```

### CSV Analysis Output

```
SIMILARITY ANALYSIS SUMMARY
============================================================
Total prompts analyzed: 79

Very High Similarity:
  Total matches: 5
  Average per prompt: 0.06
  Maximum matches: 2

High Similarity:
  Total matches: 45
  Average per prompt: 0.57
  Maximum matches: 3

Top 5 prompts with most high similarities:
  'スネアドラムの音' - 3 matches
  '808のキック' - 2 matches
  'グラスを叩く音' - 2 matches