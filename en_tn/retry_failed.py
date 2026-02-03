"""
Retry Failed Translations
Attempts to re-scrape sentences that previously failed
"""

import csv
import time
from pathlib import Path

from scraper import translate_with_retry, REQUEST_DELAY


FAILED_CSV = Path(__file__).parent / "failed_translations.csv"
OUTPUT_CSV = Path(__file__).parent / "en_tn_couples.csv"
RETRY_OUTPUT = Path(__file__).parent / "retry_results.csv"


def main():
    """Retry failed translations"""
    if not FAILED_CSV.exists():
        print("❌ No failed_translations.csv found")
        return
    
    # Read failed translations
    failed = []
    with open(FAILED_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            failed.append((row['id'], row['english']))
    
    print(f"🔄 Found {len(failed)} failed translations to retry")
    
    if not failed:
        print("✨ No failed translations to retry!")
        return
    
    # Open output files
    success_file = open(OUTPUT_CSV, 'a', encoding='utf-8', newline='')
    success_writer = csv.DictWriter(success_file, fieldnames=['id', 'english', 'tunisian'])
    
    retry_file = open(RETRY_OUTPUT, 'w', encoding='utf-8', newline='')
    retry_writer = csv.DictWriter(retry_file, fieldnames=['id', 'english', 'tunisian', 'status'])
    retry_writer.writeheader()
    
    success_count = 0
    still_failed = 0
    
    try:
        for sentence_id, english_text in failed:
            print(f"Retrying ID {sentence_id}...", end=' ')
            
            tunisian_text, status = translate_with_retry(english_text, sentence_id)
            
            if status == 'success':
                # Save to main CSV
                success_writer.writerow({
                    'id': sentence_id,
                    'english': english_text,
                    'tunisian': tunisian_text
                })
                success_file.flush()
                success_count += 1
                print("✅")
            else:
                # Log in retry results
                retry_writer.writerow({
                    'id': sentence_id,
                    'english': english_text,
                    'tunisian': tunisian_text or '',
                    'status': status
                })
                retry_file.flush()
                still_failed += 1
                print(f"❌ ({status})")
            
            time.sleep(REQUEST_DELAY)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        success_file.close()
        retry_file.close()
        
        print(f"\n📊 Retry Summary:")
        print(f"✅ Now successful: {success_count}")
        print(f"❌ Still failed: {still_failed}")
        print(f"💾 Results saved to: {RETRY_OUTPUT}")


if __name__ == "__main__":
    main()
