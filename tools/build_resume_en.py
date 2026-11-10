# -*- coding: utf-8 -*-
import sys, pathlib
sys.path.insert(0, '/tmp/pdflib')
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable)
from reportlab.lib import colors

# Helvetica covers Latin; STHeiti only used if any CJK slips in
BODY  = ParagraphStyle('B', fontName='Helvetica', fontSize=9.2, leading=13.2, alignment=TA_LEFT)
BOLD  = ParagraphStyle('BD', fontName='Helvetica-Bold', fontSize=9.2, leading=13.2)
NAME  = ParagraphStyle('N', fontName='Helvetica-Bold', fontSize=18, leading=22)
ROLE  = ParagraphStyle('R', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#333333'))
SEC   = ParagraphStyle('S', fontName='Helvetica-Bold', fontSize=10, leading=14,
                       textColor=colors.HexColor('#0B3D63'), spaceBefore=8, spaceAfter=3)
ORG   = ParagraphStyle('O', fontName='Helvetica-Bold', fontSize=9.4, leading=13)
META  = ParagraphStyle('M', fontName='Helvetica-Oblique', fontSize=8.6, leading=12,
                       textColor=colors.HexColor('#555555'))
BUL   = ParagraphStyle('BU', parent=BODY, leftIndent=11, bulletIndent=2, spaceAfter=1.2)

NAME_T = 'Hengji Zhang'
ROLE_T = 'Quantitative Research & Investment Data Analytics  |  Market Data Due Diligence, PIT Validation, Factor Verification'
CONTACT = ('bosprimigenious@bupt.edu.cn  ·  github.com/bosprimigenious  ·  bosprimigenious.github.io  ·  Beijing, China')

SUMMARY = (
 "Quantitative research and investment-data specialist with hands-on experience across two sell-side "
 "and buy-side internships: alternative-data tracking at a top-tier brokerage research institute and "
 "investment-data verification inside a leading securities asset-management arm. Work centres on whether "
 "a number can be used at a given decision date - source licensing, point-in-time (PIT) availability, "
 "entity mapping validity, unit and frequency consistency, coverage denominators and missing-value "
 "semantics - then on whether a signal survives out-of-sample and after trading costs. Certified "
 "CFA Level 2 candidate; builds reproducible, fully traceable workbooks rather than narrative reports."
)

COMPETENCIES = [
 ("Market data due diligence", "source licensing, coverage denominators, PIT vs snapshot, publication calendars, revision history"),
 ("Entity & instrument mapping", "share-code reuse, cross-exchange duplicates (000001.SH vs 000001.SZ), fund-vs-portfolio aggregation, SPV chains"),
 ("Missing-value taxonomy", "UNKNOWN vs NOT_OBSERVED vs NOT_PROVEN; prohibiting zero-fill and its effect on coverage"),
 ("Quant factor validation", "IC / RankIC, layered backtests, decay curves, parameter grids, out-of-sample and survivorship control"),
 ("Trading-cost economics", "turnover-to-cost conversion, impact estimates, gross vs net return, capacity limits"),
 ("LLM benchmark quality", "rubric authoring, adjudication, six mandatory validation checks, hallucination case library"),
]

EXPERIENCE = [
 dict(org='CITIC Securities · Asset Management', role='Investment Data Verification Intern',
      when='Mar 2023 - Present', where='Beijing',
      bullets=[
       "Verify the factual queries behind investment-research outputs: 1,200+ alternative and market indicators "
       "(freight rates, capacity utilisation, production schedules, tenders, satellite and passenger-flow series) "
       "checked under a four-step template - raise, reconcile, evidence, conclude.",
       "Run three-way source comparison across Wind, Bloomberg, iFinD and third-party alternative vendors; classify "
       "every discrepancy into five causes (definition, update timing, entity mapping, unit/precision, discontinuation) "
       "so recurring breaks are fixed at the definition level rather than re-checked each cycle.",
       "Authored 80+ methodology documents, each stating definition, formula, frequency, unit, publication calendar, "
       "change log, known defects and applicability boundary - used downstream as the acceptance basis for queries.",
       "Maintain a change-and-sample-adjustment ledger (date, before/after value, affected scope) and a "
       "discontinuation register recording the last valid publication date, preventing stale snapshots from being "
       "consumed as current data.",
      ]),
 dict(org='Shenwan Hongyuan Securities · Research Institute', role='Cyclical Industries Research Intern (Transport & Commodities)',
      when='Feb 2021 - Feb 2023', where='Beijing',
      bullets=[
       "Co-maintained high-frequency alternative databases - container freight (SCFI / CCFI / BFI families), blast-furnace "
       "and cement utilisation, order books and production schedules, tender award values, freight volume and passenger "
       "flow - supporting 240+ weekly notes and thematic data commentaries across 10+ sub-sectors.",
       "Built the indicator ledger: publishing entity, frequency, history start, release time and licensing constraint for "
       "every series, which later became the denominator source for coverage checks.",
       "Cross-validated 1,500+ alternative indicators, reconciling same-source definition variants (composite vs route-level, "
       "tax-inclusive vs exclusive, MoM vs YoY base) and flagging definition changes and sample-universe adjustments.",
       "Applied seasonal adjustment and base restoration to freight-rate and utilisation series, and separated initial prints, "
       "revised prints and forecast vintages in working papers so revised values were never presented as first releases.",
      ]),
 dict(org='Independent Expert Engagement · Financial Benchmark Quality', role='Part-time Expert Reviewer (LLM Evaluation)',
      when='Jun 2024 - Present', where='Remote',
      bullets=[
       "Review 1,300+ model responses for market-data query benchmarks: rubric scoring, ground-truth cross-checks and "
       "180+ cross-reviewer adjudications; contributed sample screening, criterion decomposition, rubric calibration and "
       "dispute post-mortems.",
       "Enforced six mandatory checks: PIT availability by publication date; entity-mapping validity windows including "
       "cross-market duplicate codes; unit and frequency consistency (index points vs percent, TEU vs FEU, daily vs weekly); "
       "coverage numerator/denominator alignment; missing-value taxonomy instead of zero-fill; and feasibility of documented "
       "replacement sources.",
       "Maintain a hallucination case library of 260+ instances (snapshot passed as PIT, missing values zero-filled, wrong "
       "coverage denominator, uncitable source, silent definition swap), classified by error type, trigger condition, "
       "decision boundary and correct handling; issued 110+ root-cause reports feeding the annotation standard.",
       "Compiled replacement-source lists for 70+ discontinued, low-frequency or broken series, recording channel, update "
       "cadence, definitional gap versus the original indicator and a comparability verdict.",
      ]),
]

QUANT = [
 dict(org='WorldQuant BRAIN · Alpha Research (concurrent with asset-management internship)',
      role='Alpha research and factor validation', when='Jun 2023 - Present',
      bullets=[
       "Construct cross-sectional and event-driven factors from price-volume, fundamental and alternative inputs "
       "(freight, utilisation, passenger flow, tenders); each factor carries a registry entry for input fields, frequency, "
       "unit, availability date and source permission.",
       "Evaluate single factors with IC / RankIC, layered backtests, long-short spread and turnover; retain decay curves "
       "across holding periods, and archive factor definition, universe and industry-neutralisation scheme together so "
       "results produced under different parameterisations are never pooled.",
       "Test robustness through out-of-sample windows, parameter grids and year-by-market-cap stability, guarding against "
       "reporting the best in-sample parameter set as the result.",
       "Convert turnover into commission and impact cost to report net-of-cost return and capacity, rather than gross spread.",
       "Control look-ahead and survivorship: align strictly to publication date, use point-in-time index constituents, and "
       "archive delisted or removed names separately.",
       "Gate factor admission on data acceptance: coverage, missing-value type and update frequency bound the usable sample "
       "and therefore IC reliability, so sources failing acceptance never enter factor computation.",
      ]),
]

PROJECTS = [
 dict(name='TextGuard - Chinese AI-generated-text detection platform', when='Nov 2025 - Jul 2026',
      role='Project lead (undergraduate innovation programme)',
      bullets=[
       "Designed and built a full-stack detection platform (Python / FastAPI inference, React / TypeScript front end) with "
       "risk visualisation, explanation panel, sample comparison and exportable detection reports.",
       "Authored TextGuard-Bench (five-axis evaluation suite) and the MGAB held-out attack protocol; quantified "
       "in-distribution versus OOD separation with a G3 metric instead of a single accuracy figure.",
      ]),
 dict(name='MingChaWanXiang - multimodal research-integrity monitoring platform', when='Jan 2026 - Jun 2026',
      role='Engineering intern, Information Network Engineering Research Centre, MOE',
      bullets=[
       "Contributed multi-stage recall and similarity search (CLIP + Milvus) to detect image reuse, paper-mill output and "
       "AIGC artefacts across text, figures, formulas, tables and citation networks.",
       "Supported evidence-chain construction and report export; every finding is traceable to a source location.",
      ]),
 dict(name='Zhilian 3.0 - university LLM practice platform', when='Jul 2025 - Jan 2026',
      role='Full-stack intern, Information Network Engineering Research Centre, MOE',
      bullets=[
       "Implemented list, filter, pagination and record-version views in Vue 3 + TypeScript; aligned field definitions, "
       "error codes and record versions with backend, with empty-result, no-permission and timeout states surfaced explicitly.",
      ]),
]

RESEARCH = [
 "Hengji Zhang et al., \"TextGuard: a dual-path semantic-statistical robust framework for Chinese AI-generated text "
 "detection\", NeurIPS 2026, under review (student first author / co-first author). Contributions: LPP statistical "
 "features, MGAB held-out protocol, cross-dataset OOD design. Holdout n=33,739: Acc 98.75%, AUC 0.9992, MCC 0.9746; "
 "QA n=3,516: AUC 0.950.",
]

SKILLS = [
 ("Programming & data", "Python (pandas / NumPy, backtesting and factor evaluation), SQL, Excel advanced functions and pivot tables, FastAPI, React / TypeScript"),
 ("Platforms", "Wind, Bloomberg, iFinD, WorldQuant BRAIN, Milvus, CLIP"),
 ("Methods", "PIT alignment, entity-mapping validity, coverage and denominator design, missing-value taxonomy, factor validation, cost and capacity estimation"),
]

EDU = dict(school='Beijing University of Posts and Telecommunications (BUPT)', degree='B.Eng. in Computer Science and Technology',
           when='Sep 2024 - Jun 2028 (expected)', note='Rank 47/452 (top 10%). Coursework: Data Structures 100, OOP 100, Mathematical Modelling 99.')
CERTS = [("CFA", "Level 2"),
         ("Languages", "IELTS 6.5; CET-4 and CET-6 passed. Reads English filings, prospectuses, overseas research and English data dictionaries; verifies field definitions in Bloomberg English UI and vendor documentation.")]
HONOURS = ["National-level competition awards: 2  ·  Provincial / ministerial: 8  ·  University-level: 4",
           "University second-class scholarship; Merit Student; 2026 campus top-10 psychological-support volunteer (nominee)"]

# ---------------- render ----------------
story = [Paragraph(NAME_T, NAME), Paragraph(ROLE_T, ROLE), Spacer(1, 2),
         Paragraph(CONTACT, META), Spacer(1, 3),
         HRFlowable(width='100%', thickness=0.8, color=colors.HexColor('#0B3D63')), Spacer(1, 4)]

story.append(Paragraph('PROFILE', SEC)); story.append(Paragraph(SUMMARY, BODY))

story.append(Paragraph('CORE COMPETENCIES', SEC))
rows = [[Paragraph(f'<b>{a}</b>', BODY), Paragraph(b, BODY)] for a, b in COMPETENCIES]
t = Table(rows, colWidths=[42*mm, 128*mm])
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                       ('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),1),
                       ('BOTTOMPADDING',(0,0),(-1,-1),1)]))
