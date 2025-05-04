import os
import pytesseract
from PIL import Image
import docx
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import mimetypes
import tempfile
from django.conf import settings

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with Tesseract configuration"""
        # Try to get Tesseract path from environment or settings
        tesseract_cmd = os.getenv('TESSERACT_CMD', settings.TESSERACT_CMD)
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.debug = settings.DEBUG

    def extract_text(self, file_path):
        """Extract text from various document types"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = self._guess_mime_type(file_path)
        
        if not mime_type:
            raise ValueError("Could not determine file type")

        try:
            if 'image' in mime_type:
                text = self._process_image(file_path)
            elif mime_type == 'application/pdf':
                text = self._process_pdf(file_path)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                text = self._process_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")

            if not text or not text.strip():
                raise ValueError("No text could be extracted from the document")

            return text.strip()
        except Exception as e:
            if self.debug:
                print(f"Error processing document: {str(e)}")
            raise

    def _guess_mime_type(self, file_path):
        """Basic file type detection based on content"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(2048)
                # PDF magic number
                if header.startswith(b'%PDF'):
                    return 'application/pdf'
                # DOCX is a ZIP file
                if header.startswith(b'PK'):
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                # Common image formats
                if header.startswith(b'\xFF\xD8'):
                    return 'image/jpeg'
                if header.startswith(b'\x89PNG'):
                    return 'image/png'
            return None
        except Exception:
            return None

    def _process_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Improve image quality for OCR
                img = img.resize((int(img.size[0] * 2), int(img.size[1] * 2)), Image.LANCZOS)

                # Apply OCR with improved configuration
                text = pytesseract.image_to_string(
                    img,
                    config='--psm 1 --oem 3'  # Use advanced OCR mode
                )
                return text.strip()
        except Exception as e:
            if self.debug:
                print(f"Error processing image: {str(e)}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")

    def _process_pdf(self, pdf_path):
        """Extract text from PDF using PyPDF2 and OCR if needed"""
        text = ""
        try:
            # Try text extraction first
            pdf = PdfReader(pdf_path)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text += page_text + "\n"

            # If no text was extracted, try OCR
            if not text.strip():
                try:
                    # Convert PDF to images
                    images = convert_from_path(pdf_path, dpi=300)  # Higher DPI for better quality
                    for image in images:
                        # Convert image to RGB mode if needed
                        if image.mode not in ('RGB', 'L'):
                            image = image.convert('RGB')
                        
                        # Apply OCR with improved configuration
                        page_text = pytesseract.image_to_string(
                            image,
                            config='--psm 1 --oem 3'  # Use advanced OCR mode
                        )
                        text += page_text + "\n"
                except Exception as e:
                    if self.debug:
                        print(f"Error during PDF OCR: {str(e)}")
                    raise ValueError(f"Failed to extract text from PDF using OCR: {str(e)}")
                    
            return text.strip()
        except Exception as e:
            if self.debug:
                print(f"Error processing PDF: {str(e)}")
            raise ValueError(f"Failed to process PDF: {str(e)}")

    def _process_docx(self, docx_path):
        """Extract text from Word document"""
        try:
            doc = docx.Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            if not text.strip():
                raise ValueError("No text found in Word document")
            return text
        except Exception as e:
            if self.debug:
                print(f"Error processing Word document: {str(e)}")
            raise ValueError(f"Failed to extract text from Word document: {str(e)}")