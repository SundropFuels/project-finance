"""ProjectFinanceTest.py
Unit tests for Project Finance program
Chris Perkins
2012-04-17
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

class CapitalProjectTests(unittest.TestCase):
    """Tests for whether the implementation of a capital project is working correctly"""
    fp = pf.FinancialParameters()
    
    fp['Initial_period'] = dt.datetime(2012,1,1)
    fp['Startup_period']= None
    fp['Target_IRR'] = 0.15
    fp['Depreciation_type'] = 'straight-line'
    fp['Depreciation_length'] = 20
    fp['Analysis_period'] = 25
    fp['Plant_life'] = 20
    fp['Inflation_rate'] = 0.018
    fp['State_tax_rate'] = 0.06
    fp['Federal_tax_rate'] = 0.35
    fp['Design_cap'] = uv.UnitVal(1000000,'kg')
    fp['Cap_factor'] = 0.95
    fp['Capital_expense_breakdown'] = [0.25, 0.50, 0.25]
    fp['Startup_revenue_breakdown'] = 0.50
    fp['Startup_fixed_cost_breakdown'] = 0.75
    fp['Startup_variable_cost_breakdown'] = 0.50
    fp['Salvage_value'] = 400000.0
    fp['Decommissioning_cost'] = 400000.0

    def testInitiateCapitalProject(self):
        """Test that the capital project gets correctly initialized with the proper objects"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        self.assertTrue(isinstance(cap_proj.cf_sheet,pd.DataFrame))
        count = np.arange(0,9132)
        for i in range(len(count)):
            self.assertEqual(cap_proj.cf_sheet['Period'][i], count[i])
        self.assertEqual(cap_proj.cf_sheet.loc['2015-01-01']['Period'],1096) 

    def testFailOnFinParamNotSet(self):
        """Test whether the aggregator fails if financial parameters not set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW*hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))

    def testFailOnCapexNotSet(self):
        """Test whether the aggregator fails if capex not set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        #cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))

    def testFailOnVariableNotSet(self):
        """Test whether the aggregator fails if variable expenses not set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        #cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))

    def testFailOnFixedNotSet(self):
        """Test whether the aggregator fails if fixed expenses not set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        #cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))

    def testFailOnDebtNotSet(self):
        """Test whether the aggregator fails if debt portfolio not set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        #cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))
   
    def testSetPrices_Fixed(self):
        """The prices should be correctly calculated"""
        
        fp2 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp2)
        cap_proj.setPrices(mode = 'fixed', base_price = 1.0)
	dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        values = [1.025541, 1.064144, 1.101344, 1.222123, 1.50259]
        for date, val in zip(dates, values):
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Sales_price'], val,2)

        

    def testSetPrices_BadMode(self):
        """Giving an unrecognized inflation mode should raise an error"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        self.assertRaises(pf.ProjFinError, cap_proj.setPrices,3.0, 'poop')
        
    def testSetCapitalCosts(self):
        """Make sure the capital costs are correctly set in the cashflow sheet"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 1.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        #Set up tests
        ce = np.zeros(8401)
        dp = np.zeros(8401)
        for j in range(0, 366):
            ce[j] = 2730.25/366.0
        for j in range(366, 731):
            ce[j] = 5460.5/365.0
        for j in range(731, 1096):
            ce[j] = 2730.25/365.0
        
        for i in range(1096,8401):
            dp[i] = 921.0/(8401-1096)


        for i in range(len(ce)):
            self.assertEqual(cap_proj.cf_sheet['Capital_expenditures'][i], ce[i])
            self.assertEqual(cap_proj.cf_sheet['Depreciation'][i], dp[i])

    def testBadCapitalCosts(self):
        """Setting the self.capex item of CapitalProject to a non CapitalCosts object should raise an error"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 1.0)
        self.assertRaises(pf.ProjFinError,cap_proj.setCapitalCosts,"fart")  


    def testSetAnnualOutput(self):
        """Test that the Annual Output is correctly set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 1.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        values = [0.0, 475000/365.0, 950000/365.0, 950000/365.0, 950000/365.0]
    
     

        for date, val in zip(dates, values):
            
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Production'], val, 2)

    def testSetRevenue(self):
        """Ensure that the revenue items are correctly set"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
               
        dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        values = [0.0, 2769.69, 5733.022, 6361.734, 7821.699]
        

        for date, val in zip(dates, values):
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Sales'], val,2)
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Revenue'], val, 2)
        self.assertAlmostEqual(cap_proj.cf_sheet.loc['2035-01-01']['Salvage'], 400000, 2)

    def testSetVariableCosts(self):
        """The variable costs must be calculated correctly"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
       
        dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        values = [0.0, 549.7644591, 1137.965482, 1262.760309, 1552.553447]
    
     

        for date, val in zip(dates, values):

            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Variable_costs'],val,2)


    def testBadVariableCosts(self):
        """Trying to set the variable costs to a non-VariableCosts object should raise an error"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        self.assertRaises(pf.ProjFinError, cap_proj.setVariableCosts,4)

    def testSetFixedCosts(self):
        """The fixed costs column in the cash flow sheet must be calculated correctly"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        cap_proj._calcFixedCosts()
        dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        values = [0.0, 8859.63083/365.0, 12225.7862/365.0, 13566.5253/365.0, 16679.9316/365.0]
    
     

        for date, val in zip(dates, values):
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Fixed_costs'], val,2)


    def testBadFixedCosts(self):
        """Passing an object that is not a FixedCosts object to setFixedCosts should raise an error"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
        self.assertRaises(pf.ProjFinError,cap_proj.setFixedCosts,(0,3,"elephant"))

    def testSetDebt(self):
        """The debt columns in the cash flow sheet must be calculated correctly"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1.00000E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6.00000E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        cap_proj._calcFixedCosts()
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj._calcDebt()

                
        dates = ['2012-01-01', '2012-12-31', '2014-12-31', '2023-12-31']
        interest= [0.0, 800000, 763637.9245, 509007.4656]
        principal_paid = [0.0, 218522.0882, 254884.1637, 509514.6226]
        proceeds = [1E7, 0,0,0]

        for d, i, p, pro in zip(dates, interest, principal_paid, proceeds):

            self.assertEqual(pro, cap_proj.cf_sheet.loc[d]['Loan_proceeds'])
            self.assertAlmostEqual(i, cap_proj.cf_sheet.loc[d]['Interest'],2)
            self.assertAlmostEqual(p, cap_proj.cf_sheet.loc[d]['Principal_payments'],2)


    def testBadDebt(self):
        """Passing a non-DebtPortfolio object to setDebt should raise an error"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        cap_proj._calcFixedCosts()
        self.assertRaises(pf.ProjFinError, cap_proj.setDebt,"monster")

    def testSetOtherFinancials(self):
        """The balance of the cash flow sheet should be calculated correctly"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        cap_proj._calcCapitalCosts()
        cap_proj.setAnnualOutput()
        cap_proj.setRevenue()
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        cap_proj._calcVariableCosts()
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        cap_proj._calcFixedCosts()
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj._calcDebt()
        cap_proj.setOtherFinancials()

        #decom_costs = np.zeros(25)
        #decom_costs[23] = 400000
        #APPEARS TO BE WORKING, BUT REALLY NEED TO CHECK THESE AT ROLL UP OR WITH A FULL SIM FILE
        dates = ['2013-05-31', '2015-06-26', '2017-05-29', '2023-03-28', '2034-10-23']
        cost_of_sales = [0.0, 574.0374, 1171.460786, 1299.928871, 1598.25189]
        EBITDA = [0.0, 2195.653, 4561.562, 5061.805, 6223.447]
        pdi = [0.0, 1444.048, 3096.78745, 3721.82531, 5173.26114]
        ti = [0.0, 1443.921, 3096.661, 3721.699, 5173.135]
        tax = [0.0, 592.0078, 1269.631, 1525.897, 2120.985]
        #ncf = []    
     

        for date, cos, E, p, inc, tx in zip(dates, cost_of_sales, EBITDA, pdi, ti, tax):
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Cost_of_sales'], cos,2)
            self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['EBITDA'], E, 2)
            #self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Pre-depreciation_income'], p, 2)
            #self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Taxable_income'], inc, 2)
            #self.assertAlmostEqual(cap_proj.cf_sheet.loc[date]['Taxes'], tx, 2)
        
	"""
        for i in range(len(decom_costs)):

            self.assertAlmostEqual(decom_costs[i], cap_proj.cf_sheet['Decommissioning_costs'][i],2)
            self.assertAlmostEqual(cost_of_sales[i]/100.0, cap_proj.cf_sheet['Cost_of_sales'][i]/100.0,2)
            self.assertAlmostEqual(EBITDA[i]/100.0, cap_proj.cf_sheet['EBITDA'][i]/100.0,2)
            self.assertAlmostEqual(pdi[i]/100.0, cap_proj.cf_sheet['Pre-depreciation_income'][i]/100.0,2)
            self.assertAlmostEqual(ti[i]/1000.0, cap_proj.cf_sheet['Taxable_income'][i]/1000.0,1)
            self.assertAlmostEqual(tax[i]/1000.0, cap_proj.cf_sheet['Taxes'][i]/1000.0,1)
            self.assertAlmostEqual(ncf[i]/1000.0, cap_proj.cf_sheet['Net_cash_flow'][i]/1000.0,1)
        """

    def testAssembleFinancials(self):
        """Test whether the aggregator works as required"""
        fp1 = pf.FinancialParameters()
        
        fp1['Initial_period'] = dt.datetime(2012,1,1)
        fp1['Startup_period']= None
        fp1['Target_IRR'] = 0.15
        fp1['Depreciation_type'] = 'straight-line'
        fp1['Depreciation_length'] = 20
        fp1['Analysis_period'] = 25
        fp1['Plant_life'] = 20
        fp1['Inflation_rate'] = 0.015
        fp1['State_tax_rate'] = 0.00
        fp1['Federal_tax_rate'] = 0.35
        fp1['Design_cap'] = uv.UnitVal(187000000/0.95,'gal')
        fp1['Cap_factor'] = 0.95
        fp1['Capital_expense_breakdown'] = [0.3, 0.4, 0.3]
        fp1['Startup_revenue_breakdown'] = 0.50
        fp1['Startup_fixed_cost_breakdown'] = 0.75
        fp1['Startup_variable_cost_breakdown'] = 0.50
        fp1['Salvage_value'] = 140000000.0
        fp1['Decommissioning_cost'] = 140000000.0

        
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 600000000.0, installation_factor = 1.0)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 300000000.0, installation_factor = 2.0)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100000000.0, 'engineering_and_design':0.0, 'process_contingency':20000000.0, 'project_contingency':50000000.0, 'other':0.0, 'one-time_licensing_fees':0.0, 'up-front_permitting_costs':0.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 30000000.0
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.05,'$/kW/hr'), prod_required = uv.UnitVal(2.5,'kW*hr/gal'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(2.0,'$/MMBtu'), prod_required = uv.UnitVal(0.237,'MMBtu/gal'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 1500000
        fc['g_and_a'] = 6000000
        fc['other_fees'] = 0.0
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 2.5E8, term = 10, rate = 0.085, pmt_freq = 2, strt_period = dt.datetime(2012,1,1))
	loan2 = pf.Loan("loan2", principal = 3.5E8, term = 10, rate = 0.08, pmt_freq = 2, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        dp.add_loan(loan2)
        cap_proj.setDebt(dp)
        cap_proj.assembleFinancials(price = (2.6, 'fixed'))
        cap_proj.rollUpMonthly()
        cap_proj.rollUpAnnual()
        #create the three required dataframes from the files representing the daily, monthly, and annual cash flow sheets
        ##f_daily = open('daily_test.csv')
        ##f_monthly = open('monthly_test.csv')
        ##f_annual = open('annual_test.csv')

        ##daily_df = df.generateDataframeFromCSV(f_daily, col_for_rows = 'Date')
        ##monthly_df = df.generateDataframeFromCSV(f_monthly, col_for_rows = 'Date')
        ##annual_df = df.generateDataframeFromCSV(f_annual, col_for_rows = 'Date')
        
        print cap_proj.annual_cash_sheet
        for i in range(0,len(cap_proj.annual_cash_sheet)):
            
            print "Period: %s\tFixed_cost:%s" % (cap_proj.annual_cash_sheet['Period'][i], cap_proj.annual_cash_sheet['Interest'][i])
	"""
        for key in daily_df:
            self.assertAlmostEqual(daily_df[key], cap_proj.cf_sheet[key], 4)
        for key in monthly_df:
            self.assertAlmostEqual(monthly_df[key], cap_proj.monthly_cash_sheet[key], 4)

        for key in annual_df:
            self.assertAlmostEqual(annual_df[key], cap_proj.annual_cash_sheet[key], 4)

        self.assertEqual(daily_df.rows_dict, cap_proj.cf_sheet.rows_dict)
        self.assertEqual(monthly_df.rows_dict, cap_proj.cf_sheet.rows_dict)
        self.assertEqual(annual_df.rows_dict, cap_proj.cf_sheet.rows_dict)
        """
        self.assertEqual(1,2)
        #for i in range(len(ncf)):
        #    self.assertAlmostEqual(ncf[i]/1000.0, cap_proj.cf_sheet['Net_cash_flow'][i]/1000.0, 1)

    def testMissingCapex_simulate(self):
        pass

    def testMissingVC_simulate(self):
        pass

    def testMissingFC_simulate(self):
        pass

    def testCalcIRRandNPV(self):
        """Test whether the system correctly calculates the IRR and NPV"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 10000000.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 10000000.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        cap_proj.setCapitalCosts(capcosts)
        
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/kg'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/kg'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        cap_proj.setVariableCosts(VC)
        
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        cap_proj.setFixedCosts(fc)
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj.assembleFinancials(price = (2.0, 'fixed'))
        #print cap_proj.cf_sheet['Net_cash_flow']
        #cap_proj.printFinancials(filename = 'cfs.csv')
        self.assertEqual(1,0)
        #self.assertAlmostEqual(cap_proj.calcIRR(), 'what')
        #self.assertAlmostEqual(cap_proj.calcNPV(0.25),'what')

    

