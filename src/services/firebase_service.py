import firebase_admin
from firebase_admin import credentials, storage
import os
from datetime import datetime, timedelta
import uuid

import logging
logger = logging.getLogger(__name__)

class FirebaseStorageService:
    """Service for interacting with Firebase Storage."""
    
    def __init__(self, credential_path=None, bucket_name=None):
        """
        Initialize Firebase Storage service.
        
        Args:
            credential_path (str, optional): Path to Firebase credentials JSON file
            bucket_name (str, optional): Firebase Storage bucket name
        """
        self.initialized = False
        self.bucket = None
        if not credential_path:
            credential_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
        if not bucket_name:
            bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        self.init_firebase(credential_path, bucket_name)
    
    def init_firebase(self, credential_path=None, bucket_name=None):
        """Initialize Firebase app if not already initialized."""
        if not self.initialized:
            try:
                # Try to get default app, will raise if not initialized
                firebase_admin.get_app()
                self.initialized = True
            except ValueError:
                # Initialize app if not already done
                if credential_path:
                    cred = credentials.Certificate(credential_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': bucket_name
                    })
                else:
                    # Initialize using environment variables or default credentials
                    firebase_admin.initialize_app(options={
                        'storageBucket': bucket_name
                    })
                self.initialized = True
        
        # Get bucket
        if bucket_name:
            self.bucket = storage.bucket(bucket_name)
        else:
            self.bucket = storage.bucket()
    
    def upload_file(self, file_path, destination_path=None, make_public=False):
        """
        Upload a file to Firebase Storage.
        
        Returns:
            str: URL of the uploaded file
        """
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        # If no destination path provided, use filename with timestamp
        if not destination_path:
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            destination_path = f"uploads/{timestamp}_{unique_id}_{filename}"
        
        # Create a blob and upload the file
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(file_path)
        
        # Make public if requested
        if make_public:
            blob.make_public()
            return blob.public_url
        else:
            # Generate a signed URL that expires after a set time
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="GET"
            )
    
    def upload_from_memory(self, file_data, destination_path, content_type=None, make_public=False):
        """
        Upload data from memory to Firebase Storage.
        
        Returns:
            str: URL of the uploaded file
        """
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(file_data, content_type=content_type)
        
        if make_public:
            blob.make_public()
            return blob.public_url
        else:
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="GET"
            )
        
    def upload_gltf_file(self, file_path, destination_path=None, make_public=False):
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        if not destination_path:
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            destination_path = f"uploads/{timestamp}_{unique_id}_{filename}"
        
        # Create a blob and upload the file
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(file_path, content_type='model/gltf-binary')

        # Make public if requested
        if make_public:
            blob.make_public()
            return blob.public_url
        else:
            # Generate a signed URL that expires after a set time
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="GET"
            )
        
    
        
    @classmethod
    def upload_from_url(cls, source_url=None, destination_path=None):
        """
        Upload file from a URL to Firebase Storage.
        
        Args:
            source_url: URL of the file to upload
            destination_path: Path in Firebase Storage
            
        Returns:
            str: URL of the uploaded file
        """
        if not source_url:
            return None
            
        try:
            # Create a new instance of the service for this operation
            service = cls()
            
            # Download the file from the URL
            import requests
            response = requests.get(source_url, stream=True)
            response.raise_for_status()
            
            # Create a blob and upload the file
            blob = service.bucket.blob(destination_path)
            
            # Upload from the response content
            blob.upload_from_string(
                response.content,
                content_type=response.headers.get('content-type', 'application/octet-stream')
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Return the public URL
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading from URL: {str(e)}")
            return None
    
    def download_file(self, source_path, destination_path):
        """Download a file from Firebase Storage."""
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        blob = self.bucket.blob(source_path)
        blob.download_to_filename(destination_path)
        return os.path.exists(destination_path)
    
    def get_file_url(self, file_path, make_public=False, expiration_minutes=15):
        """Get the URL for a file in Firebase Storage."""
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        blob = self.bucket.blob(file_path)
        
        if make_public:
            blob.make_public()
            return blob.public_url
        else:
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
    
    def delete_file(self, file_path):
        """Delete a file from Firebase Storage."""
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        blob = self.bucket.blob(file_path)
        blob.delete()
        return True
    
    def list_files(self, prefix=None):
        """List files in Firebase Storage with optional prefix filter."""
        if not self.initialized or not self.bucket:
            raise ValueError("Firebase Storage not properly initialized")
        
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    

firebase_storage_service = FirebaseStorageService(
    credential_path=os.getenv("FIREBASE_CREDENTIAL_PATH"),
    bucket_name=os.getenv("FIREBASE_STORAGE_BUCKET")
)