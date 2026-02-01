#!/usr/bin/env python3
"""Generate minimal sample data for testing purposes."""

import json
import os
from pathlib import Path


SAMPLE_DATA = {
    "clubs": {
        "1001": {"name": "Test Club 1", "logo": ""},
        "1002": {"name": "Test Club 2", "logo": ""},
        "1003": {"name": "Test Club 3", "logo": ""},
    },
    "leagues": {
        "2001": "Test League A",
        "2002": "Test League B",
    },
    "fixtures": {
        "2001": [
            {
                "fixtureID": "101",
                "homeTeamID": "1001",
                "awayTeamID": "1002",
                "compYear": "2026",
                "kickOffTime": "2026-02-01T14:00:00",
                "status": "Scheduled",
            },
            {
                "fixtureID": "102",
                "homeTeamID": "1003",
                "awayTeamID": "1001",
                "compYear": "2026",
                "kickOffTime": "2026-02-15T15:00:00",
                "status": "Scheduled",
            },
        ],
        "2002": [
            {
                "fixtureID": "201",
                "homeTeamID": "1002",
                "awayTeamID": "1003",
                "compYear": "2026",
                "kickOffTime": "2026-03-01T14:00:00",
                "status": "Scheduled",
            },
        ],
    },
    "standings": {
        "2001": [
            {
                "teamID": "1001",
                "teamName": "Test Club 1",
                "played": 2,
                "won": 2,
                "drawn": 0,
                "lost": 0,
                "pointsFor": 40,
                "pointsAgainst": 20,
                "pointsDifference": 20,
                "bonusPoints": 0,
                "points": 10,
                "position": 1,
            },
            {
                "teamID": "1002",
                "teamName": "Test Club 2",
                "played": 2,
                "won": 1,
                "drawn": 0,
                "lost": 1,
                "pointsFor": 30,
                "pointsAgainst": 35,
                "pointsDifference": -5,
                "bonusPoints": 0,
                "points": 5,
                "position": 2,
            },
        ],
        "2002": [
            {
                "teamID": "1002",
                "teamName": "Test Club 2",
                "played": 1,
                "won": 1,
                "drawn": 0,
                "lost": 0,
                "pointsFor": 20,
                "pointsAgainst": 10,
                "pointsDifference": 10,
                "bonusPoints": 0,
                "points": 5,
                "position": 1,
            },
        ],
    },
}

UNIONS = ["ab", "bc", "mb", "nb", "ns", "on", "qc", "sk"]


def generate_sample_data(output_dir: str = "src/data", year: int = 2026) -> None:
    """Generate sample data files for all unions and the specified year."""
    for union in UNIONS:
        union_dir = Path(output_dir) / union / str(year)
        union_dir.mkdir(parents=True, exist_ok=True)

        # Write sample data files
        with open(union_dir / "clubs.json", "w") as f:
            json.dump(SAMPLE_DATA["clubs"], f, indent=2)

        with open(union_dir / "leagues.json", "w") as f:
            json.dump(SAMPLE_DATA["leagues"], f, indent=2)

        with open(union_dir / "fixtures.json", "w") as f:
            json.dump(SAMPLE_DATA["fixtures"], f, indent=2)

        with open(union_dir / "standings.json", "w") as f:
            json.dump(SAMPLE_DATA["standings"], f, indent=2)

        print(f"✅ Generated sample data for {union} {year}")


if __name__ == "__main__":
    generate_sample_data()
