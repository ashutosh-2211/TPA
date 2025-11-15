"""
Test script for the Travel Planning AI Agent

Run this to test the agent's capabilities:
    python test_agent.py
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add services directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from services import chat, get_stored_data, clear_data_store


def print_separator(char="=", length=70):
    """Print a visual separator"""
    print(f"\n{char * length}\n")


def test_agent():
    """Test the AI agent with various queries"""

    print("🤖 Travel Planning AI Agent - Test Suite")
    print_separator()

    # Test queries
    test_cases = [
        {
            "name": "Flight Search",
            "query": "Find me flights from Mumbai to Delhi on 2025-12-15",
            "thread_id": "test_flight"
        },
        {
            "name": "Hotel Search",
            "query": "Search for beach hotels in Bali from 2025-12-20 to 2025-12-25",
            "thread_id": "test_hotel"
        },
        {
            "name": "News Search",
            "query": "What's the latest news about travel to Japan?",
            "thread_id": "test_news"
        },
        {
            "name": "Multi-step Planning",
            "query": "I want to plan a trip from New York to Paris in January. Help me find flights and hotels.",
            "thread_id": "test_multi"
        }
    ]

    for idx, test_case in enumerate(test_cases, 1):
        print(f"TEST {idx}: {test_case['name']}")
        print_separator("-")

        print(f"USER QUERY: {test_case['query']}")
        print()

        try:
            # Call the agent
            result = chat(
                user_message=test_case['query'],
                thread_id=test_case['thread_id']
            )

            # Print the response
            print("AGENT RESPONSE:")
            print(result['response'])
            print()

            # Show data store summary
            print("📊 DATA STORED:")
            data_store = result.get('data_store', {})
            for data_type, stored_data in data_store.items():
                if stored_data:
                    print(f"  ✓ {data_type.upper()}: {len(stored_data)} request(s)")
                    for key in stored_data.keys():
                        print(f"    - Key: {key}")

            print_separator()

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print_separator()
            import traceback
            traceback.print_exc()

        # Ask if user wants to continue
        if idx < len(test_cases):
            response = input("\nPress Enter to continue to next test (or 'q' to quit): ")
            if response.lower() == 'q':
                break

    print("\n✅ Testing completed!")


def interactive_mode():
    """Interactive chat mode with the agent"""

    print("🤖 Travel Planning AI Agent - Interactive Mode")
    print_separator()
    print("Type your queries and press Enter. Type 'quit' to exit.")
    print_separator()

    thread_id = "interactive_session"

    while True:
        try:
            user_input = input("\nYOU: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == 'clear':
                clear_data_store()
                print("🧹 Data store cleared!")
                continue

            # Get agent response
            result = chat(user_message=user_input, thread_id=thread_id)

            print(f"\nAGENT: {result['response']}")

            # Show stored data summary
            data_store = result.get('data_store', {})
            non_empty = {k: v for k, v in data_store.items() if v}
            if non_empty:
                print(f"\n📊 Data available: {', '.join(non_empty.keys())}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""

    print("\nChoose mode:")
    print("1. Run automated tests")
    print("2. Interactive chat mode")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        test_agent()
    elif choice == "2":
        interactive_mode()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
