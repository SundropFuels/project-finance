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

    def testSetVariableCosts(self):
        """The variable costs must be calculated correctly"""
        fp1 = copy.deepcopy(CapitalProjectTests.fp)
        cap_proj = pf.CapitalProject()
        cap_proj.setFinancialParameters(fp1)
        print "Fin param set"
        cap_proj.setPrices(mode = 'fixed', base_price = 2.0)
        print "Prices set"
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
        print "Cap costs set"
        cap_proj._calcCapitalCosts()
        print "Capital costs calculated"
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



if __name__ == "__main__":

    unittest.main()
