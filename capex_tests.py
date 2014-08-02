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
        kwargs = {'cost':100.0, 'basis_date':start, 'new_date':finish}
        self.assertRaises(pf.BadDateError, es.escalate, **kwargs)
        start = finish
        finish = 234.0
        kwargs = {'cost':100.0, 'basis_date':start, 'new_date':finish}
        self.assertRaises(pf.BadDateError, es.escalate, **kwargs)

    def testBadEscalationCost(self):
        """Cost should be a non-zero value"""
	start = dt.datetime(2010,01,01)
        finish = dt.datetime(2012,01,01)
        es = pf.NoEscalationEscalator()
        kwargs = {'cost':'moop', 'basis_date':start, 'new_date':finish}
        self.assertRaises(pf.BadValue, es.escalate, **kwargs)

        
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
	start = dt.datetime(2010,01,01)
        finish = dt.datetime(2011,01,01)
        es = pf.InflationRateEscalator()
	rate = 'poop'
	self.assertRaises(pf.BadValue, es.escalate, rate, kwargs = {'cost':100.0, 'basis_date':start, 'new_date':finish})
	rate = 0.15
	self.assertRaises(pf.MissingInfoError, es.escalate, rate, kwargs = {'cost':100.0, 'new_date':finish})
	self.assertRaises(pf.MissingInfoError, es.escalate, rate, kwargs = {'cost':100.0, 'basis_date':start})
	self.assertRaises(pf.MissingInfoError, es.escalate, rate, kwargs = {'basis_date':start, 'new_date':finish})
      

    def testProperEscalationCPI(self):
        """Escalation using the CPI index should be properly calculated"""
        self.assertEqual(0,1)


    def testCreateCapitalExpense(self):
        """Testing correct setting of a capital expense"""
	IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM, size_basis = uv.UnitVal(100, 'lb/hr') )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'MACRS')
        self.assertEqual(capex1.name, "Feeder")
       
        self.assertEqual(capex1.description,"Biomass feeder")
        self.assertEqual(capex1.tag,"F-1401")
        self.assertEqual(capex1.quote_basis,QB)
	self.assertEqual(capex1.depreciation_type, 'MACRS') 
        


    def testBadCapitalCostInput(self):
        """Bad input types or values should throw a BadCapitalCostInput error on initialization"""
        #String based inputs won't throw errors, so won't test for errors on tag, name, or description
	tag = 'a'
	name = 'something'
	IM = pf.FactoredInstallModel(1.6)
	QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor", scaling_method = 'linear', installation_model = IM, size_basis = uv.UnitVal(100, 'lb/hr') )
	self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, tag, name, 'poop', 'jimmy', None, 'StraightLine') 

        self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, tag, name, 'poop', QB, None, 'MoFarter') 
	self.assertRaises(pf.BadEscalatorTypeError, pf.CapitalExpense, tag, name, 'poop', QB, 'WhoSays', 'StraightLine') 

       

       
    
    def testSetQuoteBasis(self):
        """Testing correct setting of quote basis"""
	capex1 = pf.CapitalExpense(name = "feeder", tag = 'F-401')
	IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), size_basis = uv.UnitVal(100, 'lb/hr'), source = "Vendor", scaling_method = 'linear', installation_model = IM)
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
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), size_basis = uv.UnitVal(100, 'lb/hr'), source = "Vendor", scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        year1 = dt.datetime(2012,1,1)
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v)
        

    def testCorrectlyBuildDeprecSchedMACRS(self):
        """Testing if a MACRS depreciation sheet is correctly created"""
       
        IM = pf.FactoredInstallModel(1.0)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'MACRS')
        
        year1 = dt.datetime(2012,1,1)

	date1 = dt.datetime(2012,01,01)
	date2 = dt.datetime(2014,06,05)
	date3 = dt.datetime(2018,04,03)
	date4 = dt.datetime(2020,8, 5)
	date5 = dt.datetime(2026,03,04)
	date6 = dt.datetime(2032,10,23)
	length = 3
        #Need to do this for ALL valid MACRS lengths
        #spot check the values that are charged
	dates = np.array([date1,date2])
	values = np.array([128.402459, 57.21123288])
                
        capex1.build_depreciation_schedule(starting_period = year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

	length = 5
	dates = np.array([date1,date2])
	values = np.array([77.04918033, 74.16986301])
	capex1.build_depreciation_schedule(starting_period=year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

	length = 7
	dates = np.array([date1,date2, date3])
	values = np.array([55.05163934, 67.56410959, 34.49671233])
	capex1.build_depreciation_schedule(starting_period=year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

	length = 10
	dates = np.array([date1,date2,date3,date4])
	values = np.array([38.52459016,55.62739726, 25.30273973, 25.27213115])
	capex1.build_depreciation_schedule(starting_period=year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

	length = 15
	dates = np.array([date1,date2,date3,date4,date5])
	values = np.array([19.2622958,33.02876712, 22.79178082, 22.76803279, 22.83041096])
	capex1.build_depreciation_schedule(starting_period=year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

	length = 20
	dates = np.array([date1,date2,date3,date4,date5,date6])
	values = np.array([14.44672131, 25.79334247, 18.88241096, 17.18967213, 17.23676712, 8.594836066])
	capex1.build_depreciation_schedule(starting_period=year1, length=length)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)
	



    def testCorrectlyBuildDeprecSchedSchedule(self):
        """Testing if a Schedule depreciation sheet is correctly created"""
       
        IM = pf.FactoredInstallModel(1.0)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'Schedule')
              
        year1 = dt.datetime(2012,1,1)
	rng = pd.date_range(year1, periods = 10*365, freq = 'D')
        sched = pd.DataFrame(index = rng, data = {'depreciation':np.zeros(10*365)})
	date1 = dt.datetime(2015,3,28)
	sched['depreciation'][date1] = 0.95
	date2 = dt.datetime(2018,6,2)
	sched['depreciation'][date2] = 0.05


        length = 10
        dates = np.array([date1, date2, dt.datetime(2020,03,2)])
	       
        values = np.array([141000.0*0.95, 141000*0.05, 0.00])
        
        capex1.build_depreciation_schedule(year1, length, schedule=sched)
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex1.depreciation_schedule.value(date),v,4)

    def testBadDepreciationInputs(self):
        """Test that invalid inputs to the depreciation functions throw proper errors"""
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
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
        
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", depreciation_type = 'StraightLine')
       
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length)
        
   
    def testTICCorrectCalculation(self):
        """Test that TIC is correctly calculated for all supported methods"""
        IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        self.assertEqual(capex1.TIC(dt.datetime(2014,01,01)), 141000.0*1.6)

        IM = pf.FixedInstallModel(100000.0)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2012,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM )
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine')
        
        self.assertEqual(capex1.TIC(dt.datetime(2014,01,01)), 141000.0+100000.0)

        #Need one that tests escalation here
        
	IM = pf.FactoredInstallModel(1.6)
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2009,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'), scaling_method = 'linear', installation_model = IM)
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", quote_basis = QB, depreciation_type = 'StraightLine', escalation_type = "InflationRate" )
        
        self.assertAlmostEqual(capex1.TIC(dt.datetime(2011,01,01), rate = 0.05), 141000.0*1.6*1.05*1.05)

    def testTICUnderdefined(self):
        """Test that the Capex TIC function throws the proper errors when the Capital Expense is underdefined"""
	IM = pf.FactoredInstallModel(1.6)        
	QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor", size_basis = uv.UnitVal(100, 'lb/hr'))
	
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", depreciation_type = 'StraightLine')
        self.assertRaises(pf.BadCapitalTICInput, capex1.TIC, dt.datetime(2015,01,01))
        

    def testCostLayoutScheduleFixedDate(self):
        """Test that the Capex can calculate its own layout schedule (with and without escalation) on a Fixed Date"""
        
        ##!!##HERE##!!##
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        date = dt.datetime(2012,1,1)
        schedule = capex1.calc_investment_schedule(date)  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testCostLayoutScheduleFixedSchedule(self): 
        """Test that the Capex can calculate its own layout schedule (with no escalation) on a Fixed Schedule"""
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        #set_schedule = CostSchedule()
        schedule = capex1.calc_investment_schedule(set_schedule)  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testCostLayoutScheduleFixedPeriodInterval(self):
        """Test that the Capex can calculate its own layout schedule (with no escalation) on a Fixed Interval"""
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        start_date = dt.datetime(2012,1,1)
        end_date = dt.datetime(2014,1,1)
        schedule = capex1.calc_investment_schedule(start_date = start_date, end_date = end_date, period = 'monthly')  #escalation implied as "off" when None
        #schedule_ck = CostSchedule() dataframe object not yet implemented
        self.assertEqual(schedule, schedule_ck)

    def testBadCapitalCostScheduleInput(self):
        """Test that we get the appropriate errors when inputs are invalid or underdefined"""
        QB = pf.QuoteBasis(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
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
