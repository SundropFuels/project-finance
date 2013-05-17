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


class CapitalProjectTests(unittest.TestCase):
    """Tests for whether the implementation of a capital project is working correctly"""
    fp = pf.FinancialParameters()
    
    fp['Initial_period'] = ct.FinDate(2012,1,1)
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
        self.assertTrue(isinstance(cap_proj.cf_sheet,df.Dataframe))
        count = np.arange(0,25)
        for i in range(len(count)):
            self.assertEqual(cap_proj.cf_sheet['Period'][i], count[i])
        self.assertEqual(cap_proj.cf_sheet.get_row(2015),{'Period':3}) 

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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        #cap_proj.setDebt(dp)
        self.assertRaises(pf.ProjFinError,cap_proj.assembleFinancials,(2.0, 'fixed'))
   
    def testSetPrices_Fixed(self):
        """The prices should be correctly calculated"""
        inflation_factor = [1,1.018,1.036324,1.054977832,1.073967433,1.093298847,1.112978226,1.133011834,1.153406048,1.174167356,1.195302368,1.216817811,1.238720532,1.261017501,1.283715816,1.306822701,1.330345509,1.354291729,1.37866898,1.403485021,1.428747752,1.454465211,1.480645585,1.507297206,1.534428555]
        ifs = np.array(inflation_factor)
        fp2 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp2)
        cap_proj.setPrices(mode = 'fixed', base_price = 1.0)
        for i in range(len(ifs)):
            self.assertAlmostEqual(ifs[i], cap_proj.cf_sheet['Sales_price'][i])


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
        ce = np.zeros(25)
        dp = np.zeros(25)
        ce[0] = 2730.25
        ce[1] = 5460.5
        ce[2] = 2730.25
        for i in range(3,23):
            dp[i] = 46.05


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
        AnnOut = np.zeros(25)
        
        AnnOut[3] = 475000
        for i in range(4,24):
            AnnOut[i] = 950000
        for i in range(len(AnnOut)):

            self.assertEqual(AnnOut[i], cap_proj.cf_sheet['Production'][i])

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
        sales = [0,0,0,1002228.94,2040538.123,2077267.809,2114658.6298,2152722.485,2191471.489,2230917.976,2271074.5,2311953.842,2353569.01,2395933.252,2439060.051,2482963.132,2527656.468,2573154.284,2619471.062,2666621.541,2714620.728,2763483.901,2813226.612,2863864.691,0.0]
        rev = copy.deepcopy(sales)
        rev[23] += 400000
        s = np.ones(25) * sales
        r = np.ones(25) * rev
        salv = np.zeros(25)
        salv[23] = 400000
        


        for i in range(len(s)):
            self.assertAlmostEqual(cap_proj.cf_sheet['Sales'][i], s[i],2)
            self.assertAlmostEqual(cap_proj.cf_sheet['Salvage'][i], salv[i],2)
            self.assertAlmostEqual(cap_proj.cf_sheet['Revenue'][i], r[i],2)

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
        tvc = np.array([0,0,0,198935.55,405032.79,412323.38,419745.20,427300.61,434992.02,442821.88,450792.67,458906.94,467167.26,475576.27,484136.65,492851.11,501722.43,510753.43,519946.99,529306.04,538833.55,548532.55,558406.14,568457.45,0])
        
        for i in range(len(tvc)):
            self.assertAlmostEqual(cap_proj.cf_sheet['Variable_costs'][i], tvc[i],1)


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
        fc = np.array([0,0,0,8783.32,11921.89,12136.48,12354.94,12577.33,12803.72,13034.19,13268.80,13507.64,13750.78,13998.29,14250.26,14506.76,14767.89,15033.71,15304.31,15579.79,15860.23,16145.71,16436.34,16732.19,0.0])
        
        

        for i in range(len(fc)):
            self.assertAlmostEqual(cap_proj.cf_sheet['Fixed_costs'][i], fc[i],2)


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
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj._calcDebt()

        

        proceeds = np.zeros(25)
        proceeds[0] = 1E7
        interest = np.array([800000,782518.23,763637.92,743247.19,721225.20,697441.45,671755.00,644013.63,614052.95,581695.42,546749.29,509007.47,468246.30,424224.23,376680.40,325333.07,269877.95,209986.42,145303.56,75446.08,0,0,0,0,0])
        principal = np.array([218522.09,236003.86,254884.16,275274.90,297296.89,321080.64,346767.09,374508.46,404469.13,436826.67,471772.80,509514.62,550275.79,594297.86,641841.68,693189.02,748644.14,808535.67,873218.53,943076.01,0,0,0,0,0])
        
        for i in range(len(proceeds)):

            self.assertEqual(proceeds[i], cap_proj.cf_sheet['Loan_proceeds'][i])
            self.assertAlmostEqual(interest[i], cap_proj.cf_sheet['Interest'][i],2)
            self.assertAlmostEqual(principal[i], cap_proj.cf_sheet['Principal_payments'][i],2)


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
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj._calcDebt()
        cap_proj.setOtherFinancials()

        decom_costs = np.zeros(25)
        decom_costs[23] = 400000
        cost_of_sales = np.array([0,0,0,207718.87,416954.67,424459.86,432100.13,439877.94,447795.74,455856.06,464061.47,472414.58,480918.04,489574.57,498386.91,507357.87,516490.31,525787.14,535251.31,544885.83,554693.78,564678.26,574842.47,985189.64,0])
        EBITDA = np.array([0,0,0,794510.07,1623583.45,1652807.95,1682558.50,1712844.55,1743675.75,1775061.91,1807013.03,1839539.26,1872650.97,1906358.69,1940673.14,1975605.26,2011166.15,2047367.15,2084219.75,2121735.71,2159926.95,2198805.64,2238384.14,2278675.05,0.00])
        pdi = np.array([-800000,-782518.23,-763637.92,51262.88,902358.25,955366.50,1010803.50,1068830.92,1129622.80,1193366.49,1260263.74,1330531.80,1404404.67,1482134.45,1563992.74,1650272.19,1741288.21,1837380.73,1938916.19,2046289.63,2159926.95,2198805.64,2238384.14,2278675.05,0])
        ti = np.array([-800000,-782518.23,-763637.92,51216.83,902312.20,955320.45,1010757.45,1068784.87,1129576.75,1193320.44,1260217.69,1330485.75,1404358.62,1482088.40,1563946.69,1650226.14,1741242.16,1837334.68,1938870.14,2046243.58,2159880.90,2198759.59,2238338.09,2278629.00,0])
        tax = np.array([0,0,0,20998.90,369948.00,391681.39,414410.55,438201.80,463126.47,489261.38,516689.25,545499.16,575787.04,607656.25,641218.14,676592.72,713909.28,753307.22,794936.76,838959.87,885551.17,901491.43,917718.62,934237.89,0])
        ncf = np.array([8978747.66,-1023982.59,-1021252.34,-245010.9168,235113.3597,242604.478,249625.8535,256120.6641,262027.1958,267278.4446,271801.6875,275518.0181,278341.8454,280180.3527,280932.9123,280490.4538,278734.7819,275537.8386,270760.9077,264253.7538,1274375.782,1297314.206,1320665.522,1344437.162,0])        
       

        for i in range(len(decom_costs)):

            self.assertAlmostEqual(decom_costs[i], cap_proj.cf_sheet['Decommissioning_costs'][i],2)
            self.assertAlmostEqual(cost_of_sales[i]/100.0, cap_proj.cf_sheet['Cost_of_sales'][i]/100.0,2)
            self.assertAlmostEqual(EBITDA[i]/100.0, cap_proj.cf_sheet['EBITDA'][i]/100.0,2)
            self.assertAlmostEqual(pdi[i]/100.0, cap_proj.cf_sheet['Pre-depreciation_income'][i]/100.0,2)
            self.assertAlmostEqual(ti[i]/1000.0, cap_proj.cf_sheet['Taxable_income'][i]/1000.0,1)
            self.assertAlmostEqual(tax[i]/1000.0, cap_proj.cf_sheet['Taxes'][i]/1000.0,1)
            self.assertAlmostEqual(ncf[i]/1000.0, cap_proj.cf_sheet['Net_cash_flow'][i]/1000.0,1)

    def testAssembleFinancials(self):
        """Test whether the aggregator works as required"""
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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj.assembleFinancials(price = (2.0, 'fixed'))
        ncf = np.array([8978747.66,-1023982.59,-1021252.34,-245010.9168,235113.3597,242604.478,249625.8535,256120.6641,262027.1958,267278.4446,271801.6875,275518.0181,278341.8454,280180.3527,280932.9123,280490.4538,278734.7819,275537.8386,270760.9077,264253.7538,1274375.782,1297314.206,1320665.522,1344437.162,0])

        for i in range(len(ncf)):
            self.assertAlmostEqual(ncf[i]/1000.0, cap_proj.cf_sheet['Net_cash_flow'][i]/1000.0, 1)

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
        
        loan = pf.Loan("loan1", principal = 10000000, term = 20, rate = 0.080, pmt_freq = 1, strt_year = 2012)
        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        cap_proj.setDebt(dp)
        cap_proj.assembleFinancials(price = (2.0, 'fixed'))
        #print cap_proj.cf_sheet['Net_cash_flow']
        cap_proj.printFinancials(filename = 'cfs.csv')

        #self.assertAlmostEqual(cap_proj.calcIRR(), 'what')
        #self.assertAlmostEqual(cap_proj.calcNPV(0.25),'what')

    

