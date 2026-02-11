# Futebas - Série A Brasil Data Collection

Coleta dados da **Série A Brasil** (2022-2024) da API [API-Sports Football](https://www.api-football.com/) com cache inteligente e exporta para CSV pronto para **PowerBI**.

**Dados preparados:**
- 1140 jogos (resultados + placar)
- 2280 rodadas (classificação por rodada)  
- 60 standings finais

Coluna `season` em todos para filtro no PowerBI.

## Instalação

```bash
git clone https://github.com/seu-usuario/Futebas.git
cd Futebas
pip install -r requirements.txt
cp .env.example .env
# Edite .env e adicione sua API key
```

## Uso

```bash
cd src
python collect_multi_season.py
```

**Output:** `data/output/*.csv`

## Scripts

- `collect_multi_season.py` - Principal (2022-2024 com cache)
- `gerar_classificacao_rodada.py` - Reconstrói rodadas da rodada
- `main.py` - Versão v1 (reference)

**Detalhes técnicos, exemplos de dados e explicações estão nos comentários do código.**

## API Setup

Obtér sua chave: [API-Sports Football](https://www.api-football.com/) (plano free = 100 req/dia)

Veja [docs/API_SETUP.md](docs/API_SETUP.md) para endpoints e troubleshooting.

## Estrutura

```
src/             # Python scripts (comentados)
data/
  ├── output/    # CSV exportados
  └── cache/     # JSON (local)
docs/API_SETUP.md
```

**Status:** Ativo | **Última atualização:** Fevereiro 2026
