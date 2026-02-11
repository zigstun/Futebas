# API-Football Setup Guide

## O que é API-Sports Football?

[API-Sports Football](https://www.api-football.com/) fornece dados históricos e em tempo real de ligas de futebol mundiais.

Plano **free**:
- 100 requisições por dia
- 10 requisições por minuto
- Dados históricos completos
- Suporte por email

## Obter sua API Key

### 1. Criar conta

1. Acesse [https://www.api-football.com/](https://www.api-football.com/)
2. Clique em "Sign Up"
3. Preencha email e senha
4. Confirme seu email

### 2. Copiar sua chave

1. Faça login
2. Vá para "Dashboard"
3. Procure por "API Key"
4. Copie a chave (exemplo: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

### 3. Adicionar ao projeto

```bash
# Copie .env.example para .env
cp .env.example .env

# Edite .env e cole sua chave
API_KEY=sua_chave_aqui
```

## Endpoints Utilizados

### 1. `/teams` - Listar times

**Objetivo**: Obter lista de times participantes de uma liga

**Parâmetros**:
- `league`: ID da liga (71 para Série A Brasil)
- `season`: Ano (ex: 2024)

**Resposta**:
```json
{
  "response": [
    {
      "team": {
        "id": 120,
        "name": "Botafogo",
        "country": "Brazil",
        "founded": 1894,
        "national": false
      }
    },
    ...
  ]
}
```

**Requisições**: 1 por season

---

### 2. `/fixtures` - Listar jogos

**Objetivo**: Obter todos os jogos (matchs) de uma temporada

**Parâmetros**:
- `league`: ID da liga (71)
- `season`: Ano (ex: 2024)

**Resposta**:
```json
{
  "response": [
    {
      "fixture": {
        "id": 1180355,
        "date": "2024-04-13T21:30:00+00:00",
        "status": {"short": "FT", "long": "Match Finished"}
      },
      "league": {
        "id": 71,
        "name": "Série A",
        "round": "Regular Season - 1"
      },
      "teams": {
        "home": {"id": 262, "name": "Internacional"},
        "away": {"id": 274, "name": "Bahia"}
      },
      "goals": {
        "home": 2,
        "away": 1
      }
    },
    ...
  ]
}
```

**Requisições**: 1 por season

---

### 3. `/standings` - Classicação final

**Objetivo**: Obter classificação oficial da liga

**Parâmetros**:
- `league`: ID da liga (71)
- `season`: Ano (ex: 2024)

**Resposta**:
```json
{
  "response": [
    {
      "league": {
        "id": 71,
        "name": "Série A",
        "standings": [
          [
            {
              "rank": 1,
              "team": {"id": 120, "name": "Botafogo"},
              "points": 76,
              "goals": {"for": 57, "against": 28},
              "all": {
                "played": 38,
                "win": 22,
                "draw": 10,
                "lose": 6
              }
            },
            ...
          ]
        ]
      }
    }
  ]
}
```

**Requisições**: 1 por season

---

## Estratégia de Requisições

### Problema
- Plano free = 100 requisições/dia
- Coletar 2022, 2023, 2024 = 3 years × 3 endpoints = 9 requisições mínimo

### Solução: Cache

```
Execução 1: 3 requisições (2024)
└─ Dados salvos em cache/season_2024_*.json

Execução 2: 0 requisições
└─ Lê do cache (sem gastar requisição!)

Execução 3: 3 requisições (2023)
└─ Dados salvos em cache/season_2023_*.json

...
```

**Resultado**: Múltiplas executives, mesmos dados, zero desperdício!

---

## Status Codes

No campo `status.short`:

| Código | Significado |
|--------|------------|
| `TBD` | To Be Determined (ainda não começou) |
| `1H` | Primeiro tempo |
| `HT` | Intervalo |
| `2H` | Segundo tempo |
| `ET` | Prorrogação |
| `BT` | Verificação de vídeo (VAR) |
| `P` | Pênalti (VAR) |
| `FT` | Fim do jogo |
| `AET` | Fim com prorrogação |
| `PEN` | Decidido por pênalti |
| `CANC` | Cancelado |
| `ABD` | Abandonado |
| `AWD` | Prêmio por walk-over |
| `WO` | Walk-over |
| `LIVE` | Ao vivo |

**No script usamos**: `status in ['FT', 'AET']` (apenas jogos finalizados)

---

## Troubleshooting

### Erro: "Invalid API Key"

```
❌ [ERRO] {"errors": ["invalid_key"]}
```

**Solução**:
1. Verifique se `.env` existe
2. Verifique se `API_KEY` está correto (sem espaços)
3. Teste manualmente:

```bash
curl -H "x-apisports-key: SEU_API_KEY" \
  "https://v3.football.api-sports.io/fixtures?league=71&season=2024" \
  | head -20
```

### Erro: "Too many requests"

```
❌ [ERRO] {"errors": ["requests_delay_2"]}
```

**Solução**:
- Aguarde 1 minuto (10 req/minuto é o limite)
- Script já aguarda 1s entre requisições

### Erro: "Account expired"

```
❌ [ERRO] {"errors": ["account_expired"]}
```

**Solução**:
- Chave expirou (renovar em dashboard)
- Ou limite diário atingido (espera até meia-noite UTC)

---

## Limite de Requisições

API-Sports impõem 2 limites:

### 1. Por Minuto
- **Free**: 10 requisições/minuto
- Script aguarda 1s entre requisições (30 req/30 seg)

### 2. Por Dia
- **Free**: 100 requisições/dia
- Reseta à meia-noite UTC (17h Brasília)

### Calculadora

```
Seasons: 3 (2022, 2023, 2024)
Endpoints: 3 (/teams, /fixtures, /standings)
Total: 3 × 3 = 9 requisições

Saldo diário: 100 - 9 = 91 requisições
```

Você ainda teria 91 requisições para:
- Coletar season adicional (2025): 3 req
- Testes e debug: ~30 req
- Futuro (estatísticas de players): ~20 req

---

## Próximos Passos

1. ✅ Obter API Key
2. ✅ Adicionar a `.env`
3. ✅ Executar `collect_multi_season.py`
4. ✅ Verificar `data/output/*.csv`
5. ✅ Importar em PowerBI

## Links Úteis

- [API Docs Completa](https://www.api-football.com/documentation)
- [League IDs](https://www.api-football.com/documentation#tag/Leagues)
- [Série A Brasil - League 71](https://www.api-football.com/#league-details=71)
- [Dashboard](https://www.api-football.com/dashboard)
