import os
import json
import time
from typing import Any, Dict

import requests
import pandas as pd
import numpy as np
from requests.exceptions import RequestException


# ============================================================
# CONFIG
# ============================================================
URL = "https://hub.snapshot.org/graphql"
SPACE_ID = "arbitrumfoundation.eth"

TARGET_PROPOSALS = 15
FETCH_POOL = 200
PAGE_SIZE = 1000             

VALID_PROPOSAL_TYPES = {"single-choice", "basic"}

RAW_DIR = "raw_votes"
os.makedirs(RAW_DIR, exist_ok=True)


# ============================================================
# API HELPERS
# ============================================================

def run_query(query: str, variables: Dict[str, Any], retries: int = 10) -> Dict[str, Any]:
    last_error = None

    for attempt in range(retries):
        try:
            response = requests.post(
                URL,
                json={"query": query, "variables": variables},
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()

                if "errors" in data:
                    raise Exception(f"GraphQL errors: {data['errors']}")

                return data

            last_error = f"HTTP {response.status_code}: {response.text[:300]}"

        except RequestException as e:
            last_error = e

        wait = min(90, 2 ** attempt)
        print(f"Network/query failed. Retry {attempt + 1}/{retries} in {wait}s...")
        print(f"Reason: {last_error}")
        time.sleep(wait)

    raise Exception(f"Failed after {retries} retries. Last error: {last_error}")


# ============================================================
# METRIC HELPERS
# ============================================================

def calculate_gini(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]

    if len(arr) == 0 or arr.sum() == 0:
        return 0.0

    sorted_arr = np.sort(arr)
    n = len(sorted_arr)
    index = np.arange(1, n + 1)

    return np.sum((2 * index - n - 1) * sorted_arr) / (n * sorted_arr.sum())


def calculate_hhi(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]

    total = arr.sum()
    if len(arr) == 0 or total == 0:
        return 0.0

    shares = arr / total
    return float(np.sum(shares ** 2))


def safe_pct(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100


def choice_label(choice, choices):
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(choices):
            return choices[idx]
    except Exception:
        pass

    return str(choice)


# ============================================================
# FETCH PROPOSALS
# ============================================================

def fetch_top_valid_proposals(limit=TARGET_PROPOSALS, fetch_pool=FETCH_POOL):
    print(f"Fetching top {limit} valid closed Arbitrum proposals by voter turnout...")

    query = """
    query ($space: String!,$limit: Int!) {
      proposals(
        first: $limit,
        where: { space: $space, state: "closed" },
        orderBy: "votes",
        orderDirection: desc
      ) {
        id
        title
        votes
        choices
        type
        scores
        scores_total
        start
        end
        snapshot
      }
    }
    """

    data = run_query(query, {"space": SPACE_ID, "limit": fetch_pool})
    proposals = data["data"]["proposals"]

    valid = [
        p for p in proposals
        if p.get("type") in VALID_PROPOSAL_TYPES
    ]

    print(f"Fetched {len(proposals)} total proposals from pool.")
    print(f"Found {len(valid)} valid single-choice/basic proposals.")

    if len(valid) < limit:
        print("Not enough valid proposals. Doing deeper scan...")
        data_deep = run_query(query, {"space": SPACE_ID, "limit": fetch_pool})
        proposals = data_deep["data"]["proposals"]

        valid = [
            p for p in proposals
            if p.get("type") in VALID_PROPOSAL_TYPES
        ]

        print(f"After deeper scan, found {len(valid)} valid proposals.")

    return valid[:limit]


# ============================================================
# FETCH VOTES WITH CHECKPOINTING
# ============================================================

def fetch_all_votes(proposal_id):
    raw_path = os.path.join(RAW_DIR, f"{proposal_id}.csv")

    if os.path.exists(raw_path):
        existing_df = pd.read_csv(raw_path)

        if not existing_df.empty and "created" in existing_df.columns:
            existing_df["created"] = pd.to_numeric(existing_df["created"], errors="coerce").fillna(0).astype(int)
            last_created_timestamp = int(existing_df["created"].max())
            all_votes = existing_df.to_dict("records")
            print(f"  Resuming from checkpoint: {len(all_votes)} votes already saved.")
        else:
            last_created_timestamp = 0
            all_votes = []
    else:
        last_created_timestamp = 0
        all_votes = []

    print(f"  Starting deep-harvest for proposal: {proposal_id[:8]}...")

    while True:
        query = f"""
        query ($proposal: String!,$lastTimestamp: Int!) {{
          votes(
            first: {PAGE_SIZE},
            where: {{ proposal: $proposal, created_gt:$lastTimestamp }},
            orderBy: "created",
            orderDirection: asc
          ) {{
            voter
            choice
            vp
            created
          }}
        }}
        """

        data = run_query(
            query,
            {
                "proposal": proposal_id,
                "lastTimestamp": last_created_timestamp
            }
        )

        votes = data["data"]["votes"]

        if not votes:
            break

        all_votes.extend(votes)
        last_created_timestamp = int(votes[-1]["created"])

        df_checkpoint = pd.DataFrame(all_votes)
        df_checkpoint.to_csv(raw_path, index=False)

        print(f"    Collected {len(all_votes)} votes total... checkpoint saved.")

        time.sleep(2.5)  # Healthy rest break between requests

    return all_votes


# ============================================================
# MAIN DATA COLLECTION
# ============================================================

proposals = fetch_top_valid_proposals(limit=TARGET_PROPOSALS, fetch_pool=FETCH_POOL)

with open("proposals_manifest.json", "w") as f:
    json.dump(proposals, f, indent=4)

all_compiled_data = []

for p in proposals:
    proposal_id = p["id"]
    title_short = p["title"][:70].replace("\n", " ")

    print(f"\nDownloading votes for: {title_short} | votes: {p['votes']} | type: {p['type']}")

    votes = fetch_all_votes(proposal_id)
    df = pd.DataFrame(votes)

    if df.empty:
        print("No votes found. Skipping.")
        continue

    df["proposal_id"] = proposal_id
    df["proposal_title"] = p["title"]
    df["proposal_type"] = p["type"]

    all_compiled_data.append(df)

if not all_compiled_data:
    raise Exception("No vote data downloaded.")

master_df = pd.concat(all_compiled_data, ignore_index=True)

master_df["vp"] = pd.to_numeric(master_df["vp"], errors="coerce").fillna(0)
master_df["created"] = pd.to_numeric(master_df["created"], errors="coerce").fillna(0).astype(int)

master_df.to_csv("master_proposals_data.csv", index=False)

print("\nSaved master_proposals_data.csv")


# ============================================================
# SIMULATION ENGINE
# ============================================================

with open("proposals_manifest.json", "r") as f:
    proposals_manifest = json.load(f)

summary_results = []

print("\n==================================================================")
print("BATCH SIMULATION ENGINE: SQUARE-ROOT VOTING")
print("==================================================================")

for p in proposals_manifest:
    proposal_id = p["id"]
    proposal_title = p["title"]
    choices = p["choices"]

    df_p = master_df[master_df["proposal_id"] == proposal_id].copy()

    if df_p.empty:
        continue

    df_p["vp"] = pd.to_numeric(df_p["vp"], errors="coerce").fillna(0)
    df_p = df_p[df_p["vp"] > 0].copy()

    if df_p.empty:
        continue

    total_vp = df_p["vp"].sum()
    unique_voters = df_p["voter"].nunique()

    # -----------------------------
    # Whale concentration
    # -----------------------------
    sorted_vp = df_p["vp"].sort_values(ascending=False)

    top_1_share = safe_pct(sorted_vp.head(1).sum(), total_vp)
    top_5_share = safe_pct(sorted_vp.head(5).sum(), total_vp)
    top_10_share = safe_pct(sorted_vp.head(10).sum(), total_vp)

    gini = calculate_gini(df_p["vp"].values)
    hhi = calculate_hhi(df_p["vp"].values)

    # -----------------------------
    # Traditional token voting
    # -----------------------------
    trad_votes = df_p.groupby("choice")["vp"].sum()
    trad_pct = trad_votes / trad_votes.sum() * 100

    trad_winner = trad_votes.idxmax()
    trad_winner_label = choice_label(trad_winner, choices)

    sorted_trad_pct = trad_pct.sort_values(ascending=False)
    trad_margin = sorted_trad_pct.iloc[0] - (
        sorted_trad_pct.iloc[1] if len(sorted_trad_pct) > 1 else 0
    )

    # -----------------------------
    # Corrected QV Simulation
    # qv_score(choice) = sum(sqrt(vp))
    # -----------------------------
    df_p["compressed_weight"] = np.sqrt(df_p["vp"])

    # CHANGED: Dropped the erroneous `** 2` exponential scaling component
    qv_scores = df_p.groupby("choice")["compressed_weight"].sum()
    qv_pct = qv_scores / qv_scores.sum() * 100

    qv_winner = qv_scores.idxmax()
    qv_winner_label = choice_label(qv_winner, choices)

    sorted_qv_pct = qv_pct.sort_values(ascending=False)
    qv_margin = sorted_qv_pct.iloc[0] - (
        sorted_qv_pct.iloc[1] if len(sorted_qv_pct) > 1 else 0
    )

    # -----------------------------
    # Difference metrics (Percentage Points)
    # -----------------------------
    flipped = trad_winner != qv_winner
    margin_delta_pp = qv_margin - trad_margin  # Expressed directly as absolute percentage points

    # -----------------------------
    # Validate reconstruction
    # -----------------------------
    snapshot_scores_total = float(p.get("scores_total") or 0)
    reconstruction_diff = abs(total_vp - snapshot_scores_total)

    if snapshot_scores_total > 0:
        reconstruction_error_pct = reconstruction_diff / snapshot_scores_total * 100
    else:
        reconstruction_error_pct = 0.0

    summary_results.append({
        "Proposal ID": proposal_id,
        "Proposal Title": proposal_title,
        "Proposal Type": p.get("type"),
        "Snapshot Votes Count": p.get("votes"),
        "Unique Voters Downloaded": unique_voters,

        "Traditional Winner": trad_winner_label,
        "QV Winner": qv_winner_label,
        "Winner Flipped": flipped,

        "Traditional Margin %": round(trad_margin, 2),
        "QV Margin %": round(qv_margin, 2),
        "Margin Delta (pp)": round(margin_delta_pp, 2),

        "Total VP Reconstructed": round(total_vp, 2),
        "Snapshot Scores Total": round(snapshot_scores_total, 2),
        "Reconstruction Error %": round(reconstruction_error_pct, 4),

        "Top 1 Voter Share %": round(top_1_share, 2),
        "Top 5 Voter Share %": round(top_5_share, 2),
        "Top 10 Voter Share %": round(top_10_share, 2),
        "Gini Score": round(gini, 4),
        "HHI Score": round(hhi, 4),
    })

summary_df = pd.DataFrame(summary_results)

print("\nSummary Results:")
print(summary_df.to_string(index=False))

summary_df.to_csv("reproducible_batch_results.csv", index=False)

print("\nSaved reproducible_batch_results.csv")
print("Saved proposals_manifest.json")
print("Saved master_proposals_data.csv")