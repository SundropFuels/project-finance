"""company_test.py
Unit tests for company objects
Chris Perkins
2012-10-23
"""

import unittest
from company import *
from company_tools import *
import numpy as np
import dataFrame_v2 as df
import copy
import UnitValues as uv

class CurrentPeriodTests(unittest.TestCase):
    """Tests for setting the current period and getting the date back from the current period"""

    def setCurrentPeriodTestAnnual(self):
        c = Company(name = "PCT")
        p = annualTimePeriod(15, start_period = "2012")
        c.set_current_period(p)
        self.assertEqual(c.current_period.now(), "2027")

    def setCurrentPeriodTestQuarterly(self):
        c = Company(name = "PCT")
        p = quarterlyTimePeriod(15, start_period = "2012Q1")
        c.set_current_period(p)
        self.assertEqual(c.current_period.now(), "2015Q4")

    def setCurrentPeriodTestMonthly(self):
        c = Company(name = "PCT")
        p = monthlyTimePeriod(15, start_period = "Jun 2012")
        c.set_current_period(p)
        self.assertEqual(c.current_period.now(), "Sep 2013")

class ProjectExpendituresTests(unittest.TestCase):
    """Tests for determining if the Company correctly calculates the period expenditures for projects"""
    def testSingleCapitalProjectExpenditures(self):
        """For a single capital project, the Company should correctly calculate the expenditures for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define a capital program with a single project (load from a file)
        #using 1000 as a placeholder for the capital program expenditures        
        c.capital_program.generate_expenditures()
        self.assertEqual(c.capital_program.expenditures.cost_of_sales, 1000)
        self.assertEqual(c.capital_program.expenditures.interest, 1000)
        

    def testMultipleCapitalProjectExpenditures(self):
        """For a given list of capital projects, the Company should correctly calculate the expenditures for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define a capital program with a single project (load from a file)
        #using 1000 as a placeholder for the capital program expenditures        
        c.capital_program.generate_expenditures()
        self.assertEqual(c.capital_program.expenditures.cost_of_sales, 1000)
        self.assertEqual(c.capital_program.expenditures.interest, 1000)

    def testSingleRDProjectExpenditures(self):
        """For a single R&D project, the Company should correctly calculate the expenditures for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define an R&D program with a single project (load from a file)
        #using 1000 as a placeholder for the research program expenditures        
        c.research_program.generate_expenditures()
        self.assertEqual(c.research_program.expenditures.research_expenses, 1000)
        

    def testMultipleRDProjectExpenditures(self):
        """For a given list of R&D projects, the Company should correctly calculate the expenditures for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define an R&D program with a single project (load from a file)
        #using 1000 as a placeholder for the research program expenditures        
        c.research_program.generate_expenditures()
        self.assertEqual(c.research_program.expenditures.research_expenses, 1000)

    def testMixedProjectsExpenditures(self):
        """For a total list of projects, the Company should correctly calculate all expenditures for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define an R&D program with a single project (load from a file)
        #define a capital program with multple projects (load from files)
        #using 1000 as a placeholder for the research program expenditures        
        c.research_program.generate_expenditures()
        c.capital_program.generate_expenditures()
        self.assertEqual(c.expenditures.cost_of_sales, 1000)
        self.assertEqual(c.expenditures.interest, 1000)
        self.assertEqual(c.expenditures.research_expenses, 1000)


class StaffExpendituresTests(unittest.TestCase):
    """Tests for determining if the Company correctly calculates the period expenditures for staffing"""
    def testPeriodStaffingExpenditures(self):
        """For a given period and a given list of staff, correctly calculate the staffing expenditure"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define a company staff
        #assume staffing costs equal to 1000 before tests written
        self.assertEqual(c.staff.expenditures(), 1000)

class IndirectExpendituresTests(unittest.TestCase):
    """Tests for determining if the Company correctly calculates the period indirect costs (buildings, utilities, postage, G&A, etc.)"""
    def testTotalGALoadExpenditures(self):
        """For a given set of capital and research programs, correctly calculate the G&A loads"""
        
        #likely going to do these as a fraction of the total economic activity and the total number of staff
        #when adding a project, need to ensure that there is enough support staff in the indirects and G&A to cover it
        self.assertEqual(1,0)

