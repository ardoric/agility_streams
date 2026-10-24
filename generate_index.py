from __future__ import annotations

import argparse
import os
import re
import tempfile
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote


SEASON_PATTERN = re.compile(r"\d{4}-\d{2}")
DEFAULT_SOURCE = Path("Z:\\")
DEFAULT_OUTPUT = Path(__file__).with_name("index.html")

HTML_START = """<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <base href="/videos/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PT Agility Streams</title>
  <style>
    :root { color-scheme: dark; --bg: #183d28; --panel: #224e32; --text: #f3fff5; --muted: #c5dfcb; --accent: #c3f7ae; --line: #587f60; }
    * { box-sizing: border-box; }
    [hidden] { display: none !important; }
    body { margin: 0; min-height: 100vh; background: radial-gradient(ellipse at 85% 0, #365e39 0, transparent 38rem), var(--bg); color: var(--text); font: 15px/1.6 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    button, input { font: inherit; }
    :focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
    main { width: min(1120px, calc(100% - 3rem)); margin: 0 auto; }
    .masthead { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem 0; border-bottom: 1px solid var(--line); }
    .brand { display: flex; align-items: center; gap: .7rem; font-weight: 700; letter-spacing: -.02em; }
    .brand-mark { display: grid; place-items: center; width: 2rem; height: 2rem; border-radius: .65rem; background: var(--accent); color: var(--bg); font-size: .85rem; }
    .masthead-note, .eyebrow { color: var(--accent); font-size: .72rem; text-transform: uppercase; letter-spacing: .17em; font-weight: 650; }
    .hero { padding: 3.5rem 0 2.5rem; }
    .eyebrow { margin: 0 0 .85rem; }
    h1 { max-width: 850px; margin: 0; font-size: clamp(2.5rem, 6vw, 4.6rem); font-weight: 650; line-height: 1.08; letter-spacing: -.055em; }
    h1 span { color: var(--accent); }
    .subtitle { max-width: 38rem; margin: 1.2rem 0 0; color: var(--muted); font-size: 1.05rem; }
    .stats { display: flex; flex-wrap: wrap; gap: 1.5rem 3rem; margin: 0 0 2.5rem; padding: 1.3rem 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
    .stats div { display: flex; align-items: baseline; gap: .65rem; }
    .stats dt { color: var(--muted); font-size: .85rem; order: 1; }
    .stats dd { margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -.04em; font-variant-numeric: tabular-nums; }
    .toolbar { display: flex; flex-wrap: wrap; align-items: end; gap: 1rem; margin-bottom: .8rem; }
    .search { flex: 1; min-width: min(100%, 20rem); }
    .search label { display: block; color: var(--muted); margin-bottom: .5rem; font-size: .8rem; }
    .search input { width: 100%; min-height: 3rem; padding: .7rem 1rem; border: 1px solid var(--line); border-radius: .7rem; background: var(--panel); color: var(--text); }
    .search input::placeholder { color: var(--muted); opacity: 1; }
    .controls { display: flex; gap: .5rem; }
    button { min-height: 3rem; border: 1px solid var(--line); border-radius: .7rem; padding: .65rem .95rem; background: transparent; color: var(--text); cursor: pointer; }
    button:hover { background: #315f3c; border-color: #83ac85; }
    .archive-meta { display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; margin: 0 0 1.3rem; color: var(--muted); font-size: .8rem; }
    .archive { padding-bottom: 3rem; }
    details { border: 1px solid var(--line); border-radius: .85rem; background: var(--panel); }
    .season + .season { margin-top: 1rem; }
    summary { display: flex; align-items: center; gap: .85rem; padding: 1rem; cursor: pointer; list-style: none; }
    summary::-webkit-details-marker { display: none; }
    summary::before { content: ""; width: .45rem; height: .45rem; flex-shrink: 0; border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted); transform: rotate(-45deg); transition: transform .15s; }
    details[open] > summary::before { transform: rotate(45deg); }
    summary:hover { color: var(--accent); }
    summary > span:first-of-type { min-width: 0; overflow-wrap: anywhere; }
    .season > summary { padding: 1.3rem 1.4rem; font-size: 1.3rem; font-weight: 600; letter-spacing: -.025em; }
    .season[open] > summary { border-bottom: 1px solid var(--line); }
    .season > .content { padding: .3rem 1.2rem 1rem; }
    .day { border: 0; border-bottom: 1px solid var(--line); border-radius: 0; background: transparent; }
    .day:last-child { border-bottom: 0; }
    .day > summary { padding: 1.2rem .2rem; font-size: .98rem; font-weight: 550; }
    .day[open] > summary { color: var(--accent); }
    .count { margin-left: auto; color: var(--muted); font-size: .78rem; font-weight: 400; letter-spacing: 0; text-align: right; flex-shrink: 0; }
    .content { padding: 0 0 .9rem .8rem; }
    ul { margin: 0; padding: 0; list-style: none; }
    .folder { margin: .5rem 0; background: #1d442c; border-radius: .6rem; }
    .folder > summary { font-size: .9rem; }
    .folder ul { padding: 0 .8rem .5rem; }
    li.file { display: flex; align-items: center; gap: .5rem; border-bottom: 1px solid #426b4c; }
    li.file:last-child { border-bottom: 0; }
    .file a { display: flex; align-items: center; gap: .8rem; min-width: 0; padding: .8rem .5rem; border-radius: .4rem; color: var(--text); text-decoration: none; }
    .file a:hover { background: #315f3c; color: var(--accent); }
    .file-link { flex: 1; }
    .file .download-link, .player-download { display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; width: 44px; height: 44px; padding: .6rem; border: 1px solid var(--line); border-radius: .5rem; color: var(--accent); text-decoration: none; }
    .download-icon { display: block; width: 20px; height: 20px; flex-shrink: 0; background: currentColor; mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v12m-5-5 5 5 5-5M5 16v4a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-4'/%3E%3C/svg%3E") center / contain no-repeat; }
    .player-download:hover { background: #315f3c; }
    .player-open { overflow: hidden; }
    .player { width: min(960px, calc(100% - 2rem)); max-height: calc(100dvh - 2rem); padding: 1rem; border: 1px solid var(--line); border-radius: 1rem; background: var(--panel); color: var(--text); }
    .player::backdrop { background: rgb(0 0 0 / .8); }
    .player-header { display: flex; align-items: start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
    .player h2 { margin: 0; font-size: 1rem; overflow-wrap: anywhere; }
    .player form { flex-shrink: 0; }
    .player video { display: block; width: 100%; max-height: 65dvh; background: #000; border-radius: .5rem; }
    .player-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-top: 1rem; }
    .player-actions a { color: var(--accent); }
    .player-error { color: #ffb9a9; }
    .file-type { display: grid; place-items: center; flex: 0 0 2.4rem; height: 2rem; border: 1px solid #6f9773; border-radius: .4rem; color: var(--accent); font-size: .6rem; font-weight: 700; letter-spacing: .04em; }
    .file-name { min-width: 0; overflow-wrap: anywhere; font-size: .88rem; }
    .size { margin-left: auto; flex-shrink: 0; color: var(--muted); font-size: .75rem; font-variant-numeric: tabular-nums; }
    .file-arrow { color: var(--muted); flex-shrink: 0; }
    .empty { margin: 1rem 0; padding: 1.5rem; border: 1px dashed var(--line); border-radius: .7rem; color: var(--muted); }
    footer { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .5rem; padding: 1.5rem 0 2rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .75rem; }
    @media (max-width: 640px) {
      main { width: calc(100% - 2rem); }
      .masthead-note { display: none; }
      .hero { padding: 2.5rem 0 2rem; }
      .stats { gap: 1rem 1.8rem; }
      .stats div { display: block; }
      .stats dd { font-size: 1.5rem; }
      .stats dt { font-size: .75rem; }
      .controls { width: 100%; }
      .controls button { flex: 1; }
      .season > summary { padding: 1rem; font-size: 1.1rem; flex-wrap: wrap; gap: .6rem; }
      .season > summary .count { width: 100%; margin-left: 1.1rem; text-align: left; }
      .season > .content { padding-inline: .7rem; }
      .day > summary { align-items: start; flex-wrap: wrap; }
      .day > summary::before { margin-top: .5rem; }
      .day > summary > span:first-of-type { flex: 1; }
      .day > summary .count { width: 100%; margin-left: 1.3rem; text-align: left; }
      .content { padding-left: .2rem; }
      .file a { gap: .5rem; flex-wrap: wrap; }
      .file-name { flex: 1; }
      .size { width: 100%; margin-left: 2.9rem; }
      .file-arrow { display: none; }
      .file { flex-wrap: wrap; padding-bottom: .5rem; }
      .file-link { flex-basis: 100%; }
      .file .download-link { margin-left: 2.9rem; }
    }
    @media (prefers-reduced-motion: reduce) { summary::before { transition: none; } }
  </style>
</head>
<body>
<main>
  <header class="masthead">
    <div class="brand"><span class="brand-mark" aria-hidden="true">PT</span> PT Agility Streams</div>
    <span class="masthead-note">O arquivo do agility português</span>
  </header>
  <section class="hero" aria-labelledby="page-title">
    <p class="eyebrow">Provas. Percursos. Memórias.</p>
    <h1 id="page-title">O agility português,<br><span>prova a prova.</span></h1>
    <p class="subtitle">Reveja cada percurso. Explore os vídeos e ficheiros das provas, organizados por época e por dia.</p>
  </section>
"""

