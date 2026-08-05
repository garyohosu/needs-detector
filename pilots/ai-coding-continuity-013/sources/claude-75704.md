# Public Issue Observation: background task中断

- Source: anthropics/claude-code#75704
- Event: 実行中に新しいmessageを送るとbackground taskが終了し、partial outputが保存されなかった。
- Workaround: unknown。再実行が示唆される。
- Impact: 長時間multi-agent jobを失ったと報告。
- Short quote: “no partial output is saved”
- Interpretation: interruptionをcheckpointに変える必要性を支持する。
- URL: https://github.com/anthropics/claude-code/issues/75704
