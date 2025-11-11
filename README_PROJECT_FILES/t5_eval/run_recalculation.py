#!/usr/bin/env python3
"""
Simple script to recalculate similarity using existing English translations
"""

from recalculate_similarity import RecalculateSimilarity
import argparse
import os

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Recalculate similarity counts using existing English translations')
    parser.add_argument('--csv', '-c', default='before_ft_with_english_similarity.csv',
                       help='CSV file with English translations (default: before_ft_with_english_similarity.csv)')
    parser.add_argument('--reference', '-r', default='prompts_update.jsonl',
                       help='Reference JSONL file (default: prompts_update.jsonl)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output CSV file (default: overwrite input file)')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.csv):
        print(f"❌ Error: CSV file '{args.csv}' not found")
        return
        
    if not os.path.exists(args.reference):
        print(f"❌ Error: Reference JSONL '{args.reference}' not found")
        return
    
    print("🔄 Starting Similarity Recalculation")
    print(f"📁 Input CSV: {args.csv}")
    print(f"📁 Reference JSONL: {args.reference}")
    print(f"📁 Output: {args.output or args.csv}")
    print("-" * 50)
    
    # Create recalculator
    recalc = RecalculateSimilarity(args.csv, args.reference)
    
    try:
        # Load CSV
        recalc.load_csv()
        
        # Initialize analyzer
        recalc.initialize_analyzer()
        
        # Recalculate similarities
        recalc.recalculate_similarities()
        
        # Save results
        recalc.save_results(args.output)
        
        # Print detailed analysis
        recalc.print_detailed_analysis()
        
        print(f"\n✅ Recalculation complete!")
        
    except Exception as e:
        print(f"❌ Error during recalculation: {e}")
        return

if __name__ == "__main__":
    main() 