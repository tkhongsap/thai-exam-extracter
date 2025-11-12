"""Tests for DataValidator class."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import exam_extractor
sys.path.insert(0, str(Path(__file__).parent.parent))
from exam_extractor import DataValidator


class TestDataValidator:
    """Test cases for DataValidator class."""

    def test_valid_exam_data(self):
        """Test validation of valid exam data."""
        valid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam",
                "level_name": "ป.1",
                "subject_name": "ภาษาไทย",
                "question_count": 10
            },
            "questions": [
                {
                    "question_number": 1,
                    "question_id": 456,
                    "question_text": "What is the capital?",
                    "choices": [
                        {"choice_number": 1, "choice_text": "Bangkok", "is_correct": True},
                        {"choice_number": 2, "choice_text": "Chiang Mai", "is_correct": False}
                    ]
                }
            ]
        }

        is_valid, errors = DataValidator.validate_exam_data(valid_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_metadata(self):
        """Test validation with missing metadata."""
        invalid_data = {
            "questions": [
                {
                    "question_number": 1,
                    "question_id": 456,
                    "question_text": "Test question",
                    "choices": []
                }
            ]
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("metadata" in error.lower() for error in errors)

    def test_missing_questions(self):
        """Test validation with missing questions."""
        invalid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam",
                "level_name": "ป.1",
                "subject_name": "ภาษาไทย"
            }
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("questions" in error.lower() for error in errors)

    def test_missing_required_metadata_keys(self):
        """Test validation with missing required metadata keys."""
        invalid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam"
                # Missing level_name and subject_name
            },
            "questions": [
                {
                    "question_number": 1,
                    "question_id": 456,
                    "question_text": "Test question",
                    "choices": []
                }
            ]
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("level_name" in error for error in errors)
        assert any("subject_name" in error for error in errors)

    def test_empty_questions_list(self):
        """Test validation with empty questions list."""
        invalid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam",
                "level_name": "ป.1",
                "subject_name": "ภาษาไทย"
            },
            "questions": []
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("empty" in error.lower() for error in errors)

    def test_invalid_data_type(self):
        """Test validation with invalid data type (not a dict)."""
        invalid_data = "This is a string, not a dict"

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("dictionary" in error.lower() for error in errors)

    def test_questions_not_a_list(self):
        """Test validation when questions is not a list."""
        invalid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam",
                "level_name": "ป.1",
                "subject_name": "ภาษาไทย"
            },
            "questions": "not a list"
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        assert any("list" in error.lower() for error in errors)

    def test_missing_question_keys(self):
        """Test validation with missing required question keys."""
        invalid_data = {
            "metadata": {
                "exam_id": 123,
                "exam_name": "Test Exam",
                "level_name": "ป.1",
                "subject_name": "ภาษาไทย"
            },
            "questions": [
                {
                    "question_number": 1,
                    # Missing question_id, question_text, choices
                }
            ]
        }

        is_valid, errors = DataValidator.validate_exam_data(invalid_data)

        assert is_valid is False
        # Should report missing question keys
        assert len(errors) > 0
