import unitConversion as uc


class UnitVal:
    def __init__(self, value = None, units = None):
        self.value = value
        self.units = units

    def set_unit_class(self):
        """Will find out to what class of physical measurements (e.g. length, time, pressure, temperature, etc.) the units belong"""
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value and self.units == other.units

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        """Returns the sum of this with other, in this' units, as a UnitVal"""
        if not isinstance(other, UnitVal):
            raise ValueError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert(other, other.units, self.units)
            return UnitVal(self.value+rarg, self.units)
        except uc.InconsistentUnitError:
            raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)
     
    def __sub__(self, other):
        """Returns the difference of this with other, in this' units, as a UnitVal"""
        if not isinstance(other, UnitVal):
            raise ValueError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert(other, other.units, self.units)
            return UnitVal(self.value-rarg, self.units)
        except uc.InconsistentUnitError:
            raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)

    def __radd__(self, other):
        """Returns the sum of this with other, in this' units, as a UnitVal"""
        if not isinstance(other, UnitVal):
            raise ValueError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert(self.value, self.units, other.units)
            return UnitVal(other.value+rarg, self.units)
        except uc.InconsistentUnitError:
            raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)

    def __rsub__(self, other):
        """Returns the sum of this with other, in this' units, as a UnitVal"""
        if not isinstance(other, UnitVal):
            raise ValueError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert(self.value, self.units, other.units)
            return UnitVal(other.value-rarg, self.units)
        except uc.InconsistentUnitError:
            raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)

    def __mul__(self, other):
        """Returns the product of this with other, in this' units, as a UnitVal"""
        #Want to include the ability to do scalar multiplication as well as uv multiplication
        pass
