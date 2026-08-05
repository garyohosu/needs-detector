# 公開GitHub Issue証拠登録簿

- 取得日: 2026-08-05 JST
- 取得方法: GitHub公式REST API（`/search/issues` と `/repos/{owner}/{repo}/issues/{number}`）
- 対象: 公式リポジトリのIssueのみ。投稿者名、メール、組織名は保存していない。
- 注意: Issueは公開観察材料であり、顧客インタビューではない。Issue件数から市場頻度は推定しない。

## 採用Issue

### Claude Code

- repository: `anthropics/claude-code`
- issue number: `79958`
- title: Deep-research workflow loses progress on token/spend limit, restarts from zero on resume
- URL: https://github.com/anthropics/claude-code/issues/79958
- created/updated: `2026-07-21` / `2026-07-30`
- state: open
- observed event: spend limitで二度中断され、再実行が最初から始まり、検証済みの途中成果物が利用可能な成果物にならなかったと報告。
- workaround: リセットを待って同じskillを再実行。
- impact: quotaを二度使い、最終成果物なしと報告。正確な金額はunknown。
- short quote: “Re-invoking the skill starts a brand-new run and repeats the entire fan-out from scratch.”
- theme: session・利用量制限 / checkpoint
- hypothesis: support
- unavailable: 投稿者属性、母数、再現率、支払意思

- repository: `anthropics/claude-code`
- issue number: `82802`
- title: VS Code worktree conversation restores as an empty conversation after restart
- URL: https://github.com/anthropics/claude-code/issues/82802
- created/updated: `2026-07-31` / `2026-08-04`
- state: open
- observed event: worktree内の会話を再起動するとsessionIDなしの空会話になった。ディスク上のtranscriptは残っていたがUIから見つけにくかった。
- workaround: 別の正常なsessionIDやディスク上のtranscriptを調べる。
- impact: 長時間作業がUI上で失われたように見える。時間損失はunknown。
- short quote: “Tab silently restores as a fresh empty conversation.”
- theme: restart・resume・state参照
- hypothesis: support
- unavailable: 投稿者属性、再現率、復旧所要時間

- repository: `anthropics/claude-code`
- issue number: `83412`
- title: Subagents die silently on spend/usage limit with no partial-result handoff
- URL: https://github.com/anthropics/claude-code/issues/83412
- created/updated: `2026-08-02` / `2026-08-02`
- state: open
- observed event: 利用量制限でsubagentが途中終了し、partial outputやstateが親へ戻らず、リセット後の再dispatchが最初からになった。
- workaround: リセットを待って同じtaskを再dispatch。
- impact: 同じ検証作業を複数回やり直したと報告。正確なtoken量はunknown。
- short quote: “No partial output or state is returned to the orchestrating session.”
- theme: multi-agent・利用量制限
- hypothesis: support
- unavailable: 投稿者属性、一般頻度、費用、支払意思

- repository: `anthropics/claude-code`
- issue number: `73366`
- title: Context compaction triggered incorrectly at 0% usage
- URL: https://github.com/anthropics/claude-code/issues/73366
- created/updated: `2026-07-02` / `2026-07-02`
- state: open
- observed event: 一度しかpromptを送っていないのにcompactionを要求されたと報告。
- workaround: 記載なし。
- impact: 早すぎる圧縮要求。作業損失はunknown。
- short quote: “I am using 0% context but it says that I must compact.”
- theme: context圧縮
- hypothesis: support
- unavailable: 原因、再現率、実害の大きさ

- repository: `anthropics/claude-code`
- issue number: `68619`
- title: Subagent recursion causes token burn and lost accumulated work
- URL: https://github.com/anthropics/claude-code/issues/68619
- created/updated: `2026-06-15` / `2026-07-22`
- state: open
- observed event: subagentが深く再帰し、interrupt時に中間作業が失われたと報告。
- workaround: 環境変数や権限設定を試したが、報告上は制御できなかった。
- impact: 数百万token級の消費とsession limit消費を報告。数値は投稿者報告で一般化しない。
- short quote: “all intermediate work from every agent in the tree is lost.”
- theme: multi-agent・安全な停止
- hypothesis: support
- unavailable: 母数、典型値、復旧率

- repository: `anthropics/claude-code`
- issue number: `75704`
- title: Interrupting a conversation terminates background tasks
- URL: https://github.com/anthropics/claude-code/issues/75704
- created/updated: `2026-07-08` / `2026-07-08`
- state: open
- observed event: 新しいmessageを送って作業へ文脈を追加すると、実行中background taskが終了しpartial outputが保存されなかった。
- workaround: 記載なし。再実行が示唆される。
- impact: multi-agent jobを失ったと報告。正確な損失時間はunknown。
- short quote: “no partial output is saved”
- theme: interruption・checkpoint
- hypothesis: support
- unavailable: 投稿者属性、一般頻度、金額

### Codex

