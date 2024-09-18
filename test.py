import pandas as pd
import sys

csv_file_path = sys.argv[1]

df = pd.read_csv(csv_file_path)
print(type(df))
print(df)