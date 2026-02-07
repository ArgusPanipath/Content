# 🛡️ Argus: The Supply Chain Sentinel

**Tagline:** A dual-engine defense system (Gatekeeper + Auditor) securing the open-source supply chain against typosquatting, social engineering, and dormant malware.

---

## 🚀 Project Overview

Modern software relies on **"blind trust"** in open-source registries. **Argus Panipath** replaces this with **"Verified Truth."** We use a **Gatekeeper** to block malicious updates in real-time and an **Auditor (Leader Election)** to continuously scan the existing ecosystem for latent threats using distributed AI.

---

## 📂 Repository Breakdown

Our system is modularized into four specialized repositories. Here is how they fit into the architecture:

### 1. **static_params** (The First Line of Defense)

**Role:** The Filter Gateway & Static Registry.

**Function:** This module acts as the initial firewall for incoming packages. It houses the lightweight, high-speed rules used to reject obvious threats before they reach the expensive AI layers.

**Key Capabilities:**
- **Metadata Filtering:** Validates package names, versions, and author details.
- **Static Testing Modules:** Runs rapid checks for "Entropy" (obfuscated code), dangerous API calls, and known malicious signatures.
- **Tech:** JavaScript/Python, Regex Engines.

**Repository:** [Link to static_params](#)

---

### 2. **Dependancy_graph_builder** (The Map)

**Role:** The Graph Database Construction Engine.

**Function:** Builds and maintains the massive "Graph DB of Packages". It ingests raw data from npm/PyPI and maps the complex web of dependencies to depth 10+.

**Key Capabilities:**
- **Ingestion Pipeline:** Asynchronously fetches package updates.
- **Cluster Analysis:** Identifies "Dependency Clusters" to help the Auditor prioritize high-impact libraries.
- **Neo4j Integration:** Stores the "Shadow Graph" for fast lookups without querying the public registry API every time.

**Repository:** [Link to Dependancy_graph_builder](#)

---

### 3. **llm-council** (The Judge)

**Role:** The Council LLM & Consensus Engine.

**Function:** The "Brain" of the Gatekeeper. When code passes static checks, it enters this layer where multiple LLM agents (e.g., Gemini, Llama) vote on its safety.

**Key Capabilities:**
- **Code Understanding:** Analyzes obfuscated logic that static tools miss.
- **Final Conscience:** Aggregates votes from different models to reach a "Decision Box" verdict (Flag/Alert).
- **Context Saving:** Packages the reasoning to be stored on the Blockchain.

**Repository:** [Link to llm-council](#)

---

### 4. **LeaderElection** (The Auditor / The Swarm)

**Role:** The Distributed Auditor System.

**Function:** Manages the background scanning of millions of existing packages. It uses a Leader-Follower architecture to distribute work across multiple nodes without duplication.

**Architecture Components:**

#### Leader Node:
- **Consensus Algorithm:** Uses Redis Lease ("Life TTL") to maintain authority.
- **Randomised Accepter:** Stochastically selects high-priority clusters from the Graph DB.
- **Queue Push:** Assigns tasks to the "Leader Queue".

#### Follower Nodes:
- **Gemma for Code Check:** Runs localized LLM inference.
- **RAG Vulnerability Finder:** Queries the Vector DB for historical attack patterns.
- **Blockchain Commit:** Writes the final audit report to the immutable ledger.

**Repository:** [Link to LeaderElection](#)

---

## �️ System Architecture

Our solution is divided into two autonomous flows:

### Flow A: The Gatekeeper (Real-Time)

**Trigger:** New npm publish event.

**Process:** `static_params` (Filter) → `llm-council` (Analysis) → Blockchain Decision.

**Goal:** Stop the attack before it enters the registry.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Package   │────▶│   Static    │────▶│ LLM Council │
│   Upload    │     │   Params    │     │   (Judge)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Blockchain  │
                                        │  Decision   │
                                        └─────────────┘
```

### Flow B: The Leader Election (Background)

**Trigger:** Scheduled Audit / Heartbeat.

**Process:** `Dependancy_graph_builder` (Map) → `LeaderElection` (Assign) → Follower Nodes (Execute).

**Goal:** Find dormant threats (Sleeper Agents) that are already inside.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Dependency     │────▶│     Leader      │────▶│    Follower     │
│  Graph Builder  │     │    Election     │     │     Nodes       │
│   (Neo4j Map)   │     │  (Consensus)    │     │  (AI Workers)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │ Blockchain  │
                                                   │   Commit    │
                                                   └─────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Core** | Python 3.10+ |
| **Databases** | Neo4j (Graph), Redis (Consensus/Queue), Vector DB (RAG) |
| **AI Models** | Gemini Pro (Council), Gemma (Local Follower) |
| **Infrastructure** | Docker, Polygon Blockchain (L2) |
| **Orchestration** | Leader Election (Redis Lease Pattern) |

---

## 🏁 Getting Started

To run the full system, clone the repositories and start the orchestration:

### 1. Initialize the Graph
Run `Dependancy_graph_builder` to seed the Neo4j instance.

```bash
cd Dependancy_graph_builder
docker-compose up -d
python -m graph_builder.main
```

### 2. Start the Gatekeeper
Deploy `static_params` and `llm-council` as microservices.

```bash
cd static_params
docker-compose up -d

cd ../llm-council
docker-compose up -d
```

### 3. Unleash the Swarm
Run `LeaderElection` on multiple nodes. One will automatically become Leader; the others will start processing the queue.

```bash
cd LeaderElection
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 1 - Node A
python -m auditor.main --node-id node-A

# Terminal 2 - Node B
python -m auditor.main --node-id node-B

# Terminal 3 - Node C
python -m auditor.main --node-id node-C
```

---

## 📊 Key Features

### Real-Time Protection
- ⚡ **Sub-second filtering** with static_params
- 🧠 **Multi-LLM consensus** for complex threats
- 🚫 **Immediate blocking** of malicious packages

### Background Auditing
- 🔍 **Continuous scanning** of existing packages
- 📈 **Priority-based** cluster analysis
- 🤖 **Distributed AI** processing with fault tolerance

### Immutable Audit Trail
- ⛓️ **Blockchain storage** of all decisions
- 📝 **Transparent reasoning** from LLM council
- 🔒 **Tamper-proof** security reports

---

## 🎯 Use Cases

1. **Typosquatting Detection:** Catch packages with names similar to popular libraries
2. **Social Engineering:** Identify suspicious author patterns and metadata
3. **Dormant Malware:** Find "sleeper agents" that activate after installation
4. **Supply Chain Attacks:** Detect compromised maintainer accounts
5. **Obfuscated Code:** Analyze intentionally hidden malicious logic

---

## 🤝 Contributing

We welcome contributions to any of the four repositories! Please see individual repository READMEs for specific contribution guidelines.

---

## 📄 License

[Specify License Here]

---

## 🔗 Links

- **Documentation:** [Link to Docs](#)
- **Research Paper:** [Link to Paper](#)
- **Demo Video:** [Link to Demo](#)
- **Contact:** [Your Contact Info]

---

**Built with ❤️ to secure the open-source ecosystem**