HTML_END = r"""  </section>
  <footer><span>PT Agility Streams &middot; Arquivo de provas</span><span>Feito para quem vive o agility.</span></footer>
  <dialog id="video-player" class="player" aria-labelledby="player-title">
    <div class="player-header">
      <h2 id="player-title">Reproduzir vídeo</h2>
      <form method="dialog"><button type="submit" autofocus>Fechar</button></form>
    </div>
    <video controls autoplay playsinline preload="metadata" aria-label="Reprodutor de vídeo"></video>
    <p id="player-error" class="player-error" role="alert" hidden>Não foi possível reproduzir este vídeo. Tente abrir o ficheiro diretamente ou descarregá-lo.</p>
    <div class="player-actions">
      <a class="player-download" download aria-label="Descarregar vídeo" title="Descarregar vídeo"><span class="download-icon" aria-hidden="true"></span></a>
      <a class="player-direct" target="_blank" rel="noopener">Abrir ficheiro diretamente</a>
    </div>
  </dialog>
  <script>
    const details = [...document.querySelectorAll("details")];
    const search = document.querySelector("#search");
    const status = document.querySelector("#search-status");
    const empty = document.querySelector("#no-results");
    const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt");
    const files = [...document.querySelectorAll(".file")].map(element => ({
      element,
      text: normalize(decodeURIComponent(element.querySelector("a").getAttribute("href"))),
    }));
    const groups = [...details].reverse().map(element => {
      const container = element.querySelector(":scope > .content > ul")
        || element.querySelector(":scope > ul")
        || element.querySelector(":scope > .content");
      return { element, children: container ? [...container.children] : [] };
    });
    let savedOpen = new Map(details.map(item => [item, item.open]));
    let searching = false;
    search.addEventListener("input", () => {
      const tokens = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      if (tokens.length && !searching) savedOpen = new Map(details.map(item => [item, item.open]));
      searching = tokens.length > 0;
      let matches = 0;
      files.forEach(({element, text}) => {
        element.hidden = !tokens.every(token => text.includes(token));
        if (!element.hidden) matches++;
      });
      groups.forEach(({element, children}) => {
        element.hidden = searching && !children.some(child => !child.hidden);
        if (element.parentElement.classList.contains("folder-node")) element.parentElement.hidden = element.hidden;
        element.open = searching ? !element.hidden : savedOpen.get(element);
      });
      empty.hidden = !searching || matches > 0;
      status.textContent = searching ? `${matches.toLocaleString("pt-PT")} ficheiros encontrados` : "Explore o arquivo por época e por dia.";
    });
    document.querySelector("[data-action=expand]").addEventListener("click", () => details.forEach(item => { if (!item.hidden) item.open = true; }));
    document.querySelector("[data-action=collapse]").addEventListener("click", () => details.forEach(item => item.open = false));
    const player = document.querySelector("#video-player");
    const video = player.querySelector("video");
    const playerError = document.querySelector("#player-error");
    document.querySelector("#archive").addEventListener("click", event => {
      const link = event.target.closest("a[data-player]");
      if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      if (!player.showModal) return;
      event.preventDefault();
      const name = link.querySelector(".file-name").textContent;
      player.querySelector("#player-title").textContent = name;
      player.querySelector(".player-download").href = link.href;
      player.querySelector(".player-download").download = name;
      player.querySelector(".player-direct").href = link.href;
      playerError.hidden = true;
      player.showModal();
      document.documentElement.classList.add("player-open");
      video.src = link.href;
    });
    player.addEventListener("close", () => {
      video.pause();
      video.removeAttribute("src");
      video.load();
      document.documentElement.classList.remove("player-open");
    });
    player.addEventListener("click", event => {
      if (event.target !== player) return;
      const bounds = player.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) player.close();
    });
    video.addEventListener("error", () => {
      if (video.hasAttribute("src")) playerError.hidden = false;
    });
  </script>
</main>
</body>
</html>
"""


