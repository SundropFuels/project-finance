"""capex_tests.py
Unit tests for Project Finance program
Chris Perkins
2012-04-17

split out 2014-07-23
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


class CapitalExpenseTests(unittest.TestCase):
    
    def testProperEscalationNone(self):
        """Default esclator should return the same value on escalation"""
        start = dt.datetime(2010,01,01)
        finish = dt.datetime(2012,01,01)
        es = pf.NoEscalationEscalator()
        val = es.escalate(cost = 100.0, basis_date = start, new_date = finish)
        self.assertEqual(100.0, val)

    def testBadEscalationDates(self):
        """Not passing in proper dates should throw an error"""
        start = 'poop'
	finish = dt.datetime(2012,01,01)
        es = pf.NoEscalationEscalator()
        self.assertRaises(pf.BadDateError, es.escalate, 100.0, start, finish)
        start = finish
        finish = 234.0
        self.assertRaises(pf.BadDateError, es.escalate, 100.0, start, finish)

    def testBadEscalationCost(self):
        """Cost should be a non-zero value"""
	start = dt.datetime(2010,01,01)
        finish = dt.datetime(2012,01,01)
        es = pf.NoEscalationEscalator()
        self.assertRaises(pf.BadValue, es.escalate, 'moop', start, finish)

        
    def testProperEscalationInflationRate(self):
        """Test whether an inflation rate is properly escalated"""
        start = dt.datetime(2010,01,01)
        finish = dt.datetime(2011,01,01)
        es = pf.InflationRateEscalator()
        val = es.escalate(rate = 0.015, cost = 100.0, basis_date = start, new_date = finish)
        actual = 100.0*(1+0.015)
        self.assertAlmostEqual(val,actual)
        finish = dt.datetime(2012,06,25)
        val = es.escalate(rate = 0.015, cost = 100.0, basis_date = start, new_date = finish)
        r = (np.power(1.015,1/365.0)-1)
        actual = 100.0 * (1+r)**906
        self.assertAlmostEqual(val, actual)

    def testBadEscalationRate(self):
        """Rate should be non-zero, or throw an error"""
        self.assertEqual(0,1)

    def testProperEscalationCPI(self):
        """Escalation using the CPI index should be properly calculated"""
        self.assertEqual(0,1)


    def testCreateCapitalExpense(self):
        """Testing correct setting of a capital expense"""
	IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'MACRS')
        self.assertEqual(capex1.name, "Feeder")
        self.assertEqual(capex1.uninstalled_cost, 141000.0)
        self.assertEqual(capex1.description,"Biomass_feeder")
        self.assertEqual(capex1.tag,"F-1401")
        self.assertEqual(capex1.quote_basis,QB)
	self.assertEqual(capex1.depreciation_type, 'MACRS') 
        


    def testBadCapitalCostInput(self):
        """Bad input types or values should throw a BadCapitalCostInput error on initialization"""
        #First test that minimum amount of items have been defined (name and tag)
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)

        #Now test that the wrong types for the various arguments raise the error
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)

        #Now test that invalid values for size basis (i.e. <0) or for depreciation type raise errors
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)
        self.assertEqual(1,0)

       
    
    def testSetQuoteBasis(self):
        """Testing correct setting of quote basis"""
	capex1 = pf.CapitalExpense(name = "feeder", tag = 'F-401')
	IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
        capex1.set_quote_basis(QB)
        self.assertEqual(capex1.quote_basis, QB)

    def testBadQuoteBasis(self):
        """Non QB quote basis through throw a BadCapitalCostInput error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        basis = 'sss'
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_quote_basis, basis)

    def testSetDepreciationType(self):
        """Testing correct setting of the depreciation type"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        depreciation_types = ['StraightLine', 'MACRS', 'Schedule', 'NonDepreciable']
        for t in depreciation_types:
            capex1.set_depreciation_type(t)
            self.assertEqual(capex1.depreciation_type, t)

    def testBadDepreciationtype(self):
        """An unsupported depreciation type should throw an error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        #First test a problem with a non-string type
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_depreciation_type, 3.4)
        #Now test a non-supported type
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_depreciation_type, 'random-turtles')


    def testAddCommentCorrectly(self):
        """Test that a comment is correctly added"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = 'f-101')
        capex1.add_comment("K-tron KCLKT20")
        capex1.add_comment("Bought from ebay")
        self.assertEqual(capex1.comments, ['K-tron KCLKT20','Bought from ebay'])

    def testCommentErrorNotString(self):
        """A non-string comment should raise an error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        self.assertRaises(pf.ProjFinError, capex1.add_comment, 6)
    
    
    def testCorrectlyBuildDeprecSchedSL(self):
        """Testing if a straight-line depreciation sheet is correctly created"""
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        year1 = dt.datetime(2012,1,1)
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)


    def testCorrectlyBuildDeprecSchedMACRS(self):
        """Testing if a MACRS depreciation sheet is correctly created"""
       
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'MACRS')
        
        year1 = dt.datetime(2012,1,1)
        length = 10
        #Need to do this for ALL valid MACRS lengths
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0          #This is wrong, and it needs to be updated to the actual value set
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)

    def testCorrectlyBuildDeprecSchedSchedule(self):
        """Testing if a Schedule depreciation sheet is correctly created"""
       
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'Schedule')
              
        year1 = dt.datetime(2012,1,1)
        length = 10
        schedule = pf.DepreciationSchedule() #This still needs to be implemented to work correctly
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0          #This is wrong, and it needs to be updated to the actual value set
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)

    def testBadDepreciationInputs(self):
        """Test that invalid inputs to the depreciation functions throw proper errors"""
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        #Test that a bad length throws an error
        
        length = 'six'
        year1 = dt.datetime(2012,1,1)
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length)
        length = -5
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length)
        #Test that a bad initial year throws an error
        
        year1 = 'poop'
        length = 10
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length)
        
        #Fail on underdefined inputs -- this will currently be broken
        
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)

        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB)
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
   
    def testTICCorrectCalculation(self):
        """Test that TIC is correctly calculated for all supported methods"""
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        self.assertEqual(capex1.TIC(dt.datetime(2014,01,01)), 141000.0*1.6)

        IM = pf.FixedInstallModel(100000.0)
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        self.assertEqual(capex1.TIC(dt.datetime(2014,01,01)), 141000.0+100000.0)

        #Need one that tests escalation here
        self.assertEqual(0,1)

    def testTICUnderdefined(self):
        """Test that the Capex TIC function throws the proper errors when the Capital Expense is underdefined"""
	IM = pf.FactoredInstallModel(1.6)        
	QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", depreciation_type = 'StraightLine')
        self.assertRaises(pf.BadCapitalTICInput, capex1.TIC)
        

    def testCostLayoutScheduleFixedDate(self):
        """Test that the Capex can calculate its own layout schedule (with and without escalation) on a Fixed Date"""
        
        ##!!##HERE##!!##
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        date = dt.datetime(2012,1,1)
        schedule = capex1.calc_investment_schedule(date)  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testCostLayoutScheduleFixedSchedule(self): 
        """Test that the Capex can calculate its own layout schedule (with no escalation) on a Fixed Schedule"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        #set_schedule = CostSchedule()
        schedule = capex1.calc_investment_schedule(set_schedule)  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testCostLayoutScheduleFixedPeriodInterval(self):
        """Test that the Capex can calculate its own layout schedule (with no escalation) on a Fixed Interval"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        start_date = dt.datetime(2012,1,1)
        end_date = dt.datetime(2014,1,1)
        schedule = capex1.calc_investment_schedule(start_date = start_date, end_date = end_date, period = 'monthly')  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testBadCapitalCostScheduleInput(self):
        """Test that we get the appropriate errors when inputs are invalid or underdefined"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        start_date = dt.datetime(2012,1,1)
        end_date = dt.datetime(2014,1,1)
        self.assertRaises(pf.BadCapitalCostScheduleInput, 'meep')
        #self.assertRaises(pf.BadCapitalCostScheduleInput  Need definition for kwargs to do errors for bad inputs for the fixed period-interval
        #underdefined rules
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalCostScheduleInput, start_date)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalCostScheduleInput, start_date)


if __name__ == "__main__":
    unittest.main()
