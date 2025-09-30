# csp_analyzer.py (public-safe version)

"""
Scans .http response files for Content-Security-Policy headers
and evaluates their strictness. Outputs a summary of findings.
"""

import os
import json
import argparse

DEFAULT_INPUT_DIR = "final_submissions/Reportable"
OUTPUT_DIR = "recon_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEYWORDS = [
    "unsafe-inline", "unsafe-eval", "data:", "blob:", "*",
    "strict-dynamic", "nonce-", "sha256-"
]

WEAK_DIRECTIVES = ["script-src", "default-src", "object-src"]

def extract_headers(path):
    try:
        with open(path, "r") as f:
            lines = f.readlines()
            headers = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
            return headers
    except Exception:
        return {}

def analyze_csp(csp):
    score = 0
    flags = []

    for keyword in KEYWORDS:
        if keyword in csp:
            score += 1
            flags.append(keyword)

    return score, flags

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="Folder of .http files")
    args = parser.parse_args()

    results = {}
    summary = {}
    files = [f for f in os.listdir(args.input_dir) if f.endswith(".http")]
    print(f"[*] Scanning {len(files)} .http files for CSP headers...")

    for filename in files:
        path = os.path.join(args.input_dir, filename)
        headers = extract_headers(path)
        csp = headers.get("content-security-policy")
        if csp:
            score, flags = analyze_csp(csp)
            results[filename] = {"score": score, "flags": flags, "policy": csp}
            summary[filename] = score

    with open(os.path.join(OUTPUT_DIR, "csp_analysis.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "csp_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[✓] CSP analysis complete. {len(results)} headers found.")
    print("[✓] Output saved to recon_data/")

if __name__ == "__main__":
    main()
