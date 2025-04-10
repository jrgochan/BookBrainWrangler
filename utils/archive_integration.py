"""
Internet Archive integration utilities for Book Knowledge AI.

This module provides functionality for searching and downloading books
from the Internet Archive for integration with the Book Knowledge Base.
"""

import os
import re
import hashlib
import logging
import requests
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Configure logging
from utils.logger import get_logger
from database import get_connection
logger = get_logger(__name__)

# Base URLs for Internet Archive API
SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata"
DOWNLOAD_URL_BASE = "https://archive.org/download"

# Directory to save downloads
DEFAULT_DOWNLOAD_DIR = "downloads/archive_org"

class ArchiveOrgClient:
    """Client for interacting with the Internet Archive API."""
    
    def __init__(self, download_dir: str = DEFAULT_DOWNLOAD_DIR):
        """
        Initialize the Internet Archive client.
        
        Args:
            download_dir: Directory to save downloaded files
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"Initialized Internet Archive client with download directory: {download_dir}")
    
    def search_books(self, query: str, max_results: int = 50, media_type: str = "texts") -> List[Dict[str, Any]]:
        """
        Search for books in the Internet Archive.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            media_type: Type of media to search for (default: texts)
            
        Returns:
            List of book metadata dictionaries
        """
        logger.info(f"Searching Internet Archive for: '{query}', max_results={max_results}")
        
        # Prepare search parameters for the API
        search_query = f'("{query}") AND mediatype:{media_type}'
        params = {
            "q": search_query,
            "fl[]": ["identifier", "title", "creator", "date", "description", "subject", "mediatype", "downloads"],
            "output": "json",
            "rows": max_results,
            "page": 1,
            "sort[]": ["downloads desc"]  # Sort by number of downloads
        }
        
        try:
            logger.debug(f"Sending search request with params: {params}")
            resp = requests.get(SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get('response', {}).get('docs', [])
            logger.info(f"Found {len(results)} results for query '{query}'")
            
            # Enhance results with preview URLs and clean up data
            enhanced_results = []
            for item in results:
                # Create a sanitized result with consistent keys
                result = {
                    'identifier': item.get('identifier', ''),
                    'title': item.get('title', 'Unknown Title'),
                    'author': item.get('creator', ['Unknown Author'])[0] if isinstance(item.get('creator', []), list) and item.get('creator', []) else item.get('creator', 'Unknown Author'),
                    'date': item.get('date', 'Unknown Date'),
                    'description': item.get('description', 'No description available'),
                    'subjects': item.get('subject', []),
                    'mediatype': item.get('mediatype', 'texts'),
                    'downloads': item.get('downloads', 0),
                    'preview_url': f"https://archive.org/details/{item.get('identifier', '')}"
                }
                
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching Internet Archive: {str(e)}")
            return []
    
    def get_available_formats(self, identifier: str) -> List[Dict[str, Any]]:
        """
        Get available formats for a book.
        
        Args:
            identifier: Internet Archive identifier
            
        Returns:
            List of available file formats and their details
        """
        logger.info(f"Getting available formats for book: {identifier}")
        
        try:
            meta_url = f"{METADATA_URL}/{identifier}"
            resp = requests.get(meta_url, timeout=10)
            resp.raise_for_status()
            
            meta = resp.json()
            files = meta.get('files', [])
            
            # Filter for supported document formats
            desired_exts = {".pdf", ".epub", ".txt", ".docx", ".doc"}
            available_formats = []
            
            for file_info in files:
                name = file_info.get('name', '')
                if not name:
                    continue
                
                # Check file extension against allowed set (case-insensitive)
                _, ext = os.path.splitext(name.lower())
                if ext in desired_exts:
                    # Calculate the full download URL
                    download_url = f"{DOWNLOAD_URL_BASE}/{identifier}/{name}"
                    
                    # Add to available formats list
                    available_formats.append({
                        'name': name,
                        'format': ext[1:],  # Remove the leading dot
                        'size': file_info.get('size', 0),
                        'url': download_url
                    })
            
            logger.info(f"Found {len(available_formats)} available formats for book {identifier}")
            return available_formats
            
        except Exception as e:
            logger.error(f"Error getting formats for book {identifier}: {str(e)}")
            return []
    
    def download_book(self, 
                     identifier: str, 
                     file_url: str, 
                     title: Optional[str] = None,
                     author: Optional[str] = None) -> Optional[str]:
        """
        Download a book from the Internet Archive.
        
        Args:
            identifier: Internet Archive identifier
            file_url: URL to download the file
            title: Book title (for organizing files)
            author: Book author (for organizing files)
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        logger.info(f"Downloading book: {identifier} from {file_url}")
        
        # Extract filename from URL
        file_name = os.path.basename(file_url)
        
        # Create a sanitized directory based on title and author if available
        if title and author:
            # Sanitize title and author for use in directory name
            safe_title = re.sub(r'[^\w.\&()\- ]+', '_', title)[:50].strip()
            safe_author = re.sub(r'[^\w.\&()\- ]+', '_', author)[:30].strip()
            book_dir = os.path.join(self.download_dir, f"{safe_author}_{safe_title}")
        else:
            book_dir = os.path.join(self.download_dir, identifier)
        
        os.makedirs(book_dir, exist_ok=True)
        local_path = os.path.join(book_dir, file_name)
        
        # Check if file already exists
        if os.path.exists(local_path):
            logger.info(f"File already exists: {local_path}")
            return local_path
        
        try:
            logger.debug(f"Downloading file from {file_url} to {local_path}")
            r = requests.get(file_url, stream=True, timeout=60)
            r.raise_for_status()
            
            # Stream download to file in chunks
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded book successfully: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading file {file_url}: {str(e)}")
            return None
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file to check for duplicates.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash of the file as a hexadecimal string
        """
        logger.debug(f"Calculating hash for file: {file_path}")
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            file_hash = hash_md5.hexdigest()
            logger.debug(f"File hash calculated: {file_hash}")
            return file_hash
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
            
    def check_book_exists_by_title_author(self, title: str, author: str) -> bool:
        """
        Check if a book already exists in the database based on title and author.
        
        Args:
            title: Book title
            author: Book author
            
        Returns:
            True if book exists, False otherwise
        """
        logger.debug(f"Checking if book exists: '{title}' by '{author}'")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Case-insensitive match on title and author
            cursor.execute(
                "SELECT COUNT(*) FROM books WHERE LOWER(title) = LOWER(?) AND LOWER(author) = LOWER(?)",
                (title, author)
            )
            count = cursor.fetchone()[0]
            exists = count > 0
            
            if exists:
                logger.info(f"Book '{title}' by '{author}' already exists in database")
            else:
                logger.debug(f"Book '{title}' by '{author}' not found in database")
                
            return exists
            
        except Exception as e:
            logger.error(f"Error checking if book exists: {str(e)}")
            return False
        finally:
            conn.close()
            
    def store_file_hash(self, book_id: int, file_hash: str) -> bool:
        """
        Store a file hash in the database for duplicate detection.
        
        Args:
            book_id: Book ID
            file_hash: MD5 hash of the file
            
        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Storing file hash for book ID {book_id}: {file_hash}")
        
        # First, check if we need to create the file_hashes table
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                book_id INTEGER PRIMARY KEY,
                file_hash TEXT NOT NULL,
                date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            )
            ''')
            
            # Store the hash
            cursor.execute(
                "INSERT OR REPLACE INTO file_hashes (book_id, file_hash) VALUES (?, ?)",
                (book_id, file_hash)
            )
            
            conn.commit()
            logger.info(f"File hash stored for book ID {book_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing file hash: {str(e)}")
            return False
        finally:
            conn.close()
            
    def check_hash_exists(self, file_hash: str) -> Optional[int]:
        """
        Check if a file hash already exists in the database.
        
        Args:
            file_hash: MD5 hash of the file
            
        Returns:
            Book ID if hash exists, None otherwise
        """
        logger.debug(f"Checking if file hash exists: {file_hash}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # First check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_hashes'")
            if not cursor.fetchone():
                logger.debug("file_hashes table does not exist yet")
                return None
                
            # Check for the hash
            cursor.execute("SELECT book_id FROM file_hashes WHERE file_hash = ?", (file_hash,))
            result = cursor.fetchone()
            
            if result:
                book_id = result[0]
                logger.info(f"File hash {file_hash} found for book ID {book_id}")
                return book_id
            else:
                logger.debug(f"File hash {file_hash} not found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error checking if file hash exists: {str(e)}")
            return None
        finally:
            conn.close()