# Public Issue Observation: セッション・利用量制限

- Data classification: unknown
- Sources: anthropics/claude-code#79958, #83412; openai/codex#31205
- Observations: 利用量やspend limitで長い処理が中断され、途中結果が親へ戻らず、リセット後に再実行される事例が報告された。
- Direct quotes: “No partial output or state is returned to the orchestrating session.” / “usage limits currently interrupt active coding work”
- Interpretation: 途中成果物の保存とreset後の再開が有望な問題仮説。
- Unknown: 発生頻度、典型的損失時間、支払意思、実顧客であること。