class DebtExpenditureTests(unittest.TestCase):
    """For explicit liabilities, test whether the Company correctly calculates the period expenditures"""
    #Need to decide whether I am going to determine financing at the project level or at the company level
    #Actually, it makes more sense for projects to finance themselves -- this is a self-contained decision point
    #Then, for the company level, financing should be explicit for outside-project pieces

    def testInterestExpenditures(self):
        """The company should correctly calculate this period's interest expenditures"""

        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the company liabilities
        #define a capital program
        #add some notes to the company liabilities
        #assume staffing costs equal to 1000 before tests written
        self.assertEqual(c.liabilities.interest(), 1000)

    
class ProjectIncomeTests(unittest.TestCase):
    """Tests for determining if the Company correctly calculates the period income for projects"""
    def testSingleCapitalProjectIncome(self):
        """For a single capital project, the Company should correctly calculate the income for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define a capital program with a single capital project
        #assume staffing costs equal to 1000 before tests written
        c.capital_program.generate_income()
        self.assertEqual(c.income.sales, 1000)

    def testMultipleCapitalProjectIncome(self):
        """For a given list of capital projects, the Company should correctly calculate the income for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define a capital program with multiple capital projects
        #assume staffing costs equal to 1000 before tests written
        c.capital_program.generate_income()
        self.assertEqual(c.income.sales, 1000)
    

class AssetIncomeTests(unittest.TestCase):
    """Tests for determining if the Company correctly calculates the period income from assets"""
    def testTotalAssetIncome(self):
        """For all assets, the Company should correctly calculate the income for the current period"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the corporate assets
        #assume staffing costs equal to 1000 before tests written
        self.assertEqual(c.assets.income(), 1000)

class BalanceSheetTests(unittest.TestCase):
    """Tests for determining if the Company correctly generates a balance sheet"""
    def testGenerateBalanceSheet(self):
        """The Company should correctly generate a balance sheet"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the corporate assets
        #define the corporate liabilities
        #define the corporate equity
        #define project lists (where new items may arise from the projects)
        #define a Balance Sheet object that is the standard
        #assume staffing costs equal to 1000 before tests written
        self.assertEqual(c.balance_sheet, 1000)
        #NOTE: This interface assumes that the balance sheet is always updated whenever something is changed

    def testGenerateAssets(self):
        """The Company should correctly generate a categorization of assets for the balance sheet"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the corporate assets
        #define project lists (where new items may arise from the projects)
        self.assertEqual(c.assets, 1000)
        #NOTE: This interface assumes that the balance sheet is always updated whenever something is changed

    def testGenerateLiabilities(self):
        """The Company should correctly generate a categorization of liabilities for the balance sheet"""
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the corporate liabilities
        #define project lists (where new items may arise from the projects)
        self.assertEqual(c.liabilities, 1000)
        #NOTE: This interface assumes that the balance sheet is always updated whenever something is changed

    def testGenerateEquity(self):
        """The Company should correctly generate a categorization of equity for the balance sheet"""
        
        c = Company(name = "PCT")
        p = annualTimePeriod(1, start_period = "2012")
        c.set_current_period(p)
        #define the corporate equity
        #define project lists (where new items may arise from the projects)
        self.assertEqual(c.equity, 1000)
        #NOTE: This interface assumes that the balance sheet is always updated whenever something is changed

    def testGetInventory(self):
        """The Company should correctly determine its inventory from its project list"""
        self.assertEqual(0,1)

    def testGetCapitalAssets(self):
        """The Company should correctly determine its fixed assets (in categories) from its project list"""
        self.assertEqual(0,1)

    def testGetAccumulatedDepreciation(self):
        """The Company should correctly update its accumulated depreciation from its project list"""
        self.assertEqual(0,1)

    def testGetShortTermLiabilities(self):
        """The Company should correctly calculate its short-term liabilities from its project and expenditures list"""
        self.assertEqual(0,1)

    def testGetLongTermLiabilities(self):
        """The Company should correctly calculate its long-term liabilities from its project and liabilities lists"""
        self.assertEqual(0,1)

    def testGetStock(self):
        """The Company should correctly calculate its outstanding stock issues"""
        self.assertEqual(0,1)

    def testIssueStock(self):
        """The Company should correctly account for an issuance of stock at a given value"""
        self.assertEqual(0,1)

    def testGetPIC(self):
        """The Company should correctly calculate its paid-in capital above par"""
        self.assertEqual(0,1)

    def testGetRetainedEarnings(self):
        """The Company should correctly calculate its retained earnings"""
        self.assertEqual(0,1)

    def testPayDividend(self):
        """The Company should correctly account for a dividend issuance"""
        self.assertEqual(0,1)



if __name__ == "__main__":
    unittest.main()





