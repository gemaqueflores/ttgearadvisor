# Table Tennis Gear Advisor — Project Prompt
## Versão 1.3 — CONGELADO

> Fusão: prompt técnico (Sonnet v1.1) + prompt operacional (Codex v1.1)
> Data: 20/03/2026 | Autor: Leo (lfsystems) | Belém, PA, Brasil

---

## 1. Visão Geral

Desenvolver um **app mobile nativo multi-language (Android + iOS)** que analisa o perfil técnico de atletas de tênis de mesa e recomenda equipamentos (lâmina + borrachas) com base em dados técnicos objetivos de datasets especializados.

O app é um **motor de compatibilidade técnica**:
- cruza atributos numéricos dos equipamentos com o perfil do atleta
- gera recomendações justificadas tecnicamente
- explica por que determinada combinação faz sentido para aquele atleta específico

**Diferencial central:** não existe produto equivalente no mercado com foco em compatibilidade técnica objetiva. A recomendação não é baseada em estoque, loja, marketplace ou opinião subjetiva.

---

## 2. Stack Tecnológica — Confirmada

| Camada | Tecnologia | Observação |
|---|---|---|
| App Mobile | Expo + React Native + TypeScript | Android + iOS, único projeto |
| Navegação | expo-router | Estrutura moderna baseada em rotas |
| i18n | i18next + react-i18next + expo-localization | pt-BR no lançamento |
| Backend / API | Python + FastAPI | Separado do app mobile |
| Orquestração | n8n self-hosted | Nova VM Oracle Cloud |
| LLM MVP | Claude Sonnet 4.6 — Anthropic API direta | Sem OpenRouter no MVP |
| LLM v1.1+ | Gemini Flash + Sonnet | Quando dataset crescer |
| Banco de dados | PostgreSQL | Schema `tt_advisor` — nova VM |
| Infra backend | Oracle Cloud Free Tier ARM | Nova instância exclusiva |
| Build mobile | EAS Build | Cloud build — funciona em Windows para iOS |
| Publicação | EAS Submit → Google Play + App Store | Lojas oficiais |

### O que NÃO fazer
- Não usar Next.js como frontend principal do produto
- Não usar `next-i18next`
- Não usar Capacitor no MVP
- Não depender de Vercel como frontend do produto
- Não compartilhar VM, banco ou serviços com o projeto anterior
- Não tratar o app como web app adaptado para mobile

---

## 3. Fluxo Principal do Usuário

```text
1. Usuário abre o app
2. Usuário preenche perfil do atleta
3. App envia payload ao backend (FastAPI)
4. Backend faz pré-filtro no dataset unificado (Python)
5. Backend chama Sonnet com perfil + candidatos filtrados
6. Sonnet retorna análise técnica estruturada (JSON)
7. App exibe resultado em 4 blocos:
   - análise do perfil
   - análise do setup atual
   - top 3 recomendações
   - roadmap de evolução
```

---

## 4. Campos do Perfil do Atleta

### Dados de jogo
- Nível: `iniciante` / `intermediário` / `avançado` / `federado`
- Estilo: `ofensivo` / `defensivo` / `all-round`
- Empunhadura: `shakehand` / `penhold-classico` / `classineta`
- Lado dominante: `destro` / `canhoto`
- Pontos fortes e fracos em multi-select
- Frequência: `ocasional` / `1-2x/semana` / `3-4x/semana` / `diário` / `federado`

### Material atual
- Lâmina: marca + modelo
- Borracha FH: marca + modelo + espessura
- Borracha BH: marca + modelo + espessura, ou `dorso-liso` no penhold clássico
- Tempo de uso do setup atual

### Histórico
- Materiais anteriores
- Problemas percebidos
- Objetivo: `mais-velocidade` / `mais-spin` / `mais-controle` / `equilíbrio` / `competição-federada`

---

## 5. Output da IA

O Sonnet deve retornar JSON válido, sem texto adicional, com:
- `analise_perfil`
- `analise_setup_atual`
- `recomendacoes`
- `roadmap`

No caso de BH com penhold clássico, o campo `borracha_bh` deve aceitar `tipo: "dorso-liso"` com `marca/modelo/espessura` nulos e `observacao` opcional.

