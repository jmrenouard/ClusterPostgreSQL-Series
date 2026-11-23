"""MkDocs Material build hooks for ClusterPostgreSQL-Series."""

from __future__ import annotations

import os
from pathlib import Path
import posixpath
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.structure.files import Files

DEFAULT_REPO_URL = "https://github.com/jmrenouard/ClusterPostgreSQL-Series"
VIRTUAL_DOCS: dict[str, tuple[str, str]] = {
    "overview-en.md": ("README.md", ""),
    "overview-fr.md": ("README.fr.md", ""),
    "stacks-overview.md": ("stacks/README.md", "stacks"),
}
STATIC_TREES = ("assets", "dashboard")
_ALT_DIRS = {
    "en": ("README.fr.md", "/fr/overview-fr", "docs/fr/index.md", "/fr", ("fr/", "01-tutoriels/", "02-guides-pratiques/")),
    "fr": ("README.md", "/overview-en", "docs/en/index.md", "", ("en/", "01-tutorials/", "02-how-to-guides/")),
}
ALERT_MAP = {"NOTE": "note", "TIP": "tip", "IMPORTANT": "info", "WARNING": "warning", "CAUTION": "danger"}
_FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
_ALERT_RE = re.compile(
    r"(?m)^([ \t]*)>[ \t]*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*([^\r\n]*)\r?\n((?:[ \t]*>.*(?:\r?\n|$))*)"
)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_HTML_ATTR_RE = re.compile(r"""(<(?:img|a|source)\b[^>]*?\b(?:src|href)\s*=\s*)(["'])([^"']+)\2""", re.I)


def gfm_slugify(value: str, separator: str = "-") -> str:
    """Slugify headings with GitHub Flavored Markdown anchor rules."""
    return "".join(
        separator if ch == " " else ch
        for ch in value.strip().lower()
        if ch.isalnum() or ch in (" ", "-", "_")
    )


def _repo_ref(raw_ref: str | None = None) -> str:
    """Resolve Git ref for repository blob/tree URLs."""
    ref = (raw_ref if raw_ref is not None else os.environ.get("DOCS_REPO_REF", "main")).strip()
    return "main" if not ref or ref in {"WORKTREE", "HEAD", "origin/main"} else ref


def _split_fences(md: str) -> list[tuple[bool, str]]:
    """Split Markdown into (is_fence, text) chunks preserving newlines."""
    chunks, buf, in_f, fc, fl = [], [], False, "", 0
    for ln in md.splitlines(keepends=True):
        s = ln.rstrip("\r\n")
        if not in_f:
            if m := _FENCE_RE.match(s):
                if buf:
                    chunks.append((False, "".join(buf)))
                    buf.clear()
                in_f, fc, fl = True, m.group(2)[0], len(m.group(2))
        elif (ls := s.lstrip(" \t")).startswith(fc) and len(ls) - len(ls.lstrip(fc)) >= fl and not ls.lstrip(fc).strip():
            buf.append(ln)
            chunks.append((True, "".join(buf)))
            buf.clear()
            in_f, fc, fl = False, "", 0
            continue
        buf.append(ln)
    if buf:
        chunks.append((in_f, "".join(buf)))
    return chunks


def _fmt_alert(m: re.Match[str]) -> str:
    """Convert one GitHub alert match into a Material admonition block."""
    ws, kind, title, body = m.group(1), ALERT_MAP[m.group(2).upper()], m.group(3).strip(), m.group(4)
    out = [f'{ws}!!! {kind} "{title}"\n' if title else f"{ws}!!! {kind}\n"]
    for raw in body.splitlines(keepends=True):
        stripped = raw.rstrip("\r\n")
        inner, nl = re.sub(r"^[ \t]*>[ \t]?", "", stripped), raw[len(stripped) :] or "\n"
        out.append(nl if not inner.strip() else f"{ws}    {inner}{nl}")
    return "".join(out)


def convert_github_alerts(markdown: str) -> str:
    """Convert GitHub blockquote alerts to Material admonitions outside fences."""
    return "".join(c if f else _ALERT_RE.sub(_fmt_alert, c) for f, c in _split_fences(markdown))


def _esc(text: str, pos: int) -> bool:
    """Return True if character at pos is backslash-escaped."""
    cur = pos - 1
    while cur >= 0 and text[cur] == "\\":
        cur -= 1
    return ((pos - 1 - cur) & 1) == 1


def _match_delim(text: str, start: int, o: str, c: str, skip_code: bool) -> int | None:
    """Find matching closing delimiter while respecting escapes and inline code."""
    depth, i, n = 1, start + 1, len(text)
    while i < n:
        ch = text[i]
        if skip_code and ch == "`":
            tl = 1
            while i + tl < n and text[i + tl] == "`":
                tl += 1
            if (end := text.find("`" * tl, i + tl)) == -1:
                return None
            i = end + tl
            continue
        if not skip_code and ch == "\n":
            return None
        if ch == o and not _esc(text, i):
            depth += 1
        elif ch == c and not _esc(text, i):
            depth -= 1
            if depth == 0:
                return i
        elif skip_code and ch == "\n" and i + 1 < n and text[i + 1] == "\n":
            return None
        i += 1
    return None


