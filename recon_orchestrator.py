# recon_orchestrator.py - Full Production-Ready Recon Wrapper

import argparse
import subprocess
import os
import json
from datetime import datetime

TOOLS = {
    "passive_recon": "passive_recon.py",
    "csp_analyzer": "csp_analyzer.py",
    "dom_classifier": "dom_classifier.py"
}

OUTPUT_DIR = "orchestrator_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_command(cmd, label=None):
    print(f"\n[+] Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print("[stdout]\n" + result.stdout)
        if result.stderr:
            print("[stderr]\n" + result.stderr)
        if label:
            with open(os.path.join(OUTPUT_DIR, f"{label}_log.txt"), "w") as f:
                f.write(result.stdout + "\n" + result.stderr)
    except Exception as e:
        print(f"[!] Error running {cmd[0]}: {e}")

def load_json_if_exists(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def summarize_recon(target):
    recon_file = os.path.join("passive-recon-results", f"recon__{target}.json")
    csp_summary = load_json_if_exists("recon_data/csp_summary.json")
    dom_summary = load_json_if_exists("recon_data/dom_summary.json")

    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target": target,
        "csp_summary": csp_summary,
        "dom_summary": dom_summary
    }

    with open(os.path.join(OUTPUT_DIR, f"summary__{target}.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n[✓] Summary written to:", os.path.join(OUTPUT_DIR, f"summary__{target}.json"))

def main():
    parser = argparse.ArgumentParser(description="OWX Recon Orchestrator")
    parser.add_argument("--target", required=True, help="Target key or domain")
    parser.add_argument("--with-nmap", action="store_true", help="Run nmap against resolved IP")
    parser.add_argument("--with-gobuster", action="store_true", help="Run gobuster if target is a domain")
    parser.add_argument("--run-csp", action="store_true", help="Run CSP analysis")
    parser.add_argument("--run-dom", action="store_true", help="Run DOM classification")
    args = parser.parse_args()

    # Step 1: Passive Recon
    run_command(["python3", TOOLS["passive_recon"], "--target", args.target], label="passive_recon")

    # Step 2: Optional Nmap
    if args.with_nmap:
        run_command(["nmap", "-sV", "-Pn", args.target], label="nmap")

    # Step 3: Optional Gobuster (if domain)
    if args.with_gobuster and not args.target.replace("_", ".").isdigit():
        gobuster_cmd = [
            "gobuster", "dir",
            "-u", f"https://{args.target.replace('_', '.')}",
            "-w", "/usr/share/wordlists/dirb/common.txt",
            "-t", "20"
        ]
        run_command(gobuster_cmd, label="gobuster")

    # Step 4: CSP Analyzer
    if args.run_csp:
        run_command(["python3", TOOLS["csp_analyzer"]], label="csp")

    # Step 5: DOM Classifier
    if args.run_dom:
        run_command(["python3", TOOLS["dom_classifier"]], label="dom")

    # Final summary
    summarize_recon(args.target)

if __name__ == "__main__":
    main()
