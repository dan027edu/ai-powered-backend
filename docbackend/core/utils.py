from django.core.cache import cache
from django.db import transaction
import time

def get_processing_lock(document_id, timeout=30, max_retries=3, retry_delay=1):
    """
    Attempt to acquire a processing lock with retries
    
    Args:
        document_id: ID of the document
        timeout: Lock timeout in seconds (default: 30 seconds)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 1 second)
    """
    lock_id = f'doc_processing_{document_id}'
    
    for attempt in range(max_retries):
        try:
            acquired = cache.add(lock_id, 'lock', timeout)
            if acquired:
                return True
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
    
    return False

def release_processing_lock(document_id):
    """Release the processing lock for a document"""
    lock_id = f'doc_processing_{document_id}'
    try:
        cache.delete(lock_id)
        return True
    except Exception:
        return False

def process_document(document):
    # Acquire lock before processing
    if not get_processing_lock(document.id):
        raise Exception("Document is currently being processed. Please try again in a few moments.")
    
    try:
        with transaction.atomic():
            # ...existing document processing code...
            pass
    finally:
        release_processing_lock(document.id)