@dataclass(frozen=True)
class FileItem:
    name: str
    path: Path
    size: int


@dataclass(frozen=True)
class DirectoryNode:
    name: str
    directories: tuple[DirectoryNode, ...]
    files: tuple[FileItem, ...]
    file_count: int


@dataclass(frozen=True)
class Season:
    name: str
    days: tuple[DirectoryNode, ...]
    file_count: int


def scan_directory(path: Path) -> DirectoryNode:
    directories: list[DirectoryNode] = []
    files: list[FileItem] = []

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    directories.append(scan_directory(Path(entry.path)))
                elif entry.is_file(follow_symlinks=False):
                    files.append(
                        FileItem(
                            name=entry.name,
                            path=Path(entry.path),
                            size=entry.stat(follow_symlinks=False).st_size,
                        )
                    )
    except OSError as error:
        raise RuntimeError(f"Não foi possível ler {path}: {error}") from error

    directories.sort(key=lambda item: item.name, reverse=True)
    files.sort(key=lambda item: item.name, reverse=True)
    file_count = len(files) + sum(item.file_count for item in directories)
    return DirectoryNode(path.name, tuple(directories), tuple(files), file_count)


def scan_seasons(source: Path) -> tuple[Season, ...]:
    if not source.is_dir():
        raise RuntimeError(f"A pasta de origem não está acessível: {source}")

    try:
        season_paths = sorted(
            (
                item
                for item in source.iterdir()
                if item.is_dir() and SEASON_PATTERN.fullmatch(item.name)
            ),
            key=lambda item: item.name,
            reverse=True,
        )
    except OSError as error:
        raise RuntimeError(f"Não foi possível ler {source}: {error}") from error

    seasons: list[Season] = []
    for season_path in season_paths:
        try:
            day_paths = sorted(
                (item for item in season_path.iterdir() if item.is_dir()),
                key=lambda item: item.name,
                reverse=True,
            )
        except OSError as error:
            raise RuntimeError(
                f"Não foi possível ler {season_path}: {error}"
            ) from error

        days = tuple(scan_directory(day_path) for day_path in day_paths)
        seasons.append(
            Season(
                name=season_path.name,
                days=days,
                file_count=sum(day.file_count for day in days),
            )
        )

    return tuple(seasons)


