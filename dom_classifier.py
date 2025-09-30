# dom_classifier.py (updated)

import os
import json
import argparse
from bs4 import BeautifulSoup

DEFAULT_INPUT_DIR = "final_submissions/Reportable"
RECON_DATA_DIR = "recon_data"
os.makedirs(RECON_DATA_DIR, exist_ok=True)

def classify_html(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    score = 0
    reasons = []

    if soup.find_all("script"):
        score += 2
        reasons.append("has <script>")

    for tag in soup.find_all(True):
        for attr in tag.attrs:
            if attr.lower().startswith("on"):
                score += 2
                reasons.append(f"inline event: {attr}")
        if tag.name.lower() in ["iframe", "object", "embed"]:
            score += 1
            reasons.append(f"dangerous tag: {tag.name}")

    return score, reasons

def main():
    parser = argparse.ArgumentParser(description="DOM Classifier")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="Directory with .html files to scan")
    args = parser.parse_args()

    summary = {}
    details = {}

    html_files = [f for f in os.listdir(args.input_dir) if f.endswith(".html")]
    print(f"[*] Scanning {len(html_files)} HTML files in {args.input_dir}...")

    for filename in html_files:
        path = os.path.join(args.input_dir, filename)
        score, reasons = classify_html(path)
        details[filename] = {"score": score, "reasons": reasons}
        summary[filename] = score

    with open(os.path.join(RECON_DATA_DIR, "dom_classification.json"), "w") as f:
        json.dump(details, f, indent=2)
    with open(os.path.join(RECON_DATA_DIR, "dom_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[✓] DOM classification complete. Scanned {len(html_files)} files.")
    print("[✓] Results saved to recon_data/dom_classification.json and dom_summary.json")

if __name__ == "__main__":
    main()