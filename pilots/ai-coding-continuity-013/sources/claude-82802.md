# Public Issue Observation: worktree再起動

- Source: anthropics/claude-code#82802
- Event: VS Code再起動後、worktree会話がsessionIDなしの空会話として復元された。transcriptはディスクに残っていた。
- Workaround: sessionIDと保存ファイルを手動調査。
- Impact: UI上で長時間作業が消えたように見える。
- Short quote: “Tab silently restores as a fresh empty conversation.”
- Interpretation: 保存データとUI参照の結合が脆い可能性を示す。
- URL: https://github.com/anthropics/claude-code/issues/82802
