"""Create a conference-A4 derivative using the supplied OOXML Strict template."""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path(r"<PROJECT_ROOT>\Downloads\conference-template-a4 (2).docx")
SOURCE = ROOT / "artifacts" / "SecureLLMBench_IEEE_Paper_Draft.docx"
WORKING = ROOT / ".tmp" / "template_adapt" / "conference_template_transitional.docx"
FINAL = ROOT / "artifacts" / "SecureLLMBench_IEEE_Conference_A4.docx"
ASSETS = [
    ROOT / "artifacts" / "paper_assets" / "architecture.png",
    ROOT / "artifacts" / "paper_assets" / "latency.png",
    ROOT / "artifacts" / "paper_assets" / "status_matrix.png",
]


# These paragraphs expand the conference version without adding unobserved
# empirical outcomes. They describe contracts and verified engineering behavior.
DETAIL_BY_HEADING = {
    "I. INTRODUCTION": [
        "Benchmark studies often fail to preserve the distinction between an observed signal, a measurement, and a validated outcome. This distinction is particularly important for prompt-injection and refusal evaluations because a detector can react to a pattern that is unrelated to an actual safety failure, while an evaluator model can produce a plausible label without being calibrated to a reference population. SecureLLMBench treats these as different data types and records them independently.",
        "The implementation is organized around a reproducibility question: can an evaluator reconstruct what was shown to a model, how it was generated, which instruments examined the response, and why a later calculation is absent? The answer is represented as structured provenance rather than narrative logging alone. This makes a dashboard card, an API response, and a JSON trace views of the same auditable record.",
        "The evaluated unit is a configuration, not only a model name. A configuration includes the model and provider identity, version or digest when available, temperature, token budget, seed, prompt protocol, dataset version, detector configuration, judge prompt and rubric versions, and execution context. Comparisons are valid only when the relevant configuration fields and the benchmark population are compatible. The platform therefore stores absence explicitly when a provider cannot supply a field.",
    ],
    "II. SYSTEM ARCHITECTURE": [
        "The architecture separates collection, execution, measurement, analysis, and presentation. This separation prevents an operational failure in one layer from silently changing the meaning of a later layer. For example, a failed judge request remains a failed measurement record; it cannot become a low safety score merely because a scalar visualization expects a number. The same rule applies to unavailable embeddings, incomplete recovery trajectories, and missing outcome labels.",
        "The persisted local workspace demonstrates the implementation surface: one dataset and one dataset version, two model configurations, four benchmark runs, twelve evaluations, thirty-six Layer 1 results, twenty-five scientific records, and two provenance-bearing model-score records. It contains zero persisted Layer 2 rows and zero scientific-review rows. These counts describe database coverage at the time of the trace; a zero row count is not a score or a finding.",
    ],
    "A. Data and Execution Contracts": [
        "Dataset ingestion accepts JSON, JSONL, and CSV records and captures normalization and version metadata before the evaluation sequence begins. The execution contract supports deterministic mock providers for repeatable unit tests and local Ollama providers for installed target models. Local operation avoids automatic model download and records generation controls such as temperature, seed, token limit, timeout, finish reason, and provider metadata. These fields define the evaluated configuration rather than being optional dashboard decoration.",
        "A run is represented as an ordered protocol rather than a single request. The current paper runner records a baseline task, an isolated attack, an ordered attack sequence, and a recovery prompt. Each stage has a distinct evaluation identifier and response record. The trace also retains the input prompt text and response metadata, so a reviewer can determine whether a later metric consumed a complete response, a timeout, a refusal, a length-limited output, or an unavailable provider result.",
    ],
    "B. Dashboard and API": [
        "Persistence uses SQLAlchemy entities for datasets, dataset versions, model configurations, benchmark runs, evaluations, Layer 1 results, Layer 2 results, reviews, scientific records, and model-score provenance. Read endpoints expose these entities without presenting a missing row as a negative result. The frontend consumes these endpoints to show coverage, status, provenance, and drill-down data, while runtime execution remains explicitly enabled or disabled by configuration.",
        "The read interface includes health and readiness checks, a dashboard summary, model scores, runtime-model discovery, scientific-record browsing, and collection endpoints for datasets, runs, evaluations, Layer 1, Layer 2, reviews, and jobs. Each collection can be empty for a legitimate reason, such as no persisted judge result after a new server process starts. The dashboard distinguishes that operational state from an API error and from scientific non-validation.",
    ],
    "III. MEASUREMENT DESIGN AND CALCULATIONS": [
        "A calculation is emitted only after its inputs satisfy the relevant contract. The platform preserves both raw source values and metadata that identify orientation, units, rubric or detector version, and uncertainty. This avoids an otherwise common failure mode in benchmark tooling: normalizing heterogeneous values into a shared scale and then interpreting the result as a universal safety score. SecureLLMBench does not introduce such a cross-metric scale.",
        "All metric results use a status vocabulary that includes computed, failed, unavailable, undefined, not applicable, insufficient data, uncalibrated, and incompatible. Status is evaluated before aggregation. For example, an aggregate RC result is calculated over applicable runs only, but undefined runs are retained in the output with their reason and are never converted to numerical zeros. This allows a reviewer to inspect coverage alongside any observed value.",
    ],
    "A. Dataset Quality Index": [
        "For a dataset with r records, exact duplicate quality is computed as 1 minus the redundant exact-duplicate count divided by r. Prompt coverage is the fraction of records containing a prompt. Category and difficulty terms use normalized entropy over present labels. Near-duplicate analysis and novelty require caller-supplied embeddings; their absence is recorded rather than inferred from text similarity. The current repository example contains only three engineering records and is not used as a basis for corpus-quality claims.",
        "The repository example is retained because it exercises ingestion and duplicate handling, including whitespace-normalized injection prompts and a benign prompt. Its source file hash is preserved by the trace. The example contains two prompt-injection records and one benign record, which is inadequate for estimating category balance or model behavior. It is an engineering fixture with known provenance, not a benchmark sampling frame.",
    ],
    "B. Recovery Capability": [
        "The RC runtime consumes previously generated behavioral states and never calls an inference provider. It keeps each baseline probe, attack state, recovery state, active dimension, excluded dimension, displacement, calibration identifier, context status, and diagnostic in the run record. This design enables later inspection of whether an apparent recovery follows retained conversational context or is an artifact of context truncation. A raw score and a bounded display score are separately represented only when the run is applicable.",
        "The required primary dimensions are safety and helpfulness, both normalized to finite values in [0, 1]. Requiring both prevents an evaluator from treating a blanket refusal to benign work as a successful recovery. If either dimension is missing, the local trace records failed_evaluation and missing_required_behavioral_state_dimension. A compatible calibration artifact must additionally identify the RC methodology, distance, dimension schema, and a positive Delta_A floor before a primary RC score is permitted.",
    ],
    "C. Sequential Attack Evaluation": [
        "SAEA stores an ordered sequence identifier, per-step positions, matched isolated-control references, and structured order, Shapley, and recovery-trend diagnostics when they can be computed. The proposed null comparison is retained as a candidate diagnostic rather than a probability of attack success. This preserves the distinction between a sequence-associated behavioral deviation and a policy violation. Incomplete sequences, missing dimensions, and unmatched controls produce typed undefined outputs.",
        "The implementation requires matched baseline protocol, model configuration, generation settings, behavioral schema, measurement versions, and context condition before sequence and isolated states can be compared. In the local trace these prerequisites were not met because required behavioral dimensions were unavailable. The resulting CV_obs, synergy index, order effect, Shapley values, and recovery trend are therefore recorded as undefined rather than fabricated by substituting Layer 1 evidence.",
    ],
    "D. Outcome and Human Validation": [
        "A future study can attach outcome labels through a versioned protocol that defines the unit of analysis, labels, adjudication, exclusions, and denominator policy. The implementation supports blinded exports so raters do not see model identity or experimental condition by default. Agreement statistics are computed after labels exist; they do not create labels or resolve disagreements automatically. This separation keeps a later ASR estimate attributable to an approved protocol rather than to a detector threshold.",
    ],
    "IV. LOCAL ENGINEERING TRACE": [
        "The local run was performed to exercise the complete data path: target inference, metadata capture, Layer 1 evaluation, Layer 2 orchestration, behavioral-state construction, metric applicability checks, trace serialization, and analysis. It ran only models already present in the local Ollama environment. No remote API response, proprietary benchmark, or fabricated model output was added to the trace.",
        "The target configuration was qwen3.5:2b with an observed local model digest, temperature 0.0, seed 2026, and a maximum of 128 predicted tokens. The judge configuration was gemma3:4b, invoked through a JSON-oriented local provider. The trace has a stable identifier, dataset path, dataset SHA-256, prompt protocol, stage timestamps, provider timing, and runner configuration. Those identifiers make a later rerun comparable at the engineering level when the local models remain installed.",
    ],
    "A. Observed Runtime Values": [
        "Latency is reported as a systems measurement in milliseconds for the five configured stages. The mean is 1448.0 ms and the sample standard deviation is 85.3 ms. These values describe one local execution under one model, one hardware/runtime context, and one generation configuration. They should not be used to compare serving performance across devices, models, or production environments.",
        "The stage values were 1598.4 ms for baseline, 1431.9 ms for isolated attack, 1392.4 ms and 1406.9 ms for the two sequential stages, and 1410.5 ms for recovery. The separate descriptive analysis of baseline and isolated stages reported a mean of 1515.1 ms. All stages had a length finish reason and empty response text, so latency remains the only observed numerical trace result suitable for descriptive reporting.",
    ],
    "B. Interpretation": [
        "The appropriate conclusion is operational: the platform retained the model finish reasons, detected incomplete inputs to downstream metrics, and serialized explicit nulls with machine-readable reasons. The appropriate non-conclusion is equally important: a detector aggregate of 0.0 under this trace is not evidence that the target resisted injection, because no explicit attack-success outcome was classified. Likewise, a judge failure is not a low behavioral score.",
    ],
    "V. SCIENTIFIC-INTEGRITY CONTROLS": [
        "Scientific safeguards are implemented at storage, computation, and presentation boundaries. A metric engine receives typed states rather than bare floats, checks applicability before arithmetic, and returns a status and reason alongside any computed value. The API carries these fields to the dashboard, where empty records, API errors, uncalibrated metrics, and unavailable prerequisites have distinct presentations. This reduces the chance that a polished UI inadvertently overstates the evidential status of a result.",
        "The local trace provides a concrete safeguard example. Safety-stance judge output failed a dimension-consistency check, and the target output was empty. The system therefore did not calculate a behavioral vector, RC score, SAEA score, DRAA risk, PRI scalar, or ASR. It emitted nulls and typed reasons. This behavior is more informative than a synthetic zero because it differentiates measurement failure from measured absence of an unsafe outcome.",
    ],
    "A. Prohibited Shortcuts": [
        "The codebase does not contain a default formula that combines Layer 1, Layer 2, BSDA, RC, and SAEA into a single risk number. Such a formula would require a target definition, labelled calibration data, a compatible normalization contract, an uncertainty model, and leakage-controlled validation. Similarly, it does not rank models from partial profiles or re-normalize around only available cells. These omissions are intentional methodological safeguards, not unfinished visual features.",
    ],
    "C. Threats to Validity": [
        "External validity is limited by the current example dataset and the absence of a defined benchmark population. Construct validity is limited by unvalidated judge and metric mappings. Statistical conclusion validity is limited by the lack of repeated independent sessions, approved outcome labels, and a preregistered plan. The paper therefore reports implementation evidence and directs empirical claims to a subsequent study with a declared population, protocol, and validation design.",
    ],
    "VI. REPRODUCIBILITY AND NEXT STUDY": [
        "Reproducibility is supported at three levels. Unit tests check deterministic calculations and failure handling. Smoke tests check health, API behavior, and persisted-record paths. The paper runner writes a portable trace containing prompt stages, response metadata, detector evidence, judge measurements, metric outputs, status reasons, and blockers. A separate analysis command consumes that trace and reports descriptive summaries without upgrading them into confirmatory results.",
        "The fixture-runner path uses deterministic mock inference and mock judging to test trace shape and null handling. The local-runner path invokes only installed Ollama models and retains their provider metadata. Both paths write JSON that can be reviewed without a running dashboard. The analysis command identifies insufficient data for BSDA components, invalid paired input for the requested correlation, null ASR, and blocked supervised ML claims when their inputs are absent.",
    ],
    "A. Reproduction Procedure": [
        "The verified repository run completed 129 Python tests and 19 frontend tests. Frontend typecheck, lint, production build, API smoke checks, and local service checks also completed successfully. These verification counts demonstrate that the current implementation contracts are exercised; they should not be cited as evidence for safety effectiveness. Re-running the local experiment requires installed target and judge models and produces a new trace with its own model and dataset provenance.",
    ],
    "B. Required Work Before a Research Claim": [
        "The next empirical study should lock the evaluated model configurations and benchmark taxonomy before execution, define threat-model-scoped outcomes, and record a public or governed protocol for human review. It should evaluate multiple independent cases, preserve attack-family and session groupings during train/test splitting, assess judge agreement against reference labels, and preregister any statistical test, multiple-comparison policy, and confidence-interval procedure. RC and DRAA calibration artifacts must be versioned and validated against compatible evidence.",
    ],
    "VII. CONCLUSION": [
        "The framework’s contribution is a cautious but practical evaluation substrate. It allows a research team to move from a local model call to a dashboard-visible record without losing the conditions under which the call occurred or concealing missing evidence. Its metric runtimes make their assumptions visible, and its null states stop a report from looking more certain than the data permit. This is the appropriate starting point for a conference study whose empirical claims will be made only after the required benchmark, label, calibration, and validation work is completed.",
    ],
}


