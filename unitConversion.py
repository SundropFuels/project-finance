"""Unit conversion module for Python"""

import numpy as np
import itertools as it
import copy

class UnitError(Exception):
    pass

class BadCharacterError(UnitError):
    pass

class EmptyUnitError(UnitError):
    pass

class UnitNotFoundError(UnitError):
    pass

class InconsistentUnitError(UnitError):
    pass

class BadExponentError(UnitError):
    pass

class UnitConverter:
    """This class converts arbitrary fundamental units from one to the other"""

    mass_dict = {'kg':1.0,'g':1000.0, 'lb':2.20462,'mg':1000000.0}
    time_dict = {'hr':1.0/3600.0, 'min':1.0/60.0, 's':1.0, 'day':1.0/(24.0*3600.0)}
    length_dict = {'m':1.0, 'in':39.37, 'mm':1000.0, 'cm':100.0, 'ft' : 39.37/12.0}
    mole_dict = {'mol':1.0}
    temperature_dict = {'K': 1.0, 'C': 1.0, 'R': 1.8, 'F': 1.8}
    money_dict = {'$':1.0}
    unity_dict = {'1':1.0}

    energy_dict = {'J':1.0, 'kJ':0.001, 'MJ':1E-6, 'cal':0.238845896628, 'kcal':238.845896628, 'Btu':9.47817120313E-4, 'MMBtu':9.47817120313E-10}
    energy_units = 'kg*m^2/s^2'    
    energy_pref_u = 'J'

    pressure_dict = {'Pa':1,'psi':1.4503773773E-4, 'bar':1E-5, 'atm':9.86923266716E-6, 'mmHg':0.007500616827, 'mmH2O':0.101971621298, 'inH2O':0.00401463076}
    pressure_units = 'kg/s^2/m'
    pressure_pref_u = 'Pa'

    volume_dict = {'L':1000.0, 'gal':264.172052358}
    volume_units = 'm^3'
    volume_pref_u = 'L'

    power_dict = {'W':1, 'kW':0.001, 'MW':1E-6, 'mW':1000}
    power_units = 'kg*m^2/s^3'
    power_pref_u = 'W'


    units = [mass_dict, time_dict, length_dict, mole_dict, temperature_dict, money_dict]
    derived_units = [(energy_units, energy_dict),(pressure_units,pressure_dict),(volume_units,volume_dict),(power_units,power_dict)]
    derived_preferred_units = [energy_pref_u, pressure_pref_u, volume_pref_u, power_pref_u]

    non_abs_temp_factors = {'K':0, 'C':-273.15, 'R':0, 'F':-459.67}

    
    
    temp_units = ['R', 'C', 'K', 'F']

    def __init__(self):
        self.unit_list = []


    def simplify_units(self, unit):
	"""Returns a reduced unit string for the given unit"""
        parsed = self._parse_inputstr(unit)
	#Now I have a list of (unit, exponent) tuples

	#Strategy1: 
	#Parse the string
	#Determine the preferred units?  maybe?
	#Shift the derived units to base units, tack onto the list
	#File the list into base unit buckets
	#Add the exponents
	#Search for derived unit permutations among the derived unit set, rewrite in terms of those
	#Recast in terms of preferred units
	#Calculate the return factor


        

	if len(parsed) == 1:
            return (1.0,unit)

	simplified_list = [0] * len(UnitConverter.units)
	self.unit_names = [None] * len(UnitConverter.units)
	dunit_names = copy.deepcopy(UnitConverter.derived_preferred_units)
	found = False
	for (u, exponent) in parsed:
                    

            for (base_units, unit_dict) in UnitConverter.derived_units:
                for (key,value) in unit_dict.items():
                    if u == key:
                        found = True
                        dunit_names[UnitConverter.derived_units.index((base_units,unit_dict))] = u	#uses the first derived unit it encounters as the preferred unit
                        parsed_sub = self._parse_inputstr(base_units)
                        for st, exponent2 in parsed_sub:
                            parsed.append((st, float(exponent2)*float(exponent)))

                if found == True:
                    break

            
            for unit_dict in UnitConverter.units:
                for (key, value) in unit_dict.items():
                    if u == key:
                        
                        found = True
                        simplified_list[UnitConverter.units.index(unit_dict)] += exponent
			if self.unit_names[UnitConverter.units.index(unit_dict)] is None:
			    self.unit_names[UnitConverter.units.index(unit_dict)] = u		#uses the first base unit it encounters as the natural unit -- can do the same above for derived units


                        break
                if found == True:
                    break

            if found == False:
                raise UnitNotFoundError, "The unit %s is not in the database" % u
            found = False

	found = False

	#Now we should have a list of the net exponents; it should be easy to write a new string for this
	out_string = ""
	for unit_dict in UnitConverter.units:
	    if simplified_list[UnitConverter.units.index(unit_dict)] != 0:
	        out_string += "%s^%s*" % (self.unit_names[UnitConverter.units.index(unit_dict)], simplified_list[UnitConverter.units.index(unit_dict)])
        out_string = out_string[:-1]
	#right now, this is where I'm stopping -- I can search for derived units when I have this working

	#ok -- now we want to look for derived units
	#the simplified_list contains [[exponent1],[exponent2],[exponent3],...] for the base units involved here
	#if we iterate over the absolute value of the exponents, starting at the highest value from the first base unit, we can cover all combinations
	#The combinations here are given by the itertools.combinations library, which we want to sort from longest to shortest
	#We'll create all of the combinations, then sort them by the sum of their exponents.  That is what we'll do.
	#[[4,1,0], [3,1,0], [2,1,0], [1,1,0], [4,0,0], ...]
	
        drv_list = [0] * len(UnitConverter.derived_units)
        (simplified_list, derived_list) = self._find_derived_units(simplified_list, drv_list)


        out_string = ""
        for unit_dict in UnitConverter.units:
            if simplified_list[UnitConverter.units.index(unit_dict)] != 0:
                out_string += "%s^%s*" % (self.unit_names[UnitConverter.units.index(unit_dict)], simplified_list[UnitConverter.units.index(unit_dict)])

        for (base_unit, unit_dict) in UnitConverter.derived_units:
            if derived_list[UnitConverter.derived_units.index((base_unit,unit_dict))] != 0:
                out_string += "%s^%s*" % (dunit_names[UnitConverter.derived_units.index((base_unit,unit_dict))], derived_list[UnitConverter.derived_units.index((base_unit,unit_dict))])
        out_string = out_string[:-1]

        
	return (self.convert_units(1.0,unit,out_string),out_string)

    def _find_derived_units(self, smp_list, drv_list):
        """Determines whether a simplified unit expression in base units can be expressed in more complicated derived units.
           Searches the most complex units first.  smp_list is a list of exponents for base units in the simplified expression,
           ordered by the unit dictionary at the top.  Ordering is implicit.  drv_list is the list of exponents for derived
           units in the new expression, ordered by its unit dictionary at the top, with implicit ordering.
           Returns (smp_list,drv_list) tuple, with a new simplified list and derived list)"""
        lsl = self._simp_list(smp_list)		#this will have the simplified list, now we need to organize it by exponential sum
        lsl_d = {lsl.index(lsl_i):sum(lsl_i) for lsl_i in lsl}
	lsl_s = sorted(lsl_d, key = lsl_d.get)		#this is the sorted list of indices in simplified_list -- we want to work it in reverse order
        N = len(lsl_s) - 1
        
	while N >0:
            #build the unit string
            u_string = ""
	    temp_list = lsl[lsl_s[N]]

	    for unit_dict in UnitConverter.units:
                i = UnitConverter.units.index(unit_dict)
                if temp_list[i] != 0:
                    u_string += "%s^%s*" % (self.unit_names[i], int(temp_list[i]*np.sign(smp_list[i])))
            u_string = u_string[:-1]			#this should be the simplified unit string, now we'll test it against all of the base units in the derived dictionary
            N -= 1
	    
	    
	    for bu, dd in UnitConverter.derived_units:
                try:
                    self.convert_units(1.0, u_string, bu)	#this attempts to convert between the base unit in the derived dictionary and the subunit string
                    #now strip out the derived unit from the simplified_list and tag the derived unit onto the new parsed list -- easier said than done
		    ###!!!###
                    #increment the derived unit by one
                    drv_list[UnitConverter.derived_units.index((bu,dd))] += 1
		    #parse the string to get the exponents
                    dec = self._parse_inputstr(u_string)
                    for (u,exponent) in dec:
                        for unit_dict in UnitConverter.units:
                            if u in unit_dict:
                                smp_list[UnitConverter.units.index(unit_dict)] -= exponent
                                break
		                #return the list with the function called on itself with the shorter list
                            #this should be safe -- base units should have already been vetted if I get here, so u should not NOT be in a unit_dict
                    return self._find_derived_units(smp_list, drv_list)
                except InconsistentUnitError:
                    #flip it around
                    try:
                        self.convert_units(1.0, u_string, "(%s)^-1" % bu)
                        drv_list[UnitConverter.derived_units.index((bu,dd))] -= 1
                        dec = self._parse_inputstr(u_string)
                        for (u,exponent) in dec:
                            for unit_dict in UnitConverter.units:
                                if u in unit_dict:
                                    smp_list[UnitConverter.units.index(unit_dict)] -= exponent
                                    break
                        return self._find_derived_units(smp_list,drv_list)

                    except InconsistentUnitError:
                        pass
        
            #didn't find any derived units.  Just return the simplified list and the derived unit list

        
        return (smp_list, drv_list)    

    def _simp_list(self, ll):
        rlist = []


        #need a base case here

        if len(ll) == 1:
            for j in range(0,int(abs(ll[0]))+1):
                rlist.append([j])
            return rlist
    
        #iterating case
        
        for i in range(0, int(abs(ll[0]))+1):       #if this were zero, it would skip it
            sl = self._simp_list(ll[1:])		#want this to return a list of lists, with exponents at the appropriate location
            for l in sl:
                l.insert(0,i)
            rlist.extend(sl)
        
        return rlist

        
    
    def _derived_unit_replace(self, unit):
        """Takes derived units (N, J, etc.) and replaces them with new text representing the fundamental units"""
        #Search through the dictionary and see if the given unit is a derived unit
        #Return text for the fundamental unit  #THIS IS NOT WORKING YET!!!!!!!!!!!!
        if unit in UnitConverter.derived_units.keys():
            return UnitConverter.derived_units[unit]
        else:
            return unit

    def convert_units(self, val, from_str, to_str):
        from_parsed = self._parse_inputstr(from_str)
        to_parsed = self._parse_inputstr(to_str)
        
        if len(from_parsed) == 1:
            if from_parsed[0][0] in UnitConverter.temp_units and from_parsed[0][1] == 1:
                if to_parsed[0][0] in UnitConverter.temp_units and len(to_parsed) == 1 and to_parsed[0][1] == 1:
                    ret_val = val - UnitConverter.non_abs_temp_factors[from_parsed[0][0]]
                    ret_val = ret_val / UnitConverter.temperature_dict[from_parsed[0][0]]
                    ret_val = ret_val * UnitConverter.temperature_dict[to_parsed[0][0]]
                    ret_val = ret_val + UnitConverter.non_abs_temp_factors[to_parsed[0][0]]
                    return ret_val
                else:
                    raise InconsistentUnitError, "The units were not consistent for this temperature conversion"
            #Do nothing if it is not a direct temperature conversion; we could put gauge pressure conversions here, as well

        found = False

        consistency_list = [0] * len(UnitConverter.units)

        factor = 1.0
        for (unit, exponent) in from_parsed:
            
            
            #Check if the unit is in the derived_unit dictionaries first

            for (base_units, unit_dict) in UnitConverter.derived_units:
                for (key,value) in unit_dict.items():
                    if unit == key:
                       
                        factor = factor / np.power(value, float(exponent))
                        found = True
                        
                        parsed_sub = self._parse_inputstr(base_units)
                        for st, exponent2 in parsed_sub:
                            from_parsed.append((st, float(exponent2)*float(exponent)))

                if found == True:
                    break

            
            for unit_dict in UnitConverter.units:
                for (key, value) in unit_dict.items():
                    if unit == key:
                        factor = factor / np.power(value, float(exponent))
                        found = True
                        consistency_list[UnitConverter.units.index(unit_dict)] += exponent


                        break
                if found == True:
                    break

            if found == False:
                raise UnitNotFoundError, "The unit %s is not in the database" % unit
            found = False

        

        for (unit, exponent) in to_parsed:
            
            for (base_units, unit_dict) in UnitConverter.derived_units:
                for (key,value) in unit_dict.items():
                    if unit == key:
                        
                        factor = factor * np.power(value, float(exponent))
                        found = True
                        
                        parsed_sub = self._parse_inputstr(base_units)
                        for st, exponent2 in parsed_sub:
                            to_parsed.append((st, float(exponent2)*float(exponent)))

                if found == True:
                    break

            

            for unit_dict in UnitConverter.units:
                for (key, value) in unit_dict.items():
                    if unit == key:
                        factor = factor * np.power(value, float(exponent))
                        found = True
                        consistency_list[UnitConverter.units.index(unit_dict)] += -exponent
                        break
                if found == True:
                    break


            
            if found == False:
                raise UnitNotFoundError, "The unit %s is not in the database" % unit
            found = False

       

        for checksum in consistency_list:
            if checksum != 0:
                raise InconsistentUnitError, "The to and from units do not match"


        
        return val * factor

        

    def _parse_inputstr(self, i_string):
        """Parser for arbitrary symbolic mathematical expressions of units"""

        operators = ['*','/','^','(',')']
        number_sym = ['.', '-']
        parsed_units = []      
        sub_parsed = None
        last_char = ""
        current_unit = ""
        current_exp_str = ""
        current_exp = 1
        i = 0
        while i < len(i_string):
            current_char = i_string[i]
            if current_char not in operators:
                
                if not current_char.isalpha() and current_char != '$' and current_char != '1':
                    raise BadCharacterError, "Unit names can only contain alphabetical characters"
                else:
                    current_unit = "".join([current_unit, current_char])
                    
                    last_char = current_char
                    i += 1
                    
            else: 
                if current_char == '*' or current_char == '/':
                    
                    
                    if sub_parsed is not None:
                        for (u,e) in sub_parsed:
                            e = e * current_exp
                            parsed_units.append((u,e))
                        sub_parsed = None
                    else:
                        if current_unit == "":
                            raise EmptyUnitError, "Cannot add an empty unit"
                        parsed_units.append((current_unit, current_exp))
                    current_unit = ""
                    current_exp = 1
                    if current_char == '/':
                        current_exp = -1
                    i += 1
                
                elif current_char == '^':
                                       
                    while (i+1) < len(i_string) and (i_string[i+1] in number_sym or i_string[i+1].isdigit()):
                        i += 1
                        current_exp_str = "".join([current_exp_str, i_string[i]])
                    try:
                        current_exp = current_exp * float(current_exp_str)
                        current_exp_str = ""
                    except ValueError:
                        raise BadExponentError, "The exponent for %s was formatted incorrectly" % current_unit
                    if (i+1) < len(i_string) and i_string[i+1] not in operators:
                        #There are still more characters to come, so I want to make sure the next character is an operator
                        raise BadCharacterError, "An improper character followed the exponent string"
                    i += 1

                elif current_char == '(':
                    #get the substring
                    paren_level = 1
                    j = i
                    while paren_level > 0:
                        j += 1
                        if i_string[j] == '(':
                            paren_level += 1
                        elif i_string[j] == ')':
                            paren_level -= 1
                    
                    sub_parsed = self._parse_inputstr(i_string[i+1:j])
                    i = j + 1      #move to the next i
                    

        if sub_parsed is not None:
            for (u,e) in sub_parsed:
                e = e * current_exp
                parsed_units.append((u,e))
            sub_parsed = None
        else:
            if current_unit == "":
                raise EmptyUnitError, "Cannot add an empty unit"
            parsed_units.append((current_unit, current_exp))
        return parsed_units

if __name__ == '__main__':
   conv = UnitConverter()
   print "3 m^3 to L: %s" % conv.convert_units(3, 'm^3', 'L')


                        

                
                    
