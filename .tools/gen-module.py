#!/usr/bin/env python3
"""Gerador de páginas de módulo no formato INEMA.CLUB.

Lê dados de cada módulo do dicionário MODULES e produz arquivos HTML em
curso/trilhaN/modulo-N-Y.html seguindo o template do MASTER.
Requer apenas Python 3.8+; nada além de stdlib.
"""
from __future__ import annotations
import os, json, re, textwrap
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cores por trilha (trail -> cor accent)
TRAIL_COLORS = {
    1: ("emerald", "#059669", "5, 150, 105", "Fundamentos"),
    2: ("blue",    "#2563eb", "37, 99, 235", "Setup"),
    3: ("purple",  "#7c3aed", "124, 58, 237", "Operação"),
    4: ("amber",   "#92400e", "217, 119, 6", "Diagnóstico"),
    5: ("teal",    "#0d9488", "13, 148, 136", "Multi-runtime"),
}

# Mapa para mostrar todas as trilhas no nav
ALL_TRAILS = [
    (1, "emerald", "Fundamentos"),
    (2, "blue",    "Setup"),
    (3, "purple",  "Operação"),
    (4, "amber",   "Diagnóstico"),
    (5, "teal",    "Multi-runtime"),
]

@dataclass
class Topic:
    emoji: str
    title: str
    subtitle: str
    intro: str  # parágrafo introdutório
    boxes: list  # lista de (kind, content) — kind in {"main","data","tip","grid","timeline","alert"}

@dataclass
class Module:
    trail: int
    n: int  # 1..N
    emoji: str
    title: str
    subtitle: str  # uma linha após o título
    duration_min: int
    nivel: str
    tipo: str
    next_module_title: str  # título resumido do próximo
    next_module_url: str    # href relativo ao próximo
    topics: list  # 6 Topic


def b_main(title, body, items=None):
    return ("main", {"title": title, "body": body, "items": items or []})

def b_data(title, items):
    return ("data", {"title": title, "items": items})

def b_tip(title, body):
    return ("tip", {"title": title, "body": body})

def b_grid(do_title, do_items, dont_title, dont_items):
    return ("grid", {"do_title": do_title, "do_items": do_items, "dont_title": dont_title, "dont_items": dont_items})

def b_timeline(steps):
    # steps = [(title, ctx, body), ...]
    return ("timeline", {"steps": steps})

def b_alert(title, body):
    return ("alert", {"title": title, "body": body})


def render_box(kind, data, color):
    if kind == "main":
        items_html = ""
        if data["items"]:
            lis = "\n          ".join(
                f'<li class="flex items-start space-x-2"><span class="text-{color}-400 mt-1">•</span><span>{i}</span></li>'
                for i in data["items"]
            )
            items_html = f'\n        <ul class="space-y-2 text-neutral-300">\n          {lis}\n        </ul>'
        return f'''      <div class="bg-gradient-to-br from-{color}-900/30 to-dark-800 rounded-xl border border-{color}-500/30 p-6 mb-6">
        <h3 class="text-lg font-semibold text-{color}-400 mb-4">{data["title"]}</h3>
        <p class="text-neutral-300 mb-4">{data["body"]}</p>{items_html}
      </div>'''
    if kind == "data":
        lis = "\n          ".join(f'<li>{i}</li>' for i in data["items"])
        return f'''      <div class="bg-blue-900/20 rounded-xl border border-blue-500/30 p-6 mb-6">
        <h3 class="text-lg font-semibold text-blue-400 mb-4">{data["title"]}</h3>
        <ul class="space-y-2 text-neutral-300">
          {lis}
        </ul>
      </div>'''
    if kind == "tip":
        return f'''      <div class="bg-primary/10 rounded-xl border border-primary/40 p-6 mb-6">
        <h3 class="text-lg font-semibold text-primary mb-3">{data["title"]}</h3>
        <p class="text-neutral-300">{data["body"]}</p>
      </div>'''
    if kind == "grid":
        do_lis = "\n            ".join(
            f'<li class="flex items-start space-x-2"><span class="text-emerald-400">✓</span><span>{i}</span></li>'
            for i in data["do_items"])
        dont_lis = "\n            ".join(
            f'<li class="flex items-start space-x-2"><span class="text-red-400">✗</span><span>{i}</span></li>'
            for i in data["dont_items"])
        return f'''      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="bg-emerald-900/20 rounded-xl border border-emerald-500/30 p-6">
          <h4 class="font-bold text-emerald-400 mb-4">{data["do_title"]}</h4>
          <ul class="space-y-3 text-neutral-300 text-sm">
            {do_lis}
          </ul>
        </div>
        <div class="bg-red-900/20 rounded-xl border border-red-500/30 p-6">
          <h4 class="font-bold text-red-400 mb-4">{data["dont_title"]}</h4>
          <ul class="space-y-3 text-neutral-300 text-sm">
            {dont_lis}
          </ul>
        </div>
      </div>'''
    if kind == "timeline":
        steps = "\n        ".join(
            f'''<div class="flex items-start space-x-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-full bg-{color}-500/20 flex items-center justify-center"><span class="text-{color}-400 font-bold">{idx+1}</span></div>
          <div class="flex-1 bg-dark-800 rounded-xl p-6 border border-dark-600">
            <h4 class="font-semibold text-white mb-2">{t}</h4>
            <p class="text-sm text-neutral-400 mb-3">{ctx}</p>
            <p class="text-neutral-300 text-sm">{body}</p>
          </div>
        </div>'''
            for idx, (t, ctx, body) in enumerate(data["steps"])
        )
        return f'      <div class="space-y-6 mb-6">\n        {steps}\n      </div>'
    if kind == "alert":
        return f'''      <div class="bg-red-900/20 rounded-xl border border-red-500/30 p-6 mb-6">
        <h3 class="text-lg font-semibold text-red-400 mb-3">{data["title"]}</h3>
        <p class="text-neutral-300">{data["body"]}</p>
      </div>'''
    raise ValueError(f"unknown box kind: {kind}")


def render_topic(idx, t: Topic, color):
    boxes = "\n".join(render_box(k, d, color) for k, d in t.boxes)
    return f'''
    <section id="topico-{idx}" class="mb-16">
      <div class="flex items-center space-x-4 mb-6">
        <span class="flex items-center justify-center w-12 h-12 rounded-full bg-{color}-500/20 text-{color}-400 font-bold text-xl">{idx}</span>
        <h2 class="text-2xl font-bold">{t.emoji} {t.title}</h2>
      </div>
      <p class="text-neutral-300 mb-6 leading-relaxed">{t.intro}</p>
{boxes}
    </section>'''


def render_nav(active_trail):
    items = []
    for n, color, label in ALL_TRAILS:
        if n == active_trail:
            items.append(
                f'<a href="index.html" class="px-3 py-1.5 rounded-lg text-sm font-semibold text-{color}-400 bg-{color}-500/10">'
                f'<span class="sm:hidden">T{n}</span><span class="hidden sm:inline">{label}</span></a>'
            )
        else:
            href = f"../trilha{n}/index.html"
            items.append(
                f'<a href="{href}" class="px-3 py-1.5 rounded-lg text-sm font-semibold text-neutral-400 hover:text-{color}-400 hover:bg-{color}-500/10 transition-colors">'
                f'<span class="sm:hidden">T{n}</span><span class="hidden sm:inline">{label}</span></a>'
            )
    return "\n          ".join(items)


def render_lightmode_css(color, rgb):
    base = '''
    body { font-family: 'Inter', sans-serif; }
    .dark body { background-color: #111827; }
    html:not(.dark) body { background-color: #f8fafc; }
    html:not(.dark) .bg-dark-900 { background-color: #ffffff; }
    html:not(.dark) .bg-dark-800 { background-color: #f9fafb; }
    html:not(.dark) .bg-dark-700 { background-color: #f3f4f6; }
    html:not(.dark) .bg-dark-600 { background-color: #e5e7eb; }
    html:not(.dark) .text-neutral-100 { color: #111827; }
    html:not(.dark) .text-neutral-300 { color: #4b5563; }
    html:not(.dark) .text-neutral-400 { color: #6b7280; }
    html:not(.dark) .text-neutral-500 { color: #9ca3af; }
    html:not(.dark) .border-dark-600 { border-color: #d1d5db; }
    html:not(.dark) .border-dark-700 { border-color: #e5e7eb; }'''
    accent = ALL_TRAILS_RGB_CSS  # gerado abaixo
    return base + accent


# Pré-gera blocos light-mode para cada trilha (todas as cores aparecem na nav, então sempre incluo todas)
def all_light_mode_css(self_color, self_light, self_rgb):
    out = []
    out.append(f'''    html:not(.dark) .text-{self_color}-400 {{ color: {self_light}; }}
    html:not(.dark) .bg-{self_color}-500\\/20 {{ background-color: rgba({self_rgb}, 0.12); }}
    html:not(.dark) .bg-{self_color}-500\\/10 {{ background-color: rgba({self_rgb}, 0.08); }}
    html:not(.dark) .border-{self_color}-500\\/30 {{ border-color: rgba({self_rgb}, 0.25); }}
    html:not(.dark) .hover\\:bg-{self_color}-500\\/30:hover {{ background-color: rgba({self_rgb}, 0.18); }}''')
    # outras trilhas, hover only
    for n, c, _ in ALL_TRAILS:
        _, light, rgb, _ = TRAIL_COLORS[n]
        if c == self_color: continue
        out.append(f'''    html:not(.dark) .text-{c}-400 {{ color: {light}; }}
    html:not(.dark) .hover\\:text-{c}-400:hover {{ color: {light}; }}
    html:not(.dark) .hover\\:bg-{c}-500\\/10:hover {{ background-color: rgba({rgb}, 0.08); }}''')
    out.append('''    html:not(.dark) .bg-blue-900\\/20 { background-color: rgba(37, 99, 235, 0.08); }
    html:not(.dark) .border-blue-500\\/30 { border-color: rgba(37, 99, 235, 0.25); }
    html:not(.dark) .text-red-400 { color: #b91c1c; }
    html:not(.dark) .bg-red-900\\/20 { background-color: rgba(185, 28, 28, 0.08); }
    html:not(.dark) .border-red-500\\/30 { border-color: rgba(185, 28, 28, 0.25); }
    html:not(.dark) [class*="bg-gradient-to"] { background-image: none !important; }
    html:not(.dark) .text-primary { color: #a16207; }
    html:not(.dark) .bg-primary\\/10 { background-color: rgba(161, 98, 7, 0.08); }
    html:not(.dark) .border-primary\\/40 { border-color: rgba(161, 98, 7, 0.25); }
    html:not(.dark) .text-sky-400 { color: #0369a1; }
    html:not(.dark) .text-yellow-400 { color: #a16207; }
    html:not(.dark) .hover\\:text-sky-300:hover { color: #0284c7; }
    html:not(.dark) .hover\\:text-yellow-300:hover { color: #854d0e; }
    html:not(.dark) .bg-dark-900\\/95 { background-color: rgba(255, 255, 255, 0.95); }''')
    return "\n".join(out)