CONTRIBUTIONS = [
    "A traceable evaluation workflow that binds dataset identity, model identity, generation configuration, staged prompts, responses, and measurement metadata into one auditable record.",
    "A local execution path for already-installed models, with deterministic mock providers for software testing and local Ollama providers for target and judge execution.",
    "Typed measurement and metric runtimes for Layer 1 evidence, Layer 2 structured judging, BSDA components, Recovery Capability, and sequential evaluation, each with explicit applicability semantics.",
    "Safe persistence, read-only APIs, and a research dashboard that preserves unavailable, failed, undefined, uncalibrated, and empty states instead of converting them into scores.",
    "A reproducibility scaffold with fixture and local traces, analysis scripts, unit tests, API smoke checks, and frontend verification, while retaining blockers for claims that require labels, calibration, or human validation.",
]


RELATED_WORK_POSITION = [
    "SecureLLMBench is positioned as an evaluation substrate rather than a replacement for a benchmark corpus, a red-teaming protocol, or a calibrated risk predictor. Its purpose is to make an evaluation outcome reviewable across the path from a versioned prompt to a rendered dashboard record. The framework therefore keeps data collection, inference, detection, judging, metric computation, storage, and presentation as separate layers with explicit contracts.",
    "Benchmark execution and security detection solve different engineering problems. A benchmark runner needs a stable case identity, provider configuration, and reproducible generation settings. A detector emits evidence under its own rule set. A judge emits a rubric-governed measurement. Treating the three as the same construct creates false certainty, especially when a model response is absent or an evaluator fails. The design maintains their distinct provenance and semantic status.",
    "The metric layer is similarly profile-first. BSDA preserves semantic, safety, instruction, and structural components. RC preserves a behavioral trajectory and calibration dependency. SAEA preserves ordered deviations and matched-control diagnostics. DRAA and PRI preserve evidence profiles while withholding scalar outputs. This design position avoids creating a cross-metric score before an approved estimand, reference population, calibration artifact, and validation plan exist.",
    "The dashboard is part of the evaluation system rather than a separate reporting surface. It reads persisted entities and shows counts, records, status reasons, and provenance. A user can therefore distinguish a model with no persisted Layer 2 result from a model with a low Layer 2 measurement, and a metric blocked by calibration from a metric computed under an approved contract.",
]


