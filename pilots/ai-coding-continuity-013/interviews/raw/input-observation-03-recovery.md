# Public Issue Observation: クラッシュ・再起動後の復旧

- Data classification: unknown
- Sources: openai/codex#19037, #35801; google-gemini/gemini-cli#27180, #27368
- Observations: shutdown、renderer reload、resume後の索引処理でsessionが失われたり、空会話・chat listからの消失になった事例が報告された。
- Direct quotes: “A long-running Codex CLI session was lost and cannot be resumed.” / “the chat is lost forever”
- Interpretation: transcript本体だけでなくsession参照とcheckpointの復旧が必要な可能性。
- Unknown: 端末種別ごとの差、復旧率、現行版での解決。
