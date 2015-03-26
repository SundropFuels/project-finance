"""prod_tests.py
Unit tests for Product/Production classes in Project Finance program
Chris Perkins
2012-04-17

split out 2015-03-20
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


class ProductTests(unittest.TestCase):
    
    
    def testCreateProduct(self):
        """Testing correct setting of a capital expense"""


	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)

	self.assertEqual(pr1.name, 'gasoline')
	self.assertEqual(pr1.description, 'People')
	self.assertEqual(pr1.quote_basis, QB)
	self.assertEqual(pr1.escalator, esc)	

    def testBadProductInput(self):
	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()

	kwargs = {}
	kwargs['name'] = 'gasoline'
	kwargs['description'] = 'people'
	kwargs['quote_basis'] = QB
	kwargs['escalator'] = 'fart'

	self.assertRaises(pf.BadProductInput, pf.Product, **kwargs)
	kwargs['escalator'] = esc

	kwargs['quote_basis'] = 'snot'
	self.assertRaises(pf.BadProductInput, pf.Product, **kwargs)
	kwargs['quote_basis'] = QB

	kwargs['description'] = 12
	self.assertRaises(pf.BadProductInput, pf.Product, **kwargs)
	kwargs['description'] = 'people'

	kwargs['name'] = QB
	self.assertRaises(pf.BadProductInput, pf.Product, **kwargs)
	kwargs['name'] = 'gasoline'

    def testCreateProduction(self):
        scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)

	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = None, init_date = dt.datetime(2015,01,01))

	self.assertEqual(pro1.name, 'stream1')
	self.assertEqual(pro1.product, pr1)
	self.assertEqual(pro1.rate, uv.UnitVal(15000,'gal/hr'))
	self.assertEqual(pro1.init_date, dt.datetime(2015,01,01))
	self.assertEqual(pro1.method, 'simple')
	self.assertEqual(pro1.freq, 'D')

    def testBadProductionInput(self):

	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2012,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(100, '1/gal'))
	esc = pf.NoEscalationEscalator()
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)

	kwargs = {}
	kwargs['name'] = 'stream1'
	kwargs['product'] = pr1
	kwargs['rate'] = uv.UnitVal(15000, 'gal/hr')
	kwargs['method'] = 'simple'
	kwargs['freq'] = 'D'
	kwargs['init_date'] = dt.datetime(2015,01,01)

	kwargs['startup_discounter'] = 'poop'
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['startup_discounter'] = None

	kwargs['name'] = 25
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['name'] = 'stream1'
	
	kwargs['product'] = 253
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['product'] = pr1

	kwargs['rate'] = 34
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['rate'] = uv.UnitVal(15000, 'gal/hr')

	kwargs['comment'] = QB
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['comment'] = 'goop'

	kwargs['method'] = 'horned_toad'
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['method'] = 'simple'


	kwargs['freq'] = 'never'
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['freq'] = 'D'

	kwargs['init_date'] = 24
	self.assertRaises(pf.BadProductionInput, pf.Production, **kwargs)
	kwargs['init_date'] = dt.datetime(2015,01,01)


    def testBuildProductionSchedule(self):

	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2015,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(1, '1/gal'))
	esc = pf.InflationRateEscalator(rate = 0.01)
	sd = pf.dtFractionalStartupDiscounter(time_span = dt.timedelta(days=1*365), fraction = 0.75)
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = sd, init_date = dt.datetime(2015,01,01))
	pro1.sch_args['term'] = dt.timedelta(10*400)			#This is kind of ugly, from an OO perspective; it gives waaaay too much insight into how this works -- fix later
	pro1.build_production_schedule()

	dates = [dt.datetime(2015,01,01), dt.datetime(2017,03,25), dt.datetime(2024,12,31)]
	production_vals = [270000,360000,360000]		#This could be very difficult to parse, and math will be much slower -- maybe hold the units separately
	price_vals = [1.53,1.564331125,1.690164001]
	revenue_vals = [413100, 563159.2049, 608459.0404]

	for d,v1,v2,v3 in zip(dates, production_vals, price_vals, revenue_vals):
            self.assertAlmostEqual(pro1.schedule.loc[d,'rate'], v1,4)
	    self.assertAlmostEqual(pro1.schedule.loc[d,'price'],v2,4)
	    self.assertAlmostEqual(pro1.schedule.loc[d,'revenue'],v3,4)

    def testUnitMismatch(self):
        self.assertTrue(False)

class ProductPortfolioTests(unittest.TestCase):

    def testBadProductionItem(self):
        """Adding an item that is not a fixed expense should raise an error"""
	prod = pf.ProductionPortfolio()
	self.assertRaises(pf.BadProductionItem, prod.add_production, 45)
	


    def testAggregateCorrectly(self):
        """ProductionPortfolio must correctly build the fixed cost schedule"""
	
	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2015,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(1, '1/gal'))
	esc = pf.InflationRateEscalator(rate = 0.01)
	sd = pf.dtFractionalStartupDiscounter(time_span = dt.timedelta(days=1*365), fraction = 0.75)
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = sd, init_date = dt.datetime(2015,01,01))
	pro1.sch_args['term'] = dt.timedelta(10*366)			#This is kind of ugly, from an OO perspective; it gives waaaay too much insight into how this works -- fix later
	QB2 = pf.ProductQuoteBasis(base_price = 0.04*2.205, date = dt.datetime(2015,01,01), source = 'mag', scaler = scaler, size_basis = uv.UnitVal(1, '1/kg'))
	pr2 = pf.Product(name = 'char', description = 'coally waste', quote_basis = QB2, escalator = None)
	pro2 = pf.Production(name = 'stream2', product = pr2, rate = uv.UnitVal(150000, 'lb/day'), startup_discounter = None, init_date = dt.datetime(2015,01,01))
	pro2.sch_args['term'] = dt.timedelta(10*366)
	port = pf.ProductionPortfolio()
	port.add_production(pro1)
	port.add_production(pro2)
	port.build_production_schedule()
		

	dates = [dt.datetime(2015,01,01), dt.datetime(2017,03,25), dt.datetime(2024,12,31)]
	revenue_vals = [419101.05, 569160.2549, 614460.0904]
	

	for d,v in zip(dates, revenue_vals):
            
	    self.assertAlmostEqual(port.schedule.loc[d,'revenue'],v,1)

    def testAggregateDetailed(self):
	"""ProductionPortfolio must correctly build the fixed cost schedule"""
	
	scaler = pf.LinearScaler()
	QB = pf.ProductQuoteBasis(base_price = 1.53, date = dt.datetime(2015,01,01), source = "P&T", scaler = scaler, size_basis = uv.UnitVal(1, '1/gal'))
	esc = pf.InflationRateEscalator(rate = 0.01)
	sd = pf.dtFractionalStartupDiscounter(time_span = dt.timedelta(days=1*365), fraction = 0.75)
	pr1 = pf.Product(name = 'gasoline', description = 'People', quote_basis = QB, escalator = esc)
	pro1 = pf.Production(name = 'stream1', product = pr1, rate = uv.UnitVal(15000, 'gal/hr'), startup_discounter = sd, init_date = dt.datetime(2015,01,01))
	pro1.sch_args['term'] = dt.timedelta(10*366)			#This is kind of ugly, from an OO perspective; it gives waaaay too much insight into how this works -- fix later
	QB2 = pf.ProductQuoteBasis(base_price = 0.04*2.205, date = dt.datetime(2015,01,01), source = 'mag', scaler = scaler, size_basis = uv.UnitVal(1, '1/kg'))
	pr2 = pf.Product(name = 'char', description = 'coally waste', quote_basis = QB2, escalator = None)
	pro2 = pf.Production(name = 'stream2', product = pr2, rate = uv.UnitVal(150000, 'lb/day'), startup_discounter = None, init_date = dt.datetime(2015,01,01))
	pro2.sch_args['term'] = dt.timedelta(10*366)
	port = pf.ProductionPortfolio()
	port.add_production(pro1)
	port.add_production(pro2)
	port.detailed = True	
	port.build_production_schedule()
	
	

	dates = [dt.datetime(2015,01,01), dt.datetime(2017,03,25), dt.datetime(2024,12,31)]
	revenue_vals = [419101.05, 569160.2549, 614460.0904]
	

	for d,v in zip(dates, revenue_vals):
            
	    self.assertAlmostEqual(port.schedule.loc[d,'revenue'],v,1)

	for n in ['stream1_rate','stream1_price','stream1_revenue','stream2_rate','stream2_price','stream2_revenue','rate','price','revenue']:
	    self.assertIn(n, port.schedule.columns)
	self.assertTrue((port.schedule['stream1_price']== pro1.schedule['price']).all())
	self.assertTrue((port.schedule['stream1_rate']==pro1.schedule['rate']).all())
	self.assertTrue((port.schedule['stream1_revenue']== pro1.schedule['revenue']).all())
	self.assertTrue((port.schedule['stream2_price']==pro2.schedule['price']).all())
	self.assertTrue((port.schedule['stream2_rate']==pro2.schedule['rate']).all())
	self.assertTrue((port.schedule['stream2_revenue']==pro2.schedule['revenue']).all())

if __name__ == "__main__":
    unittest.main()
