# -*- coding: utf-8 -*-
"""English CV: finance/quant + every CS experience, reverse-chronological."""
import sys, json, pathlib
sys.path.insert(0, '/tmp/pdflib')
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether)
from reportlab.lib import colors

BODY = ParagraphStyle('B', fontName='Helvetica', fontSize=8.9, leading=12.4, alignment=TA_LEFT)
NAME = ParagraphStyle('N', fontName='Helvetica-Bold', fontSize=17.5, leading=21)
ROLE = ParagraphStyle('R', fontName='Helvetica', fontSize=9.2, leading=13, textColor=colors.HexColor('#243447'))
SEC  = ParagraphStyle('S', fontName='Helvetica-Bold', fontSize=9.6, leading=13,
                      textColor=colors.HexColor('#0B3D63'), spaceBefore=7, spaceAfter=2.5)
ORG  = ParagraphStyle('O', fontName='Helvetica-Bold', fontSize=9.1, leading=12.6)
META = ParagraphStyle('M', fontName='Helvetica-Oblique', fontSize=8.2, leading=11.4,
                      textColor=colors.HexColor('#5a5a5a'))
BUL  = ParagraphStyle('BU', parent=BODY, leftIndent=10, bulletIndent=1, spaceAfter=1.0)

NAME_T = 'HENGJI ZHANG'
ROLE_T = ('Quantitative Research · Investment Data Engineering · Machine Learning Systems  |  '
          'Market-data due diligence, point-in-time validation, factor verification, LLM benchmark design')
CONTACT = 'bosprimigenious@bupt.edu.cn  ·  github.com/bosprimigenious  ·  bosprimigenious.github.io  ·  Beijing, China'

PROFILE = (
 'Computer-science undergraduate working at the intersection of market data and machine-learning systems. '
 'Two research/data internships in securities (alternative-data tracking at a sell-side institute; investment-data '
 'verification at an asset manager) plus a part-time benchmark-quality engagement, alongside four ship-and-ship '
 'engineering roles: a multimodal integrity platform (CLIP + Milvus), a Chinese AI-text detection platform built '
 'end to end, a university LLM practice platform, and a first-author detection framework under review at NeurIPS 2026. '
 'Habit of building the measurement before the claim: every number carries a source ID, a publication date and a '
 'reproducible workbook.'
)

CURRENT = [
 dict(org='Independent Expert Engagement — Financial Benchmark Quality',
      role='Part-time Expert Reviewer (LLM evaluation)', when='Jun 2024 – Present', where='Remote',
      bullets=[
       'Review 1,300+ model responses for market-data query benchmarks: rubric scoring, ground-truth cross-checks, '
       'and 180+ cross-reviewer adjudications; contributed sample screening, criterion decomposition, rubric '
       'calibration and dispute post-mortems.',
       'Enforce six mandatory checks: PIT availability by publication date; entity-mapping validity windows including '
       'cross-market duplicate codes; unit and frequency consistency (index points vs percent, TEU vs FEU, daily vs '
       'weekly); coverage numerator/denominator alignment; missing-value taxonomy instead of zero-fill; feasibility of '
       'documented replacement sources.',
       'Maintain a hallucination case library of 260+ instances (snapshot passed as PIT, missing values zero-filled, '
       'wrong coverage denominator, uncitable source, silent definition swap), classified by error type, trigger '
       'condition, decision boundary and correct handling; issued 110+ root-cause reports that fed back into the '
       'annotation standard.',
       'Compiled replacement-source registers for 70+ discontinued, low-frequency or broken series, each recording '
       'channel, update cadence, definitional gap versus the original indicator and a comparability verdict.',
      ]),
 dict(org='WorldQuant BRAIN — Alpha Research',
      role='Alpha research and factor validation (concurrent)', when='Jun 2023 – Present', where='Remote',
      bullets=[
       'Construct cross-sectional and event-driven factors from price-volume, fundamental and alternative inputs '
       '(freight, utilisation, passenger flow, tenders); every factor carries a registry entry for input fields, '
       'frequency, unit, availability date and source permission.',
       'Evaluate single factors with IC / RankIC, layered backtests, long-short spread and turnover; retain decay '
       'curves across holding periods, and archive factor definition, universe and industry-neutralisation scheme '
       'together so results from different parameterisations are never pooled.',
       'Test robustness with out-of-sample windows, parameter grids and year-by-market-cap stability, guarding against '
       'reporting the best in-sample parameter set as the result.',
       'Convert turnover into commission and market-impact cost to report net-of-cost return and capacity, not gross spread.',
       'Control look-ahead and survivorship: align strictly to publication date, use point-in-time index constituents, '
       'and archive delisted or removed names separately.',
       'Gate factor admission on data acceptance — coverage, missing-value type and update frequency bound the usable '
       'sample and therefore IC reliability, so sources that fail acceptance never enter factor computation.',
      ]),
 dict(org='CITIC Securities · Asset Management',
      role='Investment Data Verification Intern', when='Mar 2023 – Present', where='Beijing',
      bullets=[
       'Verify the factual queries behind investment-research output: 1,200+ alternative and market indicators '
       '(freight rates, capacity utilisation, production schedules, tender awards, satellite and passenger-flow '
       'series) checked under a four-step template — raise, reconcile, evidence, conclude.',
       'Run three-way source comparison across Wind, Bloomberg, iFinD and third-party alternative vendors; classify '
       'every discrepancy into five causes (definition, update timing, entity mapping, unit/precision, discontinuation) '
       'so a recurring break is fixed at the definition level instead of re-checked every cycle.',
       'Authored 80+ methodology documents stating definition, formula, frequency, unit, publication calendar, change '
       'log, known defects and applicability boundary; these became the acceptance basis for downstream queries.',
       'Maintain a change-and-sample-adjustment ledger (date, before/after value, affected scope) and a discontinuation '
       'register holding the last valid publication date, preventing stale snapshots from being consumed as current data.',
      ]),
]

