# Manual pre-push checklist

1. Create the destination repository with PRIVATE visibility before any push.
2. Select branch `final-verification` and verify the private destination.
3. In the source-control client, untrack already-tracked blocker folders while retaining local copies: `experiments/phase3b/pilot_run_v1/`, `experiments/phase4/jbb_pilot_run_v1/`, and `experiments/local-runs/canary-devtest/`.
4. Also untrack any local raw-run outputs, `SecureLLM.zip`, local databases, model weights, and credential files that are already tracked.
5. Rescan the full proposed change with the publication audit; verify each listed exclusion and ignore pattern.
6. Review all BLOCKER and WARN findings, absolute paths, personal-data candidates, and third-party dataset terms.
7. Inspect the staged file list and final package; confirm no raw pilot or canary outputs are included.
8. Push only the reviewed files to the PRIVATE repository.
9. Review the remote file tree and access settings after the private push.
10. Make the repository public only after final review and explicit publication approval; repeat the scan immediately before changing visibility.
