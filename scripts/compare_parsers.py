"""Compare PDF text extraction across parsers on the corpus.

Usage: python scripts/compare_parsers.py data/raw

Reports, per document and parser: extraction time, characters, a word-fragment
rate, and the number of tables each table-aware parser detects.
"""
import re
import sys
import time
from pathlib import Path

import fitz
import pdfplumber
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Short tokens that are real Spanish words, so they do not count as fragments.
SHORT_WORDS = set(
    "a e o u y al de el en es la le lo me mi no se si su te tu un ya ha he las los del por con "
    "que una sus más para como dos más ley art fr ia pdf".split()
)
TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def fragment_rate(text: str) -> float:
    """Share of alphabetic tokens of three letters or fewer that are not common words."""
    tokens = TOKEN.findall(text)
    if not tokens:
        return 0.0
    fragments = [t for t in tokens if len(t) <= 3 and t.lower() not in SHORT_WORDS]
    return 100 * len(fragments) / len(tokens)


def extract_pymupdf(path: Path) -> list[str]:
    with fitz.open(path) as doc:
        return [page.get_text("text") for page in doc]


def extract_pdfplumber(path: Path) -> list[str]:
    with pdfplumber.open(path) as doc:
        return [(page.extract_text() or "") for page in doc.pages]


def extract_pypdf(path: Path) -> list[str]:
    return [(page.extract_text() or "") for page in PdfReader(path).pages]


PARSERS = {"pymupdf": extract_pymupdf, "pdfplumber": extract_pdfplumber, "pypdf": extract_pypdf}

print(f"{'document':28} {'parser':11} {'secs':>6} {'chars':>8} {'frag%':>6} {'empty':>6}")
for path in sorted(Path(sys.argv[1]).glob("*.pdf")):
    for name, extract in PARSERS.items():
        start = time.perf_counter()
        pages = extract(path)
        elapsed = time.perf_counter() - start
        text = "\n".join(pages)
        empty = sum(len(p.strip()) < 50 for p in pages)
        print(f"{path.stem:28} {name:11} {elapsed:6.1f} {len(text):8d} {fragment_rate(text):6.2f} {empty:6d}")

print("\nTables detected by PyMuPDF")
for path in sorted(Path(sys.argv[1]).glob("*.pdf")):
    with fitz.open(path) as doc:
        found = [(page.number + 1, len(page.find_tables().tables)) for page in doc]
    pages_with = [number for number, count in found if count]
    print(f"{path.stem:28} tables={sum(c for _, c in found):3d} pages={pages_with[:25]}")

print("\nImages per page, flagged when a page has little text")
for path in sorted(Path(sys.argv[1]).glob("*.pdf")):
    with fitz.open(path) as doc:
        low_text = [page.number + 1 for page in doc if len(page.get_text().strip()) < 50]
        sizes = {tuple(round(v) for v in page.rect[2:]) for page in doc}
    print(f"{path.stem:28} pages={len(low_text)} low_text={low_text} page_sizes={sorted(sizes)}")
