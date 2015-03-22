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


class FixedExpenseTests(unittest.TestCase):
    
    
    def testCreateFixedExpense(self):
        """Testing correct setting of a capital expense"""


	scaler = pf.LinearScaler()
	QB = pf.FixedExpenseQuoteBasis(base_price = 14000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq = 'M')
	esc = pf.NoEscalationEscalator()
	fex1 = pf.FixedExpense(name = 'Labor', description = 'People', quote_basis = QB, escalator = esc, startup_discounter = None, pmt_type = 'simple')

	self.assertEqual(fex1.name, 'Labor')
	self.assertEqual(fex1.description, 'People')
	self.assertEqual(fex1.quote_basis, QB)
	self.assertEqual(fex1.escalator, esc)
	self.assertEqual(fex1.pmt_type, 'simple')
	


    def testBadFixedCostInput(self):
        """Bad input types or values should throw a BadCapitalCostInput error on initialization"""

	scaler = pf.LinearScaler()
	QB = pf.FixedExpenseQuoteBasis(base_price = 14000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq = 'M')
	kwargs = {}
	kwargs['name'] = 'Labor'
	kwargs['description'] = 'farts'
	kwargs['startup_discounter'] = None
	kwargs['pmt_type'] = 'simple'

	kwargs['quote_basis'] = 'a'
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['quote_basis'] = QB

	kwargs['name'] = 29
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['name'] = 'Labor'

	kwargs['description'] = QB
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['description'] = 'farts'

	kwargs['escalator'] = 'a'
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['escalator'] = None
       
	kwargs['startup_discounter'] = 'a'
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['startup_discounter'] = None

	kwargs['pmt_type'] = 'boobs'
	self.assertRaises(pf.BadFixedExpenseInput, pf.FixedExpense, **kwargs)
	kwargs['pmt_type'] = 'simple'
 
       

    def testAggregateCorrectly_simple(self):
        """Each CapitalExpense must successfully aggregate itself"""
	

	scaler = pf.LinearScaler()
	QB = pf.FixedExpenseQuoteBasis(base_price = 14000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq = 'M')
	esc = pf.InflationRateEscalator(rate=0.01)
	fex1 = pf.FixedExpense(name = 'Labor', description = 'People', quote_basis = QB, escalator = esc)

	fex1.init_date = dt.datetime(2012,01,01)
	fex1.pmt_type = 'simple'
	fex1.pmt_args['term'] = dt.timedelta(20*365)
	fex1.startup_discounter = None

	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        vals = [14011.45438,14151.95472,15198.0633,15465.55295]
        vals2 = [20016.3634, 20217.07817, 21711.519, 22093.64707]
        vals3 = [10508.59078, 14151.95472, 15198.0633, 15465.55295]
	vals4 = [30524.95418, 34369.03288, 36909.58229, 37559.20002]

	fex1.build_fex_schedule()
        #print fex1.schedule
        for d, v in zip(dates, vals):
            self.assertAlmostEqual(v, fex1.schedule.loc[d, 'fixed_costs'],4)
	
    def testAggregateCorrectly_fixed_schedule(self):
	self.assertTrue(False)

    def testAggregateCorrectly_simple_75burnin(self):
	scaler = pf.LinearScaler()
	QB = pf.FixedExpenseQuoteBasis(base_price = 14000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq = 'M')
	esc = pf.InflationRateEscalator(rate=0.01)
	fex1 = pf.FixedExpense(name = 'Labor', description = 'People', quote_basis = QB, escalator = esc)

	fex1.init_date = dt.datetime(2012,01,01)
	fex1.pmt_type = 'simple'
	fex1.pmt_args['term'] = dt.timedelta(20*365)
	fex1.startup_discounter = pf.dtFractionalStartupDiscounter(time_span = dt.timedelta(days=1*365), fraction = 0.75)
	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        vals = [14011.45438,14151.95472,15198.0633,15465.55295]
        vals2 = [20016.3634, 20217.07817, 21711.519, 22093.64707]
        vals3 = [10508.59078, 14151.95472, 15198.0633, 15465.55295]
	vals4 = [30524.95418, 34369.03288, 36909.58229, 37559.20002]

	fex1.build_fex_schedule()

        for d, v in zip(dates, vals3):
            self.assertAlmostEqual(v, fex1.schedule.loc[d, 'fixed_costs'],4)


	

class FixedCostsTests(unittest.TestCase):

    def testBadFixedCostItem(self):
        """Adding an item that is not a fixed expense should raise an error"""
	       
        costs = pf.FixedCosts()
        self.assertRaises(pf.BadFixedCostType, costs.add_fixed_cost, "ninja")


    def testAggregateCorrectly(self):
        """FixedCosts must correctly build the fixed cost schedule"""
	scaler = pf.LinearScaler()
	QB = pf.FixedExpenseQuoteBasis(base_price = 14000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq = 'M')
        QB2 = pf.FixedExpenseQuoteBasis(base_price = 20000, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, 'lb/hr'), freq= 'M')

	esc = pf.InflationRateEscalator(rate=0.01)
	fex1 = pf.FixedExpense(name = 'Labor', description = 'People', quote_basis = QB, escalator = esc)

	fex1.init_date = dt.datetime(2012,01,01)
	fex1.pmt_type = 'simple'
	fex1.pmt_args['term'] = dt.timedelta(20*365)
	fex1.startup_discounter = pf.dtFractionalStartupDiscounter(time_span = dt.timedelta(days=1*365), fraction = 0.75)

        fex2 = pf.FixedExpense(name = 'Strippers', description = 'Entertainment', quote_basis = QB2, escalator = esc)
        fex2.init_date = dt.datetime(2012,01,01)
        fex2.pmt_type = 'simple'
        fex2.pmt_args['term'] = dt.timedelta(20*365)
        fex2.startup_discounter = None

	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        vals = [14011.45438,14151.95472,15198.0633,15465.55295]
        vals2 = [20016.3634, 20217.07817, 21711.519, 22093.64707]
        vals3 = [10508.59078, 14151.95472, 15198.0633, 15465.55295]
	vals4 = [30524.95418, 34369.03288, 36909.58229, 37559.20002]

	costs = pf.FixedCosts()
        costs.add_fixed_cost(fex1)
        costs.add_fixed_cost(fex2)
        costs.build_fex_schedule()

        for d, v in zip(dates, vals4):
            self.assertAlmostEqual(v, costs.schedule.loc[d, 'fixed_costs'],4)


    



if __name__ == "__main__":
    unittest.main()
