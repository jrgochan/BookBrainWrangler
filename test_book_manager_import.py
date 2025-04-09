"""Test script to verify book_manager import works correctly"""

print("Testing book_manager import...")

# Import using the new package structure
from book_manager.manager import BookManager
bm = BookManager()
print(f"Successfully created BookManager instance: {bm}")

print("\nImport successful!")
