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

# Check if a file has already been processed
def is_file_processed(file_path):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM processed_files WHERE file_path = ?", (file_path,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Mark a file as processed
def mark_file_as_processed(file_path):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO processed_files (file_path) VALUES (?)", (file_path,))
    conn.commit()
    conn.close()

# Find all CSV files in rundata directory (excluding "old" directories)
def find_csv_files():
    csv_files = []
    for root, dirs, files in os.walk(RUNDATA_DIR):
        # Ignore "old" directories
        if "old" in root.split(os.sep):
            continue

        for file in files:
            if file.endswith(".csv"):
                full_path = os.path.join(root, file)
                csv_files.append(full_path)

    print("Detected CSV files:", csv_files)  # Debugging output
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
    ticket_number = None
    for line in content:
        if line.startswith("Ticket #"):
            ticket_number = line.strip().split(",")[1]
            break

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

    # Convert relevant columns to numeric types
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
    print(f"Found {len(all_csv_files)} CSV files.")

    # Step 2: Filter out recently modified files
    eligible_files = filter_recent_files(all_csv_files)
    print(f"{len(eligible_files)} files are eligible for processing.")

    for file in eligible_files:
        if is_file_processed(file):
            print(f"Skipping already processed file: {file}")
            continue

        # Step 3: Parse the CSV and extract data
        data = parse_csv(file)

        if data:
            # Step 4: Send data to API
            send_to_api(data)

            # Step 5: Mark file as processed
            mark_file_as_processed(file)

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    main()