def render_module(m: Module):
    color, light, rgb, trail_label = TRAIL_COLORS[m.trail]
    nav_links = render_nav(m.trail)
    base_css = '''    body { font-family: 'Inter', sans-serif; }
    .dark body { background-color: #111827; }
    html:not(.dark) body { background-color: #f8fafc; }
    html:not(.dark) .bg-dark-900 { background-color: #ffffff; }
    html:not(.dark) .bg-dark-800 { background-color: #f9fafb; }
    html:not(.dark) .bg-dark-700 { background-color: #f3f4f6; }
    html:not(.dark) .bg-dark-600 { background-color: #e5e7eb; }
    html:not(.dark) .text-neutral-100 { color: #111827; }
    html:not(.dark) .text-neutral-300 { color: #4b5563; }
    html:not(.dark) .text-neutral-400 { color: #6b7280; }
    html:not(.dark) .text-neutral-500 { color: #9ca3af; }
    html:not(.dark) .border-dark-600 { border-color: #d1d5db; }
    html:not(.dark) .border-dark-700 { border-color: #e5e7eb; }'''
    light_css = all_light_mode_css(color, light, rgb)
    topics_html = "\n".join(render_topic(i+1, t, color) for i, t in enumerate(m.topics))
    summary_items = "\n          ".join(
        f'<div class="flex items-start space-x-3"><span class="text-{color}-400 mt-1">✓</span><div><strong class="text-white">{t.title}</strong><span class="text-neutral-400"> — {t.subtitle}</span></div></div>'
        for t in m.topics
    )
    title_full = f"{m.emoji} {m.title}"
    return f'''<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Módulo {m.trail}.{m.n} - {m.title} | Equipes de Agentes</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{ darkMode: 'class', theme: {{ extend: {{ colors: {{ primary: '#FACC15', dark: {{ 900: '#111827', 800: '#1f2937', 700: '#374151', 600: '#4b5563' }} }} }} }} }}
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
{base_css}
{light_css}
  </style>
</head>
<body class="bg-dark-900 text-neutral-100 min-h-screen">

  <nav class="sticky top-0 z-50 bg-dark-900/95 backdrop-blur-sm border-b border-dark-600">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-14">
        <div class="flex items-center space-x-4">
          <a href="../../index.html" class="flex items-center space-x-2 text-yellow-400 hover:text-yellow-300">
            <span class="text-2xl">🤖</span>
            <span class="font-bold text-lg hidden sm:inline">Equipes de Agentes</span>
          </a>
          <span class="text-neutral-600">|</span>
          <a href="https://inema.club" target="_blank" class="text-sky-400 hover:text-sky-300 text-sm font-medium">INEMA.CLUB</a>
        </div>
        <div class="flex items-center space-x-1 sm:space-x-2">
          {nav_links}
          <button id="theme-toggle" class="p-2 rounded-lg bg-dark-700 hover:bg-dark-600 transition-colors ml-2">
            <svg id="theme-toggle-dark-icon" class="hidden w-5 h-5 text-neutral-300" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path></svg>
            <svg id="theme-toggle-light-icon" class="hidden w-5 h-5 text-neutral-300" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" fill-rule="evenodd" clip-rule="evenodd"></path></svg>
          </button>
        </div>
      </div>
    </div>
  </nav>

  <nav class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
    <div class="flex items-center space-x-2 text-sm text-neutral-400">
      <a href="../../index.html" class="hover:text-{color}-400">Início</a>
      <span>/</span>
      <a href="index.html" class="hover:text-{color}-400">{trail_label}</a>
      <span>/</span>
      <span class="text-{color}-400">Módulo {m.trail}.{m.n}</span>
    </div>
  </nav>

  <header class="bg-gradient-to-br from-{color}-900/30 via-dark-800 to-dark-800 py-12 border-b border-dark-600">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <span class="inline-block px-3 py-1 bg-{color}-500/20 text-{color}-400 text-xs font-semibold rounded-full mb-4">MÓDULO {m.trail}.{m.n}</span>
      <h1 class="text-3xl sm:text-4xl font-bold mb-4">{title_full}</h1>
      <p class="text-lg text-neutral-400 max-w-3xl">{m.subtitle}</p>
      <div class="grid grid-cols-4 gap-4 mt-8 max-w-2xl">
        <div class="bg-dark-800/50 rounded-lg p-3 border border-dark-600"><div class="text-xl font-bold text-{color}-400">6</div><div class="text-xs text-neutral-400">Tópicos</div></div>
        <div class="bg-dark-800/50 rounded-lg p-3 border border-dark-600"><div class="text-xl font-bold text-{color}-400">{m.duration_min}</div><div class="text-xs text-neutral-400">Minutos</div></div>
        <div class="bg-dark-800/50 rounded-lg p-3 border border-dark-600"><div class="text-xl font-bold text-{color}-400">{m.nivel}</div><div class="text-xs text-neutral-400">Nível</div></div>
        <div class="bg-dark-800/50 rounded-lg p-3 border border-dark-600"><div class="text-xl font-bold text-{color}-400">{m.tipo}</div><div class="text-xs text-neutral-400">Tipo</div></div>
      </div>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
{topics_html}

    <section class="mb-12">
      <div class="bg-gradient-to-br from-{color}-900/40 via-dark-800 to-dark-800 rounded-xl border border-{color}-500/30 p-8">
        <h2 class="text-2xl font-bold mb-6">📌 Resumo do Módulo</h2>
        <div class="space-y-4 mb-8">
          {summary_items}
        </div>
        <div class="bg-dark-800/50 rounded-lg p-4 mb-8">
          <h3 class="font-semibold text-{color}-400 mb-2">Próximo módulo:</h3>
          <p class="text-neutral-300">{m.next_module_title}</p>
        </div>
        <div class="flex flex-col sm:flex-row gap-4">
          <a href="index.html" class="flex-1 text-center px-6 py-3 bg-dark-700 text-neutral-300 rounded-lg font-semibold hover:bg-dark-600 transition-colors">← Voltar para Trilha</a>
          <a href="{m.next_module_url}" class="flex-1 text-center px-6 py-3 bg-{color}-600 text-white rounded-lg font-semibold hover:bg-{color}-500 transition-colors">Próximo Módulo →</a>
        </div>
      </div>
    </section>
  </main>

  <footer class="border-t border-dark-600 py-8 mt-16">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-neutral-500 text-sm">
      <p>Equipes de Agentes na Prática • 2026</p>
    </div>
  </footer>

  <script>
    const themeToggle = document.getElementById('theme-toggle');
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    const html = document.documentElement;
    if (localStorage.getItem('theme') === 'light' || (!localStorage.getItem('theme') && !html.classList.contains('dark'))) {{
      themeToggleDarkIcon.classList.remove('hidden');
      html.classList.remove('dark');
    }} else {{
      themeToggleLightIcon.classList.remove('hidden');
    }}
    themeToggle.addEventListener('click', () => {{
      themeToggleDarkIcon.classList.toggle('hidden');
      themeToggleLightIcon.classList.toggle('hidden');
      html.classList.toggle('dark');
      localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
    }});
  </script>
</body>
</html>
'''


# ----------------------------------------------------------------
# Conteúdo dos 19 módulos restantes
# ----------------------------------------------------------------

MODULES = []

# T1.2 — Subagentes vs Teams
MODULES.append(Module(
    trail=1, n=2, emoji="🔍", title="Subagentes vs Teams",
    subtitle="Contexto, custo, comunicação e árvore de decisão.",
    duration_min=45, nivel="Básico", tipo="Teoria",
    next_module_title="1.3 — Estado da arte fora do Claude Code",
    next_module_url="modulo-1-3.html",
    topics=[
        Topic("📦", "Subagentes: contexto isolado", "Caller dispara, recebe sumário",
              "Subagent é uma instância <strong class=\"text-emerald-400\">dentro</strong> da sessão atual. Tem contexto próprio, tools restritas por allowlist, executa a task e devolve um resultado para quem chamou. Não conversa com outros subagents.",
              [b_main("📌 Quando usar subagent",
                      "Quando você quer paralelizar pesquisa/sumarização sem poluir o contexto principal e sem precisar que os workers troquem mensagens.",
                      ["Pesquisa de docs/repos", "Sumário de logs", "Análise de PRs (read-only)", "Verificações que não escrevem código"]),
               b_tip("💡 Custo baixo", "Subagents são o jeito mais barato de ganhar paralelismo: 1 chamada extra, retorno em texto.")]),
        Topic("👥", "Teams: contexto + mailbox", "Vários subagents que conversam",
              "Em um team, cada teammate é uma <strong class=\"text-emerald-400\">sessão Claude Code completa e independente</strong>. O que muda é o canal de mailbox que permite comunicação P2P direta — mais a task list compartilhada.",
              [b_main("📌 Quando usar team",
                      "Quando teammates precisam trocar contratos, pedir retrabalho, debater hipóteses ou cobrir camadas distintas em paralelo.",
                      ["Cross-layer (front + back + tests)", "PR review com 3 lentes", "Debug com hipóteses concorrentes", "Squad Dev↔QA com retrabalho"]),
               b_alert("⚠️ Custo alto", "Cada teammate é uma sessão completa. 5 teammates ≈ 5× tokens da sessão equivalente.")]),
        Topic("💰", "Custo: 1x → 3x → 5x", "A regra linear",
              "A doc oficial e a prática convergem: <strong class=\"text-emerald-400\">cada teammate adiciona ~1x ao custo</strong> da sessão. 5 teammates ≈ 5x. Times grandes parecem mais inteligentes, mas raramente entregam 5x mais.",
              [b_data("📊 Numbers que importam",
                      ["3-5 teammates é o doce-spot", "5-6 tasks por teammate", "&gt; 10 teammates = retorno cai rápido",
                       "Misturar Haiku/Sonnet/Opus por papel reduz 30-50%"]),
               b_tip("💡 Decisão prática", "Comece sempre com 3 teammates. Só aumente se medir ganho real, não percepção.")]),
        Topic("⏱️", "Latência: paralelo vs sequencial", "Onde aparece o ganho",
              "Subagents geralmente <strong class=\"text-emerald-400\">rodam em sequência</strong> dentro do caller. Teams rodam concorrentes — o tempo de parede colapsa para o do gargalo.",
              [b_grid("✓ Quando teams ganham", ["Tarefas independentes", "Caminhos paralelos de pesquisa", "5 hipóteses testadas em paralelo"],
                      "✗ Quando teams empatam", ["Trabalho intrinsecamente sequencial", "Tudo depende de um único output anterior", "Time fica esperando 1 teammate"])]),
        Topic("🛡️", "Permissões: herança e propagação", "O que cada um pode fazer",
              "Subagents têm <strong class=\"text-emerald-400\">tools controlados por allowlist no frontmatter</strong>. Teammates herdam permissões do lead no spawn. Erro grave de configuração se propaga para todo o time.",
              [b_alert("⚠️ Cuidado com --dangerously-skip-permissions",
                       "Se o lead roda em modo permissivo, todo o time também roda. Risco real, especialmente com QA com Bash livre."),
               b_tip("💡 Pre-aprove no settings", "Allowlist específica em <code class=\"text-emerald-400\">.claude/settings.json</code> resolve sem abrir tudo.")]),
        Topic("🧭", "Árvore de decisão: 3 perguntas", "Team, Subagent ou Single?",
              "Decida em 30 segundos com 3 perguntas: (1) <strong class=\"text-emerald-400\">precisam conversar entre si?</strong> (2) precisa paralelo real? (3) cabe em 1 contexto?",
              [b_timeline([
                  ("Pergunta 1", "Workers precisam trocar mensagens?", "Sim → Team. Não → continua."),
                  ("Pergunta 2", "Trabalho paraleliza?", "Sim → Subagents (paralelos). Não → continua."),
                  ("Pergunta 3", "Cabe em uma sessão?", "Sim → Single session. Não → divida em subagents.")
              ]),
               b_tip("💡 Dúvida persistente?", "Comece com subagents. Migra para team só se sentir falta de mailbox.")]),
    ]
))

# T1.3 — Estado da arte
MODULES.append(Module(
    trail=1, n=3, emoji="🌍", title="Estado da arte fora do Claude Code",
    subtitle="Codex, Gemini, CrewAI, AutoGen, LangGraph, Symphony — o ecossistema 2026.",
    duration_min=50, nivel="Básico", tipo="Panorama",
    next_module_title="2.1 — Setup do Claude Code",
    next_module_url="../trilha2/modulo-2-1.html",
    topics=[
        Topic("🔧", "Codex CLI Subagents", "TOML em ~/.codex/agents/",
              "OpenAI lançou Codex Subagents em 2026: agents declarados em <strong class=\"text-emerald-400\">arquivos TOML</strong> em <code class=\"text-emerald-400\">~/.codex/agents/</code> ou <code class=\"text-emerald-400\">.codex/agents/</code>. Codex orquestra spawning, routing e shutdown automaticamente.",
              [b_main("📌 Anatomia de um agent TOML",
                      "Campos obrigatórios: name, description, developer_instructions. Opcionais: model, sandbox_mode, mcp_servers.",
                      ["<code class=\"text-emerald-400\">name = \"security-reviewer\"</code>",
                       "<code class=\"text-emerald-400\">model = \"o3\"</code>",
                       "<code class=\"text-emerald-400\">sandbox_mode = \"workspace-write\"</code>"]),
               b_data("📊 Config global [agents]",
                      ["<code>max_threads = 6</code> (paralelismo)",
                       "<code>max_depth = 1</code> (recursão)",
                       "<code>job_max_runtime_seconds</code>"])]),
        Topic("💎", "Gemini CLI Subagents", "Markdown + YAML + @nome",
              "Google trouxe Subagents para o Gemini CLI também em 2026: arquivos <code class=\"text-emerald-400\">.gemini/agents/*.md</code> com YAML frontmatter; corpo do markdown vira system prompt. Uso por delegação automática ou explícito com <code class=\"text-emerald-400\">@nome</code>.",
              [b_main("📌 Built-ins prontos",
                      "Antes de criar agent novo, veja se um built-in já resolve.",
                      ["<strong>codebase_investigator</strong> — exploração de código",
                       "<strong>cli_help</strong> — doc de CLIs",
                       "<strong>generalist</strong> — task pesada genérica",
                       "<strong>browser_agent</strong> (experimental) — interação web"]),
               b_alert("⚠️ Sem nesting", "Subagent não pode invocar outro subagent. Modelagem hierárquica não funciona — pense flat.")]),
        Topic("🛠️", "CrewAI: papéis e crews", "Equipe humana como abstração",
              "Framework Python que modela agentes como <strong class=\"text-emerald-400\">papéis com backstory e goal</strong>. Você assembla uma 'crew' e dá tasks. É o jeito mais rápido de prototipar (2-3 dias).",
              [b_main("📌 Vantagem CrewAI",
                      "Mental model próximo do humano. 'Researcher → Writer → Editor' é literalmente código.",
                      ["Time-to-prototype baixo",
                       "Flows event-driven (2025+)",
                       "Bom para PoCs comerciais",
                       "Observabilidade limitada"]),
               b_tip("💡 Quando escolher CrewAI",
                     "Quando o stakeholder precisa entender o fluxo sem ler código. Para produção robusta, considere LangGraph.")]),
        Topic("🕸️", "AutoGen / AG2: GroupChat", "Conversa como primitivo",
              "Microsoft AutoGen (agora <strong class=\"text-emerald-400\">AG2</strong>) usa GroupChat: múltiplos agentes em uma conversa, selector decide quem fala. É o padrão ideal para <strong>debate</strong> entre agentes.",
              [b_main("📌 Onde AG2 brilha",
                      "Tarefas que se beneficiam de raciocínio adversarial entre agentes.",
                      ["Pre-mortem (cético + advogado)",
                       "Solucionador + crítico",
                       "Brainstorm com restrições",
                       "Consenso via debate"]),
               b_data("📊 Estado em 2026",
                      ["AutoGen v1 está em maintenance", "AG2 é o caminho ativo (event-driven)", "Pluggable orchestration", "Async-first"])]),
        Topic("📊", "LangGraph: workflow como grafo", "Determinismo + observabilidade",
              "Trata workflow como <strong class=\"text-emerald-400\">grafo dirigido</strong>: nodes (funções/LLM) + edges (controle) + state (typed dict). Curva de aprendizado de 10-14 dias, mas é a opção mais robusta para produção.",
              [b_grid("✓ Vantagens",
                      ["Replay step-by-step (LangSmith)", "Checkpointing", "Branching explícito", "Inject inputs em runtime"],
                      "✗ Custos",
                      ["Curva longa", "Verbosidade real", "Overkill para PoC", "Time precisa investir"])]),
        Topic("🎯", "Symphony: spec aberto da OpenAI", "Linear como control plane",
              "Spec open-source que turbina times reportadamente em <strong class=\"text-emerald-400\">+500% de PRs aterrissados</strong> ao usar Linear como painel de orquestração de agentes. Codex como MCP server + Agents SDK.",
              [b_main("📌 O que Symphony aponta",
                      "Para onde o mercado vai: orquestração visual + governança baseada em ticket/issue.",
                      ["Pipeline declarativo",
                       "Reviewable workflows",
                       "Integração CI nativa",
                       "Auditoria completa"]),
               b_tip("💡 Padrão portátil",
                     "Mesmo que você use Claude Code Teams hoje, conhecer Symphony te prepara para o ano que vem.")]),
    ]
))

