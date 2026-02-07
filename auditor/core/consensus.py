"""
Consensus Engine - Enhanced Leader Election with Fault Tolerance
Implements Redis Lease pattern (King of the Hill) with heartbeat monitoring.
"""
import logging
import time
from typing import Optional
from auditor.infra.redis_client import get_redis_client
from auditor.config import (
    LEADER_KEY,
    NODE_HEALTH_PREFIX,
    HEARTBEAT_COUNTER,
    LEADER_TTL,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_MISS_THRESHOLD,
    NODE_HEALTH_TTL
)

logger = logging.getLogger(__name__)


class ConsensusManager:
    """
    Manages distributed consensus using Redis Lease pattern.
    
    Features:
    - Leader election using SETNX (Set if Not Exists)
    - Heartbeat monitoring with configurable miss threshold
    - Node health tracking with ephemeral keys
    - Automatic failover on leader failure
    """
    
    def __init__(self, node_id: str, ttl: int = LEADER_TTL):
        """
        Initialize the consensus manager.
        
        Args:
            node_id: Unique identifier for this node
            ttl: Time-to-live for leader lease in seconds
        """
        self.node_id = node_id
        self.ttl = ttl
        self._is_leader = False
        self._last_heartbeat = 0
        self._missed_heartbeats = 0
        self.redis_client = get_redis_client()
        
        # Register this node on startup
        self.register_node()
        
        logger.info(f"🗳️  ConsensusManager initialized for node: {self.node_id}")
    
    def attempt_leadership(self) -> bool:
        """
        Attempt to claim or maintain leadership.
        
        Uses Redis SETNX to atomically claim the leader key.
        If already leader, verifies and renews the lease.
        
        Returns:
            bool: True if this node is/became leader, False otherwise
        """
        try:
            # Try to set the leader key with our node_id
            result = self.redis_client.set(
                LEADER_KEY,
                self.node_id,
                nx=True,  # Only set if not exists
                ex=self.ttl  # Set expiry
            )
            
            if result:
                # We just claimed leadership
                if not self._is_leader:
                    self._is_leader = True
                    self._missed_heartbeats = 0
                    logger.info(f"👑 Node {self.node_id} claimed LEADERSHIP")
                return True
            else:
                # Key already exists, check if we're still the leader
                current_leader = self.redis_client.get(LEADER_KEY)
                
                if current_leader == self.node_id:
                    # We're still the leader
                    self._is_leader = True
                    return True
                else:
                    # Someone else is leader
                    if self._is_leader:
                        logger.info(f"👥 Node {self.node_id} lost leadership to {current_leader}")
                    self._is_leader = False
                    return False
        
        except Exception as e:
            logger.error(f"❌ Leadership attempt failed for {self.node_id}: {e}")
            self._is_leader = False
            return False
    
    def heartbeat(self) -> bool:
        """
        Send heartbeat to maintain leadership and node health.
        
        For leaders:
        - Refreshes the leader key TTL
        - Tracks missed heartbeats
        
        For all nodes:
        - Updates node health key with TTL
        - Increments heartbeat counter
        
        Returns:
            bool: True if heartbeat successful, False otherwise
        """
        try:
            current_time = time.time()
            
            # Register node health (all nodes)
            self.register_node()
            
            # Increment heartbeat counter
            self.redis_client.incr(HEARTBEAT_COUNTER)
            
            if self._is_leader:
                # Verify we're still the leader
                current_leader = self.redis_client.get(LEADER_KEY)
                
                if current_leader == self.node_id:
                    # Refresh the TTL
                    self.redis_client.expire(LEADER_KEY, self.ttl)
                    self._missed_heartbeats = 0
                    self._last_heartbeat = current_time
                    
                    active_nodes = self.get_active_node_count()
                    logger.debug(f"💓 Heartbeat sent by leader {self.node_id} (active nodes: {active_nodes})")
                    return True
                else:
                    # We lost leadership
                    logger.warning(f"⚠️  Node {self.node_id} lost leadership during heartbeat")
                    self._is_leader = False
                    self._missed_heartbeats += 1
                    return False
            else:
                # Follower heartbeat
                active_nodes = self.get_active_node_count()
                logger.debug(f"💓 Heartbeat sent by follower {self.node_id} (active nodes: {active_nodes})")
                self._last_heartbeat = current_time
                return True
        
        except Exception as e:
            logger.error(f"❌ Heartbeat failed for {self.node_id}: {e}")
            self._missed_heartbeats += 1
            
            # Check if we've exceeded the threshold
            if self._missed_heartbeats >= HEARTBEAT_MISS_THRESHOLD:
                logger.error(
                    f"💀 Node {self.node_id} exceeded heartbeat miss threshold "
                    f"({self._missed_heartbeats}/{HEARTBEAT_MISS_THRESHOLD})"
                )
                if self._is_leader:
                    self.abdicate()
            
            return False
    
    def register_node(self) -> bool:
        """
        Register this node's health with an ephemeral key.
        
        Sets a key with TTL that expires if the node goes down.
        This allows tracking of active nodes in the cluster.
        
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            node_key = f"{NODE_HEALTH_PREFIX}{self.node_id}"
            self.redis_client.set(
                node_key,
                f"alive:{int(time.time())}",
                ex=NODE_HEALTH_TTL
            )
            logger.debug(f"✅ Node {self.node_id} health registered")
            return True
        
        except Exception as e:
            logger.error(f"❌ Node registration failed for {self.node_id}: {e}")
            return False
    
    def get_active_node_count(self) -> int:
        """
        Get the count of currently active nodes in the cluster.
        
        Counts all node health keys that haven't expired.
        
        Returns:
            int: Number of active nodes
        """
        try:
            # Scan for all node health keys
            pattern = f"{NODE_HEALTH_PREFIX}*"
            keys = list(self.redis_client.scan_iter(match=pattern, count=100))
            count = len(keys)
            
            logger.debug(f"📊 Active node count: {count}")
            return count
        
        except Exception as e:
            logger.error(f"❌ Failed to get active node count: {e}")
            return 0
    
    def abdicate(self) -> bool:
        """
        Gracefully give up leadership.
        
        Deletes the leader key to allow another node to take over.
        Used during shutdown or when stepping down voluntarily.
        
        Returns:
            bool: True if abdication successful, False otherwise
        """
        if not self._is_leader:
            logger.debug(f"ℹ️  Node {self.node_id} is not leader, nothing to abdicate")
            return True
        
        try:
            # Only delete if we're the current leader
            current_leader = self.redis_client.get(LEADER_KEY)
            
            if current_leader == self.node_id:
                self.redis_client.delete(LEADER_KEY)
                logger.info(f"🚪 Node {self.node_id} abdicated leadership")
                self._is_leader = False
                return True
            else:
                logger.warning(f"⚠️  Node {self.node_id} cannot abdicate, not current leader")
                self._is_leader = False
                return False
        
        except Exception as e:
            logger.error(f"❌ Abdication failed for {self.node_id}: {e}")
            return False
    
    def cleanup(self) -> None:
        """
        Cleanup node resources.
        
        Removes node health key and abdicates leadership if leader.
        Should be called on shutdown.
        """
        try:
            # Abdicate if leader
            if self._is_leader:
                self.abdicate()
            
            # Remove node health key
            node_key = f"{NODE_HEALTH_PREFIX}{self.node_id}"
            self.redis_client.delete(node_key)
            
            logger.info(f"🧹 Node {self.node_id} cleanup complete")
        
        except Exception as e:
            logger.error(f"❌ Cleanup failed for {self.node_id}: {e}")
    
    @property
    def is_leader(self) -> bool:
        """
        Check if this node is currently the leader.
        
        Returns:
            bool: True if this node is leader, False otherwise
        """
        return self._is_leader
    
    @property
    def missed_heartbeats(self) -> int:
        """
        Get the number of consecutive missed heartbeats.
        
        Returns:
            int: Number of missed heartbeats
        """
        return self._missed_heartbeats
