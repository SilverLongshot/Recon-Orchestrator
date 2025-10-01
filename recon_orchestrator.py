# recon_orchestrator.py

"""
High-level wrapper to automate recon, CSP analysis, and DOM scoring.
Supports test mode using example/ files without internet access.
Summarizes JSON output into .txt log files in orchestrator_results/.
"""

import os
import argparse
import subprocess
import datetime
import shutil
import json

RECON_DIR = "recon_data"
RESULT_DIR = "orchestrator_results"
os.makedirs(RECON_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Clean up old logs
for log_file in ["csp_log.txt", "dom_log.txt", "passive_recon_log.txt"]:
    full_path = os.path.join(RESULT_DIR, log_file)
    if os.path.exists(full_path):
        os.remove(full_path)

def run(cmd):
    print(f"\n[+] Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print("[stdout]\n" + result.stdout)
    if result.stderr:
        print("[stderr]\n" + result.stderr)

def summarize_dom():
    path = os.path.join(RECON_DIR, "dom_classification.json")
    out_path = os.path.join(RESULT_DIR, "dom_log.txt")
    if not os.path.exists(path):
        return
    with open(path) as f:
        data = json.load(f)
    lines = ["[DOM Risk Report]"]
    for file, info in data.items():
        lines.append(f"File: {file}")
        lines.append(f"Score: {info.get('score')}")
        for reason in info.get("reasons", []):
            lines.append(f"- {reason}")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

def summarize_csp():
    path = os.path.join(RECON_DIR, "csp_analysis.json")
    out_path = os.path.join(RESULT_DIR, "csp_log.txt")
    if not os.path.exists(path):
        return
    with open(path) as f:
        data = json.load(f)
    lines = ["[CSP Header Report]"]
    for file, result in data.items():
        lines.append(f"File: {file}")
        lines.append(f"Score: {result.get('score')}")
        lines.append(f"Policy: {result.get('policy')}")
        for flag in result.get("flags", []):
            lines.append(f"- {flag}")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Target domain (used for passive recon and file naming)")
    parser.add_argument("--run-csp", action="store_true", help="Run CSP header analysis")
    parser.add_argument("--run-dom", action="store_true", help="Run DOM classifier")
    parser.add_argument("--test-mode", action="store_true", help="Use example/ as input, skip network calls")
    args = parser.parse_args()

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary = {"target": args.target or "test", "timestamp": timestamp, "modules": []}

    if args.test_mode:
        print("[!] Test mode enabled: using example/ inputs only")
        if args.run_csp:
            run("python3 csp_analyzer.py --input-dir example")
            summary["modules"].append("csp_analyzer (example)")
            summarize_csp()
        if args.run_dom:
            run("python3 dom_classifier.py --input-dir example")
            summary["modules"].append("dom_classifier (example)")
            summarize_dom()
    else:
        if args.target:
            run(f"python3 passive_recon.py --target {args.target}")
            summary["modules"].append("passive_recon")
            # passive recon log handling can be added here

        if args.run_csp:
            run("python3 csp_analyzer.py")
            summary["modules"].append("csp_analyzer")
            summarize_csp()

        if args.run_dom:
            run("python3 dom_classifier.py")
            summary["modules"].append("dom_classifier")
            summarize_dom()

    # Save summary
    outfile = os.path.join(RESULT_DIR, f"summary__{args.target or 'test'}.json")
    with open(outfile, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[✓] Summary written to: {outfile}")

if __name__ == "__main__":
    main()