# T2.1 — Setup do Claude Code
MODULES.append(Module(
    trail=2, n=1, emoji="⚡", title="Setup do Claude Code",
    subtitle="Flag experimental, settings.json, modos de display e treinar o repo com a doc oficial.",
    duration_min=50, nivel="Intermediário", tipo="Mão na massa",
    next_module_title="2.2 — Anatomia do prompt de spawn",
    next_module_url="modulo-2-2.html",
    topics=[
        Topic("🚀", "Versão e flag experimental", "v2.1.32+ + AGENT_TEAMS=1",
              "Pré-requisito hard: Claude Code v2.1.32+. Verifique com <code class=\"text-blue-400\">claude --version</code>. Habilite com <code class=\"text-blue-400\">CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1</code> em settings.json (projeto ou user) ou no env.",
              [b_main("📌 Onde colocar a flag",
                      "Pode ir em 3 lugares; escolha por escopo.",
                      ["<code>.claude/settings.json</code> — projeto",
                       "<code>~/.claude/settings.json</code> — user",
                       "Variável de ambiente — sessão",
                       "Recomendado: settings.local.json no projeto"]),
               b_alert("⚠️ Erro silencioso", "Sem a flag, comandos de team falham sem mensagem clara. Sintoma: 'Claude não cria os agentes'.")]),
        Topic("🖥️", "Modos de display", "auto, tmux, in-process",
              "<code class=\"text-blue-400\">teammateMode</code> aceita 3 valores. Padrão é <strong class=\"text-blue-400\">auto</strong>: usa tmux se já estiver dentro de tmux, senão in-process. Para forçar, use <code class=\"text-blue-400\">--teammate-mode</code>.",
              [b_grid("✓ Tmux/iTerm2 (split-pane)",
                      ["Cada teammate em pane próprio", "Diagnóstico ao vivo", "Mais natural para demos", "macOS: tmux -CC dentro de iTerm2"],
                      "✗ VS Code/Win Terminal/Ghostty",
                      ["NÃO suportam split", "Use in-process", "Funciona, só não é split", "Cheque <code>which tmux</code>"])]),
        Topic("🔐", "Permissões herdadas e pré-aprovação", "Reduzir prompts no spawn",
              "Teammates herdam permissões do lead. Sem pré-aprovação, cada um pausa pedindo permissão a cada <code class=\"text-blue-400\">npm</code>/<code class=\"text-blue-400\">git</code>. Allowlist no settings é a primeira correção que dobra produtividade.",
              [b_main("📌 Allowlist canônica para projetos JS",
                      "Padrões de comando que cobrem 90% dos casos.",
                      ["<code>Bash(npm install)</code>",
                       "<code>Bash(npm test*)</code>",
                       "<code>Bash(git status)</code>",
                       "<code>Bash(git diff*)</code>",
                       "Edit, Write, Read"]),
               b_alert("⚠️ --dangerously-skip-permissions", "É pegada: liga em produção e pode rodar rm -rf por engano. Use só em dev isolado.")]),
        Topic("📚", "Treinar o repo com docs locais", "Aprende uma vez, usa sempre",
              "Salve a doc oficial em <code class=\"text-blue-400\">docs/agent-teams-reference.md</code>. O lead consulta localmente, decisões ficam mais rápidas e melhores. Reduz busca web em runtime.",
              [b_main("📌 Estrutura recomendada",
                      "Pastas que valem a pena criar de cara.",
                      ["<code>docs/</code> — refs locais",
                       "<code>prompts/</code> — templates de spawn",
                       "<code>.claude/agents/</code> — subagent definitions",
                       "<code>.claude/hooks/</code> — scripts dos hooks"]),
               b_tip("💡 Aponte o CLAUDE.md", "Adicione referência aos docs no CLAUDE.md para o lead saber que existem.")]),
        Topic("🧩", "MCP servers e skills herdadas", "Toda a equipe ganha de fábrica",
              "MCP servers e skills configurados no projeto/user ficam disponíveis a todos os teammates. Configurar 1 vez vale para 5+ teammates. <strong class=\"text-blue-400\">É uma alavanca enorme</strong> que muitos esquecem.",
              [b_alert("⚠️ Subagent definitions são exceção",
                       "Quando você usa um subagent definition como tipo de teammate, os campos <code class=\"text-blue-400\">skills</code> e <code class=\"text-blue-400\">mcpServers</code> do frontmatter são ignorados — teammates carregam sempre do projeto/user."),
               b_tip("💡 Skills úteis para teams",
                     "skill-creator, simplify, formato-curso, n8n-* — vale revisar quais skills você tem ativas.")]),
        Topic("✅", "Smoke test: o demo Neuroflow", "Validar setup em 15 minutos",
              "Use o prompt do vídeo (Backend + Frontend + QA, todos em Sonnet) e observe o ciclo: spawn paralelo → trabalho → QA reprova → retrabalho → QA aprova → entrega.",
              [b_timeline([
                  ("Spawn", "Lead cria 3 teammates", "Você vê 3 prompts iniciais nos logs"),
                  ("Trabalho", "Cada um no seu território", "Backend em src/api, Frontend em src/ui, QA em tests/"),
                  ("QA reprova", "3 issues críticos", "Mensagens P2P para Backend e Frontend"),
                  ("Retrabalho", "Backend e Frontend reagem", "Edição direta sem passar pelo lead"),
                  ("QA aprova", "Tests verdes", "Idle notifications chegam no lead"),
              ]),
               b_tip("💡 Se o smoke passa, setup está sólido", "Daí em diante, qualquer falha é prompt, não configuração.")]),
    ]
))

# T2.2 — Anatomia do prompt
MODULES.append(Module(
    trail=2, n=2, emoji="📝", title="Anatomia do prompt de spawn",
    subtitle="Goal → Team → Roles → Final deliverables — o template canônico em 4 blocos.",
    duration_min=55, nivel="Intermediário", tipo="Mão na massa",
    next_module_title="2.3 — Faça vs Não Faça",
    next_module_url="modulo-2-3.html",
    topics=[
        Topic("🎯", "Bloco 1: Goal", "O 'porquê' antes dos 'quem'",
              "Frase única que descreve o <strong class=\"text-blue-400\">objetivo final do time</strong>, não o passo-a-passo. Teammates acordam sem contexto; o Goal dá norte para decisões locais.",
              [b_main("📌 Goal eficiente vs ineficiente",
                      "Goal observável tem critério de aceite embutido.",
                      ["✓ 'app rodando em localhost:3000 com login'",
                       "✗ 'fazer um app legal'",
                       "✓ 'pull request mergeable até sexta'",
                       "✗ 'ajude com o projeto'"]),
               b_tip("💡 Regra de ouro",
                     "Se você não sabe quando o time terminou só lendo o Goal, ele está vago demais.")]),
        Topic("👥", "Bloco 2: Team (N + modelo)", "Tamanho e modelo importam",
              "Especifique quantos teammates e qual modelo padrão. <strong class=\"text-blue-400\">Sem N explícito o lead chuta</strong>. Sem modelo, default herda do lead — pode ser caro demais.",
              [b_data("📊 Mix de modelos por papel",
                      ["Tech Writer / docs → Haiku",
                       "Dev padrão → Sonnet",
                       "Architect / decisão → Opus",
                       "QA simples → Haiku, complexo → Sonnet"]),
               b_main("📌 Nomeando o time",
                      "Nome próprio facilita auditoria e resume.",
                      ["✓ 'Create a team called Neuroflow with 3 teammates'",
                       "✓ 'Spawn the backend_review squad'",
                       "✗ 'Crie uns agentes'"])]),
        Topic("🎭", "Bloco 3: Roles", "Papel + entrega + destinatário",
              "Cada role tem 3 campos no prompt: <strong class=\"text-blue-400\">o que faz, o que entrega, e para quem manda mensagem ao terminar</strong>. Sem destinatário explícito, todos voltam ao lead.",
              [b_main("📌 Template de role",
                      "Estrutura repetível.",
                      ["<strong>Papel</strong>: Backend Dev",
                       "<strong>Faz</strong>: API REST em src/api/",
                       "<strong>Entrega</strong>: rotas /users e /posts funcionando",
                       "<strong>Quando termina</strong>: mande contrato para Frontend Dev"]),
               b_alert("⚠️ Erro comum",
                       "Esquecer o 'destinatário'. Sem ele, todos retornam ao lead, eliminando vantagem do mailbox.")]),
        Topic("📦", "Bloco 4: Final deliverables", "Como sei que terminou",
              "Lista <strong class=\"text-blue-400\">explícita de artefatos</strong>: app rodando, <code class=\"text-blue-400\">tests/report.md</code>, <code class=\"text-blue-400\">docs/build-summary.md</code>. Sem isso, time pode encerrar com trabalho parcial.",
              [b_main("📌 Deliverables observáveis",
                      "Path + formato + critério de aceite.",
                      ["✓ <code>tests/report.md</code> com lista pass/fail",
                       "✓ App acessível em localhost:3000 sem erros",
                       "✓ <code>docs/build-summary.md</code> com decisões",
                       "✗ 'um relatório do trabalho'"]),
               b_tip("💡 Executável > documentação",
                     "Sempre inclua um deliverable que possa ser <em>rodado</em> ou <em>aberto</em>, não só lido.")]),
        Topic("📐", "Templates reutilizáveis", "Salvar prompts que funcionam",
              "Mantenha prompts versionados em <code class=\"text-blue-400\">prompts/</code>. Times bem desenhados são reutilizáveis. Salvar bons prompts vale ouro — escala para o time todo.",
              [b_main("📌 Estrutura de prompts/",
                      "Catalog de spawns por situação.",
                      ["<code>prompts/spawn-fullstack.md</code>",
                       "<code>prompts/spawn-pr-review.md</code>",
                       "<code>prompts/spawn-debug-hypothesis.md</code>",
                       "<code>prompts/spawn-incident-response.md</code>"]),
               b_tip("💡 Versionamento",
                     "Cada prompt tem changelog próprio. Pequenas mudanças trazem ganho ou regressão — saiba qual.")]),
        Topic("🧪", "Refactor: vago → cirúrgico", "Antes/depois lado a lado",
              "Lab: pegue um prompt vago e transforme em prompt de 4 blocos com roles e deliverables claros. Treina o olho — depois você corrige no automático.",
              [b_grid("✓ Versão cirúrgica",
                      ["Goal observável", "N e modelo definidos", "Cada role tem destinatário", "Deliverables com path"],
                      "✗ Versão vaga",
                      ["'Faça uma equipe pra ajudar'", "'uns agentes'", "'alguém revisa no final'", "'me dê o resultado'"])]),
    ]
))

