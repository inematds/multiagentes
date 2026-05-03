# Equipes de Agentes na Prática 🤖

Curso completo sobre como projetar, orquestrar e operar squads de agentes de IA — **Claude Code**, **OpenAI Codex** e **Gemini CLI**.

**Acesso direto:** abra `index.html` no navegador.

## Estrutura

```
.
├── index.html                  # Landing page
├── curso/
│   ├── trilha1/                # 🧭 Fundamentos (Emerald)
│   │   ├── index.html
│   │   └── modulo-1-1.html     # Módulo modelo completo
│   ├── trilha2/                # ⚙️ Setup & Prompting (Blue)
│   ├── trilha3/                # 🎮 Operação (Purple)
│   ├── trilha4/                # 🔧 Diagnóstico, Custo & Encerramento (Amber)
│   └── trilha5/                # 🌐 Multi-runtime + Capstone (Teal)
└── imgs/                       # Cartões visuais por aula
```

## As 5 trilhas

| # | Trilha | Módulos | Foco |
|---|--------|---------|------|
| 1 | 🧭 Fundamentos | 3 | Lead/teammate/mailbox; Subagent vs Team; ecossistema 2026 |
| 2 | ⚙️ Setup & Prompting | 3 | Flag experimental; anatomia do prompt; Faça vs Não Faça |
| 3 | 🎮 Operação | 5 | 3 regras de ouro; contexto; plan mode; hooks; tmux |
| 4 | 🔧 Diagnóstico | 5 | 6 armadilhas; árvore de decisão; custo; shutdown limpo |
| 5 | 🌐 Multi-runtime + Capstone | 4 + 4h | Codex/Gemini portáteis; NeuroFlow Pro |

**Total:** 20 módulos • 120 tópicos • ~16h de conteúdo + 4h de capstone.

## Fontes oficiais usadas

- [Claude Code — Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code — Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code — Hooks](https://code.claude.com/docs/en/hooks)
- [OpenAI Codex — Subagents](https://developers.openai.com/codex/subagents)
- [OpenAI Codex — CLI](https://developers.openai.com/codex/cli)
- [Gemini CLI — Subagents](https://geminicli.com/docs/core/subagents/)
- [Symphony (OpenAI orchestration spec)](https://openai.com/index/open-source-codex-orchestration-symphony/)

## Stack técnico das páginas

- HTML estático + Tailwind CDN (sem build)
- Inter (Google Fonts)
- Dark/light toggle persistente em `localStorage`
- Tópicos expansíveis com JS vanilla
- Padrão visual INEMA.CLUB
