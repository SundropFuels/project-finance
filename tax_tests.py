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
	b['income'][np.logical_and(b.index >= dt.datetime(2016,01,01), b.index < dt.datetime(2017,01,01))] = b['income'] - 250.0
	b['income'][np.logical_and(b.index >= dt.datetime(2017,01,01), b.index < dt.datetime(2018,01,01))] = b['income'] - 140.0
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
	taxes = [0.00, 0.00, 2.01619, 38.41152839,39.93110896,46.39298181]

	for date, tax in zip(check_dates, taxes):
	    self.assertAlmostEqual(t.schedule.loc[date,'tax'],tax,3)

    def testBuildTaxScheduleUnderdefined(self):
	"""A call to build_tax_schedule() should raise appropriate errors on underdefined input"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
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
	
	
	kwargs['rate'] = None
	t = pf.FractionalTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	t = pf.GraduatedFractionalTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)


	kwargs['rate'] = None
	t = pf.FixedTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)
	t = pf.GraduatedFixedTax(**kwargs)
	self.assertRaises(pf.TaxUnderdefinedError, t.build_tax_schedule)



    def testBuildTaxScheduleFixed(self):
	"""FixedTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
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
	    self.assertAlmostEqual(t.schedule.loc[date,'tax'], tax, 3)

    def testBuildTaxScheduleGraduatedFractional(self):
	"""GraduatedFractionalTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = {0:0.10, 25000.0:0.25, 35000.0:0.35}


	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['basis'] = b
	kwargs['deductions'] = d
	kwargs['credits'] = None
	kwargs['rate'] = r
	t = pf.GraduatedFractionalTax(**kwargs)
	t.build_tax_schedule()


	check_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2020,11,22), dt.datetime(2024,12,31)]
	taxes = [12.911873,15.296399,19.837197,26.220554]


	for date, tax in zip(check_dates, taxes):
	    self.assertAlmostEqual(t.schedule.loc[date,'tax'],tax,3)

    def testBuildTaxScheduleGraduatedFixed(self):
	"""GraduatedFixedTax should correctly build its schedule"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	b['income'][np.logical_and(b.index < dt.datetime(2017,01,01), b.index >= dt.datetime(2016,01,01))] = 25000.0/366.0
	b['income'][b.index > dt.datetime(2024,01,01)] = 0.0
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	d['depreciation'][np.logical_and(b.index < dt.datetime(2017,01,01), b.index >= dt.datetime(2016,01,01))] = 0.0
	d['interest'][np.logical_and(b.index < dt.datetime(2017,01,01), b.index >= dt.datetime(2016,01,01))] = 0.0
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
	taxes = [100.0/365.0, 100.0/366.0, 200.0/365.0, 10.0/366.0]

	for date, tax in zip(check_dates, taxes):
	    self.assertAlmostEqual(t.schedule.loc[date,'tax'], tax, 3)


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
	manager = pf.TaxManager()


        self.assertTrue(False)

    def testAddRevenueStream(self):
	"""TaxManager should correctly add a revenue stream"""
	manager = pf.TaxManager()
	
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	a2 = a1**2
	b = df.DataFrame({'income':a1, 'foreign_income':a2}, index = dates)

	manager.add_revenue(b, name = 'b', columns = ['income'])
	self.assertTrue((b['income'] == manager.revenue['b_income']).all())
	manager.add_revenue(b, name = 'c')
	self.assertTrue((b['income'] == manager.revenue['c_income']).all())
	self.assertTrue((b['foreign_income'] == manager.revenue['c_foreign_income'].all())

    def testAddDeductionStream(self):
	"""TaxManager should correctly add a depreciation stream"""
	manager = pf.TaxManager()
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')

	a = range(0,len(dates))
	a1 = np.array([100*1.01**i for i in a])
	a2 = a1**2
	b = df.DataFrame({'depreciation':a1, 'expenses':a2}, index = dates)
	manager.add_deduction(b, name = 'b', columns = ['depreciation','expenses'])
	self.assertTrue((b['depreciation'] == manager.deductions['b_depreciation']).all())
	self.assertTrue((b['expenses'] == manager.expenses['b_expenses']).all())
	manager.add_deduction(b, name = 'c')
	self.assertTrue((b['depreciation'] == manager.deductions['c_depreciation']).all())
	self.assertTrue((b['expenses'] == manager.deductions['c_expenses']).all())

    def testAddTax(self):
	"""TaxManager should correctly add a tax
	-Need to test adding an empty tax with the tax parameters, but no associated revenue, deductions, or credits
	-TaxManager has a factory feature that creates the appropriate tax object

        """
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
	kwargs['rate'] = r
	t = pf.FractionalTax(**kwargs)
	manager = TaxManager()
	manager.create_tax(kind = 'Fractional', **kwargs)

	self.assertEqual(t, manager.taxes['fed1'])

	manager=TaxManager()
	manager.create_tax(kind= 'Fractional', **kwargs)
	manager.add_revenue(b, name = 'US')
	manager.add_deductions(d, name = 'US')	

	manager.associate_revenue('fed1', ['US_income'])
	manager.associate_deductions('fed1', ['US_depreciation','US_interest'])

	kwargs2['name'] = 'fed1'
	kwargs2['rate'] = r
	kwargs2['basis'] = b
	kwargs2['deductions'] = d
	
	t = pf.FractionalTax(**kwargs)
	manager.build_taxes()	#This is an internal function that would not normally be externally called, but is here for test purposes
	self.assertEqual(t, manager.taxes['fed1'])

	#Test that fractional tax is created correctly
	

	#Test that tax is created correctly with associated income, depreciation columns


    def testAddTaxCredit(self):
	"""TaxManager should successfully add a TaxCredit object to its list of tax credits"""
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	kw2 = {'basis':b}
	cr = pf.TaxCredit(name = 'ITC', refundable = True, kind = 'Fixed', rate = 10000.0, **kw2)
	c = [cr]
	kwargs['name'] = 'ITC'
	kwargs['rate'] = 10000.00
	kwargs['refundable'] = True

	manager.create_tax_credit(kind = 'Fixed', **kwargs)
	manager.add_revenue(b, name = 'US')
	manager.associate_revenue('ITC', ['US_income'])
	
	manager.build_taxes()
	self.assertEqual(cr, manager.credits['ITC'])

    def testBadInputs(self):
	manager = TaxManager()

	#TaxCredit with the same name as a tax
	kwargs = {}
	kwargs['name'] = 'fed1'
	kwargs['rate'] = 0.35
	manager.create_tax(kind = 'Fractional', **kwargs)
	kwargs['kind'] = 'Fractional'
	self.assertRaises(pf.TaxManagerError, manager.create_tax_credit, **kwargs)
	#Tax with the same name as a tax
	self.assertRasies(pf.TaxManagerError, manager.create_tax, **kwargs)
	kwargs['name'] = 'ITC'
	manager.create_tax_credit(**kwargs)
	self.assertRaises(pf.TaxManagerError, manager.create_tax, **kwargs)

	#Kind of tax/tax credit that doesn't exist
	kwargs['kind'] = 'RegressiveFlatTax'
	self.assertRaises(pf.TaxManagerError, manager.create_tax, **kwargs)
	self.assertRaises(pf.TaxManagerError, manager.create_tax_credit, **kwargs)
	#Revenue stream not in the list
	kwargs = {}
	kwargs['tax'] = 'fed1'
	kwargs['revenue'] = ['poop']
	self.assertRaises(pf.TaxManagerError, manager.associate_revenue, **kwargs)
	kwargs = {}
	kwargs['tax'] = 'fed1'
	kwargs['deductions'] = ['kangaroo']


	#Deductions not in the list
	self.assertRaises(pf.TaxManagerError, manager.associate_deductions, **kwargs)

	#Credits not in the list
	kwargs = {}
	kwargs['tax'] = 'fed1'
	kwargs['credits'] = 'juicy'
	self.assertRaises(pf.TaxManagerError, manager.associate_credits, **kwargs)

	#Tax for deductions not in the list
	kwargs = {}
	kwargs['tax'] = 'fed1'
	kwargs['deductible_taxes'] = ['fed2']
	self.assertRaises(pf.TaxManagerError, manager.associate_deductible_taxes, **kwargs)

    def testAggregateTaxesNoCrossDeduction(self):
	"""TaxManager should correctly aggregate the taxes and return a tax column"""


	#First case is not cross deductable
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	kw2 = {'basis':b}
	r2 = {0.0:0.1, 25000.0:0.25, 35000.0:0.35}

	kwargs = {}
	kwargs['name'] = 'fed'
	kwargs['rate'] = r

	manager = TaxManager(revenue = b, deductions = d)
	manager.create_tax(kind = 'Fractional', revenue = 'income', deductions = ['depreciation','interest'], **kwargs)	
	kwargs['rate'] = r2
	kwargs['name'] = 'fed2'
	manager.create_tax(kind = 'GraduatedFractional', revenue = 'income', deductions = ['depreciation','interest'],**kwargs)
	manager.build_tax_schedule()
	
	test_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2019,10,31), dt.datetime(2024,12,31)]
	fed1_test_vals = [17.2, 18.6977876448,20.5179592665,26.220554]
	fed2_test_vals = [12.911837, 15.296399, 18.30583,24.7813443226]
	agg_test_vals = [30.1118731645, 33.99418678,38.8237891985,51.0018986985]
	for td, f1tv, f2tv, atv in zip(test_dates, fed1_test_vals, fed2_test_vals, agg_test_vals):
		
		self.assertAlmostEqual(manager.schedule.loc[td,'fed1_tax'], f1tv,4)
		self.assertAlmostEqual(manager.schedule.loc[td,'fed2_tax'], f2tv,4)
		self.assertAlmostEqual(manager.schedule.loc[td,'tax'],atv,4)

    def testAggregateTaxesOneDDeduction(self):
	"""TaxManager should correctly aggregate the taxes and return a tax column"""

	#Second case is one-direction deductable
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	kw2 = {'basis':b}
	r2 = {0.0:0.1, 25000.0:0.25, 35000.0:0.35}

	kwargs = {}
	kwargs['name'] = 'fed'
	kwargs['rate'] = r

	manager = TaxManager(revenue = b, deductions = d)
	manager.create_tax(kind = 'Fractional', revenue = 'income', deductions = ['depreciation','interest'], **kwargs)	
	kwargs['rate'] = r2
	kwargs['name'] = 'fed2'
	manager.create_tax(kind = 'GraduatedFractional', revenue = 'income', deductions = ['depreciation','interest'],**kwargs)
	manager.associate_deductible_taxes('fed2', 'fed1')
	manager.build_tax_schedule()


	
	test_dates = [dt.datetime(2015,01,01), dt.datetime(2017,04,15), dt.datetime(2019,10,31), dt.datetime(2024,12,31)]
	fed1_test_vals = [17.2, 18.6977876448,20.5179592665,26.220554]
	fed2_test_vals = [8.611873165,10.13482314,11.90730403,17.42708386]
	agg_test_vals = [25.81187316,28.83261079,32.42526329,42.32842819]
	for td, f1tv, f2tv, atv in zip(test_dates, fed1_test_vals, fed2_test_vals, agg_test_vals):
		
		self.assertAlmostEqual(manager.schedule.loc[td,'fed1_tax'], f1tv,4)
		self.assertAlmostEqual(manager.schedule.loc[td,'fed2_tax'], f2tv,4)
		self.assertAlmostEqual(manager.schedule.loc[td,'tax'],atv,4)	

    def testAggregateTaxesCrossDeduction(self):
	"""TaxManager should correctly aggregate the taxes and return a tax column"""
	self.assertTrue(False)

	#Third case is reciprocally cross deductable
	dates = pd.date_range(dt.datetime(2015,01,01), dt.datetime(2025,01,01), freq = 'D')
	a = range(0,len(dates))
	a1 = np.array([100*1.0001**i for i in a])
	b = df.DataFrame({'income':a1}, index = dates)
	a2 = a1*.05
	a3 = a1*.03
	d = df.DataFrame({'depreciation':a2,'interest':a3}, index = dates)
	r = 0.35
	kw2 = {'basis':b}
	r2 = {0.0:0.1, 25000.0:0.25, 35000.0:0.35}

	kwargs = {}
	kwargs['name'] = 'fed'
	kwargs['rate'] = r

	manager = TaxManager(revenue = b, deductions = d)
	manager.create_tax(kind = 'Fractional', revenue = 'income', deductions = ['depreciation','interest'], **kwargs)	
	kwargs['rate'] = r2
	kwargs['name'] = 'fed2'
	manager.create_tax(kind = 'GraduatedFractional', revenue = 'income', deductions = ['depreciation','interest'],**kwargs)
	manager.associate_deductible_taxes('fed1',['fed2'])
	manager.associate_deductible_taxes('fed2',['fed1'])
	manager.build_tax_schedule()
	
	test_dates = []
	fed1_test_vals = []
	fed2_test_vals = []
	agg_test_vals = []
	for td, f1tv, f2tv, atv in zip(test_dates, fed1_test_vals, fed2_test_vals, agg_test_vals):
		
		self.assertEqual(manager.schedule.loc[td,'fed1_tax'], f1tv)
		self.assertEqual(manager.schedule.loc[td,'fed2_tax'], f2tv)
		self.assertEqual(manager.schedule.loc[td,'tax'],atv)






if __name__ == "__main__":
    unittest.main()
