#!/usr/bin/env python3
"""Convert Pandoc longtable blocks into IEEEtran-compatible tabularx floats."""
from pathlib import Path
import re

path = Path("build/Paper1_IEEEtran.tex")
source = path.read_text(encoding="utf-8")

# Break the long MITM payload header inside its table cell; this is a
# presentation-only change and leaves the underlying label and values intact.
source = source.replace(
    "log2(payload bytes)",
    r"\shortstack{log2(payload\\ bytes)}",
)
if "log2(payload bytes)" in source:
    raise SystemExit("MITM payload header wrapping substitution failed")

# Make long decimal literals breakable without changing their values.
# seqsplit is used in text mode; the one display-math modulus is wrapped in text.
def format_display_modulus(match):
    digits = match.group(1)
    # Preserve the exact integer while splitting its display over aligned rows.
    chunks = [digits[i:i + 22] for i in range(0, len(digits), 22)]
    rows = [r"Q={}&\mathtt{" + chunks[0] + "}"]
    rows.extend(r"&\mathtt{" + chunk + "}" for chunk in chunks[1:])
    return r"\begin{aligned}" + r" \\ ".join(rows) + r"\end{aligned}"

source = re.sub(
    r"Q=(\d{40,})",
    format_display_modulus,
    source,
)
source = re.sub(
    r"(?<![A-Za-z0-9\{])([0-9]{14,})(?![A-Za-z0-9\}])",
    lambda m: r"\seqsplit{" + m.group(1) + "}",
    source,
)

# Permit long repository paths and identifiers to wrap at character boundaries.
source = re.sub(
    r"\\texttt\{([^{}]+)\}",
    lambda m: r"\texttt{\seqsplit{" + m.group(1) + "}}",
    source,
)

# Pandoc inserts line breaks between booktabs rules and longtable markers.
# Allow whitespace at those boundaries; do not parse the nested column preamble.
pattern = re.compile(
    r"\\begin\{longtable\}.*?\\toprule\\noalign\{\}\s*"
    r"(.*?)\s*\\midrule\\noalign\{\}\s*\\endhead\s*"
    r"\\bottomrule\\noalign\{\}\s*\\endlastfoot\s*"
    r"(.*?)\s*\\end\{longtable\}",
    re.S,
)
matches = list(pattern.finditer(source))
if len(matches) != 3:
    raise SystemExit(f"Expected 3 Pandoc longtables after the hand-authored full-width table, found {len(matches)}")


def convert(match):
    header = match.group(1).strip()
    body = match.group(2).strip()
    columns = header.count("&") + 1
    if columns < 2:
        raise SystemExit(f"Unexpected table header with {columns} columns: {header!r}")
    if r"\bottomrule" in body:
        raise SystemExit("Unexpected bottomrule inside table body")
    if "Modulus q" in header or "Negacyclic root" in header:
        # The four 16-digit CRT moduli and roots must remain on one line.
        # A two-column float gives each numeric column enough width.
        table_env = "table*"
        table_width = r"\textwidth"
        table_font = r"\centering\small"
        column_spec = "@{}cXX@{}"
    elif "log2(half-table entries)" in header:
        table_env = "table"
        table_width = r"\columnwidth"
        table_font = r"\centering\scriptsize"
        column_spec = "@{}XXXXX@{}"
    else:
        table_env = "table"
        table_width = r"\columnwidth"
        table_font = r"\centering\small"
        column_spec = "@{}" + "X" * columns + "@{}"
    return (
        r"\begin{" + table_env + r"}[!t]" + "\n"
        + table_font + "\n"
        + r"\begin{tabularx}{" + table_width + "}{" + column_spec + "}" + "\n"
        + r"\toprule\noalign{}" + "\n"
        + header + "\n"
        + r"\midrule\noalign{}" + "\n"
        + body + "\n"
        + r"\bottomrule\noalign{}" + "\n"
        + r"\end{tabularx}" + "\n"
        + r"\end{" + table_env + "}"
    )


source, converted = pattern.subn(convert, source)
if converted != 3:
    raise SystemExit(f"Expected to convert 3 Pandoc longtables, converted {converted}")
if r"\begin{longtable}" in source or r"\end{longtable}" in source:
    raise SystemExit("Unconverted longtable environment remains")

# Confirm that every converted table has a valid width/spec pair and ordered rules.
table_starts = len(re.findall(r"\\begin\{tabularx\}", source))
table_ends = len(re.findall(r"\\end\{tabularx\}", source))
if table_starts != 4 or table_ends != 4:
    raise SystemExit(
        f"Expected 4 IEEE tabularx tables (3 converted plus 1 authored), "
        f"found {table_starts} begins and {table_ends} ends"
    )
for table in re.finditer(
    r"\\begin\{tabularx\}.*?\\end\{tabularx\}", source, re.S
):
    body = table.group(0)
    if not (body.find(r"\toprule") < body.find(r"\midrule") < body.rfind(r"\bottomrule")):
        raise SystemExit("Table rule ordering check failed")

path.write_text(source, encoding="utf-8")
print(f"Converted and verified {converted} IEEE-compatible tables.")
