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
    total_entries = 0
    skipped_entries = 0
    for pair in data['table_pairs']:
        service_auth = pair['service_authorization']
        table_data = pair['date_of_service_table']

        rows_to_insert = []
        duplicates = []

        for row in table_data:
            # Check if any required field is empty
            if not all([row.get('Date of Service'), row.get('Start Time'), row.get('End Time')]):
                skipped_entries += 1
                continue

            try:
                date = datetime.strptime(row['Date of Service'], '%m/%d/%Y').date()
                start_time = datetime.strptime(f"{row['Date of Service']} {row['Start Time']}", '%m/%d/%Y %I:%M %p')
                end_time = datetime.strptime(f"{row['Date of Service']} {row['End Time']}", '%m/%d/%Y %I:%M %p')
                rows_to_insert.append((service_auth, date, start_time, end_time))
                total_entries += 1
            except ValueError:
                # This will catch any datetime parsing errors due to invalid data
                skipped_entries += 1
                continue

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
    successful_entries = total_entries - len(duplicates)
    
    feedback = f"Import completed. {successful_entries} out of {total_entries} entries were successfully imported."
    if duplicates:
        feedback += f"\n{len(duplicates)} duplicate entries were skipped:"
        for dup in duplicates:
            feedback += f"\n - Service Auth: {dup[0]}, Date: {dup[1]}, Start: {dup[2]}, End: {dup[3]}"
    if skipped_entries:
        feedback += f"\n{skipped_entries} entries were skipped due to missing or invalid data."

    return feedback