# Public Issue Observation: subagent利用量制限

- Source: anthropics/claude-code#83412
- Event: subagentが利用量制限で終了し、partial output/stateが親へ戻らず、リセット後も再dispatchが必要だった。
- Workaround: リセット後に再dispatch。
- Impact: 途中作業の再実行とtoken再消費。
- Short quote: “No partial output or state is returned to the orchestrating session.”
- Interpretation: multi-agentの中間成果物handoffとpause/resumeへのニーズを支持する。
- URL: https://github.com/anthropics/claude-code/issues/83412
