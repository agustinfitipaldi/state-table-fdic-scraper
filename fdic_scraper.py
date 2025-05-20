from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from webdriver_manager.firefox import GeckoDriverManager
import time
import os
import pandas as pd
import logging
from datetime import datetime
import glob
import re

class FDICScraper:
    def __init__(self):
        self.url = "https://state-tables.fdic.gov/"
        self.setup_driver()
        self.setup_logging()
        self.download_dir = os.path.expanduser('~/Downloads/csvs')
        os.makedirs(self.download_dir, exist_ok=True)
        
    def generate_filename(self, states, date):
        """Generate a filename based on states and date"""
        states_str = ''.join(states)
        return f"{states_str}{date}.csv"
        
    def get_existing_files(self):
        """Get a set of existing state-date combinations"""
        existing_files = set()
        pattern = re.compile(r'([A-Z]{2,6})(\d{6})\.csv')
        
        for file in glob.glob(os.path.join(self.download_dir, '*.csv')):
            match = pattern.match(os.path.basename(file))
            if match:
                states = match.group(1)
                date = match.group(2)
                # Split states into pairs of two characters
                state_list = [states[i:i+2] for i in range(0, len(states), 2)]
                existing_files.add((tuple(state_list), date))
        
        return existing_files

    def rename_latest_csv(self, states, date):
        """Rename the most recently downloaded CSV file"""
        latest_file = self.get_latest_csv()
        if latest_file:
            new_filename = self.generate_filename(states, date)
            new_path = os.path.join(self.download_dir, new_filename)
            
            # If file already exists, add a timestamp to avoid conflicts
            if os.path.exists(new_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{new_filename[:-4]}_{timestamp}.csv"
                new_path = os.path.join(self.download_dir, new_filename)
            
            try:
                os.rename(latest_file, new_path)
                self.logger.info(f"Renamed file to {new_filename}")
                return new_path
            except Exception as e:
                self.logger.error(f"Error renaming file: {str(e)}")
                return latest_file
        return None

    def setup_logging(self):
        """Set up logging configuration"""
        log_dir = os.path.expanduser('~/Downloads/csvs/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'fdic_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def validate_csv(self, file_path, states, date):
        """
        Validate the downloaded CSV file for data quality.
        
        Args:
            file_path (str): Path to the CSV file
            states (list): List of states that should be in the file
            date (str): Date of the data
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            df = pd.read_csv(file_path)
            
            # Log basic file info
            self.logger.info(f"Validating {os.path.basename(file_path)}")
            self.logger.info(f"File size: {os.path.getsize(file_path) / 1024:.2f} KB")
            self.logger.info(f"Number of rows: {len(df)}")
            self.logger.info(f"Number of columns: {len(df.columns)}")
            
            # Check for missing values
            missing_values = df.isnull().sum()
            if missing_values.any():
                self.logger.warning("Missing values found:")
                for col, count in missing_values[missing_values > 0].items():
                    self.logger.warning(f"  {col}: {count} missing values")
            
            # Check for duplicate rows
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                self.logger.warning(f"Found {duplicates} duplicate rows")
            
            # Validate numeric columns
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            for col in numeric_cols:
                # Skip columns that might legitimately have large values
                if 'total' in col.lower() or 'amount' in col.lower():
                    continue
                    
                # Check for unreasonable values
                if df[col].max() > 1e9:  # Values over 1 billion
                    self.logger.warning(f"Column {col} has unusually large values: max={df[col].max()}")
                if df[col].min() < -1e9:  # Values under -1 billion
                    self.logger.warning(f"Column {col} has unusually small values: min={df[col].min()}")
            
            # Check if all expected states are present
            if 'STNAME' in df.columns:
                missing_states = set(states) - set(df['STNAME'].unique())
                if missing_states:
                    self.logger.warning(f"Missing states in data: {missing_states}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating CSV: {str(e)}")
            return False

    def get_latest_csv(self):
        """Get the path of the most recently downloaded CSV file"""
        download_dir = os.path.expanduser('~/Downloads/csvs')
        list_of_files = glob.glob(os.path.join(download_dir, '*.csv'))
        if not list_of_files:
            return None
        return max(list_of_files, key=os.path.getctime)

    def setup_driver(self):
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--window-size=1920,1080")
        
        # Set up Firefox options for automatic CSV download
        download_dir = os.path.expanduser('~/Downloads/csvs')
        os.makedirs(download_dir, exist_ok=True)
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.dir", download_dir)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/csv,application/vnd.ms-excel")
        firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference("pdfjs.disabled", True)
        firefox_options.set_preference("browser.download.panel.shown", False)
        firefox_options.set_preference("browser.download.useDownloadDir", True)
        firefox_options.set_preference("browser.helperApps.alwaysAsk.force", False)
        
        service = Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=firefox_options)
        self.driver.implicitly_wait(10)
    
    def download_state_data(self, states, date="201903"):
        # Check if this combination already exists
        existing_files = self.get_existing_files()
        if (tuple(states), date) in existing_files:
            self.logger.info(f"File for states {states} and date {date} already exists, skipping...")
            return
            
        print(f"Downloading data for {', '.join(states)} for date {date}...")
        self.logger.info(f"Starting download for states {states} and date {date}")
        
        # Load the page
        self.driver.get(self.url)
        
        # Wait for page to be fully loaded
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        
        try:
            # Wait for Angular to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.custom_download_buttons"))
            )
            
            # First set up all states
            for i, state in enumerate(states):
                print(f"Setting up state {state}...", end="\r")
                
                # Find the dropdowns for this column
                institution_select = self.driver.find_element(By.CSS_SELECTOR, f"app-institution-type-list[column='{i}'] select")
                area_select = self.driver.find_element(By.CSS_SELECTOR, f"app-geographical-area-list[column='{i}'] select")
                date_select = self.driver.find_element(By.CSS_SELECTOR, f"app-report-date-list[column='{i}'] select")
                
                # Select values
                Select(institution_select).select_by_value("9")
                Select(area_select).select_by_value(state)
                Select(date_select).select_by_value(date)
            
            # After all states are set up, click any CSV button
            print("All states set up, downloading CSV...")
            # Wait for the CSV button to be clickable (instead of sleep)
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.custom_download_link[aria-label='Download\u00a0CSV']"))
            )
            csv_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.custom_download_link[aria-label='Download\u00a0CSV']")
            if not csv_buttons:
                # Try finding by text content as a fallback
                csv_buttons = self.driver.find_elements(By.XPATH, "//a[text()='CSV']")
            
            if csv_buttons:
                print("Found CSV button, clicking...")
                csv_buttons[0].click()
                
                # Wait for download to complete and validate
                time.sleep(2)  # Give time for download to start
                csv_path = self.rename_latest_csv(states, date)
                if csv_path:
                    if self.validate_csv(csv_path, states, date):
                        self.logger.info("CSV validation passed")
                        print("✓ Validation passed")
                    else:
                        self.logger.error("CSV validation failed")
                        print("✗ Validation failed")
                else:
                    self.logger.error("No CSV file found after download")
                    print("✗ No file found")
            else:
                print("Debug: Available buttons:")
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.custom_download_link")
                for button in all_buttons:
                    print(f"Button text: {button.text}, aria-label: {button.get_attribute('aria-label')}")
                raise Exception("No CSV download button found")
            
        except Exception as e:
            self.logger.error(f"Error during download: {str(e)}")
            print(f"Error: {str(e)}")
            print("\nCurrent URL:", self.driver.current_url)
            print("\nPage title:", self.driver.title)
            raise
    
    def scrape_all_states(self):
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        
        # Generate all quarters from 2019 to present
        quarters = []
        for year in range(2019, 2025):  # Adjust end year as needed
            for quarter in ["03", "06", "09", "12"]:
                quarters.append(f"{year}{quarter}")
        
        # Get existing files to avoid re-downloading
        existing_files = self.get_existing_files()
        self.logger.info(f"Found {len(existing_files)} existing files")
        
        # Calculate total combinations
        total_combinations = (len(states) // 3 + (1 if len(states) % 3 else 0)) * len(quarters)
        remaining_combinations = total_combinations - len(existing_files)
        
        print(f"\nStarting scrape with {remaining_combinations} files remaining out of {total_combinations} total")
        print("=" * 50)
        
        # Process states in groups of three
        current_file = 0
        for i in range(0, len(states), 3):
            state_group = states[i:i+3]
            for quarter in quarters:
                current_file += 1
                if (tuple(state_group), quarter) not in existing_files:
                    print(f"\nProcessing file {current_file}/{total_combinations}")
                    print(f"States: {', '.join(state_group)}")
                    print(f"Date: {quarter}")
                    print("-" * 30)
                    try:
                        self.download_state_data(state_group, quarter)
                    except Exception as e:
                        self.logger.error(f"Error processing {state_group} for quarter {quarter}: {str(e)}")
                        continue
                else:
                    self.logger.info(f"Skipping existing file for {state_group} {quarter}")
                    print(f"\rSkipping {current_file}/{total_combinations}: {', '.join(state_group)} {quarter}", end="")

    def close(self):
        self.driver.quit()

    def debug_scrape(self, date, states):
        """
        Debug method to scrape specific states for a specific date.
        
        Args:
            date (str): Date in format YYYYMM (e.g., "201903")
            states (list): List of up to 3 state codes (e.g., ["CA", "NY", "TX"])
        """
        if len(states) > 3:
            print("Error: Maximum of 3 states allowed")
            return
        
        try:
            self.download_state_data(states, date)
            print(f"\nSuccessfully downloaded data for {', '.join(states)} for date {date}")
        except Exception as e:
            print(f"Error during debug scrape: {str(e)}")

    def scrape_date_range(self, start_date, end_date, states=None):
        """
        Scrape data for states within a date range.
        
        Args:
            start_date (str): Start date in format YYYYMM (e.g., "202003")
            end_date (str): End date in format YYYYMM (e.g., "202212")
            states (list): Optional list of states to scrape. If None, all states will be scraped.
        """
        # Validate date format
        if not (len(start_date) == 6 and len(end_date) == 6 and 
                start_date.isdigit() and end_date.isdigit()):
            print("Invalid date format. Please use YYYYMM format.")
            return
            
        # Validate month part is valid quarter
        for date in [start_date, end_date]:
            month = date[4:6]
            if month not in ["03", "06", "09", "12"]:
                print(f"Invalid month in date {date}. Must be 03, 06, 09, or 12.")
                return
        
        # Generate quarters between start and end
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        quarters = []
        
        for year in range(start_year, end_year + 1):
            for quarter in ["03", "06", "09", "12"]:
                current_date = f"{year}{quarter}"
                if start_date <= current_date <= end_date:
                    quarters.append(current_date)
        
        if not quarters:
            print("No valid quarters found in the specified range.")
            return
            
        print(f"\nScraping data for {len(quarters)} quarters from {start_date} to {end_date}")
        
        # If no states provided, use all states
        if states is None:
            states = [
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
            ]
        
        total_combinations = (len(states) // 3 + (1 if len(states) % 3 else 0)) * len(quarters)
        current_file = 0
        
        for i in range(0, len(states), 3):
            state_group = states[i:i+3]
            for quarter in quarters:
                current_file += 1
                print(f"\nProcessing file {current_file}/{total_combinations}")
                print(f"States: {', '.join(state_group)}")
                print(f"Date: {quarter}")
                print("-" * 30)
                try:
                    self.download_state_data(state_group, quarter)
                except Exception as e:
                    self.logger.error(f"Error processing {state_group} for quarter {quarter}: {str(e)}")
                    continue

def convert_date(date_str):
    # Convert "Month DD, YYYY" to "MM/DD/YYYY"
    try:
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%m/%d/%Y")
    except Exception as e:
        print(f"Error converting date {date_str}: {str(e)}")
        return date_str

def get_available_variables():
    """Extract all available variables from a sample CSV file"""
    csv_dir = os.path.expanduser("~/Downloads/csvs")
    files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    if not files:
        return []
    
    try:
        with open(files[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        variables = []
        start_collecting = False
        
        for line in lines:
            # Start collecting after "AGGREGATE CONDITION..."
            if "AGGREGATE CONDITION" in line:
                start_collecting = True
                continue
            
            # Stop collecting at all-caps sections
            if start_collecting and line.strip().isupper():
                break
                
            # Skip empty lines and section headers
            if start_collecting and line.strip() and not line.strip().isupper():
                # Extract the variable name (first part before the first comma)
                var = line.split('"')[1].strip()
                if var and var not in variables:
                    variables.append(var)
        
        return variables
    except Exception as e:
        print(f"Error reading variables: {str(e)}")
        return []

def process_file(file_path, selected_variables=None, institution_categories=None):
    print(f"Processing {os.path.basename(file_path)}")
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get the date from line 4
        date_line = lines[4]
        date = date_line.split('",,,"')[0].split('\n')[-1].strip()
        date = convert_date(date)  # Convert to MM/DD/YYYY format
        
        # Get the state names from lines 3, 6, and 9
        states = []
        state_lines = [lines[3], lines[6], lines[9]]
        for state_line in state_lines:
            state = state_line.strip().strip('"')
            if state and "National" not in state and not any(month in state for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
                states.append(state)
        
        # If no variables are selected, use default ones
        if selected_variables is None:
            selected_variables = ['Total Deposits', 'Total Assets']
            
        # If no institution categories are selected, use default (All Institutions)
        if institution_categories is None:
            institution_categories = ['All Institutions']
            
        # Map institution categories to their indices
        category_indices = {
            'All Institutions': [0, 3, 6],
            'Assets Less Than $1 Billion': [1, 4, 7],
            'Assets Greater Than $1 Billion': [2, 5, 8]
        }
        
        # Initialize results list
        results = []
        
        # Process each state
        for i, state in enumerate(states):
            state_data = {'State': state, 'Date': date}
            
            # Process each selected variable
            for var in selected_variables:
                # Find the line containing the variable
                var_line = None
                for line in lines:
                    if var in line:
                        var_line = line
                        break
                
                if var_line:
                    # Split by quotes and get the values, handling "0*" case
                    values = []
                    for x in var_line.split('"')[3::2]:
                        if x.strip():
                            # Handle "0*" case by treating it as 0
                            if x.strip() == "0*":
                                values.append(0.0)
                            else:
                                values.append(float(x.replace(',', '')))
                    
                    # Add values for each selected institution category
                    for category in institution_categories:
                        if category in category_indices:
                            idx = category_indices[category][i]
                            if idx < len(values):
                                state_data[f"{var} - {category}"] = values[idx]
                            else:
                                state_data[f"{var} - {category}"] = None
                else:
                    # If variable not found, set all categories to None
                    for category in institution_categories:
                        state_data[f"{var} - {category}"] = None
            
            results.append(state_data)
        
        return results
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def combine_data(selected_variables=None, institution_categories=None):
    # Get all FDIC files
    csv_dir = os.path.expanduser("~/Downloads/csvs")
    files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    # Filter files to only include those matching the state-date pattern
    state_date_pattern = re.compile(r'^[A-Z]{2,6}\d{6}\.csv$')
    files = [f for f in files if state_date_pattern.match(os.path.basename(f))]
    
    if not files:
        print(f"No matching files found in {csv_dir}")
        return
    
    print(f"Processing {len(files)} files...")
    
    # If no variables are selected, use default ones
    if selected_variables is None:
        selected_variables = ['Total Deposits', 'Total Assets']
        
    # If no institution categories are selected, use default
    if institution_categories is None:
        institution_categories = ['All Institutions']
    
    # Process each file
    all_data = []
    for file in files:
        results = process_file(file, selected_variables, institution_categories)
        if results:
            all_data.extend(results)
    
    # Save the results
    if all_data:
        output_file = os.path.join(csv_dir, 'combined_fdic_data.csv')
        with open(output_file, 'w') as f:
            # Create header with all variable-category combinations
            header_parts = ['Obs', 'State', 'Date']
            for var in selected_variables:
                for category in institution_categories:
                    header_parts.append(f"{var} - {category}")
            
            f.write(",".join(header_parts) + "\n")
            
            # Sort data by state and properly parsed date
            def sort_key(row):
                state = row['State']
                # Parse date from MM/DD/YYYY format
                date_parts = row['Date'].split('/')
                if len(date_parts) == 3:
                    month, day, year = map(int, date_parts)
                    # Create a tuple for sorting (state, year, month, day)
                    return (state, year, month, day)
                return (state, row['Date'])  # Fallback if date parsing fails
            
            # Write data with proper sorting
            for i, row in enumerate(sorted(all_data, key=sort_key), 1):
                values = [str(i), row['State'], row['Date']]
                for var in selected_variables:
                    for category in institution_categories:
                        values.append(str(row.get(f"{var} - {category}", '')))
                f.write(",".join(values) + "\n")
        
        print(f"Successfully combined {len(all_data)} records into {output_file}")
    else:
        print("No data was processed successfully")

def main():
    scraper = FDICScraper()
    try:
        while True:
            print("\nFDIC Scraper Menu:")
            print("1. Run full scrape (all states, all quarters)")
            print("2. Debug mode (specific states and date)")
            print("3. Scrape date range")
            print("4. Combine existing CSV files")
            print("5. Full scrape and combine")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                print("\nStarting full scrape...")
                scraper.scrape_all_states()
            elif choice == "2":
                date = input("\nEnter date (YYYYMM format, e.g., 201903): ").strip()
                if not date.isdigit() or len(date) != 6:
                    print("Invalid date format. Please use YYYYMM format.")
                    continue
                
                states_input = input("Enter up to 3 state codes separated by spaces (e.g., CA NY TX): ").strip().upper()
                states = states_input.split()
                
                if not states:
                    print("No states provided.")
                    continue
                
                scraper.debug_scrape(date, states)
            elif choice == "3":
                date_range = input("\nEnter date range (YYYYMM-YYYYMM format, e.g., 202003-202212): ").strip()
                try:
                    start_date, end_date = date_range.split('-')
                    
                    print("\nDate Range Options:")
                    print("1. All states")
                    print("2. Specific states")
                    range_choice = input("\nEnter your choice (1-2): ").strip()
                    
                    if range_choice == "1":
                        scraper.scrape_date_range(start_date, end_date)
                    elif range_choice == "2":
                        states_input = input("Enter up to 3 state codes separated by spaces (e.g., CA NY TX): ").strip().upper()
                        states = states_input.split()
                        if not states:
                            print("No states provided.")
                            continue
                        scraper.scrape_date_range(start_date, end_date, states)
                    else:
                        print("Invalid choice. Please enter 1 or 2.")
                except ValueError:
                    print("Invalid date range format. Please use YYYYMM-YYYYMM format.")
            elif choice == "4":
                print("\nCombining existing CSV files...")
                
                # Get available variables
                variables = get_available_variables()
                if not variables:
                    print("No variables found in CSV files.")
                    continue
                
                # Display variables with numbers
                print("\nAvailable variables:")
                for i, var in enumerate(variables, 1):
                    print(f"{i}. {var}")
                
                # Get variable selections
                print("\nEnter the numbers of the variables you want (space-separated, e.g., '1 3 5'):")
                var_nums = input().strip().split()
                try:
                    selected_vars = [variables[int(num)-1] for num in var_nums]
                except (ValueError, IndexError):
                    print("Invalid selection. Using default variables.")
                    selected_vars = ['Total Deposits', 'Total Assets']
                
                print("\nSelect institution categories:")
                print("1. All Institutions")
                print("2. Assets Less Than $1 Billion")
                print("3. Assets Greater Than $1 Billion")
                print("4. All Categories")
                
                cat_choice = input("\nEnter your choice (1-4): ").strip()
                
                if cat_choice == "1":
                    selected_cats = ['All Institutions']
                elif cat_choice == "2":
                    selected_cats = ['Assets Less Than $1 Billion']
                elif cat_choice == "3":
                    selected_cats = ['Assets Greater Than $1 Billion']
                elif cat_choice == "4":
                    selected_cats = ['All Institutions', 'Assets Less Than $1 Billion', 'Assets Greater Than $1 Billion']
                else:
                    print("Invalid choice. Using default category.")
                    selected_cats = ['All Institutions']
                
                combine_data(selected_vars, selected_cats)
            elif choice == "5":
                print("\nStarting full scrape and combine...")
                scraper.scrape_all_states()
                print("\nCombining downloaded files...")
                combine_data()
            elif choice == "6":
                print("\nExiting...")
                break
            else:
                print("Invalid choice. Please enter 1-6.")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 