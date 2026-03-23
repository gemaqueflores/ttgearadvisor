# Table Tennis Gear Advisor — Project Prompt
## Versao 1.8 — CONGELADO DEFINITIVO
> Fusao: prompt tecnico (Sonnet v1.1) + prompt operacional (Codex v1.1)
> v1.8: AnalysisConfidence no output + limiares realistas de cobertura para o MVP
> Data: 20/03/2026 | Autor: Leo (lfsystems) | Belem, PA, Brasil

---

## 1. Visao Geral

Desenvolver um **app mobile nativo multi-language (Android + iOS)** que analisa o perfil tecnico e o setup atual de atletas de tenis de mesa com base em dados tecnicos objetivos de datasets especializados.

> **Escopo MVP:** apenas analise do setup atual.
> Recomendacoes de novos equipamentos serao implementadas na v1.0.

O app e um **motor de compatibilidade tecnica**:
- cruza atributos numericos dos equipamentos atuais do atleta com seu perfil tecnico
- gera analise tecnica detalhada do setup atual
- identifica pontos fortes, limitacoes e riscos do equipamento em uso

**Diferencial central:** nao existe produto equivalente no mercado com foco em analise tecnica objetiva do setup do atleta. A analise e baseada exclusivamente em atributos numericos dos datasets, nao em opiniao subjetiva, estoque ou loja.

---

## 2. Stack Tecnologica — Confirmada

| Camada | Tecnologia | Observacao |
|---|---|---|
| App Mobile | Expo + React Native + TypeScript | Android + iOS, unico projeto |
| Navegacao | expo-router | Estrutura moderna baseada em rotas |
| i18n | i18next + react-i18next + expo-localization | pt-BR no lancamento |
| Backend / API | Python + FastAPI | Separado do app mobile |
| Orquestracao | n8n self-hosted | Nova VM Oracle Cloud |
| LLM MVP | Claude Sonnet 4.6 — Anthropic API direta | Quando a analise via LLM for ativada |
| LLM v1.1+ | Gemini Flash + Sonnet | Quando dataset crescer |
| Banco de dados | PostgreSQL | Schema `tt_advisor` — nova VM |
| Infra backend | Oracle Cloud Free Tier ARM | Nova instancia exclusiva |
| Build mobile | EAS Build | Cloud build — funciona em Windows para iOS |
| Publicacao | EAS Submit → Google Play + App Store | Lojas oficiais |

### O que NAO fazer
- Nao usar Next.js como frontend principal do produto
- Nao usar `next-i18next`
- Nao usar Capacitor no MVP
- Nao depender de Vercel como frontend do produto
- Nao compartilhar VM, banco ou servicos com o projeto anterior
- Nao tratar o app como web app adaptado para mobile

### Custos de publicacao
- Google Play: taxa unica de US$25
- Apple App Store: US$99/ano
- EAS Build iOS: funciona em Windows via cloud build

---

## 3. Contexto do Desenvolvedor

- Desenvolvedor fullstack: Oracle PL/SQL, PHP, Python, JavaScript/TypeScript
- Atleta federado de tenis de mesa — empunhadura classineta, estilo ofensivo/topspin
- MEI ativo — CNPJ `65.808.344/0001-77`
- Amazon Associados ID: `lfsystems-20`
- Projeto anterior separado: `pingpongpaidegua.vercel.app`
- VM Oracle Cloud existente de outro projeto **nao deve ser reutilizada**

---

## 4. Fluxo Principal do Usuario

```text
1. Usuario abre o app
2. Usuario preenche perfil do atleta + setup atual
3. App envia payload ao backend (FastAPI)
4. Backend consulta o dataset unificado para localizar os equipamentos atuais
5. Backend monta contexto tecnico do setup atual
6. Backend gera analise estruturada
7. App exibe resultado em 2 blocos:
   ├── Analise do perfil
   └── Analise do setup atual
```

> Recomendacoes e roadmap ficam para a v1.0.

---

## 5. Campos do Perfil do Atleta

### Dados de jogo
- Nivel: `iniciante` / `intermediario` / `avancado` / `federado`
- Estilo: `ofensivo` / `defensivo` / `all-round`
- Empunhadura: `shakehand` / `penhold-classico` / `classineta`
- Lado dominante: `destro` / `canhoto`
- Pontos fortes (multi-select)
- Pontos fracos (multi-select)
- Frequencia: `ocasional` / `1-2x/semana` / `3-4x/semana` / `diario` / `federado`

