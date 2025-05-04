# filepath: /docbackend/docbackend/core/services/appwrite_service.py

import requests

class AppwriteService:
    def __init__(self, endpoint, project_id, api_key):
        self.endpoint = endpoint
        self.project_id = project_id
        self.api_key = api_key

    def create_document(self, collection_id, document_id, data):
        url = f"{self.endpoint}/v1/database/collections/{collection_id}/documents/{document_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
        }
        response = requests.post(url, json=data, headers=headers)
        return response.json()

    def get_document(self, collection_id, document_id):
        url = f"{self.endpoint}/v1/database/collections/{collection_id}/documents/{document_id}"
        headers = {
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def delete_document(self, collection_id, document_id):
        url = f"{self.endpoint}/v1/database/collections/{collection_id}/documents/{document_id}"
        headers = {
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
        }
        response = requests.delete(url, headers=headers)
        return response.json()