"""Parse the corpus PDFs into clean, page-level text.

Usage: python scripts/parse_corpus.py [--manifest data/manifest.json] [--raw data/raw] [--out data/parsed]

Writes, for each document in the manifest:
  data/parsed/<doc_id>.jsonl  one record per PDF page, used by the pipeline
  data/parsed/<doc_id>.md     the same text, for reading and annotating ground truth

Each document has a parsing profile in the manifest:
  legal     digital legal text: remove repeated headers and footers
  designed  laid-out report: also separate footnotes, drop footnote markers, render tables
  ocr       scanned text: also repair misread list numerals and drop OCR noise
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import fitz

CHAR_MAP = str.maketrans(
    {
        "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
        " ": " ", "­": "", "​": "", "\t": " ",
    }
)

HEADER_ZONE = 0.20
FOOTER_ZONE = 0.88
MIN_REPEAT_SHARE = 0.40

# A real table covers a meaningful part of the page and has most of its cells filled.
# This excludes the page frames and section banners that PyMuPDF also detects as tables.
TABLE_MIN_AREA, TABLE_MAX_AREA = 0.05, 0.80
TABLE_MIN_FILLED = 0.70

CHECKBOX_VALUES = {"", "o", "si", "sí", "no", "no aplica"}
NEW_ITEM = re.compile(r"^(art[ií]culo\s+\d|[IVXLC]+\.(\s|$)|\d{1,3}\.(\s|$)|[a-z]\)\s|•)", re.I)
LIST_MARKER = re.compile(r"^([IVXLC]+|\d{1,3}|[a-z])[.)]$")
OCR_LIST_MARKER = re.compile(r"^(l|1{1,3}|[IVXL]+)[.)]?$")

# A footnote number stuck to the end of a word, such as "pensar33". Words inside URLs are
# excluded by the lookbehind, and all-caps names such as "COVID19" by the lowercase letter.
STUCK_MARKER = re.compile(r"(?<![\w/.:#%@-])([A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}[a-záéíóúñ][”\"')]?)\d{1,3}(?=[\s.,;:)]|$)", re.M)

# Footers of the scanned bill vary under OCR, so they are matched by pattern.
OCR_FOOTER = re.compile(r"(p[aá]gina\s+\d+\s+de\s+\d+|iniciativa\s+con\s+proyecto|se\s+expide\s+la\s+ley|sectores\s+p[uú]blico)", re.I)
OCR_HEADER = re.compile(r"a[ñn]o\s+de\s+la\s+mujer", re.I)

# Tabla 1 of the UNESCO report merges its first column into one cell, which separates each
# activity from its figures. These values were checked by hand against the page image.
TABLE_PATCHES = {
    ("unesco_ram_mexico", 45): (
        "ACTIVIDADES: Servicios de diseño de sistemas de cómputo y servicios relacionados\n2021: 30,691\n2022 (preliminar): 34,439\n\n"
        "ACTIVIDADES: Servicios de consultoría administrativa, científica y técnica\n2021: 42,650\n2022 (preliminar): 53,928\n\n"
        "ACTIVIDADES: Servicios de investigación científica y desarrollo\n2021: 30,967\n2022 (preliminar): 33,153"
    ),
}


def clean_chars(text: str) -> str:
    return text.translate(CHAR_MAP)


def repeat_key(line: str) -> str:
    """Normalize a line so page numbers and letter spacing do not hide repetition."""
    return re.sub(r"[\d\s]+", "", line).lower()


def join_lines(lines: list[str]) -> list[str]:
    """Reflow wrapped lines into paragraphs, repairing hyphenation at line ends."""
    paragraphs: list[str] = []
    for raw in lines:
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        previous = paragraphs[-1] if paragraphs else None
        if previous is None or (NEW_ITEM.match(line) and not LIST_MARKER.match(previous)):
            paragraphs.append(line)
        elif previous.endswith("-") and (line[0].islower() or (previous[-2:-1].isupper() and line[0].isupper())):
            # The uppercase case repairs acronyms split across lines, such as "LFPD-" and "PPP".
            paragraphs[-1] = previous[:-1] + line
        else:
            paragraphs[-1] = f"{previous} {line}"
    return paragraphs


def merge_broken_paragraphs(parts: list[str]) -> list[str]:
    """Rejoin a sentence that the PDF split across separate text blocks."""
    merged: list[str] = []
    for part in parts:
        continues = (
            merged
            and part[:1].islower()
            and not NEW_ITEM.match(part)
            and not merged[-1].endswith((".", ":", ";", "?", "!"))
        )
        if not continues:
            merged.append(part)
        elif merged[-1].endswith("-"):
            merged[-1] = merged[-1][:-1] + part
        else:
            merged[-1] = f"{merged[-1]} {part}"
    return merged


def read_blocks(page: fitz.Page, strip_markers: bool) -> list[dict]:
    """Return text blocks in reading order, with each line's text and font size."""
    blocks = []
    for block in page.get_text("dict", sort=True)["blocks"]:
        if block["type"] != 0:
            continue
        lines = []
        for line in block["lines"]:
            spans = line["spans"]
            largest = max((s["size"] for s in spans), default=0)
            parts = []
            for span in spans:
                is_marker = re.fullmatch(r"[\d,\s]+", span["text"]) and (
                    span["flags"] & 1 or span["size"] < 0.8 * largest
                )
                if strip_markers and is_marker:
                    continue
                parts.append(span["text"])
            text = clean_chars("".join(parts)).strip()
            if text:
                lines.append({"text": text, "size": largest, "y0": line["bbox"][1], "y1": line["bbox"][3]})
        if lines:
            blocks.append({"bbox": block["bbox"], "lines": lines})
    return blocks


