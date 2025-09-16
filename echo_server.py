import requests
from bot_discord import trigger_message
from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

mcp = FastMCP("Chess Analysis Server")


def _fetch_tournaments_page() -> str:
    """Fetch the raw content from the chess tournaments page."""
    url = "https://www.echecsfrance.com/en/tournaments"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return ""


def _extract_tournament_references(html_content: str) -> List[str]:
    """Extract all FicheTournoi.aspx?Ref=XXXXX patterns from HTML."""
    pattern = r"FicheTournoi\.aspx\?Ref=\d+"

    matches = re.findall(pattern, html_content)

    unique_matches = list(dict.fromkeys(matches))

    return unique_matches


def _fetch_tournament_details(tournament_ref: str) -> Dict[str, str]:
    """Fetch tournament details from a specific tournament page."""
    base_url = "https://www.echecs.asso.fr/"
    full_url = base_url + tournament_ref

    try:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        response = session.get(full_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        def extract_field(field_id: str) -> str:
            """Helper function to extract field value by ID."""
            elem = soup.find("span", {"id": field_id})
            return elem.get_text().strip() if elem else "N/A"

        details = {
            "name": extract_field("ctl00_ContentPlaceHolderMain_LabelNom"),
            "dates": extract_field("ctl00_ContentPlaceHolderMain_LabelDates"),
            "nombre_rondes": extract_field(
                "ctl00_ContentPlaceHolderMain_LabelNbrRondes"
            ),
            "cadence": extract_field("ctl00_ContentPlaceHolderMain_LabelCadence"),
            "organisateur": extract_field(
                "ctl00_ContentPlaceHolderMain_LabelOrganisateur"
            ),
            "arbitre": extract_field("ctl00_ContentPlaceHolderMain_LabelArbitre"),
            "adresse": extract_field("ctl00_ContentPlaceHolderMain_LabelAdresse"),
            "contact": extract_field("ctl00_ContentPlaceHolderMain_LabelContact"),
            "premier_prix": extract_field("ctl00_ContentPlaceHolderMain_LabelPrix1"),
            "inscription_senior": extract_field(
                "ctl00_ContentPlaceHolderMain_LabelInscriptionSenior"
            ),
            "inscription_jeunes": extract_field(
                "ctl00_ContentPlaceHolderMain_LabelInscriptionJeune"
            ),
            "annonce": extract_field("ctl00_ContentPlaceHolderMain_LabelAnnonce"),
            "url": full_url,
        }

        return details
    except Exception as e:
        print(f"Error fetching tournament {tournament_ref}: {e}")
        return {
            "name": "Error",
            "dates": "Error",
            "nombre_rondes": "Error",
            "cadence": "Error",
            "organisateur": "Error",
            "arbitre": "Error",
            "adresse": "Error",
            "contact": "Error",
            "premier_prix": "Error",
            "inscription_senior": "Error",
            "inscription_jeunes": "Error",
            "annonce": "Error",
            "url": full_url,
        }


@mcp.tool(
    description="Retrieves information about upcoming chess tournaments (name, dates, number of rounds, organizer)"
)
def get_tournaments_upcoming():
    """Récupère rapidement les informations des tournois d'échecs à venir.
    Version optimisée qui ne récupère que les champs principaux pour une réponse plus rapide.
    Récupère tous les tournois à venir.
    """
    html_content = _fetch_tournaments_page()

    if not html_content:
        return {"total_tournaments": 0, "tournaments": []}

    tournament_refs = _extract_tournament_references(html_content)

    def _fetch_basic_details(tournament_ref: str) -> Dict[str, str]:
        """Fetch only basic tournament details."""
        base_url = "https://www.echecs.asso.fr/"
        full_url = base_url + tournament_ref

        try:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            response = session.get(full_url, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            def extract_field(field_id: str) -> str:
                elem = soup.find("span", {"id": field_id})
                return elem.get_text().strip() if elem else "N/A"

            return {
                "name": extract_field("ctl00_ContentPlaceHolderMain_LabelNom"),
                "dates": extract_field("ctl00_ContentPlaceHolderMain_LabelDates"),
                "nombre_rondes": extract_field(
                    "ctl00_ContentPlaceHolderMain_LabelNbrRondes"
                ),
                "organisateur": extract_field(
                    "ctl00_ContentPlaceHolderMain_LabelOrganisateur"
                ),
                "url": full_url,
            }
        except Exception as e:
            return {
                "name": "Error",
                "dates": "Error",
                "nombre_rondes": "Error",
                "organisateur": "Error",
                "url": full_url,
            }

    tournament_details = []

    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_ref = {
            executor.submit(_fetch_basic_details, ref): ref for ref in tournament_refs
        }

        for future in as_completed(future_to_ref):
            ref = future_to_ref[future]
            try:
                details = future.result()
                tournament_details.append(details)
            except Exception as e:
                print(f"Error processing tournament {ref}: {e}")

    result = {
        "total_tournaments": len(tournament_details),
        "tournaments": tournament_details,
    }

    return result


def _get_games_json(archive_url: str) -> dict:
    r = requests.get(archive_url, headers={"User-Agent": "python-chess-data/1.0"})
    r.raise_for_status()
    return r.json()


def get_last_game_pgn(username: str):
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    r = requests.get(url, headers={"User-Agent": "python-chess-data/1.0"})
    r.raise_for_status()
    print(r.json()["archives"][0])
    return _get_games_json(r.json()["archives"][-1])


@mcp.tool(
    description="Analyzes the most recent chess game of a user and provides detailed analysis for the specified player color"
)
def analyze_latest_game(username: str, player_color: str):
    game = get_last_game_pgn(username)
    return {"player_username": username, "pgn": game["games"][-1]["pgn"]}


@mcp.tool(
    description="Sends a Discord message to announce that a participant joins a tournament."
)
def send_message_discord(nom: str, tournoi: str, lien: str, date: str, lieu: str):
    trigger_message(nom, tournoi, lien, date, lieu)


# @mcp.tool(description="Extracts FEN from a Chess.com game URL")
# def get_game_pgn_from_url(game_url: str, player_username: str):
#     game_id = game_url.split("/")[-1]
#     url = f"https://www.chess.com/callback/live/game/{game_id}"
#     r = requests.get(url, headers={"User-Agent": "python-chess-data/1.0"})
#     r.raise_for_status()
#     data = r.json()
#     fen = data["game"]["pgnHeaders"]["FEN"]
#     return {"player_username": player_username, "fen": fen}


# print(get_game_pgn_from_url("https://www.chess.com/game/live/143092396166", "hikaru"))
