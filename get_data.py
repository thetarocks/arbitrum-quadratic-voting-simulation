import requests
import pandas as pd
import time

# The public gateway to Snapshot's database
URL = "https://hub.snapshot.org/graphql"

# The unique IDs of the two Arbitrum proposals we selected
proposals = {
    "aligned_proposal": "0xb380013efad355a9888561e1a108f0e6344f2e39c11087bb9043378d14ecec4d",
    "disaligned_proposal": "0x38663c36b26252acff6c6ca43663167858f51f960235dc0441bd2ad4a8f66fb1"
}

def fetch_all_votes(proposal_id):
    print(f"Starting download for proposal: {proposal_id[:10]}...")
    all_votes = []
    skip = 0
    
    # Snapshot's API limits us to 1000 rows per request, so we loop until we get everything
    while True:
        query = """
        query ($proposal: String!, $skip: Int!) {
          votes (
            first: 1000,
            skip: $skip,
            where: { proposal: $proposal },
            orderBy: "vp",
            orderDirection: desc
          ) {
            voter
            choice
            vp
          }
        }
        """
        
        response = requests.post(URL, json={'query': query, 'variables': {'proposal': proposal_id, 'skip': skip}})
        
        # Guard rail for empty or bad responses
        if response.status_code != 200 or 'data' not in response.json():
            print("Error connecting to Snapshot. Retrying...")
            break
            
        data = response.json()['data']['votes']
        
        if not data:
            break
            
        all_votes.extend(data)
        skip += 1000
        print(f"  Downloaded {len(all_votes)} votes so far...")
        time.sleep(0.2)  # Polite pause so Snapshot doesn't block us
        
    return pd.DataFrame(all_votes)

# 1. Download the data for the 'Aligned' case (Transaction Ordering)
df_aligned = fetch_all_votes(proposals["aligned_proposal"])
df_aligned.to_csv("aligned_data.csv", index=False)
print("✓ Saved aligned_data.csv\n")

# 2. Download the data for the 'Disaligned' case (Council Terms)
df_disaligned = fetch_all_votes(proposals["disaligned_proposal"])
df_disaligned.to_csv("disaligned_data.csv", index=False)
print("✓ Saved disaligned_data.csv\n")

print("All data successfully downloaded! Check your folder for the two new CSV files.")