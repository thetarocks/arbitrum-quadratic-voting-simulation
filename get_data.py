import requests
import pandas as pd
import time
import json

URL = "https://hub.snapshot.org/graphql"
SPACE_ID = "arbitrumfoundation.eth"  # Core Arbitrum DAO Space

def fetch_top_proposals(limit=15):
    print(f"📡 Fetching top {limit} recent proposals from Arbitrum DAO...")
    query = """
    query ($space: String!, $limit: Int!) {
      proposals (
        first: $limit,
        where: { space: $space, state: "closed" },
        orderBy: "votes",
        orderDirection: desc
      ) {
        id
        title
        votes
        choices
      }
    }
    """
    response = requests.post(URL, json={'query': query, 'variables': {'space': SPACE_ID, 'limit': limit}})
    if response.status_code == 200 and 'data' in response.json():
        return response.json()['data']['proposals']
    else:
        raise Exception(f"Failed to fetch proposals: {response.text}")

def fetch_all_votes(proposal_id):
    all_votes = []
    skip = 0
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
        if response.status_code != 200 or 'data' not in response.json():
            break
        data = response.json()['data']['votes']
        if not data:
            break
        all_votes.extend(data)
        skip += 1000
        time.sleep(0.1)
    return all_votes

# 1. Gather Proposals
proposals = fetch_top_proposals(limit=15)

# Save proposal manifest metadata for the simulation script
with open("proposals_manifest.json", "w") as f:
    json.dump(proposals, f, indent=4)

# 2. Loop and Harvest Votes
all_compiled_data = []
for p in proposals:
    p_id = p['id']
    p_title = p['title'][:50] + "..."
    print(f"⬇️ Downloading votes for: {p_title} ({p['votes']} total votes cast)")
    
    votes_list = fetch_all_votes(p_id)
    df = pd.DataFrame(votes_list)
    df['proposal_id'] = p_id
    all_compiled_data.append(df)

# Combine everything into a single massive scalable database file
master_df = pd.concat(all_compiled_data, ignore_index=True)
master_df.to_csv("master_proposals_data.csv", index=False)
print("\n🏁 EXCELLENT TIER REACHED: master_proposals_data.csv saved successfully with batch data!")
