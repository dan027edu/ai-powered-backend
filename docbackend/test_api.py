import requests
import os
from pathlib import Path

def test_document_process():
    # URL of your document processing endpoint
    url = 'http://127.0.0.1:8000/api/documents/process/'
    
    # Path to the test image
    image_path = Path(__file__).parent.parent / 'assets' / 'images' / 'udmaddress.png'
    
    print(f"Testing with image: {image_path}")
    print(f"Image exists: {image_path.exists()}")
    
    if not image_path.exists():
        print(f"Error: Test image file {image_path} not found")
        return
    
    try:
        # Open the image file
        with open(image_path, 'rb') as f:
            # Create the multipart form data
            files = {'file': ('udmaddress.png', f, 'image/png')}
            
            print("\nSending request to:", url)
            print("File size:", os.path.getsize(image_path), "bytes")
            
            # Make the POST request
            response = requests.post(url, files=files)
            
            # Print detailed response information
            print('\nResponse Status Code:', response.status_code)
            print('Response Headers:', response.headers)
            
            if response.ok:
                print('\nSuccess! Response data:')
                data = response.json()
                print('\nExtracted Text:')
                print('-' * 40)
                print(data.get('extracted_text', 'No text extracted'))
                print('-' * 40)
                print('\nClassification:', data.get('classification', 'No classification'))
                print('Document ID:', data.get('document_id'))
            else:
                print('\nError Response:')
                print(response.text)
            
    except requests.exceptions.RequestException as e:
        print('Network Error:', e)
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_document_process()