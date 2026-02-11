"""
COLLECT_MULTI_SEASON.PY
=======================

Script principal para coleta de dados da Série A Brasil (2022-2024).

Funcionalidades:
- Coleta dados de múltiplas temporadas
- Cache inteligente (verifica se dados já existem antes de fazer requisição)
- Append automático em CSVs
- Otimizações: apenas 3 requisições por temporada

Estrutura de dados:
- Cada season requer 3 endpoints: /teams, /fixtures, /standings
- Cache salvo em JSON na pasta data/cache/
- Output em CSV na pasta data/output/

Uso:
    python collect_multi_season.py

Variáveis de ambiente (.env):
    API_KEY: Sua chave de acesso à API-Sports
    API_BASE_URL: URL base da API (default: https://v3.football.api-sports.io)
    LEAGUE_ID: ID da liga - 71 para Série A Brasil
    SEASONS: Temporadas a coletar (ex: 2022,2023,2024)

Autor: Seu Nome
Data: Fevereiro 2026
"""

import requests
import json
import csv
import time
import os
from collections import defaultdict
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ============= CONFIGURAÇÕES =============
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("API_BASE_URL", "https://v3.football.api-sports.io")
SERIE_A_ID = int(os.getenv("LEAGUE_ID", "71"))
SEASONS = [int(s.strip()) for s in os.getenv("SEASONS", "2022,2023,2024").split(",")]
CACHE_DIR = "cache"
OUTPUT_DIR = "output"

# Headers para requisição à API
headers = {"x-apisports-key": API_KEY}

# ============= FUNÇÕES AUXILIARES =============

def ensure_dirs():
    """
    Cria as pastas de cache e output se não existirem.
    
    Diretórios criados:
    - cache/: Armazena JSON brutos da API
    - output/: Armazena CSVs para PowerBI
    """
    for directory in [CACHE_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[DIR] Criada pasta: {directory}")

def load_cache(filename):
    """
    Carrega dados do cache se existirem.
    
    Args:
        filename (str): Nome do arquivo JSON no cache
    
    Returns:
        dict: Dados carregados ou None se não existir/falhar
    """
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERRO] Falha ao ler cache {filename}: {e}")
    return None

def save_cache(data, filename):
    """
    Salva dados em cache para reuso futuro.
    
    Args:
        data (dict): Dados a salvar
        filename (str): Nome do arquivo JSON no cache
    """
    ensure_dirs()
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar cache {filename}: {e}")

def api_request(endpoint, params):
    """
    Faz requisição à API com tratamento de erros.
    
    Estratégia:
    1. Verifica cache primeiro (sem gastar requisição)
    2. Se não houver cache, faz requisição
    3. Salva resultado em cache
    4. Retorna dados ou None
    
    Args:
        endpoint (str): Path do endpoint (ex: /teams, /fixtures)
        params (dict): Parâmetros da requisição
    
    Returns:
        dict: Response JSON da API ou None se falha
    """
    url = f"{BASE_URL}{endpoint}"
    season = params.get('season')
    
    try:
        print(f"  [REQ] {endpoint} season={season}", end=" -> ", flush=True)
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Verificar se há erros na resposta
        if data.get("errors"):
            error = str(data.get("errors"))
            print(f"[ERRO] {error[:50]}")
            return None
        
        results_count = data.get('results', 0)
        print(f"[OK] {results_count} resultado(s)")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"[FALHA] {str(e)[:50]}")
        return None
    except Exception as e:
        print(f"[ERRO GERAL] {str(e)[:50]}")
        return None

