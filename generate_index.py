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
    :root { color-scheme: dark; --bg: #071c13; --panel: #0d3021; --panel-2: #145136; --text: #f2fff7; --muted: #add5bd; --accent: #76f0a7; --line: #2d7852; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: linear-gradient(145deg, #176b43 0, var(--bg) 42rem); color: var(--text); font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(1100px, calc(100% - 2rem)); margin: 0 auto; padding: 2.5rem 0 5rem; }
    header { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 1rem; margin-bottom: 1.5rem; }
    h1 { margin: 0; font-size: clamp(2rem, 7vw, 4.2rem); line-height: 1; letter-spacing: -.04em; }
    .subtitle { margin: .65rem 0 0; color: var(--muted); }
    .controls { display: flex; gap: .5rem; }
    button { border: 1px solid var(--line); border-radius: .55rem; padding: .55rem .8rem; background: var(--panel); color: var(--text); cursor: pointer; }
    button:hover { background: var(--panel-2); }
    details { border: 1px solid var(--line); border-radius: .7rem; background: color-mix(in srgb, var(--panel) 92%, transparent); }
    details + details { margin-top: .75rem; }
    details details { margin: .55rem 0 0 1rem; background: rgba(255, 255, 255, .025); }
    summary { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; padding: .8rem 1rem; cursor: pointer; font-weight: 700; }
    .season > summary { padding: 1rem 1.2rem; font-size: 1.4rem; background: var(--panel-2); border-radius: .65rem; }
    .day > summary { font-size: 1.08rem; }
    .count, .size { flex: 0 0 auto; color: var(--muted); font-size: .82rem; font-weight: 500; }
    .content { padding: .15rem .85rem .9rem; }
    ul { margin: .15rem 0 0; padding: 0 0 0 1.2rem; list-style: none; }
    li.folder-node + li.folder-node { margin-top: .55rem; }
    li.file { display: flex; justify-content: space-between; gap: 1rem; padding: .32rem .25rem; border-bottom: 1px solid rgba(173, 213, 189, .12); }
    li.file:last-child { border-bottom: 0; }
    a { min-width: 0; color: var(--accent); overflow-wrap: anywhere; text-decoration-thickness: .08em; text-underline-offset: .16em; }
    a:hover { color: #c7ffdc; }
    .empty { margin: .5rem 1rem 1rem; color: var(--muted); font-style: italic; }
    @media (max-width: 600px) { main { width: min(100% - 1rem, 1100px); padding-top: 1.25rem; } header { align-items: start; } .controls { width: 100%; } button { flex: 1; } details details { margin-left: .35rem; } summary { padding-inline: .7rem; } .size { display: none; } }
  </style>
</head>
<body>
<main>
  <header>
    <div><h1>PT Agility Streams</h1><p class="subtitle">Vídeos e ficheiros de provas.</p></div>
    <div class="controls"><button type="button" data-action="expand">Expandir tudo</button><button type="button" data-action="collapse">Recolher tudo</button></div>
  </header>
"""

HTML_END = """  <script>
    document.querySelector("[data-action=expand]").addEventListener("click", () => document.querySelectorAll("details").forEach(item => item.open = true));
    document.querySelector("[data-action=collapse]").addEventListener("click", () => document.querySelectorAll("details").forEach(item => item.open = false));
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
    lines.append(
        f'{indent}<li class="file"><a href="{href}">{name}</a>'
        f'<span class="size">{format_file_size(file.size)}</span></li>'
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
                f"        <summary><span>{escape(day.name)}</span>"
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
