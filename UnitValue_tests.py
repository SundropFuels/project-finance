"""UnitValue_tests.py
Unit tests for the UnitValue set of objects
Chris Perkins
2015-03-24

"""

import UnitValues as uv
import unittest
import unitConversion as uc



class UnitValueTests(unittest.TestCase):
    
    
    def testCorrectUnitValueCreation(self):
	"""UnitVal must be correctly created"""
	a = uv.UnitVal(value = 35, units = 'gal')
	self.assertEqual(a.value, 35)
	self.assertEqual(a.units, 'gal')

    def testBadUnitValInitialization(self):
	"""Non-numeric values or non-string units should raise an error"""
	self.assertRaises(uv.BadValueError, uv.UnitVal, 'm', 'gal')
	self.assertRaises(uv.BadUnitError, uv.UnitVal, 35, 35)


    def testUnitValAddition(self):
	"""Two UnitVals should be correctly added"""
	a = uv.UnitVal(value = 35, units = 'gal')
        b = uv.UnitVal(value = 10, units = 'L')
        c = a+b
        d = b+a

        self.assertEqual(c.units, 'gal')
	self.assertEqual(d.units, 'L')

	self.assertAlmostEqual(c.value, 35+10/3.785, 1)
	self.assertAlmostEqual(d.value, 10+35*3.785, 1)


    def testUnitValAdditionNotSameUnit(self):
	"""UnitVals with different physical units should raise an error on addition"""
	a = uv.UnitVal(value = 35, units = 'gal')
	b = uv.UnitVal(value = 10, units = 'm')
	self.assertRaises(TypeError, lambda: a+b)
	self.assertRaises(TypeError, lambda: b+a)

    def testUnitValAdditionNotSameType(self):
	"""UnitVals should raise an error when attempting to add a non-UnitVal"""
        a = uv.UnitVal(value = 35, units = 'gal')
	b = 234
	self.assertRaises(TypeError, lambda: a+b)
	self.assertRaises(TypeError, lambda: b+a)

    def testUnitValSubtraction(self):
	"""Two UnitVals should be subtracted correctly"""
	a = uv.UnitVal(value = 35, units = 'gal')
        b = uv.UnitVal(value = 10, units = 'L')
        c = a-b
        d = b-a

        self.assertEqual(c.units, 'gal')
	self.assertEqual(d.units, 'L')

	self.assertAlmostEqual(c.value, 35-10/3.785, 1)
	self.assertAlmostEqual(d.value, 10-35*3.785, 1)

    def testUnitValSubtractionNotSameUnit(self):
	"""Two UnitVals with different physical units should raise an error on subtraction"""
	a = uv.UnitVal(value = 35, units = 'gal')
	b = uv.UnitVal(value = 10, units = 'm')
	self.assertRaises(TypeError, lambda: a-b)
	self.assertRaises(TypeError, lambda: b-a)

    def testUnitValSubtractionNotSameType(self):
	"""A UnitVal should raise an error when trying to subtract a non-UnitVal"""
        a = uv.UnitVal(value = 35, units = 'gal')
	b = 234
	self.assertRaises(TypeError, lambda: a-b)
	self.assertRaises(TypeError, lambda: b-a)

    def testUnitValMultiplication(self):
	"""UnitVals should multiply correctly, with proper units"""
	a = uv.UnitVal(value = 35, units = 'gal')
	b = uv.UnitVal(value = 10, units = '1/s')
	c = a * b
	c.simplify_units()
	d = b * a
	d.simplify_units()
	u = ['gal^1*s^-1','s^-1*gal^1']

	self.assertAlmostEqual(35*10, c.value,4)
	self.assertAlmostEqual(10*35, c.value,4)

        self.assertIn(c.units, u)
	self.assertIn(d.units, u)

    def testUnitValMultiplicationBadType(self):
	"""UnitVals should throw an error when not multiplied by scalars or other UnitVals"""
	a = uv.UnitVal(value = 35, units = 'gal')
	self.assertRaises(TypeError, lambda: a*'m')
	self.assertRaises(TypeError, lambda: 'm'*a)

    def testUnitValScalarMultiplication(self):
	"""UnitVals should correctly perform scalar multiplication"""
	a = uv.UnitVal(value = 35, units = 'gal')
	b = a * 100
	c = 100 * a
	self.assertEqual(b.value, 3500)
	self.assertEqual(c.value, 3500)
        self.assertEqual(b.units, 'gal')
	self.assertEqual(c.units, 'gal')

    def testUnitValDivision(self):
	"""UnitVals should correctly divide between them, with appropriate concatenated units"""
	a = uv.UnitVal(value = 35, units = 'gal')
	b = uv.UnitVal(value = 10, units = '1/s')
	c = a / b
	c.simplify_units()
	d = b / a
	d.simplify_units()
	u = ['gal^-1*s^-1','s^-1*gal^-1']
	v = ['gal^1*s^1', 's^1*gal^1']

	self.assertAlmostEqual(35.0/10.0, c.value,4)
	self.assertAlmostEqual(10.0/35.0, d.value,4)

        self.assertIn(c.units, v)
	self.assertIn(d.units, u)

    def testUnitValDivisionBadType(self):
	"""UnitVals should throw an error when trying to divide with a non-scalar/non-UnitVal"""
	a = uv.UnitVal(value = 35, units = 'gal')
	self.assertRaises(TypeError, lambda: a/'m')
	self.assertRaises(TypeError, lambda: 'm'/a)


    def testUnitValScalarDivision(self):
	"""UnitVals should properly perform scalar division, with inversion of the unit"""
        a = uv.UnitVal(value = 35.0, units = 'gal')
	b = a / 10
	c = 350 / a
	self.assertAlmostEqual(b.value, 3.5, 4)
	self.assertAlmostEqual(c.value, 10.0, 4)
        self.assertEqual(b.units, 'gal')
	self.assertEqual(c.units, '(gal)^-1')

    def testUnitValDivByZero(self):
	"""UnitVals should throw an error when trying to divide by zero or when a divisor UnitVal has a zero value"""
        a = uv.UnitVal(value = 35, units = 'gal')
	self.assertRaises(ValueError, lambda: a/0)
	a.value = 0
	self.assertRaises(ValueError, lambda: 35/a)

if __name__ == "__main__":
    unittest.main()