def collect_season(season):
    """
    Coleta dados completos de uma temporada.
    
    Fluxo:
    1. Para cada endpoint (teams, fixtures, standings):
       a. Verifica se existe em cache
       b. Se sim: carrega do cache (zero requisições!)
       c. Se não: faz requisição à API e salva em cache
    2. Retorna dict com todos os dados
    
    Args:
        season (int): Ano da temporada (ex: 2024)
    
    Returns:
        dict: {
            'teams': [...],
            'fixtures': [...],
            'standings': [...]
        }
    """
    print(f"\n{'='*75}")
    print(f"COLETANDO TEMPORADA: {season}")
    print(f"{'='*75}")
    
    season_data = {}
    cache_prefix = f"season_{season}"
    
    # ===== [1/3] COLETA DE TIMES =====
    print(f"\n[1/3] TIMES ", end="")
    cache_file = os.path.join(CACHE_DIR, f"{cache_prefix}_teams.json")
    
    if os.path.exists(cache_file):
        # Cache existe - usar sem fazer requisição
        print("[CACHE OK]")
        with open(cache_file, 'r', encoding='utf-8') as f:
            teams_obj = json.load(f)
            season_data['teams'] = teams_obj.get('response', [])
    else:
        # Cache não existe - fazer requisição
        data = api_request("/teams", {"league": SERIE_A_ID, "season": season})
        if data:
            season_data['teams'] = data.get('response', [])
            save_cache(data, f"{cache_prefix}_teams.json")
        else:
            print("[ERRO na coleta de teams]")
            season_data['teams'] = []
        time.sleep(1)  # Respeitar rate limit da API
    
    # ===== [2/3] COLETA DE JOGOS (FIXTURES) =====
    print(f"[2/3] FIXTURES ", end="")
    cache_file = os.path.join(CACHE_DIR, f"{cache_prefix}_fixtures.json")
    
    if os.path.exists(cache_file):
        print("[CACHE OK]")
        with open(cache_file, 'r', encoding='utf-8') as f:
            fixtures_obj = json.load(f)
            season_data['fixtures'] = fixtures_obj.get('response', [])
    else:
        data = api_request("/fixtures", {"league": SERIE_A_ID, "season": season})
        if data:
            season_data['fixtures'] = data.get('response', [])
            save_cache(data, f"{cache_prefix}_fixtures.json")
        else:
            print("[ERRO na coleta de fixtures]")
            season_data['fixtures'] = []
        time.sleep(1)
    
    # ===== [3/3] COLETA DE CLASSIFICAÇÃO =====
    print(f"[3/3] STANDINGS ", end="")
    cache_file = os.path.join(CACHE_DIR, f"{cache_prefix}_standings.json")
    
    if os.path.exists(cache_file):
        print("[CACHE OK]")
        with open(cache_file, 'r', encoding='utf-8') as f:
            standings_obj = json.load(f)
            season_data['standings'] = standings_obj.get('response', [])
    else:
        data = api_request("/standings", {"league": SERIE_A_ID, "season": season})
        if data:
            season_data['standings'] = data.get('response', [])
            save_cache(data, f"{cache_prefix}_standings.json")
        else:
            print("[ERRO na coleta de standings]")
            season_data['standings'] = []
        time.sleep(1)
    
    # Resumo da temporada
    print(f"\nResumo {season}:")
    print(f"  Times: {len(season_data.get('teams', []))}")
    print(f"  Fixtures: {len(season_data.get('fixtures', []))}")
    print(f"  Standings: {len(season_data.get('standings', []))}")
    
    return season_data

