# Public Issue Observation: shutdown後のsession loss

- Source: google-gemini/gemini-cli#27180
- Event: unexpected shutdown後にhistoryが失われ、resumeはsecond-to-last sessionへ戻った。
- Workaround: logsを調べたが完全復旧できなかった。
- Impact: contextを完全復旧できず、作業継続不能。
- Short quote: “the chat is lost forever”
- Interpretation: 端末障害に対する自動保存・復旧のニーズを支持する。
- URL: https://github.com/google-gemini/gemini-cli/issues/27180
