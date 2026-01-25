import argparse
import json
import os

import requests


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = "https://s1.rseq.ca/api/LeagueApi/GetLeagueDiffusion/"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "https://diffusion.rseq.ca",
    "Referer": "https://diffusion.rseq.ca/",
}

LEAGUES = {
    "Collégial Masculin Sud-Ouest": "77390fac-c162-47e4-9f91-b4bf5151b938",
    "Collégial Masculin Nord-Est": "a7e8232c-9d47-49cc-b578-1482d0f34bce",
    "Collégial Féminin Sud-Ouest": "a87e9fe1-3972-42eb-be01-b19f1304c3b4",
    "Collégial Féminin Nord-Est QCA": "12a14f6f-5e2d-442f-9b32-e53df70980bb",
    "Collégial Féminin Nord-Est QC": "c705d49e-e082-4922-98e1-9a636e9fd391",
    "Universitaire Masculin": "c80803ae-8c87-4619-8d76-3eda0fdf2d27",
    "Universitaire Féminin": "f675b71f-ef1a-4dc5-ba09-0e378be48975",
}

TEAM_ID_MAP = {
    # cegep
    "01c83f3e-efe3-4d3b-8864-5f79ac764329": "e4a5282d-4093-4c43-98ef-103912518fc9",
    "28daff3d-3fbc-4f00-9092-f87940c4232d": "22c1dc92-c684-4528-ac31-154ff5d0daaa",
    "d6627ecd-a2c7-4eb2-9255-1a2c9ea73840": "e635ab97-3ddf-47c6-8b1b-10aa0eb30679",
    "897495b8-1451-4510-8ce4-6038228aedca": "8d0be92f-fbe0-454b-a35f-a366282ecade",

    # university
    "78a948a7-5eed-4f98-ba32-1b73ba2b3e91": "a1044ae6-abd9-49db-9e69-9e94617cb64f",
    "2ecc0d44-bbe0-4b8f-84e3-777f76ccacfb": "990077e5-e3ef-49b3-82aa-dc1fea75388a",
    "7effe149-5b71-4664-bade-6f91c5516c74": "e539f8b7-945a-4a92-9e71-390c704b0571",
    "effba245-ab6c-4f22-9897-c32c8a2cd59f": "25a57eba-fc38-4481-9438-5e49fcb2c161",
    "559d4c83-3b88-489f-a343-62e84f44a5df": "7ee0ec36-4447-4803-83ef-822f3e32d7d0",
    "b4d1de6c-3279-4c62-979d-9b5eb47ebd40": "fc7a0121-93db-4711-8366-e8ac903a0986",
}

