# FDIC State Tables Scraper

This script automates the process of downloading FDIC state tables data for all 50 states from 2019 onwards.

## Prerequisites

- Python 3.7 or higher
- Firefox browser installed
- pip (Python package installer)

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
# On Linux/Mac:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

3. Install the required packages:
```bash
pip3 install -r requirements.txt
```

## Usage

1. Make sure your virtual environment is activated (you should see `(venv)` at the start of your command prompt)
2. Run the script:
```bash
python3 fdic_scraper.py
```

### Managing the Virtual Environment

To exit the virtual environment:
```bash
deactivate
```

To re-enter the virtual environment:
```bash
# On Linux/Mac:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

The script will:
1. Open a headless Firefox browser
2. Iterate through all 50 states
3. Download data for each state from 2019 onwards
4. Combine all data into a single CSV file named `fdic_all_states_data.csv`

## Notes

- The script includes a 1-second delay between states to be respectful to the server
- If the script encounters any errors with a particular state, it will log the error and continue with the next state
- The final CSV will include a 'State' column to identify the data source
- The script runs in headless mode (no visible browser window)
- You must activate the virtual environment each time you want to run the script in a new terminal session

## Troubleshooting

If you encounter any issues:
1. Make sure Firefox is installed and up to date
2. Check that you have a stable internet connection
3. Verify that your Downloads folder is accessible
4. If you get timeout errors, you may need to increase the wait times in the script
5. If you get "ModuleNotFoundError", make sure your virtual environment is activated 