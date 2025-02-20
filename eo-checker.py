#!/usr/bin/env python3
import requests
import csv
import os
import datetime
import xml.etree.ElementTree as ET

# Constants for CSV and tracking file
CSV_FILE = "executive_orders.csv"
LAST_DATE_FILE = "last_eo_date.txt"
DEFAULT_START_DATE = "2025-01-20"
BASE_API_URL = "https://www.federalregister.gov/api/v1/documents.json"

# Define the CSV columns (flattened from the JSON response)
CSV_COLUMNS = [
    "document_number",
    "executive_order_number",
    "title",
    "citation",
    "publication_date",
    "signing_date",
    "pdf_url",
    "html_url",
    "full_text_xml_url",
    "raw_text_url",
    "body_html_url",
    "agency_names",
    "president",
    "page_views_count",
    "toc_doc",
    "toc_subject",
    "subtype",
    "executive_order_notes",
    "disposition_notes"
]

def get_start_date():
    """Read the last recorded publication date from file; if not found, return default."""
    if os.path.exists(LAST_DATE_FILE):
        with open(LAST_DATE_FILE, "r") as f:
            return f.read().strip()
    return DEFAULT_START_DATE

def set_start_date(new_date_str):
    """Save the new start date to file."""
    with open(LAST_DATE_FILE, "w") as f:
        f.write(new_date_str)

def load_processed_document_numbers():
    """Return a set of document numbers already recorded in CSV_FILE (if it exists)."""
    processed = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                doc_num = row.get("document_number")
                if doc_num:
                    processed.add(doc_num)
    return processed

def fetch_executive_orders(start_date):
    """
    Fetch executive orders signed by Donald Trump published on or after start_date.
    Uses parameters: type=PRESDOCU, presidential_document_type=executive_order, president=donald-trump.
    """
    params = {
        "per_page": "1000",
        "order": "newest",
        "conditions[publication_date][gte]": start_date,
        "conditions[type][]": "PRESDOCU",
        "conditions[presidential_document_type][]": "executive_order",
        "conditions[president][]": "donald-trump"
    }
    response = requests.get(BASE_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print("Error fetching data:", response.status_code)
        return []

def process_order(order):
    """
    Flatten and extract order fields into a dictionary matching CSV_COLUMNS.
    """
    agencies = order.get("agency_names", [])
    agency_names = ", ".join(agencies) if isinstance(agencies, list) else ""
    pres = order.get("president", {})
    president_name = pres.get("name", "") if isinstance(pres, dict) else ""
    pv = order.get("page_views", {})
    page_views_count = pv.get("count", "")
    row = {
        "document_number": order.get("document_number", ""),
        "executive_order_number": order.get("executive_order_number", ""),
        "title": order.get("title", ""),
        "citation": order.get("citation", ""),
        "publication_date": order.get("publication_date", ""),
        "signing_date": order.get("signing_date", ""),
        "pdf_url": order.get("pdf_url", ""),
        "html_url": order.get("html_url", ""),
        "full_text_xml_url": order.get("full_text_xml_url", ""),
        "raw_text_url": order.get("raw_text_url", ""),
        "body_html_url": order.get("body_html_url", ""),
        "agency_names": agency_names,
        "president": president_name,
        "page_views_count": page_views_count,
        "toc_doc": order.get("toc_doc", ""),
        "toc_subject": order.get("toc_subject", ""),
        "subtype": order.get("subtype", ""),
        "executive_order_notes": order.get("executive_order_notes", ""),
        "disposition_notes": order.get("disposition_notes", "")
    }
    return row

def update_csv_and_date(orders):
    """
    Append new orders to the CSV file and update LAST_DATE_FILE with the most recent publication date.
    """
    if not orders:
        print("No new executive orders found.")
        return
    rows = [process_order(order) for order in orders]
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    max_date = max([datetime.datetime.strptime(order.get("publication_date", "1900-01-01"), "%Y-%m-%d").date()
                    for order in orders if order.get("publication_date")])
    set_start_date(max_date.strftime("%Y-%m-%d"))
    print(f"Recorded {len(rows)} new executive order(s). Last publication date updated to {max_date}.")

def generate_xml_url(publication_date, document_number):
    """
    Given a publication_date (YYYY-MM-DD) and document_number,
    return the URL:
    https://www.federalregister.gov/documents/full_text/xml/[year]/[month]/[day]/[document_number].xml
    """
    try:
        parts = publication_date.split("-")
        if len(parts) != 3:
            return None
        year, month, day = parts
        return f"https://www.federalregister.gov/documents/full_text/xml/{year}/{month}/{day}/{document_number}.xml"
    except Exception as e:
        print("Error generating XML URL:", e)
        return None

# --- XML to plain text conversion functions ---

def element_to_lines(elem):
    """
    Recursively extract text from an element.
    Each nonempty text fragment is added as one line.
    """
    lines = []
    if elem.text and elem.text.strip():
        lines.append(elem.text.strip())
    for child in elem:
        lines.extend(element_to_lines(child))
        if child.tail and child.tail.strip():
            lines.append(child.tail.strip())
    return lines

def xml_to_plain_text(xml_content):
    """
    Convert XML content into plain text.
    Each text fragment is output on its own new line.
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print("XML parse error:", e)
        return ""
    lines = element_to_lines(root)
    filtered = [line for line in lines if line]
    return "\n".join(filtered)

def save_order_txt(order):
    """
    For a given order, generate the XML URL from its publication_date and document_number,
    fetch the XML content, convert it to plain text, and save it to a file named [document_number].txt
    in the folder "executive_order_txt".
    """
    pub_date = order.get("publication_date", "")
    doc_num = order.get("document_number", "")
    if not pub_date or not doc_num:
        print("Missing publication_date or document_number for order",
              order.get("executive_order_number", "unknown"))
        return
    xml_url = generate_xml_url(pub_date, doc_num)
    if not xml_url:
        print("Could not generate XML URL for order",
              order.get("executive_order_number", "unknown"))
        return
    response = requests.get(xml_url)
    if response.status_code == 200:
        xml_content = response.text
        plain_text = xml_to_plain_text(xml_content)
        output_dir = "executive_order_txt"
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"{doc_num}.txt"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(plain_text)
        print(f"Saved plain text for document {doc_num} to {file_path}")
    else:
        print(f"Error fetching XML from {xml_url}: {response.status_code}")

def main():
    start_date = get_start_date()
    print("Fetching executive orders published on or after:", start_date)
    orders = fetch_executive_orders(start_date)
    # Load document numbers already processed to avoid duplicates.
    processed_docs = load_processed_document_numbers()
    new_orders = [order for order in orders if order.get("document_number") not in processed_docs]
    if not new_orders:
        print("No new executive orders to process.")
    else:
        update_csv_and_date(new_orders)
        for order in new_orders:
            save_order_txt(order)

if __name__ == "__main__":
    main()
