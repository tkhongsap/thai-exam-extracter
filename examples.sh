#!/bin/bash
# Example usage commands for Thai Exam Extractor

echo "Thai Exam Data Extractor - Example Commands"
echo "==========================================="
echo ""

echo "1. Basic extraction with default config:"
echo "   python3 exam_extractor.py"
echo ""

echo "2. Extract specific range:"
echo "   python3 exam_extractor.py --start 14000 --end 15000"
echo ""

echo "3. Dry-run to preview (no actual downloads):"
echo "   python3 exam_extractor.py --dry-run --start 14000 --end 14010"
echo ""

echo "4. Extract with debug logging:"
echo "   python3 exam_extractor.py --log-level DEBUG --start 14000 --end 14100"
echo ""

echo "5. Force re-download (disable resume):"
echo "   python3 exam_extractor.py --no-resume --start 14000 --end 14010"
echo ""

echo "6. Use custom config file:"
echo "   python3 exam_extractor.py --config my_config.yaml"
echo ""

echo "7. Small test run (recommended for first time):"
echo "   python3 exam_extractor.py --start 50 --end 75"
echo ""

echo "8. View help and all options:"
echo "   python3 exam_extractor.py --help"
echo ""
