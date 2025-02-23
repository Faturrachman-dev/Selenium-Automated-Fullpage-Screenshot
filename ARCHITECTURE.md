# Selenium Automated Full-page Screenshot

A robust Python application for automated full-page screenshot capture with Google Drive integration.

## Project Architecture

### Directory Structure
```
selenium-automated-fullpage-screenshot/
├── docs/
│   └── ARCHITECTURE.md
├── utils/
│   └── selenium_utils.py
├── main.py
├── requirements.txt
├── .env
├── cookies.json
├── credentials.json
├── error_logs.txt
└── README.md
```

## Core Components

### 1. Selenium WebDriver Management (`utils/selenium_utils.py`)

#### Key Functions:

##### `setup_driver()`
- Initializes Chrome WebDriver with optimized settings
- Configures headless mode and performance optimizations
- Sets up network conditions and browser preferences

##### `capture_full_page_screenshot(driver, url, output_path)`
- Captures full-page screenshots with reliable height calculation
- Handles dynamic content and lazy loading
- Uses multiple fallback methods for screenshot capture
- Key stages:
  1. Page load and validation
  2. Layout preparation
  3. Dimension calculation
  4. Content loading through scrolling
  5. Screenshot capture

##### `load_cookies(driver, cookies_path)`
- Manages cookie injection for authenticated sessions
- Handles domain-specific cookie setup
- Provides batch cookie operations

##### `close_driver(driver)`
- Safely terminates WebDriver instance
- Includes validation and error handling

### 2. Configuration Files

#### `.env`
Contains environment variables:
```
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
SPREADSHEET_ID=your_spreadsheet_id
```

#### `credentials.json`
Google API credentials for:
- Google Drive API
- Google Sheets API

#### `cookies.json`
- Stores authentication cookies
- Format: Array of cookie objects with domain, name, value, etc.

### 3. Logging System

#### `error_logs.txt`
- Comprehensive logging of operations
- Includes timestamps and error tracebacks
- Log levels: INFO, WARNING, ERROR

## Technical Implementation Details

### Screenshot Capture Process

1. **Page Preparation**
```javascript
// Layout optimization
document.documentElement.style.display = 'table';
document.documentElement.style.width = '100%';
document.body.style.display = 'table-row';

// Image loading optimization
document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    img.loading = 'eager';
    img.src = img.src;
});
```

2. **Dimension Calculation**
```javascript
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
```

3. **Content Loading**
```javascript
const height = document.documentElement.scrollHeight;
const steps = Math.ceil(height / 1000);
const stepSize = height / steps;

// Synchronous scrolling with setTimeout
for (let i = 0; i <= steps; i++) {
    setTimeout(() => {
        window.scrollTo(0, i * stepSize);
    }, i * 100);
}
```

### Browser Configuration

#### Performance Optimizations
```python
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
# ... additional optimizations
```

#### Network Settings
```python
options.add_experimental_option('prefs', {
    'disk-cache-size': 4096,
    'network.http.pipelining': True,
    'network.http.max-connections-per-server': 8
})
```

## Integration Points

### 1. Google Drive Integration
- Uploads screenshots to specified folder
- Uses service account authentication
- Handles file naming and duplicates

### 2. Google Sheets Integration
- Reads URLs from specified spreadsheet
- Updates processing status
- Maintains execution logs

## Error Handling

### Retry Mechanism
- Multiple attempts for screenshot capture
- Exponential backoff for retries
- Detailed error logging

### Exception Handling
```python
try:
    # Operation code
except Exception as e:
    logging.error(f"Operation failed: {str(e)}", exc_info=True)
    # Fallback or recovery code
```

## Best Practices

### 1. Screenshot Capture
- Wait for page load completion
- Handle dynamic content loading
- Account for lazy-loaded images
- Manage fixed position elements

### 2. Resource Management
- Proper driver cleanup
- Memory optimization
- Network resource handling

### 3. Error Recovery
- Graceful degradation
- Multiple fallback methods
- Comprehensive error logging

## Dependencies

Key dependencies from `requirements.txt`:
```
selenium==4.10.0
google-api-python-client==2.92.0
google-auth==2.23.0
python-dotenv==1.0.0
webdriver_manager
```

## Future Improvements

1. **Performance Optimization**
   - Parallel processing for multiple URLs
   - Improved caching mechanisms
   - Network optimization

2. **Feature Additions**
   - Additional screenshot formats
   - Custom viewport sizes
   - Advanced authentication methods

3. **Monitoring & Logging**
   - Performance metrics collection
   - Advanced error tracking
   - Real-time status updates

## Troubleshooting

Common issues and solutions:

1. **Screenshot Capture Failures**
   - Check page load completion
   - Verify dimension calculations
   - Ensure proper scroll handling

2. **Authentication Issues**
   - Validate cookie format
   - Check credential permissions
   - Verify API access

3. **Performance Issues**
   - Monitor memory usage
   - Check network conditions
   - Verify browser configuration

## Contributing

Guidelines for contributing to the project:

1. Follow existing code structure
2. Maintain comprehensive error handling
3. Update documentation for changes
4. Add tests for new features

---

*This documentation is maintained by the project team. Last updated: February 2025* 