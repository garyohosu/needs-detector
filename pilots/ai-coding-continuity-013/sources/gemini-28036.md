# Public Issue Observation: resumed sessionの停止

- Source: google-gemini/gemini-cli#28036
- Event: resumed sessionが長いmulti-step taskの途中で止まり、`continue`入力で一時的に進んだ。
- Workaround: `continue`、terminate/restart、新しいsession。
- Impact: 手動再開が必要で、長いtaskほど目立つと報告。
- Short quote: “Entering `continue` resumes the same task temporarily”
- Interpretation: resume後の明示的状態通知と自動継続へのニーズを支持する。
- URL: https://github.com/google-gemini/gemini-cli/issues/28036
