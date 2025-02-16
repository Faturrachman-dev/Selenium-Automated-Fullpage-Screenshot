import os
import logging
import time
from datetime import datetime
from urllib.parse import urlparse
import re
from utils import selenium_utils, gdrive_utils, gsheet_utils
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    filename='error_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration from environment variables
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
URL_RANGE = os.getenv('SHEET_RANGE')
FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')
COOKIES_PATH = os.getenv('COOKIES_PATH')
SCREENSHOTS_DIR = os.getenv('SCREENSHOTS_DIR', 'screenshots')

def generate_screenshot_filename(url):
    """Generate unique filename for screenshot"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    url_part = re.sub(r'[^\w\-_.]', '_', urlparse(url).netloc)[:50]
    return f"screenshot_{timestamp}_{url_part}.png"

def process_url(url, row_index, driver, drive_service, sheets_service):
    """Process a single URL with improved error handling"""
    try:
        # Check if URL has already been processed
        if gsheet_utils.is_url_processed(sheets_service, SPREADSHEET_ID, row_index):
            print(f"⏩ Skipping URL (already processed): {url}")
            logging.info(f"Skipped already processed URL: {url}")
            return True

        if not url.strip().startswith(('http://', 'https://')):
            print(f"❌ Invalid URL format: {url}")
            logging.error(f"Invalid URL format: {url}")
            return False

        metadata_range = f'Sheet1!B{row_index + 2}:D{row_index + 2}'
        screenshot_filename = generate_screenshot_filename(url)
        screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
        
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"\n📸 Processing URL ({row_index + 1}): {url}")
                # Capture screenshot
                page_title = selenium_utils.capture_full_page_screenshot(driver, url, screenshot_path)
                print(f"✅ Screenshot captured: {screenshot_filename}")
                
                # Upload to Drive
                print("📤 Uploading to Google Drive...")
                if not FOLDER_ID:
                    raise Exception("Google Drive folder ID not configured in .env file")
                    
                file_id, web_link = gdrive_utils.upload_file(drive_service, screenshot_path, FOLDER_ID)
                file_metadata = gdrive_utils.get_file_metadata(drive_service, file_id)
                print(f"✅ Uploaded to Drive: {web_link}")
                
                # Update sheet
                print("📝 Updating Google Sheet...")
                metadata = [[page_title, web_link, file_metadata.get('thumbnailLink', '')]]
                gsheet_utils.update_metadata(
                    sheets_service,
                    SPREADSHEET_ID,
                    metadata_range,
                    metadata
                )
                print("✅ Sheet updated successfully")
                
                # Cleanup
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    
                logging.info(f"Successfully processed URL: {url}")
                print(f"✅ Successfully processed URL: {url}\n")
                return True
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"❌ Failed to process URL after {max_retries} attempts: {str(e)}")
                    logging.error(f"Failed to process URL {url}: {str(e)}")
                    return False
                    
                print(f"\n⚠️ Attempt {retry_count} failed: {str(e)}")
                print(f"⏳ Retrying in {2 ** retry_count} seconds...")
                time.sleep(2 ** retry_count)
                
    except Exception as e:
        print(f"❌ Error processing URL: {str(e)}")
        logging.error(f"Error processing URL {url}: {str(e)}")
        return False

def main():
    """Main execution function with improved error handling"""
    driver = None
    try:
        # Validate environment variables
        if not all([SPREADSHEET_ID, URL_RANGE, FOLDER_ID, COOKIES_PATH]):
            raise Exception("Missing required environment variables. Please check your .env file.")
            
        print("\n🔄 Initializing services...")
        drive_service = gdrive_utils.get_drive_service()
        print("✅ Google Drive service initialized")
        
        sheets_service = gsheet_utils.get_sheets_service()
        print("✅ Google Sheets service initialized")
        
        driver = selenium_utils.setup_driver()
        
        print("🍪 Loading cookies...")
        selenium_utils.load_cookies(driver, COOKIES_PATH)
        print("✅ Cookies loaded")
        
        print("\n📋 Reading URLs from spreadsheet...")
        urls = gsheet_utils.read_urls(sheets_service, SPREADSHEET_ID, URL_RANGE)
        
        if not urls:
            print("⚠️ No URLs found to process")
            logging.warning("No URLs found to process")
            return
        
        total_urls = len(urls)
        print(f"📊 Found {total_urls} URLs to process")
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls):
            print(f"\n[Progress: {i+1}/{total_urls}]")
            success = process_url(url, i, driver, drive_service, sheets_service)
            if success:
                successful += 1
            else:
                failed += 1
                print(f"❌ Failed to process URL: {url}")
            
            if i < len(urls) - 1:
                print("⏳ Waiting 3 seconds before next URL...")
                time.sleep(3)  # Increased delay between requests
        
        print(f"\n✨ Process completed!")
        print(f"📊 Summary:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total: {total_urls}\n")
                
    except Exception as e:
        print(f"❌ Main execution error: {str(e)}")
        logging.error(f"Main execution error: {str(e)}")
    finally:
        if driver:
            print("\n🔄 Closing Chrome WebDriver...")
            selenium_utils.close_driver(driver)
            print("✅ Chrome WebDriver closed")

if __name__ == "__main__":
    main()
