# Public Issue Observation: コンテキスト圧縮と情報欠落

- Data classification: unknown
- Sources: anthropics/claude-code#73366; openai/codex#34656; google-gemini/gemini-cli#21792
- Observations: 誤った圧縮要求、compaction summaryのcross-tool import、長期sessionのcontext degradationが報告・提案された。#21792はclosed。
- Direct quotes: “I am using 0% context but it says that I must compact.” / “Long-running sessions often suffer from context degradation”
- Interpretation: 圧縮を単なる履歴短縮ではなく、状態・制約を保つ変換にする必要がある可能性。
- Unknown: 現行版での解決範囲、頻度、顧客価値。
