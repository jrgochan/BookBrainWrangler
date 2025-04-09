#!/usr/bin/env python3
"""
Cleanup script to remove old and unused source files after refactoring.
This script identifies and removes old source files that are no longer in use
after the 3-phase migration of the application architecture.

Usage:
    python scripts/cleanup_old_files.py [--dry-run]

Options:
    --dry-run    Show what would be removed without actually deleting files
"""

import os
import shutil
import sys
import argparse
from typing import List, Tuple, Set


# Files and directories that should be retained (never deleted)
PROTECTED_PATHS = {
    # Core application files
    "app.py",
    "requirements.txt",
    "pyproject.toml",
    ".streamlit",
    "README.md",
    "ARCHITECTURE.md",
    "MIGRATION_GUIDE.md",
    "LICENSE",
    ".gitignore",
    "scripts",
    ".git",
    
    # Data directories
    "models",
    "knowledge_base_data",
    "exports",
    "logs",
    "data",
    "temp",
    "book_manager.db",
    
    # Module directories (new structure)
    "ai",
    "book_manager",
    "components",
    "config",
    "core",
    "database",
    "document_processing",
    "knowledge_base",
    "ollama",
    "pages",
    "utils",
}

# Old module directories and files to be removed
OLD_MODULES = {
    # Old UI files and directories
    "ui/components",
    "ui/helpers.py",
    "ui/pages",
    "ui/state.py",
    "ui/__init__.py",
    
    # Legacy code paths
    "legacy",
    "old",
    "archive",
    
    # Old standalone files
    "settings.py",     # Now in pages/settings.py
    "kb.py",           # Now in knowledge_base/
    "extraction.py",   # Now in document_processing/
    "vectordb.py",     # Now in knowledge_base/vector_store.py
    "embeddings.py",   # Now in knowledge_base/embedding.py
    "chunking.py",     # Now in knowledge_base/chunking.py
    "processing.py",   # Now in document_processing/processor.py
    "pdf_tools.py",    # Now in document_processing/formats/pdf.py
    "docx_tools.py",   # Now in document_processing/formats/docx.py
    "metadata_extract.py",  # Now in document_processing/metadata.py
    "db.py",           # Now in database/connection.py
    "models.py",       # Now in database/models.py
    "logger.py",       # Now in utils/logger.py
}


def find_files_to_remove(root_dir: str = ".") -> Tuple[List[str], List[str]]:
    """
    Find files that should be removed.
    
    Args:
        root_dir: Root directory to search from
        
    Returns:
        Tuple of (directories to remove, files to remove)
    """
    dirs_to_remove = []
    files_to_remove = []
    
    for path in OLD_MODULES:
        full_path = os.path.join(root_dir, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                dirs_to_remove.append(full_path)
            else:
                files_to_remove.append(full_path)
    
    return dirs_to_remove, files_to_remove


def is_path_protected(path: str, protected_paths: Set[str], root_dir: str = ".") -> bool:
    """
    Check if a path is protected from deletion.
    
    Args:
        path: Path to check
        protected_paths: Set of protected paths
        root_dir: Root directory
        
    Returns:
        True if the path is protected, False otherwise
    """
    # Get relative path for checking against protected paths
    rel_path = os.path.relpath(path, root_dir)
    
    # Check if the path itself is protected
    if rel_path in protected_paths:
        return True
    
    # Check if the path is inside a protected directory
    for protected in protected_paths:
        protected_full = os.path.join(root_dir, protected)
        if os.path.isdir(protected_full) and path.startswith(protected_full):
            return True
    
    return False


def cleanup(dry_run: bool = False) -> None:
    """
    Remove old and unused source files.
    
    Args:
        dry_run: If True, only show what would be removed without actually deleting
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Set the working directory to the root
    os.chdir(root_dir)
    
    dirs_to_remove, files_to_remove = find_files_to_remove()
    
    # Remove files first
    for file_path in files_to_remove:
        if is_path_protected(file_path, PROTECTED_PATHS):
            print(f"Protected: {file_path}")
            continue
        
        if dry_run:
            print(f"Would remove file: {file_path}")
        else:
            try:
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {str(e)}")
    
    # Then remove directories
    for dir_path in sorted(dirs_to_remove, key=len, reverse=True):  # Remove deepest dirs first
        if is_path_protected(dir_path, PROTECTED_PATHS):
            print(f"Protected: {dir_path}")
            continue
        
        if dry_run:
            print(f"Would remove directory: {dir_path}")
        else:
            try:
                shutil.rmtree(dir_path)
                print(f"Removed directory: {dir_path}")
            except Exception as e:
                print(f"Error removing {dir_path}: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cleanup script to remove old and unused source files after refactoring."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually deleting files"
    )
    
    args = parser.parse_args()
    
    print("=== Book Knowledge AI Cleanup Script ===")
    print("This script will remove old source files that are no longer needed.")
    
    if args.dry_run:
        print("\nRunning in DRY RUN mode - no files will be deleted.")
    else:
        print("\nWARNING: This will delete files. Make sure you have a backup or Git commit.")
        
        if input("Continue? (y/N): ").lower() != 'y':
            print("Aborting.")
            sys.exit(0)
    
    cleanup(dry_run=args.dry_run)
    
    print("\nCleanup complete.")
    
    if args.dry_run:
        print("This was a dry run. No files were actually deleted.")
        print("Run without --dry-run to perform actual deletion.")


if __name__ == "__main__":
    main()