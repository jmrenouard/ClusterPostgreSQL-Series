#!/usr/bin/env python3
"""Build and verify the zero-CDN static GitHub Pages bundle in _site/."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH_DIR, ASSETS_DIR, DEFAULT_OUT = ROOT / "dashboard", ROOT / "assets", ROOT / "_site"
TEXT_EXTS = {".html", ".css", ".js", ".svg", ".json", ".txt", ".md"}
EXT_RX = re.compile(r"^(?:https?:)?//", re.I)
SKIP_RX = re.compile(r"^(?:https?://|//|mailto:|tel:|data:|javascript:|#)", re.I)
REFRESH_RX = re.compile(r"url\s*=\s*['\"]?([^'\"\s;]+)", re.I)
BANNED = (
    ("secret-store", re.compile(r"\b(?:k[e]epass|v[a]ult|password[_ -]?manag[e]r)\b|\.(?:kdb[x]|key[x])\b", re.I)),
    ("local-path", re.compile(r"[A-Za-z]:\\[U]sers\\|/mnt/[c]/|\b[D]ropbox\b", re.I)),
    ("token", re.compile(r"(?:gh[p]|gh[o]|github_p[a]t)_[A-Za-z0-9_]{16,}|\bAKI[A][0-9A-Z]{16}\b")),
)
REDIRECT_HTML = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<meta http-equiv="refresh" content="0; url=dashboard/index.html">'
    "<title>ClusterPostgreSQL-Series | Offline Benchmark Explorer</title>"
    "<style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:grid;place-items:center;min-height:100vh;margin:0}a{color:#38bdf8}</style>"
    '</head><body><p>Redirecting to <a href="dashboard/index.html">ClusterPostgreSQL-Series Benchmark Explorer</a>...</p>'
    '<script>window.location.replace("dashboard/index.html");</script></body></html>\n'
)


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cdn: list[str] = []
        self.rel: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t, amap = tag.lower(), {k.lower(): (v or "").strip() for k, v in attrs}
        if t == "meta" and amap.get("http-equiv", "").lower() == "refresh":
            m = REFRESH_RX.search(amap.get("content", ""))
            if m and not SKIP_RX.match(m.group(1)):
                self.rel.append(m.group(1))
            return
        for a in ("src", "href", "data"):
            val = amap.get(a, "")
            if not val:
                continue
            if t in {"script", "link", "img"} and a in {"src", "href"} and EXT_RX.match(val):
                self.cdn.append(f"<{t} {a}={val}>")
            elif not SKIP_RX.match(val):
                self.rel.append(val)


def _copy_tree(src: pathlib.Path, dst: pathlib.Path) -> int:
    n = 0
    for item in sorted(src.rglob("*")):
        if item.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in item.relative_to(src).parts):
            dst_f = dst / item.relative_to(src)
            dst_f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, dst_f)
            n += 1
    return n


def build_pages_bundle(out_dir: pathlib.Path = DEFAULT_OUT) -> dict[str, int]:
    """Stage _site/ with .nojekyll, index.html redirect, dashboard/, and assets/."""
    out = out_dir.resolve()
    if out == out.parent or any(out == d.resolve() or d.resolve().is_relative_to(out) for d in (ROOT, DASH_DIR, ASSETS_DIR)):
        raise ValueError(f"Refusing unsafe output directory: {out}")
    if not (DASH_DIR / "index.html").is_file():
        raise FileNotFoundError(f"Missing dashboard entrypoint: {DASH_DIR / 'index.html'}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8", newline="\n")
    (out / "index.html").write_text(REDIRECT_HTML, encoding="utf-8", newline="\n")
    dn, an = _copy_tree(DASH_DIR, out / "dashboard"), _copy_tree(ASSETS_DIR, out / "assets")
    return {"files": dn + an + 2, "dashboard_files": dn, "asset_files": an, "bytes": sum(p.stat().st_size for p in out.rglob("*") if p.is_file())}


def verify_pages_bundle(out_dir: pathlib.Path = DEFAULT_OUT) -> list[str]:
    """Verify .nojekyll, zero CDN refs, relative link resolution, and hygiene."""
    out, errs = out_dir.resolve(), []
    if not out.is_dir():
        return [f"Missing bundle dir: {out}"]
    for req in (".nojekyll", "index.html", "dashboard/index.html"):
        if not (out / req).is_file():
            errs.append(f"Missing required artifact: {req}")
    for hp in sorted(out.rglob("*.html")):
        p = _LinkCollector()
        p.feed(hp.read_text(encoding="utf-8"))
        rel_h = hp.relative_to(out).as_posix()
        errs.extend(f"External CDN ref in {rel_h}: {c}" for c in p.cdn)
        for ref in p.rel:
            clean = ref.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            target = (hp.parent / clean).resolve()
            if not target.is_relative_to(out):
                errs.append(f"Escaping path in {rel_h}: {ref}")
            elif not target.is_file():
                errs.append(f"Broken relative link in {rel_h}: {ref}")
    for fp in sorted(out.rglob("*")):
        if fp.is_file() and fp.suffix.lower() in TEXT_EXTS:
            txt, rel_f = fp.read_text(encoding="utf-8", errors="ignore"), fp.relative_to(out).as_posix()
            errs.extend(f"Hygiene violation ({lbl}) in {rel_f}" for lbl, pat in BANNED if pat.search(txt))
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build or verify static GitHub Pages bundle.")
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.check:
        errs = verify_pages_bundle(args.out)
        if errs:
            print("\n".join(f"[FAIL] {e}" for e in errs), file=sys.stderr)
            return 1
        print(f"[OK] Pages bundle verified: {args.out}")
        return 0
    st = build_pages_bundle(args.out)
    print(f"[OK] Built Pages bundle in {args.out}: {st['files']} files ({st['bytes']:,} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
