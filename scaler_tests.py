"""scaler_tests.py
Unit tests for Project Finance program
Chris Perkins
2012-04-17

split out 2015-03-17
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



class ScalerTests(unittest.TestCase):

    """
    -Correctly initialize
    -Throw error with bad input to scale function
    -Incompatible units
    -Non-positive scale values
    -Non-numeric scale values
    
    """
    def testCreateScaler(self):

	sc = pf.Scaler()
	self.assertEqual(sc.factor, 1.0)

    def testBadScalerInput(self):
	cs = pf.Scaler()
	kwargs = {'base_scale':uv.UnitVal(1.0, 'lb'), 'new_scale':uv.UnitVal('poof', 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'lb'), 'new_scale':uv.UnitVal(0.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'lb'), 'new_scale':uv.UnitVal(-1.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal('poof', 'lb'), 'new_scale':uv.UnitVal(1.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(-1.0, 'lb'), 'new_scale':uv.UnitVal(1.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(0.0, 'lb'), 'new_scale':uv.UnitVal(1.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'm'), 'new_scale':uv.UnitVal(1.0, 'lb'), 'base_price':1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'm'), 'new_scale':uv.UnitVal(2.0, 'm'), 'base_price':'poof'}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'm'), 'new_scale':uv.UnitVal(2.0, 'm'), 'base_price':0.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
	kwargs = {'base_scale':uv.UnitVal(1.0, 'm'), 'new_scale':uv.UnitVal(2.0, 'm'), 'base_price':-1.0}
	self.assertRaises(pf.BadScaleInput, cs.scale, **kwargs)
    
class LinearScalerTests(unittest.TestCase):

    """
    
    -Correctly scale value
    -Throw error on bad scaler input
    """

    def testCorrectScale(self):
	sc = pf.LinearScaler()
	ns = sc.scale(base_scale = 1.0, new_scale = 3.0, base_price = 10.0)
	self.assertEqual(ns, 30.0)

    def testBadInput(self):
	"""Spot check that derived class will throw the same error as the parent class"""
	kwargs = {'base_scale':uv.UnitVal(1.0, 'm'), 'new_scale':uv.UnitVal(2.0, 'm'), 'base_price':0.0}
	self.assertRaises(pf.BadScaleInput, sc.scale, **kwargs)

class ExponentialScalerTests(unittest.TestCase):

    """
    -Test correct initialization
    -Throw error on bad values for initialization
    -Correctly scale value
  
    """
    def testExponentialScalerIntialization(self):
	sc = pf.ExponentialScaler(exponent = 0.2)
	self.assertEqual(sc.exponent, 0.2)

    def testBadInitializationInput(self):
	self.assertRaises(pf.BadScalerInitialization, sc.ExponentialScaler, -1.0)
	self.assertRaises(pf.BadScalerInitialization, sc.ExponentialScaler, 'poof')


    def testCorrectScale(self):
	sc = pf.ExponentialScaler(exponent = 0.6)
	ns = sc.scale(base_scale = 1.0, new_scale = 3.0, base_price = 10.0)
	self.assertEqual(ns, 30.0*3**0.6)



class NoneScalerTests(unittest.TestCase):

    """
    -Correctly scale value
    
    """ 

    def testCorrectScale(self):
        sc = pf.NoneScaler()
	self.assertEqual(10.0, sc.scale(base_scale = 1.0, new_scale = 3.0, base_price = 10.0))


class SteppedScalerTests(unittest.TestCase):

    """
    -Properly initialize
    -Correctly scale value
    -Throw error on bad scaler input
    """ 
    
    def testSteppedInitialization(self):
	pw = {-np.Inf:1.0, 'noosh':1.2}
	self.assertRaises(pf.BadScalerInitialization, pf.SteppedScaler, pw)
	pw = {-np.Inf:1.0, 1.2:'noosh'}
	self.assertRaises(pf.BadScalerInitialization, pf.SteppedScaler, pw)
	pw = {-np.Inf:1.0, 1.2:-1.0}
	self.assertRaises(pf.BadScalerInitialization, pf.SteppedScaler, pw)

    def testCorrectScale(self):
	pw = {-np.inf:1.0, 1.5:1.1, 2.0:1.5}
        sc = pf.SteppedScaler(steps = pw)
        self.assertEqual(1.0, sc.scale(base_scale = 1.0, new_scale = 1.3, base_price = 1.0))
	self.assertEqual(1.0, sc.scale(base_scale = 1.0, new_scale = 0.4, base_price = 1.0))
	self.assertEqual(1.0*1.1, sc.scale(base_scale = 1.0, new_scale = 1.6, base_price = 1.0))
	self.assertEqual(1.0*1.1, sc.scale(base_scale = 1.0, new_scale = 1.5, base_price = 1.0))
	self.assertEqual(1.0*1.5, sc.scale(base_scale = 1.0, new_scale = 2.2, base_price = 1.0))
	self.assertEqual(1.0*1.5, sc.scale(base_scale = 1.0, new_scale = 2.0, base_price = 1.0))


    
if __name__ == "__main__":
    unittest.main()
