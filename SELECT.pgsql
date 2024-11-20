SELECT 
    service_auth AS "Service Auth",
    date_of_service AS "Date of Service",
    to_char(start_time, 'HH12:MI AM') AS "Start Time",
    to_char(end_time, 'HH12:MI AM')  AS "End Time",
    'F84.0-Autism' AS "Diagnosis Code 1",
    'H2027 - Psychoeducational' AS "Service Line Proc Code",
    4 AS "Units"
FROM services WHERE date_of_service > '2024-11-01' ORDER BY date_of_service ASC, start_time;