def _site_lang(cfg: Any) -> str:
    """Return theme language."""
    try:
        return str(cfg.theme["language"] or "en").lower()
    except (AttributeError, KeyError, TypeError):
        return "en"


def _alt_url(rel: str, lang: str, ud: bool, anc: str) -> str | None:
    """Rewrite excluded cross-language link to sibling EN/FR site."""
    if not (spec := _ALT_DIRS.get(lang)):
        return None
    rm, rm_u, idx, pre, dirs = spec
    sub = rel[5:] if rel.startswith("docs/") else ""
    base = rm_u if rel == rm else (pre if rel == idx else (f"{pre}/{sub}" if sub.startswith(dirs) else None))
    if base is None:
        return None
    b = base[:-3] if base.endswith(".md") else base
    if ud:
        return f"{b[:-6] if b.endswith('/index') else b}/{anc}"
    return f"{'/fr/index' if b == '/fr' else (b or '/index')}.html{anc}"


def _resolve_target(
    raw_url: str, page_src: str, pfx: str, ref: str, repo_url: str,
    docs_dir: Path | None = None, lang: str = "en", ud: bool = True,
) -> str:
    """Resolve a repository-relative target URL for MkDocs publishing."""
    if not raw_url or raw_url.startswith(("#", "/", "\\")) or _SCHEME_RE.match(raw_url):
        return raw_url
    path_part, sep, frag = raw_url.partition("#")
    anchor = f"{sep}{frag}" if sep else ""
    if not path_part:
        return raw_url
    ns = page_src.replace("\\", "/").lstrip("/")
    fr_i = lang == "fr" and ns == "index.md" and docs_dir is not None and (docs_dir / "fr" / "index.md").is_file()
    src_dir = "docs/fr" if fr_i else (VIRTUAL_DOCS[ns][1] if ns in VIRTUAL_DOCS else posixpath.dirname(f"docs/{ns}"))
    tslash = path_part.endswith("/")
    rel = posixpath.normpath(posixpath.join(src_dir, path_part)) if src_dir else posixpath.normpath(path_part)
    if (alt := _alt_url(rel, lang, ud, anchor)) is not None:
        return alt
    clean_repo = repo_url.rstrip("/")
    repo_root = docs_dir.parent if docs_dir is not None else None
    direct = {
        "README.md": "overview-en.md",
        "README.fr.md": "overview-fr.md",
        "stacks/README.md": "stacks-overview.md",
        "docs/index.md": "index.md",
        "docs/en/index.md": "index.md",
        "docs/fr/index.md": "index.md",
    }
    if rel in direct:
        return f"{pfx}{direct[rel]}{anchor}"
    if rel.startswith("docs/"):
        sub = rel[5:]
        if docs_dir is not None and (docs_dir / sub).is_dir() and (docs_dir / sub / "index.md").is_file():
            sub = posixpath.join(sub.rstrip("/"), "index.md")
        return f"{pfx}{sub}{'/' if tslash and sub and not sub.endswith('/') else ''}{anchor}"
    if rel in STATIC_TREES or rel.startswith(("assets/", "dashboard/")):
        return f"{pfx}{rel}{'/' if tslash and not rel.endswith('/') else ''}{anchor}"
    if rel in (".", "..") or rel.startswith("../"):
        return clean_repo
    kind = "tree" if (tslash or (repo_root is not None and (repo_root / rel).is_dir())) else "blob"
    return f"{clean_repo}/{kind}/{ref}/{rel}{'/' if tslash and not rel.endswith('/') else ''}{anchor}"


def _split_dest(raw_dest: str) -> tuple[str, str, bool]:
    """Split Markdown link destination into (url, title_suffix, had_angles)."""
    s = raw_dest.strip()
    if s.startswith("<") and (end := s.find(">")) != -1:
        return s[1:end].strip(), s[end + 1 :], True
    for i, ch in enumerate(s):
        if ch.isspace():
            return s[:i], s[i:], False
    return s, "", False


def _rewrite_prose(
    text: str, page_src: str, md_pfx: str, html_pfx: str, ref: str, repo_url: str,
    docs_dir: Path | None, lang: str = "en", ud: bool = True,
) -> str:
    """Rewrite Markdown links and HTML src/href outside inline code."""
    out, pstart, i, n = [], 0, 0, len(text)

    def _flush(end_i: int) -> None:
        if end_i > pstart:
            out.append(
                _HTML_ATTR_RE.sub(
                    lambda m: f"{m.group(1)}{m.group(2)}{_resolve_target(m.group(3), page_src, html_pfx, ref, repo_url, docs_dir, lang, ud)}{m.group(2)}",
                    text[pstart:end_i],
                )
            )

    while i < n:
        ch = text[i]
        if ch == "`":
            _flush(i)
            tl = 1
            while i + tl < n and text[i + tl] == "`":
                tl += 1
            if (end := text.find("`" * tl, i + tl)) == -1:
                out.append(text[i:])
                pstart = n
                break
            out.append(text[i : end + tl])
            i = pstart = end + tl
            continue
        is_img = ch == "!" and i + 1 < n and text[i + 1] == "[" and not _esc(text, i)
        bs = i + 1 if is_img else (i if ch == "[" and not _esc(text, i) else -1)
        if bs != -1 and (be := _match_delim(text, bs, "[", "]", True)) is not None:
            if be + 1 < n and text[be + 1] == "(" and (pe := _match_delim(text, be + 1, "(", ")", False)) is not None:
                _flush(i)
                lbl = _rewrite_prose(text[bs + 1 : be], page_src, md_pfx, html_pfx, ref, repo_url, docs_dir, lang, ud)
                url, sfx, ang = _split_dest(text[be + 2 : pe])
                nu = _resolve_target(url, page_src, md_pfx, ref, repo_url, docs_dir, lang, ud)
                out.append(f"{'!' if is_img else ''}[{lbl}]({f'<{nu}>' if ang else nu}{sfx})")
                i = pstart = pe + 1
                continue
        i += 1
    _flush(n)
    return "".join(out)


