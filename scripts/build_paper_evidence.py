"""Build the final paper evidence bundle from persisted, source-native artifacts."""
from __future__ import annotations
import csv, hashlib, json, sqlite3, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments/jailbreakbench-validation/results.json"
SOURCE_MANIFEST = ROOT / "data/external/jailbreakbench_judge_comparison_b2b462fd.manifest.json"
OUT = ROOT / "artifacts/paper_evidence"

def kappa(pairs):
    n=len(pairs); observed=sum(p==y for p,y in pairs)/n
    pp=[sum(p==v for p,_ in pairs)/n for v in (0,1)]; py=[sum(y==v for _,y in pairs)/n for v in (0,1)]
    expected=sum(a*b for a,b in zip(pp,py)); return None if expected==1 else (observed-expected)/(1-expected)

def write_csv(name, rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def svg(path, title, body):
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="600" viewBox="0 0 1200 600"><style>text{{font-family:Arial,sans-serif;fill:#17352a}}.t{{font-size:28px;font-weight:bold}}.s{{font-size:18px}}.b{{fill:#eef6f0;stroke:#42745a;stroke-width:2}}.r{{fill:#fff2ed;stroke:#a64c35;stroke-width:2}}</style><text x="60" y="55" class="t">{title}</text>{body}</svg>',encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result=json.loads(RESULTS.read_text(encoding="utf-8")); manifest=json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    digest=hashlib.sha256(Path(result["source"]["path"]).read_bytes()).hexdigest()
    if digest!=result["source"]["sha256"] or digest!=manifest["sha256"]: raise SystemExit("source checksum mismatch")
    records=result["records"]; pairs=[(r["prediction"],r["human_majority"]) for r in records if r["prediction"] is not None]
    confusion={f"pred_{p}_label_{y}":sum(a==p and b==y for a,b in pairs) for p in (0,1) for y in (0,1)}
    accuracy=sum(a==b for a,b in pairs)/len(pairs); recomputed_kappa=kappa(pairs); coverage=len(pairs)/len(records)
    for value, expected in ((coverage,result["coverage"]),(accuracy,result["agreement"]["accuracy"]),(recomputed_kappa,result["agreement"]["cohen_kappa"])):
        if abs(value-expected)>1e-12: raise SystemExit("persisted calibration result does not recompute")
    connection=sqlite3.connect(ROOT/"securellmbench.db")
    counts={name:connection.execute(f"select count(*) from {name}").fetchone()[0] for name in ("benchmark_runs","evaluation_results","layer1_results","layer2_results","scientific_records")}
    families=[{"family":a,"status":b,"count":c} for a,b,c in connection.execute("select family,status,count(*) from scientific_records group by family,status order by family,status")]
    components=[
      {"component":"Dataset ingestion","unit_of_analysis":"dataset record","output":"validated record and version hash","validation_status":"engineering implementation"},
      {"component":"Benchmark execution","unit_of_analysis":"evaluation","output":"response, finish reason, latency","validation_status":"engineering implementation"},
      {"component":"Layer 1","unit_of_analysis":"evaluation","output":"detector-native evidence","validation_status":"engineering-only; not ground truth"},
      {"component":"Layer 2","unit_of_analysis":"evaluation × dimension","output":"structured judge measurement","validation_status":"uncalibrated; not outcome label"},
      {"component":"BSDA","unit_of_analysis":"matched prompt/response set","output":"four-component profile","validation_status":"exploratory; no composite"},
      {"component":"Recovery Capability","unit_of_analysis":"behavioral trajectory","output":"RC trajectory/AUC when applicable","validation_status":"uncalibrated without compatible artifact"},
      {"component":"SAEA","unit_of_analysis":"ordered attack sequence","output":"sequence-effect vector","validation_status":"exploratory; not attack success"},
      {"component":"DRAA","unit_of_analysis":"evaluation","output":"evidence profile","validation_status":"uncalibrated; risk scalar null"},
      {"component":"PRI","unit_of_analysis":"benchmark run","output":"profile","validation_status":"uncalibrated; scalar null"},
      {"component":"ML prediction","unit_of_analysis":"labelled outcome","output":"blocked readiness record","validation_status":"blocked without independent labels"},
      {"component":"Attack success rate","unit_of_analysis":"labelled attack evaluation","output":"ASR","validation_status":"blocked without approved outcome protocol"},
    ]
    table2=[{"source_n":len(records),"usable_n":len(pairs),"coverage":coverage,"raw_agreement":accuracy,"cohen_kappa":recomputed_kappa,**confusion,"source_revision":manifest["dataset_revision"],"source_sha256":digest,"status":"empirical exploratory calibration; current judge not validated"}]
    table3=[{"models":"qwen3.5:2b; gemma3:4b","benchmark_runs":counts["benchmark_runs"],"evaluations":counts["evaluation_results"],"layer1_records":counts["layer1_results"],"layer2_records":counts["layer2_results"],"scientific_records":counts["scientific_records"],"families_and_statuses":"; ".join(f"{x['family']}:{x['status']}={x['count']}" for x in families),"status":"local engineering demonstration; not scientific model comparison"}]
    write_csv("table1_components.csv",components); write_csv("table2_jbb_calibration.csv",table2); write_csv("table3_local_engineering.csv",table3)
    (OUT/"calibration_verification.json").write_text(json.dumps({"source_manifest":manifest,"recomputed":{"source_n":len(records),"usable_n":len(pairs),"coverage":coverage,"confusion_matrix":confusion,"raw_agreement":accuracy,"cohen_kappa":recomputed_kappa},"status":"verified from persisted results.json"},indent=2),encoding="utf-8")
    (OUT/"table_data.json").write_text(json.dumps({"table1":components,"table2":table2,"table3":table3},indent=2),encoding="utf-8")
    svg(OUT/"figure1_architecture.svg","SecureLLMBench evidence pipeline",'<rect x="60" y="150" width="190" height="100" class="b"/><text x="85" y="205" class="s">Versioned dataset</text><rect x="330" y="150" width="190" height="100" class="b"/><text x="355" y="205" class="s">Model execution</text><rect x="600" y="150" width="190" height="100" class="b"/><text x="625" y="205" class="s">Layer 1 / Layer 2</text><rect x="870" y="150" width="190" height="100" class="b"/><text x="895" y="205" class="s">Persisted evidence</text><path d="M250 200H330M520 200H600M790 200H870" stroke="#42745a" stroke-width="4"/><text x="60" y="340" class="s">Outputs retain provenance, applicability, and scientific-status fields.</text>')
    svg(OUT/"figure2_judge_human_confusion.svg","JailbreakBench judge vs human-majority labels",f'<text x="350" y="130" class="s">Human label 0</text><text x="650" y="130" class="s">Human label 1</text><text x="70" y="260" class="s">Predicted 0</text><text x="70" y="410" class="s">Predicted 1</text><rect x="300" y="170" width="220" height="110" class="b"/><text x="390" y="235" class="t">{confusion["pred_0_label_0"]}</text><rect x="600" y="170" width="220" height="110" class="r"/><text x="690" y="235" class="t">{confusion["pred_0_label_1"]}</text><rect x="300" y="320" width="220" height="110" class="r"/><text x="385" y="385" class="t">{confusion["pred_1_label_0"]}</text><rect x="600" y="320" width="220" height="110" class="b"/><text x="685" y="385" class="t">{confusion["pred_1_label_1"]}</text><text x="60" y="520" class="s">Usable N={len(pairs)}; coverage={coverage:.3%}; raw agreement={accuracy:.3%}; Cohen’s κ={recomputed_kappa:.3f}</text>')
    svg(OUT/"figure3_readiness_gates.svg","Scientific-readiness gates",'<rect x="60" y="140" width="220" height="100" class="b"/><text x="83" y="195" class="s">Engineering evidence</text><rect x="360" y="140" width="220" height="100" class="r"/><text x="382" y="185" class="s">Independent labels</text><text x="420" y="212" class="s">REQUIRED</text><rect x="660" y="140" width="220" height="100" class="r"/><text x="680" y="185" class="s">Calibration / review</text><text x="725" y="212" class="s">REQUIRED</text><rect x="960" y="140" width="180" height="100" class="r"/><text x="990" y="195" class="s">Scientific claim</text><path d="M280 190H360M580 190H660M880 190H960" stroke="#a64c35" stroke-width="4"/><text x="60" y="330" class="s">Blocked: ASR without outcome protocol; ML without labels; calibrated risk without calibration; rankings from pilot evidence.</text>')
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(); status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True).strip() or "clean"
    manifest_text=f'''# Paper Evidence Manifest\n\n| Claim/result | Exact value | Source artifact | Producing script | Dataset/configuration | N | Status |\n|---|---:|---|---|---|---:|---|\n| JailbreakBench source records | {len(records)} | `results.json`; source manifest | `validate_jailbreakbench_judge.py` | revision `{manifest["dataset_revision"]}`, SHA-256 `{digest}` | {len(records)} | empirical, exploratory calibration |\n| Usable judge records | {len(pairs)} | `results.json` | `build_paper_evidence.py` recomputation | local `{result["protocol"]["score_dimension"]}` judge, threshold `{result["protocol"]["threshold"]}` | {len(records)} | empirical, exploratory calibration |\n| Coverage | {coverage:.3%} | `calibration_verification.json` | `build_paper_evidence.py` | same as above | {len(records)} | empirical, exploratory calibration |\n| Raw agreement | {accuracy:.3%} | `calibration_verification.json` | `build_paper_evidence.py` | source `human_majority`; fixed predeclared rule | {len(pairs)} | empirical, exploratory calibration |\n| Cohen’s kappa | {recomputed_kappa:.3f} | `calibration_verification.json` | `build_paper_evidence.py` | same as above | {len(pairs)} | empirical, exploratory calibration; insufficient to replace labels |\n| Local engineering demonstration | {counts["benchmark_runs"]} runs; {counts["evaluation_results"]} evaluations; {counts["layer1_results"]} Layer 1 records | SQLite `securellmbench.db` | `run_local_benchmark.py` | repository 3-case example; Qwen/Gemma configurations | {counts["evaluation_results"]} | engineering-only; not comparison |\n| Layer 2 dashboard availability | {counts["layer2_results"]} persisted records | SQLite `securellmbench.db` | n/a | dashboard database | {counts["layer2_results"]} | absent |\n\nConfusion matrix: `pred_0_label_0={confusion["pred_0_label_0"]}`, `pred_0_label_1={confusion["pred_0_label_1"]}`, `pred_1_label_0={confusion["pred_1_label_0"]}`, `pred_1_label_1={confusion["pred_1_label_1"]}`.\n\nClaims not supported: calibrated human-equivalent judge, ASR, statistical significance, model ranking, novelty, general safety claims, ML prediction utility, DRAA scalar risk, or PRI scalar score.\n'''
    (ROOT/"docs/PAPER_EVIDENCE_MANIFEST.md").write_text(manifest_text,encoding="utf-8")
    freeze=f'''# Paper Freeze Report\n\n- Freeze commit: `{commit}`\n- Working-tree status at generation:\n```text\n{status}\n```\n- Calibration verification: source N={len(records)}, usable N={len(pairs)}, coverage={coverage:.3%}, raw agreement={accuracy:.3%}, Cohen’s κ={recomputed_kappa:.3f}.\n- Confusion matrix: {confusion}.\n- Reproduce evidence bundle: `F:\\SecureLLM\\.venv\\Scripts\\python.exe scripts\\build_paper_evidence.py`\n- Reproduce calibration: `F:\\SecureLLM\\.venv\\Scripts\\python.exe scripts\\verify_persisted_judge_calibration.py`\n- Reproduce paper trace: `F:\\SecureLLM\\.venv\\Scripts\\python.exe experiments\\paper_2026\\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b --output experiments\\paper_2026\\outputs\\local_trace.json`\n- Regression: `F:\\SecureLLM\\.venv\\Scripts\\python.exe -m pytest -q`; `F:\\SecureLLM\\.venv\\Scripts\\python.exe scripts\\api_smoke.py`; frontend `npm test`, `npm run typecheck`, `npm run build`.\n\n## Limitations and unsupported claims\n\nThe Gemma judge under this fixed rule is not sufficiently validated to replace independent human labels. The three-case local pilot is engineering-only. No ASR, significance, novelty, model ranking, calibrated risk, calibrated recovery probability, or ML predictive claim is supported.\n'''
    (ROOT/"docs/PAPER_FREEZE_REPORT.md").write_text(freeze,encoding="utf-8")
    print(json.dumps({"output":str(OUT),"source_n":len(records),"usable_n":len(pairs),"coverage":coverage,"accuracy":accuracy,"kappa":recomputed_kappa,"confusion":confusion}))
if __name__=="__main__": main()
