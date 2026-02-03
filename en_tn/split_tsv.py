"""
Split TSV file from a specific ID onwards
Creates a new file with sentences starting from the given ID
"""

from pathlib import Path


INPUT_TSV = Path(__file__).parent / "eng_sentences_second_half.tsv"
OUTPUT_TSV = Path(__file__).parent / "eng_sentences_second_half2.tsv"
START_ID = "10159624"  # Change this to your desired starting ID


def split_tsv_from_id(start_id: str):
    """Split TSV file starting from a specific ID"""
    
    print(f"📖 Reading from: {INPUT_TSV}")
    print(f"🎯 Starting from ID: {start_id}")
    
    found_start = False
    line_count = 0
    written_count = 0
    
    with open(INPUT_TSV, 'r', encoding='utf-8') as infile:
        with open(OUTPUT_TSV, 'w', encoding='utf-8') as outfile:
            for line in infile:
                line_count += 1
                
                # Check if this line starts with the target ID
                if not found_start:
                    if line.startswith(start_id + '\t'):
                        found_start = True
                        print(f"✅ Found starting ID at line {line_count}")
                
                # Write all lines after finding the start ID
                if found_start:
                    outfile.write(line)
                    written_count += 1
    
    if not found_start:
        print(f"❌ ID {start_id} not found in file!")
        OUTPUT_TSV.unlink()  # Delete the empty output file
        return
    
    print(f"\n📊 Summary:")
    print(f"📝 Total lines in original: {line_count}")
    print(f"✂️  Lines written to new file: {written_count}")
    print(f"💾 Output saved to: {OUTPUT_TSV}")


if __name__ == "__main__":
    split_tsv_from_id(START_ID)
