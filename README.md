# Argus - Distributed Leader Election & Auditor System

A robust leader election system for supply chain security scanning, coordinating multiple auditor nodes using Redis with strict Leader-Follower role separation.

## Architecture (Refactored)

The system implements a **strict separation** between Leader and Follower roles:

### Consensus Layer
- **Redis Lease Pattern** (King of the Hill) for leader election
- **Heartbeat Monitoring** with 3-miss fault tolerance
- **Node Health Tracking** using ephemeral keys with TTL
- **Automatic Failover** when leader fails

### Leader Responsibilities (Runs ONLY on elected leader)
1. **Graph Search**: Query dependency graph for vulnerable packages
2. **Randomised Accepter**: Stochastically filter to 20% of results
3. **Queue Push**: Add filtered tasks to `LEADER_QUEUE`

### Follower Responsibilities (Runs on ALL non-leader nodes)
1. **Task Consumption**: Pop tasks from `LEADER_QUEUE` (BLPOP)
2. **3-Step Pipeline**:
   - **Gemma Code Check** (stub for LLM integration)
   - **RAG Vulnerability Lookup** (stub for vector DB)
   - **Blockchain Commit** (stub for Polygon integration)

## Components

### Configuration (`auditor/config.py`)
Centralized configuration for Redis keys and system constants:
- `LEADER_KEY`, `LEADER_QUEUE`, `NODE_HEALTH_PREFIX`
- TTL, heartbeat intervals, filter percentage

### Infrastructure (`auditor/infra/`)
- `redis_client.py`: Singleton Redis connection manager with retry logic

### Core (`auditor/core/`)
- `consensus.py`: Enhanced consensus engine with heartbeat and fault tolerance
- `leader.py`: Leader orchestrator (graph search + filtering + scheduling)
- `follower.py`: Follower worker with 3-step pipeline (all stubs)
- `data.py`: Mock GraphDB and VulnerabilityIndexer

### Main (`auditor/main.py`)
Orchestrator with dynamic role switching:
- **Consensus Thread**: Manages leader election
- **Heartbeat Thread**: Maintains node health (all nodes)
- **Role Thread**: Runs LeaderOrchestrator OR FollowerWorker based on consensus

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Ensure Redis is running:
```bash
docker run -d -p 6379:6379 redis:7-alpine
# OR
docker-compose up -d
```

## Usage

### Single Node
```bash
python -m auditor.main --node-id node-A
```

### Multiple Nodes (Different Terminals)
```bash
# Terminal 1
python -m auditor.main --node-id node-A

# Terminal 2
python -m auditor.main --node-id node-B

# Terminal 3
python -m auditor.main --node-id node-C
```

### Custom Configuration
```bash
python -m auditor.main --ttl 10 --heartbeat-interval 3
```

## How It Works

### Consensus Thread (All Nodes)
- Runs every `TTL/2` seconds
- Attempts to claim leadership using Redis SETNX
- Triggers role change when leadership status changes

### Heartbeat Thread (All Nodes)
- Runs every 2 seconds (configurable)
- Registers node health with ephemeral key
- Leader refreshes lease TTL
- Tracks missed heartbeats (abdicates after 3 misses)

### Leader Orchestrator (Leader Only)
1. Query graph database for vulnerable packages
2. Apply 20% randomized filter
3. Push selected packages to `LEADER_QUEUE`
4. Repeat every 10 seconds

### Follower Worker (Followers Only)
1. Block on `BLPOP` waiting for tasks from `LEADER_QUEUE`
2. Execute 3-step pipeline:
   - Run Gemma code check (stub)
   - Query RAG indexer (stub)
   - Save to blockchain (stub)
3. Repeat continuously

## Key Logs

Watch for these events:

**Consensus:**
- `👑 Node X claimed LEADERSHIP` - Node became leader
- `👥 Node X lost leadership` - Node became follower
- `💓 Heartbeat sent` - Node health update

**Leader:**
- `🔍 Querying dependency graph...` - Graph search started
- `🎲 Randomised filter: selected 20%` - Filtering applied
- `📤 Pushed N tasks to queue` - Tasks scheduled

**Follower:**
- `📥 Received task: package@version` - Task received
- `🤖 [STUB] Running Gemma code check...` - Pipeline step 1
- `🔍 [STUB] Querying RAG indexer...` - Pipeline step 2
- `⛓️  [STUB] Saving to blockchain...` - Pipeline step 3
- `✅ Pipeline complete` - Task finished

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Consensus Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Election   │  │  Heartbeat   │  │ Node Health  │  │
│  │  (SETNX)     │  │  (3-miss)    │  │  Tracking    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                  │
┌─────────▼──────────┐            ┌─────────▼──────────┐
│      LEADER        │            │     FOLLOWER       │
│  ┌──────────────┐  │            │  ┌──────────────┐  │
│  │ Graph Search │  │            │  │ Pop from     │  │
│  └──────┬───────┘  │            │  │ Queue        │  │
│  ┌──────▼───────┐  │            │  └──────┬───────┘  │
│  │ Randomised   │  │            │  ┌──────▼───────┐  │
│  │ Filter (20%) │  │            │  │ Gemma Check  │  │
│  └──────┬───────┘  │            │  │   (stub)     │  │
│  ┌──────▼───────┐  │            │  └──────┬───────┘  │
│  │ Push to      │  │            │  ┌──────▼───────┐  │
│  │ LEADER_QUEUE │  │            │  │ RAG Lookup   │  │
│  └──────────────┘  │            │  │   (stub)     │  │
└────────────────────┘            │  └──────┬───────┘  │
                                   │  ┌──────▼───────┐  │
                                   │  │ Blockchain   │  │
                                   │  │   (stub)     │  │
                                   │  └──────────────┘  │
                                   └────────────────────┘
```

## Edge Cases Handled

- **Redis Connection Loss**: Automatic reconnection with retry logic
- **Leader Failure**: Automatic failover within `TTL` seconds
- **Heartbeat Misses**: Leader abdicates after 3 consecutive misses
- **Graceful Shutdown**: Leader abdicates, workers finish current task
- **Split Brain Prevention**: Redis SETNX ensures only one leader
- **Node Health**: Ephemeral keys expire if node crashes

## Follower Pipeline Stubs

The follower pipeline methods are **intentionally left as stubs**:

```python
def run_gemma_check(package_data):
    # TODO: Implement Gemma LLM integration
    pass

def query_rag_indexer(package_data):
    # TODO: Query Vector DB
    pass

def save_conclusion_to_blockchain(result):
    # TODO: Commit to Polygon
    pass
```

These will be implemented in future sprints:
- **Sprint 2**: Gemma LLM integration
- **Sprint 3**: RAG vector database
- **Sprint 4**: Blockchain commit

## Testing

Run the demo:
```bash
./demo.py
```

Run comprehensive tests:
```bash
./test_system.py
```

## Breaking Changes from v1

- **Queue Name**: `argus:tasks` → `argus:leader_queue`
- **Classes**: `LeaderElector` → `ConsensusManager`, `AuditScheduler` → `LeaderOrchestrator`, `AuditWorker` → `FollowerWorker`
- **Behavior**: Strict role separation (leader doesn't execute tasks, followers don't schedule)

## Next Steps

1. Implement Gemma LLM integration in `follower.py`
2. Implement RAG vector database in `follower.py`
3. Implement blockchain commit in `follower.py`
4. Replace mock GraphDB with real Neo4j queries
5. Add metrics and monitoring