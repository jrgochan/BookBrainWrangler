import os
import re
import sys
import logging
import requests

# Configure logging to show INFO messages and above
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Accept search phrase from command-line arguments for automation
if len(sys.argv) < 2:
    logging.error("Usage: python script.py <search phrase>")
    sys.exit(1)
search_phrase = sys.argv[1]

# Base URL for advanced search and metadata
SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata"

# Prepare search parameters for the API
query = f'("{search_phrase}") AND mediatype:texts'
params = {
    "q": query,
    "fl[]": ["identifier", "title", "subject"],
    "output": "json",
    "rows": 50,         # number of results to fetch (adjust as needed)
    "page": 1
}

try:
    resp = requests.get(SEARCH_URL, params=params)
    resp.raise_for_status()
except Exception as e:
    logging.error(f"Search request failed: {e}")
    sys.exit(1)

# Parse search results
results = resp.json().get('response', {}).get('docs', [])
if not results:
    logging.info("No results found for the search query.")
    sys.exit(0)

logging.info(f"Found {len(results)} results for '{search_phrase}'. Processing each...")

# Directory to save downloads (organized by subject)
BASE_DIR = "downloads"
os.makedirs(BASE_DIR, exist_ok=True)

for doc in results:
    identifier = doc.get('identifier')
    title = doc.get('title', 'Untitled')
    subjects = doc.get('subject', None)
    # Determine primary subject for folder name
    if isinstance(subjects, list):
        primary_subject = subjects[0] if subjects else "Unknown"
    elif isinstance(subjects, str):
        primary_subject = subjects
    else:
        primary_subject = "Unknown"

    # Sanitize folder name
    safe_subject = re.sub(r'[^\w.\&()\- ]+', '_', primary_subject)[:100].strip() or "Unknown"

    folder_path = os.path.join(BASE_DIR, safe_subject)
    os.makedirs(folder_path, exist_ok=True)

    # Get detailed metadata for the item
    meta_url = f"{METADATA_URL}/{identifier}"
    try:
        meta_resp = requests.get(meta_url)
        meta_resp.raise_for_status()
    except Exception as e:
        logging.warning(f"Skipping '{title}' ({identifier}) – metadata fetch failed: {e}")
        continue
    meta = meta_resp.json()
    files = meta.get('files', [])

    # Filter for files in desired formats
    desired_exts = {".pdf", ".epub", ".txt", ".docx"}
    files_to_download = []
    for file_info in files:
        name = file_info.get('name')
        if not name:
            continue
        # Check file extension against allowed set (case-insensitive)
        _, ext = os.path.splitext(name.lower())
        if ext in desired_exts:
            files_to_download.append(name)

    if not files_to_download:
        logging.info(f"Skipped '{title}' – no PDF, EPUB, TXT, or DOCX format available.")
        continue

    # Download each file in the allowed formats
    for file_name in files_to_download:
        file_url = f"https://archive.org/download/{identifier}/{file_name}"
        local_path = os.path.join(folder_path, file_name)
        try:
            r = requests.get(file_url, stream=True)
            r.raise_for_status()
            # Stream download to file in chunks
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Downloaded '{title}' – saved file: {safe_subject}/{file_name}")
        except Exception as e:
            logging.error(f"Failed to download file '{file_name}' for item '{title}': {e}")
