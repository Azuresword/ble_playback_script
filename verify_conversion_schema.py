import pandas as pd
import sys

ORIGINAL_FILE = 'WTB1_data/WTB1.csv'
CONVERTED_FILE = 'converted_WTB1_format.csv'

def main():
    print(f"Verifying {CONVERTED_FILE} against {ORIGINAL_FILE}...")
    
    # Check headers directly (as pandas might mangle duplicate names)
    with open(ORIGINAL_FILE, 'r') as f:
        header_orig = f.readline().strip().split(',')
        
    with open(CONVERTED_FILE, 'r') as f:
        header_conv = f.readline().strip().split(',')
        
    print(f"Original Header Count: {len(header_orig)}")
    print(f"Converted Header Count: {len(header_conv)}")
    
    if header_orig != header_conv:
        print("❌ Header Verification Failed!")
        print("Diff:")
        for i, (col_o, col_c) in enumerate(zip(header_orig, header_conv)):
            if col_o != col_c:
                print(f"  Col {i}: Expected '{col_o}', Got '{col_c}'")
        sys.exit(1)
    else:
        print("✅ Header Verify Passed! Exact match (including duplicate SpeedY).")

    # Check content loadability
    try:
        # Just check we can load it. No header check here as pd mangles dups
        df = pd.read_csv(CONVERTED_FILE)
        print(f"✅ Pandas load check passed. Rows: {len(df)}")
    except Exception as e:
        print(f"❌ Pandas load failed: {e}")
        sys.exit(1)
        
    print("Verification Complete.")

if __name__ == "__main__":
    main()
