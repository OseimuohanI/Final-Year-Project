"""Collect/replay dated open-business facts; never substitute publicity for reviews.

Outputs are research files, not dashboard imports. Existing source captures are
reused byte-for-byte. New downloads require --collect and obey robots rules.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import httpx

AGENT = 'PulseboardResearchCollector'
MONTHS = {name.lower(): i for i, name in enumerate(
    ('January February March April May June July August September October November December').split(), 1)}
LABELS = {'MRR': 'mrr_usd', 'ARR': 'arr_usd', 'Customers': 'customers',
          'MAU': 'monthly_active_users', 'ARPU': 'arpu_usd', 'Team Size': 'team_size',
          'Net Income': 'net_income_usd', 'Bank Balance': 'bank_balance_usd',
          'Revenue Per Employee': 'reported_revenue_per_employee_usd'}
HOSTS = {'buffer.com', 'ghost.org', 'baremetrics.com', 'apps.apple.com', 'suggestions.buffer.com',
         'www.capterra.com', 'www.trustradius.com', 'www.g2.com'}


def number(text: str) -> str:
    match = re.match(r'^\s*([-−]?)\$?([\d,]+(?:\.\d+)?)([KMB])?', text, re.I)
    if not match:
        raise ValueError(f'Not a reported number: {text!r}')
    sign, digits, suffix = match.groups()
    value = Decimal(digits.replace(',', '')) * {'K': 1000, 'M': 1000000, 'B': 1000000000}.get((suffix or '').upper(), 1)
    return format(-value if sign else value, 'f')


def report_links(html: str, source: str) -> list[str]:
    result = set()
    for anchor in BeautifulSoup(html, 'html.parser').select('a[href]'):
        url = urljoin(source, anchor['href']).split('#')[0]
        path = urlsplit(url).path
        if urlsplit(url).hostname == 'buffer.com' and re.fullmatch(
                r'/shareholders/(?:'+'|'.join(MONTHS)+r')-\d{4}', path):
            result.add(url)
    return sorted(result)


def parse_report(html: str, source: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main') or soup
    heading = main.find('h1')
    title = heading.get_text(' ', strip=True) if heading else ''
    match = re.fullmatch(r'([A-Za-z]+)(?: and Q[1-4])?\s+(\d{4})(?:\s+shareholder update)?', title, re.I)
    if not match or match[1].lower() not in MONTHS:
        raise ValueError('Not an individually identified calendar-month report.')
    period = date(int(match[2]), MONTHS[match[1].lower()], 1)
    texts = list(main.stripped_strings)
    published = None
    if 'Date:' in texts:
        value = texts[texts.index('Date:')+1]
        published = datetime.strptime(value, '%B %d, %Y').date().isoformat()
    if 'Key numbers' not in texts:
        raise ValueError('Missing the reported key-number table.')
    start = texts.index('Key numbers')+1
    end = next((i for i in range(start, len(texts)) if texts[i] in ('Notes:', 'Note-worthy Updates & Reflections', 'More shareholder updates')), len(texts))
    metrics = {}
    for i in range(start, end-1):
        if texts[i] in LABELS:
            metrics[LABELS[texts[i]]] = {'value': number(texts[i+1]), 'reported_text': texts[i+1]}
    if 'mrr_usd' not in metrics:
        raise ValueError('No explicitly labelled MRR value.')
    notes = ' '.join(texts[end:])
    revenue = re.search(r'\b'+match[1]+r' revenue (?:finished at|was|came in at)[^$]{0,45}(\$[\d,.]+[KMB]?)', notes, re.I)
    if revenue:
        metrics['monthly_revenue_usd'] = {'value': number(revenue[1]), 'reported_text': revenue[1], 'rounded_source_value': True}
    article_end = texts.index('More shareholder updates') if 'More shareholder updates' in texts else len(texts)
    body = ' '.join(texts[:article_end])
    definition_change = bool(re.search(r'(?:change|adjust|updat|revis).{0,100}MRR.{0,100}(?:calculat|method|defin)', body, re.I))
    return {'business_id': 'buffer', 'period_start': period.isoformat(), 'frequency': 'monthly',
            'published_at': published, 'source_url': source, 'currency': 'USD', 'metrics': metrics,
            'mrr_definition_change_mentioned': definition_change,
            'report_also_contains_quarter_summary': bool(re.search(r'\bQ[1-4]\b', title)),
            'historical_publication_time_verified': False,
            'publication_date_policy': 'Reported date; only eligible on the following day (time unknown).',
            'scope': 'Global company; not Nigeria-only; self-reported public figures.'}


def parse_apple_reviews(html: str, source: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='serialized-server-data')
    if not script:
        raise ValueError('Apple serialized page data is missing.')
    payload = json.loads(script.get_text())
    records = {}

    def visit(value):
        if isinstance(value, dict):
            if value.get('$kind') == 'Review' and all(k in value for k in ('id', 'contents', 'rating', 'date')):
                stamp = datetime.fromisoformat(value['date'].replace('Z', '+00:00'))
                rating = int(value['rating'])
                if not 1 <= rating <= 5 or not value['contents'].strip():
                    raise ValueError('Invalid source review.')
                key = 'apple:490474324:'+str(value['id'])
                record = {'business_id': 'buffer', 'source_review_id': key,
                          'raw_text': '\n'.join(filter(None, [value.get('title', '').strip(), value['contents'].strip()])),
                          'reviewed_at': stamp.isoformat(), 'star_rating': rating,
                          'source_url': source, 'source': 'apple_app_store', 'storefront': 'us',
                          'paid_customer_verified': False, 'historical_text_vintage_verified': False,
                          'edited_text_possible': True}
                if key in records and records[key]['raw_text'] != record['raw_text']:
                    raise ValueError('Conflicting duplicate review ID in one capture.')
                records[key] = record
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(payload)
    return list(records.values())


class Sources:
    def __init__(self, root: Path, live: bool = False):
        self.root, self.live = root, live
        self.manifest_file = root/'sources/manifest.json'
        self.rows = json.loads(self.manifest_file.read_text()) if self.manifest_file.exists() else []
        self.robots = {}
        self.last_request = {}
        self.client = httpx.Client(headers={'User-Agent': AGENT+'/1.0 (+https://github.com/OseimuohanI/Final-Year-Project)'}, timeout=30)

    def fetch(self, url: str, redirects: int = 0) -> str:
        if redirects > 5:
            raise ValueError('Too many public-source redirects.')
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.hostname not in HOSTS or parts.username or parts.password:
            raise ValueError('Unrecognised public-source URL.')
        existing = next((row for row in reversed(self.rows) if row.get('url') == url and row.get('http_status') == 200), None)
        if existing:
            content = (self.root/existing['path']).read_bytes()
            if hashlib.sha256(content).hexdigest() != existing['sha256']:
                raise ValueError('Source checksum mismatch.')
            return content.decode('utf-8')
        redirect = next((row for row in reversed(self.rows) if row.get('url') == url and row.get('redirect_to')), None)
        if redirect:
            return self.fetch(redirect['redirect_to'], redirects+1)
        if not self.live:
            raise ValueError('Source not captured: '+url)
        if parts.path != '/robots.txt':
            if parts.hostname not in self.robots:
                policy = RobotFileParser()
                policy.parse(self.fetch(f'https://{parts.hostname}/robots.txt').splitlines())
                self.robots[parts.hostname] = policy
            if not self.robots[parts.hostname].can_fetch(AGENT, url):
                raise ValueError('Crawler rules disallow '+url)
        pause = 3-(time.monotonic()-self.last_request.get(parts.hostname, 0))
        if pause > 0:
            time.sleep(pause)
        response = self.client.get(url)
        self.last_request[parts.hostname] = time.monotonic()
        content = response.content
        digest = hashlib.sha256(content).hexdigest()
        dest = self.root/'sources'/f'{parts.hostname}-{digest[:20]}.source'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        self.rows.append({'url': url, 'http_status': response.status_code, 'path': str(dest.relative_to(self.root)),
                          'captured_at': datetime.now(timezone.utc).isoformat(), 'sha256': digest, 'bytes': len(content)})
        if response.is_redirect and response.headers.get('location'):
            self.rows[-1]['redirect_to'] = urljoin(url, response.headers['location'])
        self.manifest_file.write_text(json.dumps(self.rows, indent=2)+'\n')
        if self.rows[-1].get('redirect_to'):
            return self.fetch(self.rows[-1]['redirect_to'], redirects+1)
        response.raise_for_status()
        return content.decode('utf-8')


def build_monthly_panel(financials: list[dict], feedback: list[dict]) -> list[dict]:
    """Alignment/availability audit only. No outcome is passed as a predictor."""
    result = []
    for target in sorted(financials, key=lambda row: row['period_start']):
        origin = date.fromisoformat(target['period_start'])
        previous_end = origin
        previous_start = origin.replace(year=origin.year-1, month=12) if origin.month == 1 else origin.replace(month=origin.month-1)
        # Strict earlier-date check conservatively excludes same-day releases.
        available = [row for row in financials if row['period_start'] < target['period_start']
                     and row['published_at'] and date.fromisoformat(row['published_at']) < origin]
        previous = max(available, key=lambda row: row['period_start']) if available else None
        reviews = [r for r in feedback if previous_start <= datetime.fromisoformat(r['reviewed_at']).date() < previous_end]
        scored = [r for r in reviews if r.get('sentiment')]
        result.append({'business_id': 'buffer', 'forecast_origin': origin.isoformat(),
                       'target_period': target['period_start'], 'target_mrr_usd': target['metrics']['mrr_usd']['value'],
                       'latest_available_financial_period': previous['period_start'] if previous else None,
                       'latest_available_mrr_usd': previous['metrics']['mrr_usd']['value'] if previous else None,
                       'feedback_window_start': previous_start.isoformat(),
                       'sampled_feedback_count': len(reviews), 'sampled_scored_count': len(scored),
                       'mean_sentiment': sum(r['sentiment']['compound_score'] for r in scored)/len(scored) if scored else None,
                       'negative_share': sum(r['sentiment']['label'] == 'negative' for r in scored)/len(scored) if scored else None,
                       'feedback_collection_complete': False, 'historical_text_vintage_verified': False,
                       'paired_observation_available': previous is not None and bool(scored)})
    return result


def snapshot_context(sources: Sources) -> dict:
    """Retain source discoveries without presenting live metrics as history."""
    audit = {}
    try:
        url = 'https://ghost.org/about/'
        tokens = list(BeautifulSoup(sources.fetch(url), 'html.parser').stripped_strings)
        metrics = {}
        for label in ['Annual Run Rate', 'Monthly Run Rate', 'Net churn', 'Active customers']:
            index = tokens.index(label)
            for text in reversed(tokens[max(0, index-4):index]):
                try:
                    metrics[label] = {'value': number(text), 'source_text': text}
                    break
                except ValueError:
                    continue
        capture = next(row for row in reversed(sources.rows) if row.get('url') == url and row.get('http_status') == 200)
        record = {'business_id': 'ghost', 'source_url': url, 'captured_at': capture['captured_at'],
                  'metrics': metrics, 'currency': 'USD', 'period_start': None,
                  'usable_as_historical_training_series': False,
                  'reason': 'Live snapshot has no verified monthly history or reference period.'}
        (sources.root/'ghost-current-snapshot.json').write_text(json.dumps(record, indent=2)+'\n')
        audit['ghost'] = {'status': 'live_snapshot_only', 'metrics': len(metrics)}
    except (ValueError, httpx.HTTPError) as error:
        audit['ghost'] = {'status': 'unavailable', 'reason': str(error)}
    try:
        url = 'https://baremetrics.com/open-startups'
        soup = BeautifulSoup(sources.fetch(url), 'html.parser')
        candidates = []
        for a in soup.select('a[href]'):
            host = urlsplit(a['href']).hostname or ''
            if host.endswith('.baremetrics.com') and host not in {
                    'app.baremetrics.com', 'demo.baremetrics.com', 'developers.baremetrics.com',
                    'help.baremetrics.com', 'status.baremetrics.com'}:
                candidates.append({'dashboard_url': a['href'].split('?')[0],
                                   'directory_description': a.get_text(' ', strip=True), 'historical_data_verified': False})
        record = {'source_url': url, 'candidates': candidates, 'usable_as_training_series': False}
        (sources.root/'baremetrics-directory-candidates.json').write_text(json.dumps(record, indent=2)+'\n')
        audit['baremetrics'] = {'status': 'directory_only', 'candidates': len(candidates)}
    except (ValueError, httpx.HTTPError) as error:
        audit['baremetrics'] = {'status': 'unavailable', 'reason': str(error)}
    (sources.root/'source-context-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    return audit


def collect(root: Path, live: bool = False, audit_reviews: bool = False) -> dict:
    sources = Sources(root, live)
    financials, exclusions = [], []
    index = sources.fetch('https://buffer.com/shareholders')
    links = report_links(index, 'https://buffer.com/shareholders')
    for position, url in enumerate(links, 1):
        try:
            financials.append(parse_report(sources.fetch(url), url))
        except (ValueError, httpx.HTTPError) as error:
            exclusions.append({'url': url, 'reason': str(error)})
        if position % 8 == 0 or position == len(links):
            print('Financial reports:',len(financials),flush=True)
    feedback = {}
    app_url = 'https://apps.apple.com/us/app/buffer-plan-schedule-posts/id490474324'
    app = sources.fetch(app_url)
    review_urls = {app_url}
    for a in BeautifulSoup(app, 'html.parser').select('a[href]'):
        if urlsplit(a['href']).hostname == 'apps.apple.com' and 'see-all=reviews' in a['href']:
            review_urls.add(a['href'])
    for url in sorted(review_urls):
        try:
            for row in parse_apple_reviews(sources.fetch(url), url):
                prior = feedback.get(row['source_review_id'])
                if prior and (prior['raw_text'],prior['star_rating'],prior['reviewed_at']) != (row['raw_text'],row['star_rating'],row['reviewed_at']):
                    raise ValueError('Conflicting repeated source ID across pages.')
                feedback[row['source_review_id']] = row
        except (ValueError, httpx.HTTPError) as error:
            exclusions.append({'url': url, 'reason': str(error)})
    financials.sort(key=lambda r:r['period_start'])
    if len({r['period_start'] for r in financials}) != len(financials):
        raise ValueError('Duplicate monthly reports need manual resolution.')
    records = sorted(feedback.values(), key=lambda r:r['reviewed_at'])
    review_audit = []
    if audit_reviews:
        for url in ['https://www.capterra.com/p/143492/Buffer/reviews/',
                    'https://www.trustradius.com/products/buffer/reviews',
                    'https://www.g2.com/products/buffer/reviews']:
            try:
                html = sources.fetch(url)
                review_audit.append({'url': url, 'status': 'captured_needs_parser_audit', 'bytes': len(html.encode())})
            except (ValueError, httpx.HTTPError) as error:
                review_audit.append({'url': url, 'status': 'unavailable_to_collector', 'reason': str(error)})
        (root/'additional-review-source-audit.json').write_text(json.dumps(review_audit,indent=2)+'\n')
    for name, data in [('buffer-financials.json',financials),('buffer-feedback.raw.json',records),('exclusions.json',exclusions)]:
        (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    result = {'business': 'Buffer', 'financial_months':len(financials), 'feedback_records':len(records),
              'financial_period_range':[r['period_start'] for r in financials[::max(1,len(financials)-1)]],
              'feedback_months':dict(sorted(Counter(r['reviewed_at'][:7] for r in records).items())),
              'financials_missing_publication_dates':sum(not r['published_at'] for r in financials),
              'definition_change_periods':[r['period_start'] for r in financials if r['mrr_definition_change_mentioned']],
              'exclusions':exclusions, 'status':'collected_for_coverage_audit_not_trained',
              'target_definition':'Global company monthly recurring run rate, not sales or Nigerian revenue.',
              'feedback_scope':'Visible US Apple app review sample; free and paid users not distinguished; historical text versions unverified.',
              'other_sources': {'ghost':'Live snapshot retained; monthly financial history not established.',
                                'baremetrics':'Current directory retained; not itself a financial time series.',
                                'trustpilot':'Collector access disallowed by crawler rules; no reviews downloaded.'}}
    result['context_source_audit'] = snapshot_context(sources)
    (root/'collection-report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--audit-review-sources', action='store_true')
    args = parser.parse_args()
    print(json.dumps(collect(args.snapshot, args.collect, args.audit_review_sources),indent=2))
