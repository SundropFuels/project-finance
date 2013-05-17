"""company_sim_test.py
Unit tests for company objects
Chris Perkins
2012-10-23
"""

import unittest
from company import *
from company_simulation import *
import numpy as np
import dataFrame_v2 as df
import copy
import UnitValues as uv

class testGenerateIncomeStatement(unittest.TestCase):
    """Test whether the simulator generates the income statement properly"""
    def testGenerateIncomeStatement(self):
        """The simulator should correctly generate an income statement for a given year with a company with a set list of projects"""
        self.assertEqual(0,1)

    
