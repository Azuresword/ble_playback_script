import pandas as pd
import numpy as np

FILE_ORIG = 'WTB1_data/WTB1.csv'
FILE_CONV = 'converted_WTB1_format.csv'

def clean_and_get_stats(df, label):
    stats = {'Source': label}
    cols = ['AccX(g)', 'AccY(g)', 'AccZ(g)']
    
    for col in cols:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce')
            stats[f'{col} Mean'] = s.mean()
            stats[f'{col} Min'] = s.min()
            stats[f'{col} Max'] = s.max()
            stats[f'{col} Std'] = s.std()
        else:
            print(f"Warning: {col} not found in {label}")
            
    return stats

def main():
    # Read csv, all as string initially
    df_orig = pd.read_csv(FILE_ORIG, dtype=str)
    df_conv = pd.read_csv(FILE_CONV, dtype=str)
    
    stats_orig = clean_and_get_stats(df_orig, "WTB1.csv")
    stats_conv = clean_and_get_stats(df_conv, "App Data")
    
    # Create simple markdown table logic
    print("| Metric | WTB1.csv (原始) | App Data (新) | 差异倍数 (App/WTB1) |")
    print("| :--- | :--- | :--- | :--- |")
    
    metrics = ['Mean', 'Min', 'Max', 'Std']
    axes = ['AccX(g)', 'AccY(g)', 'AccZ(g)']
    
    for ax in axes:
        for m in metrics:
            key = f"{ax} {m}"
            val_o = stats_orig.get(key, 0)
            val_c = stats_conv.get(key, 0)
            
            # Formatting
            val_o_str = f"{val_o:.4f}"
            val_c_str = f"{val_c:.4f}"
            
            # Ratio
            ratio_str = "-"
            try:
                if abs(val_o) > 1e-4:
                    ratio = val_c / val_o
                    ratio_str = f"{ratio:.2f}x"
                elif abs(val_c) > 1e-4:
                     ratio_str = "Inf"
            except:
                pass
                
            print(f"| {key} | {val_o_str} | {val_c_str} | {ratio_str} |")

if __name__ == "__main__":
    main()
