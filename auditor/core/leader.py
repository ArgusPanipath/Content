"""
Leader Orchestrator - Runs ONLY when node is elected leader
Responsible for graph search, randomized filtering, and task scheduling.
"""
import logging
import random
import time
from typing import List
from auditor.infra.redis_client import get_redis_client
from auditor.core.data import GraphDB
from auditor.config import (
    LEADER_QUEUE,
    LEADER_TTL,
    RANDOMISED_FILTER_PERCENTAGE,
    GRAPH_SEARCH_INTERVAL
)

logger = logging.getLogger(__name__)


class LeaderOrchestrator:
    """
    Leader-only orchestrator for task scheduling.
    
    Responsibilities:
    1. Query dependency graph for vulnerable packages
    2. Apply randomized filter (20% selection)
    3. Push filtered tasks to shared queue
    """
    
    def __init__(self, node_id: str, ttl: int = LEADER_TTL):
        """
        Initialize the leader orchestrator.
        
        Args:
            node_id: Unique identifier for this node
            ttl: Leader lease time-to-live
        """
        self.node_id = node_id
        self.ttl = ttl
        self.redis_client = get_redis_client()
        self.graph_db = GraphDB()
        self._running = False
        
        logger.info(f"👑 LeaderOrchestrator initialized for node: {self.node_id}")
    
    def query_dependency_graph(self) -> List[str]:
        """
        Query the dependency graph for vulnerable package clusters.
        
        Component: Graph Search (from architecture diagram)
        
        In production, this would execute Cypher queries against Neo4j
        to find high-priority clusters based on vulnerability scores,
        dependency depth, and usage patterns.
        
        Returns:
            List[str]: List of package identifiers to audit
        """
        logger.info(f"🔍 [{self.node_id}] Querying dependency graph...")
        
        try:
            # Get clusters from graph database
            clusters = self.graph_db.get_clusters()
            
            logger.info(
                f"📊 [{self.node_id}] Graph search found {len(clusters)} "
                f"candidate packages"
            )
            
            return clusters
        
        except Exception as e:
            logger.error(f"❌ Graph query failed: {e}")
            return []
    
    def randomised_filter(self, candidates: List[str]) -> List[str]:
        """
        Apply randomised accepter filter to candidates.
        
        Component: Randomised Accepter (from architecture diagram)
        
        Implements stochastic filtering to prevent over-scanning.
        Selects only a percentage (default 20%) of candidates randomly.
        
        This ensures:
        - System doesn't get overwhelmed with tasks
        - Different packages get scanned over time
        - Load is distributed across multiple cycles
        
        Args:
            candidates: List of package candidates from graph search
            
        Returns:
            List[str]: Filtered list of packages to audit
        """
        if not candidates:
            logger.warning(f"⚠️  [{self.node_id}] No candidates to filter")
            return []
        
        # Calculate number to select (20% by default)
        num_to_select = max(1, int(len(candidates) * RANDOMISED_FILTER_PERCENTAGE))
        
        # Randomly select packages
        selected = random.sample(candidates, min(num_to_select, len(candidates)))
        
        logger.info(
            f"🎲 [{self.node_id}] Randomised filter: selected {len(selected)} "
            f"packages from {len(candidates)} candidates "
            f"({RANDOMISED_FILTER_PERCENTAGE * 100:.0f}%)"
        )
        
        return selected
    
    def push_to_queue(self, packages: List[str]) -> int:
        """
        Push filtered packages to the leader queue.
        
        Uses Redis RPUSH to add packages to the right end of the queue.
        Followers will pop from the left end (BLPOP) for FIFO processing.
        
        Args:
            packages: List of package identifiers to schedule
            
        Returns:
            int: Number of packages successfully pushed
        """
        if not packages:
            logger.debug(f"ℹ️  [{self.node_id}] No packages to push")
            return 0
        
        try:
            # Push all packages to the queue atomically
            count = self.redis_client.rpush(LEADER_QUEUE, *packages)
            
            logger.info(
                f"📤 [{self.node_id}] Pushed {len(packages)} tasks to queue "
                f"(total queue size: {count})"
            )
            
            return len(packages)
        
        except Exception as e:
            logger.error(f"❌ Failed to push tasks to queue: {e}")
            return 0
    
    def run_scheduling_cycle(self) -> int:
        """
        Execute a complete leader scheduling cycle.
        
        Workflow:
        1. Graph Search - Query dependency graph
        2. Randomised Accepter - Filter to 20%
        3. Queue Push - Add to shared queue
        
        Returns:
            int: Number of tasks scheduled
        """
        logger.info(f"🔄 [{self.node_id}] Starting leader scheduling cycle...")
        
        start_time = time.time()
        
        try:
            # Step 1: Graph Search
            candidates = self.query_dependency_graph()
            
            if not candidates:
                logger.warning(f"⚠️  [{self.node_id}] No candidates from graph search")
                return 0
            
            # Step 2: Randomised Accepter
            selected = self.randomised_filter(candidates)
            
            # Step 3: Queue Push
            scheduled_count = self.push_to_queue(selected)
            
            elapsed = time.time() - start_time
            logger.info(
                f"✅ [{self.node_id}] Scheduling cycle complete: "
                f"{scheduled_count} tasks scheduled in {elapsed:.2f}s"
            )
            
            return scheduled_count
        
        except Exception as e:
            logger.error(f"❌ Scheduling cycle failed: {e}")
            return 0
    
    def run(self) -> None:
        """
        Run the leader orchestrator loop.
        
        Continuously executes scheduling cycles while respecting
        the leader lease TTL (Life TTL component).
        """
        self._running = True
        logger.info(f"▶️  [{self.node_id}] Leader orchestrator started")
        
        while self._running:
            try:
                # Run scheduling cycle
                self.run_scheduling_cycle()
                
                # Sleep for the configured interval
                # This respects the "Life TTL" - we don't schedule
                # more frequently than the system can handle
                logger.debug(
                    f"⏸️  [{self.node_id}] Sleeping for {GRAPH_SEARCH_INTERVAL}s "
                    f"before next cycle"
                )
                time.sleep(GRAPH_SEARCH_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info(f"⚠️  [{self.node_id}] Leader interrupted by user")
                self.stop()
                break
            
            except Exception as e:
                logger.error(f"❌ Leader loop error: {e}")
                time.sleep(5)  # Back off on error
        
        logger.info(f"🛑 [{self.node_id}] Leader orchestrator stopped")
    
    def stop(self) -> None:
        """Stop the leader orchestrator."""
        logger.info(f"🛑 [{self.node_id}] Stopping leader orchestrator...")
        self._running = False
    
    @property
    def is_running(self) -> bool:
        """Check if orchestrator is running."""
        return self._running
