#!/usr/bin/env python3
"""Create a finance task scaffold using the captured platform registry."""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"finance"/"skill_registry.json"
DOMAINS=ROOT/"finance"/"domain_catalog.json"
BATCH=ROOT/"finance"/"batch"/"selected_tasks.json"
SUBMITTED_REGISTRY=ROOT/"registry"/"submitted_skill_registry.json"

def load(path):
    with path.open(encoding="utf-8") as f: return json.load(f)

def create_case(case_code: str, batch_root: Path, registry_path=REGISTRY, domains_path=DOMAINS, batch_path=BATCH, submitted_registry_path=SUBMITTED_REGISTRY):
    registry=load(registry_path); domains=load(domains_path); batch=load(batch_path)
    selected={x["case_code"]:x for x in batch["selected_tasks"]}
    if case_code not in selected: raise ValueError(f"unknown case_code: {case_code}")
    task=selected[case_code]
    skill_rows={str(x["platform_task_id"]):x for x in registry["skills"]}
    domain_rows={str(x["platform_task_id"]):x for x in domains["professional_domains"]}
    sid=str(task["platform_task_id"])
    if sid not in skill_rows or sid not in domain_rows: raise ValueError(f"Skill/domain not registered: {sid}")
    skill=skill_rows[sid]; domain=domain_rows[sid]
    for field in ("second_level_skill","third_level_skill"):
        if skill.get(field)!=task.get(field) or domain.get(field)!=task.get(field):
            raise ValueError(f"platform mapping mismatch for {field}")
    labels=[x["third_level_skill"] for x in batch["selected_tasks"]]
    ids=[str(x["platform_task_id"]) for x in batch["selected_tasks"]]
    if len(labels)!=len(set(labels)) or len(ids)!=len(set(ids)):
        raise ValueError("duplicate third-level Skill or platform task ID in selected batch")
    # Cross-check the live project reservation ledger. The selected batch may
    # use only exact, already-reserved draft entries; other occupied Skills
    # cannot be silently reused or renamed.
    submitted=load(submitted_registry_path)
    entries=submitted.get("entries",[])
    by_id={str(x.get("platform_task_id")):x for x in entries}
    for selected_item in batch["selected_tasks"]:
        entry=by_id.get(str(selected_item["platform_task_id"]))
        if not entry:
            raise ValueError(f"platform task ID missing from submitted_skill_registry: {selected_item['platform_task_id']}")
        if entry.get("level3_skill")!=selected_item["third_level_skill"] or entry.get("l2_skill")!=selected_item["second_level_skill"]:
            raise ValueError(f"submitted Skill registry mismatch for {selected_item['platform_task_id']}")
        if entry.get("status") not in {"draft","carried_over_previous"}:
            raise ValueError(f"platform Skill is not reserved as draft: {selected_item['third_level_skill']} ({entry.get('status')})")
    occupied={}
    for entry in entries:
        if entry.get("status") in {"draft","submitted","carried_over_previous"}:
            label=entry.get("level3_skill")
            prior=occupied.get(label)
            if prior and prior!=str(entry.get("platform_task_id")):
                raise ValueError(f"duplicate occupied third-level Skill in project registry: {label}")
            occupied[label]=str(entry.get("platform_task_id"))
    root=batch_root/"cases"/case_code
    if root.exists(): raise FileExistsError(f"case directory already exists: {root}")
    dirs=["01_PUBLIC_DOUBAO/inputs","02_PRIVATE_EXPERT","03_OPERATIONS","04_EVIDENCE","05_PLATFORM_FIELDS","06_READINESS"]
    for d in dirs: (root/d).mkdir(parents=True,exist_ok=True)
    card=(f"# {case_code}\n\n- Industry: 金融\n- Platform task ID: {sid}\n- L2: {task['second_level_skill']}\n- L3: {task['third_level_skill']}\n- Professional domain: {domain['domain']}\n- Status: SCAFFOLD_ONLY\n\n## Business objects\n"+"\n".join(f"- {x}" for x in domain["business_objects"])+"\n\n## Genuine input classes\n"+"\n".join(f"- {x}" for x in domain["typical_inputs"])+"\n\n## Professional decisions\n"+"\n".join(f"- {x}" for x in domain["professional_decisions"])+"\n\n## Failure modes to test (derive from real evidence)\n"+"\n".join(f"- {x}" for x in domain["failure_modes"])+"\n\nNo real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.\n")
    (root/"CASE_CARD.md").write_text(card,encoding="utf-8")
    prompt=(f"# {task['third_level_skill']}\n\n## Role and real business context\n[Populate from the author's genuine work case; do not invent employer/client/events.]\n\n## Objective\n[One specific business work unit and downstream decision.]\n\n## Input scope\nOnly approved files in inputs/. Do not use private expert/reference materials.\n\n## Cutoff and conventions\n- Business as-of: [REQUIRED]\n- Timezone: [REQUIRED]\n- Currency/unit/precision: [REQUIRED]\n- Source precedence: [CITE AUTHORIZED POLICY]\n- Missing semantics: UNKNOWN / NOT_OBSERVED / NOT_PROVEN / NOT_RUN remain distinct.\n\n## Required output\n[Freeze exact filenames, schemas, primary keys, units, precision, enums and null semantics.]\n\n## Restrictions\nDo not invent missing evidence or policy parameters. Distinguish facts, calculations, assumptions and unresolved issues. Do not claim execution/approval not performed.\n")
    (root/"01_PUBLIC_DOUBAO"/"PROMPT.md").write_text(prompt,encoding="utf-8")
    (root/"01_PUBLIC_DOUBAO"/"INPUT_CONTRACT.md").write_text(
        "Only source-authorized, redacted, versioned materials may be placed in inputs/. Each material needs source_id, owner/publisher, canonical URL or path, capture time UTC, version, SHA-256, byte size, license/redistribution boundary, real/synthetic designation, authorization evidence ID and exact locator.\n\nCSV: UTF-8/UTF-8-SIG, stable headers, ISO-8601 timestamps, explicit timezone, units/currency and null semantics. No nested archives, password-protected files, irrelevant database dumps, duplicates or screenshots in place of structured data.\n\nPrivate Reference, Ideal Steps, platform Rubric, hidden tests and grader must never be placed in this folder.\n",encoding="utf-8")
    (root/"OUTPUT_CONTRACT.md").write_text(
        "Freeze each filename, format, schema version, grain, primary key, exact headers, enum, units, precision, timezone and null semantics before the model run. Every output row must trace to source material IDs and business keys. Totals must reconcile. Unknowns must remain explicit. Reopen and independently validate every generated artifact.\n\nExpected work products:\n"+"\n".join(f"- {x}" for x in domain["deliverables"])+"\n",encoding="utf-8")
    (root/"02_PRIVATE_EXPERT"/"IDEAL_STEPS.md").write_text(
        "Template only; replace with case-specific professional operations and evidence locators.\n\n1. Freeze cutoff, source versions, scope, units, timezone and permissions.\n2. Inspect all source materials; validate schema, row counts, keys, duplicates, nulls, coverage and lineage.\n3. Resolve evidence conflicts using only cited policy/source hierarchy; preserve unresolved conflicts.\n4. Perform the professional decisions defined for this Skill using exact source locators.\n5. Independently recalculate all critical figures; document equations, assumptions and tolerances.\n6. Test edge cases, missing evidence, reasonable alternatives and negative cases.\n7. Generate and reopen all deliverables; reconcile them against independent reference workpapers.\n8. State the downstream decision, limitations and actions not performed.\n",encoding="utf-8")
    (root/"02_PRIVATE_EXPERT"/"GOLDEN_RESPONSE.md").write_text(
        "NOT_READY: no genuine case materials or independently reconciled results supplied. Do not invent numerical results.\n\n## Conclusion\n[Populate from verified case evidence.]\n\n## Method and calculations\n[Equations, source hierarchy, assumptions, tolerances and sensitivity.]\n\n## Findings and evidence\n[Every conclusion maps to material ID and exact row/page/section.]\n\n## Decision, limitations and unresolved matters\n[Separate UNKNOWN, NOT_PROVEN and NOT_RUN.]\n",encoding="utf-8")
    platform_cols=["rubric_type","core_criterion","acceptance_standard","professional_judgment","evidence_source_and_location","numeric_tolerance","reasonable_alternative_or_boundary","gate_candidate","gate_reason"]
    with (root/"02_PRIVATE_EXPERT"/"PLATFORM_RUBRIC.csv").open("w",newline="",encoding="utf-8-sig") as f: csv.writer(f).writerow(platform_cols)
    with (root/"02_PRIVATE_EXPERT"/"INTERNAL_GRADER_20x5.csv").open("w",newline="",encoding="utf-8-sig") as f:
        csv.writer(f).writerow(["criterion_id","criterion","weight","machine_or_human","expected_evidence","test_method","tolerance","reference","alternative","negative_mutation","status"])
    with (root/"02_PRIVATE_EXPERT"/"HIDDEN_DIFFICULTY_MAP.csv").open("w",newline="",encoding="utf-8-sig") as f:
        csv.writer(f).writerow(["hidden_id","material_id","exact_locator","real_conflict_or_edge_case","critical_path_step","business_impact","platform_rubric_id","machine_check_id","correct_path","reasonable_alternative","negative_failure"])
    manifest={
      "schema_version":"financial-case-manifest/2.1","case_code":case_code,"industry":"金融",
      "platform_task_id":sid,"second_level_skill":task["second_level_skill"],"third_level_skill":task["third_level_skill"],
      "source_class":"PENDING","authorization_status":"PENDING","source_approval_ref":None,"author_profile":{"role":"PENDING","qualification_evidence":"PENDING"},
      "professional_context":{"business_process":"PENDING","product_or_instrument":"PENDING","business_date_or_period":"PENDING","decision_owner":"PENDING","decision_consequence":"PENDING","jurisdiction_or_not_applicable":"PENDING"},
      "policy_parameters":[],"materials":[],"materials_status":"PENDING","reference_status":"NOT_STARTED","alternative_status":"NOT_STARTED","negative_status":"NOT_STARTED",
      "hidden_difficulty_count":0,"rubric_status":"TEMPLATE_ONLY","grader_status":"NOT_STARTED","c20_status":"PENDING","platform_skill_verified":False,"platform_skill_verified_at":None,"platform_fields_status":"NOT_STARTED",
      "model_runs":[],"difficulty_evaluation":{"judge_score":None,"official_single_round_steps":None,"official_evidence":"PENDING"},
      "readiness_status":"SCAFFOLD_ONLY","platform_acceptance":{"status":"NOT_SUBMITTED","receipt":None}
    }
    (root/"03_OPERATIONS"/"CASE_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (root/"03_OPERATIONS"/"RUN_LOG.csv").write_text("run_id,role,model,mode,environment,reasoning,answer_url,feedback_url,start_at,end_at,duration_seconds,input_sha256,output_sha256,manual_intervention,status\n",encoding="utf-8")
    (root/"04_EVIDENCE"/"SOURCE_REGISTER.csv").write_text("source_id,canonical_url_or_path,publisher_owner,capture_timestamp_utc,version,sha256,byte_size,license,redistribution_boundary,real_or_synthetic,authorization_evidence_id,redaction_status,exact_locator,status\n",encoding="utf-8")
    (root/"04_EVIDENCE"/"C20_REVIEW.csv").write_text("reviewer_id,qualification,conflict_declaration,criterion_id,score,reason,evidence_locator,adjudication,status\n",encoding="utf-8")
    (root/"04_EVIDENCE"/"PLATFORM_SKILL_SNAPSHOT.csv").write_text("checked_at,task_id,industry,second_level_skill,third_level_skill,live_status,screenshot_or_receipt,checked_by,status\n",encoding="utf-8")
    (root/"04_EVIDENCE"/"MATERIAL_ACCEPTANCE.csv").write_text("material_id,filename,source_id,version,captured_at,sha256,byte_size,license_status,authorization_status,redaction_status,model_visibility,exact_locator,reviewer,decision,status\n",encoding="utf-8")
    (root/"04_EVIDENCE"/"MODEL_RUN_EVIDENCE.csv").write_text("run_id,run_role,status,model,mode,environment,reasoning,answer_url,feedback_url,raw_output_path,attachments,input_sha256,output_sha256,judge_score,official_single_round_steps,official_evidence,duration_seconds\n",encoding="utf-8")
    (root/"02_PRIVATE_EXPERT"/"ORACLE_CALIBRATION.md").write_text(
        "Reference: NOT_STARTED. Must be independently derived from accepted real case inputs.\nAlternative: NOT_STARTED. Must be a materially different but professionally valid solution.\nNegative: NOT_STARTED. Must target actual failure modes without unrelated formatting penalties.\nINVALID_SCHEMA means no score. NOT_RUN is neither PASS nor model failure.\n",encoding="utf-8")
    (root/"02_PRIVATE_EXPERT"/"GRADER_SPEC.md").write_text(
        "Evidence-based grader specification; not implemented for this case yet.\nThe grader must inspect actual public output artifacts, not self-reported assessment JSON. Strict schema preflight runs first. It must report expected value, observed value, evidence locator, unit/tolerance and failure reason. Mutation, property, permutation, valid-alternative and adversarial tests are required.\nInternal C01-C19 machine checks max 95 and C20 human review 5 are separate from the platform expert Rubric.\n",encoding="utf-8")
    (root/"03_OPERATIONS"/"CHANGE_LOG.md").write_text("Case scaffold initialized by deterministic finance batch generator. No real case data or business facts added.\n",encoding="utf-8")
    (root/"06_READINESS"/"FINAL_READINESS.md").write_text("SCAFFOLD_ONLY. G0-G10 are not passed. Do not submit until source authorization, material acceptance, public contract, hidden difficulty, independent oracle, grader, official Doubao run, current FDE 11.4 difficulty gate, C20 and platform readiness are verified.\n",encoding="utf-8")
    (root/"05_PLATFORM_FIELDS"/"PLATFORM_FIELDS.md").write_text(
        f"# Platform fields\n\n- 任务名称：{task['third_level_skill']} — [真实对象/期间]\n- 任务类型：[按平台实际选项]\n- Prompt：01_PUBLIC_DOUBAO/PROMPT.md\n- 输入附件：仅已授权的 01_PUBLIC_DOUBAO/inputs/\n- Rubric：02_PRIVATE_EXPERT/PLATFORM_RUBRIC.csv\n- 作答思路：02_PRIVATE_EXPERT/IDEAL_STEPS.md\n- 标准答案文本：02_PRIVATE_EXPERT/GOLDEN_RESPONSE.md\n- 标准答案附件：另行打包；不得混入输入附件。\n\n补充填写作者资质、能力选择、难度、回答评级、运行时长、豆包版本确认、回答链接和反馈链接。职业枚举必须从实时平台下拉读取。\n",encoding="utf-8")
    (root/"06_READINESS"/"G0_G10.md").write_text(
        "G0 version freeze and preserve old evidence.\nG1 real source, license, redistribution and authorization verified.\nG2 public prompt/output schema frozen; no answer leakage.\nG3 8-15 genuine evidence-derived critical-path difficulty items mapped to Rubric and checks.\nG4 independent Reference, materially valid Alternative, targeted Negative baselines.\nG5 strict Schema Preflight before evidence-based grader; mutation/property/permutation tests.\nG6 Doubao Work Task 2.1 Pro, cloud computer, high reasoning; retain raw output, answer URL, feedback URL, attachments and hashes.\nG7 CURRENT FDE 11.4: platform Judge <= 50 AND platform-published single-round model-call steps >= 50. Both required; duration is rating metadata only.\nG8 C20 independent qualified human review; unresolved remains PENDING.\nG9 live platform taxonomy, qualifications and submission fields checked.\nG10 separate public/private/operations/evidence archives; SHA-256, ZIP CRC and leakage scan.\n\nDo not use the older time-or-steps rule. Do not infer official steps from tool calls, files or dialogue turns.\n",encoding="utf-8")
    (root/"README_STATUS.md").write_text(
        f"# {case_code} status\n\nSCAFFOLD_ONLY — no genuine case materials, authorization, independent Reference, final Rubric, valid model run, C20 review, difficulty-gate result or platform acceptance has been established.\n",
        encoding="utf-8")
    import hashlib
    records=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in {"DELIVERY_MANIFEST.json","MANIFEST.sha256"}:
            data=p.read_bytes()
            records.append({"path":str(p.relative_to(root)),"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    (root/"DELIVERY_MANIFEST.json").write_text(json.dumps({"case_code":case_code,"platform_task_id":sid,"status":"SCAFFOLD_ONLY","file_count":len(records),"files":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name!="MANIFEST.sha256":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}")
    (root/"MANIFEST.sha256").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return root

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case-code",required=True); ap.add_argument("--batch-root",default="work/financial-eight")
    args=ap.parse_args()
    try:
        root=create_case(args.case_code,Path(args.batch_root))
        print(f"SCAFFOLD_CREATED {root}")
        return 0
    except Exception as e:
        print(f"BLOCKED: {e}",file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
