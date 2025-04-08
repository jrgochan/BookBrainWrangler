#!/bin/bash
# Helper script for jnius setup

echo "===== Jnius Setup Helper ====="

# Check for Java
if command -v java &>/dev/null; then
    echo "Found Java installation"
else
    echo "Error: Java not found. Please install JDK 8+"
    exit 1
fi

# Check for JAVA_HOME
if [ -z "$JAVA_HOME" ]; then
    echo "JAVA_HOME not set - this is required for jnius"
    echo "Please set JAVA_HOME to your JDK installation path"
else
    echo "JAVA_HOME is set to: $JAVA_HOME"
fi

echo "To install jnius:"
echo "1. First install Cython"
echo "2. Then install jnius"
echo "See jnius_installation_guide.txt for details"