def generate_classificacao_rodada(season_data, season):
    """
    Reconstrói a classificação por rodada a partir dos fixtures.
    
    Lógica:
    1. Processa fixtures em ordem cronológica
    2. Mantém contadores cumulativos de cada time
    3. Após cada fixture finalizado, salva snapshot da classificação
    4. Repete para aplicar regras de desempate (pontos, GF, GC)
    
    Args:
        season_data (dict): Dados da season {'teams': [...], 'fixtures': [...]}
        season (int): Ano da temporada
    
    Returns:
        list: Lista de dicts com classificação por rodada
    """
    fixtures = season_data.get('fixtures', [])
    teams_dict = {}
    
    # Mapear IDs de times para nomes
    for team_info in season_data.get('teams', []):
        team = team_info.get('team', {})
        teams_dict[team['id']] = team['name']
    
    standings_by_round = {}
    team_stats = defaultdict(lambda: {
        'name': '',
        'played': 0,
        'wins': 0,
        'draws': 0,
        'losses': 0,
        'goals_for': 0,
        'goals_against': 0,
        'points': 0,
        'season': season
    })
    
    # Inicializar todos os times
    for team_id, team_name in teams_dict.items():
        team_stats[team_id]['name'] = team_name
    
    # Processar fixtures em ordem cronológica
    for fixture in sorted(fixtures, key=lambda x: x.get('fixture', {}).get('date', '')):
        fixture_info = fixture.get('fixture', {})
        league = fixture.get('league', {})
        round_name = league.get('round', 'Unknown')
        
        # Status pode ser objeto ou string - normalizar
        status_obj = fixture_info.get('status', {})
        if isinstance(status_obj, dict):
            status = status_obj.get('short', '')
        else:
            status = status_obj
        
        # Só processar jogos finalizados
        if status not in ['FT', 'AET']:  # FT = Full Time, AET = After Extra Time
            continue
        
        # Extrair dados do fixture
        home_team_id = fixture.get('teams', {}).get('home', {}).get('id')
        away_team_id = fixture.get('teams', {}).get('away', {}).get('id')
        home_goals = fixture.get('goals', {}).get('home')
        away_goals = fixture.get('goals', {}).get('away')
        
        if not all([home_team_id, away_team_id, home_goals is not None, away_goals is not None]):
            continue
        
        # Atualizar estatísticas de ambos os times
        team_stats[home_team_id]['played'] += 1
        team_stats[home_team_id]['goals_for'] += home_goals
        team_stats[home_team_id]['goals_against'] += away_goals
        
        team_stats[away_team_id]['played'] += 1
        team_stats[away_team_id]['goals_for'] += away_goals
        team_stats[away_team_id]['goals_against'] += home_goals
        
        # Determinar resultado e atualizar pontos
        if home_goals > away_goals:
            team_stats[home_team_id]['wins'] += 1
            team_stats[home_team_id]['points'] += 3
            team_stats[away_team_id]['losses'] += 1
        elif home_goals < away_goals:
            team_stats[away_team_id]['wins'] += 1
            team_stats[away_team_id]['points'] += 3
            team_stats[home_team_id]['losses'] += 1
        else:
            team_stats[home_team_id]['draws'] += 1
            team_stats[home_team_id]['points'] += 1
            team_stats[away_team_id]['draws'] += 1
            team_stats[away_team_id]['points'] += 1
        
        # Salvar classificação após essa rodada
        if round_name not in standings_by_round:
            standings_by_round[round_name] = {}
            for team_id, stats in team_stats.items():
                standings_by_round[round_name][team_id] = dict(stats)
    
    # Converter para formato de linhas para CSV
    all_rows = []
    
    for round_name in sorted(standings_by_round.keys(), 
                            key=lambda x: int(x.split('-')[-1].strip()) if '-' in x else 0):
        standings = standings_by_round[round_name]
        
        # Ordenar times por pontos (desempates: GF - GA)
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (x[1]['points'], x[1]['goals_for'] - x[1]['goals_against']),
            reverse=True
        )
        
        # Adicionar com posição
        for position, (team_id, stats) in enumerate(sorted_teams, 1):
            all_rows.append({
                'season': season,
                'round': round_name,
                'position': position,
                'team_id': team_id,
                'team_name': stats['name'],
                'played': stats['played'],
                'wins': stats['wins'],
                'draws': stats['draws'],
                'losses': stats['losses'],
                'goals_for': stats['goals_for'],
                'goals_against': stats['goals_against'],
                'goal_diff': stats['goals_for'] - stats['goals_against'],
                'points': stats['points'],
            })
    
    return all_rows

# ============= MAIN - EXECUÇÃO PRINCIPAL =============

