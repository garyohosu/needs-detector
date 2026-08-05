# Public Issue Observation: 手作業の回避策と反証

- Data classification: unknown
- Sources: google-gemini/gemini-cli#3882, #21792, #22705; google-gemini/gemini-cli#28036
- Observations: chat history保存、context改善、checkpointingはIssueや設計として既に扱われ、一部Issueはclosed。一方、resume後にcontinueを手入力する回避策も報告された。
- Direct quotes: “Use checkpointing for versioning and restoring” / “Entering `continue` resumes the same task temporarily”
- Interpretation: 問題全体が未解決とは限らず、既存機能との差分と未充足部分を顧客に確認する必要がある。
- Unknown: closed Issueの実装効果、現行ユーザーの不満、再発率。
