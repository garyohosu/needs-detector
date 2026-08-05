# AIコーディングCLIの作業継続性: 最終ニーズレポート

## 1. Executive Summary

Claude Code、Codex、Gemini CLIの公式公開Issueを20件調査した。Issueは実顧客インタビューではなく、すべてunknownの公開観察である。

最も強い暫定仮説は、利用量制限・再起動・圧縮・agent境界をまたぐとき、目的・完了済み作業・成果物・未完了項目を再利用可能なcheckpointとして残し、同じ作業を最初から再実行せずに復旧できる仕組みへのニーズである。ただし頻度、時間損失、購入行動、支払意思は未確認であり、CPFや市場成立は断定しない。

## 2. 調査対象と方法

2026-08-05にGitHub公式APIで、`anthropics/claude-code`、`openai/codex`、`google-gemini/gemini-cli` のIssueを検索した。session/usage limit、context/resume、restart/recovery、handoff/subagent、checkpoint/progressを検索軸とし、Issue本文を読み、具体的な出来事と回避策が確認できるものを採用した。

主要URLは [証拠登録簿](evidence-register.md) に全件記載している。Issue本文は大量転載せず、短い引用と要約だけを保存した。

## 3. 収集した証拠の内訳

| リポジトリ | 件数 | open | closed |
|---|---:|---:|---:|
| Claude Code | 6 | 6 | 0 |
| Codex | 6 | 6 | 0 |
| Gemini CLI | 8 | 5 | 3 |
| 合計 | 20 | 17 | 3 |

反証・解決済み候補はGemini CLI #21792（continuity epic）、#3882（chat history保存）、#22705（checkpointing）。closedは現行で未解決である証拠ではなく、解決範囲と現在の効果はunknownとした。

## 4. 優先ニーズランキング

点数はIssue件数の単純集計ではなく、複数リポジトリにまたがる具体的な出来事、再実行・停止の影響、既存回避策、未解決性を相対評価した暫定値である。

### 1位: 利用量制限・再起動をまたぐ耐久checkpointと再開

**合計24/25**（観察5 / 広がり5 / 重大さ5 / 回避策5 / 未解決性4）。

根拠: Claude #79958, #83412、Codex #19037, #31205、Gemini #27180, #27368。limitで途中結果が親へ戻らず再実行になる、shutdown後にresumeできない、resume後にsession参照が消えるという異なる失敗がある。回避策はreset待ち、再dispatch、`--resume`、ログ探索で、いずれも手作業または再実行である。closedの保存・checkpoint Issueがあるため未解決性は満点にしなかった。

### 2位: 長時間タスクの進捗・終了状態・復旧範囲の可視化

**合計22/25**（観察5 / 広がり4 / 重大さ4 / 回避策5 / 未解決性4）。

根拠: Codex #32001, #35801、Gemini #22323, #28036、Claude #73366, #82802。中間進捗が見えない、MAX_TURNSが成功扱いになる、resume後に途中停止して`continue`が必要、空会話として復元されるという事例がある。利用者が「完了」「中断」「再開可能」を区別できないことが問題である。

### 3位: 複数CLI・親子agent間のportable handoff

**合計21/25**（観察5 / 広がり4 / 重大さ4 / 回避策4 / 未解決性4）。

根拠: Claude #68619, #83412、Codex #32017, #34656、Gemini #17758, #22323。中間作業の消失、parent/child要約handoffの要望、compaction summaryの誤import、subagentの再開不能・状態誤表示がある。手動要約や一つのtaskへの詰め込みが代替だが、形式の互換性と作業状態の真正性が未確認である。

## 5. 最重要問題仮説

複数のAIコーディングCLIを使う開発者は、利用量制限や再起動などでsessionが途切れたとき、作業の「何を目指し、何を確認し、何が終わり、何が残り、どの成果物を信頼してよいか」をportableなcheckpointとして復旧できず、手動の再説明・ログ探索・再実行を行っている。

支持証拠は #79958, #83412, #19037, #27180, #27368, #34656。反証・限定は、Gemini #21792, #3882, #22705がclosedであり、履歴保存やcheckpointが一部実装・統合済みの可能性があること。またCodex #32017は要望中心で事故件数を示さない。未確認なのは、実顧客の頻度、1回あたりの損失時間、回避策を継続するコスト、支払意思である。

## 6. 現在の代替手段・回避策

- 各CLIの`--resume`、履歴、session一覧を試す
- `continue`、reset待ち、再dispatch、同じpromptの再入力
- transcript、ログ、sessionID、git差分を手動探索
- Markdownのplan、状態ファイル、checkpoint、commitを手で更新
- 一つの長いtaskにまとめる、または別CLIへ要約を貼り付ける

これらは実際のIssue本文で報告・提案されたものだが、利用者の標準手順、所要時間、継続理由はunknownである。

## 7. 反証・すでに解決済みの事項

- Gemini #21792はcontinuityとcontext改善を扱うepicだがclosed。現在も同じ問題が残るとは言えない。
- Gemini #3882はchat history自動保存の要望でclosed。保存機能の現在の実装・効果は確認していない。
- Gemini #22705はcheckpointingでversioning/restoringする設計を記録しclosed。checkpointが既に存在する可能性がある。
- Claude #82802には、同じ再起動でも別worktree会話は正常復元したというcounter-exampleがある。問題は全session共通とは限らない。

