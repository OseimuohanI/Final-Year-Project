"""Source integrity, review timing and commercial aggregation regression tests."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRAPER))
from olist import verify
from prepare_olist import prepare


def write_csv(root, name, rows):
    with (root/name).open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(root):
    orders = [
        {'order_id': 'a', 'order_purchase_timestamp': '2017-01-03 09:00:00',
         'order_approved_at': '2017-01-03 10:00:00', 'order_status': 'canceled'},
        {'order_id': 'b', 'order_purchase_timestamp': '2017-01-04 09:00:00',
         'order_approved_at': '', 'order_status': 'created'},
    ]
    items = [
        {'order_id': 'a', 'order_item_id': '1', 'price': '100.10', 'freight_value': '10'},
        {'order_id': 'a', 'order_item_id': '2', 'price': '20.20', 'freight_value': '2'},
        {'order_id': 'b', 'order_item_id': '1', 'price': '99', 'freight_value': '1'},
    ]
    a = {'review_id': 'r1', 'order_id': 'a', 'review_score': '1', 'review_comment_title': '',
         'review_comment_message': 'bom produto', 'review_creation_date': '2017-01-08 00:00:00',
         'review_answer_timestamp': '2017-01-10 10:00:00'}
    reviews = [a, a, {**a, 'review_id': 'impossible', 'review_answer_timestamp': '2017-01-01 00:00:00'},
               {**a, 'review_id': 'conflict'}, {**a, 'review_id': 'conflict', 'review_comment_message': 'different text'}]
    payments = [{'order_id': 'a', 'payment_value': '100'}, {'order_id': 'a', 'payment_value': '32.30'}]
    for name, data in [('olist_orders_dataset.csv', orders), ('olist_order_items_dataset.csv', items),
                       ('olist_order_reviews_dataset.csv', reviews), ('olist_order_payments_dataset.csv', payments)]:
        write_csv(root, name, data)
    manifest = {'version': 2, 'source_url': 'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce',
                'licence': 'CC BY-NC-SA 4.0',
                'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.csv')}}
    (root/'source-manifest.json').write_text(json.dumps(manifest))


def test_child_tables_do_not_multiply_value_and_final_status_does_not_leak(tmp_path):
    fixture(tmp_path)
    report = prepare(tmp_path)
    weeks = json.loads((tmp_path/'weekly-panel.json').read_text())
    reviews = json.loads((tmp_path/'reviews.prepared.json').read_text())
    assert weeks[0]['approved_merchandise_value_brl'] == '120.30'
    assert weeks[0]['approved_order_count'] == 1
    assert weeks[0]['text_review_count'] == 0
    assert weeks[1]['text_review_count'] == 1  # Answer, not purchase week.
    assert len(reviews) == 1
    assert reviews[0]['star_rating'] == 1 and reviews[0]['raw_text'] == 'bom produto'
    assert 'sentiment' not in reviews[0]  # Stars are never converted into text sentiment.
    assert report['conflicting_review_ids_excluded'] == 1
    assert report['invalid_review_times_excluded'] == 1
    assert report['orders_with_items_without_approval_excluded'] == 1
    assert report['payments_reconciliation']['within_one_cent_of_items_plus_freight'] == 1


def test_modified_sources_are_rejected_before_preparation(tmp_path):
    fixture(tmp_path)
    (tmp_path/'olist_orders_dataset.csv').write_text('changed')
    with pytest.raises(ValueError, match='checksum mismatch'):
        verify(tmp_path)


def test_hash_sample_is_rating_independent_and_reproducible(tmp_path):
    fixture(tmp_path)
    prepare(tmp_path)
    first = (tmp_path/'reviews.sample.json').read_bytes()
    prepare(tmp_path)
    assert (tmp_path/'reviews.sample.json').read_bytes() == first
