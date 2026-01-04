import pandas as pd
import numpy as np

FILE_ORIG = 'WTB1_data/WTB1.csv'
FILE_CONV = 'converted_WTB1_format.csv'

def clean_numeric(df, col):
    """Convers 'null' strings to NaN and numericizes."""
    if col in df.columns:
        # Force coerce to numeric, 'null' becomes NaN
        return pd.to_numeric(df[col], errors='coerce')
    return pd.Series([np.nan] * len(df))

def get_stats(df, label):
    stats = {}
    stats['Source'] = label
    stats['Rows'] = len(df)
    
    # Time analysis
    if 'time' in df.columns:
        t = pd.to_numeric(df['time'], errors='coerce')
        t = t.dropna().sort_values()
        if len(t) > 1:
            duration_us = t.iloc[-1] - t.iloc[0]
            stats['Duration(s)'] = duration_us / 1_000_000.0
            
            # Estimate Hz
            # diffs = t.diff().dropna()
            # mean_diff_us = diffs.mean()
            # if mean_diff_us > 0:
            #    stats['Est. Freq(Hz)'] = 1_000_000.0 / mean_diff_us
            stats['Est. Freq(Hz)'] = len(t) / (duration_us / 1_000_000.0)
        else:
            stats['Duration(s)'] = 0
            stats['Est. Freq(Hz)'] = 0
            
    # Sensor Stats (Mean/Max/Min for AccX to see range)
    numeric_cols = ['AccX(g)', 'AsX(°/s)', 'HX(uT)', 'Temperature(°C)', 'pressure']
    
    for col in numeric_cols:
        series = clean_numeric(df, col)
        stats[f'{col}_Mean'] = series.mean()
        stats[f'{col}_Min'] = series.min()
        stats[f'{col}_Max'] = series.max()
        stats[f'{col}_Std'] = series.std()
        stats[f'{col}_NullCount'] = series.isna().sum()

    return stats

def main():
    print("Loading datasets...")
    # Read csv, all as string initially to handle 'null' literal
    df_orig = pd.read_csv(FILE_ORIG, dtype=str)
    df_conv = pd.read_csv(FILE_CONV, dtype=str)
    
    print("Calculating statistics...")
    stats_orig = get_stats(df_orig, "Original (WTB1.csv)")
    stats_conv = get_stats(df_conv, "Converted (App Data)")
    
    # Print comparison table
    df_res = pd.DataFrame([stats_orig, stats_conv])
    
    # Transpose for readability
    print("\n" + "="*60)
    print("COMPARISON REPORT")
    print("="*60)
    print(df_res.set_index('Source').T)
    print("="*60)

if __name__ == "__main__":
    main()
