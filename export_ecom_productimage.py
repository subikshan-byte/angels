import mysql.connector
import csv

# --- Database connection details ---
HOST = "742612"
USER = "root"
PASSWORD = "Subi14082006@"
DATABASE = "angles"
TABLE_NAME = "ecom_productimage"
CSV_FILE = "ecom_productimage.csv"

try:
    # Connect to MySQL database
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )

    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {TABLE_NAME}")

    # Fetch column names
    columns = [desc[0] for desc in cursor.description]
    
    # Fetch all rows
    rows = cursor.fetchall()

    # Write to CSV file
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(columns)  # write header
        writer.writerows(rows)    # write data

    print(f"✅ Data from table '{TABLE_NAME}' exported successfully to '{CSV_FILE}'")

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()

