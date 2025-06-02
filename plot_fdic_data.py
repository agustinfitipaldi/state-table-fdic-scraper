import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def plot_time_series(csv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get the numeric columns (excluding Date and State)
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    
    # Set up the plotting style
    sns.set_style("whitegrid")
    sns.set_context("notebook", font_scale=1.2)
    
    # Create a figure for each numeric column
    for column in numeric_columns:
        plt.figure(figsize=(15, 8))
        
        # Plot each state as a line
        for state in df['State'].unique():
            state_data = df[df['State'] == state]
            plt.plot(state_data['Date'], state_data[column], label=state, alpha=0.7)
        
        # Customize the plot
        plt.title(f'{column} Over Time by State', fontsize=14, pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel(column, fontsize=12)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(f'{column.replace(" ", "_").lower()}_over_time.png', bbox_inches='tight', dpi=300)
        plt.close()

if __name__ == "__main__":
    plot_time_series('combined_fdic_data.csv') 