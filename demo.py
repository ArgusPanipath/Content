#!/usr/bin/env python3
"""
Quick demo script to show Argus in action.
Starts Redis if needed and runs a single node.
"""
import subprocess
import sys
import time

def start_redis():
    """Try to start Redis using Docker."""
    print("🔄 Attempting to start Redis...")
    try:
        # Try to start Redis container
        result = subprocess.run(
            ["docker", "run", "-d", "--name", "argus-redis-demo", "-p", "6379:6379", "redis:7-alpine"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Redis started successfully")
            time.sleep(2)
            return True
        else:
            # Container might already exist
            print("ℹ️  Redis container may already exist, trying to start it...")
            subprocess.run(["docker", "start", "argus-redis-demo"], capture_output=True)
            time.sleep(2)
            return True
    except Exception as e:
        print(f"⚠️  Could not start Redis: {e}")
        print("Please ensure Redis is running manually:")
        print("  docker run -d -p 6379:6379 redis:7-alpine")
        return False

def check_redis():
    """Check if Redis is accessible."""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        client.ping()
        return True
    except:
        return False

def main():
    """Run the demo."""
    print("🚀 Argus Leader Election System - Quick Demo\n")
    
    # Check Redis
    if not check_redis():
        print("❌ Redis is not running")
        if not start_redis():
            return 1
        if not check_redis():
            print("❌ Still cannot connect to Redis")
            return 1
    else:
        print("✅ Redis is running\n")
    
    print("▶️  Starting Argus node...")
    print("Press Ctrl+C to stop\n")
    print("-" * 60)
    
    try:
        subprocess.run([
            "python", "-m", "auditor.main",
            "--node-id", "demo-node",
            "--ttl", "5",
            "--scheduling-interval", "10"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Demo stopped")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