class FinancialParametersTests(unittest.TestCase):
    """All of the test cases for the Financial Parameters class"""

    def testCorrectAccess(self):
        """Tests if the FinancialParameters object correctly sets and accesses items"""
        fp = pf.FinancialParameters()
        fp['Initial_year'] = 2024
        self.assertEqual(fp['Initial_year'],2024)

    def testBadKey(self):
        fp = pf.FinancialParameters()
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Gonzo', 2)
        self.assertRaises(pf.ProjFinError, fp.__getitem__, 'Gonzo')

    def testBadValue(self):
        fp = pf.FinancialParameters()
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Initial_year', 'shwee-bang')
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Capital_expense_breakdown', 2.0)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Depreciation_type', 43)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', 234)
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', ('fart', 'gassy'))
        self.assertRaises(pf.ProjFinError, fp.__setitem__, 'Design_cap', (24.3, 123))


    def testCompleteness(self):

        fp = pf.FinancialParameters()
        key_list = ['Initial_year', 'Startup_year','Target_IRR', 'Depreciation_type', 'Depreciation_length', 'Analysis_period', 'Plant_life', 'Inflation_rate', 'State_tax_rate', 'Federal_tax_rate','Design_cap','Cap_factor','Capital_expense_breakdown','Startup_revenue_breakdown','Startup_fixed_cost_breakdown','Startup_variable_cost_breakdown','Salvage_value','Decommissioning_cost']
        #Take lists out of the FinancialParameters!#!
        for key in key_list:
            if key == 'Capital_expense_breakdown':
                fp[key] = [0.25, 0.25, 0.25, 0.25]
            elif key == 'Depreciation_type':
                fp[key] = 'straight-line'
            elif key == 'Design_cap':
                fp[key] = uv.UnitVal(453, 'gal') 
            else:
                fp[key] = 2.1


        self.assertEqual(fp.is_incomplete(), False)
        fp['Initial_year'] = None
        self.assertEqual(fp.is_incomplete(), True)



