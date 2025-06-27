#!/usr/bin/env python3
"""
Example test for PXBot apps
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from apps.demo_calculator import DemoCalculator
except ImportError:
    DemoCalculator = None

class TestDemoCalculator(unittest.TestCase):
    def setUp(self):
        if DemoCalculator:
            self.calc = DemoCalculator()
    
    @unittest.skipIf(DemoCalculator is None, "DemoCalculator not available")
    def test_basic_calculation(self):
        result = self.calc.execute_command("calc:eval:2+2")
        self.assertIn("4", result)
    
    @unittest.skipIf(DemoCalculator is None, "DemoCalculator not available")
    def test_invalid_command(self):
        result = self.calc.execute_command("invalid:command")
        self.assertIn("calc:", result)

if __name__ == "__main__":
    unittest.main()
