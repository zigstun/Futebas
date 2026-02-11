import requests
import json
import csv
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# API configuration
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("API_BASE_URL", "https://v3.football.api-sports.io")
headers = {"x-apisports-key": API_KEY}

# Serie A Brasil
SERIE_A_ID = 71
CURRENT_SEASON = 2024
CACHE_DIR = "cache"

def ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_from_cache(cache_file):
    """Load data from cache file"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except:
            pass
    return None

def save_to_cache(data, cache_file):
    """Save data to cache file"""
    ensure_cache_dir()
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def make_request(endpoint, params, cache_file=None):
    """
    Make API request APENAS com certeza de sucesso
    Retorna dados do cache se existir
    Retorna None se API falhar (sem retry para economizar requisicoes)
    """
    
    # Verificar cache PRIMEIRO
    if cache_file:
        cached = load_from_cache(cache_file)
        if cached:
            print(f"[CACHE OK] {os.path.basename(cache_file)}", flush=True)
            return cached
    
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"[API] GET {endpoint} ", end="", flush=True)
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Verificar erros
        if data.get("errors"):
            error = str(data.get("errors"))
            if "rateLimit" in error:
                print(f"[LIMITE ATINGIDO]")
            else:
               print(f"[ERRO API]")
            return None
        
        # Sucesso - salvar em cache
        if cache_file:
            save_to_cache(data, cache_file)
            print(f"[OK] {data.get('results', 0)} resultado(s)", flush=True)
        else:
            print(f"[OK]", flush=True)
        
        return data
        
    except Exception as e:
        print(f"[FALHA] {str(e)[:40]}", flush=True)
        return None

def get_teams_by_league(league_id=SERIE_A_ID, season=CURRENT_SEASON):
    """Buscar times (1 requisicao)"""
    params = {"league": league_id, "season": season}
    cache_file = os.path.join(CACHE_DIR, "teams.json")
    data = make_request("/teams", params, cache_file=cache_file)
    return data.get("response", []) if data else []

def get_fixtures(league_id=SERIE_A_ID, season=CURRENT_SEASON):
    """Buscar fixtures (1 requisicao)"""
    params = {"league": league_id, "season": season}
    cache_file = os.path.join(CACHE_DIR, "fixtures.json")
    data = make_request("/fixtures", params, cache_file=cache_file)
    return data.get("response", []) if data else []

def get_standings(league_id=SERIE_A_ID, season=CURRENT_SEASON):
    """Buscar standings (1 requisicao)"""
    params = {"league": league_id, "season": season}
    cache_file = os.path.join(CACHE_DIR, "standings.json")
    data = make_request("/standings", params, cache_file=cache_file)
    return data.get("response", []) if data else []

def export_fixtures_csv(fixtures):
    """Exportar resultados para CSV"""
    if not fixtures:
        print("[ERRO] Sem dados de fixtures")
        return
    
    data = []
    for fixture in fixtures:
        fixture_info = fixture.get("fixture", {})
        league = fixture.get("league", {})
        home = fixture.get("teams", {}).get("home", {})
        away = fixture.get("teams", {}).get("away", {})
        goals = fixture.get("goals", {})
        
        data.append({
            "fixture_id": fixture_info.get("id"),
            "round": league.get("round", ""),
            "date": fixture_info.get("date", ""),
            "status": fixture_info.get("status", ""),
            "home_team": home.get("name", ""),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "away_team": away.get("name", ""),
        })
    
    if data:
        with open("resultados_serie_a.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"[OK] resultados_serie_a.csv ({len(data)} jogos)")

def export_standings_csv(standings):
    """Exportar classificacao para CSV"""
    if not standings:
        print("[ERRO] Sem dados de standings")
        return
    
    data = []
    for standing in standings:
        league_standings = standing.get("league", {}).get("standings", [])
        for group_standings in league_standings:
            for position, team_standing in enumerate(group_standings, 1):
                data.append({
                    "position": position,
                    "team_id": team_standing.get("team", {}).get("id"),
                    "team_name": team_standing.get("team", {}).get("name"),
                    "points": team_standing.get("points"),
                    "played": team_standing.get("all", {}).get("played"),
                    "wins": team_standing.get("all", {}).get("win"),
                    "draws": team_standing.get("all", {}).get("draw"),
                    "losses": team_standing.get("all", {}).get("lose"),
                    "gf": team_standing.get("all", {}).get("goals", {}).get("for"),
                    "ga": team_standing.get("all", {}).get("goals", {}).get("against"),
                    "gd": team_standing.get("goalsDiff"),
                })
    
    if data:
        with open("classificacao_serie_a.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"[OK] classificacao_serie_a.csv ({len(data)} linhas)")

if __name__ == "__main__":
    print("\n" + "=" * 75)
    print("SERIE A 2024 - COLETA OTIMIZADA")
    print("=" * 75)
    print("\nEstrategia:")
    print("  [CACHE] Verifica dados existentes no cache primeiro")
    print("  [OTIMIZADO] Apenas 3 requisicoes ESSENCIAIS (teams, fixtures, standings)")
    print("  [RAPIDO] Sem coleta de jogadores (economiza 20+ requisicoes)")
    print("  [POWERBI] Exportacao direto para CSV")
    print("=" * 75)
    
    ensure_cache_dir()
    all_data = {}
    
    # Coleta 1: Times
    print("\n[1/3] TIMES ", end="")
    teams = get_teams_by_league()
    all_data['teams'] = teams
    if teams:
        print(f"- {len(teams)} encontrados")
    else:
        print("- ERRO")
    
    # Coleta 2: Fixtures
    print("[2/3] FIXTURES ", end="")
    fixtures = get_fixtures()
    all_data['fixtures'] = fixtures
    if fixtures:
        print(f"- {len(fixtures)} encontrados")
    else:
        print("- ERRO")
    
    # Coleta 3: Standings
    print("[3/3] STANDINGS ", end="")
    standings = get_standings()
    all_data['standings'] = standings
    if standings:
        print(f"- {len(standings)} encontrados")
    else:
        print("- ERRO")
    
    # Exportar CSVs
    print("\n" + "=" * 75)
    print("EXPORTANDO PARA PowerBI")
    print("=" * 75 + "\n")
    
    export_fixtures_csv(fixtures)
    export_standings_csv(standings)
    
    print("\n" + "=" * 75)
    print("COLETA COMPLETA!")
    print("=" * 75)
    print("\nArquivos para PowerBI:")
    print("  > resultados_serie_a.csv")
    print("  > classificacao_serie_a.csv")
    print("\nCache (reutilizavel):")
    print("  > cache/teams.json")
    print("  > cache/fixtures.json")
    print("  > cache/standings.json")
    print("\nPROXIMO USO:")
    print("  Tudo em cache = 0 requisicoes!")
    print("=" * 75 + "\n")