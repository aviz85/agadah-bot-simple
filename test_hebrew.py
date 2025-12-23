#!/usr/bin/env python3
"""
Quick test script for Hebrew input
"""
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import crew
from app.crew import create_activity_crew

def test_hebrew_input():
    """Test with simple Hebrew input"""

    # Simple Hebrew input
    user_input = "פעילות על אהבת חינם לחטיבה, 40 דקות"

    print("=" * 60)
    print("Testing agadah-bot with Hebrew input")
    print("=" * 60)
    print(f"\nInput: {user_input}\n")
    print("Creating crew...")

    try:
        # Create crew
        crew = create_activity_crew()
        print("✓ Crew created successfully")

        print("\nStarting activity generation...")
        print("(This may take 2-3 minutes)\n")

        # Run crew
        result = crew.kickoff(inputs={"user_input": user_input})

        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(result)
        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_hebrew_input()
