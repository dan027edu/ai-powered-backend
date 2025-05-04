# DocBackend

DocBackend is a Django-based backend application that integrates with Appwrite and utilizes pre-trained Optical Character Recognition (OCR) and Convolutional Neural Network (CNN) models for extracting text and classifying documents.

## Features

- Integration with Appwrite for backend services.
- Pre-trained OCR model for text extraction from documents.
- Pre-trained CNN model for document classification.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd docbackend
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- The API endpoints can be accessed at `http://localhost:8000/api/`.
- Refer to the `api/urls.py` file for available endpoints.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.