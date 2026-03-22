# Table Tennis Gear Advisor

Repositório inicial do app mobile de recomendação técnica de equipamentos para tênis de mesa.

## Estrutura

- `app/`: Expo + React Native + TypeScript
- `backend/`: FastAPI + integração futura com Sonnet
- `etl/`: scripts de scraping, normalização e merge
- `data/`: datasets brutos e unificados
- `PROJECT_PROMPT_V1_3.md`: documento congelado do projeto

## Estado atual

- Scaffold mobile criado com `expo-router`
- Base de i18n criada com `i18next` e `expo-localization`
- Scaffold do backend FastAPI preparado
- Scaffold do pipeline ETL preparado
- Docker Compose raiz alinhado com PostgreSQL + API + n8n

## Como começar

### App mobile

```bash
cd app
npm install
npm start
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Próximo passo recomendado

Começar pela Fase 1 do prompt congelado:

1. Implementar `etl/scrape_larc.py`
2. Criar `etl/aliases.json`
3. Definir modelos Pydantic no backend
4. Preparar contrato do endpoint `POST /analyze`
