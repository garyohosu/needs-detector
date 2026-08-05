# Public Issue Observation: 長時間タスクの進捗・チェックポイント

- Data classification: unknown
- Sources: openai/codex#32001, #35801; google-gemini/gemini-cli#22323, #28036
- Observations: 中間進捗が見えない、MAX_TURNSがsuccessとして返る、resume後に途中停止してcontinue入力が必要という事例がある。
- Direct quotes: “it executes for a long time internally and only presents the final result” / “Entering `continue` resumes the same task temporarily”
- Interpretation: 状態を表示し、未完了・制限到達・再開可能を区別するcheckpoint UIが必要な可能性。
- Unknown: どの状態表示が復旧判断に有効か、作業損失の大きさ。
