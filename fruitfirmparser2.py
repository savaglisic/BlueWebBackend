import os
import time
import sqlite3
import pandas as pd
import requests

# Constants
RUNDATA_DIR = "/Users/savaglisic/Desktop/Code/BlueBackend/rundata"
DB_FILE = "processed_files.db"
API_ENDPOINT = "http://localhost:5001/fruit_firm"
API_KEY = "24742405-8397-11ef-9f80-12a7bbaed785"
MODIFICATION_THRESHOLD = 120  # 2 minutes in seconds

# Ensure the database exists and create tracking table
def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            file_path TEXT PRIMARY KEY,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Fetch all processed files in one query to avoid multiple DB calls
def get_processed_files():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM processed_files")
    processed_files = set(row[0] for row in cursor.fetchall())  # Store as set for O(1) lookups
    conn.close()
    return processed_files

# Mark multiple files as processed in a single batch
def mark_files_as_processed(files):
    if not files:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO processed_files (file_path) VALUES (?)", [(f,) for f in files])
    conn.commit()
    conn.close()

# Find all CSV files in rundata directory (excluding "old" directories)
def find_csv_files():
    csv_files = []
    for root, dirs, files in os.walk(RUNDATA_DIR):
        # Modify dirs in-place to avoid traversing "old"
        dirs[:] = [d for d in dirs if d.lower() != "old"]

        for file in files:
            if file.endswith(".csv"):
                full_path = os.path.join(root, file)
                csv_files.append(full_path)

    print(f"Found {len(csv_files)} CSV files.")
    return csv_files

# Filter out files modified in the last 2 minutes
def filter_recent_files(files):
    current_time = time.time()
    return [file for file in files if (current_time - os.path.getmtime(file)) > MODIFICATION_THRESHOLD]

# Extract data from a CSV file
def parse_csv(file_path):
    print(f"\nProcessing file: {file_path}")
    
    with open(file_path, 'r') as file:
        content = file.readlines()

    # Extract the ticket number (Barcode)
    ticket_number = next((line.split(",")[1] for line in content if line.startswith("Ticket #")), None)
    if not ticket_number:
        print("Error: No ticket number (barcode) found in the file!")
        return None

    # Extract only the numerical data rows (ignoring metadata)
    data_lines = [line.strip().split(',') for line in content if line[0].isdigit()]
    if not data_lines:
        print("Error: No valid berry data found in the file!")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(data_lines, columns=['BerryNumber', 'Diameter', 'Ignore', 'Firmness'])
    df = df.astype({'Diameter': float, 'Firmness': float})

    # Compute statistics
    avg_diameter = df['Diameter'].mean()
    avg_firmness = df['Firmness'].mean()
    std_diameter = df['Diameter'].std()
    std_firmness = df['Firmness'].std()

    print(f"  -> Average Diameter: {avg_diameter:.3f}")
    print(f"  -> Standard Deviation of Diameter: {std_diameter:.3f}")
    print(f"  -> Average Firmness: {avg_firmness:.3f}")
    print(f"  -> Standard Deviation of Firmness: {std_firmness:.3f}")

    return {
        "barcode": ticket_number,
        "avg_firmness": avg_firmness,
        "avg_diameter": avg_diameter,
        "sd_firmness": std_firmness,
        "sd_diameter": std_diameter
    }

# Send data to remote API
def send_to_api(data):
    print(f"Sending data to API for barcode {data['barcode']}...")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        print("  -> API Response: Success")
    else:
        print(f"  -> API Error: {response.status_code} - {response.text}")

# Main function
def main():
    print("\n--- Starting Rundata Processing ---")

    initialize_database()

    # Step 1: Find all CSV files
    all_csv_files = find_csv_files()

    # Step 2: Filter out recently modified files
    eligible_files = filter_recent_files(all_csv_files)
    print(f"{len(eligible_files)} files are eligible for processing.")

    # Step 3: Get already processed files in one DB query
    processed_files = get_processed_files()
    
    files_to_process = [file for file in eligible_files if file not in processed_files]

    print(f"{len(files_to_process)} files to be processed.")

    processed_list = []
    for file in files_to_process:
        # Step 4: Parse the CSV and extract data
        data = parse_csv(file)
        if data:
            # Step 5: Send data to API
            send_to_api(data)
            processed_list.append(file)

    # Step 6: Mark processed files in batch
    mark_files_as_processed(processed_list)

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    main()

