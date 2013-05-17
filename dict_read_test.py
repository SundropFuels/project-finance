import csv
import numpy as np


if __name__ == "__main__":
    f = open('dict_read_test.csv')
    reader = csv.DictReader(f)
    arrs = {}
    for name in reader.fieldnames:
        arrs[name] = np.array([])
    for row in reader:
        for key in row:
            arrs[key] = np.append(arrs[key],float(row[key]))

    for name in reader.fieldnames:
        print arrs[name]


