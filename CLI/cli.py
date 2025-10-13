import os
import json
import pandas as pd
import requests
import time
from tabulate import tabulate  # pip install tabulate

API_URL = os.getenv("API_URL", "http://localhost:8000/query")

def wait_for_api(timeout=60):
    """Wait for the API to become available."""
    start_time = time.time()
    while True:
        try:
            r = requests.get(API_URL.replace("/query", "/health"))
            if r.status_code == 200:
                print("API is ready!")
                break
        except requests.exceptions.ConnectionError:
            pass

        if time.time() - start_time > timeout:
            print("Timed out waiting for API.")
            break
        print("Waiting for API to start...")
        time.sleep(2)


def send_query_to_api(question: str) -> pd.DataFrame:
    """Send query to FastAPI and return results as a DataFrame (no prints)."""
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    payload = {"question": question}

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        if response.status_code == 200:
            result = response.json()
            rows = result.get("results", [])
            if rows:
                return pd.DataFrame(rows)
            return pd.DataFrame()
        else:
            print(f"Server error: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return pd.DataFrame()


def ai_data_assist_cli():
    print("=" * 45)
    print("Welcome to AI Data Assist (CLI Mode)")
    print("=" * 45)

    wait_for_api()

    while True:
        print("\nOptions:")
        print("1. Query the Database")
        print("2. Exit")

        choice = input("\nEnter your choice (1/2): ").strip()

        if choice == "1":
            question = input("\nEnter your question: ").strip()
            if not question:
                print("Please enter a valid question.")
                continue

            print(f"\n[→ Sending query: '{question}']\n")
            df = send_query_to_api(question)

            print("Response:")
            print("-" * 45)
            if not df.empty:
                print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
            else:
                print("No data returned.")
            print("-" * 45)

        elif choice == "2":
            confirm = input("\nExit? (y/n): ").strip().lower()
            if confirm == "y":
                print("\nExiting AI Data Assist. Goodbye!\n")
                break
            else:
                print("\nReturning to main menu...")

        else:
            print("\nInvalid option. Please enter 1 or 2.")


if __name__ == "__main__":
    ai_data_assist_cli()
