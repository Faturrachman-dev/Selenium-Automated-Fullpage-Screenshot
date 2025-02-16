from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import logging
import os
import time

# Update scopes to include full Drive access
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata'
]
MAX_RETRIES = 3
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def get_drive_service():
    """Initialize Google Drive service with improved error handling"""
    try:
        if not os.path.exists('credentials.json'):
            raise FileNotFoundError("credentials.json not found")
            
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json', 
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # Verify service account permissions
        try:
            about = service.about().get(fields="user").execute()
            logging.info(f"Drive service initialized for: {about.get('user', {}).get('emailAddress')}")
        except HttpError as e:
            if e.resp.status == 403:
                logging.error("Service account lacks necessary permissions. Please share the folder with the service account email.")
            raise
            
        return service
    except Exception as e:
        logging.error(f"Error initializing Drive service: {str(e)}")
        raise

def verify_folder_access(service, folder_id):
    """Verify folder exists and service account has access"""
    try:
        # Clean folder ID
        clean_folder_id = folder_id.strip().strip('"').split('#')[0].strip()
        
        # Try to get folder metadata
        folder = service.files().get(
            fileId=clean_folder_id,
            fields='id, name, mimeType'
        ).execute()
        
        # Verify it's a folder
        if folder.get('mimeType') != 'application/vnd.google-apps.folder':
            raise ValueError(f"ID {clean_folder_id} is not a folder")
            
        logging.info(f"Successfully verified access to folder: {folder.get('name')}")
        return clean_folder_id
    except HttpError as e:
        if e.resp.status == 404:
            raise ValueError(f"Folder not found or not accessible. Please verify the folder ID and ensure it's shared with {service._http.credentials.service_account_email}")
        raise

def check_file_exists(service, filename, folder_id):
    """Check if file already exists in the specified folder"""
    try:
        # Clean folder ID
        clean_folder_id = folder_id.strip().strip('"').split('#')[0].strip()
        
        # Verify folder access first
        clean_folder_id = verify_folder_access(service, clean_folder_id)
        
        query = f"name='{filename}' and '{clean_folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logging.error(f"Error checking file existence: {str(e)}")
        return []

def upload_file(service, file_path, folder_id):
    """Enhanced file upload with detailed progress reporting"""
    try:
        start_time = time.time()
        print("\n📤 Starting upload process...")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_size = os.path.getsize(file_path)
        print(f"📁 File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size ({file_size} bytes) exceeds limit ({MAX_FILE_SIZE} bytes)")
            
        file_name = os.path.basename(file_path)
        
        # Verify folder access and clean ID
        print("🔍 Verifying folder access...")
        clean_folder_id = verify_folder_access(service, folder_id)
        print(f"📂 Using Drive folder ID: {clean_folder_id}")
        
        # Optimize chunk size based on file size
        chunk_size = min(file_size, 5 * 1024 * 1024)  # 5MB chunks
        print(f"⚙️ Using chunk size: {chunk_size / (1024*1024):.2f} MB")
        
        # Check for existing files in parallel
        print("🔍 Checking for existing files...")
        check_start = time.time()
        existing_files = check_file_exists(service, file_name, clean_folder_id)
        check_duration = time.time() - check_start
        print(f"✓ File check completed in {check_duration:.2f}s")
        
        # Delete existing files if any
        if existing_files:
            print(f"🗑️ Removing {len(existing_files)} existing file(s)...")
            delete_start = time.time()
            batch = service.new_batch_http_request()
            for existing_file in existing_files:
                batch.add(service.files().delete(fileId=existing_file['id']))
            batch.execute()
            delete_duration = time.time() - delete_start
            print(f"✓ Deletion completed in {delete_duration:.2f}s")
            logging.info(f"Deleted {len(existing_files)} existing files")
        
        file_metadata = {
            'name': file_name,
            'parents': [clean_folder_id]
        }
        
        print("📦 Preparing upload...")
        media = MediaFileUpload(
            file_path,
            mimetype='image/png',
            resumable=True,
            chunksize=chunk_size
        )
        
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                upload_start = time.time()
                print("🚀 Initiating upload request...")
                request = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink',
                    supportsAllDrives=True
                )
                
                response = None
                last_progress = 0
                last_update = time.time()
                bytes_uploaded = 0
                
                print("\n📊 Upload Progress:")
                while response is None:
                    status, response = request.next_chunk()
                    current_time = time.time()
                    
                    if status:
                        progress = int(status.progress() * 100)
                        if progress > last_progress:
                            bytes_uploaded = int(file_size * (progress / 100))
                            elapsed = current_time - upload_start
                            speed = bytes_uploaded / (1024*1024*elapsed) if elapsed > 0 else 0
                            eta = (file_size - bytes_uploaded) / (speed*1024*1024) if speed > 0 else 0
                            
                            print(f"├─ {progress}% complete")
                            print(f"│  ├─ {bytes_uploaded/(1024*1024):.2f} MB / {file_size/(1024*1024):.2f} MB")
                            print(f"│  ├─ Speed: {speed:.2f} MB/s")
                            print(f"│  └─ ETA: {eta:.1f}s")
                            
                            last_progress = progress
                            last_update = current_time
                
                upload_duration = time.time() - upload_start
                total_duration = time.time() - start_time
                
                print("\n✅ Upload Summary:")
                print(f"├─ Upload duration: {upload_duration:.2f}s")
                print(f"├─ Average speed: {(file_size/1024/1024)/upload_duration:.2f} MB/s")
                print(f"└─ Total process time: {total_duration:.2f}s")
                
                logging.info(f"File uploaded successfully: {response.get('webViewLink')}")
                return response.get('id'), response.get('webViewLink')
                
            except HttpError as e:
                retry_count += 1
                if retry_count == max_retries:
                    if e.resp.status == 403:
                        raise ValueError(f"Permission denied. Please ensure the service account ({service._http.credentials.service_account_email}) has write access to the folder.")
                    raise
                wait_time = min(2 ** retry_count, 60)
                print(f"\n⚠️ Upload attempt {retry_count} failed")
                print(f"├─ Error: {str(e)}")
                print(f"└─ Retrying in {wait_time}s...")
                logging.warning(f"Upload attempt {retry_count} failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
    except Exception as e:
        error_msg = f"Error uploading file: {str(e)}"
        print(f"\n❌ {error_msg}")
        logging.error(error_msg)
        raise

def get_file_metadata(service, file_id):
    """Get file metadata with retry mechanism"""
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            file = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, thumbnailLink, webViewLink'
            ).execute()
            return file
        except HttpError as e:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                raise
            wait_time = retry_count * 2
            logging.warning(f"Metadata retrieval attempt {retry_count} failed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    raise Exception(f"Failed to retrieve metadata after {MAX_RETRIES} attempts")
