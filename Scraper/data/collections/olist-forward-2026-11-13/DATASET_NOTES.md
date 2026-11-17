# Olist forward evaluation and historical application demo

Uses the unchanged original Olist Kaggle v2 release and source hashes from the
2 January 2017–29 July 2018 study, extended only through Sunday 26 August 2018.
Credit **Olist**, [original dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
licence **CC BY-NC-SA 4.0**, non-commercial research with attribution/share-alike.
Raw source, feedback, scores and exports remain local and ignored by Git.

There are **86** complete weekly targets and **41,110** usable dated text reviews.
All prior deduplication, timing and outcome-definition rules remain. Target is
approval-week item value in BRL, excluding freight; not net revenue or profit.

The four new evaluation weeks are 30 July, 6 August, 13 August and 20 August
2018. Fixed penalties and features were declared before measuring their errors.
Sentiment inference is reused only for matching cleaned text and model identity;
2,895 additional distinct texts required inference. Full output covers every
eligible feedback record. No stars are converted into sentiment labels.

`forward-protocol.json` links the previous snapshot and protocol hashes.
`commercial-import.json` is the genuine weekly sales export for the separately
named historical demo. No artificial financial values or date spreading.
The final incomplete source tail is not used as an actual-outcome test.

The app retains source wall-clock review boundaries in its Africa/Lagos calendar
for this isolated demo. The dataset does not supply a source timezone; this is
an adapter convention, not a claim that Brazilian events occurred in Nigeria.

See [release, measured results and reproduction](../../../../docs/COMMERCIAL_RELEASE.md)
and the [fixed protocol](../../../../NLP_Service/evaluation/COMMERCIAL_FORWARD_PROTOCOL.md).
