# thoughts

Papers by Felix Krone, each with what is needed to check it.

| Paper | Where | Citable version |
|---|---|---|
| *Whether an action may take effect* — a governance language for AI agents, and the conformance suite that tests it (2026) | [`whether-an-action-may-take-effect/`](whether-an-action-may-take-effect/) — `paper.pdf`, `paper.md`, `figures/` | tag `whether-an-action-may-take-effect/v1.0.0` |

To check a paper's numbers, run its one script from a clean directory; it clones the repositories at the commits the paper pins and reruns every experiment, and the outputs the paper reports sit beside it under `audit/published/`:

```
cd whether-an-action-may-take-effect && bash reproduce.sh historical /tmp/work
```

Text and figures: CC BY 4.0 (`LICENSE`). Scripts: Apache-2.0, stated in each file. Written with Loomground agents, using Claude and Codex as tools; I read and correct all of it.
