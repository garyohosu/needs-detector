# Public Issue Observation: subagent再帰と損失

- Source: anthropics/claude-code#68619
- Event: subagentが深く再帰し、interrupt時に中間作業が失われ、tokenを大量消費したと報告。
- Workaround: 設定・権限を試したが制御できなかったと報告。
- Impact: tokenとsession limitの消費、作業損失。
- Short quote: “all intermediate work from every agent in the tree is lost.”
- Interpretation: 停止時の状態保存とbounded orchestrationへのニーズを支持する。
- URL: https://github.com/anthropics/claude-code/issues/68619
