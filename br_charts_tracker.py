#!/usr/bin/env python3
"""
br_charts_tracker.py - Coleta dados de charts do Spotify por país
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

DATA_DIR = Path("dados")

# Países suportados pelo Spotify com seus códigos de mercado
COUNTRIES = {
    "Afghanistan": "AF",
    "Albania": "AL",
    "Algeria": "DZ",
    "Andorra": "AD",
    "Angola": "AO",
    "Antigua and Barbuda": "AG",
    "Argentina": "AR",
    "Armenia": "AM",
    "Australia": "AU",
    "Austria": "AT",
    "Azerbaijan": "AZ",
    "Bahrain": "BH",
    "Bangladesh": "BD",
    "Barbados": "BB",
    "Belarus": "BY",
    "Belgium": "BE",
    "Belize": "BZ",
    "Benin": "BJ",
    "Bhutan": "BT",
    "Bolivia": "BO",
    "Bosnia and Herzegovina": "BA",
    "Botswana": "BW",
    "Brazil": "BR",
    "Brunei": "BN",
    "Bulgaria": "BG",
    "Burkina Faso": "BF",
    "Cambodia": "KH",
    "Cameroon": "CM",
    "Canada": "CA",
    "Cape Verde": "CV",
    "Chile": "CL",
    "Colombia": "CO",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Dominican Republic": "DO",
    "Ecuador": "EC",
    "Egypt": "EG",
    "El Salvador": "SV",
    "Estonia": "EE",
    "Ethiopia": "ET",
    "Fiji": "FJ",
    "Finland": "FI",
    "France": "FR",
    "Gambia": "GM",
    "Germany": "DE",
    "Ghana": "GH",
    "Greece": "GR",
    "Guatemala": "GT",
    "Guinea": "GN",
    "Honduras": "HN",
    "Hong Kong": "HK",
    "Hungary": "HU",
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Ireland": "IE",
    "Israel": "IL",
    "Italy": "IT",
    "Jamaica": "JM",
    "Japan": "JP",
    "Jordan": "JO",
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kuwait": "KW",
    "Kyrgyzstan": "KG",
    "Laos": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malaysia": "MY",
    "Maldives": "MV",
    "Malta": "MT",
    "Mexico": "MX",
    "Moldova": "MD",
    "Monaco": "MC",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Myanmar": "MM",
    "Namibia": "NA",
    "Nepal": "NP",
    "Netherlands": "NL",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Nigeria": "NG",
    "North Macedonia": "MK",
    "Norway": "NO",
    "Oman": "OM",
    "Pakistan": "PK",
    "Panama": "PA",
    "Papua New Guinea": "PG",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines": "PH",
    "Poland": "PL",
    "Portugal": "PT",
    "Qatar": "QA",
    "Romania": "RO",
    "Rwanda": "RW",
    "Saudi Arabia": "SA",
    "Senegal": "SN",
    "Serbia": "RS",
    "Singapore": "SG",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "South Africa": "ZA",
    "South Korea": "KR",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Taiwan": "TW",
    "Tajikistan": "TJ",
    "Tanzania": "TZ",
    "Thailand": "TH",
    "Trinidad and Tobago": "TT",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Uganda": "UG",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "United Kingdom": "GB",
    "United States": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Venezuela": "VE",
    "Vietnam": "VN",
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
}


def get_spotify_client():
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Erro: SPOTIPY_CLIENT_ID e SPOTIPY_CLIENT_SECRET não encontrados no .env")
        sys.exit(1)
    auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth)


def get_countries_by_letter(letters):
    result = {}
    for letter in letters:
        for country, code in COUNTRIES.items():
            if country.upper().startswith(letter.upper()):
                result[country] = code
    return result


def get_top_tracks(sp, market_code, country_name):
    try:
        playlists = sp.category_playlists(
            category_id="toplists", country=market_code, limit=5
        )
        items = playlists.get("playlists", {}).get("items", [])
        if not items:
            print(f"  Sem playlists de top para {country_name} ({market_code})")
            return None

        playlist = items[0]
        playlist_id = playlist["id"]
        playlist_name = playlist["name"]

        results = sp.playlist_tracks(playlist_id, limit=50)
        tracks = []
        for i, item in enumerate(results["items"], 1):
            track = item.get("track")
            if not track:
                continue
            tracks.append(
                {
                    "pais": country_name,
                    "mercado": market_code,
                    "playlist": playlist_name,
                    "posicao": i,
                    "track_id": track["id"],
                    "track_name": track["name"],
                    "artistas": ", ".join(a["name"] for a in track["artists"]),
                    "album": track["album"]["name"],
                    "popularidade": track["popularity"],
                    "data_coleta": datetime.now().strftime("%Y-%m-%d"),
                }
            )
        return tracks
    except spotipy.SpotifyException as e:
        print(f"  Erro Spotify para {country_name} ({market_code}): {e}")
        return None
    except Exception as e:
        print(f"  Erro inesperado para {country_name} ({market_code}): {e}")
        return None


def save_data(country_name, tracks):
    DATA_DIR.mkdir(exist_ok=True)
    filename = DATA_DIR / f"{country_name.replace(' ', '_').lower()}.csv"
    df = pd.DataFrame(tracks)
    df.to_csv(filename, index=False, encoding="utf-8")
    return filename


def run_letters(sp, letters):
    countries = get_countries_by_letter(letters)
    if not countries:
        print(f"Nenhum país encontrado para as letras: {', '.join(letters)}")
        return

    print(f"Países encontrados: {len(countries)}")
    for country, code in countries.items():
        print(f"\nColetando: {country} ({code})...")
        tracks = get_top_tracks(sp, code, country)
        if tracks:
            filename = save_data(country, tracks)
            print(f"  {len(tracks)} tracks salvas em {filename}")
        else:
            print(f"  Sem dados disponíveis para {country}")


def show_report():
    if not DATA_DIR.exists() or not list(DATA_DIR.glob("*.csv")):
        print("Nenhum dado coletado ainda. Execute com --letra para coletar dados.")
        return

    dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
    all_data = pd.concat(dfs, ignore_index=True)

    print("\n=== RELATÓRIO DE COLETA ===")
    print(f"Países coletados : {all_data['pais'].nunique()}")
    print(f"Total de tracks  : {len(all_data)}")
    print(f"Datas de coleta  : {', '.join(sorted(all_data['data_coleta'].unique()))}")

    print("\nPaíses:")
    for pais, count in all_data.groupby("pais").size().items():
        print(f"  {pais}: {count} tracks")

    print("\nTop 10 artistas mais presentes nos charts:")
    artist_counts = (
        all_data["artistas"].str.split(", ").explode().value_counts().head(10)
    )
    for artist, count in artist_counts.items():
        print(f"  {artist}: {count} aparições")


def main():
    parser = argparse.ArgumentParser(
        description="Coleta charts do Spotify por país",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python br_charts_tracker.py --letra A
  python br_charts_tracker.py --letra A B C
  python br_charts_tracker.py --relatorio
        """,
    )
    parser.add_argument(
        "--letra",
        nargs="+",
        metavar="LETRA",
        help="Letra(s) inicial dos países (ex: A B C)",
    )
    parser.add_argument(
        "--relatorio",
        action="store_true",
        help="Exibe relatório dos dados coletados",
    )
    args = parser.parse_args()

    if args.relatorio:
        show_report()
    elif args.letra:
        sp = get_spotify_client()
        run_letters(sp, [l.upper() for l in args.letra])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
