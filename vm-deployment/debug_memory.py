#!/usr/bin/env python3
import sys
sys.path.append('/Users/fredtaylor/Desktop/Projects/ai-tools/vm-deployment')

from collaborative_ai_system import CollaborativeAISystem

def test_memory_search():
    # Create system
    ai_system = CollaborativeAISystem()
    
    # Store a test memory
    ai_system.memory.store_memory("Test maintenance procedure", "maintenance", "test_system")
    
    print("Testing single word query...")
    try:
        result = ai_system.memory.retrieve_relevant_memories("test", None, 2)
        print(f"Success: Found {len(result)} memories")
        for mem in result:
            print(f"  - {mem.content[:50]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTesting with category...")
    try:
        result = ai_system.memory.retrieve_relevant_memories("maintenance", "maintenance", 2)
        print(f"Success: Found {len(result)} memories")
        for mem in result:
            print(f"  - {mem.content[:50]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_memory_search()