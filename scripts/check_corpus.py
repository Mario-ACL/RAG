"""Check the parsed corpus against the source PDFs.

Usage: python scripts/check_corpus.py [--manifest data/manifest.json] [--raw data/raw] [--parsed data/parsed]

Exits with status 1 if a check fails, so it can be rerun after any parser change.

Word coverage compares the PDF's words with the parsed text, footnotes and logged removals, so it
detects content that disappears without being logged. The removal share is reported separately,
because each removed line is meant to be a repeated header, a footer or OCR noise.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN = re.compile(r"[a-záéíóúüñ]{4,}")
LIGATURES = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "­": ""})
ARTICLE = re.compile(r"(?m)^Art[ií]culo\s+(\d+)\s*[.\-–]", re.I)
STUCK_MARKER = re.compile(r"(?<![\w/.:#%@-])[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}[a-záéíóúñ][”\"')]?\d{1,3}(?=[\s.,;:)]|$)", re.M)
BROKEN_ACRONYM = re.compile(r"\b[A-ZÁÉÍÓÚÑ]{2,}- [A-ZÁÉÍÓÚÑ]{2,}\b")
SPLIT_WORDS = ["prese nte", "Reglament o", "Declara toria", "imp ugnación", "Telecomunicac iones"]
ARTICLE_DOCS = {"lfpdppp", "lgpdppso", "reglamento_lfpdppp", "iniciativa_ley_ia_senado"}
# The scanned bill itself goes from Article 119 to 121 on PDF page 40, as the page image shows.
KNOWN_GAPS = {"iniciativa_ley_ia_senado": {120}}
MIN_COVERAGE = 99.0
MAX_REMOVED_SHARE = 10.0


def tokens(text: str) -> Counter:
    joined = re.sub(r"-\s*\n\s*", "", text.lower().translate(LIGATURES))
    return Counter(TOKEN.findall(joined))


def share_kept(raw: Counter, parsed: Counter) -> float:
    total = sum(raw.values())
    return 100 * sum(min(count, parsed[token]) for token, count in raw.items()) / max(total, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--parsed", type=Path, default=Path("data/parsed"))
    args = parser.parse_args()

    failures = []
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(f"{'document':26} {'sha':>4} {'pages':>6} {'cover%':>7} {'removed%':>9} {'stuck':>6} {'split':>6} {'acron':>6}  articles")

    for entry in manifest["documents"]:
        doc_id = entry["doc_id"]
        pdf = args.raw / entry["file"]
        lines = (args.parsed / f"{doc_id}.jsonl").read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines]

        sha_ok = hashlib.sha256(pdf.read_bytes()).hexdigest() == entry["sha256"]
        with fitz.open(pdf) as doc:
            raw_text = "\n".join(page.get_text("text") for page in doc)
            page_count = doc.page_count

        body = "\n\n".join(record["text"] for record in records)
        notes = "\n".join(note for record in records for note in record["footnotes"])
        removed = "\n".join(line for record in records for line in record["removed_lines"])

        raw_tokens = tokens(raw_text)
        cover = share_kept(raw_tokens, tokens(f"{body}\n{notes}\n{removed}"))
        removed_share = 100 * sum(tokens(removed).values()) / max(sum(raw_tokens.values()), 1)

        stuck = len(STUCK_MARKER.findall(body)) if entry["profile"] == "designed" else 0
        split = sum(body.count(word) for word in SPLIT_WORDS)
        broken = len(BROKEN_ACRONYM.findall(body))

        articles = "-"
        if doc_id in ARTICLE_DOCS:
            numbers = sorted({int(n) for n in ARTICLE.findall(body)})
            known = KNOWN_GAPS.get(doc_id, set())
            missing = [n for n in range(1, numbers[-1] + 1) if n not in numbers and n not in known]
            articles = f"1-{numbers[-1]}, gaps={len(missing)}" + (f" (source skips {sorted(known)})" if known else "")
            if missing:
                failures.append(f"{doc_id}: missing article headings {missing[:15]}")

        print(
            f"{doc_id:26} {'ok' if sha_ok else 'BAD':>4} {len(records):>6} {cover:>7.1f} {removed_share:>9.1f}"
            f" {stuck:>6} {split:>6} {broken:>6}  {articles}"
        )

        if not sha_ok:
            failures.append(f"{doc_id}: checksum does not match the manifest")
        if len(records) != page_count:
            failures.append(f"{doc_id}: {len(records)} records for {page_count} pages")
        if cover < MIN_COVERAGE:
            failures.append(f"{doc_id}: word coverage {cover:.1f}% is below {MIN_COVERAGE}%")
        if removed_share > MAX_REMOVED_SHARE:
            failures.append(f"{doc_id}: removed {removed_share:.1f}% of words, above {MAX_REMOVED_SHARE}%")
        if split:
            failures.append(f"{doc_id}: {split} known split words remain")
        if broken:
            failures.append(f"{doc_id}: {broken} acronyms are still split")
        if stuck:
            failures.append(f"{doc_id}: {stuck} footnote markers are still stuck to words")

    print()
    for failure in failures:
        print("FAIL", failure)
    print("All checks passed." if not failures else f"{len(failures)} checks failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