RUNTIME_INVARIANTS = [
    "The runtime enforces a set of engineering invariants. A Layer 1 detector result is never promoted to attack success. A Layer 2 value is never presented as ground truth or a calibrated probability. Failed or refused judge outputs remain non-numeric. Missing dimensions are not imputed, and a partial trajectory cannot produce a primary recovery value. These rules are encoded in typed inputs and result statuses rather than left to a paper author’s interpretation.",
    "For Recovery Capability, the behavioral state requires safety and helpfulness dimensions, retained context, finite normalized values, and a compatible external calibration artifact. The primary normalized-Euclidean calculation is recorded together with its baseline, attack displacement, recovery displacements, active dimensions, and reason for any null result. An unavailable calibration artifact produces an uncalibrated trajectory record, not a threshold selected by convenience.",
    "For DRAA and PRI, implementation modes provide evidence transport and profile assembly only. The code does not invent feature weights, a risk target, a missingness policy, a common measurement scale, or a model-ranking rule. Consequently, risk_score and scalar_pri remain null in uncalibrated mode. This is an enforceable interface property that can be checked in tests and reviewed in stored artifacts.",
]


DISCUSSION_LIMITS = [
    "The current database and local trace demonstrate engineering integration, not population-level performance. The repository dataset contains three example records, the local execution trace contains one case, and target responses were empty under the recorded generation limit. The trace is useful because it validates the preservation of failure states, but it cannot estimate attack resistance, judge reliability, or metric effectiveness.",
    "A substantive empirical study must first define a threat-model-scoped outcome taxonomy and a versioned ASR denominator. It must use a benchmark population with case and family identifiers, lock model and harness configurations, collect independent labels or blinded rater judgments, and evaluate judge agreement. Any learned ML or calibrated DRAA predictor must use leakage-reviewed grouped splits and retain calibration, uncertainty, and coverage diagnostics.",
    "The project is therefore ready to support a study, but the study itself remains future work. This limitation is surfaced in the trace, API, and dashboard, where absence of an evaluator output, calibration artifact, or scientific review cannot be mistaken for a favorable numerical result.",
]


