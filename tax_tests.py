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

    def testBuildTaxScheduleFractional(self):
	"""FractionalTax should correctly build its schedule"""
	self.assertTrue(False)

    def testBuildTaxScheduleBadInputs(self):
	"""A call to build_tax_schedule() should raise appropriate errors on bad input"""
	self.assertTrue(False)

    def testBuildTaxScheduleFixed(self):
	"""FixedTax should correctly build its schedule"""
	self.assertTrue(False)

    def testBuildTaxScheduleGraduatedFractional(self):
	"""GraduatedFractionalTax should correctly build its schedule"""
	self.assertTrue(False)

    def testBuildTaxScheduleGraduatedFixed(self):
	"""GraduatedFixedTax should correctly build its schedule"""
	self.assertTrue(False)


	"""Make sure that each of these cases handles capital loss carryback and carryforward accurately"""

class TaxCreditTests(unittest.TestCase):

    def createTaxCredit(self):
	"""Should correctly create a tax credit"""
	self.assertTrue(False)

	#should each tax credit simply be a wrapper around a tax, with a -1 multiple on the taxes?
	#I think so, but each credit should in turn be owned by a tax, so that we can handle refundable vs. non-refundable tax credits



    def createTaxCreditBadInputs(self):
	"""TaxCredit should throw an error when given a bad input"""
	self.assertTrue(False)

    def testBuildScheduleCorrectly(self):
	"""TaxCredit should correctly build its own schedule"""
	self.assertTrue(False)


class TaxManagerTests(unittest.TestCase):
    def testCreateTaxManager(self):
	"""TaxManager objects should be correctly initialized"""
        self.assertTrue(False)

    def testAddRevenueStream(self):
	"""TaxManager should correctly add a revenue stream and associate a tax with it"""
	self.assertTrue(False)

    def testAddTax(self):
	"""TaxManager should correctly add a tax"""
	self.assertTrue(False)

    def testAggregateTaxes(self):
	"""TaxManager should correctly aggregate the taxes and return a tax column"""
	self.assertTrue(False)

    def testAggregateTaxesDetailed(self):
	"""TaxManager should correctly aggregate the taxes and return a detailed tax dataframe"""
	self.assertTrue(False)

    """Want cases for foreign taxes with cross credits, N-sum tax carryover, etc."""





if __name__ == "__main__":
    unittest.main()