def rewrite_relative_links(
    markdown: str,
    page_src_path: str,
    ref: str = "main",
    repo_url: str = DEFAULT_REPO_URL,
    docs_dir: Path | None = None,
    use_directory_urls: bool = True,
    lang: str = "en",
) -> str:
    """Rewrite repo-relative links and HTML attributes outside code fences."""
    norm = page_src_path.replace("\\", "/").lstrip("/")
    md_d = norm.count("/")
    html_d = md_d + (0 if (not use_directory_urls or norm == "index.md" or norm.endswith("/index.md")) else 1)
    r_ref, r_docs = _repo_ref(ref), Path(docs_dir) if docs_dir is not None else None
    return "".join(
        c if f else _rewrite_prose(c, norm, "../" * md_d, "../" * html_d, r_ref, repo_url, r_docs, lang, use_directory_urls)
        for f, c in _split_fences(markdown)
    )


def on_config(config: Any) -> Any:
    """Attach GFM heading slugifier without requiring PYTHONPATH on CLI."""
    mdx = getattr(config, "mdx_configs", None)
    if isinstance(mdx, dict):
        toc_cfg = mdx.setdefault("toc", {})
        if isinstance(toc_cfg, dict) and not toc_cfg.get("slugify"):
            toc_cfg["slugify"] = gfm_slugify
    return config


def on_files(files: Files, config: Any) -> Files:
    """Inject language-filtered virtual docs, assets/, and dashboard/."""
    from mkdocs.structure.files import File

    lang, dp = _site_lang(config), Path(config.docs_dir)
    root, has_excl = dp.parent, bool(getattr(config, "exclude_docs", None))
    if lang == "fr" and (fr_i := dp / "fr" / "index.md").is_file():
        for u in ("index.md", "fr/index.md"):
            if f := files.get_file_from_path(u):
                files.remove(f)
        files.append(File.generated(config, "index.md", abs_src_path=str(fr_i)))
    skip_v = ("overview-fr.md" if lang == "en" else "overview-en.md") if has_excl else ""
    for uri, (rel_path, _) in VIRTUAL_DOCS.items():
        if uri != skip_v and (p := root / rel_path).is_file() and files.get_file_from_path(uri) is None:
            files.append(File.generated(config, uri, abs_src_path=str(p)))
    for tree in STATIC_TREES:
        if not (base := root / tree).is_dir():
            continue
        for item in sorted(base.rglob("*")):
            if item.is_file():
                rel = item.relative_to(base)
                if not any(pt.startswith(".") or pt == "__pycache__" for pt in rel.parts):
                    if files.get_file_from_path(uri := f"{tree}/{rel.as_posix()}") is None:
                        files.append(File.generated(config, uri, abs_src_path=str(item)))
    return files


def on_page_markdown(markdown: str, page: Any, config: Any, files: Files) -> str:
    """Convert alerts, rewrite links, and fix virtual edit URLs."""
    del files
    lang = _site_lang(config)
    src = getattr(page.file, "src_uri", None) or str(page.file.src_path).replace("\\", "/")
    ref, repo_url = _repo_ref(), (getattr(config, "repo_url", None) or DEFAULT_REPO_URL).rstrip("/")
    rd = getattr(config, "docs_dir", None) or (config.get("docs_dir") if isinstance(config, dict) else None)
    if getattr(page, "edit_url", None):
        if lang == "fr" and src == "index.md" and rd and (Path(rd) / "fr" / "index.md").is_file():
            page.edit_url = f"{repo_url}/edit/{ref}/docs/fr/index.md"
        elif src in VIRTUAL_DOCS:
            page.edit_url = f"{repo_url}/edit/{ref}/{VIRTUAL_DOCS[src][0]}"
    eff = lang if (getattr(config, "exclude_docs", None) or lang == "fr") else ""
    return rewrite_relative_links(
        convert_github_alerts(markdown), page_src_path=src, ref=ref, repo_url=repo_url,
        docs_dir=Path(rd) if rd else None,
        use_directory_urls=bool(getattr(config, "use_directory_urls", True)), lang=eff,
    )
