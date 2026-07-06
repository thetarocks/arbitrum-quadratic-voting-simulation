# Arbitrum Quadratic Voting Simulation

A Python-based data pipeline designed to interface with the Snapshot GraphQL API to fetch, analyze, and simulate quadratic voting behavior data for the Arbitrum DAO (`arbitrumfoundation.eth`). 

This tool extracts historical proposal configurations, pulls exhaustive voting details, and processes structural datasets for downstream simulation and algorithmic evaluation.

---

##  Features

* **GraphQL API Integration:** Queries the Snapshot Hub for high-volume governance data.
* **Proposal Extraction:** Retrieves the top recent proposals filtered by criteria like vote count and state.
* **Exhaustive Vote Pagination:** Automatically handles token pagination (`skip` loops) to fetch 100% of the voting logs for targeted proposals.
* **Structured Data Export:** Cleans and exports data outputs directly into manageable formats (`master_proposals_data.csv`, `reproducible_batch_results.csv`, and JSON manifests).

---

## Project Structure

```text
projectz/
│
├── get_data.py                  # Script responsible for querying Snapshot GraphQL API
├── simulate.py                  # Module for analyzing data models or voting simulations
├── readme.md                    # Project documentation
│
├── data_outputs/ (Generated)
│   ├── master_proposals_data.csv  # Combined dataset of tracked DAO proposals
│   ├── reproducible_batch_results.csv # Outputs from simulation routines
│   └── proposals_manifest.json    # JSON ledger tracking operation state
└── datasets/
    ├── aligned_data.csv         # Structured dataset optimized for the simulator
    └── disaligned_data.csv      # Outlier/variance tracking data