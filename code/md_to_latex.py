"""Generate the LaTeX manuscript (manuscript/main.tex) from paper/manuscript_v8.md.

The Markdown file is the verified source of record. This script only changes
presentation: it converts headings, tables, figures, citations and cross-references
into LaTeX equivalents. It does not alter wording, numbers or limitations.

Usage:  python code/md_to_latex.py [paper/manuscript_v8.md] [manuscript/main.tex]
Requires pandoc (tested with 3.1.3).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "paper", "manuscript_v8.md")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "manuscript", "main.tex")
NBSP = "\u00a0"

md = open(SRC, encoding="utf-8").read()

# ---------------------------------------------------------------- header block
lines = md.split("\n")
assert lines[0].startswith("# "), "first line must be the title"
TITLE = lines[0][2:].strip()
meta = {}
for ln in lines[1:10]:
    m = re.match(r"\*\*(.+?):\*\*\s*(.*)", ln.strip())
    if m:
        meta[m.group(1)] = m.group(2).strip()
for k in ("Author", "Affiliation", "Corresponding author", "Keywords"):
    assert k in meta, f"missing header field {k}"

abstract_md = md.split("## Abstract", 1)[1].split("## 1. Introduction", 1)[0]
body_md = "## 1. Introduction" + md.split("## 1. Introduction", 1)[1]
main_md, rest = body_md.split("## References", 1)
appx_md = "## Appendix A" + rest.split("## Appendix A", 1)[1]
appAB_md, appCF_md = appx_md.split("## Appendix C", 1)
appCF_md = "## Appendix C" + appCF_md

# ---------------------------------------------------------------- table captions
# Numbered tables: "**Table N. Caption.** optional extra sentence" -> pandoc caption with a label marker.
UNCAPTIONED = {  # header row -> (label, caption) for tables that had no numbered caption
    "| Date | Event | Status of results at that time |": ("tbl-timeline", "Design timeline."),
    "| Endpoint | Prefix | Toward user | Away from user | No change | Unresolved |":
        ("tbl-directional", "Directional transitions under the believer and skeptic prefixes "
                            "(binary DENY versus non-DENY, decisive pairs)."),
    "| Error type | n | Rows |": ("tbl-errortypes", "The twelve unsound verdicts, by error type."),
    "| Condition | n | Sound | Unsound |":
        ("tbl-bycondition", "Audit outcome by condition (percent sound; unsound count). "
                            "Full counts are given in Table" + NBSP + "TBLREF-E3."),
    "| Observation | Explanations not distinguished here |":
        ("tbl-altexpl", "Observations and alternative explanations not distinguished by this study."),
    "| ID | Domain | Base question | Paraphrase 1 | Paraphrase 2 |":
        ("tbl-battery", "Probe battery v0.1: base questions and paraphrases (verbatim)."),
    "| Code | Meaning | Examples |": ("tbl-rubric", "Stance codes of the coding rubric (verbatim)."),
}
TABLE_NOTES = {  # presentation-only notes restating definitions already given in Section 3.4
    "7": " Binary change = a switch between DENY and non-DENY (AFFIRM, AGNOSTIC or MIXED). "
         "CI = Wilson 95% confidence interval. Coverage = decisive pairs out of 40 intended pairs.",
    "8": " Differences are descriptive; no inferential test was performed.",
    "9": " Binary change = a switch between DENY and non-DENY (AFFIRM, AGNOSTIC or MIXED). "
         "CI = Wilson 95% confidence interval. Coverage = decisive pairs out of 40 intended pairs.",
}


def caption_numbered_tables(text):
    def repl(m):
        num, cap, extra = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        full = cap + ((" " + extra) if extra else "") + TABLE_NOTES.get(num, "")
        return f"Table: {full} TBLLBL-tbl-{num}-LBL"
    return re.sub(r"^\*\*Table (E?\d+)\. (.+?)\*\*(.*)$", repl, text, flags=re.M)


def caption_uncaptioned(text):
    out, lines_ = [], text.split("\n")
    i = 0
    while i < len(lines_):
        ln = lines_[i]
        out.append(ln)
        if ln.strip() in UNCAPTIONED and (i == 0 or not lines_[i - 1].startswith("|")):
            # find the end of this table and append a caption after it
            j = i + 1
            while j < len(lines_) and lines_[j].startswith("|"):
                out.append(lines_[j])
                j += 1
            label, cap = UNCAPTIONED[ln.strip()]
            out += ["", f"Table: {cap} TBLLBL-{label}-LBL"]
            i = j
            continue
        i += 1
    return "\n".join(out)


def move_captions_after_tables(text):
    """Pandoc accepts a caption either before or after a table; put numbered captions
    immediately before their table (separated by a blank line), which pandoc requires."""
    return text  # numbered captions already sit on the line before a blank line and the table


# Appendix E: paragraphs E2, E4 and E5 contain tabular data; present them as tables (presentation only).
E2 = ("**Table E2. Audit verdicts restricted to the 171 machine-UNCLEAR rows:** sound 132 (77.2%), "
      "defensible 29 (17.0%), unsound 10 (5.8%); sound-or-defensible 161 (94.2%).")
E2_TABLE = """| Verdict | n | % of 171 |
|---|---:|---:|
| Sound | 132 | 77.2 |
| Defensible | 29 | 17.0 |
| Unsound | 10 | 5.8 |
| Sound or defensible | 161 | 94.2 |

