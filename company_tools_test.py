"""company_tools_test.py
Unit tests for company tools objects
Chris Perkins
2012-10-23
"""

import unittest
from company_tools import *
from company import *
import numpy as np
import dataFrame_v2 as df
import copy
import UnitValues as uv

class TimePeriodTests(unittest.TestCase):
    """This tests the implementation of the TimePeriod object"""

    def testInstantiateAnnualTimePeriod(self):
        """This must correctly create an annual time period object"""
        p = annualTimePeriod(2, start_period = "2012")
        self.assertEqual(p.now(), "2014")

    def testInstantiateQuarterlyTimePeriod(self):
        """This must correctly create a quarterly time period object"""
        p = quarterlyTimePeriod(2, start_period = "2012Q4")
        self.assertEqual(p.now(), "2013Q2")

    def testInstantiateMonthlyTimePeriod(self):
        """This must correctly create a monthly time period object"""
        p = monthlyTimePeriod(2, start_period = "Dec 2012")
        self.assertEqual(p.now(), "Feb 2013")
           
    def testAnnualIncrease(self):
        """Increasing the time period should give the right response"""
        p = annualTimePeriod(2, start_period = "2012")
        p.increment(5)
        self.assertEqual(p.now(), "2019")

    def testQuarterlyIncrease(self):
        """Increasing the time period should give the right response"""
        p = quarterlyTimePeriod(2, start_period = "2012Q4")
        p.increment(5)
        self.assertEqual(p.now(), "2014Q3")

    def testMonthlyIncrease(self):
        """Increasing the time period should give the right response"""
        p = monthlyTimePeriod(2, start_period = "Dec 2012")
        p.increment(5)
        self.assertEqual(p.now(), "Jul 2013")

    def testAnnualDecrease(self):
        """Decreasing the time period should give the right response"""
        p = annualTimePeriod(2, start_period = "2012")
        p.decrement(5)
        self.assertEqual(p.now(), "2009")

    def testQuarterlyDecrease(self):
        """Decreasing the time period should give the right response"""
        p = quarterlyTimePeriod(2, start_period = "2012Q4")
        p.decrement(5)
        self.assertEqual(p.now(), "2012Q1")

    def testMonthlyDecrease(self):
        """Decreasing the time period should give the right response"""
        p = monthlyTimePeriod(2, start_period = "Dec 2012")
        p.decrement(5)
        self.assertEqual(p.now(), "Sep 2012")


if __name__ == "__main__":
   unittest.main()
