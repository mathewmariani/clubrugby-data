import argparse
import json
import os
from typing import Iterable

import requests


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://diffusion.rseq.ca",
    "Referer": "https://diffusion.rseq.ca/",
}


# Rugby unions
# 13329 : BC
# 14160 : NB
# 14156 : AB
# 14158 : MB
# 13986 : NS
# 13555 : ON
# 14159 : QC
# 14157 : SK


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_json(params: dict) -> dict:
    """Perform a GET request and return parsed JSON."""
    response = requests.get(API_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def pop_keys(obj: dict, keys: Iterable[str]) -> None:
    """Remove a list of keys from a dict if present."""
    for key in keys:
        obj.pop(key, None)


def dump_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def extract_teams_from_league_table(league_table: list[dict]) -> dict:
    teams = {}

    print(f"🔍 Parsing {len(league_table)} league table entries")

    for entry in league_table:
        team_id = entry.get("team_id")
        club_id = entry.get("club_id")

        if not team_id or not club_id:
            print("⚠️  Skipping entry with missing IDs")
            continue

        teams[str(club_id)] = {
            "name": entry.get("team", "").strip(),
            "logo": entry.get("club_logo", "").strip(),
        }

    print(f"✅ Extracted {len(teams)} unique clubs")
    return teams


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_active_season(user_id: int) -> str | None:
    data = get_json({
        "feedType": "competitions",
        "user_id": user_id,
        "type": "groups",
    })

    years = (
        data.get("settings", {})
            .get("season", {})
            .get(str(user_id), {})
            .get("year", [])
    )

    print(f"📅 Found {len(years)} seasons")

    for season in years:
        if season.get("active") == "yes":
            print(f"⭐ Active season: {season.get('seasonid')}")
            return season.get("seasonid")

    return None


def fetch_competitions(user_id: int, season_id: int) -> list[dict]:
    data = get_json({
        "feedType": "competitions",
        "type": "competitions",
        "user_id": user_id,
        "seasonid": season_id,
    })

    competitions = data["data"].get(str(user_id), [])

    CLEAN_KEYS = {
        "shortname", "compLogo", "Description", "groupid", "seasonid",
        "type", "gender", "displayStats", "organisationType",
        "competitionLevel", "teamType", "comment", "sportid", "sport",
    }

    for comp in competitions:
        pop_keys(comp, CLEAN_KEYS)

    print(f"🏆 Loaded {len(competitions)} competitions")
    return competitions


def fetch_league_table(competition_id: int) -> dict:
    data = get_json({
        "feedType": "fixture",
        "competition_id": competition_id,
        "type": "league_table",
    })

    data.pop("settings", None)
    pop_keys(data["data"], {"liveLeagueTable", "pendingTeams"})

    return data["data"]


# ---------------------------------------------------------------------------
# Main scrape
# ---------------------------------------------------------------------------

def scrape(output_dir: str = ".", user_id: int = 14159) -> None:
    print("🚀 Starting scrape")
    os.makedirs(output_dir, exist_ok=True)

    leagues: dict = {}
    clubs: dict = {}
    fixtures: dict = {}
    standings: dict = {}

    season_id = fetch_active_season(user_id)
    if not season_id:
        raise RuntimeError("❌ No active season found")

    competitions = fetch_competitions(user_id, season_id)

    FIXTURE_CLEAN_KEYS = {
        "competitionId", "competitionName", "postponed", "tournamentFixture",
        "sports", "fixtureComment", "competitionShortName", "competitionGroupId",
        "displayWLD", "countyName", "ageid", "ageName", "gender", "round",
        "adminnote", "metaData", "competitioncomment", "competitionDispResults",
        "scoreMetadata", "homeTeam", "awayTeam", "homeClub", "awayClub",
        "homeClubLogo", "awayClubLogo", "homeClubAlternateName",
        "awayClubAlternateName", "homeTeamComment", "homeTeamApproval",
        "awayTeamComment", "awayTeamApproval", "officials", "streaming",
    }

    TABLE_CLEAN_KEYS = {
        "club_logo", "team", "goalsFor", "goalsAgainst", "goalsDifference",
        "bonusPointsM", "teamDeduction", "setQuotient", "scoresFor",
        "scoresAgainst", "scoredraw", "scorelessdraw", "scoreRatio",
        "3-0", "3-1", "3-2", "2-3", "1-3", "0-3", "gamesBehind",
        "fpp", "fieldingpoints", "inningsbatted", "inningsfielded", "runrate",
    }

    for comp in competitions:
        league_id = comp.get("fixtureid")
        league_name = comp.get("name")

        if not league_id or not league_name:
            continue

        print(f"📊 Fetching {league_name} ({league_id})")

        leagues[league_id] = league_name.strip()
        league_data = fetch_league_table(league_id)

        clubs |= extract_teams_from_league_table(league_data["leagueTable"])

        for fixture in league_data["fixtures"]:
            pop_keys(fixture, FIXTURE_CLEAN_KEYS)

        for row in league_data["leagueTable"]:
            pop_keys(row, TABLE_CLEAN_KEYS)

        fixtures[league_id] = league_data["fixtures"]
        standings[league_id] = league_data["leagueTable"]

    dump_json(os.path.join(output_dir, "leagues.json"), leagues)
    dump_json(os.path.join(output_dir, "clubs.json"), clubs)
    dump_json(os.path.join(output_dir, "fixtures.json"), fixtures)
    dump_json(os.path.join(output_dir, "standings.json"), standings)

    print("🎉 All data saved as beautified JSON")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".", help="Output directory")
    args = parser.parse_args()

    scrape(output_dir=args.output)
