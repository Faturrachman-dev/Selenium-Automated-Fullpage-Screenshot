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

## Installation

1.  **Prerequisites**
    ```bash
    # Required
    - Python 3.7+
    - Google Chrome browser
    ```

2.  **Clone and Setup**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Create a `.env` file in the project's root directory and add the following variables:

    ```
    SPREADSHEET_ID=<your_google_sheet_id>
    FOLDER_ID=<your_google_drive_folder_id>
    URL_RANGE=<range_containing_urls>  # e.g., 'Sheet1!A2:A'
    CHROME_PATH=<optional_path_to_chrome_executable>
    COOKIES_PATH=cookies.json # Path to cookies.json
    ```

    Replace the placeholders with your actual values.  The `CHROME_PATH` is optional, but can be used to specify a specific Chrome installation.  The script will attempt to auto-detect Chrome if this is not provided.

4.  **Place `cookies.json`:**

    If you need to access websites that require login, create a `cookies.json` file in the project's root directory containing the necessary cookies.  The format of this file should be a JSON array of cookie objects.

    **How to get `cookies.json`:**

    1.  Install a cookie editor extension in your Chrome browser (e.g., "Cookie Editor").
    2.  Log in to the website you need to take screenshots of.
    3.  Open the cookie editor extension.
    4.  Export the cookies in JSON format and save the file as `cookies.json` in the project's root directory.

5.  **Place `credentials.json`:**

    You need to set up Google Cloud Project to get the `credentials.json` file.

    **How to get `credentials.json`:**

    1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
    2.  Create a new project or select an existing one.
    3.  Enable the **Google Drive API** and **Google Sheets API** for your project.
    4.  Go to "Credentials" in the left sidebar.
    5.  Click "Create Credentials" and choose "Service account".
    6.  Give your service account a name and click "Create and Continue".
    7.  Grant your service account the "Editor" role under "Grant this service account access to project (optional)" and click "Continue".
    8.  Click "Done".
    9.  Click on the service account email address you just created.
    10. Go to the "Keys" tab.
    11. Click "Add Key" and choose "Create new key".
    12. Select JSON as the key type and click "Create".
    13. Download the `credentials.json` file and place it in the project's root directory.

6.  **Share Google Drive Folder and Google Sheet:**
    *   Share the Google Drive folder with the service account email address (found in `credentials.json`). Give the service account "Editor" access.
    *   Share the Google Sheet with the service account email address. Give the service account "Editor" access.

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.