### Material atual
- Lamina: marca + modelo
- Borracha FH: marca + modelo + espessura
- Borracha BH: marca + modelo + espessura (ou `dorso-liso` para penhold classico)
- Tempo de uso do setup atual

### Historico
- Materiais anteriores (campo livre)
- Problemas sentidos com o setup atual (multi-select + campo livre)
- Objetivo: `mais-velocidade` / `mais-spin` / `mais-controle` / `equilibrio` / `competicao-federada`

---

## 6. Output da IA — MVP

### Schema JSON de retorno do Sonnet

```json
{
  "analise_perfil": {
    "resumo": "string",
    "compatibilidade_estilo_nivel": "string",
    "pontos_atencao": ["string"]
  },
  "analise_setup_atual": {
    "lamina": {
      "confianca": "alta|media|baixa|insuficiente",
      "campos_utilizados": ["string"],
      "campos_ausentes": ["string"],
      "avaliacao": "string",
      "pontos_positivos": ["string"],
      "limitacoes": ["string"]
    },
    "borracha_fh": {
      "confianca": "alta|media|baixa|insuficiente",
      "campos_utilizados": ["string"],
      "campos_ausentes": ["string"],
      "avaliacao": "string",
      "aprovado_competicao": "boolean",
      "alerta_larc": "string|null",
      "pontos_positivos": ["string"],
      "limitacoes": ["string"]
    },
    "borracha_bh": {
      "confianca": "alta|media|baixa|insuficiente",
      "campos_utilizados": ["string"],
      "campos_ausentes": ["string"],
      "avaliacao": "string",
      "aprovado_competicao": "boolean",
      "alerta_larc": "string|null",
      "pontos_positivos": ["string"],
      "limitacoes": ["string"]
    },
    "sinergia_combinacao": "string",
    "riscos": ["string"]
  }
}
```

### Fora do escopo do MVP
- `recomendacoes[]`
- `roadmap`

---

## 7. Arquitetura de Dados

### 7.1 Fontes

| Fonte | Conteudo | Metodo | Prioridade |
|---|---|---|---|
| Revspin ✅ ja disponivel | velocidade, spin, controle, dureza, avaliacao | JSON disponivel | Base principal |
| LARC ITTF | lista oficial trimestral de borrachas autorizadas | PDF → pdfplumber | Verificacao obrigatoria de conformidade |
| Fabricantes (DHS, Tibhar, Donic, Butterfly, Yasaka, Andro, Nittaku, Xiom, Joola) | composicao declarada, peso, dimensoes, espessuras, dureza | scraping HTML / Puppeteer | Alta |
| TTGearLab | Ep/Ec, Vp/Vl, frequencia Hz | scraping HTML | Alta |
| Megaspin | ratings normalizados, peso | scraping HTML estatico | Media |
| TT Reviews | peso real, dimensoes fisicas | scraping HTML | Media |

### 7.2 Papel do LARC por fase

```text
MVP:
- o atleta pode declarar qualquer equipamento
- a LARC e consultada no enriquecimento apenas das borrachas
- se a borracha nao constar na LARC vigente, o output informa irregularidade para competicoes federadas

v1.0:
- a LARC passa a ser filtro hard apenas para sugestoes de borracha
- nenhuma borracha nao aprovada entra nas recomendacoes
```

### 7.3 Regra critica de persistencia

> Os JSONs persistidos do pipeline devem conter **apenas conteudo obtido diretamente das fontes.**

**Pode persistir:**
- valores observados em Revspin, LARC e fabricantes
- textos e composicao declarada pelo fabricante
- peso, medidas, dureza e ratings observados

**Nao pode persistir:**
- equivalencias calculadas
- categorias tecnicas inferidas
- recomendacoes de uso inferidas
- score, compatibilidade, faixa de preco derivada ou completude derivada
- qualquer leitura "interpretada" como verdade do dataset

> **Toda inferencia deve acontecer em memoria no backend, no momento da analise.**

---

## 8. Schemas Persistidos

