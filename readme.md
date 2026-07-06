# Arbitrum DAO: Quadratic Voting Simulation Engine

An independent data science project evaluating the impact of wealth concentration (plutocracy) in decentralized governance, using real-world voting data from the Arbitrum DAO ecosystem.

<<<<<<< HEAD
## 📊 Core Research Findings
=======
## Core Research Findings
>>>>>>> f097dea7a2a91b85dea6ab35606d94f0d2a109bd

The simulation tested two distinct governance scenarios from Snapshot.org to analyze how a mathematical square-root weight modification ($\sqrt{\text{Tokens}}$) alters voting outcomes:

1. **Aligned Proposal (Transaction Policy):** - **Gini Coefficient:** 0.9892 (Extreme Inequality)
   - **Result:** Traditional (95.62% YES) vs. Quadratic (95.37% YES). The outcome remained stable, mathematically validating a true community consensus.

2. **Disaligned Proposal (Council Election Terms):** - **Gini Coefficient:** 0.9950 (Extreme Inequality)
   - **Result:** The outcome **COMPLETELY FLIPPED**. Traditional voting allowed a wealthy whale minority to pass a measure (50.30% YES). Applying Quadratic Voting restored democratic balance, shifting the victory to the grassroots crowd preference (45.05% NO/Choice 1).

<<<<<<< HEAD
## 🛠️ Tech Stack & Methodology
- **Language:** Python 3
- **Data Acquisition:** Snapshot GraphQL API via the `requests` library
- **Data Engineering & Simulation:** `pandas` and `numpy`
- **Inequality Metric:** Custom Gini Coefficient calculation matrix
=======
## Tech Stack & Methodology
- **Language:** Python 3
- **Data Acquisition:** Snapshot GraphQL API via the `requests` library
- **Data Engineering & Simulation:** `pandas` and `numpy`
- **Inequality Metric:** Custom Gini Coefficient calculation matrix
>>>>>>> f097dea7a2a91b85dea6ab35606d94f0d2a109bd
