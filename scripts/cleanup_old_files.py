#!/usr/bin/env python3
"""
Cleanup script to remove old and unused source files after refactoring.
This script identifies and removes old source files that are no longer in use
after the 3-phase migration of the application architecture.

It identifies files that need to be removed according to three strategies:
1. Explicitly listed old module paths that have been relocated
2. Old directory patterns that are no longer used
3. Optional detection of orphaned Python files (without imports)

Usage:
    python scripts/cleanup_old_files.py [--dry-run] [--thorough] [--backup]

Options:
    --dry-run    Show what would be removed without actually deleting files
    --thorough   Perform additional checks for orphaned files
    --backup     Create a zip backup of files before removing them
"""

import os
import re
import shutil
import sys
import argparse
import zipfile
import datetime
import glob
from typing import List, Tuple, Set, Dict, Optional


# Files and directories that should be retained (never deleted)
PROTECTED_PATHS = {
    # Core application files
    "app.py",
    "requirements.txt",
    "requirements_merged.txt",
    "RECOMMENDED_REQUIREMENTS.txt",
    "pyproject.toml",
    "uv.lock",
    ".streamlit",
    "README.md",
    "ARCHITECTURE.md",
    "MIGRATION_GUIDE.md",
    "CLAUDE.md",
    "LICENSE",
    ".gitignore",
    "scripts",
    ".git",
    ".replit",
    "replit.nix",
    "Dockerfile",
    "docker-compose.yml",
    "generated-icon.png",
    ".snapshots",
    ".config",
    "jnius_installation_guide.md",
    "jnius_installation_guide.txt",
    
    # Data directories
    "models",
    "knowledge_base_data",
    "exports",
    "logs",
    "data",
    "temp",
    "book_manager.db",
    "attached_assets",
    
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
    "ui/pages",
    "ui/helpers.py",
    "ui/state.py",
    "ui/__init__.py",
    "ui",  # Remove the UI directory after its contents are processed
    
    # Legacy code paths
    "legacy",
    "old",
    "archive",
    "temp_files",
    "_old",
    "_legacy",
    "_archive",
    "_backup",
    
    # Old standalone files
    "settings.py",     # Now in pages/settings.py
    "kb.py",           # Now in knowledge_base/
    "knowledge.py",    # Now in knowledge_base/
    "extraction.py",   # Now in document_processing/
    "vectordb.py",     # Now in knowledge_base/vector_store.py
    "vector_store.py", # Now in knowledge_base/vector_store.py
    "embeddings.py",   # Now in knowledge_base/embedding.py
    "embedding.py",    # Now in knowledge_base/embedding.py
    "chunking.py",     # Now in knowledge_base/chunking.py
    "chunks.py",       # Now in knowledge_base/chunking.py
    "processing.py",   # Now in document_processing/processor.py
    "processor.py",    # Now in document_processing/processor.py
    "pdf_tools.py",    # Now in document_processing/formats/pdf.py
    "docx_tools.py",   # Now in document_processing/formats/docx.py
    "document.py",     # Now in document_processing/
    "metadata_extract.py",  # Now in document_processing/metadata.py
    "metadata.py",     # Now in document_processing/metadata.py
    "db.py",           # Now in database/connection.py
    "database.py",     # Now in database/connection.py
    "models.py",       # Now in database/models.py
    "schema.py",       # Now in database/schema.py
    "logger.py",       # Now in utils/logger.py
    "logging_setup.py", # Now in utils/logger.py
    "helpers.py",      # Now in utils/
    "util.py",         # Now in utils/
    "utilities.py",    # Now in utils/
    "common.py",       # Now in utils/ or core/
    "config.py",       # Now in config/settings.py or core/config.py
    "constants.py",    # Now in core/constants.py
    "exceptions.py",   # Now in core/exceptions.py
    "errors.py",       # Now in core/exceptions.py
    "chat.py",         # Now in components/chat_interface.py
    "search.py",       # Now in knowledge_base/search.py
    "books.py",        # Now in book_manager/
    "documents.py",    # Now in document_processing/
    "ocr.py",          # Now in document_processing/ocr.py
    "ai.py",           # Now in ai/
    "text_splitter.py", # Now in knowledge_base/chunking.py
}


