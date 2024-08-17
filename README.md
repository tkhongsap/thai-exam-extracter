
# Exam Data Extractor

## Description:
This Python script is designed to extract examination data from a specified API endpoint and save the results as JSON files. The script loops through a range of exam IDs, processes the data, and stores it in the `output` folder with filenames that include metadata from the exams.

## Features:
- Fetches metadata, questions, and choices for each exam.
- Saves data as JSON files in the `output` directory.
- Automatically handles multiple exam IDs in a loop.

## Requirements:
- Python 3.x
- `requests` module
- `json` module
- `os` module

## Installation:
1. Ensure you have Python 3.x installed.
2. Install the required modules if not already installed:
   ```bash
   pip install requests
   ```

## Usage:
1. Modify the `exam_id` range in the script to specify the exams you want to extract data from.
2. Run the script:
   ```bash
   python exam_data_extractor.py
   ```
3. The JSON files will be saved in the `output` directory.

## Example:
For an exam with ID `13500`, the JSON file will be saved as:
```
output/13500_แนวข้อสอบ_A-level_สังคมศึกษา_ม.6_ชุดที่_4_ม.6_O-NET.json
```

## License:
This project is open-source and available under the MIT License.