story.append(t)

story.append(Paragraph('PROFESSIONAL EXPERIENCE', SEC))
for e in EXPERIENCE:
    story.append(Paragraph(f"{e['org']}  —  {e['role']}", ORG))
    story.append(Paragraph(f"{e['when']}  ·  {e['where']}", META))
    for b in e['bullets']:
        story.append(Paragraph(b, BUL, bulletText='•'))
    story.append(Spacer(1, 2))

story.append(Paragraph('QUANTITATIVE RESEARCH & FACTOR VERIFICATION', SEC))
for e in QUANT:
    story.append(Paragraph(f"{e['org']}", ORG))
    story.append(Paragraph(f"{e['role']}  ·  {e['when']}", META))
    for b in e['bullets']:
        story.append(Paragraph(b, BUL, bulletText='•'))
    story.append(Spacer(1, 2))

story.append(Paragraph('SELECTED PROJECTS', SEC))
for p in PROJECTS:
    story.append(Paragraph(f"{p['name']}  —  {p['role']}", ORG))
    story.append(Paragraph(p['when'], META))
    for b in p['bullets']:
        story.append(Paragraph(b, BUL, bulletText='•'))
    story.append(Spacer(1, 1))

story.append(Paragraph('PUBLICATION', SEC))
for r in RESEARCH:
    story.append(Paragraph(r, BUL, bulletText='•'))

story.append(Paragraph('SKILLS & TOOLS', SEC))
rows = [[Paragraph(f'<b>{a}</b>', BODY), Paragraph(b, BODY)] for a, b in SKILLS]
t = Table(rows, colWidths=[38*mm, 132*mm])
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                       ('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),1),
                       ('BOTTOMPADDING',(0,0),(-1,-1),1)]))
story.append(t)

story.append(Paragraph('EDUCATION', SEC))
story.append(Paragraph(f"{EDU['school']} — {EDU['degree']}", ORG))
story.append(Paragraph(EDU['when'], META))
story.append(Paragraph(EDU['note'], BODY))
for h in HONOURS:
    story.append(Paragraph(h, BUL, bulletText='•'))

story.append(Paragraph('CERTIFICATIONS & LANGUAGES', SEC))
for a, b in CERTS:
    story.append(Paragraph(f'<b>{a}:</b> {b}', BODY))

out = 'deliverables/resume-en/Hengji-Zhang-Resume-Finance-Quant.pdf'
doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                        topMargin=14*mm, bottomMargin=13*mm,
                        title='Hengji Zhang — Finance & Quantitative Research Resume', author='Hengji Zhang')
doc.build(story)
print('pdf', pathlib.Path(out).stat().st_size)