# T2.3 — Faça vs Não Faça
MODULES.append(Module(
    trail=2, n=3, emoji="✓✗", title="Faça vs Não Faça",
    subtitle="As 5 práticas que multiplicam qualidade e os 5 antipatterns que arruinam o time.",
    duration_min=50, nivel="Intermediário", tipo="Reference",
    next_module_title="3.1 — As 3 regras de ouro",
    next_module_url="../trilha3/modulo-3-1.html",
    topics=[
        Topic("📁", "FAÇA: 1 dono por arquivo", "Territórios não se sobrepõem",
              "Cada arquivo crítico tem <strong class=\"text-blue-400\">um único dono</strong>. Outros podem ler, mas só o dono escreve. É a regra que mais previne 'trabalho perdido'.",
              [b_main("📌 Como definir territórios",
                      "Pastas-âncora por papel.",
                      ["Backend → <code>src/api/</code>",
                       "Frontend → <code>src/ui/</code>",
                       "QA → <code>tests/</code>",
                       "Docs → <code>docs/</code>"]),
               b_alert("⚠️ Sintoma de violação",
                       "git diff mostra commits do mesmo arquivo de 2 teammates diferentes. Overwrite é silencioso.")]),
        Topic("🎯", "FAÇA: entregáveis observáveis", "Output não, artefato sim",
              "Cada role entrega <strong class=\"text-blue-400\">artefato verificável</strong>: arquivo, endpoint, teste passando — não 'um relatório'. Artefato força o agente a fechar.",
              [b_grid("✓ Entregáveis observáveis",
                      ["Arquivo no path X", "Endpoint que responde", "Teste que passa", "Doc que renderiza"],
                      "✗ Entregáveis vagos",
                      ["'Um sumário'", "'Análise da situação'", "'Recomendações'", "'Avaliação do risco'"])]),
        Topic("📨", "FAÇA: nomeie destinatários", "Comunicação direta &gt; broadcast",
              "Inclua nome explícito no prompt: <em>'Quando terminar, mande para Frontend Dev'</em>. Sem destinatário, todos retornam ao lead, criando gargalo.",
              [b_main("📌 Padrão de handoff",
                      "Quem fala com quem é parte da arquitetura.",
                      ["Backend → manda contrato para Frontend",
                       "Frontend → manda screenshot para QA",
                       "QA → manda relatório para Lead",
                       "Security → manda findings para Backend"]),
               b_tip("💡 Lead como árbitro, não middleman",
                     "Lead intervém em desempates e síntese final. O resto é P2P.")]),
        Topic("🔢", "FAÇA: 3-5 integrantes", "O ponto ótimo",
              "3-5 é o doce-spot validado pela doc oficial e pela prática. <strong class=\"text-blue-400\">Acima disso, retornos diminuem rápido</strong>. Coordenação adiciona overhead exponencial.",
              [b_data("📊 Heurística de tamanho",
                      ["3 teammates: setup mínimo viável",
                       "4-5: ponto ótimo para cross-layer",
                       "6+: provavelmente split em 2 teams",
                       "10+: swarm; quase nunca compensa"]),
               b_tip("💡 Regra de tasks",
                     "5-6 tasks por teammate. Se você tem 15 tasks, comece com 3 teammates.")]),
        Topic("📚", "FAÇA: contexto completo no spawn", "Teammates não herdam histórico",
              "Inclua links, arquivos, severidade, formato do report — direto no prompt do papel. <strong class=\"text-blue-400\">O que não estiver no spawn, não existe</strong> para o teammate.",
              [b_main("📌 Anatomia de spawn rico",
                      "Tudo que ele precisa para não voltar perguntando.",
                      ["Pasta de trabalho",
                       "Arquivos de referência",
                       "Severidade desejada",
                       "Formato do entregável",
                       "Critério de 'pronto'"]),
               b_alert("⚠️ Erro frequente",
                       "Achar que CLAUDE.md cobre tudo. Cobre o global; instruções específicas vão no spawn.")]),
        Topic("⚠️", "Os 5 antipatterns", "Compartilhar arquivo, vago, presumir...",
              "5 erros comuns: <strong class=\"text-blue-400\">arquivo compartilhado</strong>, deliverable vago, presumir o plano, 10+ integrantes, nenhum contexto. Reconhecer cada um por nome ajuda a corrigir prompts.",
              [b_grid("✓ Faça",
                      ["Defina donos", "Defina entregáveis", "Nomeie destinatários", "3-5 integrantes", "Dê contexto completo"],
                      "✗ Não faça",
                      ["Compartilhar mesmo arquivo", "Entregáveis vagos", "Pressupor o plano", "10+ integrantes", "Sem contexto prévio"])]),
    ]
))

# T3.1 — As 3 regras
MODULES.append(Module(
    trail=3, n=1, emoji="📜", title="As 3 regras de ouro",
    subtitle="Território, mensagens diretas e paralelismo real — princípios não negociáveis.",
    duration_min=50, nivel="Intermediário", tipo="Princípios",
    next_module_title="3.2 — Contexto e permissões",
    next_module_url="modulo-3-2.html",
    topics=[
        Topic("🏷️", "Regra 1: território próprio", "Um arquivo, um dono",
              "Cada arquivo crítico tem <strong class=\"text-purple-400\">1 e somente 1</strong> teammate dono. Outros podem ler; só o dono escreve. É a regra mais quebrada e a que mais causa estrago.",
              [b_alert("⚠️ Overwrite silencioso", "Sem ownership, dois teammates editando o mesmo arquivo gera merge implícito ruim. Não há crash — só código faltando."),
               b_main("📌 Como impor",
                      "Defina no spawn e replique no CLAUDE.md.",
                      ["Pasta-âncora por papel",
                       "Padrões de path por papel",
                       "Mensagens P2P para troca de info",
                       "git blame para auditar dono real"])]),
        Topic("📬", "Regra 2: mensagens diretas", "Evite o lead como middleman",
              "Teammates falam direto via <code class=\"text-purple-400\">SendMessage</code>; lead só entra para sintetizar ou desempatar. Tudo passar pelo lead serializa o time.",
              [b_main("📌 Padrões de handoff",
                      "Direto entre quem produz e quem consome.",
                      ["Backend → contrato → Frontend",
                       "Frontend → screenshot → QA",
                       "QA → findings → Backend (retrabalho)",
                       "Security → severidade → Backend"]),
               b_tip("💡 Lead como árbitro",
                     "Quando deve subir ao lead? Conflito de prioridade, dúvida fora do escopo do role, decisão arquitetural.")]),
        Topic("⚡", "Regra 3: paralelismo real", "Todos começam ao mesmo tempo",
              "Spawn em paralelo + tasks independentes na partida. <strong class=\"text-purple-400\">Quem precisa esperar, espera por mensagem</strong> — não por turno do lead.",
              [b_grid("✓ Paralelo real",
                      ["Todos acordam juntos", "Tasks independentes na partida", "Espera = aguardar mensagem", "Fan-out + fan-in"],
                      "✗ Paralelo fake",
                      ["1 acorda, depois outro", "Cadeia 1 → 2 → 3", "Espera = lead ainda processa", "Sem mailbox real"])]),
        Topic("🚧", "Demo de conflito de arquivo", "Aprender pelo erro",
              "Lab: force dois teammates a editar o mesmo arquivo. Veja o overwrite acontecer. Depois corrija com ownership e rode de novo. <strong class=\"text-purple-400\">Ver acontecer treina o olho</strong>.",
              [b_timeline([
                  ("Setup", "Spawn errado", "2 teammates ambos com 'edita src/app.js'"),
                  ("Run", "Concorrência ruim", "Backend escreve linha 50; Frontend escreve linha 50 sobrepondo"),
                  ("Diagnóstico", "git diff mostra perda", "Linha do Backend sumiu; QA falha"),
                  ("Fix", "Spawn corrigido", "Backend dono de src/api/; Frontend de src/ui/"),
                  ("Re-run", "Sem conflito", "Mensagem P2P troca contrato em vez de editar mesmo arquivo")
              ])]),
        Topic("📐", "Quando 'quebrar' as regras", "Exceções documentadas",
              "Casos pequenos onde 1 arquivo compartilhado é OK (TODO.md temporário) — desde que documentado e nunca em arquivos críticos. <strong class=\"text-purple-400\">Saber quebrar com critério é parte do ofício</strong>.",
              [b_main("📌 Exceções aceitáveis",
                      "Apenas leitura ou append; nunca em arquivos de produção.",
                      ["TODO.md temporário (apenas append)",
                       "Logs de coordenação (apenas append)",
                       "Arquivos read-only auxiliares",
                       "Lock explícito via mensagem antes de editar"])]),
        Topic("🔍", "Auditoria pós-execução", "Verificar adesão",
              "Após cada execução: mailbox + git diff + task list. Times 'aparentemente bem' às vezes serializam por baixo. <strong class=\"text-purple-400\">Auditar fecha o ciclo de aprendizado</strong>.",
              [b_data("📊 Métricas para olhar",
                      ["git blame por teammate name",
                       "Mensagens P2P vs lead-mediated",
                       "Wall-clock por papel",
                       "Tasks pending no fim",
                       "Tokens por papel"])]),
    ]
))

# T3.2 — Contexto e permissões
MODULES.append(Module(
    trail=3, n=2, emoji="🧠", title="Contexto e permissões",
    subtitle="O que cada teammate carrega ao acordar e como controlar o que ele pode fazer.",
    duration_min=45, nivel="Intermediário", tipo="Reference",
    next_module_title="3.3 — Aprovação de plano",
    next_module_url="modulo-3-3.html",
    topics=[
        Topic("📖", "CLAUDE.md compartilhado", "Constituição do projeto",
              "Todo teammate carrega CLAUDE.md ao acordar. <strong class=\"text-purple-400\">É o jeito mais robusto de dar instruções globais</strong>. Boilerplate no spawn é caro — o que vale para todos vai aqui.",
              [b_main("📌 O que entra no CLAUDE.md",
                      "Convenções globais e contratos do repo.",
                      ["Convenções de código",
                       "Mapas de pastas",
                       "Políticas de testes",
                       "Variáveis de ambiente",
                       "Comandos comuns"]),
               b_tip("💡 O que NÃO entra",
                     "Instruções específicas da tarefa atual. Aquelas vão no spawn — CLAUDE.md é estável.")]),
        Topic("🚫", "O que NÃO carrega", "Histórico do lead fica fora",
              "Conversa anterior do lead, decisões tomadas no chat, contexto implícito — <strong class=\"text-purple-400\">tudo isso fica fora do teammate</strong>. É a fonte mais comum de 'o agente esqueceu o que combinamos': ele simplesmente nunca soube.",
              [b_alert("⚠️ Pegada típica",
                       "Você decide algo no chat com o lead. Spawna teammate. Teammate ignora porque não sabe."),
               b_tip("💡 Solução",
                     "Tudo que importa para o teammate vai no spawn. Sempre. Mesmo que pareça repetição.")]),
        Topic("🛠️", "Subagent definitions reusáveis", "security-reviewer, test-runner...",
              "Um teammate pode usar uma subagent definition (em <code class=\"text-purple-400\">.claude/agents/</code>) como tipo, herdando tools e modelo. <strong class=\"text-purple-400\">Uma vez bom, vale para o time todo</strong>.",
              [b_main("📌 Como usar",
                      "Cite o nome no prompt do spawn.",
                      ["'Spawn a security-reviewer teammate to audit auth'",
                       "Body do .md vira system prompt",
                       "Tools allowlist é respeitada",
                       "Skills/MCP servers do frontmatter NÃO se aplicam"]),
               b_alert("⚠️ Limitação",
                       "Skills e mcpServers do frontmatter do subagent definition NÃO se aplicam quando ele é teammate. Apenas tools e model.")]),
        Topic("🔒", "Modos de permissão pós-spawn", "Trocar enquanto rodando",
              "Você pode mudar o modo de permissão de um teammate específico depois que ele já está rodando. Útil para 'soltar' agente que provou competência ou 'apertar' agente aventureiro.",
              [b_main("📌 Por teammate, em runtime",
                      "Não há per-teammate mode no spawn.",
                      ["Spawn: todos herdam do lead",
                       "Runtime: muda por teammate via mensagem",
                       "Auditoria via PostToolUse hook",
                       "Reverte se quiser"]),
               b_tip("💡 Padrão útil",
                     "QA sempre em modo restrito; Architect em modo permissivo; Dev no meio.")]),
        Topic("📁", "Onde a equipe vive em disco", "~/.claude/teams/ e tasks/",
              "Config em <code class=\"text-purple-400\">~/.claude/teams/{team}/config.json</code>; tasks em <code class=\"text-purple-400\">~/.claude/tasks/{team}/</code>. <strong class=\"text-purple-400\">Saber inspecionar ajuda diagnóstico</strong>.",
              [b_alert("⚠️ NÃO edite à mão",
                       "Config é regravado a cada update de estado. Modificações manuais somem na próxima ação."),
               b_data("📊 O que olhar",
                      ["config.json para session IDs e nomes",
                       "tasks/ para estado e dependências",
                       "Locking automático (file locks)",
                       "Permanece após cleanup (auditoria)"])]),
        Topic("🌐", "MCP servers e impacto no time", "Toda a equipe ganha acesso",
              "MCP servers configurados ficam disponíveis a todos os teammates como tools. <strong class=\"text-purple-400\">1 servidor MCP de qualidade = N teammates instantaneamente capazes</strong>.",
              [b_main("📌 Cuidados",
                      "Tools que escrevem precisam de allowlist por papel.",
                      ["MCP read-only: pode liberar geral",
                       "MCP que escreve: allowlist por papel",
                       "Auditoria via PostToolUse",
                       "Cuidado especial com QA"])]),
    ]
))

