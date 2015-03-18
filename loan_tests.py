"""loan_tests.py
Unit tests for Project Finance program
Chris Perkins
2012-04-17

split out 2015-03-15
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

class DebtTests(unittest.TestCase):
    """Tests for the abstract debt container"""

    def testCorrectInitialization(self):
	"""Test whether a debt object is properly initialized"""
	sec = pf.Debt(name = 'sec1', principal = 1.5E6, init_date = dt.datetime(2012,01,01), comment = 'First test debt security')
        self.assertEqual(sec.name, 'sec1')
	self.assertEqual(sec.principal, 1.5E6)
	self.assertEqual(sec.init_date, dt.datetime(2012,01,01))
	self.assertEqual(sec.comment, 'First test debt security')
	

    def testBadInput(self):
	"""Test whether a debt object throws appropriate errors on initialization"""
	
	#Bad name
	kwargs = {'name':25.0, 'principal':1.5E6, 'init_date':dt.datetime(2012,01,01), 'comment':'First test debt security'}
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)
	kwargs['name'] = 'sec1'
	
	#Bad principal
	kwargs['principal'] = 'a'
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)
	kwargs['principal'] = -12.5
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)
	kwargs['principal'] = 1.5E6

	#Bad date
	kwargs['init_date'] = 'a'
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)
	kwargs['init_date'] = 2.3
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)
	kwargs['init_date'] = dt.datetime(2012,01,01)
	
	#Bad comment
	kwargs['comment'] = 12.45
	self.assertRaises(pf.BadDebtInput, pf.Debt, **kwargs)

	





class LoanTests(unittest.TestCase):
    def testBadInputs(self):
        self.assertTrue(False)

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
