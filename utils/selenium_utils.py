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
        
        # Wait for any dynamic content
        time.sleep(2)
        
        # Prepare page layout
        print("📏 Preparing page layout...")
        logging.info("Preparing page layout for screenshot")
        driver.execute_script("""
            // Set up the page for proper height calculation
            document.documentElement.style.display = 'table';
            document.documentElement.style.width = '100%';
            document.body.style.display = 'table-row';
            
            // Force load lazy images
            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                img.loading = 'eager';
                img.src = img.src;
            });
            
            // Show collapsed elements and handle fixed positioning
            document.querySelectorAll('.collapse').forEach(el => el.classList.add('show'));
            document.querySelectorAll('*[style*="position: fixed"]').forEach(el => {
                if (!el.classList.contains('navigation-bar')) {
                    el.style.position = 'absolute';
                }
            });
        """)
        
        # Wait for layout changes
        time.sleep(1)
        
        # Get page dimensions
        dimensions = driver.execute_script("""
            return {
                width: Math.max(
                    document.documentElement.scrollWidth,
                    document.documentElement.offsetWidth,
                    document.body.scrollWidth,
                    document.body.offsetWidth
                ) + 100,
                height: Math.max(
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight,
                    document.body.scrollHeight,
                    document.body.offsetHeight
                ) + 100
            };
        """)
        
        print(f"📐 Setting viewport size: {dimensions['width']}x{dimensions['height']} pixels")
        logging.info(f"Setting viewport size: {dimensions['width']}x{dimensions['height']} pixels")
        driver.set_window_size(dimensions['width'], dimensions['height'])
        
        # Wait for resize
        time.sleep(1)
        
        # Scroll through the page to trigger lazy loading
        print("🖱️ Loading all content...")
        logging.info("Scrolling through the page to load all content")
        driver.execute_script("""
            const height = document.documentElement.scrollHeight;
            const steps = Math.ceil(height / 1000);
            const stepSize = height / steps;
            
            // Synchronous scrolling with setTimeout
            for (let i = 0; i <= steps; i++) {
                setTimeout(() => {
                    window.scrollTo(0, i * stepSize);
                }, i * 100);
            }
            setTimeout(() => window.scrollTo(0, 0), (steps + 1) * 100);
        """)
        
        # Wait for scrolling to complete
        time.sleep((math.ceil(driver.execute_script("return document.documentElement.scrollHeight") / 1000) + 1) * 0.1 + 1)
        
        print("📸 Capturing screenshot...")
        logging.info("Capturing screenshot")
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            body.screenshot(output_path)
            print("✅ Captured using body element method")
            logging.info("Screenshot captured using body element method")
        except Exception as e:
            logging.warning(f"Body capture failed, using full page method: {str(e)}")
            driver.save_screenshot(output_path)
            print("✅ Captured using full page method")
            logging.info("Screenshot captured using full page method")
        
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
