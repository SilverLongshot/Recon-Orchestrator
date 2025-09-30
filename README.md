# 🕵️‍♂️ Recon Orchestrator


A modular, CLI-based recon automation tool for bug bounty, CTF, and penetration testing workflows. It wraps passive recon, CSP analysis, and DOM surface scoring into a single command.


![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-CC--BY--NC%204.0-lightgrey)


---


## 📁 Folder Structure
```
recon_orchestrator/
├── recon_orchestrator.py # Main orchestrator CLI
├── passive_recon.py # JS/Forms/Wayback/DNS scanner
├── dom_classifier.py # Inline JS and event attribute scorer
├── csp_analyzer.py # CSP header evaluator
├── recon_data/ # Output summaries from scans
├── orchestrator_results/ # Master output + logs
├── final_submissions/Reportable/ # Place .html/.http files here for DOM/CSP scans
└── example/ # Sample inputs for testing
```


---


## 🚀 Usage
### Basic Recon:
```bash
python3 recon_orchestrator.py --target example_com
```


### With DOM and CSP Analysis:
```bash
python3 recon_orchestrator.py --target example_com --run-dom --run-csp
```


### Full with Nmap and Gobuster:
```bash
python3 recon_orchestrator.py --target example_com --with-nmap --with-gobuster --run-dom --run-csp
```


### 🧪 Test with Samples:
```bash
python3 dom_classifier.py --input-dir example
python3 csp_analyzer.py --input-dir example
```


---


## 📦 Installation
```bash
pip install -r requirements.txt
```


### Requirements
- Python 3.8+
- `requests`, `beautifulsoup4`
- `dnspython` (optional)
- ChromeDriver + `selenium` (for screenshot support)
- `nmap`, `gobuster` (optional but supported)


---


## 🔐 License
This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** License.


> You may use, share, and adapt the code **non-commercially**, with attribution.
> [Read the full license here](https://creativecommons.org/licenses/by-nc/4.0/)