def find_repeated_lines(pages: list[list[dict]], heights: list[float]) -> set[str]:
    """Find lines repeated in the header or footer zone across much of a document."""
    counts: Counter[str] = Counter()
    for blocks, height in zip(pages, heights):
        seen = set()
        for block in blocks:
            for line in block["lines"]:
                in_zone = line["y1"] < HEADER_ZONE * height or line["y0"] > FOOTER_ZONE * height
                key = repeat_key(line["text"])
                if in_zone and key:
                    seen.add(key)
        counts.update(seen)
    minimum = max(3, MIN_REPEAT_SHARE * len(pages))
    return {key for key, count in counts.items() if count >= minimum}


def body_font_size(pages: list[list[dict]]) -> float:
    counts: Counter[float] = Counter()
    for blocks in pages:
        for block in blocks:
            for line in block["lines"]:
                counts[round(line["size"], 1)] += len(line["text"])
    return counts.most_common(1)[0][0] if counts else 0.0


def accepted_tables(page: fitz.Page) -> list:
    area = page.rect.width * page.rect.height
    tables = []
    for table in page.find_tables().tables:
        x0, y0, x1, y1 = table.bbox
        share = (x1 - x0) * (y1 - y0) / area
        cells = [cell for row in table.extract() for cell in row]
        filled = sum(1 for cell in cells if cell and cell.strip()) / max(len(cells), 1)
        if (
            table.row_count >= 2
            and table.col_count >= 2
            and TABLE_MIN_AREA <= share <= TABLE_MAX_AREA
            and filled >= TABLE_MIN_FILLED
        ):
            tables.append(table)
    return tables


def clean_cell(cell: str | None) -> str:
    return " ".join(join_lines(clean_chars(cell or "").splitlines()))


def is_header_row(row: list[str]) -> bool:
    return all(len(cell) < 30 for cell in row) and any(cell.isupper() or cell == "Pregunta" for cell in row)


def render_table(raw_rows: list[list[str | None]], inherited: list[str] | None) -> tuple[str, list[str] | None]:
    """Render a table as labelled rows, so each row stays meaningful once chunked."""
    rows = [[STUCK_MARKER.sub(r"\1", clean_cell(cell)) for cell in row] for row in raw_rows]
    has_header = is_header_row(rows[0])
    header = rows[0] if has_header else inherited
    body = rows[1:] if has_header else rows

    keep = [i for i in range(len(rows[0])) if not all(row[i].lower() in CHECKBOX_VALUES for row in body)]
    rendered = []
    for row in body:
        if header and len(header) == len(row) and len(keep) > 1:
            fields = [f"{header[i]}: {row[i]}" for i in keep if row[i]]
            rendered.append("\n".join(fields))
        elif len(keep) == 2:
            rendered.append(f"{row[keep[0]]}: {row[keep[1]]}")
        else:
            rendered.append(" | ".join(row[i] for i in keep if row[i]))
    return "\n\n".join(rendered), (header if has_header else inherited)


def repair_ocr(text: str) -> tuple[str, int]:
    """Repair the numbering this scan misreads consistently: I as l, II as 11, III as 111, 10 as "1 O"."""
    fixes = {"l": "I", "11": "II", "111": "III"}
    text, count_d = re.subn(r"(?m)^(Art[ií]culo\s+\d+)\s+O\.", r"\g<1>0.", text)
    text, count_e = re.subn(r"(?m)^(Art[ií]culo\s+\d+)\s+(?=[A-ZÁÉÍÓÚÑ])", r"\1. ", text)
    text, count_f = re.subn(r"(?m)^([IVXL]{2,})(?=\s+[A-ZÁÉÍÓÚÑ])", r"\1.", text)
    # "VI l." is a misread "VII." that also lost its line break, so it starts a new paragraph again.
    text, count_g = re.subn(r"\s*\b([IVXL]+) l\.(?=\s)", r"\n\n\1I.", text)
    text, count_a = re.subn(r"(?m)^(l|11|111)\.(?=\s|$)", lambda m: f"{fixes[m.group(1)]}.", text)
    # Without the dot, a capital letter must follow, so a date such as "11 de mayo" stays intact.
    text, count_b = re.subn(r"(?m)^(11|111)(?=\s+[A-ZÁÉÍÓÚÑ])", lambda m: f"{fixes[m.group(1)]}.", text)
    text, count_c = re.subn(
        r"(fracci[oó]n\s+)(1{1,3})\b",
        lambda m: m.group(1) + "I" * len(m.group(2)),
        text,
    )
    return text, count_a + count_b + count_c + count_d + count_e + count_f + count_g


