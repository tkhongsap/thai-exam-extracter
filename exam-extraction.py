#!/usr/bin/env python3
"""
This Python script extracts exam data from an API endpoint and saves the information as JSON files. 
The script loops through a range of exam IDs, fetches data including metadata (e.g., exam name, level, subject), 
questions, and choices, and saves the files in the "data/output" directory. 
The JSON files are named based on the exam metadata for easy identification.
"""

import requests
import json
import os
import re
import time
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('exam_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Replace invalid characters in filenames with underscore.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def extract_exam_data(exam_id: int) -> Optional[Dict[str, Any]]:
    """
    Extract exam data from the API for a given exam_id.
    
    Args:
        exam_id: The ID of the exam to extract
        
    Returns:
        Dict or None: The extracted data dictionary or None if extraction failed
    """
    try:
        # API endpoint URL
        api_url = f"https://www.trueplookpanya.com/webservice/api/examination/formdoexamination?exam_id={exam_id}"
        
        # Send a GET request to the API endpoint
        response = requests.get(api_url, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract metadata
            metadata = {
                "exam_id": data['data']['exam']['exam_id'],
                "exam_name": data['data']['exam']['exam_name'],
                "level_name": data['data']['exam']['level_name'],
                "subject_name": data['data']['exam']['subject_name'],
                "question_count": data['data']['exam']['question_count']
            }
            
            # Extract questions and choices
            questions_list = []
            for i, question_data in enumerate(data['data']['formdo'], 1):
                question_detail = {
                    "question_number": i,
                    "question_id": question_data['question_id'],
                    "question_text": question_data['question_detail'],
                    "choices": []
                }
                
                for j, choice in enumerate(question_data['choice'], 1):
                    choice_detail = {
                        "choice_number": j,
                        "choice_text": choice['detail'],
                        "is_correct": True if choice['answer'] == "true" else False
                    }
                    question_detail["choices"].append(choice_detail)
                
                questions_list.append(question_detail)
            
            # Combine metadata and questions into a single dictionary
            output_data = {
                "metadata": metadata,
                "questions": questions_list
            }
            
            return output_data
        else:
            logger.error(f"Failed to retrieve data for exam_id {exam_id}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error extracting data for exam_id {exam_id}: {str(e)}")
        return None

def save_exam_data(output_data: Dict[str, Any], output_dir: str) -> str:
    """
    Save exam data to a JSON file.
    
    Args:
        output_data: The data to save
        output_dir: Directory to save the file
        
    Returns:
        str: The path to the saved file
    """
    try:
        metadata = output_data["metadata"]
        
        # Create a filename based on metadata and sanitize it
        filename = f"{metadata['exam_id']}_{metadata['exam_name']}_{metadata['level_name']}_{metadata['subject_name']}.json"
        filename = sanitize_filename(filename)  # Sanitize the filename
        
        # Full path for the output file
        file_path = os.path.join(output_dir, filename)
        
        # Save the result to a JSON file
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, ensure_ascii=False, indent=4)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        return ""

def main():
    """Main function to extract and save exam data."""
    try:
        # Ensure the output directory exists
        output_dir = os.path.join("data", "output")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Define the range of exam IDs to process
        start_id = 12585
        end_id = 12586  # Adjust the range as needed
        
        logger.info(f"Starting extraction for exam IDs {start_id} to {end_id}")
        
        success_count = 0
        failure_count = 0
        
        # Loop through the range of exam IDs
        for exam_id in range(start_id, end_id + 1):
            try:
                # Extract data for this exam ID
                output_data = extract_exam_data(exam_id)
                
                if output_data:
                    # Save the extracted data
                    file_path = save_exam_data(output_data, output_dir)
                    
                    if file_path:
                        logger.info(f"Data extraction complete for exam_id {exam_id}. Saved to '{file_path}'.")
                        success_count += 1
                    else:
                        logger.error(f"Failed to save data for exam_id {exam_id}.")
                        failure_count += 1
                else:
                    logger.warning(f"No data retrieved for exam_id {exam_id}.")
                    failure_count += 1
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing exam_id {exam_id}: {str(e)}")
                failure_count += 1
        
        logger.info(f"Extraction complete. Successfully processed {success_count} exams. Failed: {failure_count}")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()