# T3.3 — Plan mode
MODULES.append(Module(
    trail=3, n=3, emoji="📋", title="Aprovação de plano",
    subtitle="Plan mode read-only, critérios de aprovação e ciclo de revisão.",
    duration_min=50, nivel="Intermediário", tipo="Mão na massa",
    next_module_title="3.4 — Hooks como quality gates",
    next_module_url="modulo-3-4.html",
    topics=[
        Topic("🔍", "Plan mode read-only", "Pesquisar antes de mexer",
              "Teammate inicia em plan mode (sem write tools), pesquisa, monta o plano e só depois passa para execução. <strong class=\"text-purple-400\">Reduz drasticamente 'agente fez merda no caminho errado'</strong>.",
              [b_main("📌 O que muda em plan mode",
                      "Escrita desativada por construção.",
                      ["Read, Glob, Grep funcionam",
                       "Edit, Write, Bash bloqueados",
                       "Plano em formato estruturado",
                       "Sai automaticamente após aprovação"]),
               b_tip("💡 Padrão para tarefas críticas",
                     "Migração de DB, refactor grande, mudança de arquitetura — sempre em plan mode obrigatório.")]),
        Topic("📤", "Enviar plano ao lead", "Approval request",
              "Teammate envia plano formalmente para o lead via approval request. <strong class=\"text-purple-400\">Lead pode aprovar ou rejeitar com feedback</strong>. Rejeitado = volta para plan mode.",
              [b_timeline([
                  ("Pesquisa", "Read-only", "Teammate explora o código relevante"),
                  ("Plano", "Estruturado", "Lista passos concretos com paths"),
                  ("Approval request", "Para o lead", "Mensagem formal pedindo OK"),
                  ("Decisão", "Aprovado ou rejeitado com feedback", "Loop até OK ou abort"),
                  ("Execução", "Write tools liberadas", "Implementa o plano aprovado")
              ])]),
        Topic("📏", "Critérios para o lead aprovar", "Instruções no prompt",
              "<em>'Só aprove se o plano cobre testes; rejeite se mexe em schema'</em>. <strong class=\"text-purple-400\">Critérios viram texto no prompt do lead</strong>. Sem critérios, o lead aprova quase tudo.",
              [b_main("📌 Critérios típicos",
                      "Cole no prompt do spawn do lead.",
                      ["Cobertura de testes obrigatória",
                       "Sem migração de DB sem flag",
                       "Sem novos endpoints públicos",
                       "Mudanças em &lt; X linhas",
                       "Documentação atualizada"]),
               b_alert("⚠️ Sem critério, sem portão",
                       "Aprovação vira carimbo. Defina critério antes de delegar a aprovação ao lead.")]),
        Topic("🔁", "Ciclo de revisão", "Plano → feedback → revisão",
              "Quando rejeitado, teammate fica em plan mode, revisa com base no feedback e resubmete. É o equivalente a 'PR review' — só que no spawn.",
              [b_grid("✓ Loop saudável",
                      ["Feedback específico", "1-2 ciclos de revisão", "Ajustes incrementais", "Critério estável"],
                      "✗ Loop ruim",
                      ["Feedback vago ('melhore')", "&gt; 3 ciclos sem convergir", "Critério muda a cada round", "Lead aprova por cansaço"])]),
        Topic("👤", "Você como aprovador", "Quando assumir o controle",
              "Em tarefas críticas, peça que <strong class=\"text-purple-400\">todo plano passe pelo humano</strong> antes da execução. No início, é o melhor jeito de calibrar critérios.",
              [b_tip("💡 Estratégia de calibração",
                     "Aprove manualmente os primeiros 5-10 planos. Capture os critérios que você usou. Cole no prompt do lead. Delegue."),
               b_main("📌 Quando manter aprovação humana",
                      "Casos onde lead não tem alçada.",
                      ["Mudanças em produção",
                       "Tools com efeito externo (email, slack)",
                       "Migração de DB",
                       "Quando o time é novo (calibração)"])]),
        Topic("🧪", "Lab: aprovador autônomo", "Plan mode em prática",
              "Spawn de 'architect' em plan mode obrigatório, com 3 critérios de aprovação no prompt do lead. <strong class=\"text-purple-400\">Ver o ciclo completo te dá confiança</strong> para operar sem aprovador humano.",
              [b_data("📊 Lab spec",
                      ["Tarefa: refactor do módulo de auth",
                       "Teammate: architect (Opus)",
                       "Plan mode: obrigatório",
                       "Critério 1: testes cobertos",
                       "Critério 2: sem schema change",
                       "Critério 3: backwards compat"])]),
    ]
))

# T3.4 — Hooks
MODULES.append(Module(
    trail=3, n=4, emoji="🪝", title="Hooks como quality gates",
    subtitle="TaskCreated, TaskCompleted, TeammateIdle e PreToolUse — bloqueio com exit code 2.",
    duration_min=55, nivel="Avançado", tipo="Mão na massa",
    next_module_title="3.5 — Display: tmux, iTerm2, split-pane",
    next_module_url="modulo-3-5.html",
    topics=[
        Topic("🎣", "Anatomia de um hook", "Evento, matcher, comando",
              "Hook = evento + matcher + handler. Configurado em settings.json. <strong class=\"text-purple-400\">Hooks são determinísticos</strong> — onde prompt pode falhar, hook bloqueia com certeza.",
              [b_main("📌 3 partes de um hook",
                      "Estrutura repetível.",
                      ["<strong>Evento</strong>: PreToolUse, TaskCompleted, etc",
                       "<strong>Matcher</strong>: regex/literal de tool name",
                       "<strong>Handler</strong>: command/http/mcp_tool/agent",
                       "Exit 2 = bloqueia + envia stderr ao agente"]),
               b_tip("💡 Localização",
                     "Hooks em <code>.claude/settings.json</code> (projeto) ou <code>~/.claude/settings.json</code> (user).")]),
        Topic("📝", "TaskCreated", "Bloquear criação de task",
              "Dispara antes da task entrar na lista. Pode <strong class=\"text-purple-400\">bloquear com exit 2</strong> + motivo no stderr. Útil para vetar tasks ambíguas, com escopo grande, ou que extrapolam orçamento.",
              [b_main("📌 Casos típicos",
                      "Onde TaskCreated brilha.",
                      ["Task sem path concreto",
                       "Task descrita em &gt; X palavras",
                       "Task que envolve produção",
                       "Task com tool name suspeito"]),
               b_data("📊 Formato JSON",
                      ["Recebe title/description na stdin",
                       "Stdout JSON ou exit 2",
                       "Feedback no stderr volta ao agente",
                       "Pode reescrever task com updatedInput"])]),
        Topic("✅", "TaskCompleted: rodar testes", "Não fecha sem verde",
              "Hook que roda <code class=\"text-purple-400\">pytest</code>/<code class=\"text-purple-400\">npm test</code> e <strong class=\"text-purple-400\">bloqueia o 'completed'</strong> se algo falha. Transforma a task list em garantia de qualidade.",
              [b_main("📌 Script típico",
                      "<code>.claude/hooks/task-completed-tests.sh</code>",
                      ["Roda subset de testes relevantes",
                       "Exit 2 com saída do test runner",
                       "Stderr volta ao teammate",
                       "Teammate corrige e tenta de novo"]),
               b_tip("💡 Subset vs full suite",
                     "Quick subset na task local; full suite no shutdown do team.")]),
        Topic("😴", "TeammateIdle: bloquear idle", "Forçar mais um round",
              "Quando teammate vai dormir, hook pode dizer <em>'ainda não, faltam estes deliverables'</em> e devolvê-lo ao trabalho. Evita 'idle prematuro'.",
              [b_main("📌 Validações úteis",
                      "Verificar antes de deixar dormir.",
                      ["Arquivos requeridos existem?",
                       "Testes verdes?",
                       "Mensagens pendentes ao destinatário?",
                       "Resumo final escrito?"])]),
        Topic("🛡️", "PreToolUse: bloquear comandos", "Não deixar rodar rm -rf",
              "Hook inspeciona parâmetros do tool antes de rodar. Bloqueia padrões perigosos. <strong class=\"text-purple-400\">É a sua rede de segurança</strong> — mesmo com permissões liberadas, hook protege contra acidentes.",
              [b_main("📌 Padrões para bloquear",
                      "Comandos típicos perigosos.",
                      ["<code>rm -rf</code>",
                       "<code>git push --force</code> em main",
                       "<code>DROP TABLE</code>",
                       "<code>kubectl delete</code> em prod",
                       "Edit em <code>.env</code>"]),
               b_data("📊 Decisão JSON",
                      ["permissionDecision: deny|allow|ask|defer",
                       "permissionDecisionReason: string",
                       "updatedInput: pode reescrever",
                       "additionalContext: avisa o agente"])]),
        Topic("📈", "Stop e PostToolUse: telemetria", "O que medir e quando",
              "Stop dispara ao fim de cada turno; PostToolUse após cada tool. <strong class=\"text-purple-400\">Sem telemetria você não otimiza</strong>. Hooks de log dão dados para decidir tamanhos e modelos.",
              [b_main("📌 O que logar",
                      "Métricas que viram decisão.",
                      ["Tokens por papel",
                       "Latência por tool",
                       "Taxa de erro por papel",
                       "Tools mais usados",
                       "Tasks bloqueadas por hook"]),
               b_alert("⚠️ Cuidado com Stop bloqueando",
                       "Hook Stop com block pode fazer agente nunca terminar. Use com extrema cautela.")]),
    ]
))

# T3.5 — Display
MODULES.append(Module(
    trail=3, n=5, emoji="🖥️", title="Display: tmux, iTerm2, split-pane",
    subtitle="Quando vale a pena ver tudo ao vivo, atalhos do lead e armadilhas por terminal.",
    duration_min=40, nivel="Intermediário", tipo="Reference",
    next_module_title="4.1 — 6 armadilhas e correções",
    next_module_url="../trilha4/modulo-4-1.html",
    topics=[
        Topic("🪟", "In-process: tudo no mesmo terminal", "Default conservador",
              "In-process: lead lista teammates; <kbd>Shift+Down</kbd> circula; <kbd>Enter</kbd> abre, <kbd>Esc</kbd> fecha. <strong class=\"text-purple-400\">Funciona em qualquer terminal</strong>.",
              [b_main("📌 Atalhos do in-process",
                      "Os 4 que você precisa decorar.",
                      ["<kbd>Shift+Down</kbd> — circula teammates",
                       "<kbd>Enter</kbd> — foca no teammate",
                       "<kbd>Esc</kbd> — interrompe turno",
                       "<kbd>Ctrl+T</kbd> — toggle task list"]),
               b_tip("💡 Mensagem direta",
                     "Selecione teammate (Shift+Down) e digite — mensagem vai direto.")]),
        Topic("📊", "Tmux: split-pane real", "Cada teammate em um pane",
              "Tmux: cada teammate ganha pane próprio; <strong class=\"text-purple-400\">você vê tudo simultaneamente</strong>. Para diagnóstico e demos é imbatível.",
              [b_main("📌 Setup",
                      "tmux precisa estar instalado.",
                      ["Instalar via package manager",
                       "<code>--teammate-mode tmux</code>",
                       "Default 'auto' usa tmux se já estiver dentro",
                       "Clique no pane para interagir"]),
               b_tip("💡 Layout",
                     "Comece com 2-3 teammates; 5+ em telas pequenas vira sopa.")]),
        Topic("🍎", "iTerm2 + it2 CLI", "Alternativa no macOS",
              "macOS: iTerm2 com <code class=\"text-purple-400\">it2</code> CLI + Python API entrega split-pane sem tmux puro. Mais 'nativo' no Mac.",
              [b_main("📌 Setup macOS",
                      "Combo recomendado.",
                      ["Instale it2 CLI",
                       "Settings → General → Magic → Enable Python API",
                       "Use <code>tmux -CC</code> dentro do iTerm2",
                       "Auto-detecta no modo 'auto'"])]),
        Topic("🪦", "Pitfalls em VS Code/Windows", "Onde split NÃO roda",
              "VS Code integrated terminal, Windows Terminal e Ghostty <strong class=\"text-purple-400\">NÃO suportam split-pane</strong>. Use in-process ou outro terminal.",
              [b_alert("⚠️ Sintoma típico",
                       "Você liga split-pane mas só vê o lead. Teammates 'sumiram'. Nenhum erro óbvio."),
               b_grid("✓ Funciona com split",
                      ["macOS Terminal + tmux", "iTerm2 + it2", "Linux com tmux", "kitty + tmux"],
                      "✗ Não funciona",
                      ["VS Code integrated", "Windows Terminal", "Ghostty", "Hyper"])]),
        Topic("⌨️", "Atalhos do lead", "Shift+Down, Ctrl+T, Esc",
              "Sem atalhos você perde 50% da produtividade. Com atalhos você opera o time como um pianista. <strong class=\"text-purple-400\">Decore os 4 principais</strong>.",
              [b_data("📊 Atalhos por modo",
                      ["In-process: Shift+Down, Enter, Esc, Ctrl+T",
                       "Tmux: Ctrl+B + arrows entre panes",
                       "iTerm2: Cmd+arrows entre panes",
                       "Universal: digitar para mensagem"])]),
        Topic("🧹", "Tmux órfão e cleanup", "Mate sessões esquecidas",
              "Quando o team não fecha limpo, sessões tmux ficam órfãs. <code class=\"text-purple-400\">tmux ls</code> + <code class=\"text-purple-400\">tmux kill-session -t &lt;name&gt;</code>.",
              [b_main("📌 Ordem certa de cleanup",
                      "Salve, limpe, feche.",
                      ["Save first (deliverables)",
                       "Cleanup via lead (não via tmux)",
                       "Verificar tmux ls",
                       "Kill se sobrou órfão"]),
               b_alert("⚠️ Não force kill como hábito",
                       "Force kill antes de cleanup leva a configs órfãs e estado inconsistente. Reserve para emergências.")]),
    ]
))

