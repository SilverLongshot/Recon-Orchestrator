# passive_recon.py

import os, sys, json, time, argparse, datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from subprocess import Popen

try:
    import dns.resolver
    HAS_DNS = True
except Exception:
    HAS_DNS = False

OUT_DIR_DEFAULT = "passive-recon-results"
USER_AGENT = "OWX-Passive/1.0 (+https://example.com)"
TIMEOUT = 10

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def fetch(session, url, allow_redirects=True):
    try:
        return session.get(url, timeout=TIMEOUT, allow_redirects=allow_redirects, verify=True)
    except Exception:
        return None

def parse_links(html_text, base):
    soup = BeautifulSoup(html_text, "html.parser")
    js = set(); links=set(); forms=[]
    for s in soup.find_all("script"):
        src = s.get("src")
        if src: js.add(urljoin(base, src))
    for a in soup.find_all("a"):
        href = a.get("href")
        if href: links.add(urljoin(base, href))
    for ifr in soup.find_all("iframe"):
        src = ifr.get("src") or ifr.get("srcdoc")
        if src: links.add(urljoin(base, src))
    for l in soup.find_all("link"):
        href = l.get("href")
        if href:
            links.add(urljoin(base, href))
            if href.endswith(".js"): js.add(urljoin(base, href))
    for form in soup.find_all("form"):
        action = urljoin(base, form.get("action") or "")
        method = (form.get("method") or "GET").upper()
        inputs=[]
        for inp in form.find_all(['input','textarea','select']):
            inputs.append({"name": inp.get("name"), "type": inp.get("type")})
        forms.append({"action": action, "method": method, "inputs": inputs})
    return list(js), list(links), forms

def query_wayback(domain):
    try:
        api = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit=200"
        r = requests.get(api, timeout=TIMEOUT)
        if r.status_code==200:
            data = r.json()
            return list({row[2] for row in data[1:] if len(row)>=3})
    except Exception:
        pass
    return []

def dns_records(host):
    if not HAS_DNS: return {}
    recs={}
    for rtype in ("A","AAAA","MX","NS","TXT"):
        try:
            answers = dns.resolver.resolve(host, rtype, lifetime=5)
            recs[rtype] = [str(a) for a in answers]
        except Exception:
            recs[rtype] = []
    return recs

def save_outputs(outdir, key, payload):
    ensure_dir(outdir)
    fn = os.path.join(outdir, f"recon__{key}.json")
    txt = os.path.join(outdir, f"recon__{key}.txt")
    jsfile = os.path.join(outdir, f"{key}_jsfiles.txt")
    with open(fn,'w') as f: json.dump(payload,f,indent=2)
    with open(txt,'w') as f: f.write(json.dumps(payload,indent=2))
    with open(jsfile,'w') as f:
        for j in payload.get('js_files',[]): f.write(j+"\n")
    print("[✓] Done. Saved:", fn)
    return fn

def build_session(args):
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    if args.cookie:
        s.headers.update({"Cookie": args.cookie})
    if args.cookie_file:
        if os.path.exists(args.cookie_file):
            with open(args.cookie_file,'r') as f:
                s.headers.update({"Cookie": f.read().strip()})
    if args.auth_bearer:
        s.headers.update({"Authorization": f"Bearer {args.auth_bearer}"})
    if args.auth_basic:
        user, pwd = args.auth_basic.split(':',1)
        s.auth = (user, pwd)
    return s

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--target', help='target key or domain (lightspark_com or lightspark.com)')
    p.add_argument('--url', help='explicit base URL')
    p.add_argument('--outdir', default=OUT_DIR_DEFAULT)
    p.add_argument('--no-wayback', action='store_true')
    p.add_argument('--no-dns', action='store_true')
    p.add_argument('--cookie', help='cookie header string')
    p.add_argument('--cookie-file', help='file with cookie header string')
    p.add_argument('--auth-bearer', help='Bearer token for Authorization header')
    p.add_argument('--auth-basic', help='basic auth username:password for session')
    p.add_argument('--run-csp', action='store_true')
    p.add_argument('--run-dom', action='store_true')
    args = p.parse_args()

    if not args.target and not args.url:
        p.print_help(); sys.exit(1)

    base = args.url if args.url else ("https://" + (args.target.replace("_", ".") if "." not in args.target else args.target))
    parsed = urlparse(base)
    hostname = parsed.hostname
    key = args.target if args.target else hostname.replace('.', '_')

    session = build_session(args)
    payload = {"domain": key, "base_url": base, "hostname": hostname, "timestamp": datetime.datetime.utcnow().isoformat()+"Z", "js_files": [], "links": [], "forms": [], "headers": {}, "wayback_urls": [], "dns": {}}

    print("[*] Fetching", base)
    r = session.get(base, timeout=TIMEOUT, allow_redirects=True)
    if r:
        payload['status_code'] = r.status_code
        payload['headers'] = dict(r.headers)
        js, links, forms = parse_links(r.text, base)
        payload['js_files'] = js
        payload['links'] = links
        payload['forms'] = forms
    else:
        print("[!] Failed to fetch base")
        sys.exit(1)

    if not args.no_wayback:
        payload['wayback_urls'] = query_wayback(hostname)
    if not args.no_dns:
        payload['dns'] = dns_records(hostname)

    outfn = save_outputs(args.outdir, key, payload)

    if args.run_csp:
        try:
            print("[*] Running csp_analyzer.py on final_submissions/Reportable")
            Popen([sys.executable, "csp_analyzer.py", "--input-dir", "final_submissions/Reportable"])
        except Exception as e:
            print("[!] Failed to start csp_analyzer:", e)

    if args.run_dom:
        try:
            print("[*] Running dom_classifier.py")
            Popen([sys.executable, "dom_classifier.py", "--input-dir", "final_submissions/Reportable"])
        except Exception as e:
            print("[!] Failed to start dom_classifier:", e)

    print(f"[✓] Recon complete for: {key}")
    sys.exit(0)

if __name__ == "__main__":
    main()
