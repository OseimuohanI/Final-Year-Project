# RePro classification-validation snapshot

Source: [author-hosted RePro](https://huggingface.co/datasets/lucasnil/repro),
revision `cb93d9cc1183d4a594317a5188d325bcaa04cda4`.
Paper: [RePro: A Benchmark Dataset for Opinion Mining in Brazilian Portuguese](https://aclanthology.org/2024.propor-1.44/).
Credit the RePro authors and B2W Digital. Follow the explicit **CC BY-NC-SA 4.0**
licence in README Licensing and the paper, despite conflicting CC-BY frontmatter.
Non-commercial research only; raw records and scores are ignored by Git.

The downloaded original CSV has 10,003 rows. Preparation excludes 2,018 mixed
polarity examples, five exact cleaned Olist-text overlaps, and five duplicate
texts. The resulting 7,975 references use published human polarity annotations;
stars and demographic attributes are not classifier inputs or reference labels.
Processed records retain only source row ID, text and reference polarity.

`preparation-report.json` records counts, source checksums and exclusions.
`scoring-full/reviews.scored.json` records frozen-model outputs and identity.
`validation-report.json` records confusion matrix, per-class metrics and limits.
Accuracy 91.49%, macro-F1 0.803. Neutral precision is 36.75%, a material weakness.
No classifier tuning was performed against this benchmark.

See [release and reproduction commands](../../../../docs/COMMERCIAL_RELEASE.md).
