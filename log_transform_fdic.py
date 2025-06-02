import pandas as pd
import numpy as np

def log_transform_fdic_data(input_file):
    """
    Transform FDIC data to log scale, handling special cases appropriately.
    Replaces original numeric columns with their log transforms.
    
    Args:
        input_file (str): Path to input CSV file
    """
    # Read the data
    df = pd.read_csv(input_file)
    
    # Identify columns to skip (non-numeric)
    skip_columns = ['Obs', 'State', 'Date']
    
    # Process each numeric column
    for column in df.columns:
        if column not in skip_columns:
            # Get the data
            data = df[column]
            
            # Handle special cases
            # 1. Replace 0 with a small number (1% of the smallest non-zero positive value)
            min_positive = data[data > 0].min()
            if not pd.isna(min_positive):
                small_number = min_positive * 0.01
                data = data.replace(0, small_number)
            
            # 2. For negative values, we'll use the sign-preserving log transform:
            # sign(x) * log(1 + |x|)
            signs = np.sign(data)
            logs = np.log1p(np.abs(data))
            df[column] = signs * logs
    
    # Generate output filename by inserting '_log' before the extension
    base, ext = input_file.rsplit('.', 1)
    output_file = f"{base}_log.{ext}"
    
    # Save transformed data
    df.to_csv(output_file, index=False)
    
    print(f"\nLog transformation complete. Output saved to {output_file}")
    print("\nColumns transformed:")
    transformed_cols = [col for col in df.columns if col not in skip_columns]
    for col in transformed_cols:
        print(f"- {col}")

if __name__ == "__main__":
    input_file = "combined_fdic_data.csv"
    log_transform_fdic_data(input_file) 