class CapitalExpenseTests(unittest.TestCase):
    

    def testCreateCapitalExpense(self):
        """Testing correct setting of a capital expense"""
        capex1 = pf.CapitalExpense(name = "Feeder", uninstalled_cost = 141000.0, installation_factor = 1.6)
        self.assertEqual(capex1.name, "Feeder")
        self.assertEqual(capex1.installed_cost, 225600)

    def testSetUninstalledCost(self):
        """Testing correct setting of the uninstalled cost"""
        capex1 = pf.CapitalExpense("Feeder")
        capex1.uninstalled_cost = 1000.11
        self.assertEqual(capex1.uninstalled_cost, 1000.11)


    def testSetInstallationFactor(self):
        """Testing correct setting of the installation factor"""
        capex1 = pf.CapitalExpense(name = "feeder", uninstalled_cost = 141000.0)
        capex1.installation_factor = 1.5
        self.assertEqual(capex1.installation_factor, 1.5)

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

    def testSetCost(self):
        """Setting the cost later should return the correct value"""
        capex1 = pf.CapitalExpense(name = "Feeder")
        capex1.set_cost(141000,1.6)
        self.assertEqual(capex1.installed_cost, 225600)

    def testSetCostBadInput(self):
        pass

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
        year1 = 2012
        length = 10
        #spot check the values that are charged
        dates = np.array(['2012-01-01', '2014-03-20', '2016-02-29', '2012-12-31'])
        value = 921.0/3653.0
        values = np.array([value, value, value, value])
        
        capcosts.build_depreciation_schedule(year1, length, "straight-line")
        for date, v in zip(dates,values):
            index = capcosts.depreciation_schedule.rownum(date)
            self.assertEqual(capcosts.depreciation_schedule['depreciation'][index],v)
        
        

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
        year1 = 2012
        #3 year MACRS
        length = 3
        years = np.array([2012,2013,2014,2015])
        values = np.array([306.9693, 409.3845, 136.4001, 68.2461])
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])

        #5 year MACRS
        length = 5
        years = np.array([2012,2013,2014,2015,2016, 2017])
        values = np.array([184.2, 294.72, 176.832, 106.0992, 106.0992, 53.0496])
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])

        #7 MACRS
        length = 7
        years = np.array([2012,2013,2014,2015,2016,2017,2018,2019])
        values = np.array([131.6109, 225.5529, 161.0829, 115.0329, 82.2453, 82.1532, 82.2453, 41.0766])
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])

        #10 year MACRS
        length = 10
        years = np.array([2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022])
        values = np.array([92.1,165.78,132.624,106.0992,84.9162,67.8777,60.3255,60.3255,60.4176,60.3255,30.2088])
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])

        #15 year MACRS
        length = 15
        years = np.array([2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027])
        values = np.array([46.05,87.495,78.7455,70.917,63.8253,57.3783,54.3390,54.3390,54.4311,54.339,54.4311,54.3390,54.4311,54.3390,54.4311,27.1695])
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])

        #20 year MACRS
        length = 20
        years = np.array([2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026, 2027, 2028,2029,2030,2031,2032])
        values = np.array([34.5375,66.48699,61.49517,56.89017,52.61673,48.67485,45.01848,41.64762,41.09502,41.08581,41.09502,41.0858100,41.09502,41.08581,41.09502,41.08581,41.09502,41.08581,41.09502,41.08581,20.54751])
        
        capcosts.build_depreciation_schedule(year1,length,"MACRS")
        
        #self.assertEqual(capcosts.depreciation_schedule['year'].all(),years.all())
        for i in range(len(values)):
            self.assertAlmostEqual(capcosts.depreciation_schedule['depreciation'][i],values[i])


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
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_year = 2015)
        loan.generate_schedule()

        years = np.array([2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030,2031,2032,2033,2034])
        principal = np.array([686000,671819.7116,656434.0987,639740.7086,621628.3805,601976.5044,580654.2189,557519.5391,532418.4115,505183.688,475634.0131,443572.6158,408785.9997,371042.5213,330090.8472,285658.2808,237448.9463,185141.8183,128388.5845,66811.32572])
        interest = np.array([58310,57104.67549,55796.89839,54377.96023,52838.41234,51168.00287,49355.6086,47389.16082,45255.56497,42940.61348,40428.89111,37703.67234,34746.80998,31538.61431,28057.72201,24280.95387,20183.16043,15737.05456,10913.02968,5678.96286])
        principal_paid = np.array([14180.28841,15385.61292,16693.39002,18112.32817,19651.87607,21322.28554,23134.67981,25101.12759,27234.72343,29549.67492,32061.3973,34786.61607,37743.47843,40951.6741,44432.5664,48209.33454,52307.12798,56753.23385,61577.25873,66811.32572])
        
        for i in range(0,len(principal)):

            self.assertAlmostEqual(loan.schedule['principal'][i],principal[i],3)
            self.assertAlmostEqual(loan.schedule['interest'][i],interest[i],3)
            self.assertAlmostEqual(loan.schedule['principal_payment'][i],principal_paid[i],3) 
        

    def testCorrectlyGenerateScheduleBiAnnual(self):
        """Testing correct loan schedule generation for bi-annual coupon payments"""
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 2, strt_period = ct.FinDate(2012,1,1))
        loan.generate_schedule()

        years = np.array(['2012-07-01', '2013-01-01', '2013-06-30', '2016-07-01', '2022-01-01', '2027-06-30', '2032-01-01'])
        

        
        principal = np.array([686000,672102.8002,656999.2366,640584.5893,622745.048,603356.923,582285.7876,559385.546,534497.4202,507448.8496,478052.294,446103.9337,411382.256,373646.5197,332635.0856,288063.6027,239623.0365,186977.5264,129762.057,67579.92724])
        interest = np.array([58020.82938,56814.46558,55503.38186,54078.48788,52529.9042,50846.89378,49017.78753,47029.90343,44869.45857,42521.47358,39969.66883,37196.35147,34182.29284,30906.59508,27346.54628,23477.46299,19272.51909,14702.55978,9735.899438,4338.101939])
        principal_paid = np.array([13897.1998,15103.5636,16414.64731,17839.54129,19388.12497,21071.1354,22900.24164,24888.12575,27048.57061,29396.55559,31948.36035,34721.6777,37735.73634,41011.4341,44571.4829,48440.56619,52645.51009,57215.4694,62182.12974,67579.92724])
        
        for i in range(0,len(principal)):

            self.assertAlmostEqual(loan.schedule['principal'][i],principal[i],4)
            self.assertAlmostEqual(loan.schedule['interest'][i],interest[i],4)
            self.assertAlmostEqual(loan.schedule['principal_payment'][i],principal_paid[i],4)
        

