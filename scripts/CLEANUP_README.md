# Book Knowledge AI Cleanup Utility

This directory contains the `cleanup_old_files.py` script, which is designed to help clean up the codebase after the 3-phase migration of the application architecture. The script identifies and removes old source files that are no longer in use.

## Features

- **Explicit File Detection**: Finds and removes files that have been relocated to new locations in the refactored architecture
- **Directory Pattern Matching**: Identifies old backup/archive directories using naming patterns
- **Orphaned File Detection**: (Optional) Analyzes imports to find Python files that are no longer referenced
- **Backup Creation**: (Optional) Creates a zip archive of files before removing them
- **Dry Run Mode**: Preview what would be removed without actually deleting any files
- **Protected Path Detection**: Ensures critical files and directories are never removed

## Usage

```bash
python scripts/cleanup_old_files.py [OPTIONS]
```

### Options

- `--dry-run`: Show what would be removed without actually deleting files
- `--thorough`: Perform additional checks for orphaned files (analyzes imports)
- `--backup`: Create a zip backup of files before removing them

### Examples

**Preview what would be removed:**
```bash
python scripts/cleanup_old_files.py --dry-run
```

**Create a backup before removing files:**
```bash
python scripts/cleanup_old_files.py --backup
```

**Perform thorough analysis and create a backup:**
```bash
python scripts/cleanup_old_files.py --thorough --backup
```

## Safety Features

- The script will never remove files in protected directories (such as `.git`, `models`, etc.)
- A confirmation prompt is displayed before any files are deleted
- The `--dry-run` mode allows you to see what would be removed without any actual deletion
- The `--backup` option creates a zip archive of all files before removal

## How It Works

The script uses three strategies to identify files for removal:

1. **Explicit old modules list**: Files and directories listed in the `OLD_MODULES` set
2. **Pattern matching**: Directories matching patterns like `*_old`, `*_backup`, etc.
3. **Import analysis**: (Optional) Python files that are not imported anywhere else

Files are categorized into:
- Regular files (explicitly listed)
- Directories (explicitly listed or matching patterns)
- Orphaned files (detected by import analysis)

For each category, the script checks if the path is protected, and if not, removes it (unless in dry-run mode).

## Note on the Thorough Mode

The `--thorough` option performs a comprehensive analysis of Python imports to detect orphaned files. This can be slow on large codebases but provides a more complete cleanup. When orphaned files are detected, you'll be prompted whether to remove them.

## Customization

You can customize the script by editing the following lists in the script:

- `PROTECTED_PATHS`: Files and directories that should never be removed
- `OLD_MODULES`: Specific files and directories to be removed