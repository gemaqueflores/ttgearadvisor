# Table Tennis Gear Advisor

App mobile para analise tecnica do setup atual de atletas de tenis de mesa.

## Documento oficial

- `PROJECT_PROMPT.md`: prompt congelado oficial do projeto na versao `1.8`
- `PROJECT_PROMPT_V1_3.md`: historico anterior, mantido apenas como referencia

## Escopo atual do MVP

- analisar o perfil do atleta
- analisar a lamina e as borrachas atualmente em uso
- identificar pontos positivos, limitacoes e riscos
- nao recomendar novos equipamentos nesta fase

## Estrutura do repositorio

- `app/`: Expo + React Native + TypeScript
- `backend/`: FastAPI + motor local heuristico + integracao futura com Sonnet
- `etl/`: scraping, normalizacao, merge e validacao
- `data/raw/`: JSONs persistidos por fonte
- `data/unified/`: JSONs persistidos unificados

## Regra de ouro dos dados

Os JSONs persistidos em `data/raw/` e `data/unified/` devem conter apenas dados obtidos diretamente das fontes.

Pode persistir:

- valores observados em Revspin, LARC e fabricantes
- textos declarados pelo fabricante
- medidas, dureza, peso, composicao e ratings observados

Nao pode persistir:

- equivalencias calculadas
- categorias tecnicas inferidas
- compatibilidade inferida
- faixa de preco derivada
- completude derivada
- qualquer recomendacao de uso

Toda inferencia deve acontecer em memoria no backend, no momento da analise.

## Estado atual

- scaffold mobile criado com `expo-router`
- base de i18n criada com `i18next` e `expo-localization`
- backend FastAPI funcional com endpoint `POST /analyze`
- MVP atual retorna analise do perfil e do setup atual
- RevSpin real ja foi adicionado em `data/raw/`
- a LARC real ja pode ser obtida automaticamente pelo ETL, mas o casamento completo com RevSpin e fabricantes ainda esta em consolidacao
- fabricantes ainda estao em fase de consolidacao: a estrutura de ETL existe, mas a cobertura real ainda nao esta completa
- o merge ativo usa `LARC + Revspin + fabricante`, respeitando o que de fato estiver populado em cada fonte

## Como rodar

### App mobile

```bash
cd app
npm install
set EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
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

### ETL

```bash
cd etl
pip install -r requirements.txt
python normalize.py --brand "DHS" --model "Hurricane III"
```

## Fase 1 atual: prioridade LARC

O Revspin ja esta disponivel em `data/raw/`.

A LARC e a base da verificacao de conformidade das borrachas no MVP e vira filtro hard apenas para sugestoes de borracha na v1.0. Laminas nao passam por verificacao LARC.

### Modo automatico

O script tenta primeiro o PDF oficial trimestral da FFTT com URL construida automaticamente. Se o PDF do trimestre atual nao existir, ele tenta o trimestre anterior. Se ambos falharem, ativa fallback via Playwright na SPA `equipment.ittf.com`.

```bash
cd etl
python scrape_larc.py --mode auto
```

### Modo PDF

Usa apenas a estrategia do PDF da FFTT:

```bash
cd etl
python scrape_larc.py --mode pdf --year 2026 --month 1
```

### Modo Playwright

Usa apenas o fallback da SPA:

```bash
cd etl
python scrape_larc.py --mode playwright
```

### Saida

Saida padrao:

- `data/raw/larc_whitelist.json`

O JSON da LARC agora agrega cores por produto, inclui `scraped_at` e contem apenas borrachas.

### Observacao de execucao

Para usar o fallback Playwright pela primeira vez:

```bash
cd etl
pip install -r requirements.txt
python -m playwright install chromium
```

### Modo manual local

Se precisar depurar com um arquivo local especifico, use o parser antigo de arquivo exportado:

```bash
python -c "from pathlib import Path; import io, requests; Path(r'..\\data\\raw\\larc_source.pdf').write_bytes(requests.get('https://www.fftt.com/wp-content/uploads/2026/01/liste-des-revetements-autorises-2026.pdf', timeout=30).content)"
```

O fluxo principal do projeto, porem, nao depende de URL manual nem de input manual.

## Fabricantes

O scraping de fabricantes usa configuracao versionada em `etl/manufacturer_configs.json`.

Execucao:

```bash
cd etl
python scrape_manufacturers.py --config manufacturer_configs.json
python merge.py
```

As fontes de fabricantes podem ser:

- URLs HTTPS reais
- HTML local salvo para desenvolvimento incremental

Hoje o scraping real ja existe para alguns casos de laminas, mas a cobertura de borrachas ainda esta em consolidacao. A existencia dos arquivos `fabricante_*.json` e `larc_whitelist.json` nao implica que a base real ja esteja completa.

## Fixtures de validacao

Para validar o ETL sem depender das fontes externas:

```bash
python etl/scrape_manufacturers.py --include-disabled
python etl/scrape_ttgearlab.py --include-disabled
python etl/scrape_megaspin.py --include-disabled
python etl/merge.py --larc etl/fixtures/larc_sample.json --revspin-blades etl/fixtures/revspin_blade_sample.json --revspin-rubbers etl/fixtures/revspin_rubber_sample.json
python etl/validate.py
```

## Automacao n8n

Arquivos de referencia:

- `docs/n8n-larc-quarterly-workflow.md`
- `docs/n8n-larc-quarterly-workflow.json`

## Proximo passo

Seguir a Fase 1 do prompt v1.7 nesta ordem:

1. consolidar `data/raw/larc_whitelist.json` com fonte real
2. validar o fallback Playwright em ambiente com Chromium instalado
3. ampliar scraping real de fabricantes
4. manter o merge unificado fiel ao contrato persistido
