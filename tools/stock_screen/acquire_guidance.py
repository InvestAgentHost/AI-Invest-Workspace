"""Cache annual earnings exhibits near US 10-K filings for guidance review."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


def acquire(config, root):
    old = root / config['baseline_source_dir']
    source = root / config['source_dir'] / 'guidance'
    source.mkdir(parents=True, exist_ok=True)
    eligible = json.loads((root / config['baseline_dir'] / 'eligible.json').read_text())
    jobs = []
    for issuer in eligible:
        ticker = issuer['ticker']
        submissions = json.loads((old / f'{ticker}-submissions.json').read_text())
        recent = submissions['filings']['recent']
        annuals = [i for i, form in enumerate(recent['form']) if form == '10-K'
                   and recent['filingDate'][i] <= config['as_of']][:6]
        for i in annuals:
            annual_day = date.fromisoformat(recent['filingDate'][i])
            year = int(recent['reportDate'][i][:4])
            for j, form in enumerate(recent['form']):
                if (form == '8-K' and '2.02' in recent.get('items', [''] * len(recent['form']))[j]
                    and abs((annual_day - date.fromisoformat(recent['filingDate'][j])).days) <= 25):
                    url = f"https://www.sec.gov/Archives/edgar/data/{int(submissions['cik'])}/{recent['accessionNumber'][j].replace('-','')}/{recent['primaryDocument'][j]}"
                    jobs.append((ticker, year, recent['filingDate'][j], url))

    def fetch(job):
        ticker, year, day, url = job
        key = f'{ticker}-FY{year}-{day}'
        def get(address, path):
            if not path.exists():
                response = requests.get(address, timeout=45,
                    headers={'User-Agent': config.get('sec_user_agent', 'Workspace investment research research@example.com')})
                response.raise_for_status()
                path.write_bytes(response.content)
                time.sleep(.25)
            return path.read_text()
        try:
            soup = BeautifulSoup(get(url, source / f'{key}-8k.html'), 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if re.search(r'\.htm', href, re.I) and (re.search(r'99[._-]?1|ex99|exhibit99', href, re.I)
                    or re.search(r'99\.[12]', a.get_text(' ', strip=True))):
                    links.append(urljoin(url, href))
            records = []
            for n, address in enumerate(list(dict.fromkeys(links))[:2], 1):
                path = source / f'{key}-ex{n}.html'
                body = get(address, path)
                text_path = path.with_suffix('.txt')
                text_path.write_text(BeautifulSoup(body, 'html.parser').get_text(' ', strip=True))
                records.append({'ticker': ticker, 'reported_fy': year, 'published_on': day,
                    'url': address, 'local_path': str(path.relative_to(root)),
                    'text_path': str(text_path.relative_to(root)), 'retrieved_on': config['as_of'],
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            return records
        except (requests.RequestException, OSError) as error:
            return [{'ticker': ticker, 'reported_fy': year, 'url': url, 'error': str(error)}]

    with ThreadPoolExecutor(max_workers=3) as pool:
        records = [r for batch in pool.map(fetch, jobs) for r in batch]
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    records = acquire(config, Path.cwd())
    (Path(config['output_dir']) / 'guidance-release-index.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cached_exhibits': sum('error' not in r for r in records),
                      'errors': [r for r in records if 'error' in r]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
