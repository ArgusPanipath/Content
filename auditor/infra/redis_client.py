"""
Redis Client Singleton for Argus Leader Election System
Provides connection management with retry logic and key constants.
"""
import redis
import logging
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis Key Constants
LEADER_KEY = "argus:leader"
TASK_QUEUE = "argus:tasks"


class RedisClient:
    """Singleton Redis connection manager with retry logic."""
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        max_retries: int = 5,
        retry_delay: int = 2
    ):
        """
        Initialize Redis client with connection parameters.
        
        Args:
            host: Redis host address
            port: Redis port number
            db: Redis database number
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        if not hasattr(self, '_initialized'):
            self.host = host
            self.port = port
            self.db = db
            self.max_retries = max_retries
            self.retry_delay = retry_delay
            self._initialized = True
            self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Redis with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                # Test connection
                self._client.ping()
                logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
                return
            except redis.ConnectionError as e:
                logger.warning(
                    f"⚠️  Redis connection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("❌ Failed to connect to Redis after all retries")
                    raise
    
    def get_client(self) -> redis.Redis:
        """
        Get the Redis client instance.
        
        Returns:
            redis.Redis: Active Redis client
            
        Raises:
            redis.ConnectionError: If client is not connected
        """
        if self._client is None:
            raise redis.ConnectionError("Redis client not initialized")
        
        try:
            self._client.ping()
        except redis.ConnectionError:
            logger.warning("🔄 Redis connection lost, attempting to reconnect...")
            self._connect()
        
        return self._client
    
    def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            self._client.close()
            logger.info("🔌 Redis connection closed")


# Convenience function to get Redis client
def get_redis_client() -> redis.Redis:
    """Get the singleton Redis client instance."""
    return RedisClient().get_client()
