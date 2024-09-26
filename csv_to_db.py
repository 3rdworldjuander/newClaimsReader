import sqlite3
import csv
from io import StringIO

# The string provided
data_string = """Service Date,Start Time,End Time,Service Auth
09/09/2024,11:19 AM,12:19 PM,12510933
09/09/2024,12:20 PM,01:20 PM,12510933
09/10/2024,11:17 AM,12:17 PM,12510933
09/10/2024,12:18 PM,01:18 PM,12510933
09/11/2024,11:17 AM,12:17 PM,12510933
09/11/2024,12:18 PM,01:18 PM,12510933
09/12/2024,11:12 AM,12:12 PM,12510933
09/12/2024,12:13 PM,01:13 PM,12510933
09/13/2024,11:12 AM,12:12 PM,12510933
09/13/2024,12:13 PM,01:13 PM,12510933"""

# Step 1: Parse the CSV string
data = csv.reader(StringIO(data_string))
headers = next(data)  # Skip the header row

# Step 2: Create a database and table
conn = sqlite3.connect('services.db')  # Connects to a database file
cur = conn.cursor()

# Create a table if not exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS services (
        service_date TEXT,
        start_time TEXT,
        end_time TEXT,
        service_auth TEXT
    )
''')

# Step 3: Insert the data into the database
for row in data:
    cur.execute('INSERT INTO services (service_date, start_time, end_time, service_auth) VALUES (?, ?, ?, ?)', row)

# Commit the transaction and close the connection
conn.commit()
conn.close()

print("Data inserted successfully!")
