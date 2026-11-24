#!/usr/bin/env python3
"""Build and verify the MkDocs Material site bundle for IONOS Apache hosting."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "site"
TEXT_EXTS = {".html", ".css", ".js", ".svg", ".json", ".txt"}
SKIP_RX = re.compile(r"^(?:https?://|//|mailto:|tel:|data:|javascript:|#)", re.I)
BANNED = (
    ("secret-store", re.compile(r"\b(?:k[e]epass|v[a]ult|password[_ -]?manag[e]r)\b|\.(?:kdb[x]|key[x])\b", re.I)),
    ("local-path", re.compile(r"[A-Za-z]:\\[U]sers\\|/mnt/[c]/|\b[D]ropbox\b", re.I)),
    ("token", re.compile(r"(?:gh[p]|gh[o]|github_p[a]t)_[A-Za-z0-9_]{16,}|\bAKI[A][0-9A-Z]{16}\b")),
)
REQUIRED_SITE_FILES = (
    "index.html",
    ".htaccess",
    "404.html",
    "dashboard/index.html",
    "assets/charts/chart_01_tps_log_all_suites.png",
    "overview-en/index.html",
    "stacks-overview/index.html",
    "en/01_executive_summary_and_taxonomy/index.html",
    "en/14_transparent_data_encryption_tde/index.html",
    "en/solutions/yt_cluster_lite/index.html",
    "fr/index.html",
    "fr/overview-fr/index.html",
    "fr/dashboard/index.html",
    "fr/fr/01_synthese_et_taxonomie/index.html",
    "fr/fr/14_chiffrement_transparent_tde/index.html",
    "fr/fr/solutions/yt_cluster_lite/index.html",
)


class _LinkCollector(HTMLParser):
    """Collect local src/href attributes from generated HTML pages."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        for key, val in attrs:
            if key.lower() in {"src", "href"} and val:
                cleaned = val.strip()
                if cleaned and not SKIP_RX.match(cleaned):
                    self.refs.append(cleaned)


def render_htaccess() -> str:
    """Render Apache .htaccess for IONOS with HTTPS 301, headers, and caching."""
    return """# ClusterPostgreSQL-Series MkDocs Apache Configuration (IONOS)
Options -Indexes -MultiViews
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml
  AddOutputFilterByType DEFLATE application/javascript application/json image/svg+xml
</IfModule>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
  Header always set X-Frame-Options "SAMEORIGIN"
</IfModule>

<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /

  # Enforce HTTPS
  RewriteCond %{HTTPS} !=on
  RewriteCond %{HTTP:X-Forwarded-Proto} !https [NC]
  RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</IfModule>
"""


def _resolve_mkdocs_cmd(mkdocs_bin: str | None) -> list[str]:
    """Resolve the MkDocs CLI invocation command."""
    if mkdocs_bin:
        return [mkdocs_bin]
    if exe := shutil.which("mkdocs"):
        return [exe]
    return [sys.executable, "-m", "mkdocs"]


def build_mkdocs_site(
    out_dir: pathlib.Path = DEFAULT_OUT,
    strict: bool = True,
    mkdocs_bin: str | None = None,
) -> dict[str, int | str]:
    """Build EN and FR MkDocs Material sites into out_dir and write root .htaccess."""
    out = out_dir.resolve()
    protected = (ROOT, ROOT / "docs", ROOT / "scripts", ROOT / "assets", ROOT / "dashboard")
    if out == out.parent or any(out == d.resolve() or d.resolve().is_relative_to(out) for d in protected):
        raise ValueError(f"Refusing unsafe output directory: {out}")
    if out.exists():
        shutil.rmtree(out, ignore_errors=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("NO_MKDOCS_2_WARNING", "1")
    mk_cmd = _resolve_mkdocs_cmd(mkdocs_bin)
    targets = [(ROOT / "mkdocs.yml", out)]
    if (fr_cfg := ROOT / "mkdocs.fr.yml").is_file():
        targets.append((fr_cfg, out / "fr"))
    for cfg_path, dest in targets:
        cmd = [*mk_cmd, "build", "-f", str(cfg_path), "-d", str(dest)]
        if strict:
            cmd.append("--strict")
        subprocess.run(cmd, cwd=str(ROOT), env=env, check=True)
    (out / ".htaccess").write_text(render_htaccess(), encoding="utf-8", newline="\n")
    files = [p for p in out.rglob("*") if p.is_file()]
    return {"files": len(files), "bytes": sum(p.stat().st_size for p in files), "out_dir": str(out)}


def verify_mkdocs_site(out_dir: pathlib.Path = DEFAULT_OUT) -> list[str]:
    """Verify required files, .htaccess, zero leaks, valid local links, and hygiene."""
    out = out_dir.resolve()
    if not out.is_dir():
        return [f"Missing site dir: {out}"]
    errs = [f"Missing required artifact: {req}" for req in REQUIRED_SITE_FILES if not (out / req).is_file()]
    ht_path = out / ".htaccess"
    if ht_path.is_file():
        ht = ht_path.read_text(encoding="utf-8", errors="ignore")
        for tok in ("Options -Indexes", "RewriteEngine On", "R=301"):
            if tok not in ht:
                errs.append(f"Missing .htaccess directive: {tok}")

    for path in sorted(out.rglob("*")):
        rel = path.relative_to(out)
        if any(part in {".agents", ".git"} for part in rel.parts):
            errs.append(f"Forbidden repository artifact leaked: {rel.as_posix()}")
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in TEXT_EXTS or path.name == ".htaccess":
            txt = path.read_text(encoding="utf-8", errors="ignore")
            errs.extend(f"Hygiene violation ({lbl}) in {rel.as_posix()}" for lbl, pat in BANNED if pat.search(txt))
        if path.suffix.lower() == ".html":
            parser = _LinkCollector()
            parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
            for ref in parser.refs:
                clean = ref.split("#", 1)[0].split("?", 1)[0]
                if not clean:
                    continue
                target = (out / clean.lstrip("/")).resolve() if clean.startswith("/") else (path.parent / clean).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.is_relative_to(out) or not target.is_file():
                    errs.append(f"Broken local ref in {rel.as_posix()}: {ref}")
    return errs


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for building and checking MkDocs Material site bundles."""
    ap = argparse.ArgumentParser(description="Build and verify MkDocs Material site for IONOS.")
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--strict", dest="strict", action="store_true", default=True)
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--mkdocs-bin", default=None)
    args = ap.parse_args(argv)

    if not args.check_only:
        st = build_mkdocs_site(args.out, strict=args.strict, mkdocs_bin=args.mkdocs_bin)
        print(f"[OK] Built MkDocs site in {st['out_dir']}: {st['files']} files ({st['bytes']:,} B)")
    if args.check or args.check_only:
        errs = verify_mkdocs_site(args.out)
        if errs:
            print("\n".join(f"[FAIL] {e}" for e in errs), file=sys.stderr)
            return 1
        print(f"[OK] MkDocs site verified: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
