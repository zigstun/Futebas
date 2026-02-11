"""
GERAR_CLASSIFICACAO_RODADA.PY
=============================

Script para RECONSTRUIR classificação por rodada a partir dos fixtures coletados.

Diferencial:
- Usa dados EM CACHE (zero requisições à API)
- Processa 380 fixtures e reconstrói 38 rodadas
- Útil para dashboards que mostram evolução

Lógica:
1. Carrega fixtures já coletados do cache
2. Processa em ordem cronológica
3. Mantém stats cumulativas de cada time
4. Salva snapshot após cada rodada completar
5. Exporta CSV com 38 rodadas × 20 times = 760 linhas

Uso:
    python gerar_classificacao_rodada.py

Output:
    ../data/output/classificacao_por_rodada.csv (2280 linhas para 3 seasons)

Autoria: Seu Nome
Data: Fevereiro 2026
"""

import json
import csv
import os
from collections import defaultdict

# ============= CONFIGURAÇÕES =============

CACHE_DIR = "cache"          # Onde estão os fixtures em JSON
OUTPUT_DIR = "output"        # Onde salvar o CSV
SEASONS = [2022, 2023, 2024] # Seasons disponíveis

# ============= FUNÇÕES =============

def load_fixtures(season):
    """
    Carrega fixtures de uma season do cache.
    
    Args:
        season (int): Ano da temporada
    
    Returns:
        list: Array de fixtures ou [] se não existir/falhar
    
    Exemplo de fixture:
        {
            "fixture": {"id": 123, "date": "2024-04-09", "status": {"short": "FT"}},
            "teams": {"home": {"id": 1, "name": "Botafogo"}, "away": {...}},
            "goals": {"home": 2, "away": 1},
            "league": {"round": "Regular Season - 1"}
        }
    """
    cache_file = os.path.join(CACHE_DIR, f"season_{season}_fixtures.json")
    
    if not os.path.exists(cache_file):
        print(f"❌ Cache não encontrado: {cache_file}")
        return []
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            fixtures = data.get('response', [])
            print(f"✓ Carregado: {len(fixtures)} fixtures de {season}")
            return fixtures
    except Exception as e:
        print(f"❌ Erro ao ler cache {season}: {e}")
        return []

def load_teams(season):
    """
    Carrega times de uma season do cache.
    
    Args:
        season (int): Ano da temporada
    
    Returns:
        dict: Mapeamento {team_id: team_name}
    
    Exemplo:
        {
            120: "Botafogo",
            1: "Juventude",
            ...
        }
    """
    cache_file = os.path.join(CACHE_DIR, f"season_{season}_teams.json")
    
    if not os.path.exists(cache_file):
        print(f"❌ Times não encontrados: {cache_file}")
        return {}
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            teams = data.get('response', [])
            
            # Mapear ID -> Nome
            teams_dict = {}
            for team_info in teams:
                team = team_info.get('team', {})
                teams_dict[team['id']] = team['name']
            
            print(f"✓ Carregado: {len(teams_dict)} times de {season}")
            return teams_dict
    except Exception as e:
        print(f"❌ Erro ao ler times {season}: {e}")
        return {}

