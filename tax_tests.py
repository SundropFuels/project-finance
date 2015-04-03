"""tax_tests.py
Unit tests for tax objects in Project Finance program
Chris Perkins
2012-04-17

split out 2015-04-03
"""

import unittest
import ProjectFinance_daily as pf
import numpy as np
import unitConversion as uc
import dataFrame_v2 as df
import copy
import UnitValues as uv
import company_tools as ct
import pandas as pd
import datetime as dt
from pandas.tseries.offsets import DateOffset


class TaxTests(unittest.TestCase):
    
    
    def testTax(self):
        """Testing correct creation of a base tax object"""
	self.assertTrue(False)

    def testBadTaxInputs(self):
	"""Tax should throw an error on bad inputs"""
	self.assertTrue(False)

    def testFractionalTax(self):
	"""Testing correct creation of a fractional tax"""
	self.assertTrue(False)

    def testBadFractionalTaxInputs(self):
	"""Fractional tax should throw an error on bad inputs"""
	self.assertTrue(False)

    def testGraduatedFractionalTax(self):
	"""Testing correct creation of a graduated tax"""
	self.assertTrue(False)

    def testBadGraduatedFractionalTaxInputs(self):
	"""GraduatedFractionalTax should throw an error on bad inputs"""
	self.assertTrue(False)

    def testFixedTax(self):
	"""Testing creation of a fixed tax"""
	self.assertTrue(False)

    def testBadFixedTaxInputs(self):
	"""FixedTax should throw an error on bad inputs"""
	self.assertTrue(False)

    def testGraduatedFixedTax(self):
	"""Test creation of a graduated fixed tax"""
	self.assertTrue(False)

    def testBadGraduatedFixedTaxInputs(self):
	"""GraduatedFixedTax should throw an error on bad inputs"""
	self.assertTrue(False)