### `revspin_blade.json` ✅ disponivel — 3.630 registros
```json
{
  "source": "revspin",
  "source_id": "string",
  "marca": "string",
  "modelo": "string",
  "url": "string",
  "velocidade": "float|null",
  "controle": "float|null",
  "rigidez": "float|null",
  "avaliacao_geral": "float|null",
  "preco_medio_usd": "float|null",
  "scraped_at": "date"
}
```

### `revspin_rubber.json` ✅ disponivel — 2.603 registros
```json
{
  "source": "revspin",
  "source_id": "string",
  "marca": "string",
  "modelo": "string",
  "url": "string",
  "velocidade": "float|null",
  "spin": "float|null",
  "controle": "float|null",
  "dureza_esponja": "float|null",
  "decepcao": "float|null",
  "avaliacao_geral": "float|null",
  "preco_medio_usd": "float|null",
  "scraped_at": "date"
}
```

### `fabricante_blade.json`
```json
{
  "source": "fabricante",
  "source_url": "string",
  "marca": "string",
  "modelo": "string",
  "fisica": {
    "peso_g": "float|null",
    "espessura_mm": "float|null",
    "largura_mm": "float|null",
    "altura_mm": "float|null",
    "cabos_disponiveis": ["string"]
  },
  "composicao": {
    "total_camadas": "int|null",
    "estrutura": ["object"],
    "tem_carbono": "boolean|null",
    "tipo_carbono": "string|null",
    "posicao_carbono": "outer|inner|null",
    "camadas_carbono": "int|null",
    "fibra_especial": "string|null"
  },
  "scraped_at": "date"
}
```

### `fabricante_rubber.json`
```json
{
  "source": "fabricante",
  "source_url": "string",
  "marca": "string",
  "modelo": "string",
  "tipo": "IN|OUT|LONG|ANTI",
  "fisica": {
    "espessuras_disponiveis_mm": ["float|MAX"],
    "dureza_esponja_graus": "float|null",
    "escala_dureza": "chinesa|europeia|japonesa|null",
    "peso_por_espessura_g": "object|null",
    "diametro_topsheet_mm": "float|null"
  },
  "aprovacao_ittf_declarada": "boolean",
  "scraped_at": "date"
}
```

### `larc_whitelist.json`
```json
{
  "source": "ittf_larc",
  "versao": "YYYY-MM",
  "marca": "string",
  "modelo": "string",
  "codigo_ittf": "string",
  "tipo": "IN|OUT|LONG|ANTI",
  "aprovado": "boolean",
  "valido_desde": "YYYY-MM",
  "valido_ate": "YYYY-MM|null"
}
```

### `unified_blade.json`
```json
{
  "id": "marca-modelo-normalizado",
  "meta": {
    "marca": "string",
    "modelo": "string",
    "categoria": "blade",
    "codigo_ittf": "string|null",
    "fontes_disponiveis": ["string"],
    "ultima_atualizacao": "date|null"
  },
  "fisica": {
    "peso_g": "float|null",
    "espessura_mm": "float|null",
    "largura_mm": "float|null",
    "altura_mm": "float|null",
    "cabos_disponiveis": ["string"]
  },
  "composicao": {
    "total_camadas": "int|null",
    "estrutura": ["object"],
    "tem_carbono": "boolean|null",
    "tipo_carbono": "string|null",
    "posicao_carbono": "outer|inner|null",
    "camadas_carbono": "int|null",
    "fibra_especial": "string|null"
  },
  "ratings": {
    "velocidade_revspin": "float|null",
    "controle_revspin": "float|null",
    "rigidez_revspin": "float|null",
    "avaliacao_geral_revspin": "float|null",
    "velocidade_megaspin": "float|null",
    "controle_megaspin": "float|null"
  },
  "lab": {
    "Ep": "float|null",
    "Ec": "float|null",
    "Vp": "float|null",
    "Vl": "float|null",
    "frequencia_hz": "float|null"
  },
  "preco": {
    "medio_usd": "float|null"
  },
  "urls": {
    "revspin": "string|null",
    "fabricante": "string|null",
    "ttgearlab": "string|null",
    "megaspin": "string|null"
  }
}
```

