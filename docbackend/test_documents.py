import requests
import os
from pathlib import Path
import time

def test_document_processing(image_path, expected_type=None):
    """Test document processing with a specific image"""
    url = 'http://127.0.0.1:8000/api/documents/process/'
    
    print(f"\nTesting document: {os.path.basename(image_path)}")
    print(f"Image path: {image_path}")
    print(f"Expected type: {expected_type if expected_type else 'Not specified'}")
    
    if not os.path.exists(image_path):
        print(f"Error: Test image file {image_path} not found")
        return False
    
    try:
        # Open the image file
        with open(image_path, 'rb') as f:
            # Create the multipart form data
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            
            print("\nSending request...")
            print(f"File size: {os.path.getsize(image_path)} bytes")
            
            # Make the POST request
            response = requests.post(url, files=files)
            
            print('\nResponse Status Code:', response.status_code)
            
            if response.ok:
                data = response.json()
                print('\nExtracted Text:')
                print('-' * 60)
                print(data.get('extracted_text', 'No text extracted'))
                print('-' * 60)
                print('\nClassification:', data.get('classification', 'No classification'))
                print('Document ID:', data.get('document_id'))
                
                if expected_type:
                    actual_type = data.get('classification', '').lower()
                    matches = actual_type == expected_type.lower()
                    print(f'\nClassification accuracy: {"✓ Correct" if matches else "✗ Incorrect"}')
                    if not matches:
                        print(f'Expected: {expected_type.lower()}, Got: {actual_type}')
                    return matches
                return True
            else:
                print('\nError Response:')
                print(response.text)
                return False
            
    except requests.exceptions.RequestException as e:
        print('Network Error:', e)
        return False
    except Exception as e:
        print('Error:', e)
        return False

def run_test_suite():
    """Run tests with different types of documents"""
    base_dir = Path(__file__).resolve().parent
    assets_dir = base_dir.parent / 'assets' / 'images'
    
    test_cases = [
        {
            'path': str(assets_dir / 'udmaddress.png'),
            'expected_type': 'letter'
        },
        {
            'path': str(base_dir / 'test_image.jpg'),
            'expected_type': 'form'
        },
        {
            'path': str(assets_dir / 'udm-logo.png'),
            'expected_type': 'identification'
        }
    ]
    
    total_tests = len(test_cases)
    successful_tests = 0
    accurate_classifications = 0
    
    print("Starting document processing test suite...")
    print(f"Total test cases: {total_tests}")
    
    for test_case in test_cases:
        print("\n" + "="*80)
        success = test_document_processing(test_case['path'], test_case.get('expected_type'))
        if success:
            successful_tests += 1
            if test_case.get('expected_type'):
                accurate_classifications += 1
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "="*80)
    print("\nTest Suite Results:")
    print(f"Total tests run: {total_tests}")
    print(f"Successful API calls: {successful_tests}/{total_tests}")
    if total_tests > 0:
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"Classification accuracy: {(accurate_classifications/total_tests)*100:.1f}%")

if __name__ == '__main__':
    run_test_suite()