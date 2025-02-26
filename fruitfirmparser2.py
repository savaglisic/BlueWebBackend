import os
import time
import sqlite3
import pandas as pd
import requests
import traceback

# Constants
RUNDATA_DIR = "/Users/savaglisic/Desktop/Code/BlueBackend/rundata"
DB_FILE = "processed_files.db"
LOG_FILE = "error.log"
API_ENDPOINT = "http://localhost:5001/fruit_firm"
API_KEY = "24742405-8397-11ef-9f80-12a7bbaed785"
MODIFICATION_THRESHOLD = 120  # 2 minutes

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

# Log errors safely
def log_error(file_path, error_message):
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"ERROR in file {file_path}:\n{error_message}\n\n")
    print(f"  -> Error processing {file_path}. Logged in {LOG_FILE}")

# Extract data from a CSV file safely
def parse_csv(file_path):
    print(f"\nProcessing file: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            content = file.readlines()

        # Extract the ticket number (Barcode)
        ticket_number = next((line.split(",")[1] for line in content if line.startswith("Ticket #")), None)
        if not ticket_number:
            raise ValueError("No ticket number (barcode) found in the file!")

        # Extract only the numerical data rows (ignoring metadata)
        data_lines = [line.strip().split(',') for line in content if line[0].isdigit()]
        if not data_lines:
            raise ValueError("No valid berry data found in the file!")

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

    except Exception as e:
        log_error(file_path, traceback.format_exc())
        return None  # Continue with the next file

# Send data to remote API safely
def send_to_api(data, file_path):
    try:
        print(f"Sending data to API for barcode {data['barcode']}...")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": API_KEY
        }

        response = requests.post(API_ENDPOINT, json=data, headers=headers)
        
        if response.status_code in [200, 201]:  # Handle success responses correctly
            print(f"  -> API Response: Success ({response.status_code}) - {response.json()['message']}")
        else:
            print(f"  -> API Error: {response.status_code}")
            print(f"  -> Response Body: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")

    except Exception as e:
        log_error(file_path, traceback.format_exc())

# Main function with full error handling
def main():
    print("\n--- Starting Rundata Processing ---")

    initialize_database()

    # Step 1: Find all CSV files
    all_csv_files = find_csv_files()

    # Step 2: Filter out recently modified files
    eligible_files = filter_recent_files(all_csv_files)
    print(f"{len(eligible_files)} files are old enough for processing.")

    # Step 3: Get already processed files in one DB query
    processed_files = get_processed_files()
    
    files_to_process = [file for file in eligible_files if file not in processed_files]

    print(f"{len(files_to_process)} files to be processed.")

    processed_list = []
    for file in files_to_process:
        try:
            # Step 4: Parse the CSV and extract data
            data = parse_csv(file)
            if data:
                # Step 5: Send data to API
                send_to_api(data, file)
                processed_list.append(file)  # Only mark successful files
        except Exception as e:
            log_error(file, traceback.format_exc())

    # Step 6: Mark processed files in batch
    mark_files_as_processed(processed_list)

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    main()