### `unified_rubber.json`
```json
{
  "id": "marca-modelo-normalizado",
  "meta": {
    "marca": "string",
    "modelo": "string",
    "categoria": "rubber",
    "tipo": "IN|OUT|LONG|ANTI",
    "aprovado_larc": "boolean",
    "codigo_ittf": "string|null",
    "fontes_disponiveis": ["string"],
    "ultima_atualizacao": "date|null"
  },
  "fisica": {
    "espessuras_disponiveis_mm": ["float|MAX"],
    "dureza_esponja_graus": "float|null",
    "escala_dureza": "chinesa|europeia|japonesa|null",
    "peso_max_g": "float|null",
    "diametro_topsheet_mm": "float|null"
  },
  "ratings": {
    "velocidade_revspin": "float|null",
    "spin_revspin": "float|null",
    "controle_revspin": "float|null",
    "dureza_revspin": "float|null",
    "decepcao_revspin": "float|null",
    "avaliacao_geral_revspin": "float|null"
  },
  "lab": {
    "Ep": "float|null",
    "Ec": "float|null"
  },
  "preco": {
    "medio_usd": "float|null"
  },
  "urls": {
    "revspin": "string|null",
    "fabricante": "string|null",
    "ttgearlab": "string|null"
  }
}
```

---

## 8.1 Modelos Internos do Backend (apenas em memoria — nunca persistidos)

Campos derivados e inferencias existem **somente** no contrato interno do backend, populados em memoria durante o enriquecimento do setup. Nunca sao gravados nos JSONs do dataset.

```python
from pydantic import BaseModel
from typing import Optional

class BladeEnriched(BaseModel):
    blade: dict
    categoria_velocidade: Optional[str] = None
    tem_fibra_especial: Optional[bool] = None
    dwell_time_estimado: Optional[str] = None
    disponivel_classineta: Optional[bool] = None
    faixa_preco: Optional[str] = None

class RubberEnriched(BaseModel):
    rubber: dict
    aprovado_larc: Optional[bool] = False
    alerta_larc: Optional[str] = None
    equivalencia_dureza_europeia: Optional[float] = None
    indicado_classineta: Optional[bool] = None
    exige_tecnica: Optional[bool] = None
    faixa_preco: Optional[str] = None

class SetupEnriched(BaseModel):
    lamina: BladeEnriched
    borracha_fh: RubberEnriched
    borracha_bh: Optional[RubberEnriched] = None
```

### Regra de derivacao em memoria

| Campo derivado | Origem | Onde vive |
|---|---|---|
| `aprovado_larc` | consultado em `larc_whitelist.json` | `RubberEnriched` apenas |
| `alerta_larc` | derivado de `aprovado_larc` | `RubberEnriched` apenas |
| `categoria_velocidade` | calculado a partir de `velocidade_revspin` | `BladeEnriched` |
| `dwell_time_estimado` | calculado a partir de composicao + rigidez | `BladeEnriched` |
| `disponivel_classineta` | inferido de `cabos_disponiveis` | `BladeEnriched` |
| `faixa_preco` | calculado a partir de `preco.medio_usd` | `BladeEnriched` / `RubberEnriched` |
| `equivalencia_dureza_europeia` | calculado: `dureza_chinesa - 8` | `RubberEnriched` |
| `indicado_classineta` | inferido de tipo + estilo | `RubberEnriched` |
| `exige_tecnica` | inferido de dureza + velocidade | `RubberEnriched` |

### Confianca da analise

```python
class AnalysisConfidence(str, Enum):
    ALTA = "alta"         # ratings + dados fisicos + composicao
    MEDIA = "media"       # ratings completos, sem dados fisicos
    BAIXA = "baixa"       # ratings parciais
    INSUFICIENTE = "insuficiente"  # sem dados minimos
```

Cada peca analisada deve expor:
- `confianca`
- `campos_utilizados`
- `campos_ausentes`

---

## 9. Pipeline ETL

