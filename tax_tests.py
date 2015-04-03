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
import dataFrame_pd as df
import copy
import UnitValues as uv
import company_tools as ct
import pandas as pd
import datetime as dt
from pandas.tseries.offsets import DateOffset


class TaxTests(unittest.TestCase):
    
    
    def testTax(self):
        """Testing correct creation of a base tax object"""
	#basis should be a dataframe with a timeseries index and an 'income' column
	#deductions should be a dataframe with multiple columns corresponding to allowable deductions
	#credits should be a list of tax credit objects, which will use the revenue and tax itself to determine itself
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	#need to add and create the tax credits
	t = pf.Tax(name = 'fed1', basis = b, deductions = d, credits = c, freq = 'Q')
	self.assertEqual(t.name, 'fed1')
	self.assertEqual(t.basis, b)
	self.assertEqual(t.deductions, d)
	self.assertEqual(t.credits, c)
	self.assertEqual(t.freq, 'Q')		#taxes roll up all of the contributions during their period -- how does this work on an accrual basis?


    def testBadTaxInputs(self):
	"""Tax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = 'a'
	

	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['credits'] = ['a', 'b']
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	#NEED TO PUT IN CORRECT CREDITS HERE###!!!###, OW WILL THROW THE ERROR BUT BE WRONG
	kwargs['credits'] = fart  #purposely throwing an error here

	kwargs['name'] = 324
	self.assertRaises(pf.BadTaxInputerror, pf.Tax, **kwargs)
	kwargs['name'] = 'state'

	kwargs['basis'] = 'meep'
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['basis'] = df.DataFrame(index = dates)
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['basis'] = b

	kwargs['deductions'] = 'meep'
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['deductions'] = d


    def testFractionalTax(self):
	"""Testing correct creation of a fractional tax"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	t = pf.FractionalTax(rate = 0.35, **kwargs)

	self.assertEqual(t.rate, 0.35)
	self.assertEqual(t.basis, b)	#spot check for derived reach-through

    def testBadFractionalTaxInputs(self):
	"""Fractional tax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = 'beef'

	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)

    def testGraduatedFractionalTax(self):
	"""Testing correct creation of a graduated tax"""
	self.assertTrue(False)

    def testBadGraduatedFractionalTaxInputs(self):
	"""GraduatedFractionalTax should throw an error on bad inputs"""
	self.assertTrue(False)

    def testFixedTax(self):
	"""Testing creation of a fixed tax"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	t = pf.FixedTax(tax = 10000.0, **kwargs)

	self.assertEqual(t.tax, 10000.0)

    def testBadFixedTaxInputs(self):
	"""FixedTax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['tax'] = 't'
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)


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