def format_file_size(size: int) -> str:
    if size >= 1024**3:
        return f"{size / 1024**3:,.1f} GB"
    if size >= 1024**2:
        return f"{size / 1024**2:,.1f} MB"
    if size >= 1024:
        return f"{size / 1024:,.1f} KB"
    return f"{size} B"


def file_href(file: FileItem, source: Path) -> str:
    return "/".join(quote(part, safe="") for part in file.path.relative_to(source).parts)


def render_file(lines: list[str], file: FileItem, source: Path, depth: int) -> None:
    indent = "  " * depth
    href = escape(file_href(file, source), quote=True)
    name = escape(file.name)
    file_type = escape(file.path.suffix.lstrip(".").upper() or "FILE")
    is_video = file.path.suffix.lower() == ".mp4"
    player_attributes = (
        ' data-player aria-haspopup="dialog" aria-controls="video-player"'
        ' title="Reproduzir vídeo"'
        if is_video
        else ""
    )
    download = (
        f'<a class="download-link" href="{href}" download="{name}"'
        f' aria-label="Descarregar {name}" title="Descarregar vídeo">'
        '<span class="download-icon" aria-hidden="true"></span></a>'
        if is_video
        else ""
    )
    arrow = "&#9654;" if is_video else "&nearr;"
    lines.append(
        f'{indent}<li class="file"><a class="file-link" href="{href}"{player_attributes}>'
        f'<span class="file-type" aria-hidden="true">{file_type}</span>'
        f'<span class="file-name">{name}</span>'
        f'<span class="size">{format_file_size(file.size)}</span>'
        f'<span class="file-arrow" aria-hidden="true">{arrow}</span></a>{download}</li>'
    )


def render_directory(
    lines: list[str], directory: DirectoryNode, source: Path, depth: int
) -> None:
    indent = "  " * depth
    lines.append(f'{indent}<li class="folder-node">')
    lines.append(f'{indent}  <details class="folder">')
    lines.append(
        f"{indent}    <summary><span>{escape(directory.name)}</span>"
        f'<span class="count">{directory.file_count} ficheiros</span></summary>'
    )
    lines.append(f"{indent}    <ul>")
    for child in directory.directories:
        render_directory(lines, child, source, depth + 3)
    for file in directory.files:
        render_file(lines, file, source, depth + 3)
    lines.append(f"{indent}    </ul>")
    lines.append(f"{indent}  </details>")
    lines.append(f"{indent}</li>")


