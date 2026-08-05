# Final Report

データ区分: unknown
分類内訳: {'real': 0, 'synthetic': 0, 'unknown': 6}
警告: これは機能確認または仮説生成であり、実顧客検証・CPF確立・市場成立を示しません。

## 1. 初期アイデア
# AIコーディングCLIの作業継続性に関する問題仮説

## 対象者

Claude Code、Codex、Gemini CLIなどを複数併用し、個人または小規模チームで長時間の開発作業を行う人。

## 状況

利用量制限、コンテキスト圧縮、端末・アプリ再起動、サブエージェント利用、別CLIへの引継ぎが起きたとき。

## 起きていると考える問題

作業の目的、途中成果物、判断、未完了項目がセッション境界を越えて安全に引き継がれず、利用者が手動で再説明・再実行・復旧する必要がある。

## 既知の回避策

利用者は、同じプロンプトを再入力する、`continue` や `--resume` を試す、チャット履歴・ログ・git差分を探す、手動の計画・チェックポイント・状態ファイルを作る、別のCLIへ要約を貼り付けるなどで対処している。

## 今回まだ分からないこと

- どの失敗が最も頻繁で、どの程度の再作業を生むか
- 状態ファイルや要約を誰が継続的に保守できるか
- 複数CLI間で最低限共有すべき状態の形式
- 個人開発者が復旧機能へ時間または費用を払うか

## この仮説を棄却する条件

5人以上の実顧客インタビューで、直近の具体的な継続性事故がなく、既存の手動回避策で十分に短時間で復旧でき、繰り返し発生する負担も確認できない場合。


## 2. 入力資料と出典
- claude-68619.md (markdown)
- claude-73366.md (markdown)
- claude-75704.md (markdown)
- claude-79958.md (markdown)
- claude-82802.md (markdown)
- claude-83412.md (markdown)
- codex-19037.md (markdown)
- codex-31205.md (markdown)
- codex-32001.md (markdown)
- codex-32017.md (markdown)
- codex-34656.md (markdown)
- codex-35801.md (markdown)
- gemini-17758.md (markdown)
- gemini-21792.md (markdown)
- gemini-22323.md (markdown)
- gemini-22705.md (markdown)
- gemini-27180.md (markdown)
- gemini-27368.md (markdown)
- gemini-28036.md (markdown)
- gemini-3882.md (markdown)

## 3. 対象ペルソナ
[p_continuity] 複数CLIを使う個人開発者

## 4. ペルソナが置かれた状況
[p_continuity] 利用量制限、再起動、圧縮、または別CLIへの引継ぎをまたいで長時間の開発taskを続ける場面

## 5. 機能的ジョブ
[p_continuity] 目的、判断、途中成果物、未完了taskを次のsessionやCLIへ安全に引き継ぐ

## 6. 感情的ジョブ
[p_continuity] 作業を失った不安や再実行の徒労を減らす

## 7. 社会的ジョブ
[p_continuity] 小規模チームに進捗と判断根拠を説明できる

## 8. 阻害要因
[p_continuity] session固有の履歴、圧縮、利用量制限、subagent境界、CLIごとの状態形式

## 9. 現在の対処方法と不満
[p_continuity] --resumeやcontinueを試し、ログ、transcript、git差分、手動要約、checkpointを探す / 何が保存され、どこから再開できるかが一貫せず、失敗時に再実行範囲が分からない

## 10. 直接競合
- CLI内蔵のresume・session履歴: CLIごとに形式と保存境界が異なり、状態参照が失われる事例がある

## 11. 間接代替
- 手動のMarkdown、plan、git差分、checkpoint: 更新漏れと要約の陳腐化、手作業の負担
- ログ・transcript・チャット履歴の手動探索: sessionIDや索引が失われると見つけにくい

## 12. 無消費
- 作業を再実行し、同じpromptを再入力する: 途中成果物を失い、利用量と時間を再消費する

## 13. インタビューから得た事実と引用
(データなし)

## 14. 反証、CPF評価、AI補完部分
CPF評価:
cpf_evidence:
  current_alternative:
    alternatives_used:
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    - --resume、continue、再実行、手動要約、ログ・git差分探索
    continued_use_reason:
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
    dissatisfaction:
    - 手作業で状態を探す、または再実行する負担が報告・要望された
    - 手作業で状態を探す、または再実行する負担が報告・要望された
    - 手作業で状態を探す、または再実行する負担が報告・要望された
    - 手作業で状態を探す、または再実行する負担が報告・要望された
    - 手作業で状態を探す、または再実行する負担が報告・要望された
    - 手作業で状態を探す、または再実行する負担が報告・要望された
  first_mover:
    attempts:
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    - Issue本文に記録された回避策はあるが、購入・導入行動ではない
    money_spent:
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
    time_spent:
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
    - unknown
  real_problem:
    concrete_events:
    - 利用量制限で再実行が起きるIssue観察がある。token損失の一般化はしない。
    - 圧縮とcross-tool importのIssue観察がある。closed Issueの現行影響はunknown。
    - shutdownやresumeでsession参照を失うIssue観察がある。復旧率はunknown。
    - handoffとsubagent永続化のIssue観察がある。実顧客事実ではない。
    - 進捗不可視とresume後停止のIssue観察がある。実顧客頻度はunknown。
    - closed Issueがあり既存checkpoint機能の可能性がある。未解決性はunknown。
    frequency:
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    - 'unknown: 公開Issue件数は顧客頻度ではない'
    impact:
    - 'unknown: 実顧客の作業損失時間は未確認'
    - 'unknown: 実顧客の作業損失時間は未確認'
    - 'unknown: 実顧客の作業損失時間は未確認'
    - 'unknown: 実顧客の作業損失時間は未確認'
    - 'unknown: 実顧客の作業損失時間は未確認'
    - 'unknown: 実顧客の作業損失時間は未確認'
evaluations:
  current_alternative: 強い
  first_mover: 強い
  real_problem: 強い
AI補完:
(AI補完なし)

## 15. 未確認事項と次に確認すべきこと
- [p_continuity] 直近に作業を失った具体的な出来事は何か
- [p_continuity] 復旧のために実際にどのファイルやコマンドを使ったか
- [p_continuity] 再実行した作業と所要時間はどれくらいか
- [p_continuity] 複数CLIへ何を手動で渡したか

