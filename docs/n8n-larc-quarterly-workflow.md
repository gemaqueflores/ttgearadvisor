# n8n — LARC Quarterly Refresh

Cron sugerido:

```text
0 8 5 1,4,7,10 *
```

Execucao:

1. `python etl/scrape_larc.py --mode auto`
2. se sucesso, `python etl/merge.py`
3. notificar Slack ou email com total de registros

## Estrutura recomendada do workflow

### Node 1 — Cron

- tipo: `Schedule Trigger`
- expressao: `0 8 5 1,4,7,10 *`

### Node 2 — Execute Command: scrape_larc

```bash
python etl/scrape_larc.py --mode auto
```

### Node 3 — IF

- condicao: comando anterior executou com sucesso

### Node 4 — Execute Command: merge

```bash
python etl/merge.py
```

### Node 5 — Notify

- enviar total de registros atualizados
- sugerido: Slack, email ou webhook interno

## Observacao

Se o fallback Playwright for usado no servidor, garantir que o ambiente tenha:

```bash
python -m playwright install chromium
```
