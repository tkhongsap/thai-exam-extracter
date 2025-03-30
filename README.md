# Exam Data Extractor

## Description:
This Python script is designed to extract examination data from a specified API endpoint and save the results as JSON files. The script loops through a range of exam IDs, processes the data, and stores it in the `data/output` folder with filenames that include metadata from the exams.

## Features:
- Fetches metadata, questions, and choices for each exam.
- Saves data as JSON files in the `data/output` directory.
- Automatically handles multiple exam IDs in a loop.
- Includes error handling and logging of all activities.
- Implements rate limiting to avoid overwhelming the server.
- Uses type hints for better code maintainability.

## Requirements:
- Python 3.x
- `requests` module
- `json` module
- `os` module
- `pathlib` module
- `typing` module
- `logging` module

## Installation:
1. Ensure you have Python 3.x installed.
2. Install the required modules if not already installed:
   ```bash
   pip install requests
   ```

## Usage:
1. Modify the `start_id` and `end_id` variables in the script to specify the range of exams you want to extract data from.
2. Run the script:
   ```bash
   python exam-extraction.py
   ```
3. The JSON files will be saved in the `data/output` directory.
4. Progress and errors will be logged to both console and `exam_extraction.log` file.

## Example:
For an exam with ID `14000`, the JSON file will be saved as:
```
data/output/14000_exam_name_level_name_subject_name.json
```

## Structure of the JSON output:
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

## License:
This project is open-source and available under the MIT License.
