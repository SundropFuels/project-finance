"""unitConverter_tests.py
Unit tests for the unit conversion tool
Chris Perkins
2015-03-24

"""

import unitConversion as uc
import unittest


class UnitConversionTests(unittest.TestCase):
    
    
    def testCorrectUnitConversion(self):
        """A UnitConverter should correctly convert units for a variety of sample units"""
        
	conv = uc.UnitConverter()
	self.assertAlmostEqual(conv.convert_units(2.0, "kg",'lb'),4.40925, 4)
	self.assertEqual(conv.convert_units(1.0, 'J/s', 'W'), 1.0)
	self.assertAlmostEqual(conv.convert_units(2.54, "cm", 'in'), 1.0,4)
	self.assertAlmostEqual(conv.convert_units(100.0, "L", 'm^3'), 0.1,4)
	self.assertAlmostEqual(conv.convert_units(152.3, "J/(kg^2)^-3", "Btu/(lb^2)^-3"), 152.3/1055.055*2.2046**6,2)  #This case covers weird combos of exponents
	self.assertEqual(conv.convert_units(2.0, "1/s", '1/hr'), 2.0*3600)

    def testNonsenseUnitConversionInput(self):
        """UnitConverter should raise an error on bad to and from unit strings"""
	conv = uc.UnitConverter()
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "324.3", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "324.3")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "%2", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "#@")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, 234, "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", 234)
	self.assertRaises(uc.BadExponentError, conv.convert_units, 1.0, "kg^m", "kg")
	self.assertRaises(uc.BadExponentError, conv.convert_units, 1.0, "kg", "kg^m")
	self.assertRaises(uc.BadExponentError, conv.convert_units, 1.0, "kg^%", "kg")
	self.assertRaises(uc.BadExponentError, conv.convert_units, 1.0, "kg", "kg^@")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg**m", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg*/m", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg+*m", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg-*m", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg(*m", "kg")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "kg**m")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "kg*/")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "kg+*")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "kg-/")
	self.assertRaises(uc.BadCharacterError, conv.convert_units, 1.0, "kg", "kg(*")





    def testUnfoundUnitConversionInput(self):
        """UnitConverter should raise an error when a unit is not in the dictionary"""
	conv = uc.UnitConverter()
	self.assertRaises(uc.UnitNotFoundError, conv.convert_units, 1.0, "canteloupe^2", "in")
	self.assertRaises(uc.UnitNotFoundError, conv.convert_units, 1.0, "in", "canteloupe^2")
	#This is, of course, a spot check, but I doubt anybody will ever add a unit that is a canteloupe

    def testIncompatibleUnits(self):
        """UnitConverter should raise an error when the conversion is between incompatible units"""
	conv = uc.UnitConverter()
	self.assertRaises(uc.InconsistentUnitError, conv.convert_units, 1.0, "m", "kg")

class UnitSimplificationTests(unittest.TestCase):

    def testCorrectUnitSimplification(self):
	"""UnitConverter should correctly reduce units in a variety of situations"""
	conv = uc.UnitConverter()
	#we are going to test a few things on spot -- not going to be exhaustive.
	simp1 = ['W']
	simp2 = ['kg^1*s^-3', 's^-3*kg^-1']	#note, this is a little buggy -- I wanted it to find W/m^2 (a flux), but it can't because it eliminates the common area term -- just be aware
	simp3 = ['kg^1*s^-4']
	simp4 = ['gal^2']
	simp5 = ['W^1']

	s1 = conv.simplify_units('W')
	s2 = conv.simplify_units('J/s/m^2')
	s3 = conv.simplify_units('kW/m^2*s^-1')
	s4 = conv.simplify_units('gal*gal')
	s5 = conv.simplify_units('Btu/s')

	self.assertAlmostEqual(s1[0],1.0)
	self.assertAlmostEqual(s2[0],1.0)
	self.assertAlmostEqual(s3[0],1000.0)
	self.assertAlmostEqual(s4[0],1.0)
	self.assertAlmostEqual(s5[0],1055.05585,4)

	self.assertIn(s1[1],simp1)
	self.assertIn(s2[1],simp2)
	self.assertIn(s3[1],simp3)
	self.assertIn(s4[1],simp4)
	self.assertIn(s5[1],simp5)

    def testNonsenseSimplificationInput(self):
	"""UnitConverter should raise an error if a given unit string is nonsense"""
	conv = uc.UnitConverter()
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "324.3")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "%2")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, 234)
	self.assertRaises(uc.BadExponentError, conv.simplify_units, "kg^m")
	self.assertRaises(uc.BadExponentError, conv.simplify_units, "kg^%")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "kg**m")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "kg*/m")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "kg+*m")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "kg-*m")
	self.assertRaises(uc.BadCharacterError, conv.simplify_units, "kg(*m")
	

    def testUnfoundSimplificationInput(self):
	"""UnitConverter should raise an error if the unit given is not in the unit dictionary"""
	conv = uc.UnitConverter()
	self.assertRaises(uc.UnitNotFoundError, conv.simplify_units, "canteloupe^2/kg")

    def testUnitySimplification(self):
	"""UnitConverter should handle unity seamlessly when units completely cancel"""
	conv = uc.UnitConverter()
	s1 = conv.simplify_units("gal/gal")
	s2 = conv.simplify_units("gal*1/gal")
	s3 = conv.simplify_units("hr/s")

	self.assertAlmostEqual(s1[0], 1.0)
	self.assertAlmostEqual(s2[0], 1.0)
	self.assertAlmostEqual(s3[0], 1.0)

	self.assertEqual(s1[1], '1')
	self.assertEqual(s2[1], '1')
	self.assertEqual(s3[1], '1')


if __name__ == "__main__":
    unittest.main()