TEAM_LOGO_MAP = {
    # cegep_m_sud_ouest
    "01c83f3e-efe3-4d3b-8864-5f79ac764329": "https://rseq.ca/ImageGen.ashx?image=/media/24420/1.jpg&width=58&height=58&pad=true&constrain=true",
    "28daff3d-3fbc-4f00-9092-f87940c4232d": "https://rseq.ca/ImageGen.ashx?image=/media/2536015/2022-2023_dawson_blues-logo-full-color-rgb.jpg&width=58&height=58&pad=true&constrain=true",
    "6aacdf88-aad8-4e59-a052-1bb3ca919973": "https://rseq.ca/ImageGen.ashx?image=/media/463331/microsoftteams-image.png&width=58&height=58&pad=true&constrain=true",
    "d6627ecd-a2c7-4eb2-9255-1a2c9ea73840": "https://rseq.ca/ImageGen.ashx?image=/media/24490/john_abbott.jpg&width=58&height=58&pad=true&constrain=true",
    "897495b8-1451-4510-8ce4-6038228aedca": "https://rseq.ca/ImageGen.ashx?image=/media/24630/vaniercheetahsrgblrg__2_.gif&width=58&height=58&pad=true&constrain=true",

    # cegep_m_nord_est
    "b4f9a25c-b6e3-4529-94b0-e4bafc4d9686": "https://rseq.ca/ImageGen.ashx?image=/media/2703294/logo_trappeurs_avec_mention_c_gep.png&width=58&height=58&pad=true&constrain=true",
    "fa2f2d1e-bf65-4179-8e4e-959f0c2ffa42": "https://rseq.ca/ImageGen.ashx?image=/media/24465/francois_xavier_garneau-seul.jpg&width=58&height=58&pad=true&constrain=true",
    "478f9c84-0ce1-4d2f-a6fa-2b9163152a63": "https://rseq.ca/ImageGen.ashx?image=/media/2912206/cl_titans_sans_e_noirrouge_cmyk.png&width=58&height=58&pad=true&constrain=true",
    "07856c1b-26b9-447b-83e5-938cecd3673b": "https://rseq.ca/ImageGen.ashx?image=/media/347235/nd-condensee-neg.jpg&width=58&height=58&pad=true&constrain=true",
    "658fb115-60f3-4b9d-8d25-25852aec61a0": "https://rseq.ca/ImageGen.ashx?image=/media/24590/csf-logo_dynamiques_cmyk.jpg&width=58&height=58&pad=true&constrain=true",
    "0b1a8430-d0d4-47b7-afcb-ba99d4818cb8": "https://rseq.ca/ImageGen.ashx?image=/media/2539895/logo_vulkins_couleur.png&width=58&height=58&pad=true&constrain=true",
    
    # cegep_f_sud_ouest
    "e4a5282d-4093-4c43-98ef-103912518fc9": "https://rseq.ca/ImageGen.ashx?image=/media/24420/1.jpg&width=58&height=58&pad=true&constrain=true",
    "22c1dc92-c684-4528-ac31-154ff5d0daaa": "https://rseq.ca/ImageGen.ashx?image=/media/2536015/2022-2023_dawson_blues-logo-full-color-rgb.jpg&width=58&height=58&pad=true&constrain=true",
    "e635ab97-3ddf-47c6-8b1b-10aa0eb30679": "https://rseq.ca/ImageGen.ashx?image=/media/24490/john_abbott.jpg&width=58&height=58&pad=true&constrain=true",
    "8d0be92f-fbe0-454b-a35f-a366282ecade": "https://rseq.ca/ImageGen.ashx?image=/media/24630/vaniercheetahsrgblrg__2_.gif&width=58&height=58&pad=true&constrain=true",

    # cegep_f_nord_est
    "4a80e344-e20a-4376-aa0f-b7590543d7e5": "https://rseq.ca/ImageGen.ashx?image=/media/2332428/6cc74913-ad22-4935-9959-1c9a8fe572b9.png&width=58&height=58&pad=true&constrain=true",
    "69c44926-e1ed-4382-a8d5-079e1847dca4": "https://rseq.ca/ImageGen.ashx?image=/media/24465/francois_xavier_garneau-seul.jpg&width=58&height=58&pad=true&constrain=true",
    "90846462-e058-4727-97cb-3f2fb56fcb16": "https://rseq.ca/ImageGen.ashx?image=/media/2346449/118088694_4185596501515934_4396355006125742223_o.jpg&width=58&height=58&pad=true&constrain=true",
    "4bf1c15b-7ef0-4b55-9aae-4a0c05c58256": "https://rseq.ca/ImageGen.ashx?image=/media/2912206/cl_titans_sans_e_noirrouge_cmyk.png&width=58&height=58&pad=true&constrain=true",
    "0d0b9090-acf8-46d7-8b7b-23f69ec7f36f": "https://rseq.ca/ImageGen.ashx?image=/media/347235/nd-condensee-neg.jpg&width=58&height=58&pad=true&constrain=true",
    "801854c8-8799-4bba-aee5-7be408eaeb4d": "https://rseq.ca/ImageGen.ashx?image=/media/24590/csf-logo_dynamiques_cmyk.jpg&width=58&height=58&pad=true&constrain=true",
    "bc938e9b-84cf-45d2-9ba1-c09e206bda54": "https://rseq.ca/ImageGen.ashx?image=/media/347235/nd-condensee-neg.jpg&width=58&height=58&pad=true&constrain=true",
    "5b08280d-2feb-40b3-9e40-bd7668975824": "https://rseq.ca/ImageGen.ashx?image=/media/24485/laureats-light_black.jpg&width=58&height=58&pad=true&constrain=true",
    "50af410b-0961-4ea7-acfd-64535a1a27ab": "https://rseq.ca/ImageGen.ashx?image=/media/24575/volontaires_complet_pformat_couleur.jpg&width=58&height=58&pad=true&constrain=true",
    "838fbfd2-4ba7-4d63-92d8-64331b421399": "https://rseq.ca/ImageGen.ashx?image=/media/1961060/logo__12a_diablos_diablotin_cegept-r_rgb.jpg&width=58&height=58&pad=true&constrain=true",
    "089caade-8658-48a9-90f5-9a9c875120c3": "https://rseq.ca/ImageGen.ashx?image=/media/2539895/logo_vulkins_couleur.png&width=58&height=58&pad=true&constrain=true",

    # university_m
    "78a948a7-5eed-4f98-ba32-1b73ba2b3e91": "https://rseq.ca/ImageGen.ashx?image=/media/24646/uni_logos_bsh_gaiters.jpg&width=58&height=58&pad=true&constrain=true",
    "2ecc0d44-bbe0-4b8f-84e3-777f76ccacfb": "https://rseq.ca/ImageGen.ashx?image=/media/492927/uni_logos_car_ravens.jpg&width=58&height=58&pad=true&constrain=true",
    "7effe149-5b71-4664-bade-6f91c5516c74": "https://rseq.ca/ImageGen.ashx?image=/media/24651/uni_logos_cnd_stingers.jpg&width=58&height=58&pad=true&constrain=true",
    "1d966340-7fb7-4170-b623-f1b8305ed00a": "https://rseq.ca/ImageGen.ashx?image=/media/24656/logo_piranhas_ets-200x130.gif&width=58&height=58&pad=true&constrain=true",
    "effba245-ab6c-4f22-9897-c32c8a2cd59f": "https://rseq.ca/ImageGen.ashx?image=/media/76121/uni_logos_mcg.jpg&width=58&height=58&pad=true&constrain=true",
    "559d4c83-3b88-489f-a343-62e84f44a5df": "https://rseq.ca/ImageGen.ashx?image=/media/24671/uni_logos_mtl_carabins.jpg&width=58&height=58&pad=true&constrain=true",
    "b4d1de6c-3279-4c62-979d-9b5eb47ebd40": "https://rseq.ca/ImageGen.ashx?image=/media/492903/uni_logos_ott_geegees.jpg&width=58&height=58&pad=true&constrain=true",

    # university_f
    "a1044ae6-abd9-49db-9e69-9e94617cb64f": "https://rseq.ca/ImageGen.ashx?image=/media/24646/uni_logos_bsh_gaiters.jpg&width=58&height=58&pad=true&constrain=true",
    "990077e5-e3ef-49b3-82aa-dc1fea75388a": "https://rseq.ca/ImageGen.ashx?image=/media/492927/uni_logos_car_ravens.jpg&width=58&height=58&pad=true&constrain=true",
    "e539f8b7-945a-4a92-9e71-390c704b0571": "https://rseq.ca/ImageGen.ashx?image=/media/24651/uni_logos_cnd_stingers.jpg&width=58&height=58&pad=true&constrain=true",
    "0423d176-be40-4c29-8fb3-b6cb5927a207": "https://rseq.ca/ImageGen.ashx?image=/media/24661/uni_logos_lvl_rouge_or.jpg&width=58&height=58&pad=true&constrain=true",
    "25a57eba-fc38-4481-9438-5e49fcb2c161": "https://rseq.ca/ImageGen.ashx?image=/media/76121/uni_logos_mcg.jpg&width=58&height=58&pad=true&constrain=true",
    "7ee0ec36-4447-4803-83ef-822f3e32d7d0": "https://rseq.ca/ImageGen.ashx?image=/media/24671/uni_logos_mtl_carabins.jpg&width=58&height=58&pad=true&constrain=true",
    "fc7a0121-93db-4711-8366-e8ac903a0986": "https://rseq.ca/ImageGen.ashx?image=/media/492903/uni_logos_ott_geegees.jpg&width=58&height=58&pad=true&constrain=true",
    "c532d0d3-a9ce-440e-8256-9232f4d23713": "https://rseq.ca/ImageGen.ashx?image=/media/24676/uni_logos_she_vo.png&width=58&height=58&pad=true&constrain=true",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_json(params: dict) -> dict:
    """Perform a GET request and return parsed JSON."""
    response = requests.get(API_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def dump_json(path: str, data: list | dict) -> None:
    """Write data to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def id_to_logo(team_id: str) -> str:
    """Get logo URL for a team ID."""
    return TEAM_LOGO_MAP.get(team_id, "")


def minutes_to_hhmm(minutes: int) -> str:
    """Convert minutes to HH:MM format."""
    if not isinstance(minutes, int):
        return ""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


# ---------------------------------------------------------------------------
# Main scrape
# ---------------------------------------------------------------------------

def scrape() -> None:
    """Fetch RSEQ data and save into JSON files inside data/ directory."""
    print("🚀 Starting RSEQ data scrape")

    # Process each league
    clubs: dict = {}
    fixtures: dict = {}
    standings: dict = {}

    for league_name, league_id in LEAGUES.items():
        print(f"  📊 Fetching {league_name}...")

        try:
            data = get_json({"leagueId": league_id})
        except Exception as e:
            print(f"  ❌ Error fetching {league_name}: {e}")
            continue

        # Teams/Clubs
        for team in data.get("Teams", []):
            team_id = team.get("TeamId", "")
            clubs[team_id] = {
                "name": team.get("TeamName", "").strip(),
                "code": team.get("TeamCode", "").strip(),
                "pseudonym": team.get("TeamPseudonym", "").strip(),
                "logo_url": id_to_logo(team_id),
            }

        # Fixtures & Results
        fixtures_list = []
        for fixture in data.get("RegularSeasonGames", []):
            # Skip rescheduled games
            if fixture.get("IsDateModified") and fixture.get("IsTimeModified"):
                continue

            fixture_data = {
                "home_id": fixture.get("HomeTeamId", ""),
                "away_id": fixture.get("VisitingTeamId", ""),
                "date": fixture.get("GameDateText", ""),
                "time": minutes_to_hhmm(fixture.get("GameTime", "")),
            }

            if fixture.get("IsSubmittedForStandings"):
                fixture_data["home_score"] = fixture.get("HomeTeamScore", "")
                fixture_data["away_score"] = fixture.get("VisitingTeamScore", "")
            else:
                fixture_data["venue"] = fixture.get("SportFacilityDescription", "")

            fixtures_list.append(fixture_data)

        fixtures[league_id] = fixtures_list

        # Standings
        standings_list = []
        for team in data.get("Standings", []):
            standings_list.append({
                "team_id": team.get("TeamId", ""),
                "pos": team.get("Position", ""),
                "pld": team.get("GamesPlayed", ""),
                "w": team.get("Wins", ""),
                "d": team.get("Draws", ""),
                "l": team.get("Losses", ""),
                "pf": team.get("PointsFor", ""),
                "pa": team.get("PointsAgaints", ""),
                "diff": team.get("Diff1", ""),
                "tf": team.get("TriesFor", ""),
                "ta": team.get("TriesAgainst", ""),
                "td": team.get("TriesDiff", ""),
                "pts": team.get("TotalPoints", ""),
                "division": data.get("Conference", ""),
            })

        standings[league_id] = standings_list

    # Create output directory and save data
    output_dir = os.path.join("data", "rseq", "2026")
    os.makedirs(output_dir, exist_ok=True)

    dump_json(os.path.join(output_dir, "clubs.json"), clubs)
    dump_json(os.path.join(output_dir, "leagues.json"), 
              {id: name for name, id in LEAGUES.items()})
    dump_json(os.path.join(output_dir, "fixtures.json"), fixtures)
    dump_json(os.path.join(output_dir, "standings.json"), standings)

    print(f"✅ Data saved to {output_dir}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape RSEQ rugby data")
    parser.add_argument(
        "--output",
        type=str,
        default="data/rseq/2026",
        help="Output directory for JSON files (default: data/rseq/2026)",
    )
    args = parser.parse_args()

    scrape()