```text
1. LARC PDF (trimestral)
   └─ Gera: larc_whitelist.json

2. Revspin (ja disponivel)
   └─ revspin_blade.json (3.630 registros)
   └─ revspin_rubber.json (2.603 registros)

3. Scraping fabricantes
   └─ fabricante_blade.json + fabricante_rubber.json

4. Scraping TTGearLab
   └─ ttgearlab_blade.json

5. Scraping Megaspin
   └─ megaspin_blade.json

6. Normalizacao de nomes
   └─ RapidFuzz + etl/aliases.json (versionado)
   └─ ID final: kebab-case minusculo sem acentos

7. Filtros
   └─ atributos numericos minimos presentes

8. Merge por ID normalizado
   └─ Prioridade: fabricante > ttgearlab > megaspin > revspin

9. Export
   └─ unified_blade.json
   └─ unified_rubber.json
```

> ETL: gera `larc_whitelist.json` sem mudanca.
> ETL: `larc_whitelist.json` contem apenas borrachas.
> MVP: o backend consulta a LARC apenas para `borracha_fh` e `borracha_bh`.
> v1.0: a LARC vira filtro hard apenas para o pool de borrachas sugeridas.
> TTGearLab, Megaspin e TT Reviews ficam desativados no MVP e entram como enriquecimento fisico paralelo para v1.0.

---

## 10. Motor de Analise — MVP

### Enriquecimento do setup (Python)

```python
def enrich_setup(setup: dict) -> dict:
    lamina = lookup_blade(setup["lamina"]["marca"], setup["lamina"]["modelo"])
    rubber_fh = lookup_rubber(setup["borracha_fh"]["marca"], setup["borracha_fh"]["modelo"])
    rubber_bh = lookup_rubber(setup["borracha_bh"]["marca"], setup["borracha_bh"]["modelo"])
    fh_aprovado, fh_alerta = check_larc(setup["borracha_fh"]["marca"], setup["borracha_fh"]["modelo"], larc)
    bh_aprovado, bh_alerta = check_larc(setup["borracha_bh"]["marca"], setup["borracha_bh"]["modelo"], larc)
    return {
        "lamina": lamina,
        "borracha_fh": {
            "rubber": rubber_fh,
            "aprovado_larc": fh_aprovado,
            "alerta_larc": fh_alerta
        },
        "borracha_bh": {
            "rubber": rubber_bh,
            "aprovado_larc": bh_aprovado,
            "alerta_larc": bh_alerta
        }
    }
```

### Prompt base do Sonnet

```text
Voce e um especialista tecnico em equipamentos de tenis de mesa.

Perfil do atleta:
{athlete_profile}

Dados tecnicos do setup atual (extraidos do dataset):
{enriched_setup}

Responda em {user_language}.
Retorne exclusivamente JSON valido no formato {output_schema}, sem texto adicional.

Analise tecnicamente o setup atual do atleta:
- avalie a lamina individualmente
- avalie a borracha FH individualmente
- avalie a borracha BH individualmente
- avalie a sinergia da combinacao completa
- identifique pontos positivos, limitacoes e riscos

Se aprovado_competicao for false em borracha_fh ou borracha_bh,
inclua o alerta_larc correspondente na avaliacao daquela borracha.
O alerta deve aparecer de forma clara e objetiva, sem julgamento
sobre a escolha do atleta.
Laminas nao tem restricao de aprovacao ITTF — nunca incluir
alerta de irregularidade na avaliacao da lamina.

Baseie a analise exclusivamente nos atributos numericos fornecidos.
Cite valores especificos dos atributos ao justificar.

Calibre a linguagem pelo campo `confianca`:
- `alta`: afirmacoes diretas
- `media`: afirmacoes diretas sem extrapolar dados ausentes
- `baixa`: usar linguagem cautelosa como "com base nos dados disponiveis"
- `insuficiente`: explicitar que faltam dados minimos
```

### Observacao de implementacao

> No repositorio, o MVP pode usar motor local heuristico antes da ativacao do Sonnet,
> desde que mantenha o **mesmo contrato de entrada e saida** definido neste documento.

---

## 11. Internacionalizacao (i18n)

**Stack:** `i18next` + `react-i18next` + `expo-localization`

```text
src/i18n/
├── pt-BR/common.json   ← lancamento
├── en-US/common.json   ← v1.1
├── es-ES/common.json   ← v1.2
└── zh-CN/common.json   ← roadmap
```

| Fase | Idiomas |
|---|---|
| MVP | pt-BR |
| v1.1 | + en-US |
| v1.2 | + es-ES |
| Roadmap | + zh-CN |

---

## 12. Infraestrutura

