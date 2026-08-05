# Public Issue Observation: 利用量制限と再実行

- Source: anthropics/claude-code#79958
- Event: spend limitでdeep-researchが中断され、次回実行が最初から始まり途中成果物を使えなかった。
- Workaround: リセット後に同じskillを再実行。
- Impact: quotaを再消費し、成果物なしと報告。
- Short quote: “Re-invoking the skill starts a brand-new run.”
- Interpretation: durable checkpointと再開可能なrun stateへのニーズを支持する観察。
- URL: https://github.com/anthropics/claude-code/issues/79958