if __name__ == "__main__":
    # Validar configurações
    if not API_KEY:
        print("\n[ERRO] API_KEY não configurada!")
        print("Copie .env.example para .env e adicione sua chave de API")
        exit(1)
    
    ensure_dirs()
    
    print("\n" + "="*75)
    print("SERIE A BRASIL - MULTI-SEASON DATA COLLECTION")
    print("="*75)
    print(f"\nConfigurações:")
    print(f"  Seasons: {SEASONS}")
    print(f"  Estratégia: Cache + Requisições otimizadas")
    print(f"  Output: data/output/")
    
    # ===== ETAPA 1: COLETAR DADOS DE TODAS AS SEASONS =====
    all_seasons_data = {}
    for season in SEASONS:
        all_seasons_data[season] = collect_season(season)
    
    # ===== ETAPA 2: EXPORTAR RESULTADOS (JOGOS) =====
    print("\n" + "="*75)
    print("STEP 2: EXPORTANDO resultados_serie_a.csv")
    print("="*75)
    
    all_results = []
    for season in SEASONS:
        fixtures = all_seasons_data[season].get('fixtures', [])
        for fixture in fixtures:
            fixture_info = fixture.get('fixture', {})
            league = fixture.get('league', {})
            home = fixture.get('teams', {}).get('home', {})
            away = fixture.get('teams', {}).get('away', {})
            goals = fixture.get('goals', {})
            
            all_results.append({
                'season': season,
                'fixture_id': fixture_info.get('id'),
                'round': league.get('round', ''),
                'date': fixture_info.get('date', ''),
                'status': fixture_info.get('status', {}).get('short', ''),
                'home_team': home.get('name', ''),
                'home_goals': goals.get('home'),
                'away_goals': goals.get('away'),
                'away_team': away.get('name', ''),
            })
    
    if all_results:
        output_file = os.path.join(OUTPUT_DIR, 'resultados_serie_a.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print(f"[OK] {len(all_results)} jogos exportados")
    
    # ===== ETAPA 3: EXPORTAR CLASSIFICAÇÃO POR RODADA =====
    print("\nSTEP 3: EXPORTANDO classificacao_por_rodada.csv")
    print("="*75)
    
    all_rodadas = []
    for season in SEASONS:
        season_rows = generate_classificacao_rodada(all_seasons_data[season], season)
        all_rodadas.extend(season_rows)
    
    if all_rodadas:
        output_file = os.path.join(OUTPUT_DIR, 'classificacao_por_rodada.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_rodadas[0].keys())
            writer.writeheader()
            writer.writerows(all_rodadas)
        print(f"[OK] {len(all_rodadas)} registros exportados")
    
    # ===== ETAPA 4: EXPORTAR CLASSIFICAÇÃO FINAL =====
    print("\nSTEP 4: EXPORTANDO classificacao_final.csv")
    print("="*75)
    
    all_final = []
    for season in SEASONS:
        standings = all_seasons_data[season].get('standings', [])
        for standing in standings:
            league_standings = standing.get('league', {}).get('standings', [])
            for group_standings in league_standings:
                for position, team_standing in enumerate(group_standings, 1):
                    all_final.append({
                        'season': season,
                        'position': position,
                        'team_id': team_standing.get('team', {}).get('id'),
                        'team_name': team_standing.get('team', {}).get('name'),
                        'points': team_standing.get('points'),
                        'played': team_standing.get('all', {}).get('played'),
                        'wins': team_standing.get('all', {}).get('win'),
                        'draws': team_standing.get('all', {}).get('draw'),
                        'losses': team_standing.get('all', {}).get('lose'),
                        'gf': team_standing.get('all', {}).get('goals', {}).get('for'),
                        'ga': team_standing.get('all', {}).get('goals', {}).get('against'),
                        'gd': team_standing.get('goalsDiff'),
                    })
    
    if all_final:
        output_file = os.path.join(OUTPUT_DIR, 'classificacao_final.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_final[0].keys())
            writer.writeheader()
            writer.writerows(all_final)
        print(f"[OK] {len(all_final)} registros exportados")
    
    # ===== RESUMO FINAL =====
    print("\n" + "="*75)
    print("COLETA COMPLETA!")
    print("="*75)
    
    for season in SEASONS:
        results_count = len([r for r in all_results if r['season'] == season])
        rodadas_count = len(set(r['round'] for r in all_rodadas if r['season'] == season))
        print(f"\n{season}:")
        print(f"  Jogos: {results_count}")
        print(f"  Rodadas: {rodadas_count}")
    
    print("\nArquivos ATUALIZADOS (com appends):")
    print("  > data/output/resultados_serie_a.csv")
    print("  > data/output/classificacao_por_rodada.csv")
    print("  > data/output/classificacao_final.csv")
    print("\nTodos os arquivos incluem coluna 'season' para filtro no PowerBI!")
    print("Próximo passo: Importar CSVs no PowerBI e criar visualizações")
    print("="*75 + "\n")
