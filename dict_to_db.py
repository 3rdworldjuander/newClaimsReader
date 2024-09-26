from db import get_db_connection
from datetime import datetime
import psycopg2

def import_service_data(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id SERIAL PRIMARY KEY,
        service_auth TEXT,
        date_of_service DATE,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        UNIQUE(service_auth, date_of_service, start_time, end_time)
    )
    ''')

    # Prepare data for insertion
    service_auth = data['Service Auth']
    rows_to_insert = []
    duplicates = []

    for i in range(len(data['Date of Service'])):
        date = datetime.strptime(data['Date of Service'][i], '%m/%d/%Y').date()
        start_time = datetime.strptime(f"{data['Date of Service'][i]} {data['Start Time'][i]}", '%m/%d/%Y %I:%M %p')
        end_time = datetime.strptime(f"{data['Date of Service'][i]} {data['End Time'][i]}", '%m/%d/%Y %I:%M %p')
        
        rows_to_insert.append((service_auth, date, start_time, end_time))

    # Insert data and track duplicates
    for row in rows_to_insert:
        try:
            cursor.execute('''
            INSERT INTO services (service_auth, date_of_service, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            ''', row)
        except psycopg2.IntegrityError:
            duplicates.append(row)
            conn.rollback()  # Roll back the failed transaction
        else:
            conn.commit()  # Commit each successful insertion

    # Close connection
    cursor.close()
    conn.close()

    # Prepare feedback
    total_entries = len(rows_to_insert)
    successful_entries = total_entries - len(duplicates)
    
    feedback = f"Import completed. {successful_entries} out of {total_entries} entries were successfully imported."
    if duplicates:
        feedback += f"\n{len(duplicates)} duplicate entries were skipped:"
        for dup in duplicates:
            feedback += f"\n - Service Auth: {dup[0]}, Date: {dup[1]}, Start: {dup[2]}, End: {dup[3]}"

    return feedback

# Example usage:
# result = import_service_data(data)
# print(result)