#!/usr/bin/env python3
"""
Enhanced Thai Exam Data Extractor

This script extracts exam data from an API endpoint with advanced features:
- Concurrent downloads with asyncio
- Retry logic with exponential backoff
- Resume capability to skip already downloaded exams
- Progress tracking with tqdm
- Multiple export formats (JSON, CSV, SQLite)
- Comprehensive error handling and validation
- Statistics and summary reporting
- Duplicate detection
- Dry-run mode
"""

import asyncio
import aiohttp
import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
import yaml
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm


# Custom Exceptions
class ExamExtractorError(Exception):
    """Base exception for exam extractor errors."""
    pass


class APIError(ExamExtractorError):
    """Exception raised for API-related errors."""
    pass


class ValidationError(ExamExtractorError):
    """Exception raised for data validation errors."""
    pass


class ExportError(ExamExtractorError):
    """Exception raised for export/save errors."""
    pass


class ConfigurationError(ExamExtractorError):
    """Exception raised for configuration errors."""
    pass


class Config:
    """Configuration manager for the exam extractor."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        self.config_file = config_file
        self.config = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {self.config_file} not found. Using defaults.")
            return self._default_config()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # API configuration
        if api_url := os.getenv('EXAM_API_BASE_URL'):
            self.config['api']['base_url'] = api_url
        if api_timeout := os.getenv('EXAM_API_TIMEOUT'):
            self.config['api']['timeout'] = int(api_timeout)
        if api_retries := os.getenv('EXAM_API_MAX_RETRIES'):
            self.config['api']['max_retries'] = int(api_retries)

        # Download configuration
        if concurrent_limit := os.getenv('EXAM_CONCURRENT_LIMIT'):
            self.config['download']['concurrent_limit'] = int(concurrent_limit)
        if rate_limit := os.getenv('EXAM_RATE_LIMIT_DELAY'):
            self.config['download']['rate_limit_delay'] = float(rate_limit)

        # Output configuration
        if output_dir := os.getenv('EXAM_OUTPUT_DIR'):
            self.config['output']['directory'] = output_dir

        # Extraction range
        if start_id := os.getenv('EXAM_START_ID'):
            self.config['extraction']['start_id'] = int(start_id)
        if end_id := os.getenv('EXAM_END_ID'):
            self.config['extraction']['end_id'] = int(end_id)

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'api': {
                'base_url': 'https://www.trueplookpanya.com/webservice/api/examination/formdoexamination',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 2
            },
            'download': {
                'concurrent_limit': 5,
                'rate_limit_delay': 0.5,
                'resume': True
            },
            'output': {
                'directory': 'data/output',
                'formats': ['json']
            },
            'extraction': {
                'start_id': 14000,
                'end_id': 20000
            },
            'logging': {
                'level': 'INFO',
                'file': 'exam_extraction.log',
                'console': True
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'api.timeout')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


class Statistics:
    """Track and report statistics for the extraction process."""

    def __init__(self):
        """Initialize statistics tracker."""
        self.success_count = 0
        self.failure_count = 0
        self.skipped_count = 0
        self.duplicate_count = 0
        self.start_time = time.time()
        self.errors = defaultdict(int)
        self.exam_metadata = []

    def record_success(self, exam_data: Dict[str, Any]):
        """Record a successful extraction."""
        self.success_count += 1
        self.exam_metadata.append(exam_data.get('metadata', {}))

    def record_failure(self, error_type: str):
        """Record a failed extraction."""
        self.failure_count += 1
        self.errors[error_type] += 1

    def record_skip(self):
        """Record a skipped exam."""
        self.skipped_count += 1

    def record_duplicate(self):
        """Record a duplicate exam."""
        self.duplicate_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        elapsed_time = time.time() - self.start_time
        total_processed = self.success_count + self.failure_count + self.skipped_count

        return {
            'total_processed': total_processed,
            'successful': self.success_count,
            'failed': self.failure_count,
            'skipped': self.skipped_count,
            'duplicates': self.duplicate_count,
            'elapsed_time': elapsed_time,
            'avg_time_per_exam': elapsed_time / total_processed if total_processed > 0 else 0,
            'success_rate': (self.success_count / total_processed * 100) if total_processed > 0 else 0,
            'errors': dict(self.errors)
        }

    def print_summary(self):
        """Print summary statistics."""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total Processed:  {summary['total_processed']}")
        print(f"Successful:       {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed:           {summary['failed']}")
        print(f"Skipped:          {summary['skipped']}")
        print(f"Duplicates:       {summary['duplicates']}")
        print(f"Elapsed Time:     {summary['elapsed_time']:.2f} seconds")
        print(f"Avg Time/Exam:    {summary['avg_time_per_exam']:.2f} seconds")

        if summary['errors']:
            print("\nError Breakdown:")
            for error_type, count in summary['errors'].items():
                print(f"  {error_type}: {count}")

        print("="*60)


class DataValidator:
    """Validate exam data structure and content."""

    @staticmethod
    def validate_exam_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate exam data structure.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check top-level structure
        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors

        # Check for required keys
        if 'metadata' not in data:
            errors.append("Missing 'metadata' key")
        if 'questions' not in data:
            errors.append("Missing 'questions' key")

        # Validate metadata
        if 'metadata' in data:
            metadata = data['metadata']
            required_metadata_keys = ['exam_id', 'exam_name', 'level_name', 'subject_name']
            for key in required_metadata_keys:
                if key not in metadata:
                    errors.append(f"Missing metadata key: {key}")

        # Validate questions
        if 'questions' in data:
            questions = data['questions']
            if not isinstance(questions, list):
                errors.append("Questions is not a list")
            elif len(questions) == 0:
                errors.append("Questions list is empty")
            else:
                # Validate first question as sample
                question = questions[0]
                required_question_keys = ['question_number', 'question_id', 'question_text', 'choices']
                for key in required_question_keys:
                    if key not in question:
                        errors.append(f"Missing question key: {key}")

                # Validate choices
                if 'choices' in question:
                    choices = question['choices']
                    if not isinstance(choices, list) or len(choices) == 0:
                        errors.append("Choices is empty or not a list")

        return len(errors) == 0, errors


class ExamAPIClient:
    """Async API client for fetching exam data."""

    def __init__(self, config: Config):
        """Initialize the API client."""
        self.config = config
        self.base_url = config.get('api.base_url')
        self.timeout = config.get('api.timeout', 30)
        self.max_retries = config.get('api.max_retries', 3)
        self.retry_delay = config.get('api.retry_delay', 2)

    async def fetch_exam_data(self, session: aiohttp.ClientSession, exam_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch exam data from API with retry logic.

        Args:
            session: aiohttp session
            exam_id: Exam ID to fetch

        Returns:
            Dict containing exam data or None if failed
        """
        url = f"{self.base_url}?exam_id={exam_id}"

        for attempt in range(self.max_retries):
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_api_response(data)
                    elif response.status == 404:
                        logging.debug(f"Exam {exam_id} not found (404)")
                        return None
                    else:
                        logging.warning(f"Exam {exam_id}: HTTP {response.status}")

            except asyncio.TimeoutError:
                logging.warning(f"Exam {exam_id}: Timeout (attempt {attempt + 1}/{self.max_retries})")
            except aiohttp.ClientError as e:
                logging.warning(f"Exam {exam_id}: Client error {str(e)} (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logging.error(f"Exam {exam_id}: Unexpected error {str(e)}")
                return None

            # Wait before retry with exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)

        logging.error(f"Exam {exam_id}: Failed after {self.max_retries} attempts")
        return None

    def _process_api_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and extract exam data.

        Args:
            data: Raw API response

        Returns:
            Processed exam data
        """
        try:
            # Extract metadata
            metadata = {
                "exam_id": int(data['data']['exam']['exam_id']),
                "exam_name": data['data']['exam']['exam_name'],
                "level_name": data['data']['exam']['level_name'],
                "subject_name": data['data']['exam']['subject_name'],
                "question_count": int(data['data']['exam']['question_count'])
            }

            # Extract questions and choices
            questions_list = []
            for i, question_data in enumerate(data['data']['formdo'], 1):
                question_detail = {
                    "question_number": i,
                    "question_id": int(question_data['question_id']),
                    "question_text": question_data['question_detail'],
                    "choices": []
                }

                for j, choice in enumerate(question_data['choice'], 1):
                    choice_detail = {
                        "choice_number": j,
                        "choice_text": choice['detail'],
                        "is_correct": choice['answer'] == "true"
                    }
                    question_detail["choices"].append(choice_detail)

                questions_list.append(question_detail)

            # Combine metadata and questions
            output_data = {
                "metadata": metadata,
                "questions": questions_list
            }

            return output_data

        except (KeyError, IndexError) as e:
            logging.error(f"Error processing API response: {str(e)}")
            return None


class ExportHandler:
    """Handle exporting exam data to multiple formats."""

    def __init__(self, config: Config):
        """Initialize export handler."""
        self.config = config
        self.output_dir = config.get('output.directory', 'data/output')
        self.formats = config.get('output.formats', ['json'])
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize SQLite if needed
        if 'sqlite' in self.formats:
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database."""
        db_path = os.path.join(self.output_dir, 'exams.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                exam_id INTEGER PRIMARY KEY,
                exam_name TEXT,
                level_name TEXT,
                subject_name TEXT,
                question_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                question_number INTEGER,
                question_id INTEGER,
                question_text TEXT,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                choice_number INTEGER,
                choice_text TEXT,
                is_correct BOOLEAN,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')

        conn.commit()
        conn.close()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Replace invalid characters in filenames with underscore.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename
        """
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    def export(self, exam_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Export exam data to configured formats.

        Args:
            exam_data: Exam data to export

        Returns:
            Dict mapping format to file path
        """
        results = {}

        if 'json' in self.formats:
            results['json'] = self._export_json(exam_data)

        if 'csv' in self.formats:
            results['csv'] = self._export_csv(exam_data)

        if 'sqlite' in self.formats:
            results['sqlite'] = self._export_sqlite(exam_data)

        return results

    def _export_json(self, exam_data: Dict[str, Any]) -> str:
        """Export to JSON format."""
        metadata = exam_data["metadata"]
        filename = f"{metadata['exam_id']}_{metadata['exam_name']}_{metadata['level_name']}_{metadata['subject_name']}.json"
        filename = self.sanitize_filename(filename)
        file_path = os.path.join(self.output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exam_data, f, ensure_ascii=False, indent=4)

        return file_path

    def _export_csv(self, exam_data: Dict[str, Any]) -> str:
        """Export to CSV format."""
        metadata = exam_data["metadata"]
        filename = f"{metadata['exam_id']}_{metadata['exam_name']}_{metadata['level_name']}_{metadata['subject_name']}.csv"
        filename = self.sanitize_filename(filename)
        file_path = os.path.join(self.output_dir, filename)

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # Write headers
            writer.writerow(['Question Number', 'Question Text', 'Choice Number', 'Choice Text', 'Is Correct'])

            # Write data
            for question in exam_data['questions']:
                for choice in question['choices']:
                    writer.writerow([
                        question['question_number'],
                        question['question_text'],
                        choice['choice_number'],
                        choice['choice_text'],
                        choice['is_correct']
                    ])

        return file_path

    def _export_sqlite(self, exam_data: Dict[str, Any]) -> str:
        """Export to SQLite database."""
        db_path = os.path.join(self.output_dir, 'exams.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        metadata = exam_data['metadata']

        # Insert exam metadata
        cursor.execute('''
            INSERT OR REPLACE INTO exams (exam_id, exam_name, level_name, subject_name, question_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (metadata['exam_id'], metadata['exam_name'], metadata['level_name'],
              metadata['subject_name'], metadata['question_count']))

        # Insert questions and choices
        for question in exam_data['questions']:
            cursor.execute('''
                INSERT INTO questions (exam_id, question_number, question_id, question_text)
                VALUES (?, ?, ?, ?)
            ''', (metadata['exam_id'], question['question_number'],
                  question['question_id'], question['question_text']))

            question_db_id = cursor.lastrowid

            for choice in question['choices']:
                cursor.execute('''
                    INSERT INTO choices (question_id, choice_number, choice_text, is_correct)
                    VALUES (?, ?, ?, ?)
                ''', (question_db_id, choice['choice_number'],
                      choice['choice_text'], choice['is_correct']))

        conn.commit()
        conn.close()

        return db_path

    def file_exists(self, exam_id: int) -> bool:
        """Check if exam file already exists."""
        pattern = f"{exam_id}_*.json"
        existing_files = list(Path(self.output_dir).glob(pattern))
        return len(existing_files) > 0


class DuplicateDetector:
    """Detect duplicate exams based on content hash."""

    def __init__(self):
        """Initialize duplicate detector."""
        self.seen_hashes: Set[str] = set()

    def compute_hash(self, exam_data: Dict[str, Any]) -> str:
        """
        Compute hash of exam content.

        Args:
            exam_data: Exam data to hash

        Returns:
            SHA256 hash of exam content
        """
        # Create normalized string representation for hashing
        content = json.dumps(exam_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_duplicate(self, exam_data: Dict[str, Any]) -> bool:
        """
        Check if exam is a duplicate.

        Args:
            exam_data: Exam data to check

        Returns:
            True if duplicate, False otherwise
        """
        content_hash = self.compute_hash(exam_data)

        if content_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(content_hash)
        return False


class ExamExtractor:
    """Main exam extractor orchestrator."""

    def __init__(self, config: Config, dry_run: bool = False):
        """Initialize the exam extractor."""
        self.config = config
        self.dry_run = dry_run
        self.api_client = ExamAPIClient(config)
        self.export_handler = ExportHandler(config)
        self.statistics = Statistics()
        self.duplicate_detector = DuplicateDetector()
        self.validator = DataValidator()
        self.semaphore = asyncio.Semaphore(config.get('download.concurrent_limit', 5))
        self.rate_limit_delay = config.get('download.rate_limit_delay', 0.5)
        self.resume = config.get('download.resume', True)

    async def extract_single_exam(self, session: aiohttp.ClientSession, exam_id: int) -> bool:
        """
        Extract a single exam.

        Args:
            session: aiohttp session
            exam_id: Exam ID to extract

        Returns:
            True if successful, False otherwise
        """
        async with self.semaphore:
            # Check if file already exists (resume functionality)
            if self.resume and self.export_handler.file_exists(exam_id):
                self.statistics.record_skip()
                logging.debug(f"Exam {exam_id}: Skipped (already exists)")
                return True

            # Fetch exam data
            exam_data = await self.api_client.fetch_exam_data(session, exam_id)

            if exam_data is None:
                self.statistics.record_failure("API fetch failed")
                return False

            # Validate data
            is_valid, errors = self.validator.validate_exam_data(exam_data)
            if not is_valid:
                logging.error(f"Exam {exam_id}: Validation failed - {', '.join(errors)}")
                self.statistics.record_failure("Validation failed")
                return False

            # Check for duplicates
            if self.duplicate_detector.is_duplicate(exam_data):
                logging.info(f"Exam {exam_id}: Duplicate detected")
                self.statistics.record_duplicate()
                # Still continue to save if not in dry-run mode

            # Export data
            if not self.dry_run:
                try:
                    self.export_handler.export(exam_data)
                    self.statistics.record_success(exam_data)
                    logging.debug(f"Exam {exam_id}: Successfully extracted")
                except Exception as e:
                    logging.error(f"Exam {exam_id}: Export failed - {str(e)}")
                    self.statistics.record_failure("Export failed")
                    return False
            else:
                self.statistics.record_success(exam_data)
                logging.info(f"Exam {exam_id}: Would be extracted (dry-run)")

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            return True

    async def extract_range(self, start_id: int, end_id: int):
        """
        Extract exams in a given range.

        Args:
            start_id: Starting exam ID
            end_id: Ending exam ID
        """
        exam_ids = range(start_id, end_id + 1)

        async with aiohttp.ClientSession() as session:
            # Create tasks with progress bar
            tasks = [self.extract_single_exam(session, exam_id) for exam_id in exam_ids]

            # Execute with progress bar
            for coro in tqdm_asyncio.as_completed(tasks, desc="Extracting exams", total=len(tasks)):
                await coro

    def run(self, start_id: Optional[int] = None, end_id: Optional[int] = None):
        """
        Run the extraction process.

        Args:
            start_id: Starting exam ID (overrides config)
            end_id: Ending exam ID (overrides config)
        """
        start_id = start_id or self.config.get('extraction.start_id', 14000)
        end_id = end_id or self.config.get('extraction.end_id', 20000)

        logging.info(f"Starting extraction for exam IDs {start_id} to {end_id}")
        if self.dry_run:
            logging.info("DRY-RUN MODE: No files will be written")

        # Run async extraction
        asyncio.run(self.extract_range(start_id, end_id))

        # Print statistics
        self.statistics.print_summary()

        # Save statistics report
        if not self.dry_run:
            self._save_statistics_report()

    def _save_statistics_report(self):
        """Save statistics report to file."""
        report_path = os.path.join(self.export_handler.output_dir, 'extraction_report.json')
        summary = self.statistics.get_summary()
        summary['timestamp'] = datetime.now().isoformat()

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        logging.info(f"Statistics report saved to {report_path}")


def setup_logging(config: Config):
    """Setup logging configuration."""
    log_level = getattr(logging, config.get('logging.level', 'INFO'))
    log_file = config.get('logging.file', 'exam_extraction.log')
    console = config.get('logging.console', True)

    handlers = []

    if console:
        handlers.append(logging.StreamHandler())

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Enhanced Thai Exam Data Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract default range from config
  python exam_extractor.py

  # Extract specific range
  python exam_extractor.py --start 14000 --end 15000

  # Dry-run to see what would be downloaded
  python exam_extractor.py --dry-run --start 14000 --end 14010

  # Use custom config file
  python exam_extractor.py --config my_config.yaml

  # Disable resume (re-download existing files)
  python exam_extractor.py --no-resume
        """
    )

    parser.add_argument(
        '--start',
        type=int,
        help='Starting exam ID (overrides config)'
    )

    parser.add_argument(
        '--end',
        type=int,
        help='Ending exam ID (overrides config)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be downloaded without actually downloading'
    )

    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Disable resume (re-download existing files)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set logging level (overrides config)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Load configuration
    config = Config(args.config)

    # Override config with command-line arguments
    if args.log_level:
        config.config['logging']['level'] = args.log_level

    if args.no_resume:
        config.config['download']['resume'] = False

    # Setup logging
    setup_logging(config)

    # Create and run extractor
    extractor = ExamExtractor(config, dry_run=args.dry_run)

    try:
        extractor.run(start_id=args.start, end_id=args.end)
    except KeyboardInterrupt:
        logging.info("Extraction interrupted by user")
        extractor.statistics.print_summary()
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
