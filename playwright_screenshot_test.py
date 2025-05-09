from playwright.sync_api import sync_playwright, Playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time
import random
import os
from datetime import datetime
from urllib.parse import urlparse
import re
import json

from dotenv import load_dotenv
from utils import gdrive_utils, gsheet_utils

# Load environment variables
load_dotenv()

# Configuration from environment variables (similar to main.py)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
URL_RANGE = os.getenv('URL_RANGE')
FOLDER_ID = os.getenv('FOLDER_ID')
COOKIES_PATH = os.getenv('COOKIES_PATH')
SCREENSHOTS_DIR = os.getenv('SCREENSHOTS_DIR', 'screenshots')

# Setup basic logging for the test script
logging.basicConfig(
    filename='playwright_processing_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',  # Explicitly set append mode (default, but good to be clear)
    force=True     # Force this configuration
)

COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def generate_screenshot_filename(url):
    """Generate unique filename for screenshot"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    url_part = re.sub(r'[^\w\-_.]', '_', urlparse(url).netloc)[:50]
    return f"screenshot_{timestamp}_{url_part}.png"

def load_playwright_cookies(context, cookies_path):
    logging.info(f"Attempting to load cookies from: {cookies_path}")
    try:
        if not os.path.exists(cookies_path):
            logging.warning(f"Cookies file not found: {cookies_path}. Proceeding without loaded cookies.")
            print(f"⚠️ Cookies file not found: {cookies_path}")
            return
            
        with open(cookies_path, 'r') as f:
            selenium_cookies = json.load(f)
            
        if not isinstance(selenium_cookies, list):
            logging.error("Invalid cookies format in file.")
            print("❌ Invalid cookies format.")
            return

        playwright_cookies = []
        for sc in selenium_cookies:
            if not sc.get('name') or sc.get('value') is None:
                logging.warning(f"Skipping cookie with missing name or value: {sc}")
                continue

            # Handle SameSite attribute carefully
            samesite_value = sc.get('sameSite')
            valid_samesite_for_playwright = 'Lax' # Default to Lax

            if isinstance(samesite_value, str):
                samesite_lower = samesite_value.lower()
                if samesite_lower == 'strict':
                    valid_samesite_for_playwright = 'Strict'
                elif samesite_lower == 'lax':
                    valid_samesite_for_playwright = 'Lax'
                elif samesite_lower == 'none': # The string "none"
                    valid_samesite_for_playwright = 'None'
                # else it remains 'Lax' as per default
            elif samesite_value is None: # Handles JSON null
                # Typically, SameSite=None requires Secure attribute. 
                # Playwright might enforce this. For now, we'll map null to 'Lax' 
                # or 'None' if secure. A common default is Lax if unspecified.
                if sc.get('secure', False):
                    valid_samesite_for_playwright = 'None' # If secure, None is a possibility
                else:
                    # If not secure, SameSite=None is invalid. Defaulting to Lax.
                    valid_samesite_for_playwright = 'Lax' 
                    logging.warning(f"Cookie '{sc.get('name')}' has sameSite=null and is not Secure. Defaulting sameSite to Lax for Playwright.")
            # If samesite_value is some other type or an unexpected string, it will default to Lax

            pc = {
                'name': sc['name'],
                'value': sc['value'],
                'domain': sc.get('domain'),
                'path': sc.get('path', '/'),
                'httpOnly': sc.get('httpOnly', False),
                'secure': sc.get('secure', False),
                'sameSite': valid_samesite_for_playwright # Use the processed value
            }
            if sc.get('expirationDate') is not None:
                pc['expires'] = float(sc['expirationDate'])
            
            if pc['domain'] and pc['domain'].startswith('.'):
                pc['domain'] = pc['domain'][1:]

            playwright_cookies.append(pc)

        if playwright_cookies:
            context.add_cookies(playwright_cookies)
            logging.info(f"Successfully loaded {len(playwright_cookies)} cookies into Playwright context.")
            print(f"🍪 Successfully loaded {len(playwright_cookies)} cookies.")
        else:
            logging.info("No valid cookies found to load after conversion.")
            print("🍪 No valid cookies found to load.")

    except Exception as e:
        logging.error(f"Error loading cookies for Playwright: {e}", exc_info=True)
        print(f"❌ Error loading cookies: {e}")

def take_playwright_screenshot(url: str, output_path: str, context_to_use=None, headless: bool = True, timeout_ms: int = 30000) -> bool:
    """
    Navigates to a URL using Playwright and takes a full-page screenshot.
    Returns True on success, False on failure.
    """
    logging.info(f"Attempting to capture screenshot for {url} with Playwright.")
    
    owns_browser = False
    playwright_manager_local = None # Renamed to avoid conflict with global 'playwright_manager'
    browser_local = None # Renamed for clarity
    page = None # Define page here to be accessible in finally block if needed, though Playwright handles context/page closure well.

    try:
        if context_to_use:
            # Use the provided context
            page = context_to_use.new_page()
            # Cookies should already be loaded into context_to_use
        else:
            # Create new Playwright instance, browser, and context
            owns_browser = True
            logging.info("No existing Playwright context provided. Initializing new one for this screenshot.")
            playwright_manager_local = sync_playwright().start()
            browser_local = playwright_manager_local.chromium.launch(headless=True) # Or False for debugging
            
            # Create a new context if one wasn't provided
            # Ensure user_agent and viewport are consistent if creating a new context here
            context = browser_local.new_context(
                user_agent=COMMON_USER_AGENT,  # Use the global constant
                viewport={'width': 1920, 'height': 1080} # Consistent viewport
            )
            if COOKIES_PATH: # Load cookies if a new context is made
                load_playwright_cookies(context, COOKIES_PATH)
            page = context.new_page()

        # Use 'domcontentloaded' for faster page loads, 'networkidle' can be too slow for some pages.
        page.goto(url, wait_until="domcontentloaded", timeout=60000) 
        logging.info(f"Navigated to {url}")

        # Attempt to click the cookie consent button
        try:
            cookie_button_selector = "button:has-text('Accept all cookies')"
            # Wait for the button to be visible, with a timeout
            page.wait_for_selector(cookie_button_selector, timeout=5000, state='visible')
            page.click(cookie_button_selector)
            logging.info("Clicked 'Accept all cookies' button.")
            print("🍪 Clicked 'Accept all cookies' button.")
            # Wait a moment for the banner to disappear/page to adjust
            page.wait_for_timeout(1500) # 1.5 seconds
        except Exception as e_cookie_click:
            logging.warning(f"Could not click cookie consent button (or it wasn't found): {e_cookie_click}")
            print(f"⚠️  Could not click cookie consent button for {url} (or it wasn't found). Continuing...")

        # Get page dimensions for logging (optional, as full_page=True handles it)
        width = page.evaluate("() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, document.body.offsetWidth, document.documentElement.offsetWidth, document.body.clientWidth, document.documentElement.clientWidth)")
        height = page.evaluate("() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight, document.documentElement.offsetHeight, document.body.clientHeight, document.documentElement.clientHeight)")
        logging.info(f"Playwright - Page dimensions: Width={width}, Height={height}")
        print(f"📏 Playwright - Page dimensions: Width={width}, Height={height}")

        # Take full page screenshot
        page.screenshot(path=output_path, full_page=True, timeout=120000) # Increased timeout for screenshot
        logging.info(f"Screenshot saved to {output_path}")
        
        return True

    except Exception as e:
        logging.error(f"An error occurred with Playwright for {url}: {e}", exc_info=True)
        for handler in logging.getLogger().handlers:
            handler.flush() # Ensure logs are written
        if page and not page.is_closed(): # Ensure page is defined and not closed before trying to close
            try:
                # Attempt to take a screenshot of the error page, if possible
                error_screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{os.path.basename(output_path)}")
                page.screenshot(path=error_screenshot_path, full_page=True)
                logging.info(f"Saved error page screenshot to {error_screenshot_path}")
            except Exception as e_screen:
                logging.error(f"Could not take screenshot of error page: {e_screen}")
        # The rest of the cleanup (closing page, browser if owned) is in the finally block
        return False
    finally:
        if page and not page.is_closed():
            page.close()
            logging.info(f"Closed page for {url}")
        if owns_browser: # Only close browser if this function created it
            if browser_local and browser_local.is_connected(): # Check if browser_local was initialized and is connected
                logging.info("Closing Playwright browser (owned by this function).")
                browser_local.close()
            if playwright_manager_local: # Stop playwright manager if we started it
                logging.info("Stopping Playwright manager (owned by this function).")
                playwright_manager_local.stop()

def main_playwright_processing():
    logging.info("--- Starting Playwright Processing ---")
    playwright_manager = None
    browser = None
    context = None # Define context here to be accessible in finally

    try:
        missing_vars = []
        if not SPREADSHEET_ID: missing_vars.append("SPREADSHEET_ID")
        if not URL_RANGE: missing_vars.append("URL_RANGE")
        if not FOLDER_ID: missing_vars.append("FOLDER_ID")
        if not COOKIES_PATH: missing_vars.append("COOKIES_PATH")
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}."
            logging.critical(error_msg)
            print(f"❌ {error_msg} Please check your .env file.")
            return

        print("\n🔄 Initializing Google services...")
        logging.info("Initializing Google services.")
        drive_service = gdrive_utils.get_drive_service()
        print("✅ Google Drive service initialized")
        logging.info("Google Drive service initialized.")
        sheets_service = gsheet_utils.get_sheets_service()
        print("✅ Google Sheets service initialized")
        logging.info("Google Sheets service initialized.")

        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

        print("\n🚀 Initializing Playwright browser...")
        logging.info("Initializing Playwright browser and context.")
        playwright_manager = sync_playwright().start()
        browser = playwright_manager.chromium.launch(headless=True) # Or False for debugging
        context = browser.new_context(
            user_agent=COMMON_USER_AGENT,
            viewport={'width': 1920, 'height': 1080} # Default viewport
        )
        if COOKIES_PATH:
            load_playwright_cookies(context, COOKIES_PATH) # Load cookies once into the shared context
        else:
            logging.warning("COOKIES_PATH not set. Proceeding without loading cookies globally.")
            print("⚠️ COOKIES_PATH not set. Proceeding without loading cookies globally.")
        print("✅ Playwright browser and context initialized.")
        logging.info("Playwright browser and context initialized, cookies loaded if path was provided.")

        print("\n📋 Reading URLs from spreadsheet...")
        logging.info("Reading URLs from spreadsheet.")
        urls = gsheet_utils.read_urls(sheets_service, SPREADSHEET_ID, URL_RANGE)
        
        if not urls:
            msg = "⚠️ No URLs found to process"
            print(msg)
            logging.warning(msg)
            return
        
        total_urls = len(urls)
        print(f"📊 Found {total_urls} URLs to process using Playwright.")
        logging.info(f"Found {total_urls} URLs to process.")
        
        successful_pw = 0
        failed_pw = 0
        
        for i, url in enumerate(urls):
            print(f"\n[Progress: {i+1}/{total_urls}] Using Playwright for URL: {url}")
            logging.info(f"Processing URL ({i+1}/{total_urls}): {url}")

            # Check if already processed (using the existing gsheet_utils function)
            # Assumes your current sheet logic (checking column C) is up-to-date.
            # The row index for gsheet_utils.is_url_processed needs to be 0-based from the start of URL_RANGE.
            # If URL_RANGE starts at B2, then the first URL is at row index 0 relative to the fetched 'urls' list.
            # The `is_url_processed` function needs the actual row number in the sheet.
            # Example: if URL_RANGE is Sheet1!B2:B, the first URL (urls[0]) is in row 2. So, i + 2.
            # We need to parse the starting row from URL_RANGE for accuracy if it's not fixed.
            # For now, assuming URL_RANGE starts at row 2 (e.g., B2).
            # Let's pass the current row number in the sheet to is_url_processed.
            # The 'urls' list is 0-indexed. If URL_RANGE = "Sheet1!B2:B", then urls[0] is for row 2.
            # So, the sheet row number is i + starting_row_of_url_range.
            # Let's make a simple assumption: extract start row from URL_RANGE.
            match = re.search(r'![A-Z]+([0-9]+):', URL_RANGE)
            start_row_in_sheet = 2 # Default if not found or simple range like B:B
            if match:
                start_row_in_sheet = int(match.group(1))
            
            current_sheet_row = start_row_in_sheet + i

            if gsheet_utils.is_url_processed(sheets_service, SPREADSHEET_ID, current_sheet_row):
                skip_msg = f"⏩ Skipping URL (GDrive link found in Sheet row {current_sheet_row}): {url}"
                print(skip_msg)
                logging.info(skip_msg)
                successful_pw += 1 # Count as success as it's already done
                continue
            
            if not url.strip().startswith(('http://', 'https://')):
                invalid_msg = f"❌ Invalid URL format: {url}"
                print(invalid_msg)
                logging.error(invalid_msg)
                failed_pw +=1
                continue
            
            screenshot_filename = generate_screenshot_filename(url)
            screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
            
            screenshot_success = take_playwright_screenshot(url, screenshot_path, context_to_use=context) # Pass the shared context

            if screenshot_success:
                print(f"✅ Screenshot captured with Playwright: {screenshot_filename}")
                logging.info(f"Playwright screenshot successful: {screenshot_filename}")
                
                print("📤 Uploading to Google Drive...")
                logging.info(f"Uploading {screenshot_filename} to Google Drive.")
                try:
                    _file_id, web_link = gdrive_utils.upload_file(drive_service, screenshot_path, FOLDER_ID)
                    print(f"✅ Uploaded to Drive: {web_link}")
                    logging.info(f"Uploaded {screenshot_filename} to {web_link}.")
                    
                    print("📝 Updating Google Sheet with GDrive link...")
                    metadata_range = f'Sheet1!C{current_sheet_row}'
                    metadata = [[web_link]]
                    gsheet_utils.update_metadata(sheets_service, SPREADSHEET_ID, metadata_range, metadata)
                    print("✅ Sheet updated successfully with GDrive link")
                    logging.info(f"Sheet updated for {url} with {web_link}.")
                    successful_pw += 1
                except Exception as e_upload_sheet:
                    err_msg = f"Error during upload/sheet update for {url}: {e_upload_sheet}"
                    print(f"❌ {err_msg}")
                    logging.error(err_msg)
                    failed_pw += 1
                finally:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        logging.info(f"Cleaned up local screenshot: {screenshot_path}")
            else:
                err_msg = f"❌ Failed to capture screenshot with Playwright for URL: {url}"
                print(err_msg)
                logging.error(err_msg)
                failed_pw += 1
            
            if i < total_urls - 1:
                # wait_delay = random.uniform(2.0, 5.0) # Original random delay
                wait_delay = 3.0 # User requested fixed 3 seconds
                print(f"⏳ Waiting {wait_delay:.2f} seconds before next URL...")
                time.sleep(wait_delay)
        
        print(f"\n✨ Playwright Processing completed!")
        print(f"📊 Summary:")
        print(f"   ✅ Successful: {successful_pw}")
        print(f"   ❌ Failed: {failed_pw}")
        print(f"   📊 Total: {total_urls}\n")
        logging.info(f"Playwright processing summary: Successful={successful_pw}, Failed={failed_pw}, Total={total_urls}")

    except Exception as e_main:
        crit_msg = f"❌ Critical error in Playwright main processing: {e_main}"
        print(crit_msg)
        logging.critical(crit_msg, exc_info=True)
        for handler in logging.getLogger().handlers:
            handler.flush() # Ensure logs are written
    finally:
        logging.info("--- Playwright Processing Ended ---")
        for handler in logging.getLogger().handlers: # Flush logs at the very end too
            handler.flush()
        if browser and browser.is_connected():
            logging.info("Closing Playwright browser.")
            print("🚪 Closing Playwright browser...")
            browser.close()
        if playwright_manager:
            logging.info("Stopping Playwright manager.")
            playwright_manager.stop()
            print("🛑 Playwright manager stopped.")

if __name__ == "__main__":
    main_playwright_processing() 