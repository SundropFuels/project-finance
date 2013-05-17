import numpy as np
import dataFrame_v2 as df

if __name__ == "__main__":
    a = np.arange(100)
    b = np.arange(100)
    b = b + 10
    array_dict = {'a':a,'b':b}
    c = []
    year1 = 2000
    for i in range(100):
        c.append(i+year1)
    frame = df.Dataframe()
    for i in range(100):
        frame.append(row = {'a':a[i], 'b':b[i]},row_name=c[i])
        
    #print frame['a']
    print "Row 2008: %s" % frame.get_row(2008)

    #frame.append(row={'a':25,'b':37},row_name=2100)
    #print "Row 2100: %s" % frame.get_row(2100)


