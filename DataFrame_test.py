"""Unit tests for Dataframe.py"""

import dataFrame_v2 as df
import unittest
import numpy as np


class CorrectInitialization(unittest.TestCase):
    def testCorrectInitialization(self):
        """The data in the data frame should match the data in the array_dict"""
        a = np.arange(100)
        b = np.arange(100)
        b = b + 10
        array_dict = {"item1":a,"item2":b}
        frame = df.Dataframe(array_dict = array_dict)
        for key, value in frame.data.items():
            self.assertEqual(frame.data[key].all(),array_dict[key].all())

    def testCorrectInitializationRows(self):
        """The data in the data frame should match the data in the array_dict, and allow for rows"""
        a = np.arange(100)
        b = np.arange(100)
        b = b + 10
        array_dict = {"item1":a,"item2":b}
        c = []
        year1 = 2000
        for i in range(100):
            c.append(i+year1)
        frame = df.Dataframe(array_dict = array_dict, rows_list = c)
        for key,value in frame.data.items():
            self.assertEqual(frame.data[key].all(), array_dict[key].all())
        
    def testBadArrayDict(self):
        """Dataframe should not intialize correctly is array_dict is not a dict"""
        array_dict = 3
        self.assertRaises(df.dfException, df.Dataframe, array_dict)
       
    def testBadArrayDictType(self):
        """Dataframe should not initialize correctly if every element in array_dict is not a numpy array"""
        a = np.ndarray(10)
        b = "test string"
        array_dict = {"item1":a,"item2":b}
        self.assertRaises(df.dfException, df.Dataframe, array_dict)
    
    def testBadArrayLength(self):
        """All of the numpy vectors should be of the same length"""
        a = np.arange(10)
        b = np.arange(11)
        array_dict = {"item1":a,"item2":b}
        self.assertRaises(df.dfException, df.Dataframe, array_dict)

    def testBadRowsList(self):
        """The rows list must be a list"""
        a = np.arange(100)
        b = np.arange(100)
        b = b + 10
        array_dict = {"item1":a,"item2":b}
        c = 'a'
        self.assertRaises(df.dfException, df.Dataframe, array_dict, None, c)
        

    def testBadRowsListLength(self):
        """The data in the data frame should match the data in the array_dict, and allow for rows"""
        a = np.arange(100)
        b = np.arange(100)
        b = b + 10
        array_dict = {"item1":a,"item2":b}
        c = []
        year1 = 2000
        for i in range(99):
            c.append(i+year1)
        self.assertRaises(df.dfException, df.Dataframe, array_dict, None, c)
        

    


class DictAccessorTests(unittest.TestCase):
    a = np.arange(10)
    b = np.arange(10)
    array_dict = {"a":a, "b":b}
    data = df.Dataframe(array_dict)
    c = []
    year1 = 2000
    for i in range(10):
        c.append(i+year1)
    data2 = df.Dataframe(array_dict, None, c)

    #There are MAJOR errors here in the use of "self" -- I'm not really checking anything in the data frames!!!
    def testSetNewItemCorrect(self):
        """Make sure the item set to a new key matches the item held in the data frame"""
        c = np.arange(10)
        c = c + 10
        self.data['c'] = c
        self.assertEqual(c.all(),self.data['c'].all())
                
    def testSetItemBadInputType(self):
        """A new column must be a numpy array"""
        c = "fart"
        self.assertRaises(df.dfException, self.data.__setitem__,'c', c)

    def testSetItemBadInputLength(self):
        """A new column must be the right length"""
        c = np.arange(2)
        self.assertRaises(df.dfException, self.data.__setitem__,'c',c)
        #consider tests for when you try to set an EXISTING column

    def testSetExistingItemCorrect(self):
        """A replacement for an existing column must equal the np array replacing it"""
        c = np.arange(10)
        c = c + 10
        self.data['b'] = c
        self.assertEqual(c.all(), self.data['b'].all())
    
    def testGetItemCorrect(self):
        """The data returned by __getdata__ must match the actual data"""
        self.assertEqual(self.data.data['a'].all(), self.data['a'].all())

    def testGetRowCorrect(self):
        """The data returned by get_row must match the actual data"""
        row_2003 = {'a':3, 'b':3}
        self.assertEqual(DictAccessorTests.data2.get_row(2003), row_2003)

