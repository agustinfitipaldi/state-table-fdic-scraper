import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Read the CSV file
df = pd.read_csv('combined_fdic_data.csv')

# Convert date strings to datetime objects
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

# Set the style for better-looking plots
plt.style.use('seaborn')

# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot Total Assets
for state in df['State'].unique():
    state_data = df[df['State'] == state]
    ax1.plot(state_data['Date'], state_data['Total Assets - Assets Less Than $1 Billion'], 
             label=state, marker='o')

ax1.set_title('Total Assets Over Time by State')
ax1.set_xlabel('Date')
ax1.set_ylabel('Total Assets (in millions)')
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax1.grid(True)

# Plot Total Deposits
for state in df['State'].unique():
    state_data = df[df['State'] == state]
    ax2.plot(state_data['Date'], state_data['Total Deposits - Assets Less Than $1 Billion'], 
             label=state, marker='o')

ax2.set_title('Total Deposits Over Time by State')
ax2.set_xlabel('Date')
ax2.set_ylabel('Total Deposits (in millions)')
ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax2.grid(True)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the figure
plt.savefig('fdic_time_series.png', bbox_inches='tight', dpi=300)
plt.close() 