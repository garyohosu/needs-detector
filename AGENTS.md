# Repository instructions

このリポジトリの正式な詳細規約は[`.agents/AGENTS.md`](.agents/AGENTS.md)です。

作業開始時は、`.agents/AGENTS.md`と、`instructions/`配下の最新の
`instruction-*.md`を必ず読み、その指示書に対応する`result-YYYY-MM-DD-NNN.md`
へ結果を記録してください。通常の技術判断では承認待ちせず、自律的に進めます。

実装担当と独立審査担当を分け、審査はコード・テスト・生成物を直接確認します。
審査は最大3サイクル（Cycle 4は禁止）です。必要なファイルだけをcommitし、
`origin/main`へのpushが成功した場合だけ作業をCOMPLETEDとします。
既存の未コミット変更は破棄・stash・無断上書きしません。
