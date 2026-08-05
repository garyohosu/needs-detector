# instruction-2026-08-05-012 操作実験記録

- 実施日時: 2026-08-05 19:22 JST
- 実行方式: 1つのAI・1セッション
- 対象コミット: 9a6ed382bb0f97d0a95033d39a011a886cee4ebc
- 実験用ルート: `C:\Users\garyo\AppData\Local\Temp\needs-detector-operation-012`
- 入力データ: すべて合成データ。実在の個人名、会社名、連絡先、顧客情報は未使用

## 実行環境

- Python: `Python 3.12.10`
- wheel: `needs_detector-0.2.0-py3-none-any.whl`
- wheel SHA-256: `7154007abeda982a6303f52728931edf6d7e87f8a3ca58117fbf498086a6d44c`
- venv: `C:\Users\garyo\AppData\Local\Temp\needs-detector-operation-012\venv`
- インストール先: venv の `Lib\site-packages`
- import元: `...venv\Lib\site-packages\needs_detector\__init__.py`

## 実験1: wheelインストール

リポジトリ外の一時ディレクトリから次を実行した。

```text
py -3.12 --version                         # exit 0
py -3.12 -m pip wheel . --no-deps --wheel-dir <temp>\build  # exit 0
py -3.12 -m venv <temp>\venv                # exit 0
<temp>\venv\Scripts\python.exe -m pip install <temp>\build\needs_detector-0.2.0-py3-none-any.whl  # exit 0
<temp>\venv\Scripts\needs-detector.exe --help  # exit 0
```

wheelは正常に作成・導入できた。依存パッケージはwheelの通常の依存解決で導入され、CLIはリポジトリ外のカレントディレクトリから起動した。`pip show` のLocationもvenv内であり、リポジトリの `src` は参照していない。

主要コマンド（`init`, `add-idea`, `add-source`, `draw`, `explore`, `interview-guide`, `add-interview`, `learn`, `report`, `status`, `import-llm-response`, `doctor`, `next`）がhelpに表示された。

## 実験2: 合成デモ

実行コマンドと終了コード:

```text
needs-detector init synthetic-demo-012                         # 0
needs-detector draw --provider mock --fixture-key dataset_a    # 0
needs-detector explore --provider mock --fixture-key dataset_a # 0
needs-detector interview-guide --provider mock                # 0
needs-detector status                                          # 0
needs-detector doctor --json                                    # 0
needs-detector next --json                                     # 0
```

生成された主要ファイル:

- `project.yaml`
- `personas/persona_p_a.yaml`
- `alternatives/alternatives.yaml`
- `interviews/guide.md`
- `sources/index.yaml`
- `reports/ai_completions.yaml`
- `reports/mock_fixture_audit.yaml`
- `manual_prompts/index.yaml`

`status` は `step1_draw=completed`, `step2_explore=completed`, `step3_listen=in_progress`, `step4_learn=unstarted`、データ区分 `synthetic` を表示した。`doctor --json` と `next --json` はPythonのJSON parserでparseでき、前者は `warning` と「実顧客検証ではありません」を表示し、後者は実顧客インタビューと匿名化記録の登録を次手として表示した。CPF確立、市場成立、実顧客検証済みという表示はなかった。

## 実験3: Human Gate

インタビュー未登録の合成デモで次を実行した。

```text
needs-detector learn --provider mock  # exit 1
```

標準エラーには `Error: No interviews found. Cannot proceed to Learn phase.` が出た。実行後もstatusは変わらず、`step4_learn=unstarted` のままだった。既存の生成物も破損せず、`doctor --json` はwarning、`next --json` は実顧客インタビューと匿名化記録の登録を表示した。実顧客検証済みへの誤遷移はない。

## 実験4: Manual LLM待機

別プロジェクトで次を実行した。

```text
needs-detector init manual-demo-012       # 0
needs-detector draw --provider manual     # 0
needs-detector status                     # 0
needs-detector doctor --json              # 0
needs-detector next --json                # 0
```

`manual_prompts/index.yaml` と `manual_prompts/<job_id>/request.json` が生成された。job_idは `550c63ba-ae7b-4552-a014-fed0e8da98f7`、requestには `prompt_used=draw_persona`、対象、応答形式（`content` と `ai_completions`を含むJSON）が記録された。statusは `step1_draw=waiting_llm`、データ区分は `unknown` で、完了扱いではない。`next --json` は同job_idを含む `import-llm-response` コマンドを提示した。

## 実験中の操作上の記録

最初の合成デモ試行では、PowerShellの補助関数で予約済みの引数変数名を使ったためCLIへ引数が渡らず、helpが7回表示された。これは実験ハーネスの操作ミスであり、アプリの不具合ではない。補助関数を修正して同じプロジェクトを再実行し、上記の実験結果を得た。

## 利用者視点の評価

### 事実

- READMEに記載されたwheel導入後のCLI起動は、リポジトリ外で成立した。
- 合成デモ、診断、Human Gate、Manual待機の主要コマンドは、指定された順で実行できた。
- synthetic/unknownのデータ区分と、実顧客インタビューが必要な状態は表示された。
- Human Gate停止後も状態と生成物は維持された。

### 所感・改善候補

- `doctor --json` の `next_actions` が空配列で、warningはあるものの具体的な次操作は `next --json` に委ねられている。利用者は `next` まで実行すれば案内を得られるが、診断単体での誘導としては改善余地がある。重大度は `MINOR` とする。
- Human Gateのエラー文は原因を説明するが、標準出力の案内ではなく標準エラーだけである。`next` を続けて実行すれば安全な行動が分かるため、今回の再現可能なBLOCKER/MAJORとは判定しない。
- `status` のPython dict形式出力は機械利用には不向きだが、今回の指示でJSONが必要な場面では `doctor --json` / `next --json` が利用できるため、`OBSERVATION` とする。

## テスト・再検証

今回コード修正は行っていないため、修正時必須の回帰テストは該当しない。wheel作成、wheel導入、リポジトリ外CLI、JSON parse、合成デモ、Human Gate、Manual待機を上記の通り実行した。
