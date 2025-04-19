SELECT 
    service_auth AS "Service Auth",
    to_char(date_of_service, 'MM/DD/YYYY')  AS "Date of Service",
    to_char(start_time, 'HH12:MI AM') AS "Start Time",
    to_char(end_time, 'HH12:MI AM')  AS "End Time",
    'F84.0-Autism' AS "Diagnosis Code 1",
    'H2019 - Therapeutic' AS "Service Line Proc Code",
    4 AS "Units"
FROM services WHERE date_of_service > '2025-02-01' ORDER BY date_of_service ASC, start_time;