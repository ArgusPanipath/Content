"""
Argus - Main Orchestrator (Refactored)
Coordinates consensus, leader orchestration, and follower execution.

Architecture:
- Consensus Thread: Manages leader election and heartbeat
- Role Thread: Runs LeaderOrchestrator OR FollowerWorker based on consensus
"""
import logging
import threading
import time
import signal
import sys
import uuid
from typing import Optional

from auditor.core.consensus import ConsensusManager
from auditor.core.leader import LeaderOrchestrator
from auditor.core.follower import FollowerWorker
from auditor.config import LEADER_TTL, HEARTBEAT_INTERVAL, GRAPH_SEARCH_INTERVAL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArgusOrchestrator:
    """
    Main orchestrator for the Argus leader election system.
    
    Manages:
    1. Consensus (leader election + heartbeat)
    2. Leader orchestration (if elected leader)
    3. Follower execution (if not leader)
    """
    
    def __init__(
        self,
        node_id: Optional[str] = None,
        ttl: int = LEADER_TTL,
        heartbeat_interval: float = HEARTBEAT_INTERVAL
    ):
        """
        Initialize the orchestrator.
        
        Args:
            node_id: Unique node identifier (generates UUID if not provided)
            ttl: Leader lease time-to-live in seconds
            heartbeat_interval: How often to send heartbeat in seconds
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.ttl = ttl
        self.heartbeat_interval = heartbeat_interval
        
        # Initialize consensus manager
        self.consensus = ConsensusManager(self.node_id, ttl)
        
        # Initialize role-specific components (will be started based on role)
        self.leader_orchestrator: Optional[LeaderOrchestrator] = None
        self.follower_worker: Optional[FollowerWorker] = None
        
        # Control flags
        self._running = False
        self._consensus_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._role_thread: Optional[threading.Thread] = None
        self._current_role: Optional[str] = None  # "leader" or "follower"
        
        logger.info(f"🚀 ArgusOrchestrator initialized for node: {self.node_id}")
        logger.info(
            f"⚙️  Configuration: TTL={ttl}s, Heartbeat Interval={heartbeat_interval}s"
        )
    
    def _consensus_loop(self) -> None:
        """
        Consensus loop - manages leader election.
        
        Continuously attempts to claim/maintain leadership.
        Triggers role changes when leadership status changes.
        """
        logger.info(f"🗳️  [{self.node_id}] Consensus loop started")
        
        while self._running:
            try:
                # Attempt to claim/maintain leadership
                is_leader = self.consensus.attempt_leadership()
                
                # Check if role changed
                new_role = "leader" if is_leader else "follower"
                
                if new_role != self._current_role:
                    logger.info(
                        f"🔄 [{self.node_id}] Role change: "
                        f"{self._current_role or 'none'} → {new_role}"
                    )
                    self._handle_role_change(new_role)
                
                # Sleep before next election attempt
                time.sleep(self.ttl / 2)
            
            except Exception as e:
                logger.error(f"❌ Consensus loop error: {e}")
                time.sleep(self.heartbeat_interval)
        
        logger.info(f"🛑 [{self.node_id}] Consensus loop stopped")
    
    def _heartbeat_loop(self) -> None:
        """
        Heartbeat loop - maintains node health and leader lease.
        
        Runs on ALL nodes regardless of role.
        """
        logger.info(f"💓 [{self.node_id}] Heartbeat loop started")
        
        while self._running:
            try:
                # Send heartbeat
                self.consensus.heartbeat()
                
                # Sleep before next heartbeat
                time.sleep(self.heartbeat_interval)
            
            except Exception as e:
                logger.error(f"❌ Heartbeat loop error: {e}")
                time.sleep(self.heartbeat_interval)
        
        logger.info(f"🛑 [{self.node_id}] Heartbeat loop stopped")
    
    def _handle_role_change(self, new_role: str) -> None:
        """
        Handle role change between leader and follower.
        
        Stops the current role thread and starts the new one.
        
        Args:
            new_role: New role ("leader" or "follower")
        """
        # Stop current role thread if exists
        if self._role_thread and self._role_thread.is_alive():
            logger.info(f"🛑 [{self.node_id}] Stopping {self._current_role} thread...")
            
            if self._current_role == "leader" and self.leader_orchestrator:
                self.leader_orchestrator.stop()
            elif self._current_role == "follower" and self.follower_worker:
                self.follower_worker.stop()
            
            self._role_thread.join(timeout=5)
        
        # Update current role
        self._current_role = new_role
        
        # Start new role thread
        if new_role == "leader":
            self._start_leader_thread()
        else:
            self._start_follower_thread()
    
    def _start_leader_thread(self) -> None:
        """Start the leader orchestrator thread."""
        logger.info(f"👑 [{self.node_id}] Starting leader orchestrator...")
        
        self.leader_orchestrator = LeaderOrchestrator(self.node_id, self.ttl)
        
        self._role_thread = threading.Thread(
            target=self.leader_orchestrator.run,
            name=f"Leader-{self.node_id[:8]}",
            daemon=True
        )
        self._role_thread.start()
        
        logger.info(f"✅ [{self.node_id}] Leader orchestrator started")
    
    def _start_follower_thread(self) -> None:
        """Start the follower worker thread."""
        logger.info(f"👥 [{self.node_id}] Starting follower worker...")
        
        self.follower_worker = FollowerWorker(self.node_id)
        
        self._role_thread = threading.Thread(
            target=self.follower_worker.listen_and_execute,
            name=f"Follower-{self.node_id[:8]}",
            daemon=True
        )
        self._role_thread.start()
        
        logger.info(f"✅ [{self.node_id}] Follower worker started")
    
    def start(self) -> None:
        """Start the orchestrator with all threads."""
        if self._running:
            logger.warning("⚠️  Orchestrator already running")
            return
        
        self._running = True
        
        logger.info(f"▶️  Starting Argus orchestrator for node: {self.node_id}")
        
        # Start heartbeat thread (runs on all nodes)
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"Heartbeat-{self.node_id[:8]}",
            daemon=True
        )
        self._heartbeat_thread.start()
        
        # Start consensus thread (runs on all nodes)
        self._consensus_thread = threading.Thread(
            target=self._consensus_loop,
            name=f"Consensus-{self.node_id[:8]}",
            daemon=True
        )
        self._consensus_thread.start()
        
        logger.info("✅ Orchestrator started successfully")
    
    def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        if not self._running:
            logger.warning("⚠️  Orchestrator not running")
            return
        
        logger.info(f"🛑 Stopping Argus orchestrator for node: {self.node_id}")
        
        # Set running flag to False
        self._running = False
        
        # Stop role-specific components
        if self.leader_orchestrator:
            self.leader_orchestrator.stop()
        if self.follower_worker:
            self.follower_worker.stop()
        
        # Cleanup consensus (abdicate if leader, remove health key)
        self.consensus.cleanup()
        
        # Wait for threads to finish
        for thread_name, thread in [
            ("heartbeat", self._heartbeat_thread),
            ("consensus", self._consensus_thread),
            ("role", self._role_thread)
        ]:
            if thread and thread.is_alive():
                logger.debug(f"⏳ Waiting for {thread_name} thread...")
                thread.join(timeout=5)
        
        logger.info("✅ Orchestrator stopped successfully")
    
    def run_forever(self) -> None:
        """
        Start the orchestrator and run until interrupted.
        Handles graceful shutdown on SIGINT/SIGTERM.
        """
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"\n⚠️  Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the orchestrator
        self.start()
        
        # Keep main thread alive
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt received")
            self.stop()


def main():
    """Main entry point for the Argus system."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Argus - Distributed Leader Election & Auditor System (Refactored)'
    )
    parser.add_argument(
        '--node-id',
        type=str,
        help='Unique node identifier (auto-generated if not provided)'
    )
    parser.add_argument(
        '--ttl',
        type=int,
        default=LEADER_TTL,
        help=f'Leader lease TTL in seconds (default: {LEADER_TTL})'
    )
    parser.add_argument(
        '--heartbeat-interval',
        type=float,
        default=HEARTBEAT_INTERVAL,
        help=f'Heartbeat interval in seconds (default: {HEARTBEAT_INTERVAL})'
    )
    
    args = parser.parse_args()
    
    # Create and run orchestrator
    orchestrator = ArgusOrchestrator(
        node_id=args.node_id,
        ttl=args.ttl,
        heartbeat_interval=args.heartbeat_interval
    )
    
    orchestrator.run_forever()


if __name__ == '__main__':
    main()
