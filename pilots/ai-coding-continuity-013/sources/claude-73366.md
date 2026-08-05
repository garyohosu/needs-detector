# Public Issue Observation: 誤った圧縮要求

- Source: anthropics/claude-code#73366
- Event: 一度のprompt後、context使用量0%なのにcompactを要求された。
- Workaround: unknown。
- Impact: 作業前の状態認識が不正確になる可能性。
- Short quote: “I am using 0% context but it says that I must compact.”
- Interpretation: contextメタデータの信頼性が継続性判断に影響する可能性。
- URL: https://github.com/anthropics/claude-code/issues/73366
