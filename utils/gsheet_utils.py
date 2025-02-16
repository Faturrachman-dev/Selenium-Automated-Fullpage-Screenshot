from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
MAX_RETRIES = 3

def get_sheets_service():
    """Initialize Google Sheets service with improved error handling"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json', 
            scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logging.error(f"Error initializing Sheets service: {str(e)}")
        raise

def validate_range(range_name):
    """Validate sheet range format"""
    try:
        sheet, cell_range = range_name.split('!')
        if not sheet or not cell_range:
            raise ValueError(f"Invalid range format: {range_name}")
        return True
    except Exception as e:
        logging.error(f"Range validation error: {str(e)}")
        return False

def is_url_processed(service, spreadsheet_id, row_index):
    """Check if URL already has metadata filled in the spreadsheet"""
    try:
        metadata_range = f'Sheet1!B{row_index + 2}:D{row_index + 2}'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=metadata_range
        ).execute()
        
        values = result.get('values', [])
        # Check if we have all three metadata columns filled (title, link, thumbnail)
        return bool(values and len(values[0]) == 3 and all(values[0]))
    except Exception as e:
        logging.error(f"Error checking URL processing status: {str(e)}")
        return False

def read_urls(service, spreadsheet_id, range_name):
    """Enhanced URL reading with validation and retry mechanism"""
    if not validate_range(range_name):
        raise ValueError(f"Invalid range format: {range_name}")
        
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logging.warning('No URLs found in the specified range')
                return []
                
            # Validate and clean URLs
            urls = []
            for row in values:
                if row and isinstance(row[0], str):
                    url = row[0].strip()
                    if url.startswith(('http://', 'https://')):
                        urls.append(url)
                    else:
                        logging.warning(f"Skipping invalid URL: {url}")
                        
            return urls
            
        except HttpError as e:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                raise
            wait_time = retry_count * 2
            logging.warning(f"URL reading attempt {retry_count} failed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
    raise Exception(f"Failed to read URLs after {MAX_RETRIES} attempts")

def update_metadata(service, spreadsheet_id, range_name, values):
    """Update sheet with metadata using batch update"""
    if not validate_range(range_name):
        raise ValueError(f"Invalid range format: {range_name}")
        
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            body = {
                'values': values,
                'majorDimension': 'ROWS'
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logging.info(f"Sheet updated successfully: {result.get('updatedCells')} cells updated")
            return result
            
        except HttpError as e:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                raise
            wait_time = retry_count * 2
            logging.warning(f"Update attempt {retry_count} failed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
    raise Exception(f"Failed to update sheet after {MAX_RETRIES} attempts")
