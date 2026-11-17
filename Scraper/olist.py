"""Download the original Olist research release through Kaggle's public API.

No credentials, scraping proxies or third-party mirrors. Raw files stay local.
Replay verifies every captured file before analysis.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

import httpx

BASE = 'https://www.kaggle.com/api/v1/datasets'
REF = 'olistbr/brazilian-ecommerce'
VERSION = 2
FILES = {
    'olist_orders_dataset.csv', 'olist_order_items_dataset.csv',
    'olist_order_reviews_dataset.csv', 'olist_order_payments_dataset.csv',
    'olist_products_dataset.csv', 'product_category_name_translation.csv',
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    manifest = json.loads((root/'source-manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        if sha256(root/name) != expected:
            raise ValueError('Source checksum mismatch: '+name)
    return manifest


def collect(root: Path):
    if (root/'source-manifest.json').exists():
        return verify(root)
    root.mkdir(parents=True, exist_ok=True)
    captured = datetime.now(timezone.utc).isoformat()
    with httpx.Client(follow_redirects=True, timeout=180, headers={
        'User-Agent': 'PulseboardResearchCollector/1.0 (+https://github.com/OseimuohanI/Final-Year-Project)',
    }) as client:
        metadata_url = f'{BASE}/view/{REF}'
        r = client.get(metadata_url)
        r.raise_for_status()
        metadata = r.json()
        (root/'kaggle-metadata.json').write_bytes(r.content)
        licence = metadata.get('licenseName') or metadata.get('licenseNameNullable')
        if licence != 'CC BY-NC-SA 4.0':
            raise ValueError('Review the source licence before continuing: '+str(licence))
        current_version = metadata.get('currentVersionNumber')
        if not isinstance(current_version, int) or current_version < VERSION:
            raise ValueError('Missing source version number.')
        version = VERSION  # A later Kaggle release must not silently change this experiment.
        url = f'{BASE}/download/{REF}?datasetVersionNumber={version}'
        archive = root/'olist-original.zip'
        temporary = root/'olist-original.zip.part'
        with client.stream('GET', url) as response:
            response.raise_for_status()
            with temporary.open('wb') as output:
                for chunk in response.iter_bytes():
                    output.write(chunk)
                    if output.tell() > 100_000_000:
                        raise ValueError('Unexpected archive size.')
        temporary.replace(archive)
    with zipfile.ZipFile(archive) as release:
        for name in sorted(FILES):
            member = release.getinfo(name)
            if member.file_size > 40_000_000:
                raise ValueError('Unexpected file size.')
            # Explicit filenames only: never extract arbitrary archive paths.
            (root/name).write_bytes(release.read(member))
    manifest = {
        'dataset': REF, 'source_url': 'https://www.kaggle.com/datasets/'+REF,
        'metadata_url': metadata_url, 'download_url': url, 'version': version,
        'captured_at': captured, 'licence': licence,
        'use': 'Academic non-commercial research; attribution and share-alike apply.',
        'publisher': 'Olist', 'currency': 'BRL',
        'sha256': {p.name: sha256(p) for p in sorted(root.iterdir())
                   if p.name in FILES | {'olist-original.zip', 'kaggle-metadata.json'}},
    }
    (root/'source-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return verify(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--collect', action='store_true')
    args = parser.parse_args()
    result = collect(args.snapshot) if args.collect else verify(args.snapshot)
    print(json.dumps({k: v for k, v in result.items() if k != 'sha256'}, indent=2))
