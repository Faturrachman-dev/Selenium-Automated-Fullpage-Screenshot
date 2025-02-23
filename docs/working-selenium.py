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
        # Check if Chrome is installed
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"F:\Program Files\Chrome\chrome.exe",
            os.environ.get("CHROME_PATH")
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if path and os.path.exists(path):
                chrome_path = path
                print(f"✅ Chrome found at: {path}")
                logging.info(f"Chrome found at: {path}")
                break
                
        if not chrome_path:
            raise Exception("Chrome browser not found. Please install Google Chrome and try again.")

        options = Options()
        
        # Essential flags for headless operation
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Performance optimization flags
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        
        # Network optimization flags
        options.add_argument('--dns-prefetch-disable')  # Disable DNS prefetching
        options.add_argument('--disable-background-networking')  # Disable background network tasks
        options.add_argument('--proxy-server="direct://"')  # Direct connection
        options.add_argument('--proxy-bypass-list=*')  # Bypass proxy for all hosts
        
        # Memory optimization
        options.add_argument('--disable-dev-tools')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-site-isolation-trials')
        
        # Set reasonable page load strategy
        options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        # Additional preferences for better performance
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.password_manager_enabled': False,
            'profile.managed_default_content_settings.images': 1,  # Load images but optimize
            'profile.default_content_setting_values.cookies': 1,
            'disk-cache-size': 4096,
            'network.http.pipelining': True,
            'network.http.proxy.pipelining': True,
            'network.http.max-connections-per-server': 8
        })
        
        print("🔧 Setting up ChromeDriver...")
        driver = webdriver.Chrome(options=options)
        
        # Configure optimized timeouts
        driver.set_page_load_timeout(20)  # Reduced from 30
        driver.implicitly_wait(5)  # Reduced from 10
        
        # Enable performance logging
        driver.execute_cdp_cmd('Network.enable', {
            'maxTotalBufferSize': 100000000,
            'maxResourceBufferSize': 100000000
        })
        
        # Enable request interception for optimization
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
        driver.get(url)
        
        print("⏳ Waiting for page load...")
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        print("✅ Page loaded successfully")
        
        # Prepare page for screenshot by modifying layout
        print("📏 Preparing page layout...")
        driver.execute_script("""
            // Set up the page for proper height calculation
            document.documentElement.style.display = 'table';
            document.documentElement.style.width = '100%';
            document.body.style.display = 'table-row';
            
            // Force all images to load
            const images = document.getElementsByTagName('img');
            for(let img of images) {
                if(img.loading === 'lazy') {
                    img.loading = 'eager';
                    img.src = img.src;
                }
            }
            
            // Show all collapsed elements
            const collapsedElements = document.querySelectorAll('.collapse');
            collapsedElements.forEach(el => el.classList.add('show'));
            
            // Handle fixed elements except navigation
            const fixedElements = document.querySelectorAll('*[style*="position: fixed"]');
            fixedElements.forEach(el => {
                if (!el.classList.contains('navigation-bar')) {
                    el.style.position = 'absolute';
                }
            });
        """)
        
        # Wait for layout changes to take effect
        time.sleep(1)
        
        # Get accurate page dimensions
        dimensions = driver.execute_script("""
            return {
                height: Math.max(
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight,
                    document.documentElement.clientHeight,
                    document.body.scrollHeight,
                    document.body.offsetHeight,
                    document.body.clientHeight
                ),
                width: Math.max(
                    document.documentElement.scrollWidth,
                    document.documentElement.offsetWidth,
                    document.documentElement.clientWidth,
                    document.body.scrollWidth,
                    document.body.offsetWidth,
                    document.body.clientWidth
                )
            };
        """)
        
        # Add padding to dimensions
        total_width = dimensions['width'] + 100
        total_height = dimensions['height'] + 100
        
        print(f"📐 Setting viewport size: {total_width}x{total_height} pixels")
        driver.set_window_size(total_width, total_height)
        
        # Wait for resize to take effect
        time.sleep(1)
        
        # Scroll through the page to trigger lazy loading
        print("🖱️ Loading all content...")
        driver.execute_script("""
            const height = document.documentElement.scrollHeight;
            const steps = Math.ceil(height / 1000); // One step per 1000px
            const stepSize = height / steps;
            
            for(let i = 0; i <= steps; i++) {
                window.scrollTo(0, i * stepSize);
                // Small pause between scrolls
                new Promise(resolve => setTimeout(resolve, 100));
            }
            window.scrollTo(0, 0);
        """)
        
        # Final wait for any dynamic content
        time.sleep(1)
        
        print("📸 Capturing screenshot...")
        try:
            # Try capturing the body element first (most reliable method)
            body = driver.find_element(By.TAG_NAME, 'body')
            body.screenshot(output_path)
            print("✅ Captured using body element method")
        except Exception as e:
            print(f"⚠️ Body capture failed, trying full page method: {str(e)}")
            try:
                # Fallback to full page screenshot
                driver.save_screenshot(output_path)
                print("✅ Captured using full page method")
            except Exception as e2:
                print(f"⚠️ Full page capture failed, trying alternative method: {str(e2)}")
                # Final fallback using JavaScript
                screenshot = driver.execute_script("""
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    const html = document.documentElement;
                    
                    canvas.width = html.scrollWidth;
                    canvas.height = html.scrollHeight;
                    
                    // Draw the viewport
                    context.drawWindow(window, 0, 0, canvas.width, canvas.height, 'rgb(255,255,255)');
                    
                    return canvas.toDataURL('image/png');
                """)
                
                # Convert base64 to image and save
                import base64
                img_data = base64.b64decode(screenshot.split(',')[1])
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                print("✅ Captured using JavaScript method")
        
        page_title = driver.title
        print(f"✅ Screenshot captured successfully: {page_title}")
        logging.info(f"Screenshot captured successfully for {url}")
        return page_title
        
    except Exception as e:
        print(f"❌ Screenshot capture failed: {str(e)}")
        logging.error(f"Screenshot capture failed for {url}: {str(e)}")
        raise

def close_driver(driver):
    """Safely close the driver with validation"""
    try:
        if driver and hasattr(driver, 'quit'):
            driver.quit()
            logging.info("Driver closed successfully")
    except Exception as e:
        logging.error(f"Error closing driver: {str(e)}")