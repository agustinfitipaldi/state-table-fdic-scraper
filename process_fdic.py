import glob
import os
from datetime import datetime

def convert_date(date_str):
    # Convert "Month DD, YYYY" to "MM/DD/YYYY"
    try:
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%m/%d/%Y")
    except Exception as e:
        print(f"Error converting date {date_str}: {str(e)}")
        return date_str

def process_file(file_path):
    print(f"\nProcessing {os.path.basename(file_path)}")
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Debug print first 20 lines
        print("\nFirst 20 lines of file:")
        for i, line in enumerate(lines[:20]):
            print(f"Line {i}: {line.strip()}")
        
        # Get the date from line 4 (it's in the first state block)
        date_line = lines[4]
        date = date_line.split('",,,"')[0].split('\n')[-1].strip()
        date = convert_date(date)  # Convert to MM/DD/YYYY format
        print(f"Extracted date: {date}")
        
        # Get the state names from lines 3, 6, and 9
        states = []
        state_lines = [lines[3], lines[6], lines[9]]
        for state_line in state_lines:
            state = state_line.strip().strip('"')
            # Only include if it's not a date line and not "National"
            if state and "National" not in state and not any(month in state for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
                states.append(state)
                print(f"Found state: {state}")
        
        # Get the assets and deposits
        assets_line = lines[15]  # Line 16
        deposits_line = lines[19]  # Line 20
        
        print(f"\nAssets line: {assets_line}")
        print(f"Deposits line: {deposits_line}")
        
        # Split by quotes and get the values (skip the first value which is the label)
        assets = [float(x.replace(',', '')) for x in assets_line.split('"')[3::2] if x.strip()]
        deposits = [float(x.replace(',', '')) for x in deposits_line.split('"')[3::2] if x.strip()]
        
        print(f"\nFound assets: {assets}")
        print(f"Found deposits: {deposits}")
        
        # Take first, fourth, and seventh values (All Institutions for each state)
        state_assets = [assets[0], assets[3], assets[6]]
        state_deposits = [deposits[0], deposits[3], deposits[6]]
        
        # Combine the data
        results = []
        for i, state in enumerate(states):
            if i < len(state_assets) and i < len(state_deposits):
                results.append({
                    'State': state,
                    'Date': date,
                    'Total Deposits': state_deposits[i],
                    'Total Assets': state_assets[i]
                })
                print(f"Processed {state}: Deposits=${state_deposits[i]:,.0f}, Assets=${state_assets[i]:,.0f}")
        
        return results
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def main():
    # Get all FDIC files
    csv_dir = os.path.expanduser("~/Downloads/csvs")
    files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    if not files:
        print(f"No files found in {csv_dir}")
        return
    
    print(f"Found {len(files)} files to process")
    
    # Process each file
    all_data = []
    for file in files:
        results = process_file(file)
        if results:
            all_data.extend(results)
    
    # Save the results
    if all_data:
        output_file = os.path.join(csv_dir, 'combined_fdic_data.csv')
        with open(output_file, 'w') as f:
            # Write header
            f.write("Obs,State,Date,Total Deposits,Total Assets\n")
            
            # Write data
            for i, row in enumerate(sorted(all_data, key=lambda x: (x['State'], x['Date'])), 1):
                f.write(f"{i},{row['State']},{row['Date']},{row['Total Deposits']},{row['Total Assets']}\n")
        
        print(f"\nData successfully combined and saved to {output_file}")
        print(f"Total records processed: {len(all_data)}")
    else:
        print("No data was processed successfully")

if __name__ == "__main__":
    main() 