def is_ocr_noise(line: str) -> bool:
    if OCR_LIST_MARKER.match(line) or len(line) >= 40:
        return False
    letters = sum(ch.isalpha() for ch in line)
    return letters < 0.5 * len(line.replace(" ", ""))


def parse_document(path: Path, entry: dict) -> tuple[list[dict], dict]:
    profile = entry["profile"]
    designed, ocr = profile == "designed", profile == "ocr"
    stats = Counter()

    with fitz.open(path) as doc:
        all_blocks = [read_blocks(page, strip_markers=designed) for page in doc]
        heights = [page.rect.height for page in doc]
        repeated = find_repeated_lines(all_blocks, heights)
        body_size = body_font_size(all_blocks)

        records = []
        inherited_header = None
        for page, blocks, height in zip(doc, all_blocks, heights):
            tables = accepted_tables(page) if designed else []
            items: list[tuple[float, str, bool]] = []
            footnotes: list[str] = []
            removed: list[str] = []

            for table in tables:
                text, inherited_header = render_table(table.extract(), inherited_header)
                text = TABLE_PATCHES.get((entry["doc_id"], page.number + 1), text)
                items.append((table.bbox[1], text, True))
                stats["tables"] += 1
            if not tables:
                inherited_header = None

            for block in blocks:
                x0, y0, x1, y1 = block["bbox"]
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if any(t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3] for t in tables):
                    continue

                kept = []
                for line in block["lines"]:
                    text = line["text"]
                    in_header = line["y1"] < HEADER_ZONE * height
                    in_footer = line["y0"] > FOOTER_ZONE * height
                    key = repeat_key(text)
                    if (in_header or in_footer) and (not key or key in repeated):
                        stats["header_lines_removed"] += 1
                        removed.append(text)
                        continue
                    if ocr and (
                        (in_footer and OCR_FOOTER.search(text))
                        or (in_header and OCR_HEADER.search(text))
                        or OCR_FOOTER.fullmatch(text)
                        or OCR_HEADER.search(text)
                        or is_ocr_noise(text)
                    ):
                        stats["ocr_noise_removed"] += 1
                        removed.append(text)
                        continue
                    kept.append(line)
                if not kept:
                    continue

                largest = max(line["size"] for line in kept)
                if designed and largest <= body_size - 0.7 and y0 > 0.5 * height:
                    footnotes.extend(join_lines([line["text"] for line in kept]))
                    stats["footnote_blocks"] += 1
                    continue
                items.append((y0, "\n\n".join(join_lines([line["text"] for line in kept])), False))

            # Merge broken paragraphs only between text blocks, so tables stay intact.
            sections: list[str] = []
            run: list[str] = []
            for _, item, is_table in sorted(items, key=lambda entry: entry[0]):
                if is_table:
                    sections.extend(merge_broken_paragraphs(run))
                    sections.append(item)
                    run = []
                else:
                    run.extend(item.split("\n\n"))
            sections.extend(merge_broken_paragraphs(run))
            text = "\n\n".join(sections)

            if designed:
                text = STUCK_MARKER.sub(r"\1", text)
            if ocr:
                text, repaired = repair_ocr(text)
                stats["ocr_numerals_repaired"] += repaired

            number = page.number + 1
            records.append(
                {
                    "doc_id": entry["doc_id"],
                    "page": number,
                    "printed_page": number + entry.get("printed_page_offset", 0),
                    "text": text,
                    "footnotes": footnotes,
                    "tables": len(tables),
                    "removed_lines": removed,
                }
            )
    stats["pages"] = len(records)
    stats["chars"] = sum(len(record["text"]) for record in records)
    return records, dict(stats)


def write_outputs(records: list[dict], entry: dict, out_dir: Path) -> None:
    doc_id = entry["doc_id"]
    with (out_dir / f"{doc_id}.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    sections = [f"# {entry['title']}\n\nTipo: {entry['type']}. Estatus: {entry['status']}."]
    for record in records:
        section = f"## Página {record['page']} del PDF\n\n{record['text']}"
        if record["footnotes"]:
            section += "\n\n**Notas al pie**\n\n" + "\n\n".join(record["footnotes"])
        sections.append(section)
    (out_dir / f"{doc_id}.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/parsed"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    for entry in manifest["documents"]:
        records, stats = parse_document(args.raw / entry["file"], entry)
        write_outputs(records, entry, args.out)
        print(entry["doc_id"], json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
