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
        if isinstance(other, UnitVal):
            conv = uc.UnitConverter()
            try:
                rarg = conv.convert(other.value, other.units, self.units)
                return UnitVal(self.value * rarg, self.units)
            except uc.InconsistentUnitError:
                raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)

        else:
            #Need to verify that other is numeric by doing something you should only be able to do to numbers
            try:
                a = other * 2.3544
            except ValueError:
                raise ValueError, "UnitVal can only be multiplied by UnitVal or a scalar"
            return UnitVal(self.value * other, self.units)

    def __div__(self, other):
        """Returns the quotient of this by other, in this' units, as a UnitVal"""
        if isinstance(other, UnitVal): 
            conv = uc.UnitConverter()
            try:
                divisor = conv.convert(other.value, other.units, self.units)
                if divisor == 0:
                    raise ValueError, "Divide by zero error"
                return UnitVal(self.value/divisor, self.units)
            except uc.InconsistentUnitError:
                raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)
	else:
            try:
                a = other * 2.3544
            except ValueError:
                raise ValueError, "UnitVal can only be divided by UnitVal or a scalar"
            if other == 0:
                raise ValueError, "Divide by zero error"  #May want to make this np.inf instead
            return UnitVal(self.value/other, self.units)

    def __rmul__(self, other):
        """Returns the product of this with other, in others' units (if applicable), as a UnitVal"""
        #Want to include the ability to do scalar multiplication as well as uv multiplication
        if isinstance(other, UnitVal):
            conv = uc.UnitConverter()
            try:
                rarg = conv.convert(self.value, self.units, other.units)
                return UnitVal(other.value * rarg, other.units)
            except uc.InconsistentUnitError:
                raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)

        else:
            #Need to verify that other is numeric by doing something you should only be able to do to numbers
            try:
                a = other * 2.3544
            except ValueError:
                raise ValueError, "UnitVal can only be multiplied by UnitVal or a scalar"
            return UnitVal(self.value * other, self.units)

    def __rdiv__(self, other):
        """Returns the quotient of this by other, in this' units, as a UnitVal"""
        if isinstance(other, UnitVal): 
            conv = uc.UnitConverter()
            try:
                divisor = conv.convert(self.value, self.units, other.units)
                if divisor == 0:
                    raise ValueError, "Divide by zero error"
                return UnitVal(other.value/divisor, other.units)
            except uc.InconsistentUnitError:
                raise ValueError, "Inconsistent units, %s, %s" % (other.units, self.units)
	else:
            try:
                a = other * 2.3544
            except ValueError:
                raise ValueError, "UnitVal can only be divided by UnitVal or a scalar"
            if self.value == 0:
                raise ValueError, "Divide by zero error"  #May want to make this np.inf instead
            return UnitVal(other/self.value, self.units)
