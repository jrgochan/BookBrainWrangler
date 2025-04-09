# Migration Guide

This guide outlines the process for migrating the codebase to the new architecture.

## Current Status

We've completed Phase 1 of the migration:

- Created a new directory structure
- Created core modules (config, constants, exceptions)
- Set up symbolic links to maintain functionality during migration
- Documented the new architecture

## Migration Phases

### Phase 1: Core Restructuring (Completed)

- ✓ Create the new directory structure
- ✓ Create core module files
- ✓ Set up symbolic links to maintain current functionality
- ✓ Document the new architecture

### Phase 2: Interface Refinement (Next)

1. Define clean APIs in each package's `__init__.py`
2. Update imports in application code to use these new interfaces
3. Move core functionality from existing modules to the new structure
4. Test integration between components

### Phase 3: Enhanced Modularization (Future)

1. Break down large modules into more focused components
2. Improve error handling and logging
3. Add comprehensive docstrings
4. Add unit tests

## Migration Strategy

For each module:

1. **Copy the existing functionality** to the new location
2. **Update imports** to use the new module structure
3. **Update the `__init__.py`** file to expose the right components
4. **Test the functionality** to ensure it works correctly
5. **Remove the old module** once all dependencies are updated

## Import Update Guide

Here's how imports will change after migration:

### Before:
```python
from database import get_connection
from utils import extract_text, get_logger
from document_processor import DocumentProcessor
from ollama_client import OllamaClient
```

### After:
```python
from database import get_connection
from utils.text_processing import extract_text
from utils.logger import get_logger
from document_processing import DocumentProcessor
from ai.ollama import OllamaClient
```

## Tips for Successful Migration

1. **Work in Small Steps**: Migrate one module at a time
2. **Test Frequently**: Ensure the application still works after each change
3. **Use Feature Branches**: Create a branch for each migration task
4. **Update Documentation**: Keep documentation in sync with code changes

## Cleaning Up Old Files

After completing a migration phase, you'll want to clean up old files that are no longer needed. We've created a cleanup script to help with this process:

```bash
# Preview what will be removed
python scripts/cleanup_old_files.py --dry-run

# Create a backup and remove old files
python scripts/cleanup_old_files.py --backup
```

The script provides several useful features:

- **Dry Run Mode**: Preview files that would be deleted without actually removing them
- **Backup Option**: Create a ZIP archive of files before removing them
- **Thorough Mode**: Use import analysis to detect orphaned Python files

For more information on the cleanup script, see [scripts/CLEANUP_README.md](scripts/CLEANUP_README.md).

## Schedule

1. Phase 2: Interface Refinement - 1-2 weeks
2. Phase 3: Enhanced Modularization - 2-3 weeks