TIMELINE = [
 dict(org='Information Network Engineering Research Centre, Ministry of Education',
      role='Engineering Intern — MingChaWanXiang research-integrity platform', when='Jan 2026 – Jun 2026', where='Beijing',
      bullets=[
       'Contributed to a multimodal research-integrity platform spanning text, figures, formulas, tables and citation '
       'networks, targeting paper-mill output, duplicate submission, image reuse and AIGC artefacts.',
       'Built multi-stage recall and similarity retrieval with CLIP embeddings stored in Milvus, supporting reuse '
       'localisation and side-by-side comparison rather than a single opaque score.',
       'Integrated LLM reasoning into the review flow and worked on risk visualisation, detection-report generation and '
       'evidence presentation; every exported finding is traceable to a source location.',
      ]),
 dict(org='TextGuard — Chinese AI-generated-text detection platform',
      role='Founder and Technical Lead (undergraduate innovation programme)', when='Nov 2025 – Jul 2026', where='Beijing',
      bullets=[
       'Designed and shipped a full-stack detection platform: Python / FastAPI inference service, React / TypeScript '
       'front end, risk visualisation, explanation panel, sample comparison and exportable detection reports; platform live.',
       'Defined the product around evidence rather than a verdict — each detection exposes the features that drove it, '
       'the comparison sample used, and the report that a reviewer can re-check.',
       'Led a small team through design, implementation, model training experiments, evaluation logging and project '
       'reporting; filed for the undergraduate innovation programme with paper, software-copyright and patent outputs planned.',
      ]),
 dict(org='Information Network Engineering Research Centre, Ministry of Education',
      role='Full-stack Intern — Zhilian 3.0, university LLM practice platform', when='Jul 2025 – Jan 2026', where='Beijing',
      bullets=[
       'Owned one vertical slice from page to API in Vue 3 + TypeScript: list, filter, pagination and record-version '
       'views, with multi-condition state carried in the query string.',
       'Aligned field definitions, error codes and record versions with the backend, and surfaced empty-result, '
       'no-permission and timeout states explicitly so a cold start is never mistaken for an outage.',
       'Worked to a "reproducible from the public site" bar — institute review score 90.00.',
      ]),
 dict(org='Shenwan Hongyuan Securities · Research Institute',
      role='Cyclical Industries Research Intern (transport and commodities)', when='Feb 2021 – Feb 2023', where='Beijing',
      bullets=[
       'Co-maintained high-frequency alternative databases — container freight (SCFI / CCFI / BFI families), blast-furnace '
       'and cement utilisation, order books and production schedules, tender award values, freight volume and passenger '
       'flow — supporting 240+ weekly notes and data commentaries across 10+ sub-sectors.',
       'Built the indicator ledger: publishing entity, frequency, history start, release time and licensing constraint '
       'per series; it later became the denominator source for coverage checks.',
       'Cross-validated 1,500+ alternative indicators, reconciling same-source definition variants (composite vs '
       'route-level, tax-inclusive vs exclusive, MoM vs YoY base) and flagging definition changes and sample-universe shifts.',
       'Applied seasonal adjustment and base restoration to freight-rate and utilisation series, and separated initial '
       'prints, revised prints and forecast vintages in working papers so a revised value was never presented as a first release.',
      ]),
]