```text
Oracle Cloud Free Tier ARM — nova instancia exclusiva
├── PostgreSQL   (Docker)
├── FastAPI      (Docker) — porta 8000
├── n8n          (Docker) — porta 5678
└── Nginx        (reverse proxy + SSL)

Google Play Store  ← EAS Submit
Apple App Store    ← EAS Submit
```

### Docker Compose
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tt_advisor
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      DATABASE_URL: postgresql://${PG_USER}:${PG_PASS}@postgres/tt_advisor
    depends_on:
      - postgres

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_USER}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASS}
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: tt_advisor
      DB_POSTGRESDB_USER: ${PG_USER}
      DB_POSTGRESDB_PASSWORD: ${PG_PASS}
    depends_on:
      - postgres

volumes:
  postgres_data:
```

---

## 13. Estrutura do Repositorio

```text
tt-gear-advisor/
├── app/                        ← Expo + React Native
│   ├── (tabs)/
│   │   ├── index.tsx           ← formulario de perfil
│   │   └── result.tsx          ← tela de resultado
│   ├── components/
│   └── src/
│       └── i18n/
│           ├── pt-BR/common.json
│           └── en-US/common.json
├── backend/                    ← FastAPI + Python
│   ├── main.py
│   ├── enrich.py               ← enriquecimento do setup com dataset
│   ├── llm.py                  ← integracao Sonnet (ativado quando API disponivel)
│   ├── filters.py              ← scaffold — pre-filtro de candidatos (v1.0)
│   └── requirements.txt
├── etl/                        ← scripts de scraping e merge
│   ├── scrape_larc.py
│   ├── scrape_manufacturers.py
│   ├── scrape_ttgearlab.py
│   ├── normalize.py
│   ├── merge.py
│   └── aliases.json            ← mapeamento de variacoes de nomes — versionado
├── data/
│   ├── raw/                    ← schemas por fonte
│   └── unified/                ← unified_blade.json + unified_rubber.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 14. UX Mobile

**Diretrizes:**
- fluxo curto — minimo de telas para chegar ao resultado
- campos confortaveis para toque
- leitura facil em telas pequenas
- feedback de carregamento claro
- resultado escaneavel em 30 segundos
- performance em rede movel como prioridade

**Telas minimas do MVP:**
- Splash / loading
- Formulario do perfil (multi-step se necessario)
- Loading da analise
- Resultado da analise
- Configuracoes (idioma + perfil salvo)

---

## 15. Ordem de Desenvolvimento — MVP

### Fase 0 — Infraestrutura
- [ ] Provisionar nova VM Oracle Cloud ARM
- [ ] Docker + Docker Compose
- [ ] PostgreSQL + FastAPI + n8n
- [ ] Nginx + SSL + subdominio
- [ ] `.env` e secrets

### Fase 1 — Pipeline ETL
- [ ] `scrape_larc.py` → `larc_whitelist.json`
- [ ] `scrape_manufacturers.py` → `fabricante_blade.json` + `fabricante_rubber.json`
- [ ] `scrape_ttgearlab.py` → `ttgearlab_blade.json`
- [ ] `normalize.py` + `aliases.json`
- [ ] `merge.py` → `unified_blade.json` + `unified_rubber.json`
- [ ] Validacao de cobertura minima realista para o MVP

### Limiares de cobertura do MVP
- Lâminas: `velocidade_revspin >= 70%`
- Lâminas: `controle_revspin >= 70%`
- Lâminas: `rigidez_revspin >= 40%`
- Borrachas: `velocidade_revspin >= 75%`
- Borrachas: `spin_revspin >= 75%`
- Borrachas: `controle_revspin >= 75%`
- Campos fisicos nao bloqueiam o MVP; devem ser reportados como enriquecimento adicional

### Fase 2 — Backend API
- [ ] `POST /analyze` — recebe perfil + setup
- [ ] `enrich.py` — lookup no dataset unificado
- [ ] `llm.py` — integracao Sonnet (ativada quando API disponivel)
- [ ] Validacao Pydantic do output antes de enviar ao app
- [ ] Tratamento de resposta malformada
- [ ] `GET /health`
- [ ] Testes unitarios do enriquecimento
- [ ] `filters.py` — scaffold only (v1.0)

