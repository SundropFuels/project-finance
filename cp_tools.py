#cp_tools.py
#Simply python tools that might come in handy!
#Chris Perkins
#2012-05-29

#Version 1.0
#Implements is_numeric function to check if a type is numeric operable
#Implements a numpy array equality check



def is_numeric(obj):
    """Checks if obj is operable as a numeric object"""
    try:
        f = obj + 1
        return True
    except Exception:
        return False


def numpy_arrays_equal(arr1, arr2):
    """Check if two arrays are equal"""
    bit = True

    #Should check if these are array-like objects here


    #Make sure they are of the same length
    if len(arr1) != len(arr2):
        raise Exception, "Cannot evaluate the equality of two arrays not of the same length"

    #For each element, make sure the elements are equal
    for i in range(0,len(arr1)):
        if arr1[i] != arr2[i]: 
            bit = False


    return bit