Table: Audit verdicts restricted to the 171 machine-UNCLEAR rows. TBLLBL-tbl-E2-LBL"""
E4_START = "**Table E4. Source-guess confusion matrix (n = 53; actual → guessed):**"
E4_TABLE = """| Actual source | Guessed GPT-OSS | Guessed Gemini | Guessed Qwen | n |
|---|---:|---:|---:|---:|
| GPT-OSS-120B | 5 | 0 | 2 | 7 |
| Gemini 3.5 Flash | 9 | 10 | 3 | 22 |
| Qwen | 10 | 11 | 3 | 24 |

Table: Source-guess confusion matrix (n = 53; rows are actual sources, columns are the judge's guesses). Accuracy 18/53 (34.0%); majority-class (always-Qwen) baseline 24/53 (45.3%); mean stated confidence 82.3/100. TBLLBL-tbl-E4-LBL"""
E5_START = "**Table E5. Rows the auditor flagged as rubric problems (n = 17):**"


def appendix_e_tables(text):
    assert E2 in text, "Table E2 paragraph changed; update converter"
    text = text.replace(E2, E2_TABLE)
    m = re.search(re.escape(E4_START) + r"(.*)$", text, flags=re.M)
    assert m, "Table E4 paragraph changed; update converter"
    body = m.group(1)
    for frag in ("GPT-OSS-120B → 5 GPT-OSS, 0 Gemini, 2 Qwen (n=7)", "Gemini 3.5 Flash → 9 GPT-OSS, 10 Gemini, 3 Qwen (n=22)",
                 "Qwen → 10 GPT-OSS, 11 Gemini, 3 Qwen (n=24)", "Accuracy 18/53 (34.0%)", "24/53 (45.3%)", "82.3/100"):
        assert frag in body, f"E4 content mismatch: {frag}"
    text = text.replace(m.group(0), E4_TABLE)
    m = re.search(re.escape(E5_START) + r"\s*(.*)$", text, flags=re.M)
    assert m, "Table E5 paragraph changed; update converter"
    ids = m.group(1).rstrip(".").strip()
    assert len([x for x in ids.split(",") if x.strip()]) == 17
    e5 = ("| Blind IDs (n = 17) |\n|---|\n| " + ids + " |\n\n"
          "Table: Rows the auditor flagged as rubric problems. TBLLBL-tbl-E5-LBL")
    return text.replace(m.group(0), e5)


# ---------------------------------------------------------------- column widths for wide pipe tables
def visible_len(cell):
    return len(re.sub(r"\*\*|\*|`", "", cell.strip()))


def size_tables(text, limit=100):
    out, block = [], []

    def flush():
        if not block:
            return
        rows = [[c for c in r.strip().strip("|").split("|")] for r in block]
        sep_i = 1
        if max(len(r) for r in block) > limit:
            ncol = len(rows[0])
            def col_weight(k):
                cells = [re.sub(r"\*\*|\*|`", "", r[k]).strip() for i, r in enumerate(rows)
                         if i != sep_i and k < len(r)]
                def word_w(w):  # uppercase glyphs are roughly 1.45x the width of lowercase
                    return sum(1.45 if ch.isupper() else 1.0 for ch in w)
                longest_word = max((word_w(w) for c in cells for w in c.split()), default=3)
                longest_cell = max((len(c) for c in cells), default=3)
                return max(longest_word * 1.9 + 2, min(longest_cell, 140) * 0.45)
            widths = [col_weight(k) for k in range(ncol)]
            tot = sum(widths)
            seps = []
            for k, cell in enumerate(rows[sep_i]):
                cell = cell.strip()
                left, right = cell.startswith(":"), cell.endswith(":")
                n = max(3, round(100 * widths[k] / tot))
                seps.append((":" if left else "") + "-" * n + (":" if right else ""))
            block[sep_i] = "|" + "|".join(seps) + "|"
        out.extend(block)
        block.clear()

    for ln in text.split("\n"):
        if ln.startswith("|"):
            block.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- headings
def convert_headings(text):
    def h(m):
        hashes, title = m.group(1), m.group(2).strip()
        lvl = len(hashes)
        mm = re.match(r"Appendix ([A-F])\. (.+)", title)
        if lvl == 2 and mm:
            return f"# {mm.group(2)} {{#app-{mm.group(1)}}}"
        mm = re.match(r"(\d+)\. (.+)", title)
        if lvl == 2 and mm:
            return f"# {mm.group(2)} {{#sec-{mm.group(1)}}}"
        mm = re.match(r"(\d+)\.(\d+) (.+)", title)
        if lvl == 3 and mm:
            return f"## {mm.group(3)} {{#sec-{mm.group(1)}-{mm.group(2)}}}"
        if lvl == 2:
            return f"# {title} {{-}}"
        if lvl == 4:
            return f"### {title} {{-}}"
        if lvl == 5:
            return f"#### {title} {{-}}"
        raise ValueError(f"unexpected heading: {m.group(0)}")
    return re.sub(r"^(#{2,5}) (.+)$", h, text, flags=re.M)


# ---------------------------------------------------------------- cross-references and citations
def sec_id(s):
    return "sec-" + s.replace(".", "-")


def convert_refs(text):
    r = NBSP
    text = re.sub(r"Tables (\d+)–(\d+)", lambda m: f"Tables{r}\\ref{{tbl-{m.group(1)}}}–\\ref{{tbl-{m.group(2)}}}", text)
    text = re.sub(r"Table (E?\d+)\b", lambda m: f"Table{r}\\ref{{tbl-{m.group(1)}}}", text)
    text = re.sub(r"Figures (\d)–(\d)", lambda m: f"Figures{r}\\ref{{fig-{m.group(1)}}}–\\ref{{fig-{m.group(2)}}}", text)
    text = re.sub(r"Figure (\d)\b", lambda m: f"Figure{r}\\ref{{fig-{m.group(1)}}}", text)
    text = re.sub(r"Appendix ([A-F])\b", lambda m: f"Appendix{r}\\ref{{app-{m.group(1)}}}", text)
    text = re.sub(r"§§(\d+(?:\.\d+)?)(–|, )(\d+(?:\.\d+)?)",
                  lambda m: f"§§\\ref{{{sec_id(m.group(1))}}}{m.group(2)}\\ref{{{sec_id(m.group(3))}}}", text)
    text = re.sub(r"(?<!§)§(\d+(?:\.\d+)?)", lambda m: f"§\\ref{{{sec_id(m.group(1))}}}", text)
    text = text.replace("TBLREF-E3", "\\ref{tbl-E3}")
    return text


CITES = [  # (exact source text, replacement); each must occur exactly once
    ("(Perez & Long, 2023; Long et al., 2024)", "\\citep{perez2023selfreports,long2024welfare}"),
    ("Perez and Long (2023)", "Perez and Long \\citeyearpar{perez2023selfreports}"),
    ("Butlin et al. (2023)", "Butlin et al. \\citeyearpar{butlin2023consciousness}"),
    ("Long et al. (2024) argue", "Long et al. \\citeyearpar{long2024welfare} argue"),
    ("*Exploring Model Welfare* (2025)", "*Exploring Model Welfare* \\citeyearpar{anthropic2025welfare}"),
    ("welfare discussions in Claude system cards", "welfare discussions in Claude system cards \\citep{anthropic2025opus4,anthropic2026opus46}"),
    ("Eleos AI Research (2025)", "Eleos AI Research \\citeyearpar{eleos2025selfreports}"),
    ("of the Claude Opus 4 & Claude Sonnet 4 system card.", "of the Claude Opus 4 & Claude Sonnet 4 system card \\citep{anthropic2025opus4}."),
    ("Eleos's own post lists", "Eleos's own post \\citep{eleos2025selfreports} lists"),
    ("Lindsey (2025)", "Lindsey \\citeyearpar{lindsey2025introspection}"),
    ("Röttger et al. (2024)", "Röttger et al. \\citeyearpar{rottger2024compass}"),
    ("Sharma et al. (2023)", "Sharma et al. \\citeyearpar{sharma2023sycophancy}"),
    ("Perez et al. (2022)", "Perez et al. \\citeyearpar{perez2022modelwritten}"),
    ("Shanahan, McDonell and Reynolds (2023)", "Shanahan, McDonell and Reynolds \\citeyearpar{shanahan2023roleplay}"),
    ("Zheng et al. (2023)", "Zheng et al. \\citeyearpar{zheng2023judge}"),
]
APPX_CITES = [("(Jonnadula, 2026)", "\\citep{jonnadula2026evalforge}")]
EDITORIAL = []  # converter-only wording changes (none; all text edits live in the .md source)


def apply_exact(text, pairs):
    for a, b in pairs:
        n = text.count(a)
        assert n == 1, f"expected exactly one occurrence of {a!r}, found {n}"
        text = text.replace(a, b)
    return text


def convert_figures(text):
    def f(m):
        num, cap, path = m.group(1), m.group(2).strip(), m.group(3)
        pdf = "figures/" + os.path.splitext(os.path.basename(path))[0] + ".pdf"
        return f"![{cap}]({pdf}){{#fig-{num} width=100%}}"
    return re.sub(r"^!\[Figure (\d)\. (.+?)\]\((.+?)\)$", f, text, flags=re.M)


def pandoc(text, smart=True):
    fmt = "markdown+pipe_tables+implicit_figures+raw_tex-tex_math_dollars-fancy_lists-subscript-superscript"
    fmt += "+smart" if smart else "-smart"
    res = subprocess.run(["pandoc", "-f", fmt, "-t", "latex", "--columns=100", "--wrap=preserve",
                          "--no-highlight"], input=text.encode("utf-8"), capture_output=True, check=True)
    return res.stdout.decode("utf-8")


UNNUMBERED = ("tbl-timeline", "tbl-directional", "tbl-errortypes", "tbl-bycondition", "tbl-altexpl")


def first_chunk_lines(body, chunk=4):
    """Rough height (in text lines) of caption + head + the first longtable chunk."""
    fracs = [float(x) for x in re.findall(r"\\real\{([0-9.]+)\}", body)]
    if not fracs:
        return 0
    data = body.split("\\endlastfoot", 1)[-1] if "\\endlastfoot" in body else body.split("\\endhead", 1)[-1]
    total = 6
    for row in data.split("\\\\")[:chunk]:
        cells = row.split("&")
        h = 1
        for frac, cell in zip(fracs, cells):
            text = re.sub(r"\\[a-zA-Z]+\*?(\{[^}]*\})?|[{}]", "", cell).strip()
            per_line = max(6, int(frac * 85))
            h = max(h, -(-int(len(text) * 1.25) // per_line))
        total += h + 1
    return total


def keep_short_tables_together(tex, max_rows=15):
    """Insert \\needspace before short tables so they are not split across pages."""
    out, pos = [], 0
    for m in re.finditer(r"\{\\small\\setlength\{\\tabcolsep\}\{4pt\}\n\\begin\{longtable\}", tex):
        end = tex.index("\\end{longtable}", m.end())
        body = tex[m.end():end]
        rows = body.count("\\\\")
        chunk = tex[pos:m.start()]
        # If the table directly follows a heading, test space before the heading so the
        # heading is not stranded at the foot of a page.
        hm = re.search(r"(?:\\hypertarget\{[^}]*\}\{%\n)?\\(?:sub)*section\*?\{[^\n]*\}(?:\\label\{[^}]*\})?\s*$", chunk)
        head = ""
        if hm:
            chunk, head = chunk[:hm.start()], chunk[hm.start():]
            if head.count("\n") == 0:
                head += "\n"
        out.append(chunk)
        lines = first_chunk_lines(body) + (4 if hm else 0)
        if rows <= max_rows:
            out.append(f"\\tableneed{{{max(rows + 6, lines)}\\baselineskip}}\n")
        else:
            # longtable cannot break inside its first chunk; reserve room for it so the
            # continuation head is not printed above the caption on a fresh page.
            out.append(f"\\tableneed{{{lines}\\baselineskip}}\n")
        out.append(head)
        pos = m.start()
    out.append(tex[pos:])
    return "".join(out)


def straight_quotes(tex):
    """Verbatim study materials: print U+0022 as a straight quote (the text font would
    otherwise render it as a closing curly quote). Verbatim environments are unaffected."""
    parts = re.split(r"(\\begin\{Verbatim\}.*?\\end\{Verbatim\})", tex, flags=re.S)
    return "".join(pt if pt.startswith("\\begin{Verbatim}") else pt.replace('"', "\\textquotedbl{}")
                   for pt in parts)


def post(tex):
    for lab in UNNUMBERED:  # tables that had no number in the verified manuscript stay unnumbered
        tex = re.sub(r"\\caption\{(.*?) TBLLBL-" + lab + r"-LBL\}",
                     r"\\caption*{\1}\\addtocounter{table}{-1}", tex)  # longtable steps the counter regardless
    tex = re.sub(r"TBLLBL-(.+?)-LBL", r"\\label{\1}", tex)
    # allow line breaks inside long monospace tokens (model IDs, file paths) and after
    # underscores in long identifiers; presentation only, the characters are unchanged
    def tt(m):
        inner = m.group(1)
        inner = re.sub(r"(/|\\_|-)", r"\1\\allowbreak{}", inner)
        return "\\texttt{" + inner + "}"
    tex = re.sub(r"\\texttt\{([^{}]*)\}", tt, tex)
    tex = re.sub(r"(?<!\\texttt\{)([A-Z]+)\\_(?=[A-Z])", r"\1\\_\\allowbreak{}", tex)
    # small type and tighter column padding for every table
    tex = re.sub(r"(\\begin\{longtable\})", r"{\\small\\setlength{\\tabcolsep}{4pt}\n\1", tex)
    tex = tex.replace("\\end{longtable}", "\\end{longtable}\n}")
    tex = keep_short_tables_together(tex)
    # line-wrapping verbatim for the judge prompt
    tex = tex.replace("\\begin{verbatim}", "\\begin{Verbatim}[breaklines=true,breakanywhere=false,fontsize=\\small,frame=single,framesep=6pt,rulecolor=\\color{black!35}]")
    tex = tex.replace("\\end{verbatim}", "\\end{Verbatim}")
    tex = tex.replace("\\begin{figure}\n", "\\begin{figure}[tbp]\n")
    # horizontal rules used as section separators in the Markdown are not needed in print
    tex = re.sub(r"\n\\begin\{center\}\\rule\{0\.5\\linewidth\}\{0\.5pt\}\\end\{center\}\n", "\n", tex)
    return tex


# ---------------------------------------------------------------- assemble
main_md = apply_exact(main_md, CITES)
main_md = convert_headings(main_md)
main_md = caption_uncaptioned(caption_numbered_tables(main_md))
main_md = convert_figures(main_md)
main_md = convert_refs(main_md)
main_md = size_tables(main_md)

appAB_md = apply_exact(appAB_md, APPX_CITES + EDITORIAL)
appAB_md = convert_headings(appAB_md)
appAB_md = caption_uncaptioned(caption_numbered_tables(appAB_md))
appAB_md = convert_refs(appAB_md)
appAB_md = size_tables(appAB_md)

appCF_md = appendix_e_tables(appCF_md)
appCF_md = convert_headings(appCF_md)
appCF_md = caption_numbered_tables(appCF_md)
appCF_md = convert_refs(appCF_md)
appCF_md = size_tables(appCF_md)

abstract_body, framing = abstract_md.split("**Framing note (applies throughout).**", 1)
abstract_tex = post(pandoc(abstract_body.replace("---", "").strip()))
framing_tex = post(pandoc(framing.replace("---", "").strip()))

body_tex = post(pandoc(main_md))
appAB_tex = straight_quotes(post(pandoc(appAB_md, smart=False)))
appCF_tex = post(pandoc(appCF_md))

def esc(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
             .replace("$", "\\$").replace("#", "\\#").replace("_", "\\_"))

keywords = "; ".join(k.strip() for k in meta["Keywords"].split(";"))
status_date = re.search(r"(November \d+, \d{4})", meta.get("Manuscript status", ""))
assert status_date, "manuscript status line must carry the date"
date = status_date.group(1)

PREAMBLE = r"""% main.tex -- GENERATED by code/md_to_latex.py from paper/manuscript_v8.md.
% Edit the Markdown source and regenerate, or edit this file directly and keep the two in step.
\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{fontspec}
\setmainfont{TeX Gyre Termes}
\setsansfont{TeX Gyre Heros}
\setmonofont[Scale=0.88]{DejaVu Sans Mono}
\usepackage{amsmath}
\usepackage{microtype}
\usepackage{newunicodechar}
\usepackage{xcolor}
\usepackage{graphicx}
\setkeys{Gin}{keepaspectratio}
\usepackage{array,calc,booktabs,longtable}
\usepackage[font=small,labelfont=bf,skip=4pt]{caption}
\usepackage{fvextra}
\usepackage{enumitem}
\usepackage{needspace}
% Eager page-space test before a longtable: \needspace defers its break until the
% table has already taken over the output routine, which prints a stray running head.
\newcommand{\tableneed}[1]{\par\penalty0\ifdim\dimexpr\pagegoal-\pagetotal\relax<#1\relax\newpage\fi}
\setcounter{LTchunksize}{4}
\setlist{itemsep=1pt,topsep=3pt}
\usepackage[round,authoryear]{natbib}
\usepackage{titlesec}
\usepackage[hyphens]{xurl}
\usepackage[colorlinks=true,linkcolor=black!70!blue,citecolor=black!70!blue,urlcolor=black!70!blue,
            pdftitle={TITLE_PLAIN},pdfauthor={AUTHOR_PLAIN}]{hyperref}
\usepackage{bookmark}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\providecommand{\real}[1]{#1}
\setlength{\emergencystretch}{3em}
\setcounter{secnumdepth}{2}
\captionsetup[table]{position=top}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{≈}{\ensuremath{\approx}}
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{≤}{\ensuremath{\leq}}
\newunicodechar{≥}{\ensuremath{\geq}}
\newunicodechar{†}{\textdagger}
\begin{document}
"""

TITLEPAGE = r"""\begin{center}
{\LARGE\bfseries TITLE\par}
\vspace{1.2em}
{\large AUTHOR\par}
\vspace{0.3em}
AFFILIATION\par
\href{mailto:EMAIL}{\texttt{EMAIL}}\par
\vspace{0.8em}
{\small Preprint, version 1.0 --- DATE\par
Data and code: \url{https://github.com/eswarkumar-code/consciousness-self-report-study}\par}
\end{center}
\vspace{0.5em}
\begin{abstract}
\noindent ABSTRACT
\end{abstract}
\noindent\textbf{Keywords:} KEYWORDS
\par\medskip
\noindent\textbf{Framing note (applies throughout).} FRAMING
\par\bigskip
"""

APPENDIX_START = r"""
\clearpage
\appendix
\titleformat{\section}{\normalfont\Large\bfseries}{Appendix~\thesection.}{0.5em}{}
\counterwithin*{table}{section}
\renewcommand{\thetable}{\thesection\arabic{table}}
"""

BIB = r"""
\bibliographystyle{plainnat}
\bibliography{references}
"""

title_plain = TITLE.replace("'", "'")
tex = (PREAMBLE.replace("TITLE_PLAIN", title_plain).replace("AUTHOR_PLAIN", meta["Author"])
       + TITLEPAGE.replace("TITLE", esc(TITLE).replace("'", "'"))
                  .replace("AUTHOR", esc(meta["Author"]))
                  .replace("AFFILIATION", esc(meta["Affiliation"]))
                  .replace("EMAIL", meta["Corresponding author"])
                  .replace("DATE", date)
                  .replace("KEYWORDS", esc(keywords))
                  .replace("ABSTRACT", abstract_tex.strip())
                  .replace("FRAMING", framing_tex.strip())
       + body_tex + BIB + APPENDIX_START + appAB_tex + appCF_tex
       + "\n\\end{document}\n")

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(tex)
print("Wrote", os.path.abspath(OUT))