- repository: `openai/codex`
- issue number: `19037`
- title: Session lost after battery shutdown and update
- URL: https://github.com/openai/codex/issues/19037
- created/updated: `2026-04-22` / `2026-06-21`
- state: open
- observed event: shutdownと更新後に長時間sessionをresumeできず、rolloutが保存されていなかったと報告。
- workaround: 記載された復旧策では戻らなかった。
- impact: session継続不能。時間損失はunknown。
- short quote: “A long-running Codex CLI session was lost and cannot be resumed.”
- theme: restart・復旧
- hypothesis: support
- unavailable: 投稿者属性、頻度、復旧時間

- repository: `openai/codex`
- issue number: `31205`
- title: Usage limits interrupt active coding work
- URL: https://github.com/openai/codex/issues/31205
- created/updated: `2026-07-06` / `2026-07-21`
- state: open
- observed event: usage limit到達でactive coding workの継続性が損なわれると報告。
- workaround: リセット後のresumeまたは再実行が示されるが、詳細はunknown。
- impact: 実行中作業の継続が不安定。時間・費用はunknown。
- short quote: “usage limits currently interrupt active coding work”
- theme: 利用量制限
- hypothesis: support
- unavailable: 具体的な再現条件、頻度、復旧時間

- repository: `openai/codex`
- issue number: `32001`
- title: Codex App no longer shows intermediate progress or checkpoints
- URL: https://github.com/openai/codex/issues/32001
- created/updated: `2026-07-10` / `2026-07-10`
- state: open
- observed event: 長いtaskの実行中に中間進捗が見えず、利用者にはblack boxのように見えると報告。
- workaround: 記載なし。
- impact: 停止判断や復旧判断が難しい。時間損失はunknown。
- short quote: “it executes for a long time internally and only presents the final result”
- theme: progress・checkpoint
- hypothesis: support
- unavailable: 実際の損失時間、頻度、支払意思

- repository: `openai/codex`
- issue number: `32017`
- title: Support parent/child task workflows with summarized handoffs
- URL: https://github.com/openai/codex/issues/32017
- created/updated: `2026-07-10` / `2026-07-14`
- state: open
- observed event: 長いprojectでmain threadと複数subtaskを分け、親子間で要約handoffしたいという要望。
- workaround: 一つのtaskに詰め込む、手動で要約する等のpartial workaround。
- impact: 手動の文脈管理が必要。時間損失はunknown。
- short quote: “Support parent/child task workflows with summarized handoffs”
- theme: handoff・multi-agent
- hypothesis: support
- unavailable: 実利用頻度、支払意思、実際の事故件数

- repository: `openai/codex`
- issue number: `34656`
- title: Claude Code session imports ignore compaction
- URL: https://github.com/openai/codex/issues/34656
- created/updated: `2026-07-22` / `2026-07-22`
- state: open
- observed event: 外部agentのcompaction summaryが通常messageとして取り込まれ、履歴が膨張してinput item limitを超えたと報告。
- workaround: 記載なし。import形式の修正が要望される。
- impact: cross-tool引継ぎ後のfollow-upが失敗し得る。時間損失はunknown。
- short quote: “External-agent session import treats Claude Code compaction summaries as ordinary user messages.”
- theme: cross-tool・context圧縮
- hypothesis: support
- unavailable: 発生頻度、利用者属性、復旧時間

- repository: `openai/codex`
- issue number: `35801`
- title: Desktop should survive renderer reloads with checkpointing and recovery
- URL: https://github.com/openai/codex/issues/35801
- created/updated: `2026-07-28` / `2026-07-28`
- state: open
- observed event: renderer reloadやblank windowでactive client stateが失われるリスクに対し、自動checkpointとrecoveryが要望された。
- workaround: サーバ保存済みの会話へ依存するが、active stateは別問題とされる。
- impact: active session状態の復旧不能リスク。数値はunknown。
- short quote: “automatically preserving and restoring the user's active session state”
- theme: checkpoint・復旧
- hypothesis: support
- unavailable: 実事故件数、頻度、支払意思

### Gemini CLI

- repository: `google-gemini/gemini-cli`
- issue number: `17758`
- title: Subagent Resumability & Persistence
- URL: https://github.com/google-gemini/gemini-cli/issues/17758
- created/updated: `2026-01-28` / `2026-08-05`
- state: open
- observed event: primary agentにはresume/persistenceがある一方、subagentを再起動後に継続・再利用したいという要望。
- workaround: primary agentの既存resume機能へ寄せる。
- impact: subagentの反復利用と作業継続が未充足。数値はunknown。
- short quote: “Ensure work isn't lost on restart”
- theme: subagent・永続化
- hypothesis: support
- unavailable: 実事故件数、頻度、支払意思