# T4.1 — 6 armadilhas
MODULES.append(Module(
    trail=4, n=1, emoji="⚠️", title="6 armadilhas e correções",
    subtitle="Permissões, conflito, ocioso, tokens, perda, aprovação — diagnóstico e correção.",
    duration_min=50, nivel="Intermediário", tipo="Diagnóstico",
    next_module_title="4.2 — Quando usar Teams",
    next_module_url="modulo-4-2.html",
    topics=[
        Topic("🔓", "Pedir permissões a toda hora", "Pré-aprove no settings",
              "Sintoma: cada teammate trava perguntando permissão para <code class=\"text-amber-400\">npm</code>, <code class=\"text-amber-400\">git</code>, etc. <strong class=\"text-amber-400\">Pré-aprovar dobra produtividade</strong>.",
              [b_main("📌 Allowlist canônica",
                      "Cole isso e ajuste.",
                      ["Bash(npm install)",
                       "Bash(npm test*)",
                       "Bash(git status)",
                       "Bash(git diff*)",
                       "Edit, Write, Read"]),
               b_alert("⚠️ Não use --dangerously-skip em prod",
                       "Atalho perigoso. Allowlist específica é o caminho certo.")]),
        Topic("📁", "Conflito de arquivo", "Atribua donos",
              "Dois teammates editando o mesmo arquivo; segundo sobrescreve. <strong class=\"text-amber-400\">É o erro mais difícil de detectar</strong> — não há crash, só código faltando.",
              [b_main("📌 Detecção",
                      "Como auditar.",
                      ["git diff por autor (teammate name)",
                       "Procure 2 commits no mesmo arquivo",
                       "Compare deliverables vs spawn",
                       "QA reproduz bug que 'já corrigiu'"]),
               b_tip("💡 Prevenção",
                     "Territórios por pasta no spawn: 'Backend possui src/api/, ninguém mais escreve lá'.")]),
        Topic("😴", "Agente ocioso", "Trabalho independente",
              "Teammate fica esperando; trabalho dele depende do anterior. Se 1 dos 5 fica ocioso 80% do tempo, você paga 5× e obtém 4×. <strong class=\"text-amber-400\">Custo silencioso</strong>.",
              [b_main("📌 Como evitar",
                      "Tasks independentes na partida.",
                      ["QA roda mocks enquanto Dev codifica",
                       "Frontend trabalha em UI estática enquanto Backend monta API",
                       "Security audita arquivos prontos enquanto outros continuam",
                       "Lead nunca espera por todos para falar"])]),
        Topic("💸", "Muitos tokens", "Menos agentes, modelos certos",
              "Conta dispara, throughput não acompanha. Sintoma típico de <strong class=\"text-amber-400\">'swarm' com 10+ agentes</strong>. Reduzir teammates ou trocar Sonnet por Haiku no QA corta 30-50% do custo.",
              [b_data("📊 Mix recomendado por papel",
                      ["QA simples → Haiku",
                       "Tech Writer → Haiku",
                       "Dev padrão → Sonnet",
                       "Architect → Opus (sparingly)",
                       "Security Reviewer → Sonnet"])]),
        Topic("📂", "Trabalho perdido", "Persista cedo, persista frequente",
              "Sessão fecha mal e algumas decisões/análises ficam só na memória do teammate — <strong class=\"text-amber-400\">perdidas</strong>. Salvar em arquivo é a única memória durável.",
              [b_main("📌 Padrões de persistência",
                      "Onde salvar o quê.",
                      ["Arquivos temporários por papel em <code>tmp/</code>",
                       "Resumos finais em <code>docs/</code>",
                       "Commit incremental no git",
                       "Mailbox preserva mensagens — leia antes do cleanup"])]),
        Topic("❓", "Aprovação errada", "Calibre com humano antes",
              "Lead aprova planos ruins ou rejeita planos bons; critério mal calibrado. <strong class=\"text-amber-400\">No início, peça revisão humana</strong>; depois delegue.",
              [b_timeline([
                  ("Fase 1", "Manual", "Humano aprova primeiros 5-10 planos"),
                  ("Captura", "Listar critérios", "Anote o que você usou para decidir"),
                  ("Codifica", "Critérios no prompt do lead", "Cole os critérios capturados"),
                  ("Delega", "Lead aprova", "Você só auditoria pós"),
                  ("Auditoria", "Refina", "Ajusta se taxa de aprovação x retrabalho desviar")
              ])]),
    ]
))

# T4.2 — Quando usar Teams
MODULES.append(Module(
    trail=4, n=2, emoji="🧭", title="Quando usar Teams",
    subtitle="Árvore de decisão e 5 estudos de caso aplicados.",
    duration_min=45, nivel="Intermediário", tipo="Decisão",
    next_module_title="4.3 — Custo e dimensionamento",
    next_module_url="modulo-4-3.html",
    topics=[
        Topic("✅", "Use Teams: 3+ áreas", "Front + back + tests",
              "Trabalho atravessa <strong class=\"text-amber-400\">3+ camadas técnicas independentes</strong>. Cross-layer é o caso de ouro: 3 contextos especializados em paralelo, com mailbox para contratos.",
              [b_main("📌 Casos canônicos",
                      "Padrões cross-layer.",
                      ["Front + back + DB",
                       "Mobile + API + analytics",
                       "ML + serving + observability",
                       "Frontend + backend + tests + docs"])]),
        Topic("🔬", "Use Teams: pesquisa paralela", "Hipóteses concorrentes",
              "Debug com várias teorias; PR review com múltiplas lentes; reproduzir bug por caminhos diferentes. <strong class=\"text-amber-400\">Anchoring é o inimigo da investigação</strong> — teammates adversariais colapsam o tempo.",
              [b_main("📌 Padrão de debate",
                      "5 teammates, 5 hipóteses.",
                      ["Cada um defende a sua",
                       "Mensagens P2P para refutar",
                       "Lead consolida ao final",
                       "Hipótese vencedora é a 'sobrevivente'"]),
               b_tip("💡 Quando aplicar",
                     "Bug intermitente que ninguém reproduz; PR controverso; arquitetura nova.")]),
        Topic("🤝", "Use Teams: react para colaborar", "Quality gates entre teammates",
              "Squad com QA reativo: Dev entrega, QA reprova/aprova, Dev refaz. <strong class=\"text-amber-400\">Subagent não consegue 'rejeitar e devolver'</strong> — só Teams faz quality gate dinâmico.",
              [b_main("📌 Anatomia do loop Dev↔QA",
                      "Mailbox como veículo do feedback.",
                      ["Dev manda artefato para QA",
                       "QA roda critérios",
                       "Se reprova, manda findings ao Dev",
                       "Dev corrige e devolve",
                       "Loop até OK"])]),
        Topic("❌", "Evite Teams: tarefa sequencial", "Use sessão única",
              "Tarefa que vai 1→2→3 sem ramificações: rename, refactor pequeno, tipagem. Team aqui só adiciona overhead. <strong class=\"text-amber-400\">Sessão única + subagent pontual basta</strong>.",
              [b_grid("✓ Sessão única ganha",
                      ["Refactor pequeno", "Rename de função", "Adicionar typing", "Bugfix localizado"],
                      "✗ Team perde",
                      ["Coordenação custa", "Overhead alto", "Sem paralelismo real", "5× custo, 1× resultado"])]),
        Topic("📃", "Evite Teams: mesmo arquivo/contexto", "Conflito é matemático",
              "Vários teammates editando o mesmo arquivo ou precisando do contexto compartilhado <strong class=\"text-amber-400\">não escala</strong>. Sessão única ou subagent é melhor.",
              [b_alert("⚠️ Pergunta-chave",
                       "'Quem dorme com qual arquivo?' Se a resposta for 'todos', NÃO use Team."),
               b_main("📌 Quando subagent serve melhor",
                      "Trabalho paraleliza mas não conversa.",
                      ["Sumário de logs",
                       "Análise de muitos arquivos",
                       "Pesquisa documental",
                       "Verificações independentes"])]),
        Topic("🌳", "Árvore de decisão final", "3 perguntas, 1 resposta",
              "<strong class=\"text-amber-400\">Decida em 30s</strong>: (1) precisam conversar entre si? (2) precisa paralelo real? (3) cabe em 1 contexto?",
              [b_data("📊 Tabela de decisão",
                      ["Sim/Sim/Não → Team",
                       "Não/Sim/Não → Subagentes",
                       "Não/Não/Sim → Single session",
                       "Sim/Não/* → Provavelmente single + subagents"]),
               b_tip("💡 Dúvida persistente?",
                     "Comece com subagents. Migra para Team só se sentir falta de mailbox.")]),
    ]
))

# T4.3 — Custo
MODULES.append(Module(
    trail=4, n=3, emoji="💰", title="Custo e dimensionamento",
    subtitle="Token economics, modelo por papel, regras de tamanho e medição.",
    duration_min=45, nivel="Intermediário", tipo="Reference",
    next_module_title="4.4 — Encerramento limpo",
    next_module_url="modulo-4-4.html",
    topics=[
        Topic("📐", "A regra linear: N agentes = N× custo", "Sem mágica",
              "Cada teammate = 1 contexto = 1 multiplicador linear. <strong class=\"text-amber-400\">5 agentes ≈ 5× sessão única</strong>. Saber a 'lei do custo' impede a sedução do swarm.",
              [b_data("📊 Decomposição do custo",
                      ["Custo = N × tokens médios × preço modelo",
                       "Ganho ≠ N×",
                       "Coordenação tem custo (mensagens)",
                       "Idle queima tokens sem retorno"]),
               b_alert("⚠️ Pegada típica",
                       "'Adicionar mais agentes vai resolver'. Quase nunca. Adicione modelo certo e prompt melhor antes.")]),
        Topic("🎯", "3-5 teammates é o doce-spot", "O número que importa",
              "Doc oficial e prática convergem. <strong class=\"text-amber-400\">Acima de 5, ganhos diminuem rápido</strong>. Menos de 3, raramente vale Teams sobre subagentes.",
              [b_main("📌 Heurística de tamanho",
                      "Quando aumentar.",
                      ["3 = mínimo viável (1 deve ser QA)",
                       "4-5 = sweet spot cross-layer",
                       "5-6 tasks/teammate",
                       "Promover só com evidência"]),
               b_tip("💡 Se tem 15 tasks", "Comece com 3 teammates. Aumente se medir gargalo.")]),
        Topic("🧬", "Modelo certo por papel", "Haiku para QA simples",
              "Misturar modelos por papel <strong class=\"text-amber-400\">reduz custo total em 30-50% sem perda de qualidade</strong>. QA simples → Haiku, Dev → Sonnet, Architect → Opus.",
              [b_data("📊 Mix recomendado",
                      ["Tech Writer → Haiku 4.5",
                       "QA simples → Haiku 4.5",
                       "QA complexo → Sonnet 4.6",
                       "Backend/Frontend → Sonnet 4.6",
                       "Security → Sonnet 4.6",
                       "Architect → Opus 4.7 (decisões críticas)"])]),
        Topic("📊", "Como medir custo real", "/cost e telemetria",
              "Use <code class=\"text-amber-400\">/cost</code> no Claude Code, hooks PostToolUse para logar tokens, relatórios por teammate. <strong class=\"text-amber-400\">Sem números, 'sentir caro' vira intuição ruim</strong>.",
              [b_main("📌 O que medir",
                      "Métricas por papel.",
                      ["Tokens input/output por papel",
                       "Tempo de wall-clock por papel",
                       "Ratio output/input",
                       "Identificar role mais caro",
                       "Comparar com run anterior"])]),
        Topic("✂️", "Quando subagent é mais barato", "Pesquisa que não conversa",
              "Pesquisa, busca de arquivos, sumário de logs — não precisa conversar. <strong class=\"text-amber-400\">Subagent ganha em custo</strong>.",
              [b_grid("✓ Subagent suficiente",
                      ["Sumário de logs", "Busca de arquivos", "PR review read-only", "Análise de doc"],
                      "✗ Precisa Team",
                      ["Cross-layer", "Loop Dev↔QA", "Hipóteses concorrentes", "Implementação cooperativa"])]),
        Topic("🛑", "Desligue cedo", "Mate o que está descarrilando",
              "Se um teammate vai para o caminho errado, <strong class=\"text-amber-400\">não espere ele 'achar'</strong>; desligue e respawne com prompt corrigido. Reset é barato.",
              [b_main("📌 Sinais de descarrilamento",
                      "Quando puxar o gatilho.",
                      ["Repete a mesma pergunta",
                       "Tools wrong (ex: editando lugar errado)",
                       "Tempo &gt; 2× do esperado",
                       "Output não converge para deliverable"]),
               b_tip("💡 Reset com aprendizado",
                     "Salve em arquivo o que ele descobriu antes de matar; spawne novo com isso no prompt.")]),
    ]
))

