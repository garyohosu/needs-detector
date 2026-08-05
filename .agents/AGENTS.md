# needs-detector Antigravity 常設運用規約

このファイルは、Antigravity がこのリポジトリで作業するときに常に従う運用規約である。
個別作業の内容は `instructions/` 配下の最新の指示書で与える。

## 1. 指示書

- 指示書は `instructions/instruction-YYYY-MM-DD-NNN.md` の形式で保存する。
- 作業開始時に `instructions/` を確認し、日付と連番が最も新しい指示書を読む。
- すでに完了した指示書を勝手に再実行しない。
- 個別指示と本規約が矛盾する場合は、安全側に停止し、`result.md` に質問を書く。

## 2. 作業開始前の必須手順

作業を始める前に、必ず次の順序で実行する。

1. `git status --short` で未コミット変更を確認する。
2. 未コミット変更がある場合は、破棄・上書き・stashを勝手に行わない。
3. 未コミット変更が安全に処理できない場合は作業を停止し、理由を `result.md` に追記する。
4. 作業ツリーが安全な状態であることを確認する。
5. `git pull --ff-only origin main` を実行し、リモートの最新状態を取得する。
6. pullに失敗した場合は作業を続行せず、エラー内容を `result.md` に追記する。
7. `memo.md`、最新の指示書、関連する設計書・テスト計画書を読む。

## 3. 作業中の原則

- 指示書にない大規模変更、仕様変更、依存追加、ファイル削除は行わない。
- 既存の人間または別エージェントの変更を勝手に破棄しない。
- `git reset --hard`、`git clean -fd`、force pushは禁止する。
- 不明点を推測で埋めず、必要なら `result.md` に質問を書いて停止する。
- 実装を伴う場合は、関連テストを作成または更新する。
- 作業途中で重大な失敗が起きた場合も、可能な範囲で `result.md` に記録する。

## 4. result.mdへの記録

各作業の終了時に、必ずリポジトリ直下の `result.md` へ追記する。
既存内容を消さず、末尾へ新しいセクションを追加する。

最低限、次を記録する。

```markdown
## YYYY-MM-DD HH:MM JST instruction-YYYY-MM-DD-NNN

- 状態: COMPLETED / BLOCKED / FAILED
- 担当: Antigravity
- 実施内容:
- 作成・変更したファイル:
- 実行したテスト:
- テスト結果:
- 未解決事項・質問:
- Gitブランチ: main
- push結果: SUCCESS / FAILED / NOT_EXECUTED
```

- 成功していない作業を `COMPLETED` と記載しない。
- テストを実施していない場合は、その理由を明記する。
- エラーや制約は省略せず記載する。

## 5. コミットとpush

作業と `result.md` の追記が完了したら、必ず次を行う。

1. `git status --short` と `git diff` で変更内容を確認する。
2. 必要なテストを実行する。
3. `result.md` に実施内容とテスト結果を追記する。
4. `git add` で今回の作業に必要なファイルだけをステージする。
5. 内容が分かるコミットメッセージでコミットする。
6. `git push origin main` を実行する。
7. pushに失敗した場合は成功扱いにせず、理由を `result.md` に記録する。

コミットメッセージの例:

```text
feat: add initial persona workflow

docs: refine design and test plan

test: add acceptance tests for project initialization
```

## 6. 画面上の応答

Antigravityの画面上の回答は短くてよい。
ただし、作業結果の正式な記録は必ず `result.md` とGit履歴に残す。

画面上では次だけを伝える。

- 完了または停止したこと
- 対象の指示書名
- `result.md` に記録したこと
- commit・pushの成否

## 7. 完了条件

次をすべて満たしたときだけ、作業完了とする。

- 最新の個別指示を満たした
- 必要なテストを実行した、または未実施理由を記録した
- `result.md` に結果を追記した
- 変更をコミットした
- `git push origin main` が成功した

pushが成功していない場合、作業状態は `BLOCKED` または `FAILED` とする。