- repository: `google-gemini/gemini-cli`
- issue number: `21792`
- title: Epic: Improving Session Continuity and Coherence
- URL: https://github.com/google-gemini/gemini-cli/issues/21792
- created/updated: `2026-03-10` / `2026-05-05`
- state: closed
- observed event: 長期sessionのcontext degradationやforgotten constraintsを課題として整理したepic。
- workaround: 圧縮、状態ファイル、構造化context等の提案。
- impact: 問題領域がepicとして扱われたが、closedであるため一部は解決・統合済みの可能性がある。
- short quote: “Long-running sessions often suffer from context degradation”
- theme: context圧縮・反証/解決済み
- hypothesis: counterevidence_or_resolved
- unavailable: closedの意味、解決範囲、利用者成果

- repository: `google-gemini/gemini-cli`
- issue number: `3882`
- title: Automatically save chat history
- URL: https://github.com/google-gemini/gemini-cli/issues/3882
- created/updated: `2025-07-11` / `2026-04-04`
- state: closed
- observed event: chat historyの自動保存を求める要望。古いIssueで、closedのため製品側対応済みの可能性がある。
- workaround: 既存履歴や別CLIの保存に依存。
- impact: 保存の必要性を示すが、現行の未解決度はunknown。
- short quote: “I'd like Gemini to automatically record and save conversation histories”
- theme: 保存・反証/解決済み
- hypothesis: counterevidence_or_resolved
- unavailable: 現行実装、解決内容、利用者の現在の困りごと

- repository: `google-gemini/gemini-cli`
- issue number: `22323`
- title: Subagent recovery after MAX_TURNS is reported as GOAL success
- URL: https://github.com/google-gemini/gemini-cli/issues/22323
- created/updated: `2026-03-13` / `2026-08-05`
- state: open
- observed event: max turns到達で分析未実施なのに親にはsuccess/GOALとして返り、終了理由が矛盾したと報告。
- workaround: 親agentが手動探索を続けた。
- impact: 失敗を成功と誤認し、未完了作業を見逃すリスク。
- short quote: “the termination metadata is internally inconsistent”
- theme: subagent・進捗状態
- hypothesis: support
- unavailable: 発生頻度、損失時間、支払意思

- repository: `google-gemini/gemini-cli`
- issue number: `27180`
- title: Session loss during unexpected system shutdown
- URL: https://github.com/google-gemini/gemini-cli/issues/27180
- created/updated: `2026-05-17` / `2026-07-23`
- state: open
- observed event: unexpected shutdown後にchat historyが失われ、resumeは直前ではなくsecond-to-last sessionへ戻ったと報告。
- workaround: logsを調査したが完全復旧できなかった。
- impact: contextを完全復旧できず、作業継続不能。時間損失はunknown。
- short quote: “the chat is lost forever”
- theme: restart・保存
- hypothesis: support
- unavailable: 投稿者属性、頻度、復旧可能性の一般性

- repository: `google-gemini/gemini-cli`
- issue number: `27368`
- title: Latest chat session lost from /chat list after --resume
- URL: https://github.com/google-gemini/gemini-cli/issues/27368
- created/updated: `2026-05-22` / `2026-07-29`
- state: open
- observed event: `--resume`後の通常起動で最新sessionがchat listから消え、手順を繰り返して再現したと報告。
- workaround: 通常起動とresume起動を切り替えて確認。
- impact: session indexの破損または参照喪失。時間損失はunknown。
- short quote: “The most recent chat session is permanently gone from the /chat list.”
- theme: resume・索引
- hypothesis: support
- unavailable: 投稿者属性、全ユーザーへの影響、復旧時間

- repository: `google-gemini/gemini-cli`
- issue number: `28036`
- title: Resumed sessions repeatedly stop after partial execution
- URL: https://github.com/google-gemini/gemini-cli/issues/28036
- created/updated: `2026-06-19` / `2026-07-30`
- state: open
- observed event: resumed sessionが長いmulti-step taskの途中で止まり、明示的なerrorなしに`continue`を手動入力すると一時的に進んだ。
- workaround: terminate/restart、`continue`入力、新しいsession。
- impact: 手動再開が必要で、長いtaskほど問題が目立つと報告。
- short quote: “Entering `continue` resumes the same task temporarily”
- theme: resume・手動回避
- hypothesis: support
- unavailable: 正確な発生率、損失時間、支払意思

- repository: `google-gemini/gemini-cli`
- issue number: `22705`
- title: SDD: Use checkpointing for versioning and restoring
- URL: https://github.com/google-gemini/gemini-cli/issues/22705
- created/updated: `2026-03-16` / `2026-05-04`
- state: closed
- observed event: completed taskのcommitをplanと結び、checkpointでversioning/restoringする設計が記録された。
- workaround: git commitとplanの手動関連付け。
- impact: checkpointの実装・統合が進んだ可能性を示す。未解決度はunknown。
- short quote: “Use checkpointing for versioning and restoring”
- theme: checkpoint・反証/解決済み
- hypothesis: counterevidence_or_resolved
- unavailable: closed後の利用状況、実顧客の効果
