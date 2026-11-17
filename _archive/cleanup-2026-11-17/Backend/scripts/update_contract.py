from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "NLP_SERVICE_CONTRACT.md"

with CONTRACT_PATH.open("r") as f:
    text = f.read()

zero_variance_note = """- **Zero-variance jitter:** When a weekly series has near-zero variance (e.g. a perfectly flat run of identical values), the forecasting pipeline injects small deterministic noise (seeded jitter) prior to fitting. This avoids a NaN-AIC failure in the `statsmodels` statespace implementation on degenerate input. As a side effect, a genuinely flat business metric will exhibit tiny fabricated variation in its forecast values; this is a numerical necessity for stability rather than a modeling choice.
- **Mann-Kendall fallback trigger:** The `_classify_trend` function falls back from the `hamed_rao_modification_test` to the unmodified `original_test` whenever the modified test's p-value comes back `NaN`. This `NaN` output natively occurs on autocorrelation-degenerate series (e.g., near-constant or perfectly linear runs, which includes the zero-variance jitter case above). In such cases, the autocorrelation correction is skipped entirely, precisely where autocorrelation might otherwise be a structural concern (near-constant series). This fallback is a known, accepted limitation rather than an oversight."""

new_text = text.replace("## Request validation and errors", zero_variance_note + "\n\n## Request validation and errors")

with CONTRACT_PATH.open("w") as f:
    f.write(new_text)

print("Updated contract.")