class FinancialParametersTests(unittest.TestCase):
    """All of the test cases for the Financial Parameters class"""

    def testCorrectAccess(self):
        """Tests if the FinancialParameters object correctly sets and accesses items"""
        fp = pf.FinancialParameters()
        fp['Initial_period'] = dt.datetime(2024,1,1)
        self.assertEqual(fp['Initial_period'],dt.datetime(2024,1,1))

    def testBadKey(self):
        fp = pf.FinancialParameters()
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Gonzo', 2)
        self.assertRaises(pf.ProjFinError, fp.__getitem__, 'Gonzo')

    def testBadValue(self):
        fp = pf.FinancialParameters()
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Initial_period', 'shwee-bang')
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Startup_period', 'shwee-bang')
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Capital_expense_breakdown', 2.0)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Depreciation_type', 43)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', 234)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', ('fart', 'gassy'))
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', (24.3, 123))
       


    def testCompleteness(self):

        fp = pf.FinancialParameters()
        key_list = ['Initial_period', 'Startup_period','Target_IRR', 'Depreciation_type', 'Depreciation_length', 'Analysis_period', 'Plant_life', 'Inflation_rate', 'State_tax_rate', 'Federal_tax_rate','Design_cap','Cap_factor','Capital_expense_breakdown','Startup_revenue_breakdown','Startup_fixed_cost_breakdown','Startup_variable_cost_breakdown','Salvage_value','Decommissioning_cost']
        #Take lists out of the FinancialParameters!#!
        for key in key_list:
            if key == 'Capital_expense_breakdown':
                fp[key] = [0.25, 0.25, 0.25, 0.25]
            elif key == 'Depreciation_type':
                fp[key] = 'straight-line'
            elif key == 'Design_cap':
                fp[key] = uv.UnitVal(453, 'gal')
            elif key == 'Initial_period':
                fp[key] = dt.datetime(2012,1,1)
            elif key == 'Startup_period':
                fp[key] = dt.datetime(2012,2,2) 
            else:
                fp[key] = 2.1


        self.assertEqual(fp.is_incomplete(), False)
        fp['Initial_period'] = None
        self.assertEqual(fp.is_incomplete(), True)



