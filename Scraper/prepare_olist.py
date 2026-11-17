"""Audit and prepare Olist for one-week-ahead commercial forecasting.

Target: approved order merchandise value (BRL), excluding freight. It is gross
order value, NOT Olist's net revenue/profit. Never filter on final order status.
Survey scores stay separate from text sentiment. Use answer time, not purchase
or survey-creation time, to determine when feedback became available.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from olist import verify

START = datetime(2017, 1, 2)
END = datetime(2018, 7, 30)  # Last target week: July 23–29, before terminal collapse.
SAMPLE_PER_WEEK = 32
SEED = 'pulseboard-olist-pilot-v1'


def load(root, name):
    with (root/name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def stamp(text):
    return datetime.strptime(text, '%Y-%m-%d %H:%M:%S')


def week_of(day):
    return (day - timedelta(days=day.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def prepare(root: Path):
    manifest = verify(root)
    if manifest['version'] != 2:
        raise ValueError('Review the protocol for a different Olist release.')
    orders = load(root, 'olist_orders_dataset.csv')
    items = load(root, 'olist_order_items_dataset.csv')
    raw = load(root, 'olist_order_reviews_dataset.csv')
    payments = load(root, 'olist_order_payments_dataset.csv')
    order_map = {r['order_id']: r for r in orders}
    if len(order_map) != len(orders):
        raise ValueError('Duplicate order ID.')
    item_keys = {(r['order_id'], r['order_item_id']) for r in items}
    if len(item_keys) != len(items):
        raise ValueError('Duplicate item key.')
    if any(r['order_id'] not in order_map for r in items + raw + payments):
        raise ValueError('Orphan order reference.')
    value = defaultdict(Decimal)
    freight = defaultdict(Decimal)
    for row in items:
        amount, shipping = Decimal(row['price']), Decimal(row['freight_value'])
        if amount < 0 or shipping < 0:
            raise ValueError('Negative source price.')
        value[row['order_id']] += amount
        freight[row['order_id']] += shipping
    # Aggregate each child table independently. Joining items × reviews ×
    # payments first would multiply both revenue and feedback counts.
    paid = defaultdict(Decimal)
    for row in payments:
        paid[row['order_id']] += Decimal(row['payment_value'])
    revenue, count = defaultdict(Decimal), Counter()
    missing_approval = 0
    approval_before_purchase = 0
    for order_id, amount in value.items():
        order = order_map[order_id]
        if not order['order_approved_at']:
            missing_approval += 1
            continue
        approved = stamp(order['order_approved_at'])
        if approved < stamp(order['order_purchase_timestamp']):
            approval_before_purchase += 1
            continue
        week = week_of(approved).date().isoformat()
        revenue[week] += amount
        count[week] += 1
    groups = defaultdict(list)
    for row in raw:
        groups[row['review_id']].append(row)
    reviews = []
    conflicting = 0
    invalid_time = 0
    for review_id, group in sorted(groups.items()):
        fields = ['review_score', 'review_comment_title', 'review_comment_message',
                  'review_creation_date', 'review_answer_timestamp']
        if len({tuple(r[k] for k in fields) for r in group}) != 1:
            conflicting += 1
            continue
        row = group[0]
        answered = stamp(row['review_answer_timestamp'])
        if (answered < stamp(row['review_creation_date']) or
                any(answered < stamp(order_map[r['order_id']]['order_purchase_timestamp']) for r in group)):
            invalid_time += 1
            continue
        stars = int(row['review_score'])
        if not 1 <= stars <= 5:
            raise ValueError('Invalid survey score.')
        reviews.append({
            'review_id': review_id, 'order_ids': sorted({r['order_id'] for r in group}),
            'available_at': answered.isoformat(),
            'week': week_of(answered).date().isoformat(),
            'raw_text': '\n'.join(filter(None, [row['review_comment_title'].strip(), row['review_comment_message'].strip()])),
            'star_rating': stars, 'source_language': 'pt',
        })
    by_week = defaultdict(list)
    for review in reviews:
        if review['raw_text'] and START <= datetime.fromisoformat(review['week']) < END:
            by_week[review['week']].append(review)
    sample = []
    for week, group in sorted(by_week.items()):
        sample += sorted(group, key=lambda r: hashlib.sha256((SEED+r['review_id']).encode()).hexdigest())[:SAMPLE_PER_WEEK]
    weeks = []
    current = START
    while current < END:
        key = current.date().isoformat()
        feedback = [r for r in reviews if r['week'] == key]
        weeks.append({
            'week': key, 'approved_merchandise_value_brl': str(revenue[key]),
            'approved_order_count': count[key], 'unique_answered_reviews': len(feedback),
            'text_review_count': len(by_week[key]),
            'sampled_text_review_count': sum(r['week'] == key for r in sample),
        })
        current += timedelta(days=7)
    mismatches = [abs(paid[k]-value[k]-freight[k]) for k in value if k in paid]
    report = {
        'source': manifest['source_url'], 'source_version': manifest['version'], 'licence': manifest['licence'],
        'rows': {'orders': len(orders), 'items': len(items), 'reviews': len(raw), 'payments': len(payments)},
        'unique_review_ids': len(groups), 'duplicate_review_rows_collapsed': len(raw)-len(groups),
        'conflicting_review_ids_excluded': conflicting, 'invalid_review_times_excluded': invalid_time,
        'orders_with_items_without_approval_excluded': missing_approval,
        'approval_before_purchase_excluded': approval_before_purchase,
        'unique_reviews_with_text': sum(bool(r['raw_text']) for r in reviews),
        'text_reviews_in_experiment_window': sum(len(v) for v in by_week.values()),
        'sampled_text_reviews': len(sample), 'weekly_periods': len(weeks),
        'weekly_target_range': [weeks[0]['week'], weeks[-1]['week']],
        'sample_rule': f'Up to {SAMPLE_PER_WEEK} unique text reviews per response week, smallest SHA256(seed+review_id); seed={SEED}. No use of stars or target values.',
        'payments_reconciliation': {
            'orders_with_items_and_payments': len(mismatches),
            'within_one_cent_of_items_plus_freight': sum(delta <= Decimal('.01') for delta in mismatches),
            'max_absolute_difference_brl': str(max(mismatches)),
            'note': 'Payment totals include freight and can differ. They are not the merchandise-value target.',
        },
        'target': 'Sum of item prices for approved orders, grouped by approval week; BRL; excludes freight.',
        'business_scope': 'Olist store aggregate across participating sellers, not one seller or a Nigerian business.',
        'review_availability': 'review_answer_timestamp in source local wall time, not survey creation or order date. Timezone not supplied.',
        'no_final_status_filter': True, 'refunds_and_cancellations_netted': False,
        'limitations': [
            'Source is a static, anonymised historical extract, not an independently audited sales ledger.',
            'Item amounts are final snapshot values; historical amount revisions are unverified.',
            'Missing text is absent sentiment; surveys without text are not labelled from their stars.',
            'Reviews concern the order experience and can involve multiple items or sellers.',
            'The final sparse September–October 2018 orders are excluded rather than treated as business collapse.',
            'Pilot sentiment uses a fixed per-week sample; the full dated feedback is retained for expansion.',
        ],
    }
    experiment_reviews = [r for r in reviews if r['raw_text'] and START <= datetime.fromisoformat(r['week']) < END]
    for filename, payload in [('weekly-panel.json', weeks), ('reviews.prepared.json', reviews),
                              ('reviews.experiment.json', experiment_reviews),
                              ('reviews.sample.json', sample), ('readiness-report.json', report)]:
        (root/filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.snapshot), indent=2))
