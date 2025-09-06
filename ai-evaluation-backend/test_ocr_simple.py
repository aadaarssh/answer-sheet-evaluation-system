#!/usr/bin/env python3
"""
Simple OCR test without Unicode characters for Windows compatibility.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_ocr():
    try:
        print('Testing OCR Service...')
        print('=' * 40)
        
        # Test service import
        from app.services.ocr_service import OCRService
        print('[OK] OCR Service imported successfully')
        
        # Initialize service
        ocr_service = OCRService()
        print('[OK] OCR Service initialized successfully')
        
        # Find test image
        from app.config import settings
        upload_dir = Path(settings.upload_directory)
        image_files = list(upload_dir.glob('*.jpg')) + list(upload_dir.glob('*.png'))
        
        if not image_files:
            print('[ERROR] No image files found in upload directory')
            return False
            
        test_image = image_files[0]
        print(f'[INFO] Testing with image: {test_image.name}')
        print(f'[INFO] Image size: {test_image.stat().st_size} bytes')
        
        # Run OCR extraction
        start_time = time.time()
        
        print('[INFO] Starting OCR extraction...')
        questions, confidence = await ocr_service.extract_and_segment_questions(str(test_image))
        
        processing_time = time.time() - start_time
        
        print()
        print('OCR RESULTS:')
        print('=' * 40)
        print(f'Questions extracted: {len(questions) if questions else 0}')
        print(f'OCR confidence: {confidence}')
        print(f'Processing time: {processing_time:.2f} seconds')
        
        if confidence > 0:
            print('[SUCCESS] OCR SERVICE IS WORKING!')
            if questions:
                print()
                print('Sample question:')
                sample = questions[0]
                if hasattr(sample, 'raw_text'):
                    preview = sample.raw_text[:100] + '...' if len(sample.raw_text) > 100 else sample.raw_text
                    print(f'   Text: {preview}')
                if hasattr(sample, 'question_number'):
                    print(f'   Question #: {sample.question_number}')
        else:
            print('[CRITICAL] OCR CONFIDENCE IS STILL 0')
            print('This indicates API issues or image processing problems')
            
        return confidence > 0
        
    except Exception as e:
        print(f'[ERROR] OCR Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    print('AI Evaluation System - OCR Service Test')
    print('Testing OpenAI Vision API with real image')
    print()
    
    # Run the test
    success = asyncio.run(test_ocr())
    
    print()
    print('=' * 40)
    print(f'OCR Test Result: {"PASS" if success else "FAIL"}')
    
    if success:
        print('OCR service is working correctly!')
        print('The system should now be able to process answer sheets.')
    else:
        print('OCR service failed - check API keys and network connectivity.')
        
    return success

if __name__ == "__main__":
    main()