class CapitalExpenseTests(unittest.TestCase):
    

    def testCreateCapitalExpense(self):
        """Testing correct setting of a capital expense"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertEqual(capex1.name, "Feeder")
        self.assertEqual(capex1.uninstalled_cost, 141000.0)
        self.assertEqual(capex1.size_basis = uv.UnitVal(100.0, 'ton/day'))
        self.assertEqual(capex1.description,"Biomass_feeder")
        self.assertEqual(capex1.tag,"F-1401")
        self.assertEqual(capex1.quote_basis,QB)
	self.assertEqual(capex1.installation_model, IM)
        self.assertEqual(capex1.depreciation_type, 'MACRS') 
        self.assertEqual(1,0)  #NEED TO MAKE SURE THAT WE ADD THE SCALING FUNCTIONS IN QB, NOT IN THE GENERAL CAPITAL EXPENSE


    def testBadCapitalCostInput(self):
        """Bad input types or values should throw a BadCapitalCostInput error on initialization"""
        #First test that minimum amount of items have been defined (name and tag)
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)

        #Now test that the wrong types for the various arguments raise the error
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)

        #Now test that invalid values for size basis (i.e. <0) or for depreciation type raise errors
        ##!!## self.assertRaises(pf.BadCapitalCostInput, pf.CapitalExpense, ...)


    def testSetInstallationModel(self):
        """Testing correct setting of the installation factor"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = 'F-401')
        IM = pf.FactoredInstallModel(1.6)
        capex1.set_install_model(IM)
        self.assertEqual(capex1.installation_model, IM)


    def testBadInstallationModel(self):
        """Non-install model input should throw a BadCapitalCostInput error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        IM = "dd"
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_install_model, IM)

    def testSetSizeBasis(self):
        """Testing correct setting of size basis"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = 'F-401')
        basis = uv.UnitVal(100.0, 'lb/hr')
        capex1.set_size_basis(basis)
        self.assertEqual(capex1.size_basis, basis)

    def testBadSizeBasis(self):
        """Non UnitVal size basis through throw a BadCapitalCostInput error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        basis = 'sss'
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_size_basis, basis)

    def testSetQuoteBasis(self):
        """Testing correct setting of quote basis"""
	capex1 = pf.CapitalExpense(name = "feeder", tag = 'F-401')
        basis = pf.QuoteBasis(price = 454.2, date = dt.datetime(2014, 12, 1), source = "Vendor")
        capex1.set_quote_basis(basis)
        self.assertEqual(capex1.quote_basis, basis)

    def testBadQuoteBasis(self):
        """Non QB quote basis through throw a BadCapitalCostInput error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        basis = 'sss'
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_quote_basis, basis)

    def testSetDepreciationType(self):
        """Testing correct setting of the depreciation type"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        depreciation_types = ['straight-line', 'MACRS', 'schedule']
        for t in depreciation_types:
            capex1.set_depreciation_type(t)
            self.assertEqual(pf.depreciation_type, t)

    def testBadDepreciationtype(self):
        """An unsupported depreciation type should throw an error"""
        capex1 = pf.CapitalExpense(name = "feeder", tag = "f-101")
        #First test a problem with a non-string type
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_depreciation_type, 3.4)
        #Now test a non-supported type
        self.assertRaises(pf.BadCapitalCostInput, capex1.set_depreciation_type, 'random-turtles')





    def testAddCommentCorrectly(self):
        """Test that a comment is correctly added"""
        capex1 = pf.CapitalExpense(name = "feeder")
        capex1.add_comment("K-tron KCLKT20")
        capex1.add_comment("Bought from ebay")
        self.assertEqual(capex1.comments, ['K-tron KCLKT20','Bought from ebay'])

    def testCommentErrorNotString(self):
        """A non-string comment should raise an error"""
        capex1 = pf.CapitalExpense(name = "feeder")
        self.assertRaises(pf.ProjFinError, capex1.add_comment, 6)
    
    #DEPRECATED
    """
    def testSetCost(self):
        """Setting the cost later should return the correct value"""
        capex1 = pf.CapitalExpense(name = "Feeder")
        capex1.set_cost(141000,1.6)
        self.assertEqual(capex1.installed_cost, 225600)

    def testSetCostBadInput(self):
        pass

    """

    def testCorrectlyBuildDeprecSchedSL(self):
        """Testing if a straight-line depreciation sheet is correctly created"""
       
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
               
        year1 = dt.datetime(2012,1,1)
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length, escalation='off')
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)


    def testCorrectlyBuildDeprecSchedMACRS(self):
        """Testing if a MACRS depreciation sheet is correctly created"""
       
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        
        year1 = dt.datetime(2012,1,1)
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0          #This is wrong, and it needs to be updated to the actual value set
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length, escalation='off')
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)

    def testCorrectlyBuildDeprecSchedMACRS(self):
        """Testing if a Schedule depreciation sheet is correctly created"""
       
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
              
        year1 = dt.datetime(2012,1,1)
        length = 10
        schedule = pf.DepreciationSchedule() #This still needs to be implemented to work correctly
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 225600.0/3653.0          #This is wrong, and it needs to be updated to the actual value set
        values = np.array([value, value, value, value])
        
        capex1.build_depreciation_schedule(year1, length, escalation='off')
        for date, v in zip(dates,values):
            self.assertAlmostEqual(capex.depreciation_schedule.loc[date]['depreciation'],v)

    def testBadDepreciationInputs(self):
        """Test that invalid inputs to the depreciation functions throw proper errors"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        
        #Test that a bad length throws an error
        escalation = 'off'
        length = 'six'
        year1 = dt.datetime(2012,1,1)
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
        length = -5
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
        #Test that a bad initial year throws an error
        
        year1 = 'poop'
        length = 10
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
        #Test that a bad escalation function (anything other than 'off' for now) throws an error

        year1 = dt.datetime(2012,1,1)
        length = 10
        escalation = 4
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation=4)

        #Fail on underdefined inputs
        escalation = 'off'
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)

        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = pf.FactoredInstallModel(1.6), size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB)
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalDepreciationInput, capex1.build_depreciation_schedule, year1, length, escalation)
   
    def testTICCorrectCalculation(self):
        """Test that TIC is correctly calculated for all supported methods"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertEqual(capex1.TIC(), 141000.0*1.6)

        IM = pf.FixedInstallModel(100000.0)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertEqual(capex1.TIC(), 141000.0+100000.0)

    def testTICUnderdefined(self):
        """Test that the Capex TIC function throws the proper errors when the Capital Expense is underdefined"""
        QB = pf.CapitalQuote(price = 141000.0, date = dt.datetime(2010,01,01), source = "Vendor")
	IM = pf.FactoredInstallModel(1.6)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", size_basis = uv.UnitVal(100.0, 'ton/day'), quote_basis = QB, depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalTICInput, capex1.TIC)
        capex1 = pf.CapitalExpense(tag = "F-1401", name = "Feeder", description = "Biomass feeder", installation_model = IM, size_basis = uv.UnitVal(100.0, 'ton/day'), depreciation_type = 'MACRS')
        self.assertRaises(pf.BadCapitalTICInput, capex1.TIC)

    def testCostLayoutScheduleFixedDate(self):
        """Test that the Capex can calculate its own layout schedule (with no escalation) on a Fixed Date"""
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


class CapitalCostTests(unittest.TestCase):
    
    
    def testCorrectlyAddCapitalExpense(self):
        """Testing whether a capital expense is correctly added to the capital costs"""
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 141000.0, installation_factor = 1.6)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        self.assertEqual(capcosts.direct_capital[0].name, "feeder")
        self.assertEqual(capcosts.direct_capital[0].installed_cost, 225600)

    def testBadCapitalItem(self):
        """Testing if an error is raised when adding a non CapitalExpense to CapitalCosts"""
        capcosts = pf.CapitalCosts()
        self.assertRaises(pf.ProjFinError, capcosts.add_capital_item, "fart")

    def testCapitalCalculations(self):
        """Test whether the capital expenses are correctly summed and calculated"""
        #Need to fill in the values from my test spreadsheet here

        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 25000.0, installation_factor = 1.6)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100000.0, installation_factor = 2.2)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        self.assertAlmostEqual(capcosts.c_direct_capital(), 260000.0)
        self.assertAlmostEqual(capcosts.c_indirect_deprec_capital(), 721.0)
        self.assertAlmostEqual(capcosts.c_deprec_capital(), 260721.0)
        self.assertAlmostEqual(capcosts.c_indirect_nondeprec_capital(),10000.0)
        self.assertAlmostEqual(capcosts.c_total_capital(),270721)
        
    def testCorrectlyBuildDeprecSchedSL(self):
        """Testing if a straight-line depreciation sheet is correctly created"""
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        year1 = dt.datetime(2012,1,1)
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 921.0/3653.0
        values = np.array([value, value, value, value])
        
        capcosts.build_depreciation_schedule(year1, length, "straight-line")
        for date, v in zip(dates,values):
            self.assertEqual(capcosts.depreciation_schedule.loc[date]['depreciation'],v)
        
        

    def testCorrectlyBuildDeprecSchedMACRS(self):
        """Testing if a MACRS depreciation schedule is correctly created"""
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 100.0, installation_factor = 1)
        capex2 = pf.CapitalExpense(name = "POD", uninstalled_cost = 100.0, installation_factor = 1)
        capcosts = pf.CapitalCosts()
        capcosts.add_capital_item(capex1)
        capcosts.add_capital_item(capex2)
        deprec = {'site_prep':100.0, 'engineering_and_design':101.0, 'process_contingency':102.0, 'project_contingency':103.0, 'other':104.0, 'one-time_licensing_fees':105.0, 'up-front_permitting_costs':106.0}
        for (key,value) in deprec.items():
            capcosts.indirect_deprec_capital[key] = value
        capcosts.indirect_nondeprec_capital['Land'] = 10000
        year1 = dt.datetime(2012,1,1)
        #3 year MACRS
        length = 3
        
        values = {'2012':306.9693,'2013':409.3845, '2014':136.4001,'2015':68.2461}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        #Get annual totals to match to the given totals above
        
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            
            self.assertAlmostEqual(schedule.loc[year]['depreciation'],values[year])
	
        #5 year MACRS
        length = 5
        
        values = {'2012':184.2,'2013':294.72,'2014':176.832,'2015':106.0992,'2016':106.0992,'2017':53.0496}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            self.assertAlmostEqual(schedule['depreciation'][year],values[year])
        
	
        #7 MACRS
        length = 7
        years = np.array([2012,2013,2014,2015,2016,2017,2018,2019])
        values = {'2012':131.6109, '2013':225.5529, '2014':161.0829, '2015':115.0329, '2016':82.2453, '2017':82.1532, '2018':82.2453, '2019':41.0766}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            self.assertAlmostEqual(schedule['depreciation'][year],values[year])

        #10 year MACRS
        length = 10
        years = ['2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022']
        vals = [92.1,165.78,132.624,106.0992,84.9162,67.8777,60.3255,60.3255,60.4176,60.3255,30.2088]
        values = {y:v for (y,v) in zip(years, vals)}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            self.assertAlmostEqual(schedule['depreciation'][year],values[year])


        #15 year MACRS
        length = 15
        years = ['2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027']
        vals = [46.05,87.495,78.7455,70.917,63.8253,57.3783,54.3390,54.3390,54.4311,54.339,54.4311,54.3390,54.4311,54.3390,54.4311,27.1695]
        values = {y:v for (y,v) in zip(years, vals)}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            self.assertAlmostEqual(schedule['depreciation'][year],values[year])


        #20 year MACRS
        length = 20
        years = ['2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026', '2027', '2028','2029','2030','2031','2032']
        vals = [34.5375,66.48699,61.49517,56.89017,52.61673,48.67485,45.01848,41.64762,41.09502,41.08581,41.09502,41.0858100,41.09502,41.08581,41.09502,41.08581,41.09502,41.08581,41.09502,41.08581,20.54751]
        values = {y:v for (y,v) in zip(years, vals)}
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        schedule = capcosts.depreciation_schedule.resample('A', how = 'sum')
        for year in values:
            self.assertAlmostEqual(schedule['depreciation'][year],values[year])
        
        

    def testCorreclyCreateCapExpendSched(self):
        pass

class FixedCostTests(unittest.TestCase):

    
    def testBadFixedCost(self):
        """Trying to set a fixed cost not in the category should raise an error"""
        fc = pf.FixedCosts()
        self.assertRaises(pf.ProjFinError, fc.__setitem__, 'booyah', 34)
        

    def testTotalFixedCost(self):
        """Test whether the fixed costs are correctly totaled"""
        fc = pf.FixedCosts()
        fc['project_staff'] = 4500
        fc['g_and_a'] = 1000.56
        fc['other_fees'] = 5600.23
        self.assertAlmostEqual(fc.c_total_fixed_costs(),11100.79)

class VariableExpenseTests(unittest.TestCase):
    def testBadUnitCost(self):
        pass

    def testBadProdReq(self):
        pass

    def testBadAnnualCostProduction(self):
        pass       

        
    def testCorrectlyCalcAnnualCost(self):
        """Testing whether unit costs are properly set for variable expenses"""
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/gal'))
        self.assertAlmostEqual(ve1.annual_cost(uv.UnitVal(10000,'L')),440.28675393)

class VariableCostsTests(unittest.TestCase):
    def testAddVariableExpense(self):
        """Should correctly add a variable expense to the list"""
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'Jgal'))
        list1 = [ve1]
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        self.assertEqual(list1, VC.variable_exps)

    def testBadVariableExpense(self):
        """Passing an item that is not an instance of VariableExpense should raise an error"""
        ve1 = "meh"
        VC = pf.VariableCosts()
        self.assertRaises(pf.ProjFinError, VC.add_variable_exp, ve1)

    def testDelVariableExpense(self):
        """Should correctly remove a variable expense from the list"""
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/gal'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(1E7,'J/gal'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
	VC.del_variable_exp("Electricity")
        self.assertEqual(['Natural Gas'],VC.variable_exp_names())

    def testCalcTotalVC(self):
        """The total per production variable cost should be correctly calculated"""
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/gal'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(6E7,'J/gal'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        #The required amount of electricity + natural gas to make 1 L of gas is $0.104875888
        self.assertAlmostEqual(VC.c_total_VC('L'),0.104875888,5)


    def testCorrectVariableExpenseNames(self):
        """Should correctly generate the list of variable expense names"""
        ve1 = pf.VariableExpense(name = "Electricity", unit_cost = uv.UnitVal(0.06,'$/kW/hr'), prod_required = uv.UnitVal(1E7,'J/gal'))
        ve2 = pf.VariableExpense(name = "Natural Gas", unit_cost = uv.UnitVal(4.05,'$/MMBtu'), prod_required = uv.UnitVal(1E7,'J/gal'))
        VC = pf.VariableCosts()
        VC.add_variable_exp(ve1)
        VC.add_variable_exp(ve2)
        self.assertEqual(['Electricity','Natural Gas'],VC.variable_exp_names())

class LoanTests(unittest.TestCase):
    def testBadInputs(self):
        pass

    #NEED TO HAVE A BUNCH OF CHECKS HERE FOR BAD INPUT INTO THE MODEL


    def testCorrectlyGenerateScheduleAnnual(self):
        """Testing correct loan schedule generation for annual coupon payments"""
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_period = dt.datetime(2015,1,1))
        loan.generate_schedule()

        dates = np.array(['2015-12-31','2016-12-31','2017-12-31', '2023-12-31', '2034-12-31'])
        principal = np.array([671819.7116, 656434.0987, 639740.7086, 505183.688, 0.0])
        interest = np.array([58310, 57104.67549, 55796.89839, 45255.56497, 5678.962686])
        principal_paid = np.array([14180.29, 15385.61, 16693.39, 27234.72, 66811.33])
        
        for date, p, i, pp in zip(dates, principal, interest, principal_paid):
            
            self.assertAlmostEqual(loan.schedule.loc[date]['principal'],p,2)
            self.assertAlmostEqual(loan.schedule.loc[date]['interest'],i,2)
            self.assertAlmostEqual(loan.schedule.loc[date]['principal_payment'],pp,2)
        self.assertEqual(686000.0, loan.schedule.loc['2015-01-01']['cash_proceeds']) 
        

    def testCorrectlyGenerateScheduleBiAnnual(self):
        """Testing correct loan schedule generation for bi-annual coupon payments"""
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 2, strt_period = dt.datetime(2012,1,1))
        loan.generate_schedule()

        dates = np.array(['2012-06-30', '2012-12-31', '2013-06-30', '2016-06-30', '2021-12-31', '2027-06-30', '2031-12-31'])
        

        
        principal = np.array([679195.9854,672102.8002,664708.1546,613252.698,478052.294,264347.2912,0.0])
        interest = np.array([29155.0,28865.82938,28564.36901, 26466.66454,20954.89747, 12242.70311, 1465.955031])
        principal_paid = np.array([6804.015,7093.185,7394.646,9492.35,15004.12,23716.31,34493.06])
        
        for date, p, i, pp in zip(dates,principal,interest,principal_paid):
            
            self.assertAlmostEqual(loan.schedule.loc[date]['principal'],p,2)
            self.assertAlmostEqual(loan.schedule.loc[date]['interest'],i,2)
            self.assertAlmostEqual(loan.schedule.loc[date]['principal_payment'],pp,2)
        self.assertAlmostEqual(loan.schedule.loc['2012-01-01']['cash_proceeds'],686000,2)

class DebtPortfolioTests(unittest.TestCase):
    def testAddLoan(self):
        """DebtPortfolio must correctly add a loan to its set of loans"""
	loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_period = dt.datetime(2015,2,27))
	dp = pf.DebtPortfolio()
        dp.add_loan(loan)
        self.assertEqual(dp.loans[0],loan)

    def testBadLoan(self):
        """Adding a non-loan object to a debt portfolio should raise an error"""
        dp = pf.DebtPortfolio()
        self.assertRaises(pf.ProjFinError, dp.add_loan, "poop")

    def testRepeatedLoan(self):
        """Repeating a loan in the add list should raise an error"""
        dp = pf.DebtPortfolio()
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_period = dt.datetime(2015,1,1))
	dp.add_loan(loan)
	self.assertRaises(pf.ProjFinError, dp.add_loan, loan)

    def testDelLoan(self):
        """DebtPortfolio must correctly remove a loan from its set of loans"""
	loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_period = dt.datetime(2015,1,1))
	dp = pf.DebtPortfolio()
        dp.add_loan(loan)
        loan2 = pf.Loan("loan2", principal = 750000, term = 15, rate = 0.134, pmt_freq = 2, strt_period = dt.datetime(2017,3,15))
        dp.add_loan(loan2)
        dp.del_loan("loan1")
        self.assertEqual(dp.loans, [loan2])

    def testCIPcalc(self):
        """Must correctly calculate cash proceeds, interest, and principal for a loan"""
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_period = dt.datetime(2012,1,1))
        loan2 = pf.Loan("loan2", principal = 750000, term = 15, rate = 0.134, pmt_freq = 2, strt_period = dt.datetime(2012,1,1))
        #ensure correct cash, interest, principal in 2017 and in 2024
        #This test function needs to be completely re-written for the new CIP interface !!!
        r = pd.DatetimeIndex(['2012-01-01','2012-06-30','2012-12-31','2026-12-31','2028-06-30','2030-12-31'])
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        dp.add_loan(loan2)
        CIP = dp.CIP(r)
        cash = [1436000.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        interest = [0.0, 50250.0, 107998.6255, 31739.18825, 0.0, 10913.02968]
        pp = [0.0, 8378.723433, 23120.38631, 99379.8236, 0.0, 61577.2587308423]

        for d, c, i, p in zip(r, cash, interest, pp):
            self.assertAlmostEqual(CIP.loc[d]['cash_proceeds'], c, 3)
            self.assertAlmostEqual(CIP.loc[d]['interest'], i, 3)
            self.assertAlmostEqual(CIP.loc[d]['principal_payment'],p,3)        



        

if __name__ == "__main__":
    unittest.main()