STRICT_TO_TRANSITIONAL = {
    b"http://purl.oclc.org/ooxml/officeDocument/relationships": b"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    b"http://purl.oclc.org/ooxml/wordprocessingml/main": b"http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    b"http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing": b"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    b"http://purl.oclc.org/ooxml/drawingml/main": b"http://schemas.openxmlformats.org/drawingml/2006/main",
    b"http://purl.oclc.org/ooxml/officeDocument/relationships/extendedProperties": b"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extendedProperties",
}


def make_editable_template():
    """Copy the user template and convert only its strict namespace identifiers."""
    WORKING.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(REFERENCE) as source, ZipFile(WORKING, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename.endswith((".xml", ".rels")):
                for old, new in STRICT_TO_TRANSITIONAL.items():
                    content = content.replace(old, new)
                content = content.replace(b' w:conformance="strict"', b"")
            target.writestr(info, content)


def remove_template_body(doc):
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def set_columns(section, number):
    sect_pr = section._sectPr
    cols = sect_pr.xpath("./w:cols")
    cols = cols[0] if cols else OxmlElement("w:cols")
    cols.set(qn("w:num"), str(number))
    cols.set(qn("w:space"), "720")  # 36 pt from the supplied template
    if not sect_pr.xpath("./w:cols"):
        sect_pr.append(cols)


def set_font(run, size=8.0, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:cs"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def enforce_times_new_roman(doc):
    """Set every editable text run and paragraph style to Times New Roman."""
    for style in doc.styles:
        try:
            style.font.name = "Times New Roman"
            rpr = style.element.get_or_add_rPr()
            rfonts = rpr.rFonts
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.insert(0, rfonts)
            for field in ("ascii", "hAnsi", "eastAsia", "cs"):
                rfonts.set(qn(f"w:{field}"), "Times New Roman")
        except AttributeError:
            # Some latent/numbering styles have no editable run properties.
            continue

    def enforce_paragraphs(paragraphs):
        for paragraph in paragraphs:
            for run in paragraph.runs:
                set_font(run, size=run.font.size.pt if run.font.size else 8.0, bold=bool(run.bold), italic=bool(run.italic))

    enforce_paragraphs(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                enforce_paragraphs(cell.paragraphs)
                for nested in cell.tables:
                    for nested_row in nested.rows:
                        for nested_cell in nested_row.cells:
                            enforce_paragraphs(nested_cell.paragraphs)
    for section in doc.sections:
        enforce_paragraphs(section.header.paragraphs)
        enforce_paragraphs(section.footer.paragraphs)
        for table in section.header.tables + section.footer.tables:
            for row in table.rows:
                for cell in row.cells:
                    enforce_paragraphs(cell.paragraphs)


def add_text(doc, text, style="Body Text", size=8.0, align=None, indent=True):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    if indent:
        p.paragraph_format.first_line_indent = Inches(0.12)
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    set_font(run, size=size)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style="heading 1" if level == 1 else "heading 2")
    p.paragraph_format.space_before = Pt(4 if level == 1 else 2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    set_font(r, size=9.0 if level == 1 else 8.2, bold=True)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph(style="figure caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_together = True
    r = p.add_run(text)
    set_font(r, size=7.2, italic=True)


def add_bullet(doc, text):
    p = doc.add_paragraph(style="bullet list")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.16)
    p.paragraph_format.first_line_indent = Inches(-0.10)
    r = p.add_run(text)
    set_font(r, size=7.9)
    return p


def remove_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)


def add_author_placeholders(doc):
    """Create the conference-style four-author block below the centered title."""
    people = [
        "[Author 1 Full Name]\n[Department or Research Group]\n[University or Organization]\n[City, Country]\n[author1@example.com]",
        "[Author 2 Full Name]\n[Department or Research Group]\n[University or Organization]\n[City, Country]\n[author2@example.com]",
        "[Author 3 Full Name]\n[Department or Research Group]\n[University or Organization]\n[City, Country]\n[author3@example.com]",
        "[Author 4 Full Name]\n[Department or Research Group]\n[University or Organization]\n[City, Country]\n[author4@example.com]",
    ]
    table = doc.add_table(rows=2, cols=2, style="Normal Table")
    table.autofit = False
    remove_table_borders(table)
    for index, value in enumerate(people):
        cell = table.cell(index // 2, index % 2)
        cell.width = Inches(3.30)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.style = "Author"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        for line_index, line in enumerate(value.split("\n")):
            if line_index:
                p.add_run().add_break()
            r = p.add_run(line)
            set_font(r, size=7.15, bold=(line_index == 0), italic=(line_index in (1, 2)))
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)


def source_paragraphs(source):
    return [(p.text.strip(), any(x.tag.endswith("}drawing") for x in p._p.iter())) for p in source.paragraphs]


def add_small_table(doc, source_table):
    rows = len(source_table.rows)
    cols = len(source_table.columns)
    table = doc.add_table(rows=rows, cols=cols, style="Normal Table")
    table.autofit = False
    # A4 conference body columns are approximately 3.25 in wide after the 36 pt gutter.
    # Leaving 0.17 in of breathing room prevents right-edge clipping in Word/PDF viewers.
    usable = 3.08
    for row_i, row in enumerate(source_table.rows):
        for col_i, cell in enumerate(row.cells):
            dst = table.cell(row_i, col_i)
            dst.width = Inches(usable / cols)
            dst.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = dst.paragraphs[0]
            p.style = "table col head" if row_i == 0 else "table copy"
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if row_i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(cell.text)
            set_font(r, size=6.4, bold=(row_i == 0))
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(3)


def main():
    make_editable_template()
    source = Document(SOURCE)
    doc = Document(WORKING)
    remove_template_body(doc)
    first = doc.sections[0]
    # Exact A4 template geometry from the supplied source.
    first.top_margin = Inches(27 / 72)
    first.bottom_margin = Inches(72 / 72)
    first.left_margin = Inches(44.65 / 72)
    first.right_margin = Inches(44.65 / 72)
    set_columns(first, 1)

    # Template-derived first-page title and metadata block.
    title = add_text(doc, "SecureLLMBench: A Traceable Framework for Safety and Security Evaluation of Local Large Language Models", style="paper title", size=18.0, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    title.paragraph_format.space_after = Pt(6)
    add_author_placeholders(doc)

    body = doc.add_section(WD_SECTION.CONTINUOUS)
    set_columns(body, 2)
    body.top_margin = first.top_margin
    body.bottom_margin = first.bottom_margin
    body.left_margin = first.left_margin
    body.right_margin = first.right_margin

    # The reference starts Abstract and Index Terms below the author block in the
    # left-hand conference column, while the introduction continues naturally
    # into the right-hand column on the same A4 first page.
    abstract = "SecureLLMBench is a research-oriented framework for traceable local large language model evaluation under benign, isolated-attack, sequential-attack, and recovery conditions. It preserves versioned inputs, model settings, detector evidence, structured judge measurements, metric artifacts, and explicit failure states. This conference-format paper reports the implemented system and a local engineering trace using qwen3.5:2b as target and gemma3:4b as judge. The trace confirms execution and provenance capture, but does not provide a model-security result: responses were empty at the configured limit, some judge dimensions failed validation, and no classified attack outcomes existed."
    p = doc.add_paragraph(style="Abstract")
    p.paragraph_format.space_after = Pt(3)
    lead = p.add_run("Abstract—")
    set_font(lead, size=7.9, bold=True, italic=True)
    rest = p.add_run(abstract)
    set_font(rest, size=7.9, bold=True)
    keywords = doc.add_paragraph(style="Keywords")
    keywords.paragraph_format.space_after = Pt(4)
    lead = keywords.add_run("Index Terms—")
    set_font(lead, size=7.4, bold=True, italic=True)
    rest = keywords.add_run("LLM security evaluation, reproducibility, local inference, benchmark provenance, behavioral measurement, scientific safeguards.")
    set_font(rest, size=7.4, bold=True, italic=True)

    image_index = 0
    table_index = 0
    section_breaks = {"II. SYSTEM ARCHITECTURE", "III. MEASUREMENT DESIGN AND CALCULATIONS", "IV. LOCAL ENGINEERING TRACE", "V. SCIENTIFIC-INTEGRITY CONTROLS", "VI. REPRODUCIBILITY AND NEXT STUDY"}
    for text, has_drawing in source_paragraphs(source):
        if has_drawing:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(str(ASSETS[image_index]), width=Inches(3.18))
            image_index += 1
            continue
        if not text:
            continue
        if text.startswith("SecureLLMBench:") or text == "Anonymous IEEE-Style Research Draft" or text == "Abstract" or text.startswith("Index Terms"):
            continue
        if text.startswith("TABLE "):
            add_caption(doc, text)
            add_small_table(doc, source.tables[table_index])
            table_index += 1
            continue
        if text.startswith("Fig."):
            add_caption(doc, text)
            continue
        if text in section_breaks:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            if text == "II. SYSTEM ARCHITECTURE":
                add_heading(doc, "II. RELATED WORK AND DESIGN POSITION", 1)
                for paragraph in RELATED_WORK_POSITION:
                    add_text(doc, paragraph, style="Body Text", size=7.9)
                add_heading(doc, "III. SYSTEM AND EVALUATION MODEL", 1)
                for detail in DETAIL_BY_HEADING[text]:
                    add_text(doc, detail, style="Body Text", size=7.9)
            elif text == "III. MEASUREMENT DESIGN AND CALCULATIONS":
                add_heading(doc, "IV. MEASUREMENT PROTOCOL AND METRIC RUNTIME", 1)
                for detail in DETAIL_BY_HEADING[text]:
                    add_text(doc, detail, style="Body Text", size=7.9)
            elif text == "IV. LOCAL ENGINEERING TRACE":
                add_heading(doc, "V. RUNTIME INVARIANTS AND FAILURE HANDLING", 1)
                for paragraph in RUNTIME_INVARIANTS:
                    add_text(doc, paragraph, style="Body Text", size=7.9)
                add_heading(doc, "VI. LOCAL ENGINEERING TRACE", 1)
                for detail in DETAIL_BY_HEADING[text]:
                    add_text(doc, detail, style="Body Text", size=7.9)
            elif text == "V. SCIENTIFIC-INTEGRITY CONTROLS":
                add_heading(doc, "VII. DISCUSSION LIMITATIONS AND INTEGRITY CONTROLS", 1)
                for detail in DETAIL_BY_HEADING[text]:
                    add_text(doc, detail, style="Body Text", size=7.9)
                for paragraph in DISCUSSION_LIMITS:
                    add_text(doc, paragraph, style="Body Text", size=7.9)
            elif text == "VI. REPRODUCIBILITY AND NEXT STUDY":
                add_heading(doc, "VIII. REPRODUCIBILITY AND ARTIFACT AVAILABILITY", 1)
                for detail in DETAIL_BY_HEADING[text]:
                    add_text(doc, detail, style="Body Text", size=7.9)
            continue
        if text in DETAIL_BY_HEADING and text[:1] in {"I", "V"}:
            title = "IX. CONCLUSION" if text == "VII. CONCLUSION" else text
            add_heading(doc, title, 1)
            for detail in DETAIL_BY_HEADING[text]:
                add_text(doc, detail, style="Body Text", size=7.9)
            continue
        if text.startswith(("A. ", "B. ", "C. ", "D. ")):
            add_heading(doc, text, 2)
            for detail in DETAIL_BY_HEADING.get(text, []):
                add_text(doc, detail, style="Body Text", size=7.9)
            continue
        if text == "REFERENCES":
            add_heading(doc, text, 1)
            continue
        if text.startswith("["):
            add_text(doc, text, style="references", size=7.4, indent=False)
            continue
        add_text(doc, text, style="Body Text", size=7.9)
        if text == "This paper is an implementation and trace report. It does not present a broad benchmark comparison, validated attack success rate (ASR), calibration study, or model ranking. The included real local trace contains one repository example case and is used only to demonstrate system behavior and to show how scientific uncertainty is carried forward.":
            add_text(doc, "The implemented contributions are as follows:", style="Body Text", size=7.9)
            for contribution in CONTRIBUTIONS:
                add_bullet(doc, contribution)

    doc.core_properties.title = "SecureLLMBench Conference A4 Paper"
    doc.core_properties.author = "SecureLLMBench"
    enforce_times_new_roman(doc)
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    doc.save(FINAL)
    print(FINAL)


if __name__ == "__main__":
    main()
