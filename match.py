import csv

with open('MetObjects.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if row[0] == '250274' or row[0] == '250314' or '250274' in row[4]:
            print(dict(zip(header, row)))
            break
