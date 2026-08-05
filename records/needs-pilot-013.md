# instruction-2026-08-05-013 実行記録

- 実施日: 2026-08-05 JST
- 実行者: 現在のCodexセッション（AutoLoopなし）
- Python: 3.12.10
- 対象プロジェクト: `pilots/ai-coding-continuity-013`
- 公開情報: GitHub公式REST APIで3公式リポジトリのIssueを取得
- 対象リポジトリ: `anthropics/claude-code`, `openai/codex`, `google-gemini/gemini-cli`

## AutoLoopについて

ユーザーの中断指示に従い、AutoLoopは再実行していない。唯一のController起動は専用cloneで `.gitignore` がdirtyと判定され、Agent開始前に `dirty_worktree` で終了した。製品コード、main作業ツリー、既存未追跡ファイルにはAutoLoop経由の変更を残していない。

## 検索方法

検索語は次の5群を使った。

- `session limit`, `usage limit`, `quota`
- `context compaction`, `memory`, `resume`, `continue`
- `crash`, `restart`, `lost state`, `recovery`
- `handoff`, `multi-agent`, `subagent`, `orchestration`
- `unfinished task`, `checkpoint`, `progress`, `state tracking`

GitHub Search APIで候補を取得し、Issue本文を直接読み、実際の出来事・回避策・影響が確認できるものを優先した。PR、Discussion、第三者記事、同一内容の重複は採用しなかった。Issueは顧客インタビューではなく、すべてunknown観察として扱った。

## 証拠件数

- 採用Issue: 20件
- Claude Code: 6件
- Codex: 6件
- Gemini CLI: 8件
- open: 17件、closed: 3件
- 反証・解決済み候補: Gemini #21792, #3882, #22705
- 各IssueのURL、日付、state、観察、回避策、短い引用、分類は `pilots/ai-coding-continuity-013/evidence-register.md` に記録した。

## 主要CLIコマンド

```text
needs-detector init ai-coding-continuity-013 --dir pilots                    # 0
needs-detector add-idea idea.md                                               # 0
needs-detector add-source <20件のIssue資料>                                   # 各0
needs-detector add-interview <6件の観察記録> --data-classification unknown    # 各0
needs-detector draw --provider manual                                          # 0
needs-detector import-llm-response <draw response>                            # 0
needs-detector explore --provider manual                                      # 0
needs-detector import-llm-response <explore response>                         # 0
needs-detector interview-guide --provider manual                              # 0
needs-detector import-llm-response <guide response>                           # 0
needs-detector learn --provider manual                                         # 0
needs-detector import-llm-response <6 learn responses>                         # 各0
needs-detector status                                                          # 0
needs-detector doctor --json                                                   # 0
needs-detector next --json                                                      # 0
needs-detector report                                                          # 0
```

Manual jobはdraw、explore、guide、learn 6件の計9件。job_id、prompt_used、targetをrequestとresponseで一致させ、外部LLM APIとMock fixtureは使っていない。

## CLI状態と問題点

最終statusは全Step completed、data classificationはunknown（real 0 / synthetic 0 / unknown 6）。doctorはerrorsなし、manual_jobs waiting=0、unknown警告。nextはreportを提示した。

CLI生成 `reports/final_report.md` はunknown資料を扱っているにもかかわらず内部のCPF評価欄を強いと表示する。公開IssueだけからCPFを確立できない指示と矛盾するため、最終ニーズレポートではこの評価を採用せず、CPFを未確認とした。これは今回の調査結果における重要な制限であり、製品コードは変更していない。

## 生成物

- `pilots/ai-coding-continuity-013/project.yaml`
- `idea.md`, `evidence-register.md`
- `sources/` のIssue資料20件と `sources/index.yaml`
- `interviews/raw/` の観察記録6件、`interviews/interview_*.yaml`
- `manual_prompts/` のrequest/responseとjob履歴
- `reports/final_report.md`, `reports/learn_results.yaml`
- `final-needs-report.md`