したがって「全CLIで常に作業が失われる」とは結論しない。

## 8. 製品・機能仮説3案

### 案A: Portable Work Checkpoint（最有望）

- 対象場面: limit、再起動、圧縮、CLI切替の直前・直後
- 入力: goal、完了済み手順、検証結果、成果物パス、未完了task、source/session ID
- 出力: 人間可読Markdownと機械可読JSONのcheckpoint、再開用prompt、信頼度と未確認項目
- 既存回避策との差: 手動のplan・ログ探索を一つのportable schemaへまとめ、再実行範囲を明示する
- 最小実験: 5人に過去の中断taskを持参してもらい、checkpointから別CLIで再開する時間を測る
- 失敗判定: 5人中4人以上が状態を修正しないと再開できない、または手動再説明と同等以上の時間がかかる

### 案B: Limit-aware Pause / Resume Broker

- 対象場面: usage limitやturn limitが近い長時間task
- 入力: budget状況、task graph、最後の検証済みcheckpoint
- 出力: 停止理由、再開可能時刻、partial output、再開ボタンまたは別CLI向けhandoff
- 既存回避策との差: reset待ち後の再dispatchを最初から行わず、部分成果物を返す
- 最小実験: 過去のlimit事例を再現したfixtureで、部分成果物を保った再開と最初からの再実行を比較する
- 失敗判定: 利用者がpartial outputを信頼できない、または二重実行を防げない

### 案C: Cross-CLI Handoff Inspector

- 対象場面: Claude Code、Codex、Gemini CLI間で作業を引き継ぐとき
- 入力: transcript、compaction summary、git diff、plan、session metadata
- 出力: CLI非依存の要約、矛盾、欠落、未完了項目、次の質問
- 既存回避策との差: 要約の貼り付けだけでなく、出典と未確認状態を保持する
- 最小実験: 同一taskを3 CLIで引き継ぎ、重要制約と未完了項目の保持率を人間評価する
- 失敗判定: 重要な制約を落とす、または元transcriptより確認コストが増える

## 9. 実顧客インタビュー計画

対象者は、(1)個人開発で週1回以上AI CLIを使う人、(2)複数CLIまたはsubagentを併用する小規模チーム、(3)長時間task・予算/利用量制限・再起動を経験した開発者の3類型以上とする。Issue投稿者をそのまま顧客とは扱わない。

募集は、既存の開発者コミュニティ、個人開発者の知人紹介、OSS協力者、社内小規模チームから、まず各類型2人ずつ声をかける。最初の5人は、直近90日以内に具体的な中断・復旧・再実行を経験した人を優先する。

過去行動を聞く質問:

1. 最後にAIコーディング作業が止まったのはいつですか。
2. そのとき何を作っていましたか。
3. 止まる直前に完了していた作業は何ですか。
4. 何がきっかけでしたか。
5. 最初にどのコマンド、ファイル、履歴を確認しましたか。
6. 何を何回やり直しましたか。
7. 復旧まで何分・何時間かかりましたか。
8. 別のCLIや人へ何を渡しましたか。
9. 途中状態を残すために普段何を更新しますか。
10. 復旧できなかった情報は何ですか。
11. 同じ事故を避けるために手順やツールを変えましたか。
12. 直近に実際に時間・お金・手間を使った回避策は何ですか。

誘導を避けるため、製品案は最後まで提示せず、「使いたいか」「買いたいか」だけで判定しない。5面談後に、具体的な事故が3人以上、手動復旧または再実行が3人以上、各人が時間・作業・金銭のいずれかを実際に使ったことを確認できればContinue。確認できるが場面が分散すれば修正。具体的事故も回避コストもなければStopする。

## 10. Go / Continue / Stop基準

- Go: 5人中3人以上が直近の具体的事故を語り、3人以上が再実行・手動復旧を行い、同じcheckpoint欠落が再現する。
- Continue: 事故はあるが原因・対象CLI・最小状態形式が分散している。追加5人と1つの小実験へ進む。
- Stop: 5人中4人以上が具体的事故なし、既存回避策で短時間に復旧、またはclosed/既存機能で問題が解消済み。

## 11. 限界と未確認事項

公開Issueは自己選択された報告であり、頻度・市場規模・顧客代表性を示さない。投稿者の個人属性、支払意思、組織内意思決定、実際の復旧時間は集めていない。closed Issueの現在の実装効果も未確認である。

CLI生成レポートの内部CPF欄がunknown資料から強い評価を出しているため、そこからCPFを採用しない。今回のCPF判定は「未確認」。公開Issueだけでは実在課題の一部観察は得られるが、最初に動く人と現在の代替品への支出・継続理由は確認できない。

## 12. needs-detector生成成果物

- `project.yaml`: unknown、全Step completed
- `sources/index.yaml`: 20件
- `personas/persona_p_continuity.yaml`
- `alternatives/alternatives.yaml`
- `interviews/guide.md`
- `interviews/interview_*.yaml`: unknown観察6件
- `reports/learn_results.yaml`
- `reports/final_report.md`: CLI生成物。CPF強評価は採用せず、上記の最終判断で補正
- `manual_prompts/`: 9 jobのrequest/responseとimport履歴
