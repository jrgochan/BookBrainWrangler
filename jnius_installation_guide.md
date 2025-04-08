# jnius Installation Guide for WSL2 Ubuntu

This guide provides detailed steps to handle common jnius installation issues in WSL2 Ubuntu environments.

## Prerequisites

Ensure you have the following installed:

1. **Python 3.11+** (with pip and venv)
2. **Java JDK**
3. **Build tools** (gcc, build-essential)

## Step-by-Step Installation Process

### 1. Set Up Your Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install System Dependencies

Install required system packages:

```bash
sudo apt-get update
sudo apt-get install -y default-jdk build-essential python3-dev
```

### 3. Configure JAVA_HOME

Set the JAVA_HOME environment variable:

```bash
# Find your Java installation
java_path=$(readlink -f $(which java) | sed 's:/bin/java::')

# Set JAVA_HOME for current session
export JAVA_HOME=$java_path

# Optional: Add to .bashrc for persistence
echo "export JAVA_HOME=$java_path" >> ~/.bashrc
```

### 4. Install Cython

Cython must be installed before attempting to install jnius:

```bash
pip install Cython
```

### 5. Install jnius

Try different installation methods in this order:

```bash
# Method 1: Standard installation
pip install jnius

# If that fails, try Method 2: No binary installation
pip install --no-binary :all: jnius

# If that fails, try Method 3: With explicit compiler flags
JAVA_HOME=$java_path CFLAGS="-fPIC" pip install jnius
```

## Troubleshooting Common Errors

### ModuleNotFoundError: No module named 'Cython'

This error occurs when trying to install jnius without Cython:

```
error: subprocess-exited-with-error
× Getting requirements to build wheel did not run successfully.
│ exit code: 1
╰─> [output]
    You need Cython to compile Pyjnius.
    ModuleNotFoundError: No module named 'Cython'
```

**Solution**: Install Cython first with `pip install Cython`

### Could not find JVM shared library

```
OSError: cannot load library 'jvm.dll': error 0x7e
```

**Solution**: Ensure JAVA_HOME is correctly set:

```bash
# Check if Java is installed
java -version

# Set JAVA_HOME to the correct path
export JAVA_HOME=/path/to/java
```

### Build fails with gcc errors

```
error: command 'gcc' failed with exit status 1
```

**Solution**: Install build tools and development packages:

```bash
sudo apt-get install build-essential python3-dev
```

## Verifying Installation

Test if jnius was installed correctly:

```bash
python -c 'import jnius; print("jnius installed successfully!")'
```

## Note

jnius is used for Java integration and may not be required for all functionality of the application. If you continue to face installation issues, you can proceed without it for basic functionality.