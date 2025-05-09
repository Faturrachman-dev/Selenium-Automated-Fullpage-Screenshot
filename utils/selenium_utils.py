from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import os
import logging
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import math
import base64

# Clear previous logs
if os.path.exists('error_logs.txt'):
    open('error_logs.txt', 'w').close()

logging.basicConfig(
    filename='error_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_chrome_version(chrome_path):
    """Get Chrome version from the executable"""
    import subprocess
    try:
        # Different command format for Windows
        escaped_path = chrome_path.replace('\\', '\\\\')
        cmd = 'wmic datafile where name="' + escaped_path + '" get Version /value'
        output = subprocess.check_output(cmd, shell=True)
        version = output.decode().strip().split('=')[-1].split('.')[0]  # Get major version
        return version
    except Exception as e:
        logging.error(f"Error getting Chrome version: {str(e)}")
        return None

def setup_driver():
    """Setup Chrome driver with optimized settings for performance and reliability"""
    try:
        print("\n🔍 Setting up Chrome WebDriver...")
        
        options = Options()
        
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-background-networking')
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        options.add_argument('--disable-dev-tools')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-site-isolation-trials')
        options.page_load_strategy = 'eager'
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.password_manager_enabled': False,
            'profile.managed_default_content_settings.images': 1,
            'profile.default_content_setting_values.cookies': 1,
            'disk-cache-size': 4096,
            'network.http.pipelining': True,
            'network.http.proxy.pipelining': True,
            'network.http.max-connections-per-server': 8
        })
        
        print("🔧 Setting up ChromeDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(5)
        
        driver.execute_cdp_cmd('Network.enable', {
            'maxTotalBufferSize': 100000000,
            'maxResourceBufferSize': 100000000
        })
        
        driver.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
        
        print("✅ Chrome WebDriver setup complete!\n")
        return driver
    except Exception as e:
        logging.error(f"Error setting up driver: {str(e)}")
        raise

def load_cookies(driver, cookies_path):
    """Load cookies with optimized domain handling"""
    try:
        if not os.path.exists(cookies_path):
            logging.warning(f"Cookies file not found: {cookies_path}")
            return
            
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
            
        if not isinstance(cookies, list):
            raise ValueError("Invalid cookies format")

        # Get unique domains from cookies
        domains = {cookie.get('domain', '').lstrip('.') for cookie in cookies if cookie.get('domain')}
        
        # Set shorter timeout for cookie operations
        original_timeout = driver.timeouts.page_load
        driver.set_page_load_timeout(15)  # Reduced timeout for cookie operations
        
        for domain in domains:
            if domain:
                print(f"🌐 Setting up cookies for: {domain}")
                try:
                    # Use CDP to set cookies directly without navigation
                    domain_cookies = [c for c in cookies if c.get('domain', '').endswith(domain)]
                    
                    # Batch cookie setting
                    for cookie in domain_cookies:
                        try:
                            cookie_dict = {
                                'name': cookie.get('name'),
                                'value': cookie.get('value'),
                                'domain': cookie.get('domain'),
                                'path': cookie.get('path', '/'),
                                'secure': cookie.get('secure', False),
                                'httpOnly': cookie.get('httpOnly', False)
                            }
                            
                            if 'expirationDate' in cookie:
                                cookie_dict['expiry'] = int(cookie['expirationDate'])
                            
                            # Use CDP to set cookie
                            driver.execute_cdp_cmd('Network.setCookie', cookie_dict)
                            
                        except Exception as e:
                            print(f"⚠️ Error adding cookie {cookie.get('name', 'unknown')}: {str(e)}")
                            continue
                    
                    # Quick validation
                    cookies_added = driver.get_cookies()
                    if cookies_added:
                        print(f"✅ Added {len(cookies_added)} cookies for {domain}")
                    
                except Exception as e:
                    print(f"⚠️ Error setting up cookies for {domain}: {str(e)}")
                    continue
        
        # Restore original timeout
        driver.set_page_load_timeout(original_timeout)
        print("✅ Cookie setup completed")
        logging.info("Cookie setup completed")
    except Exception as e:
        error_msg = f"Error loading cookies: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(error_msg)
        raise

def capture_full_page_screenshot(driver, url, output_path):
    """Enhanced full-page screenshot capture with reliable height calculation"""
    try:
        print(f"🌐 Navigating to URL: {url}")
        logging.info(f"Navigating to URL: {url}")
        driver.get(url)
        
        print("⏳ Waiting for page load...")
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            print("✅ Page loaded successfully")
            logging.info("Page loaded successfully")
        except TimeoutException as e:
            logging.error(f"Timeout while waiting for page to load: {url}", exc_info=True)
            logging.info(f"Page title: {driver.title}")
            logging.info(f"Current URL: {driver.current_url}")
            raise
        
        # Wait for any dynamic content (reverted to static)
        print(f"⏳ Applying delay for dynamic content: 2.0s")
        time.sleep(2.0)
        
        # --- Start Conditional Screenshot Logic ---
        MAX_DIRECT_SCREENSHOT_HEIGHT = 50000 # Threshold for using simpler screenshot method

        # Get preliminary page dimensions to decide screenshot strategy
        preliminary_height_script = "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight, document.documentElement.offsetHeight);"
        preliminary_height = driver.execute_script(preliminary_height_script)
        preliminary_width_script = "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, document.body.offsetWidth, document.documentElement.offsetWidth);"
        preliminary_width = driver.execute_script(preliminary_width_script)

        logging.info(f"Preliminary page dimensions: Width={preliminary_width}, Height={preliminary_height}")

        if preliminary_height > 0 and preliminary_height <= MAX_DIRECT_SCREENSHOT_HEIGHT:
            logging.info(f"Page height ({preliminary_height}px) is within direct screenshot limit. Attempting simpler capture.")
            print(f"📏 Page height ({preliminary_height}px) allows for simpler screenshot method.")
            
            # Prepare page (minimal version for direct screenshot)
            driver.execute_script("""
                document.querySelectorAll('img[loading="lazy"]').forEach(img => {{
                    img.loading = 'eager';
                    img.src = img.src;
                }});
                window.scrollTo(0, 0); // Ensure we are at the top
            """)
            time.sleep(1.0) # Allow lazy images to load and scroll to take effect

            # Ensure full height is captured by setting window size appropriately
            # Use a slightly larger height to be safe, but based on actual content
            capture_width = preliminary_width + 100
            capture_height = preliminary_height + 100 
            print(f"📐 Setting window size for direct capture: {capture_width}x{capture_height}")
            driver.set_window_size(capture_width, capture_height)
            time.sleep(1.5) # Allow repaint and settle after resize

            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                body.screenshot(output_path)
                logging.info("Screenshot captured using body element method (direct path).")
                print("✅ Captured using direct body screenshot.")
            except Exception as e_body_direct:
                logging.warning(f"Direct body capture failed: {e_body_direct}. Falling back to driver.save_screenshot.")
                driver.save_screenshot(output_path)
                logging.info("Screenshot captured using driver.save_screenshot (direct path fallback).")
                print("✅ Captured using direct driver.save_screenshot (fallback).")
        else:
            if preliminary_height == 0:
                logging.warning(f"Preliminary height is 0 for {url}. Proceeding with CDP method as a fallback.")
            logging.info(f"Page height ({preliminary_height}px) exceeds direct limit or is zero. Using robust CDP method.")
            print(f"📏 Page height ({preliminary_height}px) requires robust CDP screenshot method.")

            # --- Robust CDP Path (for very long pages) ---
            print("📏 Preparing page layout for CDP...")
            logging.info("Preparing page layout for CDP screenshot")
            driver.execute_script(""" 
                document.querySelectorAll('img[loading="lazy"]').forEach(img => {{
                img.loading = 'eager';
                img.src = img.src;
                }});
            """)
            time.sleep(1.0) # delay for layout changes

            # Set viewport for layout using MAX_VIEWPORT_HEIGHT_FOR_LAYOUT (user setting)
            MAX_VIEWPORT_HEIGHT_FOR_LAYOUT = 45000 
            layout_viewport_height = min(preliminary_height if preliminary_height > 0 else MAX_VIEWPORT_HEIGHT_FOR_LAYOUT, MAX_VIEWPORT_HEIGHT_FOR_LAYOUT)
            layout_viewport_width = preliminary_width if preliminary_width > 0 else 1920

            print(f"📐 Setting viewport for layout (CDP path): {layout_viewport_width + 100}x{layout_viewport_height + 100} pixels")
            driver.set_window_size(layout_viewport_width + 100, layout_viewport_height + 100)
            time.sleep(1.0) # resize delay
            
            print("🖱️ Loading all content by scrolling (CDP path)...")
            driver.execute_script("""
                const scrollableHeight = document.body.scrollHeight || document.documentElement.scrollHeight;
                const viewportHeight = window.innerHeight;
                const steps = Math.ceil(scrollableHeight / viewportHeight);
                for (let i = 0; i <= steps; i++) {{
                    setTimeout(() => {{
                        window.scrollTo(0, i * viewportHeight);
                    }}, i * 150);
                }}
                setTimeout(() => window.scrollTo(0, 0), (steps + 1) * 150 + 200);
            """)
            
            scroll_steps_js = "return Math.ceil((document.body.scrollHeight || document.documentElement.scrollHeight) / window.innerHeight);"
            num_scroll_steps = driver.execute_script(scroll_steps_js)
            estimated_scroll_duration = (num_scroll_steps + 1) * 0.150 + 0.200
            settle_time = 3.0
            total_wait_for_scroll_and_settle = estimated_scroll_duration + settle_time
            print(f"⏳ Applying delay for scrolling completion and page settling (CDP path): {total_wait_for_scroll_and_settle:.2f}s")
            time.sleep(total_wait_for_scroll_and_settle)
            
            print("📸 Capturing screenshot using CDP Page.captureScreenshot...")
            metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
            content_width = math.ceil(metrics['contentSize']['width'])
            
            # New JavaScript to find the bottom-most visible element's position
            final_content_height_script = """
                const BORDERLINE_NODE_TYPES = [
                    Node.COMMENT_NODE, 
                    Node.PROCESSING_INSTRUCTION_NODE, 
                    Node.DOCUMENT_TYPE_NODE
                ];
                let allElements = Array.from(document.body.querySelectorAll(
                    '*:not(script):not(style):not(noscript):not(meta):not(link):not(title)'
                ));
                let maxY = 0;

                // Include body itself as a baseline, especially for pages with direct body styling or minimal content
                if (document.body && (document.body.offsetHeight > 0 || document.body.offsetWidth > 0 || (typeof document.body.getClientRects === 'function' && document.body.getClientRects().length > 0))) {
                  let bodyRect = document.body.getBoundingClientRect();
                  maxY = Math.max(maxY, bodyRect.bottom + window.pageYOffset);
                }

                allElements.forEach(el => {
                  if (el && typeof el.getBoundingClientRect === 'function' && !BORDERLINE_NODE_TYPES.includes(el.nodeType)) {
                    let elStyle = window.getComputedStyle(el);
                    if (elStyle.display !== 'none' && elStyle.visibility !== 'hidden' && parseFloat(elStyle.opacity) > 0) {
                        let rect = el.getBoundingClientRect();
                        if (rect.width > 0 || rect.height > 0 || (typeof el.getClientRects === 'function' && el.getClientRects().length > 0)) {
                             let elementBottom = rect.bottom + window.pageYOffset;
                             if (elementBottom > maxY) {
                                maxY = elementBottom;
                             }
                        }
                    }
                  }
                });
                // If no elements found or maxY is still 0, fallback to scrollHeight as a last resort.
                if (maxY === 0) {
                    maxY = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
                }
                return Math.ceil(maxY) + 50; // Add 50px buffer for safety (e.g., shadows, margins)
            """
            content_height = driver.execute_script(final_content_height_script)

            if content_width == 0: content_width = layout_viewport_width
            if content_height == 0: content_height = 600
            print(f" CDP Full Page Dimensions: Width={content_width}, Height={content_height}")
            screenshot_config = {
                'format': 'png',
                'captureBeyondViewport': True,
                'clip': {
                    'x': 0,
                    'y': 0,
                    'width': content_width,
                    'height': content_height,
                    'scale': 1
                }
            }
            try:
                res = driver.execute_cdp_cmd('Page.captureScreenshot', screenshot_config)
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(res['data']))
                print("✅ Captured using CDP Page.captureScreenshot")
                logging.info("Screenshot captured using CDP Page.captureScreenshot")
            except Exception as e_cdp:
                logging.warning(f"CDP Page.captureScreenshot failed: {str(e_cdp)}. Falling back to body/save_screenshot.")
                # Fallback mechanism if CDP Page.captureScreenshot fails
                try:
                    body = driver.find_element(By.TAG_NAME, 'body')
                    body.screenshot(output_path)
                    print("✅ Captured using body element method (CDP direct fallback)")
                    logging.info("Screenshot captured using body element method (CDP direct fallback)")
                except Exception as e_body_cdp_fallback:
                    logging.warning(f"Body capture failed (CDP direct fallback), using driver.save_screenshot: {str(e_body_cdp_fallback)}")
                    driver.save_screenshot(output_path)
                    print("✅ Captured using driver.save_screenshot (CDP ultimate fallback)")
                    logging.info("Screenshot captured using driver.save_screenshot (CDP ultimate fallback)")
        # --- End Conditional Screenshot Logic ---
        
        page_title = driver.title
        print(f"✅ Screenshot captured successfully: {page_title}")
        logging.info(f"Screenshot captured successfully for {url}")
        return page_title
        
    except Exception as e:
        error_msg = f"❌ Screenshot capture failed for {url}: {str(e)}"
        print(error_msg)
        logging.error(error_msg, exc_info=True)
        raise

def close_driver(driver):
    """Safely close the driver with validation"""
    try:
        if driver and hasattr(driver, 'quit'):
            driver.quit()
            logging.info("Driver closed successfully")
    except Exception as e:
        logging.error(f"Error closing driver: {str(e)}")
