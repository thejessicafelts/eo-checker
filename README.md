# EO Checker

EO Checker is a Python utility that retrieves new executive orders from the Federal Register API, records key metadata to a CSV file, and then downloads and converts each order’s full-text XML into a plain text file. The conversion process extracts all text content and writes each text fragment on a new line, without any XML wrappers. Additionally, the project maintains a record of the last publication date processed so that subsequent runs only retrieve newer executive orders.

## Features

- **Fetch Executive Orders:** Uses the Federal Register API to fetch all executive orders signed by Donald Trump (or as configured) published on or after a specified start date.
- **CSV Metadata Logging:** Extracts and flattens key order fields (such as document number, title, citation, publication date, signing date, URLs, agency names, etc.) and appends them to a CSV file.
- **XML URL Generation:** For each order, automatically generates the URL for the full-text XML document based on its publication date and document number.
- **Plain Text Conversion:** Downloads the XML content, then converts it to plain text by recursively extracting text from each element. Each text fragment is written on its own new line.
- **Incremental Processing:** Maintains a local file storing the latest publication date processed so that subsequent executions fetch only new orders.
- **Simple File Organization:** Saves each order’s plain text output as a separate .txt file (named by the document number) in a designated folder.

## Requirements

- Python 3.6 or higher
- [Requests](https://pypi.org/project/requests/) library

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/thejessicafelts/eo-checker.git
   cd eo-checker
   ```

2. **Install dependencies:**

   If you don't already have the Requests library installed, run:

   ```bash
   pip install requests
   ```

   (All other modules used are part of the Python standard library.)

## Usage

1. **Configuration:**  
   - The script uses a default start date of `2025-01-20`. This can be changed by modifying the `DEFAULT_START_DATE` constant in `eo-checker.py`.
   - The CSV file (`executive_orders.csv`) and the file that stores the last publication date (`last_eo_date.txt`) are created in the project’s root directory.
   - Plain text outputs are saved in the folder `executive_order_txt`. (You can adjust these folder names by modifying the constants in the script.)

2. **Run the script:**

   Simply execute:

   ```bash
   python eo-checker.py
   ```

   The script will:
   - Fetch executive orders published on or after the stored start date.
   - Append the order metadata to the CSV file.
   - For each order, generate the XML URL, download its content, convert it to plain text (with each text segment on a new line), and save it as `[document_number].txt` in the `executive_order_txt` folder.
   - Update the stored last publication date so that the next run only processes new orders.

3. **Scheduling:**  
   You can automate the execution of the script (for example, using cron on Unix-like systems or Task Scheduler on Windows) so that it periodically checks for and processes new executive orders.

## Project Structure

```
eo-checker/
├── eo-checker.py           # Main Python script
├── executive_orders.csv    # CSV file where metadata is recorded (created at runtime)
├── last_eo_date.txt        # File storing the latest publication date processed (created at runtime)
├── executive_order_txt/    # Folder where plain text files are saved (created at runtime)
└── README.md               # This README file
```

## How It Works

1. **Fetching Orders:**  
   The script reads the last processed publication date from `last_eo_date.txt` (or uses the default) and uses that in an API query to the Federal Register API. It retrieves executive orders that match the criteria (e.g., type, presidential document type, and president).

2. **Recording Metadata:**  
   For each fetched order, key details (such as document number, title, publication date, URLs, etc.) are flattened and appended to the CSV file. The script then updates the stored date with the most recent publication date from the orders.

3. **Processing XML:**  
   The publication date and document number are used to generate the full-text XML URL. The script downloads the XML content and then converts it to plain text by recursively extracting text from each element. Each text fragment is placed on a new line, resulting in a file that contains only the textual content.

4. **Saving Output:**  
   The plain text output is saved as a `.txt` file named with the document number (e.g., `2025-02841.txt`) in the folder `executive_order_txt`.

## Contributing

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.