#!/usr/bin/env python3
"""
Simple test script to verify translation functionality
"""

from translate_and_analyze import translate_to_english

def test_translations():
    """Test translation with sample Japanese prompts"""
    print("🧪 Testing Translation Functionality")
    print("=" * 40)
    
    # Test prompts from your CSV
    test_prompts = [
        "電車が走る音",
        "海の波の音", 
        "バスケットのドリブルの音",
        "808のキック",
        "スネアドラムの音",
        "ピアノのドの音",
        "時計のチクタク音",
        "花火の音",
        "鳥の鳴き声",
        "指パッチン"
    ]
    
    print("Testing translations...")
    print("-" * 40)
    
    for jp_prompt in test_prompts:
        try:
            en_translation = translate_to_english(jp_prompt)
            print(f"JP: {jp_prompt}")
            print(f"EN: {en_translation}")
            print()
        except Exception as e:
            print(f"Error translating '{jp_prompt}': {e}")
            print()
    
    print("✅ Translation test complete!")

if __name__ == "__main__":
    test_translations() 