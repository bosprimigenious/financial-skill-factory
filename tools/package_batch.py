#!/usr/bin/env python3
"""Package financial task cases with fail-closed readiness rules."""
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/"finance"/"batch"/"selected_tasks.json"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    with p.open(encoding="utf-8") as f: return json.load(f)
def package(batch_root:Path,output:Path,mode:str):
    batch=load(BATCH); cases=batch["selected_tasks"]
    labels=[x["third_level_skill"] for x in cases]
    ids=[x["platform_task_id"] for x in cases]
    if len(labels)!=len(set(labels)) or len(ids)!=len(set(ids)):
        raise ValueError("duplicate third-level Skill or task ID in selected batch")
    # Release packaging must agree with the project's authoritative Skill reservation ledger.
    submitted=load(ROOT/"registry"/"submitted_skill_registry.json")
    entries={str(x.get("platform_task_id")):x for x in submitted.get("entries",[])}
    for item in cases:
        entry=entries.get(str(item["platform_task_id"]))
        if not entry:
            raise ValueError(f"platform task ID missing from submitted_skill_registry: {item['platform_task_id']}")
        if entry.get("l2_skill")!=item["second_level_skill"] or entry.get("level3_skill")!=item["third_level_skill"]:
            raise ValueError(f"submitted Skill registry mismatch for {item['case_code']}")
        if entry.get("status") not in {"draft","carried_over_previous"}:
            raise ValueError(f"Skill reservation is not active for {item['case_code']}: {entry.get('status')}")
    output.mkdir(parents=True,exist_ok=True)
    case_zips=[]
    for item in cases:
        case_root=batch_root/"cases"/item["case_code"]
        if not case_root.is_dir(): raise ValueError(f"missing case directory: {case_root}")
        manifest_path=case_root/"03_OPERATIONS"/"CASE_MANIFEST.json"
        if not manifest_path.is_file(): raise ValueError(f"missing manifest: {manifest_path}")
        manifest=load(manifest_path)
        if str(manifest.get("platform_task_id"))!=str(item["platform_task_id"]):
            raise ValueError(f"task ID mismatch in {item['case_code']}")
        if manifest.get("third_level_skill")!=item["third_level_skill"]:
            raise ValueError(f"third-level Skill mismatch in {item['case_code']}")
        if mode=="release":
            if manifest.get("readiness_status")!="AUTHOR_QA_PASS":
                raise ValueError(f"{item['case_code']} not AUTHOR_QA_PASS")
            if manifest.get("platform_skill_verified") is not True or not manifest.get("platform_skill_verified_at"):
                raise ValueError(f"{item['case_code']} lacks live platform Skill verification evidence")
            if manifest.get("platform_fields_status")!="VERIFIED":
                raise ValueError(f"{item['case_code']} platform fields are not verified")
            author=manifest.get("author_profile") or {}
            if not author.get("role") or author.get("role")=="PENDING" or not author.get("qualification_evidence") or author.get("qualification_evidence")=="PENDING":
                raise ValueError(f"{item['case_code']} lacks author role/qualification evidence")
            context=manifest.get("professional_context") or {}
            if not context or any(not v or v=="PENDING" for v in context.values()):
                raise ValueError(f"{item['case_code']} lacks complete professional business context")
            real_work_ok = manifest.get("source_class")=="REAL_WORK" and manifest.get("authorization_status")=="AUTHORIZED"
            public_scenario_ok = manifest.get("source_class")=="PUBLIC_DATA_SCENARIO" and manifest.get("authorization_status")=="PROJECT_APPROVED" and bool(manifest.get("source_approval_ref"))
            if not (real_work_ok or public_scenario_ok):
                raise ValueError(f"{item['case_code']} lacks authorized real-work source or explicit public-scenario approval")
            if manifest.get("reference_status")!="VERIFIED" or manifest.get("grader_status")!="VERIFIED":
                raise ValueError(f"{item['case_code']} lacks verified Reference/Grader")
            if manifest.get("rubric_status")!="VERIFIED" or manifest.get("materials_status")!="ACCEPTED":
                raise ValueError(f"{item['case_code']} lacks accepted materials or verified platform Rubric")
            if int(manifest.get("hidden_difficulty_count",0))<8:
                raise ValueError(f"{item['case_code']} has fewer than 8 mapped difficulty items")
            if manifest.get("c20_status")!="CALIBRATED":
                raise ValueError(f"{item['case_code']} lacks completed C20 expert calibration")
            runs=manifest.get("model_runs") or []
            official=[x for x in runs if x.get("run_role")=="OFFICIAL_EVALUATION" and x.get("status")=="COMPLETED"]
            if not official:
                raise ValueError(f"{item['case_code']} lacks a completed official Doubao run")
            if not any(x.get("model")=="DOUBAO_2_1_PRO" and x.get("mode")=="WORK_TASK" and x.get("environment")=="CLOUD_COMPUTER" and x.get("reasoning")=="HIGH" and x.get("answer_url") and x.get("feedback_url") and x.get("raw_output_path") for x in official):
                raise ValueError(f"{item['case_code']} lacks compliant Doubao 2.1 Pro run evidence")
            gate=manifest.get("difficulty_evaluation") or {}
            if gate.get("judge_score") is None or float(gate["judge_score"])>50:
                raise ValueError(f"{item['case_code']} does not meet Judge <= 50")
            if gate.get("official_single_round_steps") is None or int(gate["official_single_round_steps"])<50 or not gate.get("official_evidence"):
                raise ValueError(f"{item['case_code']} does not meet official single-round steps >= 50")
            if manifest.get("readiness_status")!="AUTHOR_QA_PASS":
                raise ValueError(f"{item['case_code']} not AUTHOR_QA_PASS")
        suffix="SCAFFOLD" if mode=="scaffold" else "AUTHOR"
        zpath=output/f"{item['case_code']}_{suffix}.zip"
        with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
            for p in sorted(case_root.rglob("*")):
                if p.is_file(): z.write(p,f"{item['case_code']}/{p.relative_to(case_root).as_posix()}")
        with zipfile.ZipFile(zpath) as z:
            bad=z.testzip()
            if bad: raise ValueError(f"CRC failure {zpath}: {bad}")
        case_zips.append(zpath)
    master=output/f"FINANCIAL_EIGHT_{mode.upper()}_MASTER.zip"
    with zipfile.ZipFile(master,"w",zipfile.ZIP_DEFLATED) as z:
        for p in case_zips: z.write(p,f"INDIVIDUAL_PACKAGES/{p.name}")
        receipts=[{"path":p.name,"size_bytes":p.stat().st_size,"sha256":sha(p)} for p in case_zips]
        z.writestr("BATCH_MANIFEST.json",json.dumps({"batch_id":batch["batch_id"],"mode":mode,"status":"SCAFFOLD_ONLY" if mode=="scaffold" else "AUTHOR_PACKAGE","packages":receipts},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(master) as z:
        bad=z.testzip()
        if bad: raise ValueError(f"master CRC failure: {bad}")
    return case_zips,master

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--batch-root",default="work/financial-eight"); ap.add_argument("--output",default="dist/financial-eight")
    ap.add_argument("--mode",choices=("scaffold","release"),default="scaffold")
    a=ap.parse_args()
    try:
        cases,master=package(Path(a.batch_root),Path(a.output),a.mode)
        print(f"PACKAGED_CASES={len(cases)}")
        print(f"MASTER={master}")
        print("STATUS=SCAFFOLD_ONLY" if a.mode=="scaffold" else "STATUS=AUTHOR_PACKAGE")
        return 0
    except Exception as e:
        print(f"BLOCKED: {e}",file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
