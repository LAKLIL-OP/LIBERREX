# English-Tunisian Translation Scraper

Scrapes English-Tunisian translation pairs from `klemy.qodek.net/staging` for fine-tuning the transcriber.

## Features

- ✅ Reads English sentences from `eng_sentences.tsv`
- ✅ Scrapes Tunisian translations from Klemy API
- ✅ Saves progress to CSV with automatic resume capability
- ✅ Rate limiting to avoid overwhelming the server
- ✅ Retry logic for failed requests
- ✅ Progress tracking with tqdm
- ✅ Checkpoint system for interruption recovery

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python scraper.py
```

### Resume After Interruption

If the scraper is interrupted (Ctrl+C or error), simply run it again:

```bash
python scraper.py
```

It will automatically skip already processed sentences and continue from where it left off.

## Output Files

- **`en_tn_couples.csv`**: Main output file with successful translations
  - `id`: Sentence ID from the TSV
  - `english`: Original English text
  - `tunisian`: Translated Tunisian Arabic text

- **`failed_translations.csv`**: Failed translations for later retry
  - `id`: Sentence ID
  - `english`: Original English text
  - `status`: Failure reason ('no_translation' or 'error')

- **`scraper_debug.log`**: Debug log with timestamps and error details

- **`.scraper_checkpoint.txt`**: Hidden checkpoint file (auto-managed)

## Configuration

Edit these constants in `scraper.py` to adjust behavior:

```python
REQUEST_DELAY = 1.0      # Seconds between requests (rate limiting)
MAX_RETRIES = 3          # Number of retry attempts for failed requests
RETRY_DELAY = 5.0        # Seconds to wait before retrying
```

## Example Output

```csv
id,english,tunisian
1276,Let's try something.,خلينا نجربو حاجة
1277,I have to go to sleep.,لازمني نمشي نرقد
1280,Today is June 18th and it is Muiriel's birthday!,اليوم 18 جوان و عيد ميلاد ميريال!
```

## Retry Failed Translations

After the initial scrape, you can retry failed translations:

```bash
python retry_failed.py
```

This will:
- Read all failed translations from `failed_translations.csv`
- Attempt to translate them again
- Save successful ones to `en_tn_couples.csv`
- Log results to `retry_results.csv`

## Error Handling

- Failed translations are saved to `failed_translations.csv` for later retry
- Network errors trigger automatic retries (3 attempts)
- All progress is saved incrementally to CSV
- Checkpoint file tracks the last processed ID
- Debug log captures detailed error information

## Notes

- The scraper respects rate limits (1 second between requests by default)
- Large TSV files are handled efficiently with streaming
- CSV is written incrementally, so data is safe even if interrupted