# T4.4 — Encerramento
MODULES.append(Module(
    trail=4, n=4, emoji="🚪", title="Encerramento limpo",
    subtitle="Save first, clean second, close third — e quem nunca deve rodar cleanup.",
    duration_min=40, nivel="Intermediário", tipo="Reference",
    next_module_title="4.5 — Limitações conhecidas",
    next_module_url="modulo-4-5.html",
    topics=[
        Topic("💾", "Save first", "Cada teammate salva o que produziu",
              "Antes de qualquer cleanup, peça que cada teammate <strong class=\"text-amber-400\">consolide arquivos finais e relatórios</strong>. É a única memória que sobra.",
              [b_main("📌 O que salvar por papel",
                      "Deliverables previstos no spawn.",
                      ["Backend → arquivos do código + endpoints",
                       "Frontend → componentes + screenshots",
                       "QA → tests/report.md",
                       "Security → security-report.md",
                       "Lead → docs/build-summary.md"])]),
        Topic("🧽", "Clean second", "Lead orquestra cleanup",
              "Lead pede shutdown a cada teammate; quando todos confirmam, roda <em>cleanup the team</em>. <strong class=\"text-amber-400\">Apenas o lead deve rodar cleanup</strong>.",
              [b_alert("⚠️ NÃO peça cleanup ao teammate",
                       "Teammate fazendo cleanup pode deixar resources inconsistentes. Sempre via lead."),
               b_main("📌 Ordem do cleanup",
                      "Lead garante.",
                      ["Pede shutdown a cada teammate",
                       "Espera confirmação",
                       "Verifica todos idle",
                       "Roda cleanup",
                       "Confirma sucesso"])]),
        Topic("🚪", "Close third", "Encerre a sessão do lead",
              "Após cleanup, encerre a sessão do lead. Os artefatos ficam, o estado do team some. <strong class=\"text-amber-400\">Não tente reusar o lead</strong> — spawne novo team.",
              [b_main("📌 Por que não reusar",
                      "Lead é fixo.",
                      ["Lead é fixo na sessão de origem",
                       "Sem promoção/transferência",
                       "Saída limpa = sem zumbis",
                       "Para continuar, novo team em nova sessão"])]),
        Topic("⚡", "Forçar encerramento", "Custo do shortcut",
              "Matar processo no terminal sem cleanup. Resultado: <strong class=\"text-amber-400\">arquivos órfãos, configs órfãs, estado desconhecido</strong>. Reservado para emergências.",
              [b_main("📌 Limpeza manual pós-kill",
                      "O que checar.",
                      ["<code>~/.claude/teams/&lt;team&gt;/</code> — apague",
                       "<code>~/.claude/tasks/&lt;team&gt;/</code> — apague",
                       "<code>tmux ls</code> + kill se houver órfão",
                       "git status — commit pendentes"]),
               b_alert("⚠️ Não use por preguiça",
                       "Force kill é última opção. Prefira shutdown gracioso, mesmo que demore alguns minutos.")]),
        Topic("📂", "Auditar pós-encerramento", "Onde fica o histórico",
              "Após cleanup, audite git diff, deliverables vs spawn e custo total. <strong class=\"text-amber-400\">É a hora de aprender</strong>. Pós-mortem rápido melhora os próximos prompts.",
              [b_data("📊 Checklist pós-mortem",
                      ["Deliverables OK?",
                       "Testes passam?",
                       "Custo previsto?",
                       "Armadilha encontrada?",
                       "Prompt-base merece update?"])]),
        Topic("🔁", "Replay de execução", "Reproduzir uma run boa",
              "Quando uma run dá certo, salve <strong class=\"text-amber-400\">prompt + settings + deliverables</strong> para repetir. Times reusáveis com prompts versionados é o pulo do gato.",
              [b_main("📌 O que versionar",
                      "Reprodutibilidade real.",
                      ["<code>prompts/spawn-X.md</code>",
                       "<code>.claude/settings.json</code>",
                       "<code>.claude/agents/*.md</code> usados",
                       "<code>.claude/hooks/*</code> ativos",
                       "Commit hash da run"])]),
    ]
))

# T4.5 — Limitações
MODULES.append(Module(
    trail=4, n=5, emoji="🚧", title="Limitações conhecidas",
    subtitle="A feature é experimental — saiba o que ainda não funciona.",
    duration_min=30, nivel="Intermediário", tipo="Reference",
    next_module_title="5.1 — Codex CLI Subagents",
    next_module_url="../trilha5/modulo-5-1.html",
    topics=[
        Topic("🔁", "/resume não restaura teammates", "In-process não persiste",
              "Após <code class=\"text-amber-400\">/resume</code>, o lead pode tentar mensageriar teammates que não existem mais. <strong class=\"text-amber-400\">Mande respawnar</strong>.",
              [b_main("📌 Workaround",
                      "Spawnando novos.",
                      ["Spawne novos teammates",
                       "Informe o lead da troca",
                       "Aceite o 'reset parcial'",
                       "Salve estado em arquivo antes de /resume"])]),
        Topic("⏳", "Status pode atrasar", "Tasks sem completar",
              "Teammate às vezes esquece de marcar task como completed e <strong class=\"text-amber-400\">bloqueia dependentes</strong>. Sintoma: time parece parado.",
              [b_main("📌 Como destravar",
                      "Quando aplicar cada um.",
                      ["Marque manualmente se task está realmente pronta",
                       "Cutuque o teammate via mensagem",
                       "Audit antes de cleanup",
                       "Considere TaskCompleted hook automático"])]),
        Topic("🐌", "Shutdown pode ser lento", "Aguarda turn ou tool",
              "Teammate <strong class=\"text-amber-400\">termina request/tool atual antes de sair</strong> — shutdown demora minutos se uma build estiver rodando.",
              [b_tip("💡 Espere",
                     "Não force kill se der tempo. Espera é mais limpa que arquivos órfãos."),
               b_main("📌 Tools típicas longas",
                      "Quem causa o delay.",
                      ["Build (npm run build, bundler)",
                       "Test suite completa",
                       "Migration de DB",
                       "Upload grande"])]),
        Topic("1️⃣", "1 team por sessão", "Cleanup antes de criar outro",
              "Um lead gerencia <strong class=\"text-amber-400\">apenas um team por vez</strong>. Cleanup antes de spawnar outro. Não há 'mudança de time' no meio.",
              [b_main("📌 Estratégia",
                      "Sessões separadas para teams independentes.",
                      ["Cleanup → novo spawn na mesma sessão",
                       "Sessões diferentes para teams paralelos",
                       "Plan-spawn-execute-cleanup como ciclo padrão",
                       "Não tente 'reaproveitar' o lead"])]),
        Topic("🪆", "Sem nested teams", "Teammate não spawna time",
              "Apenas o lead pode criar/gerenciar team. Teammates <strong class=\"text-amber-400\">não criam sub-teams</strong> nem outros teammates. Modelagem hierárquica não funciona.",
              [b_tip("💡 Workaround para 'ajudante'",
                     "Subagent dentro do teammate é OK. Use subagent para o ajudante de quem é teammate."),
               b_main("📌 Pense flat",
                      "Lead = único orquestrador.",
                      ["Sem nesting de teams",
                       "Subagents dentro de teammates: OK",
                       "Lead = único orquestrador",
                       "Pode promover via re-spawn em nova sessão"])]),
        Topic("🪟", "Split-pane requer terminal certo", "Tmux ou iTerm2",
              "VS Code Terminal, Windows Terminal e Ghostty <strong class=\"text-amber-400\">NÃO suportam split</strong>. Use in-process ou outro terminal.",
              [b_data("📊 Compatibilidade",
                      ["✓ Linux + tmux",
                       "✓ macOS + tmux",
                       "✓ macOS + iTerm2 + it2",
                       "✗ VS Code integrated",
                       "✗ Windows Terminal",
                       "✗ Ghostty"])]),
    ]
))

# T5.1 — Codex
MODULES.append(Module(
    trail=5, n=1, emoji="🔧", title="Codex CLI Subagents",
    subtitle="TOML, max_threads/max_depth, spawn_agents_on_csv e Symphony.",
    duration_min=50, nivel="Avançado", tipo="Mão na massa",
    next_module_title="5.2 — Gemini CLI Subagents",
    next_module_url="modulo-5-2.html",
    topics=[
        Topic("📁", "Onde definir agents", "~/.codex/agents/ ou .codex/agents/",
              "Cada agent é um arquivo TOML em <code class=\"text-teal-400\">~/.codex/agents/</code> (user) ou <code class=\"text-teal-400\">.codex/agents/</code> (projeto). Mesma ideia do Claude Code: <strong class=\"text-teal-400\">declarativo + reusável</strong>.",
              [b_main("📌 Anatomia mínima",
                      "Campos obrigatórios.",
                      ["name = \"security-reviewer\"",
                       "description = \"Audits auth code for vulnerabilities\"",
                       "developer_instructions = '''...'''"]),
               b_data("📊 Campos opcionais",
                      ["model = \"o3\"",
                       "sandbox_mode = \"workspace-write\"",
                       "mcp_servers = [\"linear\", \"github\"]",
                       "nickname_candidates = [\"Athena\", \"Hermes\"]"])]),
        Topic("⚙️", "Config global [agents]", "max_threads, max_depth",
              "Seção <code class=\"text-teal-400\">[agents]</code> no config global controla concorrência. <strong class=\"text-teal-400\">Sem isso, swarms descontrolados</strong>.",
              [b_data("📊 Defaults importantes",
                      ["max_threads = 6 (paralelismo)",
                       "max_depth = 1 (recursão)",
                       "job_max_runtime_seconds = ?",
                       "Threads = N de agents simultâneos",
                       "Depth = quanto pode recursar"]),
               b_tip("💡 Valor seguro",
                     "max_threads = 4-6 cobre 90% dos casos. Aumente só com motivo claro.")]),
        Topic("🪪", "Nicknames e display", "nickname_candidates",
              "Array <code class=\"text-teal-400\">nickname_candidates</code> dá nomes legíveis às múltiplas instâncias do mesmo agent. <strong class=\"text-teal-400\">Sem isso, instâncias ficam 'agent-1, agent-2...'</strong>.",
              [b_main("📌 Use <code>/agent</code>",
                      "Comando para alternar threads.",
                      ["<code>/agent</code> lista threads ativas",
                       "Selecione por número ou nickname",
                       "Inspect progress",
                       "Mensagem direta"]),
               b_tip("💡 Nicknames temáticos",
                     "Athena, Hermes, Apollo — facilitam memória vs 'agent-1, agent-2'.")]),
        Topic("📊", "spawn_agents_on_csv", "Batch experimental",
              "Tool experimental que processa <strong class=\"text-teal-400\">cada linha de CSV com 1 worker</strong> e exporta resultados consolidados. Casos como 'auditar 200 PRs' ficam triviais.",
              [b_main("📌 Casos de uso",
                      "Onde batch ganha.",
                      ["Auditar 200 PRs",
                       "Resumir 500 issues",
                       "Categorizar 1000 logs",
                       "Validar dados em lote"]),
               b_alert("⚠️ Respeita max_threads",
                       "Não tente burlar com batch — Codex respeita max_threads global.")]),
        Topic("🛡️", "Sandbox e approval inheritance", "Política do pai",
              "Subagents <strong class=\"text-teal-400\">herdam sandbox e approval policies do parent</strong>. Em CI/non-interactive, approval que não consegue subir falha o run.",
              [b_main("📌 Modos sandbox",
                      "Do mais restrito ao mais permissivo.",
                      ["read-only — leitura apenas",
                       "workspace-read — workspace + leitura",
                       "workspace-write — workspace + escrita",
                       "danger-full-access — tudo"]),
               b_tip("💡 CI",
                     "CI deve ter sandbox forte; sem aprovador humano para subir prompt.")]),
        Topic("🎼", "Symphony: orquestração no Linear", "Spec aberto",
              "Spec open-source da OpenAI que turbinou times reportadamente em <strong class=\"text-teal-400\">+500% de PRs aterrissados</strong> ao usar Linear como control plane.",
              [b_main("📌 Como funciona",
                      "Codex MCP server + Agents SDK.",
                      ["Linear ticket → trigger",
                       "Codex como MCP server",
                       "Agents SDK orquestra pipeline",
                       "PR de volta no ticket",
                       "Auditável e determinístico"]),
               b_tip("💡 Padrão a observar",
                     "Mesmo se você usa Claude Code Teams hoje, Symphony aponta para o ano que vem.")]),
    ]
))

