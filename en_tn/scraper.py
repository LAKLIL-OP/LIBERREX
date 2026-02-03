"""
English-Tunisian Translation Scraper
Scrapes translations from klemy.qodek.net/staging for sentences in eng_sentences.tsv
Saves progress to CSV with resume capability
"""

import csv
import re
import time
from pathlib import Path
from typing import Optional, Set

import requests
from tqdm import tqdm


# Configuration
URL = "https://klemy.qodek.net/staging"
INPUT_TSV = Path(__file__).parent / "eng_sentences.tsv"
OUTPUT_CSV = Path(__file__).parent / "en_tn_couples.csv"
CHECKPOINT_FILE = Path(__file__).parent / ".scraper_checkpoint.txt"
FAILED_CSV = Path(__file__).parent / "failed_translations.csv"
DEBUG_LOG = Path(__file__).parent / "scraper_debug.log"

# Rate limiting
REQUEST_DELAY = 5.0  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds


def call_klemy(text: str) -> str:
    """Call the Klemy translation API"""
    headers = {"accept": "*/*"}
    payload = {
        "target_lang": "Tunisian Dialect",
        "output_alphabet": "Arabic",
        "text": text,
    }
    
    response = requests.post(URL, headers=headers, data=payload, timeout=30)
    response.raise_for_status()
    return response.text


def extract_fs3_paragraph(html: str) -> Optional[str]:
    """
    Extract text inside <p class="fs-3">...</p> from the HTML response.
    Returns cleaned text or None if not found.
    """
    match = re.search(r'<p[^>]*class="fs-3"[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    inner_html = match.group(1)
    # Remove any nested tags
    inner_text = re.sub(r"<.*?>", "", inner_html)
    # Normalize whitespace
    cleaned = " ".join(inner_text.split())
    return cleaned.strip() or None


def log_debug(message: str):
    """Log debug messages to file"""
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


def translate_with_retry(text: str, sentence_id: str) -> tuple[Optional[str], str]:
    """
    Translate text with retry logic
    Returns: (translation, status) where status is 'success', 'no_translation', or 'error'
    """
    for attempt in range(MAX_RETRIES):
        try:
            html = call_klemy(text)
            translation = extract_fs3_paragraph(html)
            
            if translation:
                return translation, 'success'
            else:
                # Log the HTML response for debugging
                log_debug(f"ID {sentence_id}: No fs-3 paragraph found. HTML length: {len(html)}")
                if attempt == MAX_RETRIES - 1:
                    print(f"\n⚠️  No translation found for ID {sentence_id}: {text[:50]}...")
                return None, 'no_translation'
                
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"\n⚠️  Error for ID {sentence_id} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"\n❌ Failed after {MAX_RETRIES} attempts for ID {sentence_id}: {e}")
                log_debug(f"ID {sentence_id}: Request failed - {e}")
                return None, 'error'
    
    return None, 'error'


def load_processed_ids() -> Set[str]:
    """Load IDs that have already been processed"""
    processed = set()
    
    if OUTPUT_CSV.exists():
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'id' in row and row['id']:
                        processed.add(row['id'])
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing CSV ({e}). Starting fresh.")
            # Backup the corrupted file
            if OUTPUT_CSV.exists():
                backup_path = OUTPUT_CSV.with_suffix('.csv.backup')
                OUTPUT_CSV.rename(backup_path)
                print(f"📦 Backed up existing file to: {backup_path}")
    
    return processed


def save_checkpoint(sentence_id: str):
    """Save the last processed ID"""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        f.write(sentence_id)


def load_checkpoint() -> Optional[str]:
    """Load the last processed ID"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def read_sentences():
    """Read sentences from TSV file"""
    sentences = []
    with open(INPUT_TSV, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                sentence_id, lang, text = parts[0], parts[1], parts[2]
                if lang == 'eng':
                    sentences.append((sentence_id, text))
    return sentences


def main():
    """Main scraping function"""
    print("🚀 Starting English-Tunisian Translation Scraper")
    print(f"📁 Input: {INPUT_TSV}")
    print(f"💾 Output: {OUTPUT_CSV}")
    print()
    
    # Load sentences
    print("📖 Reading sentences...")
    sentences = read_sentences()
    print(f"✅ Found {len(sentences)} English sentences")
    
    # Check for existing progress
    processed_ids = load_processed_ids()
    if processed_ids:
        print(f"♻️  Found {len(processed_ids)} already processed sentences")
        sentences = [(sid, text) for sid, text in sentences if sid not in processed_ids]
        print(f"📝 Remaining: {len(sentences)} sentences")
    
    if not sentences:
        print("✨ All sentences already processed!")
        return
    
    # Initialize CSV files
    file_exists = OUTPUT_CSV.exists()
    csv_file = open(OUTPUT_CSV, 'a', encoding='utf-8', newline='')
    writer = csv.DictWriter(csv_file, fieldnames=['id', 'english', 'tunisian'])
    
    if not file_exists:
        writer.writeheader()
    
    # Initialize failed translations CSV
    failed_exists = FAILED_CSV.exists()
    failed_file = open(FAILED_CSV, 'a', encoding='utf-8', newline='')
    failed_writer = csv.DictWriter(failed_file, fieldnames=['id', 'english', 'status'])
    
    if not failed_exists:
        failed_writer.writeheader()
    
    # Process sentences
    print(f"\n🔄 Starting scraping...")
    print(f"⏱️  Rate limit: {REQUEST_DELAY}s between requests")
    print()
    
    success_count = 0
    fail_count = 0
    
    try:
        for sentence_id, english_text in tqdm(sentences, desc="Scraping"):
            # Translate
            tunisian_text, status = translate_with_retry(english_text, sentence_id)
            
            if status == 'success':
                # Save to CSV
                writer.writerow({
                    'id': sentence_id,
                    'english': english_text,
                    'tunisian': tunisian_text
                })
                csv_file.flush()  # Ensure data is written
                success_count += 1
            else:
                # Save failed translation
                failed_writer.writerow({
                    'id': sentence_id,
                    'english': english_text,
                    'status': status
                })
                failed_file.flush()
                fail_count += 1
            
            # Save checkpoint
            save_checkpoint(sentence_id)
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        csv_file.close()
        failed_file.close()
        print(f"\n\n📊 Summary:")
        print(f"✅ Successfully scraped: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"💾 Saved to: {OUTPUT_CSV}")
        print(f"📝 Failed sentences: {FAILED_CSV}")
        print(f"🔍 Debug log: {DEBUG_LOG}")
        
        if CHECKPOINT_FILE.exists():
            last_id = load_checkpoint()
            print(f"📍 Last processed ID: {last_id}")
            print(f"♻️  Run again to resume from this point")


if __name__ == "__main__":
    main()
