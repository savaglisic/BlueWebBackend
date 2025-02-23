import pandas as pd

# Define the filename (assumes CSV is in the same directory)
file_path = "13-17-15_0.csv"

# Read the file and extract numeric data rows
with open(file_path, 'r') as file:
    content = file.readlines()

# Extract only the numerical data rows (ignoring metadata at the top)
data_lines = [line.strip().split(',') for line in content if line[0].isdigit()]

# Convert to DataFrame
df = pd.DataFrame(data_lines, columns=['BerryNumber', 'Diameter', 'Ignore', 'Firmness'])

# Convert relevant columns to numeric types
df = df.astype({'Diameter': float, 'Firmness': float})

# Compute statistics
avg_diameter = df['Diameter'].mean()
avg_firmness = df['Firmness'].mean()
std_diameter = df['Diameter'].std()
std_firmness = df['Firmness'].std()

# Print the results
print("\nBerry Lot Statistics:")
print(f"Average Diameter: {avg_diameter:.3f}")
print(f"Standard Deviation of Diameter: {std_diameter:.3f}")
print(f"Average Firmness: {avg_firmness:.3f}")
print(f"Standard Deviation of Firmness: {std_firmness:.3f}")


