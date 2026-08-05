# Public Issue Observation: resume後のchat list

- Source: google-gemini/gemini-cli#27368
- Event: `--resume`後の通常起動で最新sessionがchat listから消える手順が再現した。
- Workaround: 通常起動とresume起動を切り替えて確認。
- Impact: session indexの参照喪失。
- Short quote: “The most recent chat session is permanently gone from the /chat list.”
- Interpretation: resumeが保存索引を壊さないことへのニーズを支持する。
- URL: https://github.com/google-gemini/gemini-cli/issues/27368
