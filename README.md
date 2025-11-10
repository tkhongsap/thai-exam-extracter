# Thai Exam Data Extractor

## Description
A powerful and efficient Python tool for extracting examination data from the TruePlookpanya API. This enhanced version features concurrent downloads, multiple export formats, comprehensive error handling, and advanced features like resume capability and duplicate detection.

## Features

### Core Functionality
- **Concurrent Downloads**: Uses asyncio for parallel extraction of multiple exams
- **Multiple Export Formats**: Support for JSON, CSV, and SQLite database
- **Resume Capability**: Automatically skips already downloaded exams
- **Retry Logic**: Exponential backoff for failed requests
- **Progress Tracking**: Real-time progress bar with tqdm
- **Data Validation**: Ensures data integrity before saving

### Advanced Features
- **Duplicate Detection**: Content-based hashing to identify duplicate exams
- **Dry-Run Mode**: Preview what would be downloaded without actual downloads
- **Statistics Reporting**: Comprehensive summary with success rates and timing
- **Configurable Rate Limiting**: Prevents overwhelming the server
- **Command-Line Interface**: Flexible CLI with multiple options
- **YAML Configuration**: Easy configuration management

### Code Quality
- **Object-Oriented Design**: Clean, maintainable class-based architecture
- **Type Hints**: Full type annotations for better IDE support
- **Comprehensive Logging**: Debug, info, warning, and error levels
- **Error Handling**: Graceful handling of network errors and malformed data

## Requirements
- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone or download this repository

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.yaml` to customize the extraction:

```yaml
api:
  timeout: 30
  max_retries: 3
  retry_delay: 2

download:
  concurrent_limit: 5      # Max parallel downloads
  rate_limit_delay: 0.5    # Delay between requests
  resume: true             # Skip existing files

output:
  directory: "data/output"
  formats:
    - json
    # - csv
    # - sqlite

extraction:
  start_id: 14000
  end_id: 20000

logging:
  level: INFO
  file: "exam_extraction.log"
  console: true
```

## Usage

### Basic Usage

Extract exams using default configuration:
```bash
python exam_extractor.py
```

### Command-Line Options

Extract specific range:
```bash
python exam_extractor.py --start 14000 --end 15000
```

Dry-run mode (preview without downloading):
```bash
python exam_extractor.py --dry-run --start 14000 --end 14010
```

Use custom config file:
```bash
python exam_extractor.py --config my_config.yaml
```

Disable resume (re-download all):
```bash
python exam_extractor.py --no-resume
```

Set log level:
```bash
python exam_extractor.py --log-level DEBUG
```

### Full CLI Reference

```bash
python exam_extractor.py --help
```

Options:
- `--start ID`: Starting exam ID (overrides config)
- `--end ID`: Ending exam ID (overrides config)
- `--config FILE`: Path to config file (default: config.yaml)
- `--dry-run`: Preview without downloading
- `--no-resume`: Re-download existing files
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Output Formats

### JSON Format
Each exam is saved as a separate JSON file:

**Filename Pattern:**
```
data/output/{exam_id}_{exam_name}_{level_name}_{subject_name}.json
```

Example: `14000_แบบทดสอบวิทยาศาสตร์_ป.6_วิทยาศาสตร์และเทคโนโลยี.json`

**Structure:**
```json
{
    "metadata": {
        "exam_id": "14000",
        "exam_name": "Example Exam",
        "level_name": "Grade Level",
        "subject_name": "Subject Name",
        "question_count": 10
    },
    "questions": [
        {
            "question_number": 1,
            "question_id": "q123",
            "question_text": "What is the question?",
            "choices": [
                {
                    "choice_number": 1,
                    "choice_text": "Option A",
                    "is_correct": false
                },
                {
                    "choice_number": 2,
                    "choice_text": "Option B",
                    "is_correct": true
                }
            ]
        }
    ]
}
```

### CSV Format
When CSV export is enabled, each exam is saved as a flattened CSV file with columns:
- Question Number
- Question Text
- Choice Number
- Choice Text
- Is Correct

### SQLite Database
When SQLite export is enabled, all exams are stored in a single database (`data/output/exams.db`) with three tables:
- `exams`: Metadata for each exam
- `questions`: Questions linked to exams
- `choices`: Answer choices linked to questions

## Statistics & Reporting

After extraction completes, you'll see a comprehensive summary:

```
============================================================
EXTRACTION SUMMARY
============================================================
Total Processed:  1000
Successful:       956 (95.6%)
Failed:           32
Skipped:          12
Duplicates:       5
Elapsed Time:     245.32 seconds
Avg Time/Exam:    0.25 seconds

Error Breakdown:
  API fetch failed: 20
  Validation failed: 8
  Export failed: 4
============================================================
```

A detailed JSON report is also saved to `data/output/extraction_report.json`.

## Architecture

The enhanced script uses a modular, object-oriented design:

- **Config**: YAML-based configuration management
- **ExamAPIClient**: Handles API requests with retry logic
- **ExportHandler**: Manages multiple export formats
- **DataValidator**: Validates exam data integrity
- **DuplicateDetector**: Content-based duplicate detection
- **Statistics**: Tracks and reports extraction metrics
- **ExamExtractor**: Main orchestrator with async coordination

## Performance

The enhanced version offers significant performance improvements:
- **5-10x faster** than the original script due to concurrent downloads
- Configurable concurrency limit to balance speed and server load
- Resume capability eliminates redundant downloads
- Progress tracking provides real-time feedback

## Troubleshooting

### Common Issues

**ImportError: No module named 'aiohttp'**
```bash
pip install -r requirements.txt
```

**Connection timeout errors**
- Increase `api.timeout` in config.yaml
- Reduce `download.concurrent_limit` to lower server load

**Files not being downloaded**
- Check if resume is enabled and files already exist
- Use `--no-resume` to force re-download
- Enable DEBUG logging to see detailed information

**Memory issues with large ranges**
- Reduce `download.concurrent_limit` in config.yaml
- Process in smaller batches

## Migration from Original Script

The new `exam_extractor.py` is designed to be a drop-in replacement:

1. Install new dependencies: `pip install -r requirements.txt`
2. Review and adjust `config.yaml` for your needs
3. Run `python exam_extractor.py` instead of `python exam-extraction.py`

The original `exam-extraction.py` remains available for backward compatibility.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Legacy Script

The original synchronous script is still available as `exam-extraction.py` for backward compatibility.

## License
This project is open-source and available under the MIT License.
