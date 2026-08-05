# Public Issue Observation: 複数AI・サブエージェント間の状態共有

- Data classification: unknown
- Sources: anthropics/claude-code#68619, #83412; openai/codex#32017; google-gemini/gemini-cli#17758
- Observations: subagentの中間作業が失われる、親子taskの要約handoffが欲しい、subagentを再起動後も再開したいという報告・要望がある。
- Direct quotes: “all intermediate work from every agent in the tree is lost.” / “Ensure work isn't lost on restart”
- Interpretation: 複数agent間で検証済み事実・未完了task・権限を明示的に受け渡す状態形式が有望。
- Unknown: handoff対象の最小スキーマ、導入負担、顧客の支払意思。
