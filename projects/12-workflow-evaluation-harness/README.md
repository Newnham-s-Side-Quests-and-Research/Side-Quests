# Workflow Evaluation Harness

This project is an initial local implementation. It compares a baseline and a candidate using synthetic cases. It does not call a model or make release decisions.

## Run the tests

From this folder run:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Run a comparison

```powershell
$env:PYTHONPATH = "src"
python -m evaluation_harness --cases fixtures/cases.json --candidate sound --output results/sound
```

Replace `sound` with `wrong_field`, `false_accept` or `false_abstain` to run a deliberately defective candidate. The command writes a JSON report and a short text report. The rules are demonstration values and require review before any real use.

## Design and limits

See `docs/decisions.md` for the case format, scoring rules and exit codes. The three included synthetic cases check the mechanics only. They do not establish real world accuracy, cost, latency or statistical confidence. Adapter timeouts, external providers and repeat trial statistics are later work. A passing gate does not authorise a release.
