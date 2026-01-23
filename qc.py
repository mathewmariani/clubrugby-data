import requests
import os
import json
import argparse

# rugby unions
# 13329 : "BC"
# 14160 : "NB"
# 14156 : "AB"
# 14158 : "MB"
# 13986 : "NS"
# 13555 : "ON"
# 14159 : "QC"
# 14157 : "SK"

def extract_teams_from_league_table(league_table: dict, debug: bool = False) -> dict:
    teams = {}

    if debug:
        print(f"Found {len(league_table)} entries in leagueTable")

    for entry in league_table:
        team_id = entry.get("team_id")
        club_id = entry.get("club_id")
        club_logo = entry.get("club_logo", "")
        team_name = entry.get("team", "")

        if not team_id or not club_id:
            if debug:
                print(f"Skipping entry due to missing ID: {entry}")
            continue

        team_id = str(team_id)
        club_id = str(club_id)

        teams[club_id] = {
            "name": team_name.strip(),
            "logo": club_logo.strip(),
        }

    if debug:
        print(f"Extracted {len(teams)} unique teams")

    return teams

def fetch_active_season(user_id: int) -> str | None:
    url = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://diffusion.rseq.ca",
        "Referer": "https://diffusion.rseq.ca/",
    }

    params = {
        "feedType": "competitions",
        "user_id": user_id,
        "type": "groups",
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    years = (
        data
        .get("settings", {})
        .get("season", {})
        .get(str(user_id), {})
        .get("year", [])
    )

    print(f"Found {len(years)} seasons")

    for season in years:
        if season.get("active") == "yes":
            return season.get("seasonid")

    return None

def fetch_league_table(competition_id: int) -> dict:
    url = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://diffusion.rseq.ca",
        "Referer": "https://diffusion.rseq.ca/",
    }

    params = {
        "feedType": "fixture",
        "competition_id": competition_id,
        "type": "league_table",
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    data.pop("settings", None)
    data["data"].pop("liveLeagueTable", None)
    data["data"].pop("pendingTeams", None)

    return data["data"]

def fetch_competitions(user_id: int, season_id: int) -> dict:
    url = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://diffusion.rseq.ca",
        "Referer": "https://diffusion.rseq.ca/",
    }

    params = {
        "feedType": "competitions",
        "type": "competitions",
        "user_id": user_id,
        "seasonid": season_id,
    }

    response = requests.get(url, params=params, headers=headers)

    response.raise_for_status()
    data = response.json()

    for competition in data["data"][f"{user_id}"]:
        competition.pop("shortname", None)
        competition.pop("compLogo", None)
        competition.pop("Description", None)
        competition.pop("groupid", None)
        competition.pop("seasonid", None)
        competition.pop("type", None)
        competition.pop("gender", None)
        competition.pop("displayStats", None)
        competition.pop("organisationType", None)
        competition.pop("competitionLevel", None)
        competition.pop("teamType", None)
        competition.pop("comment", None)
        competition.pop("sportid", None)
        competition.pop("sport", None)

    return data["data"].get(str(user_id), [])

def scrape(output_dir: str = ".", user_id: int = 14159) -> None:
    url = "https://rugbycanada.sportsmanager.ie/dataFeed/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://diffusion.rseq.ca",
        "Referer": "https://diffusion.rseq.ca/",
    }

    leagues = {}
    clubs = {}
    standings = {}
    fixtures = {}

    os.makedirs(output_dir, exist_ok=True)

    season_id = fetch_active_season(user_id=user_id)

    if not season_id:
        raise RuntimeError("No active season found")

    print("Active season ID:", season_id)

    # next we will call
    # feedType=competitions&user_id=14159&type=competitions&seasonid=3839

    competitions = fetch_competitions(user_id=user_id, season_id=season_id)
    for comp in competitions:
        league_id = comp.get("fixtureid")
        league_name = comp.get("name")

        if not league_id or not league_name:
            continue

        print(f"Fetching {league_name} ({league_id})...")

        leagues[league_id] = league_name.strip()
        league_table = fetch_league_table(competition_id=league_id)
        clubs = clubs | extract_teams_from_league_table(league_table["leagueTable"], debug=True)

        # clear existing data
        for fixture in league_table["fixtures"]:
            fixture.pop("competitionId", None)
            fixture.pop("competitionName", None)
            fixture.pop("postponed", None)
            fixture.pop("tournamentFixture", None)
            fixture.pop("sports", None)
            fixture.pop("fixtureComment", None)
            fixture.pop("competitionShortName", None)
            fixture.pop("competitionGroupId", None)
            fixture.pop("displayWLD", None)
            fixture.pop("countyName", None)
            fixture.pop("ageid", None)
            fixture.pop("ageName", None)
            fixture.pop("gender", None)
            fixture.pop("round", None)
            fixture.pop("adminnote", None)
            fixture.pop("metaData", None)
            fixture.pop("competitioncomment", None)
            fixture.pop("competitionDispResults", None)
            fixture.pop("scoreMetadata", None)
            fixture.pop("homeTeam", None)
            fixture.pop("awayTeam", None)
            fixture.pop("homeClub", None)
            fixture.pop("awayClub", None)
            fixture.pop("homeClubLogo", None)
            fixture.pop("awayClubLogo", None)
            fixture.pop("homeClubAlternateName", None)
            fixture.pop("awayClubAlternateName", None)
            fixture.pop("homeTeamComment", None)
            fixture.pop("homeTeamApproval", None)
            fixture.pop("awayTeamComment", None)
            fixture.pop("awayTeamApproval", None)
            fixture.pop("officials", None)
            fixture.pop("streaming", None)

        for table in league_table["leagueTable"]:
            table.pop("club_logo", None)
            table.pop("team", None)
            table.pop("goalsFor", None)
            table.pop("goalsAgainst", None)
            table.pop("goalsDifference", None)
            table.pop("bonusPointsM", None)
            table.pop("teamDeduction", None)
            table.pop("setQuotient", None)
            table.pop("scoresFor", None)
            table.pop("scoresAgainst", None)
            table.pop("scoredraw", None)
            table.pop("scorelessdraw", None)
            table.pop("scoreRatio", None)
            table.pop("3-0", None)
            table.pop("3-1", None)
            table.pop("3-2", None)
            table.pop("2-3", None)
            table.pop("1-3", None)
            table.pop("0-3", None)
            table.pop("gamesBehind", None)
            table.pop("fpp", None)
            table.pop("fieldingpoints", None)
            table.pop("inningsbatted", None)
            table.pop("inningsfielded", None)
            table.pop("runrate", None)

        fixtures[league_id] = league_table["fixtures"]
        standings[league_id] = league_table["leagueTable"]  
        
    with open(os.path.join(output_dir, f"leagues.json"), "w", encoding="utf-8") as f:
        json.dump(leagues, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, f"clubs.json"), "w", encoding="utf-8") as f:
        json.dump(clubs, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, f"fixtures.json"), "w", encoding="utf-8") as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, f"standings.json"), "w", encoding="utf-8") as f:
        json.dump(standings, f, ensure_ascii=False, indent=2)

    print("\nAll data saved as beautified JSON")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Save beautified raw responses")
    args = parser.parse_args()

    scrape(output_dir=args.output)
