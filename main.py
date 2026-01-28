import argparse
import json
import os
from datetime import datetime
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
UNIONS = {
    13329: "BC",
    14160: "NB",
    14156: "AB",
    14158: "MB",
    13986: "NS",
    13555: "ON",
    14159: "QC",
    14157: "SK",
}


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

def extract_teams_from_league_table(clubs: dict, league_table: list[dict]) -> None:
    print(f"🔍 Parsing {len(league_table)} league table entries")

    for entry in league_table:
        team_id = entry.get("team_id")
        club_id = entry.get("club_id")

        if not team_id or not club_id:
            print("⚠️  Skipping entry with missing IDs")
            continue

        club_key = str(club_id)

        # Create the club if it doesn't exist yet
        if club_key not in clubs:
            clubs[club_key] = {
                "name": entry.get("team", "").strip(),
                "logo": entry.get("club_logo", "").strip(),
                "team_ids": [],
            }

        # Add the team_id if we haven't seen it before
        if team_id not in clubs[club_key]["team_ids"]:
            clubs[club_key]["team_ids"].append(team_id)

    print(f"✅ Extracted {len(clubs)} unique clubs")

def normalize_fixture(fixture: dict) -> None:
    if fixture.get("homeScore"):
        fixture["homeScore"] = fixture["homeScore"].split(";")[0]
    else:
        fixture["homeScore"] = "0"

    if fixture.get("awayScore"):
        fixture["awayScore"] = fixture["awayScore"].split(";")[0]
    else:
        fixture["awayScore"] = "0"

    stat_keys = [
        "homeDrop",
        "homePen",
        "homeConv",
        "awayDrop",
        "awayPen",
        "awayConv",
    ]

    for key in stat_keys:
        if fixture.get(key) is None:
            fixture[key] = "0"

    fixture["home"] = {
        "team_id": fixture.get("homeTeamId"),
        "club_id": fixture.get("homeClubId"),
        "score": fixture.get("homeScore", "0"),
        "drop": fixture.get("homeDrop", "0"),
        "pen": fixture.get("homePen", "0"),
        "conv": fixture.get("homeConv", "0"),
        "result": fixture.get("homeResult", ""),
    }

    fixture["away"] = {
        "team_id": fixture.get("awayTeamId"),
        "club_id": fixture.get("awayClubId"),
        "score": fixture.get("awayScore", "0"),
        "drop": fixture.get("awayDrop", "0"),
        "pen": fixture.get("awayPen", "0"),
        "conv": fixture.get("awayConv", "0"),
        "result": fixture.get("awayResult", ""),
    }

    FIXTURE_CLEAN_KEYS = {
        "competitionId", "competitionName", "postponed", "tournamentFixture",
        "sports", "fixtureComment", "competitionShortName", "competitionGroupId",
        "displayWLD", "countyName", "ageid", "ageName", "gender", "round",
        "adminnote", "metaData", "competitioncomment", "competitionDispResults",
        "scoreMetadata", "homeTeam", "awayTeam", "homeClub", "awayClub",
        "homeClubLogo", "awayClubLogo", "homeClubAlternateName",
        "awayClubAlternateName", "homeTeamComment", "homeTeamApproval",
        "awayTeamComment", "awayTeamApproval", "officials", "streaming",

        # Old flat home/away keys (now normalized)
        "homeTeamId", "homeClubId", "homeScore", "homeDrop",
        "homePen", "homeConv", "homeResult",
        "awayTeamId", "awayClubId", "awayScore", "awayDrop",
        "awayPen", "awayConv", "awayResult",
    }

    pop_keys(fixture, FIXTURE_CLEAN_KEYS)

    fixture["matchOfficials"] = normalize_match_officials(
        fixture.get("matchOfficials")
    )


def normalize_match_officials(match_officials):
    normalized = []

    if match_officials is None:
        return normalized

    if not isinstance(match_officials, dict):
        return normalized

    for key in match_officials:
        official = match_officials.get(key)

        if not isinstance(official, dict):
            continue

        role = official.get("role")
        name = official.get("name")

        normalized.append({
            "role": role,
            "name": name,
        })

    return normalized


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

def scrape(user_ids: list[int], target_year: int | None = None) -> None:
    if target_year is None:
        target_year = datetime.now().year
    
    print(f"🚀 Starting scrape for {len(user_ids)} union(s) - Year: {target_year}")

    for user_id in user_ids:
        union_code = UNIONS.get(user_id, "UNKNOWN").lower()
        output_dir = os.path.join("data", union_code, str(target_year))
        os.makedirs(output_dir, exist_ok=True)

        leagues: dict = {}
        clubs: dict = {}
        fixtures: dict = {}
        standings: dict = {}

        TABLE_CLEAN_KEYS = {
            "club_logo", "team", "goalsFor", "goalsAgainst", "goalsDifference",
            "bonusPointsM", "teamDeduction", "setQuotient", "scoresFor",
            "scoresAgainst", "scoredraw", "scorelessdraw", "scoreRatio",
            "3-0", "3-1", "3-2", "2-3", "1-3", "0-3", "gamesBehind",
            "fpp", "fieldingpoints", "inningsbatted", "inningsfielded", "runrate",
        }

        season_id = fetch_active_season(user_id)
        if not season_id:
            raise RuntimeError("❌ No active season found")
    
        competitions = fetch_competitions(user_id, season_id)
        for comp in competitions:
            league_id = comp.get("fixtureid")
            league_name = comp.get("name")

            if not league_id or not league_name:
                continue

            print(f"  📊 Fetching {league_name} ({league_id})")

            leagues[league_id] = league_name.strip()
            league_data = fetch_league_table(league_id)

            extract_teams_from_league_table(clubs, league_data["leagueTable"])

            for fixture in league_data["fixtures"]:
                normalize_fixture(fixture)

            for row in league_data["leagueTable"]:
                pop_keys(row, TABLE_CLEAN_KEYS)
            
            fixtures[league_id] = [
                f for f in league_data["fixtures"]
                if str(f.get("compYear")) == str(target_year)
            ]
            standings[league_id] = league_data["leagueTable"]


        dump_json(os.path.join(output_dir, "leagues.json"), leagues)
        dump_json(os.path.join(output_dir, "clubs.json"), clubs)
        dump_json(os.path.join(output_dir, "fixtures.json"), fixtures)
        dump_json(os.path.join(output_dir, "standings.json"), standings)

        print(f"✅ Data saved to {output_dir}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape rugby union data")
    parser.add_argument(
        "--unions",
        nargs="+",
        type=str,
        help="Union codes to scrape (e.g., BC QC AB or ALL)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Competition year to filter fixtures (default: current year)",
    )
    args = parser.parse_args()

    # Require --unions argument
    if not args.unions:
        print("❌ Please specify union codes with --unions (e.g., --unions BC QC AB or --unions ALL)")
        exit(1)

    # Convert union codes to IDs
    code_to_id = {v: k for k, v in UNIONS.items()}
    user_ids = []
    
    # Handle --unions ALL
    if len(args.unions) == 1 and args.unions[0].upper() == "ALL":
        user_ids = list(UNIONS.keys())
    else:
        for code in args.unions:
            if code.upper() in code_to_id:
                user_ids.append(code_to_id[code.upper()])
            else:
                print(f"⚠️  Unknown union code: {code}")
    
    if not user_ids:
        print("❌ No valid union codes provided")
        exit(1)

    scrape(user_ids=user_ids, target_year=args.year)


if __name__ == "__main__":
    main()
