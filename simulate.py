import pandas as pd
import numpy as np

def run_analysis(filename, label):
    # Load the CSV spreadsheet  downloaded
    df = pd.read_csv(filename)
    
    print(f"\n==========================================")
    print(f"📊 ANALYSIS FOR: {label.upper()}")
    print(f"==========================================")
    print(f"Total Unique Wallets Participated: {len(df)}")

    # 1. Calculate traditional results (1-Token-1-Vote)
    traditional_totals = df.groupby('choice')['vp'].sum()
    traditional_percentages = (traditional_totals / traditional_totals.sum()) * 100
    
    print("\n📜 TRADITIONAL RESULTS (1-Token-1-Vote):")
    for choice, tokens in traditional_totals.items():
        print(f"  Choice {choice}: {tokens:,.2f} tokens ({traditional_percentages[choice]:.2f}%)")
        
    # 2. Apply Quadratic Voting (Take the square root of each person's tokens)
    df['qv_power'] = np.sqrt(df['vp'])
    quadratic_totals = df.groupby('choice')['qv_power'].sum()
    quadratic_percentages = (quadratic_totals / quadratic_totals.sum()) * 100
    
    print("\n⚡ SIMULATED QUADRATIC RESULTS (Square Root):")
    for choice, qv_votes in quadratic_totals.items():
        print(f"  Choice {choice}: {qv_votes:,.2f} virtual votes ({quadratic_percentages[choice]:.2f}%)")

    # 3. Calculate Inequality (The Gini Coefficient)
    # 0 = perfect equality, 1 = total plutocracy (one whale rules all)
    vp_sorted = np.sort(df['vp'].values)
    n = len(vp_sorted)
    index = np.arange(1, n + 1)
    gini = (np.sum((2 * index - n - 1) * vp_sorted)) / (n * np.sum(vp_sorted))
    print(f"\n📉 Token Inequality (Gini Score): {gini:.4f}")
    
    # Quick insight text
    if gini > 0.85:
        print("💡 Insight: Extreme wealth concentration. A tiny minority of whales heavily dictated the raw numbers.")
    else:
        print("💡 Insight: Moderate wealth dispersion among voters.")

# Run the simulation on both files
run_analysis("aligned_data.csv", "Aligned Proposal (Transaction Policy)")
run_analysis("disaligned_data.csv", "Disaligned Proposal (Council Election Terms)")