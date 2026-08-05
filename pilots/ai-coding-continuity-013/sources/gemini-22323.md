# Public Issue Observation: MAX_TURNS状態誤表示

- Source: google-gemini/gemini-cli#22323
- Event: max turns到達で分析未実施なのにsuccess/GOALと返り、終了理由が矛盾した。
- Workaround: 親agentが手動探索を継続。
- Impact: 未完了作業を成功と誤認するリスク。
- Short quote: “the termination metadata is internally inconsistent”
- Interpretation: 状態と実成果物を照合するhandoffへのニーズを支持する。
- URL: https://github.com/google-gemini/gemini-cli/issues/22323