def detect_orphaned_files(root_dir: str = ".") -> List[str]:
    """
    Detect orphaned Python files that are not imported anywhere.
    
    Args:
        root_dir: Root directory to search from
        
    Returns:
        List of potentially orphaned files
    """
    # Get all Python files
    all_py_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                # Skip files in protected directories
                if any(rel_path.startswith(p) for p in PROTECTED_PATHS if os.path.isdir(os.path.join(root_dir, p))):
                    continue
                all_py_files.append(rel_path)
    
    # Check which files are imported
    imported_files = set()
    import_patterns = [
        re.compile(r'from\s+([\w.]+)\s+import'),
        re.compile(r'import\s+([\w.]+)'),
    ]
    
    for py_file in all_py_files:
        try:
            with open(os.path.join(root_dir, py_file), 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in import_patterns:
                    for match in pattern.finditer(content):
                        module_path = match.group(1)
                        # Convert module paths to file paths
                        module_parts = module_path.split('.')
                        for i in range(len(module_parts)):
                            candidate = os.path.join(*module_parts[:i+1]) + '.py'
                            if candidate in all_py_files:
                                imported_files.add(candidate)
                            # Also check for __init__.py files
                            init_candidate = os.path.join(*module_parts[:i], '__init__.py')
                            if init_candidate in all_py_files:
                                imported_files.add(init_candidate)
        except Exception:
            # Skip files with encoding issues
            continue
    
    # Find orphaned files
    orphaned_files = []
    for py_file in all_py_files:
        if py_file not in imported_files and not py_file.endswith('__init__.py'):
            # Don't include files that are entry points or scripts
            with open(os.path.join(root_dir, py_file), 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip files that are likely entry points
                if '__main__' in content or 'argparse' in content or 'sys.argv' in content:
                    continue
            
            orphaned_files.append(os.path.join(root_dir, py_file))
    
    return orphaned_files


def create_backup(files_to_backup: List[str], dirs_to_backup: List[str], root_dir: str = ".") -> str:
    """
    Create a zip backup of files and directories to be removed.
    
    Args:
        files_to_backup: List of files to backup
        dirs_to_backup: List of directories to backup
        root_dir: Root directory
        
    Returns:
        Path to the backup file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"cleanup_backup_{timestamp}.zip"
    backup_path = os.path.join(root_dir, backup_filename)
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add files
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                rel_path = os.path.relpath(file_path, root_dir)
                zipf.write(file_path, rel_path)
        
        # Add directories
        for dir_path in dirs_to_backup:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, root_dir)
                        zipf.write(file_path, rel_path)
    
    return backup_path


def find_files_to_remove(root_dir: str = ".", thorough: bool = False) -> Tuple[List[str], List[str], List[str]]:
    """
    Find files that should be removed.
    
    Args:
        root_dir: Root directory to search from
        thorough: If True, also detect orphaned files
        
    Returns:
        Tuple of (directories to remove, files to remove, orphaned files)
    """
    dirs_to_remove = []
    files_to_remove = []
    
    # Explicitly listed old modules
    for path in OLD_MODULES:
        full_path = os.path.join(root_dir, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                dirs_to_remove.append(full_path)
            else:
                files_to_remove.append(full_path)
    
    # Find old backup/archive directories using patterns
    backup_patterns = ['*_old', '*_backup', '*_archive', '*_legacy', 'old_*', 'backup_*', 'archive_*', 'legacy_*']
    for pattern in backup_patterns:
        for path in glob.glob(os.path.join(root_dir, pattern)):
            if os.path.isdir(path) and not is_path_protected(path, PROTECTED_PATHS, root_dir):
                dirs_to_remove.append(path)
    
    # Optionally find orphaned files
    orphaned_files = []
    if thorough:
        orphaned_files = detect_orphaned_files(root_dir)
    
    return dirs_to_remove, files_to_remove, orphaned_files


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


def cleanup(dry_run: bool = False, thorough: bool = False, backup: bool = False) -> None:
    """
    Remove old and unused source files.
    
    Args:
        dry_run: If True, only show what would be removed without actually deleting
        thorough: If True, perform additional checks for orphaned files
        backup: If True, create a backup of files to be removed
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Set the working directory to the root
    os.chdir(root_dir)
    
    # Find files and directories to remove
    dirs_to_remove, files_to_remove, orphaned_files = find_files_to_remove(
        root_dir=root_dir, 
        thorough=thorough
    )
    
    # Display summary
    print(f"\nFound {len(files_to_remove)} files and {len(dirs_to_remove)} directories to remove.")
    if thorough:
        print(f"Additionally found {len(orphaned_files)} potentially orphaned files.")
    
    # Create backup if requested
    if backup and not dry_run and (files_to_remove or dirs_to_remove or orphaned_files):
        # Collect all files to backup
        all_files_to_backup = files_to_remove.copy()
        
        if thorough and orphaned_files:
            # Ask about orphaned files
            print("\nOrphaned files detected:")
            for i, file_path in enumerate(orphaned_files):
                rel_path = os.path.relpath(file_path, root_dir)
                print(f"  {i+1}. {rel_path}")
            
            if input("\nInclude orphaned files in backup? (y/N): ").lower() == 'y':
                all_files_to_backup.extend(orphaned_files)
        
        backup_path = create_backup(all_files_to_backup, dirs_to_remove, root_dir)
        print(f"\nBackup created at: {backup_path}")
    
    # Process orphaned files if in thorough mode
    if thorough and orphaned_files:
        print("\nOrphaned files found:")
        for file_path in orphaned_files:
            rel_path = os.path.relpath(file_path, root_dir)
            print(f"  - {rel_path}")
        
        if not dry_run:
            if input("\nWould you like to remove these orphaned files? (y/N): ").lower() == 'y':
                for file_path in orphaned_files:
                    if is_path_protected(file_path, PROTECTED_PATHS, root_dir):
                        print(f"Protected: {file_path}")
                        continue
                    
                    try:
                        os.remove(file_path)
                        print(f"Removed orphaned file: {file_path}")
                    except Exception as e:
                        print(f"Error removing {file_path}: {str(e)}")
    
    # Remove regular files
    print("\nProcessing explicitly listed old files:")
    for file_path in files_to_remove:
        if is_path_protected(file_path, PROTECTED_PATHS, root_dir):
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
    print("\nProcessing directories:")
    for dir_path in sorted(dirs_to_remove, key=len, reverse=True):  # Remove deepest dirs first
        if is_path_protected(dir_path, PROTECTED_PATHS, root_dir):
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
    parser.add_argument(
        "--thorough",
        action="store_true",
        help="Perform additional checks for orphaned files"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a zip backup of files before removing them"
    )
    
    args = parser.parse_args()
    
    print("=== Book Knowledge AI Cleanup Script ===")
    print("This script will remove old source files that are no longer needed.")
    
    if args.thorough:
        print("Running in THOROUGH mode - will check for orphaned files.")
    
    if args.backup:
        print("BACKUP mode enabled - will create a zip archive of removed files.")
    
    if args.dry_run:
        print("\nRunning in DRY RUN mode - no files will be deleted.")
    else:
        print("\nWARNING: This will delete files. Make sure you have a backup or Git commit.")
        
        if input("Continue? (y/N): ").lower() != 'y':
            print("Aborting.")
            sys.exit(0)
    
    cleanup(dry_run=args.dry_run, thorough=args.thorough, backup=args.backup)
    
    print("\nCleanup complete.")
    
    if args.dry_run:
        print("This was a dry run. No files were actually deleted.")
        print("Run without --dry-run to perform actual deletion.")


if __name__ == "__main__":
    main()