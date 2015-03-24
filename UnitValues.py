import unitConversion as uc

class UnitValueError(Exception):
    pass

class BadUnitError(UnitValueError):
    pass

class BadValueError(UnitValueError):
    pass

class UnitVal(object):
    def __init__(self, value = None, units = None):
        self.value = value
        self.units = units

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, v):
        if v is not None and not isinstance(v, basestring):
            raise BadUnitError, "The units must be a basestring"

        self._units = v

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        try:
            if v is not None:
                v/25.3
	        v = float(v)
	    self._value = v
        except TypeError:
            self._value = None
            raise BadValueError, "The value must be numeric"
            

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
            raise TypeError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert_units(other.value, other.units, self.units)
            return UnitVal(self.value+rarg, self.units)
        except uc.InconsistentUnitError:
            raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)
     
    def __sub__(self, other):
        """Returns the difference of this with other, in this' units, as a UnitVal"""
        if not isinstance(other, UnitVal):
            raise TypeError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert_units(other.value, other.units, self.units)

	    
            return UnitVal(self.value-rarg, self.units)
        except uc.InconsistentUnitError:
            raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)
    """
    def __radd__(self, other):
        Returns the sum of this with other, in this' units, as a UnitVal
        if not isinstance(other, UnitVal):
            raise TypeError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert_units(self.value, self.units, other.units)
            return UnitVal(other.value+rarg, self.units)
        except uc.InconsistentUnitError:
            raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)

    def __rsub__(self, other):
        Returns the sum of this with other, in this' units, as a UnitVal
        if not isinstance(other, UnitVal):
            raise TypeError, "UnitVal cannot be added to %s" % type(other)
        conv = uc.UnitConverter()
        try:
            rarg = conv.convert_units(self.value, self.units, other.units)
            return UnitVal(other.value-rarg, self.units)
        except uc.InconsistentUnitError:
            raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)
    """
    def simplify_units(self):
	conv = uc.UnitConverter()
        simp_units = conv.simplify_units(self.units)
	self.value *= simp_units[0]
	self.units = simp_units[1]
	

	#self.value, self.units = conv.simplify_units(self.value, self.units)		#eliminates repeats of the same unit and returns


    def __mul__(self, other):
        """Returns the product of this with other, in this' units, as a UnitVal"""
        #Want to include the ability to do scalar multiplication as well as uv multiplication
	conv = uc.UnitConverter()
        if isinstance(other, UnitVal):
            
            try:
                #rarg = conv.convert_units(other.value, other.units, self.units)
		new_unit = "%s*%s" % (self.units, other.units)
		r = UnitVal(self.value * other.value, new_unit)
		r.simplify_units()
		return r
		#return (UnitVal(self.value * other.value, new_unit)).simplify_units()
                #return UnitVal(self.value * rarg, self.units)
            except uc.InconsistentUnitError:
                raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)

        else:
            #Need to verify that other is numeric by doing something you should only be able to do to numbers
            try:
                a = other * 2.3544
            except TypeError:
                raise TypeError, "UnitVal can only be multiplied by UnitVal or a scalar"
            return UnitVal(self.value * other, self.units)

    def __div__(self, other):
        """Returns the quotient of this by other, in this' units, as a UnitVal"""
	conv = uc.UnitConverter()
        if isinstance(other, UnitVal): 

            try:
                #divisor = conv.convert_units(other.value, other.units, self.units)
                if other.value == 0:
                    raise ValueError, "Divide by zero error"
		new_unit = "%s/(%s)" % (self.units, other.units)
		r = UnitVal(self.value/other.value, new_unit)
		r.simplify_units()
		return r
                #return (UnitVal(self.value/other.value, new_unit)).simplify_units()
            except uc.InconsistentUnitError:
                raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)
	else:
            try:
                a = other * 2.3544
            except TypeError:
                raise TypeError, "UnitVal can only be divided by UnitVal or a scalar"
            if other == 0:
                raise ValueError, "Divide by zero error"  #May want to make this np.inf instead
            return UnitVal(self.value/other, self.units)

    def __rmul__(self, other):
        """Returns the product of this with other, in others' units (if applicable), as a UnitVal"""
        #Want to include the ability to do scalar multiplication as well as uv multiplication
        conv = uc.UnitConverter()
        if isinstance(other, UnitVal):

            try:
                #rarg = conv.convert_units(self.value, self.units, other.units)
		new_unit = "%s*%s" % (self.units, other.units)
		r = UnitVal(self.value*other.value, new_unit)
		r.simplify_units()
		return r
		#return (UnitVal(self.value * other.value, new_unit)).simplify_units()
                #return UnitVal(other.value * rarg, other.units)
            except uc.InconsistentUnitError:
                raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)

        else:
            #Need to verify that other is numeric by doing something you should only be able to do to numbers
            try:
                a = other * 2.3544
            except TypeError:
                raise TypeError, "UnitVal can only be multiplied by UnitVal or a scalar"
            return UnitVal(self.value * other, self.units)

    def __rdiv__(self, other):
        """Returns the quotient of this by other, in this' units, as a UnitVal"""
	conv = uc.UnitConverter()
        if isinstance(other, UnitVal): 

            try:
                if self.value == 0:
                    raise ValueError, "Divide by zero error"
		new_unit = "%s/%s" % (self.units, other.units)
		r = UnitVal(other.value/self.value, new_unit)
		r.simplify_units()
		return r
                #return UnitVal(self.value/other.value, new_unit).simplify_units()
            except uc.InconsistentUnitError:
                raise TypeError, "Inconsistent units, %s, %s" % (other.units, self.units)
	else:
            try:
                a = other * 2.3544
            except TypeError:
                raise TypeError, "UnitVal can only be divided by UnitVal or a scalar"
            if self.value == 0:
                raise ValueError, "Divide by zero error"  #May want to make this np.inf instead
            new_units = "(%s)^-1" % self.units
            return UnitVal(other/self.value, new_units)
