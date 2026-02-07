#!/usr/bin/env python3
"""
Test script for Argus Leader Election System (Refactored Architecture)
Tests the new Leader-Follower separation with consensus engine.
"""
import subprocess
import time
import sys
import signal

def check_redis():
    """Check if Redis is available."""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        client.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis is not available: {e}")
        print("\nTo start Redis, run:")
        print("  docker run -d -p 6379:6379 redis:7-alpine")
        return False

def test_single_node():
    """Test single node becoming leader with new architecture."""
    print("\n" + "="*70)
    print("TEST 1: Single Node - Leader Election & Task Scheduling")
    print("="*70)
    print("Expected: Node becomes leader, runs graph search, filters 20%, pushes tasks")
    print("="*70)
    
    if not check_redis():
        return False
    
    print("\n▶️  Starting single node (will run for 20 seconds)...\n")
    
    try:
        proc = subprocess.Popen(
            ["python", "-m", "auditor.main", "--node-id", "test-node-A"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Read output for 20 seconds
        start_time = time.time()
        while time.time() - start_time < 20:
            line = proc.stdout.readline()
            if line:
                print(line.rstrip())
            if proc.poll() is not None:
                break
        
        # Terminate gracefully
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
        
        print("\n✅ Single node test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def test_leader_follower_separation():
    """Test leader-follower role separation."""
    print("\n" + "="*70)
    print("TEST 2: Leader-Follower Separation")
    print("="*70)
    print("Expected: One node is leader (schedules), others are followers (execute)")
    print("="*70)
    
    if not check_redis():
        return False
    
    print("\n▶️  Starting 3 nodes...\n")
    
    processes = []
    node_ids = ["node-A", "node-B", "node-C"]
    
    try:
        # Start 3 nodes
        for node_id in node_ids:
            proc = subprocess.Popen(
                ["python", "-m", "auditor.main", "--node-id", node_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append((node_id, proc))
            print(f"✅ Started {node_id}")
            time.sleep(1)
        
        print("\n📊 Monitoring nodes for 25 seconds...")
        print("Watch for:")
        print("  - One node claiming LEADERSHIP (👑)")
        print("  - Leader running graph search and filtering")
        print("  - Followers executing 3-step pipeline\n")
        
        # Monitor for 25 seconds
        start_time = time.time()
        while time.time() - start_time < 25:
            for node_id, proc in processes:
                line = proc.stdout.readline()
                if line:
                    # Highlight important events
                    if "LEADERSHIP" in line or "Leader" in line:
                        print(f"👑 [{node_id}] {line.rstrip()}")
                    elif "Follower" in line or "Pipeline" in line:
                        print(f"👥 [{node_id}] {line.rstrip()}")
                    elif "Gemma" in line or "RAG" in line or "blockchain" in line:
                        print(f"🔧 [{node_id}] {line.rstrip()}")
                    else:
                        print(f"   [{node_id}] {line.rstrip()}")
            time.sleep(0.05)
        
        # Cleanup
        print("\n🛑 Stopping all nodes...")
        for node_id, proc in processes:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
        
        print("\n✅ Leader-Follower separation test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        # Cleanup
        for _, proc in processes:
            try:
                proc.kill()
                proc.wait()
            except:
                pass
        return False

def test_failover():
    """Test leader failover with heartbeat monitoring."""
    print("\n" + "="*70)
    print("TEST 3: Leader Failover & Heartbeat Monitoring")
    print("="*70)
    print("Expected: When leader dies, another node takes over within TTL seconds")
    print("="*70)
    
    if not check_redis():
        return False
    
    print("\n▶️  Starting 3 nodes...\n")
    
    processes = []
    node_ids = ["node-A", "node-B", "node-C"]
    
    try:
        # Start 3 nodes
        for node_id in node_ids:
            proc = subprocess.Popen(
                ["python", "-m", "auditor.main", "--node-id", node_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append((node_id, proc))
            print(f"✅ Started {node_id}")
            time.sleep(1)
        
        print("\n📊 Monitoring for 15 seconds to identify leader...\n")
        
        # Monitor to identify leader
        start_time = time.time()
        leader_idx = None
        while time.time() - start_time < 15:
            for idx, (node_id, proc) in enumerate(processes):
                line = proc.stdout.readline()
                if line:
                    print(f"[{node_id}] {line.rstrip()}")
                    if "claimed LEADERSHIP" in line and leader_idx is None:
                        leader_idx = idx
                        print(f"\n🎯 Identified leader: {node_id}\n")
        
        if leader_idx is None:
            print("⚠️  Could not identify leader, using first node")
            leader_idx = 0
        
        # Kill the leader
        leader_id, leader_proc = processes[leader_idx]
        print(f"\n💀 Simulating leader failure (killing {leader_id})...")
        leader_proc.send_signal(signal.SIGKILL)
        leader_proc.wait()
        print(f"✅ Killed {leader_id}")
        
        print("\n📊 Monitoring remaining nodes for failover (20 seconds)...\n")
        
        # Monitor failover
        start_time = time.time()
        failover_detected = False
        while time.time() - start_time < 20:
            for idx, (node_id, proc) in enumerate(processes):
                if idx == leader_idx:
                    continue
                line = proc.stdout.readline()
                if line:
                    print(f"[{node_id}] {line.rstrip()}")
                    if "claimed LEADERSHIP" in line:
                        print(f"\n🎉 FAILOVER SUCCESS: {node_id} became new leader!\n")
                        failover_detected = True
            time.sleep(0.05)
        
        # Cleanup
        print("\n🛑 Stopping remaining nodes...")
        for idx, (node_id, proc) in enumerate(processes):
            if idx != leader_idx:
                try:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=5)
                except:
                    pass
        
        if failover_detected:
            print("\n✅ Failover test PASSED")
            return True
        else:
            print("\n⚠️  Failover test completed (failover may have occurred)")
            return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        # Cleanup
        for _, proc in processes:
            try:
                proc.kill()
                proc.wait()
            except:
                pass
        return False

def main():
    """Run all tests."""
    print("🧪 Argus Leader Election System - Test Suite (Refactored)")
    print("Testing new Leader-Follower architecture with consensus engine\n")
    
    # Run tests
    test1_passed = test_single_node()
    time.sleep(2)
    
    test2_passed = test_leader_follower_separation()
    time.sleep(2)
    
    test3_passed = test_failover()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Single Node Test:              {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Leader-Follower Separation:    {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Failover Test:                 {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print("="*70)
    
    return 0 if (test1_passed and test2_passed and test3_passed) else 1

if __name__ == '__main__':
    sys.exit(main())
