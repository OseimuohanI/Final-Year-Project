"""Financial period, provenance, feedback and availability regression checks."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

spec = importlib.util.spec_from_file_location('open_startups', Path(__file__).parents[1]/'open_startups.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def financial(period, published, mrr):
    return {'business_id': 'buffer', 'period_start': period, 'published_at': published,
            'metrics': {'mrr_usd': {'value': str(mrr)}}}


def test_report_keeps_mrr_revenue_and_publication_date_distinct():
    html = '''<main><h1>December 2025 shareholder update</h1><p>Date:</p><p>January 20, 2026</p>
        <h2>Key numbers</h2><p>MRR</p><p>$1,947,103</p><p>(+0.56%)</p>
        <p>ARR</p><p>$23,365,236</p><p>Customers</p><p>69,760</p>
        <h2>Notes:</h2><p>December revenue finished at an all-time high of $2.008M,
        bringing total annual revenue to $22.462M.</p>
        <h2>More shareholder updates</h2><a>August 2025 A change in MRR and ARR calculation</a></main>'''
    row = module.parse_report(html, 'https://buffer.com/shareholders/december-2025')
    assert row['period_start'] == '2025-12-01'
    assert row['published_at'] == '2026-01-20'
    assert float(row['metrics']['mrr_usd']['value']) == 1947103
    assert float(row['metrics']['monthly_revenue_usd']['value']) == 2008000
    assert row['metrics']['monthly_revenue_usd']['rounded_source_value'] is True
    assert row['metrics']['customers']['value'] == '69760'
    assert row['mrr_definition_change_mentioned'] is False


def test_missing_dates_are_not_invented_and_combined_periods_are_not_split():
    row = module.parse_report('<main><h1>January 2025</h1><p>Key numbers</p><p>MRR</p><p>$100</p></main>', 'https://buffer.com/shareholders/january-2025')
    assert row['published_at'] is None
    with pytest.raises(ValueError, match='individually'):
        module.parse_report('<h1>April + May 2023</h1>', 'https://buffer.com/shareholders/april-may-2023')
    links = module.report_links('''<a href="/shareholders/january-2025">Jan</a>
        <a href="/shareholders/april-may-2023">Both</a><a href="/shareholders/2023">Annual</a>
        <a href="https://other.example/shareholders/january-2025">Other</a>''', 'https://buffer.com/shareholders')
    assert links == ['https://buffer.com/shareholders/january-2025']


def test_named_month_with_quarter_commentary_preserves_monthly_run_rate():
    row = module.parse_report('<main><h1>September and Q3 2024</h1><p>Key numbers</p><p>MRR</p><p>$100</p></main>', 'https://buffer.com/shareholders/september-2024')
    assert row['period_start'] == '2024-09-01'
    assert row['report_also_contains_quarter_summary'] is True


def test_apple_review_ids_deduplicate_without_treating_developer_responses_as_reviews():
    review = {'$kind': 'Review', 'id': '123', 'title': 'Support', 'contents': 'Slow support',
              'rating': 2, 'date': '2025-12-15T12:00:00Z', 'reviewerName': 'Do not export this name',
              'response': {'contents': 'A company response', 'date': '2025-12-16'}}
    html = '<script id="serialized-server-data" type="application/json">'+json.dumps({'items': [review, review]})+'</script>'
    result = module.parse_apple_reviews(html, 'https://apps.apple.com/us/app/490474324?see-all=reviews')
    assert len(result) == 1
    assert result[0]['raw_text'] == 'Support\nSlow support'
    assert result[0]['star_rating'] == 2
    assert 'reviewerName' not in result[0]
    assert result[0]['historical_text_vintage_verified'] is False


def test_conflicting_review_ids_are_rejected():
    a = {'$kind': 'Review', 'id': 'a', 'contents': 'Earlier text', 'rating': 2, 'date': '2025-12-15T12:00:00Z'}
    b = {**a, 'contents': 'Different text'}
    html = '<script id="serialized-server-data">'+json.dumps([a, b])+'</script>'
    with pytest.raises(ValueError, match='Conflicting'):
        module.parse_apple_reviews(html, 'https://apps.apple.com/us/app/490474324')


def test_panel_only_uses_financials_published_strictly_before_the_forecast():
    rows = [financial('2025-11-01', '2025-12-20', 90), financial('2025-12-01', '2026-01-20', 100),
            financial('2026-01-01', '2026-02-20', 110), financial('2026-02-01', '2026-03-20', 120)]
    panel = module.build_monthly_panel(rows, [])
    assert panel[2]['latest_available_financial_period'] == '2025-11-01'
    assert panel[3]['latest_available_financial_period'] == '2025-12-01'
    assert panel[3]['mean_sentiment'] is None
    assert panel[3]['paired_observation_available'] is False
    changed = copy.deepcopy(rows)
    changed[2]['metrics']['mrr_usd']['value'] = '999999'
    after = module.build_monthly_panel(changed, [])
    assert after[2]['latest_available_mrr_usd'] == panel[2]['latest_available_mrr_usd']


def test_panel_keeps_feedback_sample_size_and_missingness_explicit():
    reviews = [{'reviewed_at': '2025-12-31T23:59:00+00:00', 'sentiment': {'label': 'negative', 'compound_score': -.8}},
               {'reviewed_at': '2026-01-01T00:00:00+00:00', 'sentiment': {'label': 'positive', 'compound_score': .9}}]
    panel = module.build_monthly_panel([financial('2025-11-01', '2025-12-20', 90), financial('2026-01-01', '2026-02-20', 110)], reviews)
    assert panel[1]['sampled_scored_count'] == 1
    assert panel[1]['mean_sentiment'] == -.8
    assert panel[1]['negative_share'] == 1
    assert panel[1]['feedback_collection_complete'] is False


def test_replay_verifies_original_source_checksum(tmp_path):
    (tmp_path/'sources').mkdir()
    (tmp_path/'sources/page').write_text('original')
    (tmp_path/'sources/manifest.json').write_text(json.dumps([{
        'url': 'https://buffer.com/shareholders', 'http_status': 200, 'path': 'sources/page',
        'sha256': hashlib.sha256(b'original').hexdigest()}]))
    sources = module.Sources(tmp_path)
    assert sources.fetch('https://buffer.com/shareholders') == 'original'
    (tmp_path/'sources/page').write_text('changed')
    with pytest.raises(ValueError, match='checksum'):
        sources.fetch('https://buffer.com/shareholders')


def test_replayed_redirects_cannot_escape_the_source_allowlist(tmp_path):
    (tmp_path/'sources').mkdir()
    (tmp_path/'sources/manifest.json').write_text(json.dumps([{
        'url': 'https://apps.apple.com/us/app/490474324', 'http_status': 301,
        'redirect_to': 'http://127.0.0.1/private'}]))
    with pytest.raises(ValueError, match='Unrecognised'):
        module.Sources(tmp_path).fetch('https://apps.apple.com/us/app/490474324')
