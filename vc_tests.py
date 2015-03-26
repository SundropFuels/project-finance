"""vc_tests.py
Unit tests for variable costs in Project Finance program
Chris Perkins
2012-04-17

split out 2015-03-26
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


class VariableExpenseTests(unittest.TestCase):
    
    
    def testCreateVariableExpense(self):
        """Testing correct setting of a variable expense"""

	scaler = pf.LinearScaler()
	QBp = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QBp, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	QB = pf.VariableExpenseQuoteBasis(base_price = 0.062, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/(kW*hr)'))
	vex1 = pf.VariableExpense(name = 'Electricity', description = 'Power consumption by plant', quote_basis = QB, production = pro1, rate = uv.UnitVal(1, 'kW*hr/gal'), escalator = esc, pmt_type = 'simple')

	self.assertEqual(vex1.name, 'Electricity')
	self.assertEqual(vex1.description, 'Power consumption by plant')
	self.assertEqual(vex1.quote_basis, QB)
	self.assertEqual(vex1.production, pro1)
	self.assertEqual(vex1.rate, uv.UnitVal(1, 'kW*hr/gal')
	self.assertEqual(vex1.escalator, esc)
	self.assertEqual(vex1.pmt_type, 'simple')	


    def testBadVariableExpenseInput(self):
        """Bad input types or values should throw a BadVariableExpenseInput error on initialization"""

	scaler = pf.LinearScaler()
	QBp = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QBp, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	QB = pf.VariableExpenseQuoteBasis(base_price = 0.062, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/(kW*hr)'))


	kwargs = {}
	kwargs['name'] = 'Labor'
	kwargs['description'] = 'farts'
	kwargs['quote_basis'] = QB
	kwargs['production'] = pro1
	kwargs['rate'] = uv.UnitVal(1,'kW*hr/gal')
	kwargs['escalator'] = esc
	kwargs['startup_discounter'] = pf.NoneStartupDiscounter()
	
	kwargs['pmt_type'] = 'balls'
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['pmt_type'] = 'simple'

	kwargs['description'] = 29
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['description'] = 'farts'

	kwargs['quote_basis'] = 2345.3
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['quote_basis'] = QB

	kwargs['production'] = QB
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['production'] = pro1

	kwargs['rate'] = 234
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['rate'] = uv.UnitVal(1, 'kW*hr/gal')

	kwargs['escalator'] = pro1
	self.assertRaises(pf.BadVariableExpenseInput, pf.VariableExpense, **kwargs)
	kwargs['escalator'] = esc

 	
       

    def testAggregateCorrectly_simple(self):
        """Each VariableExpense must successfully aggregate itself"""

	scaler = pf.LinearScaler()
	QBp = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QBp, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	QB = pf.VariableExpenseQuoteBasis(base_price = 0.062, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/(kW*hr)'))
	vex1 = pf.VariableExpense(name = 'Electricity', description = 'Power consumption by plant', quote_basis = QB, production = pro1, rate = uv.UnitVal(1, 'kW*hr/gal'), escalator = esc, pmt_type = 'simple')
	vex1.build_vex_schedule()		#Do we need a term here?  Yes?  How do we control this...through the production?  #maybe this should just be passed as an argument

	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        ###!!!###Still need values here!
        vals_cons = [,,,]
        vals_cost = [,,,]
        	
        for d, v1, v2 in zip(dates, vals_cons, vals_cost):
            self.assertAlmostEqual(v, vex1.schedule.loc[d, 'variable_consumption'],4)
	    self.assertAlmostEqual(v, vex1.schedule.loc[d, 'variable_costs'],4)
	    
class VariableCostsTests(unittest.TestCase):

    def testBadVariableCostItem(self):
        """Adding an item that is not a fixed expense should raise an error"""
	       
        costs = pf.VariableCosts()
        self.assertRaises(pf.BadVariableExpenseType, costs.add_variable_cost, "ninja")


    def testAggregateCorrectly(self):
        """VariableCosts must correctly build the fixed cost schedule"""

	scaler = pf.LinearScaler()
	QBp = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QBp, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	QB = pf.VariableExpenseQuoteBasis(base_price = 0.062, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/(kW*hr)'))
	vex1 = pf.VariableExpense(name = 'Electricity', description = 'Power consumption by plant', quote_basis = QB, production = pro1, rate = uv.UnitVal(1, 'kW*hr/gal'), escalator = esc)
	vex1.build_vex_schedule()		#Do we need a term here?  Yes?  How do we control this...through the production?  #maybe this should just be passed as an argument

	QB2 = pf.VariableExpenseQuoteBasis(base_price = 75, date = dt.datetime(2012,01,01), source= 'Tom Miles', scaler = scaler, size_basis = uv.UnitVal(1, '1/ton'))
	vex2 = pf.VariableExpense(name = 'Biomass', description = 'Biomass used by plant', quote_basis = QB2, production = pro1, rate = uv.UnitVal(1/150, 'ton/gal'), escalator = esc)


	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        vals = [,,,]

	costs = pf.VariableCosts()
        costs.add_variable_cost(vex1)
        costs.add_variable_cost(vex2)
        costs.build_vex_schedule()

        for d, v in zip(dates, vals):
            self.assertAlmostEqual(v, costs.schedule.loc[d, 'variable_costs'],4)


    def testAggregateDetailedCorrectly(self):
	"""VariableCosts must correctly build the detailed cost schedule"""
	scaler = pf.LinearScaler()
	QBp = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QBp, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	QB = pf.VariableExpenseQuoteBasis(base_price = 0.062, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/(kW*hr)'))
	vex1 = pf.VariableExpense(name = 'Electricity', description = 'Power consumption by plant', quote_basis = QB, production = pro1, rate = uv.UnitVal(1, 'kW*hr/gal'), escalator = esc)
	vex1.build_vex_schedule()		#Do we need a term here?  Yes?  How do we control this...through the production?  #maybe this should just be passed as an argument

	QB2 = pf.VariableExpenseQuoteBasis(base_price = 75, date = dt.datetime(2012,01,01), source= 'Tom Miles', scaler = scaler, size_basis = uv.UnitVal(1, '1/ton'))
	vex2 = pf.VariableExpense(name = 'Biomass', description = 'Biomass used by plant', quote_basis = QB2, production = pro1, rate = uv.UnitVal(1/150, 'ton/gal'), escalator = esc)


	dates = [dt.datetime(2012,01,31), dt.datetime(2013,01,31), dt.datetime(2020, 03, 31), dt.datetime(2021, 12,31)]
        
	costs = pf.VariableCosts()
        costs.add_variable_cost(vex1)
        costs.add_variable_cost(vex2)
	costs.detailed = True
        costs.build_vex_schedule()

        for d, dates:
            self.assertTrue((vex1.schedule['variable_production'] == costs.schedule['Electricity_variable_production']).all())
	    self.assertTrue((vex1.schedule['variable_costs'] == costs.schedule['Electricity_variable_costs').all())
	    self.assertTrue((vex2.schedule['variable_production'] == costs.schedule['Biomass_variable_production']).all())
	    self.assertTrue((vex2.schedule['variable_costs'] == costs.schedule['Biomass_variable_costs']).all())



if __name__ == "__main__":
    unittest.main()
