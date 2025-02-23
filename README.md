# Selenium Automated Full-page Screenshot

A robust Python automation tool that captures full-page screenshots of web pages, with special handling for dynamic content and lazy-loaded elements. Built with Selenium WebDriver and optimized for reliability.

## Key Features

- **Reliable Full-page Screenshots**
  - Handles dynamic content and lazy-loaded images
  - Optimized layout calculations for accurate dimensions
  - Multiple fallback capture methods
  - Smart scroll handling for content loading

- **Performance Optimizations**
  - Headless Chrome with optimized flags
  - Network and resource handling optimizations
  - Efficient memory management
  - Smart timeouts and wait conditions

- **Robust Error Handling**
  - Comprehensive exception management
  - Detailed logging system
  - Multiple retry mechanisms
  - Validation at critical points

## Installation

1. **Prerequisites**
   ```bash
   # Required
   - Python 3.7+
   - Google Chrome browser
   ```

2. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/selenium-automated-fullpage-screenshot.git
   cd selenium-automated-fullpage-screenshot
   pip install -r requirements.txt
   ```

2.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    Create a `.env` file in the project's root directory and add the following variables:

    ```
    SPREADSHEET_ID=<your_google_sheet_id>
    FOLDER_ID=<your_google_drive_folder_id>
    URL_RANGE=<range_containing_urls>  # e.g., 'Sheet1!A2:A'
    CHROME_PATH=<optional_path_to_chrome_executable>
    ```

    Replace the placeholders with your actual values.  The `CHROME_PATH` is optional, but can be used to specify a specific Chrome installation.  The script will attempt to auto-detect Chrome if this is not provided.

5.  **Place `cookies.json`:**

    If you need to access websites that require login, create a `cookies.json` file in the project's root directory containing the necessary cookies.  The format of this file should be a JSON array of cookie objects, as shown in the provided `cookies.json` example.

6. **Share Google Drive Folder and Google Sheet:**
    * Share the Google Drive folder with the service account email address (found in `credentials.json`). Give the service account "Editor" access.
    * Share the Google Sheet with the service account email address. Give the service account "Editor" access.
3. **Environment Setup**
   Create a `.env` file:
   ```env
   CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
   SCREENSHOTS_DIR=screenshots
   ```

## Usage

```python
from utils.selenium_utils import setup_driver, capture_full_page_screenshot, close_driver

# Initialize driver
driver = setup_driver()

try:
    # Capture screenshot
    page_title = capture_full_page_screenshot(
        driver=driver,
        url="https://example.com",
        output_path="screenshots/example.png"
    )
    print(f"Captured: {page_title}")
finally:
    close_driver(driver)
```

## Technical Details

### Screenshot Capture Process

1. **Page Preparation**
   - Table-based layout optimization
   - Lazy image loading handling
   - Fixed element management

2. **Dimension Calculation**
   - Multiple viewport metrics
   - Padding for safety margins
   - Dynamic content consideration

3. **Content Loading**
   - Progressive scrolling
   - Dynamic wait calculations
   - Element visibility checks

### Browser Configuration

```python
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
# ... additional optimizations
```

## Project Structure

```
selenium-automated-fullpage-screenshot/
├── utils/
│   ├── selenium_utils.py    # Core screenshot functionality
│   └── __init__.py
├── screenshots/             # Output directory
├── .env                    # Environment configuration
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## Dependencies

```
selenium==4.10.0
python-dotenv==1.0.0
webdriver_manager
```
m
## Error Handling

The tool includes comprehensive error handling for common scenarios:
- Network issues
- Dynamic content loading failures
- Browser compatibility problems
- Resource limitations

## Logging

Detailed logging is available in `error_logs.txt`:
- Operation timestamps
- Error tracebacks
- Performance metrics
- Status updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Selenium WebDriver team
- Chrome DevTools Protocol documentation
- WebDriver Manager project