class DebtPortfolioTests(unittest.TestCase):
    def testAddLoan(self):
        """DebtPortfolio must correctly add a loan to its set of loans"""
	loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_year = 2015)
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
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_year = 2015)
	dp.add_loan(loan)
	self.assertRaises(pf.ProjFinError, dp.add_loan, loan)

    def testDelLoan(self):
        """DebtPortfolio must correctly remove a loan from its set of loans"""
	loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_year = 2015)
	dp = pf.DebtPortfolio()
        dp.add_loan(loan)
        loan2 = pf.Loan("loan2", principal = 750000, term = 15, rate = 0.134, pmt_freq = 2, strt_year = 2017)
        dp.add_loan(loan2)
        dp.del_loan("loan1")
        self.assertEqual(dp.loans, [loan2])

    def testCIPcalc(self):
        """Must correctly calculate cash proceeds, interest, and principal for a loan"""
        loan = pf.Loan("loan1", principal = 686000, term = 20, rate = 0.085, pmt_freq = 1, strt_year = 2015)
        loan2 = pf.Loan("loan2", principal = 750000, term = 15, rate = 0.134, pmt_freq = 2, strt_year = 2017)
        #ensure correct cash, interest, principal in 2017 and in 2024

        dp = pf.DebtPortfolio()
	dp.add_loan(loan)
        dp.add_loan(loan2)
        self.assertAlmostEqual(dp.CIP(2017)[0], 750000)
        self.assertAlmostEqual(dp.CIP(2017)[1], 155735.5,1)
        self.assertAlmostEqual(dp.CIP(2017)[2], 34012.21,2)
        self.assertAlmostEqual(dp.CIP(2024)[0], 0.0)
        self.assertAlmostEqual(dp.CIP(2024)[1], 117262.1966,3)
        self.assertAlmostEqual(dp.CIP(2024)[2], 72485.53866,3)




if __name__ == "__main__":
    unittest.main()
