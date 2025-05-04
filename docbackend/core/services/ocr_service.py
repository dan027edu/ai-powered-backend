import pytesseract
from PIL import Image, ImageEnhance
import os
from django.conf import settings
import numpy as np

class OCRService:
    def __init__(self):
        # Set Tesseract command path if defined in settings
        if hasattr(settings, 'TESSERACT_CMD'):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        self.debug = settings.DEBUG

    def preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy"""
        try:
            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # Upscale image if too small
            if image.size[0] < 1000 or image.size[1] < 1000:
                scale = 2
                image = image.resize(
                    (int(image.size[0] * scale), int(image.size[1] * scale)),
                    Image.LANCZOS
                )

            return image
        except Exception as e:
            if self.debug:
                print(f"Error preprocessing image: {str(e)}")
            raise ValueError(f"Failed to preprocess image: {str(e)}")

    def extract_text(self, image_path):
        """Extract text from an image using Tesseract OCR."""
        try:
            if self.debug:
                print(f"Processing image: {image_path}")
                print(f"Image exists: {os.path.exists(image_path)}")
                print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

            image = Image.open(image_path)
            
            if self.debug:
                print(f"Image size: {image.size}")
                print(f"Image mode: {image.mode}")

            # Preprocess image
            image = self.preprocess_image(image)

            # Configure OCR
            custom_config = r'--oem 3 --psm 1'  # Use LSTM OCR Engine Mode and Automatic page segmentation
            
            # Extract text with improved configuration
            text = pytesseract.image_to_string(
                image,
                config=custom_config,
                lang='eng'  # Specify language explicitly
            )
            
            if self.debug:
                print(f"Extracted text length: {len(text)}")
                if text:
                    print(f"First 100 chars: {text[:100]}")
                else:
                    print("No text extracted")

            if not text.strip():
                raise ValueError("No text could be extracted from the image")

            return text.strip()

        except Exception as e:
            if self.debug:
                print(f"Error processing image: {str(e)}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")