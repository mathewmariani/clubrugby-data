import requests
import os
import json
import argparse
from datetime import datetime
from requests.exceptions import RequestException


def scrape(output_dir: str = ".", debug: bool = False) -> None:
    url = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://diffusion.rseq.ca",
        "Referer": "https://diffusion.rseq.ca/",
    }

    os.makedirs(output_dir, exist_ok=True)


    # feedType=competitions&type=competitions&user_id=14159
    params = {
        # "feedType": "competitions",
        # "type": "competitions",

        "feedType": "fixture",
        "type": "league_table",
        "competition_id": 204705,
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15,
        )

        print(f"[INFO] Request URL: {response.url}")
        print(f"[INFO] Status Code: {response.status_code}")

        # Raise HTTP errors (4xx / 5xx)
        response.raise_for_status()

    except RequestException as e:
        print("\n[ERROR] Request failed")
        print(str(e))
        return

    # Try parsing JSON
    try:
        data = response.json()
    except json.JSONDecodeError:
        print("\n[ERROR] Response is not valid JSON")
        print("Raw response (first 1000 chars):")
        print(response.text)
        return

    # Optional debug dump
    if debug:
        print("\n[DEBUG] Response headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")

        print("\n[DEBUG] JSON keys at root:")
        if isinstance(data, dict):
            print(list(data.keys()))
        else:
            print(type(data))

    # Save JSON
    output_path = os.path.join(output_dir, "clubs_14159.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Data saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Verbose output")
    args = parser.parse_args()

    scrape(output_dir=args.output, debug=args.debug)