RESEARCH_HEAD = 'Research and Publication'
PAPER = dict(
 title='TextGuard: A Dual-Path Semantic–Statistical Robust Framework for Chinese AI-Generated Text Detection',
 authors='Hengji Zhang et al. (student first author / co-first author)',
 venue='NeurIPS 2026 — under review',
 body=[
  'Problem. Chinese AI-generated-text detectors generalise poorly out of distribution. Concatenating statistical '
  'features with a semantic encoder creates a shortcut: the statistical head carries most of the in-distribution signal, '
  'then collapses when the generator or domain shifts, because the two representations are fused without any gating '
  'on the semantic path.',
  'Method. Two components replace naive concatenation. CDFI (Cross-Domain Feature Injection) treats five LPP statistics '
  'as a query over the semantic representation and injects them through residual gating instead of channel '
  'concatenation, so statistical evidence modulates the encoder rather than bypassing it. GA-AT (Granularity-Aware '
  'Adversarial Training) applies PGD perturbations at character, word and sentence granularity, forcing the decision '
  'boundary to stay stable under local rewrites that humans consider meaning-preserving.',
  'Features. A parallel Erlangshen + CNN–BiLSTM branch computes five interpretable LPP signals — four-character '
  'collocation, structural-particle usage, punctuation entropy, type-token ratio and sentence-length distribution — '
  'chosen for their known asymmetry between human and generated Chinese text.',
  'Leakage control. Training uses HC3 only; no benchmark sample is ever seen during fitting, and the evaluation suites '
  'are held out at document level rather than chunk level.',
  'Evaluation. TextGuard-Bench defines five evaluation axes; MGAB supplies a held-out attack set; G3 quantifies the gap '
  'between in-distribution and out-of-distribution AUC, so a model that wins in-distribution but degrades under shift '
  'is not rewarded. Baselines: BERT, RADAR and a Chinese paraphrase-uncertainty detector.',
  'Results. Holdout n = 33,739: accuracy 98.75%, AUC 0.9992, MCC 0.9746. Question-answer subset n = 3,516: AUC 0.950.',
  'My contribution. LPP feature design, the MGAB held-out protocol, and the cross-dataset OOD evaluation design; '
  'co-authored the method and wrote the evaluation section.',
 ],
)

EDU = dict(
 school='Beijing University of Posts and Telecommunications (BUPT)',
 degree='B.Eng. in Computer Science and Technology',
 when='Sep 2024 – Jun 2028 (expected)', where='Beijing',
 facts=[
  'Rank 47 / 452 (top 10%) in the major.',
  'Coursework: Data Structures and Course Design 100, Object-Oriented Programming 100, Mathematical Modelling 99, '
  'Introduction to Computers and Programming 97, Big Data Practice 95, Intelligent Robotics Practice 92.',
  'Campus roles: psychological-support committee member, Class 301, School of Computer Science (2024 – present; '
  'campus top-10 psychological-support volunteer, nominee, 2026); university middle/long-distance running team '
  '(2024 – 2025); 123 hours of volunteering.',
  'Interests: middle/long-distance running (5 km PB 18:20), marathons, football, tennis, reading, writing fiction; '
  'self-taught French.',
 ])