def render_index(
    seasons: tuple[Season, ...], source: Path, latest_days_open: int
) -> str:
    lines = [HTML_START.rstrip("\n")]
    day_count = sum(len(season.days) for season in seasons)
    file_count = sum(season.file_count for season in seasons)
    lines.extend(
        [
            '  <dl class="stats" aria-label="O arquivo em números">',
            f"    <div><dt>épocas</dt><dd>{len(seasons)}</dd></div>",
            f"    <div><dt>dias de provas</dt><dd>{day_count}</dd></div>",
            f"    <div><dt>ficheiros</dt><dd>{file_count:,}</dd></div>".replace(",", " "),
            "  </dl>",
            '  <div class="toolbar">',
            '    <div class="search"><label for="search">Pesquisar no arquivo</label>',
            '      <input id="search" type="search" placeholder="Nome, data, grau ou clube..." aria-controls="archive" autocomplete="off"></div>',
            '    <div class="controls"><button type="button" data-action="expand">Expandir tudo</button><button type="button" data-action="collapse">Recolher tudo</button></div>',
            "  </div>",
            '  <div class="archive-meta"><span id="search-status" role="status">Explore o arquivo por época e por dia.</span><span>Mais recentes primeiro</span></div>',
            '  <section id="archive" class="archive" aria-label="Épocas e provas">',
            '    <p id="no-results" class="empty" hidden>Nenhum ficheiro encontrado. Experimente outro nome, data ou grau.</p>',
        ]
    )

    for season_index, season in enumerate(seasons):
        season_open = " open" if season_index == 0 else ""
        lines.append(f'  <details class="season"{season_open}>')
        lines.append(
            f"    <summary><span>Época {escape(season.name)}</span>"
            f'<span class="count">{len(season.days)} dias &middot; '
            f"{season.file_count} ficheiros</span></summary>"
        )
        lines.append('    <div class="content">')

        for day_index, day in enumerate(season.days):
            day_open = (
                " open"
                if season_index == 0 and day_index < latest_days_open
                else ""
            )
            lines.append(f'      <details class="day"{day_open}>')
            lines.append(
                f"        <summary><span>{escape(day.name.replace('_', ' '))}</span>"
                f'<span class="count">{day.file_count} ficheiros</span></summary>'
            )

            if not day.directories and not day.files:
                lines.append('        <p class="empty">Sem ficheiros</p>')
            else:
                lines.append('        <div class="content"><ul>')
                for directory in day.directories:
                    render_directory(lines, directory, source, 6)
                for file in day.files:
                    render_file(lines, file, source, 6)
                lines.append("        </ul></div>")

            lines.append("      </details>")

        lines.append("    </div>")
        lines.append("  </details>")

    lines.append(HTML_END.rstrip("\n"))
    return "\n".join(lines) + "\n"


def write_atomically(output: Path, content: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, output)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Não foi possível escrever {output}: {error}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera o índice HTML do Agility PT Streams."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=r"Pasta de origem (predefinição: Z:\).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Ficheiro HTML de destino (predefinição: index.html junto ao script).",
    )
    parser.add_argument(
        "--latest-days-open",
        type=int,
        default=2,
        help="Número de dias mais recentes que ficam abertos (predefinição: 2).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica se o índice está atualizado sem o alterar.",
    )
    args = parser.parse_args()

    if args.latest_days_open < 0:
        parser.error("--latest-days-open não pode ser negativo")

    return args


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()

    try:
        seasons = scan_seasons(source)
        content = render_index(seasons, source, args.latest_days_open)
    except RuntimeError as error:
        print(f"Erro: {error}")
        return 1

    day_count = sum(len(season.days) for season in seasons)
    file_count = sum(season.file_count for season in seasons)

    if args.check:
        try:
            current_content = output.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Desatualizado: {output} não existe.")
            return 1
        except OSError as error:
            print(f"Erro: não foi possível ler {output}: {error}")
            return 1

        if current_content != content:
            print(f"Desatualizado: {output}")
            return 1

        print(
            f"Atualizado: {len(seasons)} épocas, {day_count} dias e "
            f"{file_count} ficheiros."
        )
        return 0

    try:
        write_atomically(output, content)
    except RuntimeError as error:
        print(f"Erro: {error}")
        return 1

    print(
        f"Gerado {output}: {len(seasons)} épocas, {day_count} dias e "
        f"{file_count} ficheiros."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