---

## 6. Arquitetura de Dados

### Fontes
- Revspin
- LARC ITTF
- Fabricantes
- TTGearLab
- Megaspin
- TT Reviews

### Regra de inclusão
- obrigatoriamente aprovado na LARC
- com atributos numéricos mínimos válidos

### Outputs esperados
- `larc_whitelist.json`
- `revspin_blade.json`
- `revspin_rubber.json`
- `fabricante_blade.json`
- `fabricante_rubber.json`
- `ttgearlab_blade.json`
- `megaspin_blade.json`
- `unified_blade.json`
- `unified_rubber.json`

### Normalização
- chave de merge: `marca_normalizada + modelo_normalizado`
- `RapidFuzz` + `etl/aliases.json`
- IDs finais em kebab-case

### Prioridade do merge
1. fabricante
2. ttgearlab
3. megaspin
4. revspin

---

## 7. Pipeline ETL

1. Extrair LARC trimestral
2. Consolidar Revspin já disponível
3. Scraping de fabricantes
4. Scraping TTGearLab
5. Scraping Megaspin
6. Normalizar nomes com aliases
7. Aplicar filtros
8. Fazer merge por ID normalizado
9. Calcular campos derivados
10. Exportar `unified_blade.json` e `unified_rubber.json`

---

## 8. Motor de Recomendação

### Pré-filtro Python
Antes do LLM, o backend deve selecionar top candidatos por categoria com base no perfil do atleta e nos atributos numéricos do dataset.

### Prompt do Sonnet
- responder no idioma do usuário
- retornar apenas JSON válido
- usar exclusivamente atributos numéricos fornecidos
- citar valores específicos ao justificar

---

## 9. Internacionalização

Stack oficial:
- `i18next`
- `react-i18next`
- `expo-localization`

Estrutura esperada:

```text
src/i18n/
├── pt-BR/common.json
├── en-US/common.json
├── es-ES/common.json
└── zh-CN/common.json
```

Fases:
- MVP: `pt-BR`
- v1.1: `en-US`
- v1.2: `es-ES`
- roadmap: `zh-CN`

---

## 10. Infraestrutura

Infra exclusiva em Oracle Cloud Free Tier ARM:
- PostgreSQL em Docker
- FastAPI em Docker
- n8n em Docker
- Nginx com SSL

Também preparar:
- Google Play via EAS Submit
- App Store via EAS Submit

---

## 11. Estrutura do Repositório

```text
tt-gear-advisor/
├── app/
├── backend/
├── etl/
├── data/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 12. UX Mobile

Diretrizes:
- fluxo curto
- toque confortável
- leitura rápida em telas pequenas
- loading claro
- resultado escaneável em menos de 30 segundos
- performance em rede móvel

Telas mínimas:
- splash
- boas-vindas
- formulário do perfil
- loading da análise
- resultado
- configurações

---

## 13. Ordem de Desenvolvimento

### Fase 0
- infraestrutura da nova VM

### Fase 1
- pipeline ETL

### Fase 2
- backend FastAPI
- `POST /analyze`
- `GET /health`
- validação Pydantic da resposta do Sonnet

### Fase 3
- app Expo + React Native
- `expo-router`
- i18n
- formulário
- resultado
- settings
- integração com backend

### Fase 4
- integração com n8n

### Fase 5
- build preview
- assets das stores
- publicação Android/iOS

---

## 14. Convenções

- Python: `snake_case`, type hints, docstrings em pt-BR
- TypeScript: `camelCase`
- Componentes React Native: `PascalCase`
- JSON datasets: `snake_case`
- IDs: kebab-case minúsculo sem acentos
- Conventional Commits em português
- nunca commitar credenciais

---

## 15. Diretriz Final para o LLM

- assumir Expo + React Native + TypeScript como stack oficial
- tratar Android e iOS como alvos principais desde o início
- separar claramente app mobile, backend API e pipeline ETL
- nunca usar Next.js como frontend principal
- começar pela estrutura mínima do repositório e atacar Fase 1
- priorizar pt-BR no lançamento
- basear recomendações exclusivamente em atributos numéricos do dataset

---

*Versão 1.3 — CONGELADO. Pronto para uso no repositório.*
