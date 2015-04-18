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
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]
	#need to add and create the tax credits
	t = pf.Tax(name = 'fed1', basis = b, deductions = d, credits = c, freq = 'Q')
	self.assertEqual(t.name, 'fed1')
	for col in b.columns:
	    self.assertTrue((t.basis[col]==b[col]).all())
	for col in d.columns:
	    self.assertTrue((t.deductions[col]==d[col]).all())
	
	self.assertEqual(t.credits, c)
	#We are going to have all taxes be assessed on an annual basis, but accrued on the income basis


    def testBadTaxInputs(self):
	"""Tax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = 'a'
	

	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['credits'] = ['a', 'b']
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)

	kwargs['credits'] = c  #purposely throwing an error here

	kwargs['name'] = 324
	self.assertRaises(pf.BadTaxInputError, pf.Tax, **kwargs)
	kwargs['name'] = 'state'

	kwargs['basis'] = 'meep'
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
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]


	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	t = pf.FractionalTax(rate = 0.35, **kwargs)

	self.assertEqual(t.rate, {0.0:0.35})
	self.assertTrue((t.basis['income']==b['income']).all())	#spot check for derived reach-through

    def testBadFractionalTaxInputs(self):
	"""Fractional tax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = 'beef'

	self.assertRaises(pf.BadTaxInputError, pf.FractionalTax, **kwargs)

    def testGraduatedFractionalTax(self):
	"""Testing correct creation of a graduated tax"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {0:0.10, 25000.0:0.20, 35000.0:0.3}
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = r
	t = pf.GraduatedFractionalTax(**kwargs)
	self.assertEqual(t.rate, r)
	

    def testBadGraduatedFractionalTaxInputs(self):
	"""GraduatedFractionalTax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {10000.0:0.10, 25000.0:0.20, 35000.0:0.3}
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = r
	
	kwargs['rate'] = -112
	self.assertRaises(pf.BadTaxInputError, pf.GraduatedFractionalTax, **kwargs)
	kwargs['rate'] = 'p'
	self.assertRaises(pf.BadTaxInputError, pf.GraduatedFractionalTax, **kwargs)

    def testFixedTax(self):
	"""Testing creation of a fixed tax"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	t = pf.FixedTax(rate = 10000.0, **kwargs)

	self.assertEqual(t.rate, {0.0:10000.0})

    def testBadFixedTaxInputs(self):
	"""FixedTax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = 't'
	self.assertRaises(pf.BadTaxInputError, pf.FixedTax, **kwargs)


    def testGraduatedFixedTax(self):
	"""Test creation of a graduated fixed tax"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {0:0.10, 25000.0:100.0, 35000.0:200.0}
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = r
	t = pf.GraduatedFixedTax(**kwargs)
	self.assertEqual(t.rate, r)
	

    def testBadGraduatedFixedTaxInputs(self):
	"""GraduatedFixedTax should throw an error on bad inputs"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {15.0:0.10, 25000.0:100.0, 35000.0:200.0}
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = 'poon'
	self.assertRaises(pf.BadTaxInputError, pf.GraduatedFixedTax, **kwargs)	
	kwargs['rate'] = 234.4
	self.assertRaises(pf.BadTaxInputError, pf.GraduatedFixedTax, **kwargs)
	

    def testBuildTaxScheduleFractional(self):
	"""FractionalTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35

	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, kind = 'Fractional', rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c
	kwargs['rate'] = r
	t = pf.FractionalTax(**kwargs)
	t.build_tax_schedule()
	
	check_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2020,11,22), dt.datetime(2024,12,31)]
	taxes = [17.2,18.6977876448,21.3296606862,24.7813443226]

	for date, tax in zip(check_dates, taxes):
	    self.assertAlmostEqual(t.schedule.loc[date,'tax'],tax,4)


    def testBuildtaxScheduleFractionalCarryforward(self):
	"""Need to make sure that the losses are appropriately carried forward"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	b['income'][np.logical_and(b.index > dt.datetime(2016,01,01), b.index < dt.datetime(2017,01,01))] = b['income'] - 250.0
	b['income'][np.logical_and(b.index > dt.datetime(2017,01,01), b.index < dt.datetime(2018,01,01))] = b['income'] - 140.0
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	#NEED TO SET THE CARRYOVER AGENT -- IS THIS AN OBJECT IN ITS OWN RIGHT
	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = None
	kwargs['rate'] = r
	t = pf.FractionalTax(**kwargs)
	t.build_tax_schedule()
	
	check_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2018,04,15), dt.datetime(2019,10,31), dt.datetime(2020,11,22), dt.datetime(2024,12,31)]
	taxes = [32.20, 0.00, 0.00, 24.56258,39.93110896,46.39298181]


	#key = lambda x: x.year
	#taxable['year'] = key(taxable.index)
	#taxable.agg = (taxable.groupby('year')).aggregate(np.sum)		#This is the aggregated dataframe
	#actually, the hazard here is that I am just repeating the data method, not testing whether it is correct
	for date, tax in zip(check_dates, taxes):
	    self.assertEqual(t.schedule.loc[date,'tax'],tax)

    def testBuildTaxScheduleUnderdefined(self):
	"""A call to build_tax_schedule() should raise appropriate errors on underdefined input"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = False, rate = 0.15, **kw2)
	c = [cr]

	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = c


	kwargs['basis'] = None
	t = pf.Tax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	kwargs['basis'] = b
	
	kwargs['deductions'] = None
	t = pf.Tax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	kwargs['deductions'] = d

	kwargs['credits'] = c
	t = pf.Tax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	kwargs['credits'] = c

	kwargs['rate'] = None
	t = pf.FractionalTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	t = pf.GraduatedFractionalTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	kwargs.remove('rate')

	kwargs['rate'] = None
	t = pf.FixedTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	t = pf.GraduatedFixedTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)



    def testBuildTaxScheduleFixed(self):
	"""FixedTax should correctly build its schedule"""
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
	kwargs['credits'] = None
	t = pf.FixedTax(rate = 10000.0, **kwargs)
	t.build_tax_schedule()

	check_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2018,04,15), dt.datetime(2019,10,31), dt.datetime(2020,11,22), dt.datetime(2024,12,31)]
	taxes = [10000.0/365.0, 10000.0/365.0, 10000.0/365.0, 10000.0/365.0, 10000.0/366.0, 10000.0/366.0]

	for date,tax in zip(check_dates,taxes):
	    self.assertEqual(t.schedule.loc[date,'tax'], tax)

    def testBuildTaxScheduleGraduatedFractional(self):
	"""GraduatedFractionalTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')	
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {0:0.10, 25000.0:0.20, 35000.0:0.3}


	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = None
	kwargs['rate'] = r
	t = pf.GraduatedFractionalTax(**kwargs)
	t.build_tax_schedule()

	check_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2020,11,22), dt.datetime(2024,12,31)]
	taxes = [12.911873,15.296399,19.781131,26.162247]


	for date, tax in zip(check_dates, taxes):
	    self.assertEqual(t.schedule.loc[date,'tax'],tax)

    def testBuildTaxScheduleGraduatedFixed(self):
	"""GraduatedFixedTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	b['income'][np.logical_and(b.index < dt.datetime(2017,01,01), b.index > dt.datetime(2016,01,01))] = 15000.0
	b['income'][b.index > dt.datetime(2024,01,01)] = 0.0
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {0:10.0, 25000.0:100.0, 35000.0:200.0}


	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = None
	kwargs['rate'] = r
	t = pf.GraduatedFixedTax(**kwargs)
	t.build_tax_schedule()

	check_dates = [dt.datetime(2015,01,01), dt.datetime(2016,05,05), dt.datetime(2017,06,30), dt.datetime(2024,04,05)]
	taxes = [200.0/365.0, 100.0/366.0, 200.0/365.0, 10.0/366.0]

	for date, tax in zip(check_dates, taxes):
	    self.assertEqual(t.schedule.loc[date,'tax'], tax)


class TaxCreditTests(unittest.TestCase):

    def createTaxCredit(self):
	"""Should correctly create a tax credit"""
	
	#Fractional
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	kwargs = {}
	kwargs['name'] = '15pct'
	kwargs['basis'] = b
	kwargs['kind'] = 'Fractional'
	c = pf.TaxCredit(refundable = False, rate = 0.15, **kwargs)
	t = pf.FractionalTax(rate = 0.15, **kwargs)
	self.assertEqual(c.credit, t)		#The underlying functionality in TaxCredit is built from tax
	self.assertTrue(not c.refundable)

	#Fixed

	kwargs['kind'] = 'Fixed'
	c = pf.TaxCredit(refundable = True, rate = 1005.0, **kwargs)
	t = pf.Fixedtax(rate = 1005.0, **kwargs)
	self.assertEqual(c.credit, t)
	self.assertTrue(c.refundable)

	#GraduatedFractional

	r = {0:0.10, 25000.0:0.20, 35000.0:0.3}

	kwargs['kind'] = 'GraduatedFractional'
	c = pf.TaxCredit(refundable = False, rate = r, **kwargs)
	t = pf.GraduatedFractionalTax(rate = r, **kwargs)
	self.assertEqual(c.credit, t)
	self.assertTrue(not c.refundable)

	#GraduatedFixed

	kwargs['kind'] = 'GraduatedFixed'
	c = pf.TaxCredit(refundable = True, rate = r, **kwargs)
	t = pf.GraduatedFixedTax(rate = r, **kwargs)
	self.assertEqual(c.credit, t)
	self.assertTrue(c.refundable)

    def createTaxCreditBadInputs(self):
	"""TaxCredit should throw an error when given a bad input"""
        dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	kwargs = {}
	kwargs['name'] = '15pct'
	kwargs['basis'] = b
	kwargs['rate'] = 0.15
	kwargs['refundable'] = 'bleh'
	kwargs['kind'] = 'Fractional'
	self.assertRaises(pf.BadTaxCreditInput, pf.FractionalTaxCredit, **kwargs)	
	kwargs['refundable'] = True
	kwargs['kind'] = 'bleh'
	self.assertRaises(pf.BadTaxCreditInput, pf.FractionalTaxCredit, **kwargs)

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