def generate_classificacao_rodada(fixtures, teams_dict, season):
    """
    Reconstrói classificação por rodada a partir dos fixtures.
    
    Algoritmo:
    1. Inicializa stats de todos os times em 0
    2. Ordena fixtures por data
    3. Para cada fixture finalizado:
       - Atualiza stats dos 2 times
       - Salva snapshot da classificação para essa rodada
    4. Retorna lista de registros para CSV
    
    Desempates usados: Pontos > Gols a favor - Gols contra
    
    Args:
        fixtures (list): Lista de fixtures carregado do cache
        teams_dict (dict): Mapeamento {id: name}
        season (int): Ano para adicionar coluna season
    
    Returns:
        list: Registros com estrutura pronta para CSV
    
    Registro exemplo:
        {
            'season': 2024,
            'round': 'Regular Season - 1',
            'position': 1,
            'team_id': 120,
            'team_name': 'Botafogo',
            'played': 1,
            'wins': 1,
            'draws': 0,
            'losses': 0,
            'goals_for': 3,
            'goals_against': 0,
            'goal_diff': 3,
            'points': 3
        }
    """
    
    # Estrutura para armazenar stats cumulyativos de cada time
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
    
    # Inicializar todos os times com seus nomes
    for team_id, team_name in teams_dict.items():
        team_stats[team_id]['name'] = team_name
    
    # ===== PROCESSAR FIXTURES EM ORDEM CRONOLÓGICA =====
    print(f"\nProcessando {len(fixtures)} fixtures...")
    
    processed = 0
    for fixture in sorted(fixtures, key=lambda x: x.get('fixture', {}).get('date', '')):
        try:
            # Extrair informações do fixture
            fixture_info = fixture.get('fixture', {})
            league = fixture.get('league', {})
            round_name = league.get('round', 'Unknown')
            
            # Status pode ser dict ou string - normalizar
            status_obj = fixture_info.get('status', {})
            if isinstance(status_obj, dict):
                status = status_obj.get('short', '')
            else:
                status = status_obj
            
            # Verificar se jogo foi finalizado
            # FT = Full Time, AET = After Extra Time
            if status not in ['FT', 'AET']:
                continue
            
            # Extrair dados dos times
            teams = fixture.get('teams', {})
            goals = fixture.get('goals', {})
            
            home_team_id = teams.get('home', {}).get('id')
            away_team_id = teams.get('away', {}).get('id')
            home_goals = goals.get('home')
            away_goals = goals.get('away')
            
            # Validar dados
            if not all([home_team_id, away_team_id, home_goals is not None, away_goals is not None]):
                continue
            
            # ===== ATUALIZAR STATS DOS TIMES =====
            
            # Mandante
            team_stats[home_team_id]['played'] += 1
            team_stats[home_team_id]['goals_for'] += home_goals
            team_stats[home_team_id]['goals_against'] += away_goals
            
            # Visitante
            team_stats[away_team_id]['played'] += 1
            team_stats[away_team_id]['goals_for'] += away_goals
            team_stats[away_team_id]['goals_against'] += home_goals
            
            # Determinar resultado e atualizar pontos
            if home_goals > away_goals:
                # Mandante venceu
                team_stats[home_team_id]['wins'] += 1
                team_stats[home_team_id]['points'] += 3
                team_stats[away_team_id]['losses'] += 1
            elif home_goals < away_goals:
                # Visitante venceu
                team_stats[away_team_id]['wins'] += 1
                team_stats[away_team_id]['points'] += 3
                team_stats[home_team_id]['losses'] += 1
            else:
                # Empate
                team_stats[home_team_id]['draws'] += 1
                team_stats[home_team_id]['points'] += 1
                team_stats[away_team_id]['draws'] += 1
                team_stats[away_team_id]['points'] += 1
            
            # Salvar snapshot da classificação após essa rodada
            if round_name not in standings_by_round:
                standings_by_round[round_name] = {}
                # Copiar stats atuais de todos os times
                for team_id, stats in team_stats.items():
                    standings_by_round[round_name][team_id] = dict(stats)
            
            processed += 1
        
        except Exception as e:
            print(f"⚠️  Erro ao processar fixture: {e}")
            continue
    
    print(f"✓ Processados {processed} fixtures")
    
    # ===== CONVERTER PARA FORMATO DE LINHAS PARA CSV =====
    all_rows = []
    
    # Ordenar rodadas numericamente
    sorted_rounds = sorted(
        standings_by_round.keys(),
        key=lambda x: int(x.split('-')[-1].strip()) if '-' in x else 0
    )
    
    for round_name in sorted_rounds:
        standings = standings_by_round[round_name]
        
        # Ordenar times por: Pontos DESC -> Diferença de gols DESC
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (
                x[1]['points'],
                x[1]['goals_for'] - x[1]['goals_against']
            ),
            reverse=True
        )
        
        # Adicionar cada time com sua posição
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
    
    print(f"✓ Geradas {len(all_rows)} linhas ({len(sorted_rounds)} rodadas)")
    return all_rows

def export_to_csv(all_rows, filename):
    """
    Exporta lista de registros para arquivo CSV.
    
    Args:
        all_rows (list): Registros a exportar
        filename (str): Nome do arquivo de saída
    
    Returns:
        bool: True se sucesso, False se falhar
    """
    if not all_rows:
        print(f"❌ Sem dados para exportar {filename}")
        return False
    
    # Criar pasta se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = all_rows[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"✓ Exportado: {output_path} ({len(all_rows)} linhas)")
        return True
    
    except Exception as e:
        print(f"❌ Erro ao exportar {filename}: {e}")
        return False

# ============= MAIN - EXECUÇÃO PRINCIPAL =============

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GENERATOR: CLASSIFICAÇÃO POR RODADA")
    print("="*80)
    print("\nEste script reconstrói a classificação para cada rodada usando")
    print("dados JÁ EM CACHE (zero requisições à API)")
    
    # Coletar dados de todas as seasons
    all_rodadas = []
    
    print("\n" + "="*80)
    print("CARREGANDO DADOS DO CACHE...")
    print("="*80)
    
    for season in SEASONS:
        print(f"\n[{season}]")
        
        # Carregar fixtures e times do cache
        fixtures = load_fixtures(season)
        teams_dict = load_teams(season)
        
        if not fixtures or not teams_dict:
            print(f"⚠️  Pulando {season} - dados incompletos")
            continue
        
        # Gerar classificação por rodada
        season_rows = generate_classificacao_rodada(fixtures, teams_dict, season)
        all_rodadas.extend(season_rows)
    
    # Exportar resultado consolidado
    print("\n" + "="*80)
    print("EXPORTANDO RESULTADO...")
    print("="*80)
    
    if all_rodadas:
        export_to_csv(all_rodadas, 'classificacao_por_rodada.csv')
    else:
        print("❌ Nenhum dado para exportar")
    
    # Resumo
    print("\n" + "="*80)
    print("CONCLUÍDO!")
    print("="*80)
    for season in SEASONS:
        rodadas_count = len(set(r['round'] for r in all_rodadas if r['season'] == season))
        if rodadas_count > 0:
            print(f"\n{season}: {rodadas_count} rodadas")
    
    print(f"\nTotal: {len(all_rodadas)} registros (rodadas × times × seasons)")
    print("\nPróximos passos:")
    print("1. Abra o CSV em Excel/PowerBI")
    print("2. Crie gráficos de evolução por rodada")
    print("3. Compare seasons lado a lado")
    print("="*80 + "\n")
