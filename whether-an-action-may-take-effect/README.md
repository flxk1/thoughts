# Whether an action may take effect

*A governance language for AI agents, and the conformance suite that tests it.* Felix Krone, 2026.

Read [`paper.pdf`](paper.pdf); [`paper.md`](paper.md) is the source it is built from.

## What is here

| | |
|---|---|
| `paper.md`, `paper.pdf`, `figures/` | the text and its two figures (`figures/make_figures.py` draws them) |
| `reproduce.sh` | the one entry point: `bash reproduce.sh historical WORKDIR` clones the five repositories at the commits the paper pins, builds a virtual environment from `requirements.lock`, and runs every experiment into `audit/historical/` |
| `audit/published/` | the outputs the paper reports, as recorded on 2026-10-10 and 2026-10-20, with `pins.txt` |
| `audit/differential.py`, `audit/kit-mock-evaluators.py`, `run_experiments.py` | the experiments the script runs: the randomised differential test, the mock evaluators, and the probe series |
| `ground_quotes.py`, `quote-grounding.json` | every sentence the paper quotes from a repository, located as a character span in the file at the pinned commit |
| `build/` | `build.sh` makes the HTML and the PDF (pandoc and a Chromium-family browser); `build_docx.py` makes a Word file |

## Checking the paper

```
bash reproduce.sh historical /tmp/wamte
```

needs a POSIX shell, git and Python 3.10 or later, and ends with the resolved commit hashes and
one output file per experiment. The numbers the paper states are in `audit/published/`; a run
that differs from them is a finding, and I would like to hear of it.

Everything the paper quotes from a repository is re-derivable:

```
python3 ground_quotes.py path/to/loomground path/to/loomground-ref paper.md
```

## Versions

`v1.0.0` is the version circulated for technical feedback (tag `whether-an-action-may-take-effect/v1.0.0`).