### Fase 3 — App Mobile
- [ ] Setup Expo + React Native + TypeScript
- [ ] expo-router
- [ ] i18n (i18next + expo-localization)
- [ ] Formulario do perfil (pt-BR)
- [ ] Tela de resultado da analise
- [ ] Configuracoes (idioma + perfil salvo)
- [ ] Integracao com backend
- [ ] EAS Build Android + iOS

### Fase 4 — Integracao n8n
- [ ] Webhook do app
- [ ] Workflow: perfil → enriquecimento → analise → response
- [ ] Logging + observabilidade basica

### Fase 5 — Publicacao
- [ ] Build preview + testes
- [ ] Assets das stores
- [ ] EAS Submit → Google Play
- [ ] EAS Submit → App Store

---

## 16. Convencoes de Codigo

- **Python:** `snake_case`, type hints, docstrings em pt-BR
- **TypeScript:** `camelCase`
- **React Native:** `PascalCase`
- **JSON datasets:** `snake_case`
- **IDs normalizados:** kebab-case minusculo sem acentos
- **Commits:** portugues, Conventional Commits (`feat:`, `fix:`, `data:`, `etl:`, `chore:`)
- **Credenciais:** nunca commitar — sempre `.env.example` documentado

---

## 17. Contexto Tecnico de Tenis de Mesa

> Este contexto serve para analise tecnica — **nao** para persistir inferencias no dataset.

### Empunhaduras
- **Shakehand** — cabo longo, FH e BH com borrachas inverted
- **Penhold classico** — cabo curto, BH com dorso da raquete (sem borracha BH)
- **Classineta** — penhold moderno, borracha inverted no dorso para BH ativo

### Laminas
- **ALL:** madeira pura, controle alto, velocidade baixa
- **OFF- / OFF / OFF+:** progressao ofensiva
- **Carbono inner:** mais controle, dwell time maior
- **Carbono outer:** mais velocidade, menos controle

### Borrachas
- **IN:** inverted — topspin
- **OUT:** short pips — ataque direto
- **LONG:** long pips — defesa e desorientacao
- **ANTI:** baixo atrito — bloqueio e corte

### Escala de dureza
- Chinesa ≈ 8° mais dura que europeia
- Ex: 39° chinesa ≈ 47° europeia

### Combinacoes lamina + borracha
- Rigida + mole = equilibrio
- Rigida + dura = velocidade maxima, pouco controle
- Mole + dura = spin alto, controle medio
- Mole + mole = controle maximo, velocidade baixa

---

## 18. Diretriz Final para o LLM

- Assumir **Expo + React Native + TypeScript** como stack oficial do frontend
- Tratar **Android e iOS** como alvos desde o primeiro commit
- Separar claramente **app / backend / ETL**
- Nunca usar Next.js como frontend principal
- Comecar pelo **scaffold do repositorio** e imediatamente atacar a **Fase 1 — ETL**
- Priorizar **pt-BR** no lancamento
- Usar somente atributos numericos do dataset para analise
- **Nao persistir inferencias nos JSONs**
- Manter recomendacao de novos setups **fora do MVP**

---

## Historico de Versoes

| Versao | Mudanca principal |
|---|---|
| v1.0 | Prompt inicial — web app, Next.js, OpenRouter |
| v1.1 | Stack mobile confirmada — Expo, i18n corrigido |
| v1.2 | Fusao Sonnet + Codex — schemas completos, Docker Compose |
| v1.3 | 4 ajustes Codex: penhold, Pydantic, aliases.json, scaffold primeiro |
| v1.4 | Escopo MVP reduzido — so analise, sem recomendacoes |
| v1.4.1 | Regra de JSON sem inferencia persistida + consistencia interna completa |
| v1.5 | Campos derivados removidos dos schemas persistidos — modelos internos do backend |
| v1.6 | LARC como flag de conformidade no MVP + filtro hard na v1.0 |
| **v1.7** | LARC corrigida para borrachas apenas — laminas sem restricao ITTF |
| **v1.8** | AnalysisConfidence no output + limiares realistas de cobertura para o MVP |

---

*Versao 1.8 — CONGELADO DEFINITIVO. Pronto para uso no repositorio.*
*20/03/2026 | Leo (lfsystems) | Belem, PA, Brasil*
