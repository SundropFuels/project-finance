import numpy as np
import db_toolbox as SQL
import csv
from copy import deepcopy

class dfException(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class GlossaryError(Exception):
    pass

class BadGlossaryTagError(GlossaryError):
    pass

class BadGlossaryTypeError(GlossaryError):
    pass

class NoColumnError(dfException):
    pass

class BadArgumentError(dfException):
    pass

class UncertaintyError(dfException):
    pass

class Dataframe:

    def __init__(self, array_dict = None, units_dict = None, rows_list = None):
        """Constructor puts together the basic data structure, which includes a dictionary of arrays"""
        if array_dict is None:
            array_dict = {}

        if units_dict is None:
            units_dict = {}

        if type(array_dict) != dict:
            raise dfException, "Initialization argument must be a dictionary with values np arrays"
        for value in array_dict.values():
	    if type(value) != np.ndarray:
                    raise dfException, "Data frame requires numpy arrays as data types"
        if array_dict == {}:
            self.nCols = 0
            self.nRows = 0
            

        else:
            #Check to make sure all of the items are the same size
            s = array_dict.values()[0].size
            for value in array_dict.values():
                if value.size != s:
                    raise dfException, "Array_dict must have numpy vectors all of the same length"

            self.nCols = len(array_dict.keys())
            self.nRows = s

        
        self.data = array_dict.copy()
	

        for key in units_dict:
            if key not in self.data:
                raise dfException, "Unit given for non-existent column"

        for value in units_dict.values():
            if type(value) != str and value is not None:
                raise dfException, "Units must be given as strings"

        self.units = units_dict.copy()
        
	#Initialize row names, if given a row dictionary
        
        
        self.rows_dict = {}
	if rows_list is not None:
	    
            if not isinstance(rows_list, list):
                raise dfException, "An initialization rows list must be a list of strings"
            if len(rows_list) != self.nRows:
                raise dfException, "An initialization rows list must have the same number of row names as rows"
            index = 0
            for name in rows_list:
                self.rows_dict[name] = index
                index += 1




    def  __getitem__(self, index):
        """Returns the column of the numpy array with the given index name.  Index should be a string"""
        try:
            return self.data[index]
        except KeyError:
            raise NoColumnError, "The desired column was not existent"

    def __setitem__(self,key,item):
        if type(item) != np.ndarray:
            raise dfException, "Can only set numpy arrays as dictionary entries in dataframe"
        if self.data != {} and item.size != self.nRows:
            raise dfException, "Improper length of added vector"
        if key not in self.data:
            self.nCols += 1
        if self.data == {}:
            self.nRows = item.size

        self.data[key] = item

    def append(self,row, row_name = None):
        """Appends a row (dictionary) to existing dataframe.  Makes global np function less annoying"""
        if type(row) != dict:
            raise dfException, "Row must be a dictionary"

                  

        if len(row.keys()) != self.nCols and self.nCols > 0:
            raise dfException, "New row must have same number of columns as dataframe"

        if self.rows_dict or self.nCols == 0:
            if row_name is None:
                raise dfException, "Once you have a non-empty row_dictionary, ALL new rows must have a name"
            if row_name in self.rows_dict:
                raise dfException, "Row %s is already a used name in the row dataframe; cannot be appended" % row_name
            self.rows_dict[row_name] = self.nRows

        if self.nCols == 0:
            for key in row:
                self.data[key] = np.array([row[key]])
            self.nCols = len(row.keys())

        else:
            for key, value in row.items():
                
                try:    
                    self.data[key] = np.append(self.data[key],value)
                except KeyError:
                    raise dfException, "New row has a key mismatch with existing dataframe"
        self.nRows += 1

    def get_row(self, row_name):
        """Returns the row (as a dictionary) with the given row_name"""
        if row_name not in self.rows_dict:
            raise dfException, "Bad row name %s" % row_name
        ret_dict = {}
        for col in self.data.keys():
            ret_dict[col] = self.data[col][self.rows_dict[row_name]]
        return ret_dict

    def get_col(self, col_name):
        """Returns the column (as a dictionary), with row_names as the keys, for the given col_name"""
        retval = {}
        if col_name not in self.data:
            raise dfException, "Bad column name %s" % col_name
        for row in self.rows():
            retval[row] = self.get_row(row)[col_name]
        return retval

    def row_num(self, row_name):
        """Returns the row number for a given row name -- hides some of the internal workings --  a better version would return the element for a column, row combo"""
        if row_name not in self.rows_dict:
            raise dfException, "Bad row name %s" % row_name

        return self.rows_dict[row_name]

    def rows(self):
        """Returns a list of the row names"""
        return self.rows_dict.keys()

    def numrows(self):
        return self.nRows
       
    def numcols(self):
        return self.nCols


    def add_external_column(self, ext_dataframe, df_col, ext_df_col, extend = False):
        for row in ext_dataframe.rows():
            if row in self.rows():
                self[df_col][self.row_num(row)] += ext_dataframe[ext_df_col][ext_dataframe.row_num(row)]
            elif extend:
                pass  #This needs to be implemented
            else:
                raise dfException, "The current dataframe does not have row %s" % row

    def SQL_load_data(self, db_interface, table = "", conditions = None):
        """Allows the user to load the dataframe directly from a MySQL database; must pass interface"""
        if conditions is None:
            conditions = []
        query = SQL.select_Query(objects = ['*'], table = table, condition_list = conditions)
        results = db_interface.query(query)

        #intitialize numpy arrays
        for key, value in results[0].items():
            if type(results[0][key]) == float:
                #This is the 64-bit implementation
                self.data[key] = np.ndarray(0,dtype = 'float64')
            elif type(results[0][key]) == int:
                #This is the 64-bit implementation - could do arch check if necessary
                self.data[key] = np.ndarray(0,dtype = 'int64')
            else:
                #Catchall for everything else -- will make sure things fit okay
                self.data[key] = np.ndarray(0,dtype = 'object')

        #Build the arrays row by row
        for row in results:
            self.append(row)

    def glossary_replace(self, glossary = None):
        """Replace the names of the keys in the data frame with new keys in the glossary"""
        if glossary == None:
            glossary = {}

        if type(glossary) != dict:
            raise BadGlossaryTypeError, "The glossary must be a dictionary"

        
        for key in glossary.keys():
            if key not in self.data:
                raise BadGlossaryTagError, "There is a tag in the glossary that is not in the dataframe"

            self.data[glossary[key]] = self.data[key]
            del self.data[key]

    def set_units(self, units_dict = None):
        if units_dict == None:
            units_dict = {}

        for key in units_dict:
            if key not in self.data:
                raise dfException, "Unit given for non-existent column"

        for value in units_dict.values():
            if type(value) != str and value is not None:
                raise dfException, "Units must be given as strings"

        self.units = units_dict.copy()

    def filter_vals(self, column, v, action):
        if type(column) != str or not isinstance(v, (int, long, complex, float)) or type(action) != str:
            raise BadArgumentError, "The filter function received an argument not consistent with its parameter list"

        if action not in ('high', 'low'):
            raise BadArgumentError, "The action for a filter function must be either 'high' or 'low'"

        if column not in self.data.keys:
            raise NoColumnError, "The specified column is not in the dataframe"

        ret_val = self[column].copy()

        if action == 'high':
            ret_val[ret_val>v] = np.nan
        else:
            ret_val[ret_val<v] = np.nan

        return ret_val

    def calc_uncertainty(self, function, uncertainty_dict = None, **kwargs):
        """Returns a column of uncertainty values for the given determining function, given the list of uncertainty objects for various tags"""
        #The uncertainty dict should have the form {'function argument': ('type', value)} where 'type' is column, abs, or rel

        if uncertainty_dict == None:
            uncertainty_dict = {}

        #Find the base value (should be in the dataframe) -before- uncertainty is calculated
        base = function(**kwargs)
        
        #Iterate through the uncertainty list, calculating the deviations for each of the uncertainties in the uncertainty list
        dev_list = []
        for kw in kwargs.keys():
            old_val = kwargs[kw]
            if kw in uncertainty_dict.keys():
                if uncertainty_dict[kw][0] == 'column':
                    kwargs[kw] += self['u_%s' % uncertainty_dict[kw][1]]
                elif uncertainty_dict[kw][0] == 'abs':
                    kwargs[kw] += uncertainty_dict[kw][1]
                elif uncertainty_dict[kw][0] == 'rel':
                    kwargs[kw] += uncertainty_dict[kw][1]*kwargs[kw]
                else:
                    #raise an error
                    raise UncertaintyError, "The uncertainty dictionary has an inappropriate type: %s" % uncertainty_dict[kw][0]
            
                dev_list.append(np.power((function(**kwargs)-base),2))
                kwargs[kw] = old_val
                #if a keyword NOT in the uncertainty dictionary, assume it has uncertainty 0

        
        #Return the new uncertainty column

        return np.power(sum(dev_list),0.5)




class Uncertainty_Container:
    """This is the major structure that holds uncertainty information for a specific tag
    For raw items, it holds the name of the tag, the uncertainty value, and whether it is relative or absolute
    For calculated items, it holds the name of the tag and the function used to generate those items.
    """

    def __init__(self, tag_name = None, def_function = None, uncertainty = None):
        self.tag_name = tag_name
        self.def_function = def_function
        self.uncertainty = uncertainty

 
def generateDataframeFromCSV(csv_file, col_for_rows = None, col_list = None):
    """Returns a dataframe generated from a CSV.  Will add LoadDatafromCSV as well, but later; actually, will use pandas later"""
    #Just going to cast everything to a float to start here
    try:
        reader = csv.DictReader(csv_file)
    except Exception:
        raise Exception, "Need to implement exception handling for loading the csv file"
    
    try:
        if col_list is None:
            if col_for_rows is None:
                col_list = deepcopy(reader.fieldnames)
            else:
                col_list = deepcopy(reader.fieldnames)
                col_list.remove(col_for_rows)
      
        
    except Exception:
        raise Exception, "Need to implement exception handling for col_list and col_row handling"

    #now build the dataframe
    df = Dataframe()
    
    #Get the first row
    row = reader.next()
    
    #intitialize numpy arrays
    for key in col_list:
        #if type(row[key]) == float:
            #This is the 64-bit implementation
        
        df[key] = np.ndarray(0,dtype = 'float64')
        #elif type(row[key]) == int:
            #This is the 64-bit implementation - could do arch check if necessary
        #    df[key] = np.ndarray(0,dtype = 'int64')
        #else:
            #Catchall for everything else -- will make sure things fit okay
        #    df[key] = np.ndarray(0,dtype = 'object')
    new_row = {}    
    index = 0
    
    for key in col_list:
        new_row[key] = float(row[key])
        
    df.append(new_row)
    
    if col_for_rows is not None:
        df.rows_dict[index] = row[col_for_rows]

    #Build the rest of the dataframe row by row
    
    for row in reader:
        index += 1
        new_row = {}
        for key in col_list:
            new_row[key] = float(row[key])
        
        if col_for_rows is not None:
            df.append(new_row, row_name = row[col_for_rows])
        else:
            df.append(new_row)
    return df

"""
if __name__ == "__main__":
    print "testing this object -- really need to add unit tests, you know"
    frame = Dataframe()
    interface = SQL.db_interface(host = "localhost", user = "root", passwd = "udflyer87")
    interface.connect()
    q = SQL.use_Query('trial')
    interface.query(q)
    frame.SQL_load_data(interface, table = "lv_data")
    print frame['TE_1']
"""

if __name__ == "__main__":
    #print "testing the distribution object"
    #normal = NormalDistribution(0,1)
    #print "Value of cumulative probability halfway: %s" % normal.cum[5000,1]
    #(left1, right1) = binary_search_1D(normal.cum[:,0],-1.0)
    #(left2, right2) = binary_search_1D(normal.cum[:,0],1.0)
  
    #print normal.cum[left2,1] - normal.cum[left1,1]
    #print normal.sample_N(20)

    f = open('test_xfer.csv')
    frame = generateDataframeFromCSV(f, col_for_rows = 'Date')
    for col in frame.data:
        print frame[col]
    print frame.rows_dict