# T5.2 — Gemini
MODULES.append(Module(
    trail=5, n=2, emoji="💎", title="Gemini CLI Subagents",
    subtitle="Markdown + YAML, @subagent, paralelismo e built-ins.",
    duration_min=45, nivel="Avançado", tipo="Mão na massa",
    next_module_title="5.3 — Padrão portátil",
    next_module_url="modulo-5-3.html",
    topics=[
        Topic("📝", "Formato Markdown + YAML", ".gemini/agents/*.md",
              "Cada subagent = arquivo .md com <strong class=\"text-teal-400\">frontmatter YAML</strong>; corpo do markdown é o system prompt. Familiar para quem usa Claude Code.",
              [b_data("📊 Frontmatter",
                      ["name (lowercase, hyphens, underscores)",
                       "description (curto)",
                       "kind: local (default) ou remote",
                       "tools: array com wildcards",
                       "model: override",
                       "temperature: 0.0-2.0",
                       "max_turns (default 30)",
                       "timeout_mins (default 10)"])]),
        Topic("@", "@nome para forçar uso", "Determinismo",
              "Prefixar com <code class=\"text-teal-400\">@subagent_name</code> força uso explícito sem deixar o main agent escolher. <strong class=\"text-teal-400\">Bom para debug</strong>.",
              [b_grid("✓ Auto-delegation",
                      ["Main agent escolhe", "Mais rápido em fluxo normal", "Bom para uso geral", "Reduz fricção"],
                      "✗ Auto-delegation",
                      ["Pode atrapalhar reproduzir bug", "Não-determinístico", "Difícil de testar"])]),
        Topic("⚡", "Paralelismo em Gemini", "Múltiplas instâncias",
              "Gemini suporta <strong class=\"text-teal-400\">vários subagents (ou várias instâncias) em paralelo</strong>. Padrão 'tool exposto ao agente principal' + paralelismo.",
              [b_main("📌 Vantagens",
                      "Reduz wall-clock real.",
                      ["Pesquisas paralelas",
                       "Mesmo subagent N vezes",
                       "Cada um com prompt diferente",
                       "Main agent coleta resultados"]),
               b_alert("⚠️ Sem nesting",
                       "Subagent não pode invocar outro subagent (recursion protection).")]),
        Topic("🛠️", "Built-ins prontos", "codebase, cli_help, generalist, browser",
              "Antes de criar subagent novo, <strong class=\"text-teal-400\">veja se um built-in já resolve</strong>. Reduz manutenção.",
              [b_data("📊 Built-ins disponíveis",
                      ["codebase_investigator — exploração de código",
                       "cli_help — doc de CLIs",
                       "generalist — task pesada genérica",
                       "browser_agent (experimental) — interação web"])]),
        Topic("🌎", "Remote subagents", "kind: remote",
              "Subagents podem rodar <strong class=\"text-teal-400\">remotamente</strong> (kind: remote). Útil para isolamento ou recursos diferentes.",
              [b_main("📌 Casos para remote",
                      "Quando vale a pena.",
                      ["Work pesado em CI",
                       "Privacidade local",
                       "Recursos especiais (GPU)",
                       "Compliance"]),
               b_tip("💡 Observabilidade",
                     "Remote merece observabilidade extra — você não vê tudo no terminal.")]),
        Topic("🚧", "Limitações principais", "Sem subagent → subagent",
              "Subagent <strong class=\"text-teal-400\">não pode invocar outro subagent</strong> (recursion protection). Tools restritos por allowlist. Modelagem hierárquica não funciona.",
              [b_main("📌 Pense flat",
                      "Main agent como orquestrador.",
                      ["Flat &gt; nested",
                       "Tools whitelisted no frontmatter",
                       "Isolamento total de contexto",
                       "Main agent coordena"])]),
    ]
))

# T5.3 — Padrão portátil
MODULES.append(Module(
    trail=5, n=3, emoji="🧩", title="Padrão portátil",
    subtitle="A 'interface mental' que vale para Claude Code, Codex e Gemini.",
    duration_min=50, nivel="Avançado", tipo="Síntese",
    next_module_title="5.4 — Capstone: NeuroFlow Pro",
    next_module_url="modulo-5-4.html",
    topics=[
        Topic("🧠", "Role + Tools + Owned Files + Handoff", "4 atributos universais",
              "Toda definição de agent em qualquer runtime tem 4 conceitos: <strong class=\"text-teal-400\">papel, tools permitidas, arquivos que possui, e quem recebe seu output</strong>. Pensar nesse contrato te dá portabilidade.",
              [b_main("📌 O contrato",
                      "Mude só sintaxe.",
                      ["<strong>Role</strong> = system prompt",
                       "<strong>Tools</strong> = allowlist",
                       "<strong>Owned files</strong> = território",
                       "<strong>Handoff</strong> = mailbox/return"])]),
        Topic("📋", "Mapeamento Claude/Codex/Gemini", "Tabela 1:1",
              "Cada conceito tem nome em cada runtime. <strong class=\"text-teal-400\">Tabela mental de tradução</strong> acelera migração.",
              [b_data("📊 Equivalências",
                      ["Definição: frontmatter (Claude) / TOML (Codex) / YAML (Gemini)",
                       "Tools: array em todos",
                       "Mailbox: SendMessage (Claude Teams) / N/A em subagents",
                       "Plan mode: Claude Code only"])]),
        Topic("🔄", "Lab: PR review nos 3 runtimes", "O mesmo squad portado",
              "Implemente o squad de PR review (security + perf + tests) nos 3 runtimes. <strong class=\"text-teal-400\">Lado a lado solidifica a abstração</strong>.",
              [b_timeline([
                  ("Setup Claude", "subagents em .claude/agents/", "3 .md com frontmatter; spawn como teammates"),
                  ("Setup Codex", ".codex/agents/*.toml", "3 TOML com developer_instructions"),
                  ("Setup Gemini", ".gemini/agents/*.md", "3 .md com YAML; @-mention para forçar"),
                  ("Run", "Mesmo PR nos 3", "Compare findings"),
                  ("Aprenda", "Diff entre runtimes", "Mesmo squad, sintaxe diferente")
              ])]),
        Topic("🎚️", "Quando trocar de runtime", "Critérios práticos",
              "Claude Code Teams quando precisa de mailbox; Codex quando quer Symphony/Linear; Gemini quando integra com Google. <strong class=\"text-teal-400\">Não brigue com o runtime</strong>.",
              [b_grid("✓ Claude Code Teams",
                      ["Mailbox real", "Plan mode embutido", "Hooks ricos", "Subagent definitions"],
                      "✓ Codex / Gemini",
                      ["Symphony (Codex)", "Google Workspace (Gemini)", "Sandbox CI (Codex)", "Browser_agent (Gemini)"])]),
        Topic("📤", "Exportar prompts entre runtimes", "Conversões automáticas",
              "Um prompt-base + 3 wrappers (frontmatter, TOML, YAML) é o que você quer manter. <strong class=\"text-teal-400\">Source of truth = .md</strong>; wrappers em geradores.",
              [b_main("📌 Padrão recomendado",
                      "1 fonte, N saídas.",
                      ["Prompt-base em prompts/X.md",
                       "Geradores produzem .toml e .yaml",
                       "CI valida que estão sincronizados",
                       "Mude 1 vez, propaga"])]),
        Topic("📚", "Frameworks acima dos CLIs", "LangGraph, CrewAI, Agents SDK",
              "Quando complexidade cresce (cycles, branching, observabilidade), framework Python pode <strong class=\"text-teal-400\">substituir o CLI</strong>. Trade-off de produtividade vs controle.",
              [b_data("📊 Quando cada um",
                      ["CrewAI: papéis, prototipo rápido (2-3 dias)",
                       "AutoGen / AG2: GroupChat, debate adversarial",
                       "LangGraph: grafo, cycles, observabilidade prod",
                       "Agents SDK: pipeline declarativo + Codex MCP"])]),
    ]
))

# T5.4 — Capstone
MODULES.append(Module(
    trail=5, n=4, emoji="🎓", title="Capstone: NeuroFlow Pro",
    subtitle="Squad de 5 agentes constrói app full-stack com auth + testes + relatório QA + doc.",
    duration_min=240, nivel="Avançado", tipo="Projeto final",
    next_module_title="Voltar à trilha 5",
    next_module_url="index.html",
    topics=[
        Topic("📋", "Briefing", "O que será construído",
              "App full-stack: <strong class=\"text-teal-400\">API REST (users + posts), front React, JWT, suíte de testes, relatório QA, doc operacional</strong>. Realista para exercitar todas as armadilhas; pequeno o suficiente para 4h.",
              [b_main("📌 Deliverables obrigatórios",
                      "Critério de aceite do capstone.",
                      ["App rodando em localhost:3000",
                       "tests/report.md com pass/fail",
                       "docs/build-summary.md com decisões",
                       "docs/cost-report.md com tokens por papel",
                       "Auth JWT funcionando"])]),
        Topic("👥", "Squad sugerido (5 agentes)", "Backend, Frontend, QA, Sec, Tech Writer",
              "<strong class=\"text-teal-400\">5 teammates Sonnet</strong> com territórios distintos: src/api, src/ui, tests/, audits/, docs/. Aplicação prática de tudo que veio antes.",
              [b_data("📊 Squad",
                      ["Backend Dev (Sonnet) → src/api/",
                       "Frontend Dev (Sonnet) → src/ui/",
                       "QA Engineer (Haiku) → tests/",
                       "Security Reviewer (subagent definition, Sonnet) → audits/",
                       "Tech Writer (Haiku) → docs/"]),
               b_tip("💡 Mix de modelos",
                     "QA e Tech Writer em Haiku; resto Sonnet. Reduz custo sem perder qualidade.")]),
        Topic("📐", "Rubrica de avaliação", "100 pontos",
              "<strong class=\"text-teal-400\">Critérios objetivos</strong> forçam você a aplicar conceitos do curso, não só 'fazer rodar'.",
              [b_data("📊 Pontos",
                      ["25 — prompt segue template e separa territórios",
                       "20 — hooks ativos (≥ 1 quality gate)",
                       "20 — testes verdes",
                       "15 — cost report coerente",
                       "10 — cleanup limpo (sem tmux órfão)",
                       "10 — portabilidade (1 papel em Codex ou Gemini)"])]),
        Topic("🪝", "Quality gates obrigatórios", "Hooks que bloqueiam",
              "Pelo menos <strong class=\"text-teal-400\">1 hook ativo</strong>: tests passando ao TaskCompleted, ou block-rm em PreToolUse. Hook é o que separa demo de entrega.",
              [b_main("📌 Hook canônico para o capstone",
                      "TaskCompleted que roda testes.",
                      [".claude/hooks/test-on-complete.sh",
                       "Roda npm test do path da task",
                       "Exit 2 com saída se falha",
                       "Stderr volta ao teammate",
                       "Configurado em .claude/settings.json"])]),
        Topic("📊", "Cost report", "Tokens, modelos, justificativa",
              "Documento <code class=\"text-teal-400\">docs/cost-report.md</code> com <strong class=\"text-teal-400\">tokens por teammate, modelo escolhido por papel, e justificativa do tamanho do squad</strong>. Mostra que entende custo.",
              [b_main("📌 Estrutura do report",
                      "Vá direto ao ponto.",
                      ["Tabela: papel | modelo | tokens in | tokens out",
                       "Decisões de modelo (por que cada um)",
                       "'Por que 5 e não 3'",
                       "Alternativas consideradas e descartadas",
                       "Total de custo da run"])]),
        Topic("🎬", "Apresentação final", "5 min de demo + 5 min de Q&A",
              "Grave 5 min mostrando spawn, mailbox, idle notifications e cleanup; depois discuta decisões. <strong class=\"text-teal-400\">Apresentar consolida</strong>; outros aprendem com seus erros e acertos.",
              [b_main("📌 Estrutura da demo (5 min)",
                      "Cada parte do ciclo.",
                      ["0:00-0:30 — prompt do spawn",
                       "0:30-2:00 — execução paralela (split-pane)",
                       "2:00-3:00 — mailbox em ação (Dev↔QA)",
                       "3:00-4:00 — quality gate via hook",
                       "4:00-5:00 — cleanup limpo"]),
               b_tip("💡 Tempo curto força clareza",
                     "Mostre só o que importa. Admita o que não funcionou.")]),
    ]
))


def main():
    out_dir = lambda t: os.path.join(ROOT, "curso", f"trilha{t}")
    written = []
    for m in MODULES:
        os.makedirs(out_dir(m.trail), exist_ok=True)
        path = os.path.join(out_dir(m.trail), f"modulo-{m.trail}-{m.n}.html")
        html = render_module(m)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(path)
    print(f"Wrote {len(written)} modules:")
    for p in written:
        print("  -", os.path.relpath(p, ROOT))

if __name__ == "__main__":
    main()
