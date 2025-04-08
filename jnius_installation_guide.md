# Jnius Installation Guide

The `jnius` Python package provides Java integration via JNI but requires specific setup steps that differ by platform. This guide will help you resolve common installation issues.

## Prerequisites

1. Install Java Development Kit (JDK) 8 or newer
2. Set JAVA_HOME environment variable
3. Install Cython (required to build jnius)

## Installation Steps by Platform

### Linux/Ubuntu

1. Install JDK and required dependencies:
   ```bash
   sudo apt update
   sudo apt install default-jdk python3-dev
   sudo apt install build-essential
   ```

2. Set JAVA_HOME:
   ```bash
   export JAVA_HOME=/usr/lib/jvm/default-java
   ```

3. Install Cython first:
   ```bash
   pip install Cython
   ```

4. Install jnius:
   ```bash
   pip install jnius
   ```

### Windows

1. Install JDK from [Oracle](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://adoptium.net/)

2. Add JAVA_HOME to environment variables:
   - Right-click on "This PC" and select "Properties"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Add a new system variable named JAVA_HOME pointing to your JDK installation folder (e.g., C:\Program Files\Java\jdk-17)
   - Add %JAVA_HOME%\bin to your PATH variable

3. Install Visual C++ Build Tools (required for compiling extensions)
   - Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "Desktop Development with C++" workload during installation

4. Install Cython first:
   ```
   pip install Cython
   ```

5. Install jnius:
   ```
   pip install jnius
   ```

### macOS

1. Install JDK using Homebrew:
   ```bash
   brew install openjdk
   ```

2. Set JAVA_HOME:
   ```bash
   export JAVA_HOME=$(/usr/libexec/java_home)
   ```

3. Install Cython first:
   ```bash
   pip install Cython
   ```

4. Install jnius:
   ```bash
   pip install jnius
   ```

## Common Errors and Solutions

### Error: "You need Cython to compile Pyjnius"
Solution: Install Cython before attempting to install jnius:
```
pip install Cython
```

### Error: "No module named 'jnius'"
Solution: Verify your JAVA_HOME environment variable is set correctly and try reinstalling:
```
pip uninstall jnius
pip install jnius
```

### Error: "Java library not found"
Solution: Ensure JAVA_HOME points to a valid JDK installation and that the java binary is in your PATH.

## Alternative: Manual Installation

If pip installation fails, you can try installing from source:

```bash
git clone https://github.com/kivy/pyjnius.git
cd pyjnius
pip install Cython
pip install -e .
```

## Verification

Test your installation by running:

```python
from jnius import autoclass
System = autoclass('java.lang.System')
print(System.getProperty('java.version'))
```