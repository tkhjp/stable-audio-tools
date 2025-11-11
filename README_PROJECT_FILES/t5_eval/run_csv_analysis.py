#!/usr/bin/env python3
"""
Simple script to run CSV similarity analysis
"""

from analyze_csv_similarity import CSVSimilarityAnalyzer
import argparse
import os

def main():
    """
    Main function with command line argument support
    """
    parser = argparse.ArgumentParser(description='Analyze similarity of prompts in CSV against reference JSONL')
    parser.add_argument('--input', '-i', default='before_ft.csv', 
                       help='Input CSV file (default: before_ft.csv)')
    parser.add_argument('--output', '-o', default='before_ft_with_similarities.csv',
                       help='Output CSV file (default: before_ft_with_similarities.csv)')
    parser.add_argument('--reference', '-r', default='prompts_update.jsonl',
                       help='Reference JSONL file (default: prompts_update.jsonl)')
    
    args = parser.parse_args()
    
    # Check if input files exist
    if not os.path.exists(args.input):
        print(f"❌ Error: Input CSV file '{args.input}' not found")
        return
    
    if not os.path.exists(args.reference):
        print(f"❌ Error: Reference JSONL file '{args.reference}' not found")
        return
    
    print("🚀 Starting CSV Similarity Analysis")
    print(f"📁 Input CSV: {args.input}")
    print(f"📁 Output CSV: {args.output}")
    print(f"📁 Reference JSONL: {args.reference}")
    print("-" * 50)
    
    # Create analyzer
    analyzer = CSVSimilarityAnalyzer(args.reference)
    
    try:
        # Process the CSV
        df = analyzer.process_csv(args.input, args.output)
        
        # Print summary
        analyzer.print_summary(df)
        
        print(f"\n✅ Analysis complete! Results saved to: {args.output}")
        
        # Show sample of results
        print("\n📊 Sample of results:")
        print(df[['プロンプト', 'very_high_similarity', 'high_similarity', 'medium_similarity', 'low_similarity']].head(10))
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return

if __name__ == "__main__":
    main() 