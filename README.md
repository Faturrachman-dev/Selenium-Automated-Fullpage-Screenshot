# Automated Full-Page Screenshot Capture, Upload, and Metadata Recording

This project automates the process of capturing full-page screenshots of web pages, uploading them to Google Drive, and updating a Google Sheet with relevant metadata. It leverages Selenium for web automation, Google Drive API for file storage, and Google Sheets API for data management. The project emphasizes robust error handling, performance optimization, and maintainability.

## Features

*   **Full-Page Screenshot Capture:** Captures entire web pages, including content below the fold, using Selenium and optimized techniques for handling dynamic content and lazy-loaded images.
*   **Google Drive Integration:** Uploads screenshots to a specified Google Drive folder using the Google Drive API (v3).  Handles authentication via service account credentials.  Includes robust error handling, retries, and duplicate file management.
*   **Google Sheets Integration:** Reads URLs from a Google Sheet and updates corresponding cells with screenshot metadata (file ID, web view link) using the Google Sheets API (v4).  Authenticates using service account credentials.
*   **Cookie Management:** Loads cookies from a `cookies.json` file to maintain session state and handle authentication for websites requiring login.  Uses optimized domain handling and the Chrome DevTools Protocol (CDP) for efficient cookie setting.
*   **Performance Optimization:** Employs various techniques to enhance performance, including:
    *   Headless Chrome WebDriver.
    *   Optimized WebDriver flags (disabling GPU, software rasterization, etc.).
    *   Eager page load strategy.
    *   Network and caching optimizations.
    *   Optimized timeouts.
    *   Resumable uploads with optimized chunk sizes for Google Drive.
    *   Batch operations where possible.
*   **Robust Error Handling:** Includes comprehensive error handling and logging throughout the process, with specific checks for common issues (e.g., Google API permission errors, network issues, invalid URLs).
*   **Duplicate File Handling:** Checks for existing files with the same name in the target Google Drive folder and deletes them before uploading to prevent duplicates.
*   **URL Tracking (Conceptual):** Includes a `URLTracker` class (not fully integrated in `main.py`) designed to manage processed URLs and their metadata, preventing redundant processing.
*   **Detailed Logging:** Records events, errors, and progress to a log file (`error_logs.txt`) for debugging and monitoring.
*   **Dynamic Chrome Version Handling:** Dynamically detects the installed Chrome browser's version for WebDriver compatibility.
*   **Multiple Screenshot Capture Methods:** Implements fallback mechanisms for screenshot capture, including capturing the `body` element, using Selenium's `save_screenshot`, and a JavaScript-based canvas capture method.
*   **Progress Reporting:** Provides detailed progress reporting during Google Drive uploads, including percentage completion, upload speed, and estimated time remaining.

## Project Structure

The project is organized into the following modules:

*   `main.py`: The main script that orchestrates the entire process.
*   `utils/`:
    *   `selenium_utils.py`: Contains functions for setting up the Selenium WebDriver, loading cookies, and capturing screenshots.
    *   `gdrive_utils.py`: Handles interactions with the Google Drive API, including authentication, file uploads, and metadata retrieval.
    *   `gsheet_utils.py`: Manages interactions with the Google Sheets API, including reading URLs and updating cell values.
    *   `url_tracker.py`: (Conceptual) Provides a class for tracking processed URLs and their metadata.
*   `credentials.json`: Contains service account credentials for Google API authentication.
*   `cookies.json`: Stores cookies for maintaining session state.
*   `.env`: Stores environment variables, such as the Google Sheet ID, folder ID, and URL range.
*   `error_logs.txt`: Log file for recording errors and events.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.7+
    *   Google Chrome browser
    *   A Google Cloud Platform project with the following APIs enabled:
        *   Google Drive API
        *   Google Sheets API
    *   A service account with access to the Google Drive and Google Sheets APIs. Download the service account credentials as `credentials.json` and place it in the project's root directory.
    *   A Google Sheet containing a list of URLs to process.
    *   A Google Drive folder where screenshots will be uploaded.

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

## Usage

1.  **Ensure your Google Sheet is populated with URLs in the specified range.**

2.  **Run the `main.py` script:**

    ```bash
    python main.py
    ```

The script will read URLs from the Google Sheet, capture screenshots, upload them to Google Drive, and update the sheet with the screenshot links. Progress and errors will be logged to the console and the `error_logs.txt` file.

## Troubleshooting

*   **Service account lacks necessary permissions:** If you encounter a 403 error, ensure that the Google Drive folder and Google Sheet are shared with the service account email address (found in `credentials.json`) with "Editor" permissions.
*   **Folder not found or not accessible:** Verify the `FOLDER_ID` in your `.env` file is correct and that the service account has access to the folder.
*   **Chrome browser not found:** If the script cannot find Chrome, either install it in a standard location or specify the path to the Chrome executable using the `CHROME_PATH` environment variable.
*   **Invalid cookies format:** Ensure that the `cookies.json` file is correctly formatted as a JSON array of cookie objects.
*   **Other errors:** Check the `error_logs.txt` file for detailed error messages and debugging information.

## Future Improvements

*   **Full Integration of `URLTracker`:** Integrate the `URLTracker` class into `main.py` to prevent reprocessing of URLs.
*   **Asynchronous Processing:** Implement asynchronous processing (e.g., using `asyncio`) to improve performance, especially when handling a large number of URLs.
*   **Configurable Screenshot Options:** Allow users to configure screenshot options (e.g., image format, quality) via command-line arguments or a configuration file.
*   **More Flexible Cookie Handling:** Implement more flexible cookie handling, such as allowing users to specify cookies via command-line arguments or a configuration file.
*   **GUI:** Develop a graphical user interface (GUI) to make the tool more user-friendly.
*   **Testing:** Add unit and integration tests to improve code quality and maintainability.
*   **Dockerization:** Containerize the application using Docker for easier deployment and portability.

## Contributing

Contributions are welcome! Please submit pull requests or open issues to discuss proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.