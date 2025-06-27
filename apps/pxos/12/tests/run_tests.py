#!/usr/bin/env python3
"""
PXBot Test Runner - Run all app tests
"""

import unittest
import sys
import os

# Add apps directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps'))

def run_all_tests():
    """Run all tests in the tests directory"""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