class AppendRowTests(unittest.TestCase):
    a = np.arange(10)
    b = np.arange(10)
    array_dict = {"a":a, "b":b}
    

    def testAppendedRowCorrect(self):
        """The appended row must match the row that was passed to Dataframe.append()"""
        data = df.Dataframe(self.array_dict)
        new_row = {"a":2, "b":3}
        data.append(new_row)
        for key, value in data.data.items():
            self.assertEqual(data[key][-1], new_row[key])

    def testNewRowNumber(self):
        """After append, the dataframe must have the right number of rows"""
        a = np.arange(10)
        b = np.arange(10)
        array_dict = {"a":a, "b":b}
        data = df.Dataframe(array_dict)
        new_row = {"a":2, "b":3}
        data.append(new_row)
        for key, value in data.data.items():
            self.assertEqual(data.nRows, data[key].size)

    def testBadRowInputType(self):
        """Type mismatch between append argument and numpy array must raise exception"""
        a = np.arange(10)
        b = np.arange(10)
        array_dict = {"a":a, "b":b}
        data = df.Dataframe(array_dict)
        new_row = {"a":"f", "b":"u"}
        self.assertRaises(df.dfException, data.append, new_row)

    def testBadRowInputLength(self):
        """Having the wrong length of row to append (not enough/too many keys) should raise an error"""
        data = df.Dataframe(self.array_dict)
        new_row = {"a":2}
        self.assertRaises(df.dfException, data.append, new_row)

    def testBadRowKeys(self):
        """Having a mismatch in keys should raise an error"""
        a = np.arange(10)
        b = np.arange(10)
        array_dict = {"a":a, "b":b}
        data = df.Dataframe(array_dict)
        new_row = {"a":2, "f":4}
        self.assertRaises(df.dfException, data.append, new_row)

class RowQuantifiers(unittest.TestCase):
    a = np.arange(10)
    b = np.arange(10) + 2
    array_dict = {"a":a, "b":b}

    def testRowNumsEmpty(self):
        """When array dict is empty, the number of rows should be given as zero"""
        data = df.Dataframe()
        self.assertEqual(data.numrows(), 0)
        
    def testRowNumsInitialized(self):
        """When initialized with an array_dict, the proper number of rows should be listed"""
        data = df.Dataframe(self.array_dict)
        self.assertEqual(data.numrows(), 10)    
        
    def testColNumsEmpty(self):
        """When initialized with an empty array_dict, the proper number of columns should be listed"""
        data = df.Dataframe()
        self.assertEqual(data.numcols(), 0)

    def testColNumsIntialized(self):
        """When initialized with an array_dict, the proper number of columns should be listed"""
        a = np.arange(10)
        b = np.arange(10) + 2
        array_dict = {"a":a, "b":b}
        data = df.Dataframe(array_dict)
        self.assertEqual(data.numcols(), 2)

    def testColNumsAfterColumnAdd(self):
        """After adding a column, the number of columns should be incremented by one"""
        data = df.Dataframe(self.array_dict)
        c = np.arange(10)
        data['c'] = c
        self.assertEqual(data.numcols(), 3)
"""
class SQLDataLoad(unittest.TestCase):
    def testBadTableName(self):
        pass
    def testConditionsNotList(self):
        pass
    def testConditionsNotStrings(self):
        pass
    def testConditionsBadDB(self):
        pass
    def testInterfaceBadType(self):
        pass
    def testInterfaceNotConnected(self):
        pass
    def testDatabaseNotConnected(self):
        pass
    def testKeysLoadedCorrectly(self):
        pass
    def testDataLoadedCorrectly(self):
        pass
"""

if __name__ == "__main__":
    unittest.main()
    
