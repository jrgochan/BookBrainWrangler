#!/usr/bin/env python3
"""
Test runner for Taipy integration tests.
"""

import os
import sys
import unittest

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print("Running Taipy integration tests...")
    
    # Discover and run only integration tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration-specific test files
    integration_tests = loader.discover("tests", pattern="integration_*.py")
    suite.addTest(integration_tests)
    
    # Add navigation tests
    navigation_tests = loader.discover("tests", pattern="test_taipy_navigation.py")
    suite.addTest(navigation_tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    sys.exit(not result.wasSuccessful())