HONOURS = ['National-level competition awards: 2 · Provincial / ministerial: 8 · University-level: 4',
           'University second-class scholarship; Merit Student (三好学生) — 1 each']
SKILLS = [
 ('Languages', 'Python (primary), TypeScript / JavaScript, SQL, Java (coursework), Bash'),
 ('ML / data', 'PyTorch, pandas / NumPy, scikit-learn, CLIP, Milvus vector search, LLM inference and prompt evaluation'),
 ('Web / services', 'FastAPI, React, Vue 3, Vite, REST / JSON, auth and error-code design, pagination and versioning'),
 ('Finance data', 'Wind, Bloomberg, iFinD, WorldQuant BRAIN; PIT alignment, coverage and denominator design, '
                  'entity-mapping validity, missing-value taxonomy, factor validation and cost-adjusted returns'),
]
CERTS = [('CFA', 'Level 2'), ('Languages (tests)', 'IELTS 6.5; CET-4 and CET-6 passed')]

# ---- render ----
story = [Paragraph(NAME_T, NAME), Paragraph(ROLE_T, ROLE), Spacer(1, 1.5), Paragraph(CONTACT, META), Spacer(1, 2),
         HRFlowable(width='100%', thickness=0.9, color=colors.HexColor('#0B3D63')), Spacer(1, 3)]
story.append(Paragraph('PROFILE', SEC)); story.append(Paragraph(PROFILE, BODY))

def job(e, first=False):
    blk = [Paragraph(f"{e['org']}", ORG), Paragraph(f"{e['role']}  ·  {e['when']}  ·  {e['where']}", META)]
    blk += [Paragraph(b, BUL, bulletText='•') for b in e['bullets']]
    blk.append(Spacer(1, 2.5))
    return [KeepTogether(blk)]

story.append(Paragraph('CURRENT ROLES', SEC))
for e in CURRENT: story += job(e)

story.append(Paragraph('EXPERIENCE, REVERSE-CHRONOLOGICAL', SEC))
for e in TIMELINE: story += job(e)

story.append(Paragraph(RESEARCH_HEAD.upper(), SEC))
story.append(Paragraph(PAPER['title'], ORG))
story.append(Paragraph(f"{PAPER['authors']}  ·  {PAPER['venue']}", META))
for b in PAPER['body']:
    story.append(Paragraph(b, BUL, bulletText='•'))

story.append(Paragraph('EDUCATION', SEC))
story.append(Paragraph(EDU['school'], ORG))
story.append(Paragraph(f"{EDU['degree']}  ·  {EDU['when']}  ·  {EDU['where']}", META))
for f in EDU['facts']:
    story.append(Paragraph(f, BUL, bulletText='•'))

story.append(Paragraph('HONOURS AND AWARDS', SEC))
for h in HONOURS:
    story.append(Paragraph(h, BUL, bulletText='•'))

story.append(Paragraph('TECHNICAL SKILLS', SEC))
rows = [[Paragraph(f'<b>{a}</b>', BODY), Paragraph(b, BODY)] for a, b in SKILLS]
t = Table(rows, colWidths=[30*mm, 140*mm])
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                       ('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),0.8),
                       ('BOTTOMPADDING',(0,0),(-1,-1),0.8)]))
story.append(t)
story.append(Paragraph('CERTIFICATIONS AND TESTS', SEC))
for a, b in CERTS:
    story.append(Paragraph(f'<b>{a}:</b> {b}', BODY))

out = 'deliverables/resume-en/Hengji-Zhang-CV-Full-English.pdf'
SimpleDocTemplate(out, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                  topMargin=13*mm, bottomMargin=12*mm,
                  title='Hengji Zhang — Full CV (English)', author='Hengji Zhang').build(story)
pathlib.Path('/tmp/cv_full.json').write_text(json.dumps(dict(
    NAME_T=NAME_T, ROLE_T=ROLE_T, CONTACT=CONTACT, PROFILE=PROFILE, CURRENT=CURRENT, TIMELINE=TIMELINE,
    PAPER=PAPER, EDU=EDU, HONOURS=HONOURS, SKILLS=SKILLS, CERTS=CERTS), ensure_ascii=False, indent=1), encoding='utf-8')
print('pdf', pathlib.Path(out).stat().st_size)
