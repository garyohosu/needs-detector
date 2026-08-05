# needs-detector

顧客の実際の課題を、AIによる仮説生成と人間インタビューで検証するオフラインCLIです。
AIだけで市場成立やCustomer Problem Fit（CPF）を断定しません。事実、引用、仮説、推論、AI補完を分離し、現実の顧客の過去の具体的行動を重視します。

## 対応環境とインストール

- Python 3.12以上
- Windows 11、Linux/WSL2
- 外部APIなしでMockとManual LLMを利用可能

wheelからインストールする場合:

```bash
pip install needs_detector-0.2.0-py3-none-any.whl
```

開発環境:

```bash
pip install -e .[dev]
```

## 最短の合成デモ

次のDataset Aは機能確認用の合成データです。実際の顧客検証、CPF確立、市場成立の証明ではありません。

```bash
needs-detector init demo-project
cd demo-project
needs-detector draw --provider mock --fixture-key dataset_a
needs-detector explore --provider mock --fixture-key dataset_a
needs-detector interview-guide --provider mock
needs-detector status
needs-detector doctor
needs-detector next
```

実インタビューなしで`learn`はHuman Gateにより停止します。合成データを試す場合も、実顧客検証済みとは表示されません。再現手順は[`examples/synthetic-demo/README.md`](examples/synthetic-demo/README.md)にあります。

## Manual LLMの完全手順

Manualでは各要求に固有の`job_id`が発行され、`manual_prompts/index.yaml`と`manual_prompts/<job_id>/request.json`に保存されます。回答JSONには台帳の`job_id`、`prompt_used`、必要な`target`を含めてください。

```bash
needs-detector draw --provider manual
# requestを外部LLMへ渡し、回答を response-draw.json として保存
needs-detector import-llm-response response-draw.json

needs-detector explore --provider manual
needs-detector import-llm-response response-explore.json

needs-detector interview-guide --provider manual
needs-detector import-llm-response response-guide.json

needs-detector add-interview interview-01.md --data-classification real
needs-detector add-interview interview-02.md --data-classification real
needs-detector learn --provider manual
needs-detector import-llm-response response-learn-01.json
needs-detector import-llm-response response-learn-02.json
```

複数インタビューでは全対象回答が揃うまでStep 4は`waiting_llm`です。`job_id`、対象、引用行番号が登録情報・原文と一致しない回答は取り込みません。

## 実インタビュー運用

- 録音、匿名化、記録方法について事前に同意を得る。録音は明示的な許可を取る。
- 氏名、会社名、連絡先などの個人情報を不用意に記録しない。
- 「最後にその問題へ直面したのはいつか」「実際に何をしたか」「時間・金額・代替品・不満」を聞く。
- 「このサービスを買うか」「使いたいか」という未来の意思は証拠にしない。
- `--data-classification real`は実データを扱う場合だけ指定する。
- `add-interview`は原文を`interviews/raw/<id>.md`へ改変せず保存し、derived YAMLへ`source_file`とSHA-256を記録する。raw原文を後から編集・削除するとdoctorが不整合を検出する。
- レポートの引用`[interviews/raw/<id>.md:L3]`は、そのrawファイルの指定行を開いて確認する。legacy YAMLは`source_file`なしのwarningとして読み込む。
- real、synthetic、unknownが混在するプロジェクトは`mixed`となり、実顧客検証済みとは扱わない。

## 主なコマンド

| コマンド | 用途 |
|---|---|
| `init` | プロジェクト作成 |
| `add-idea`, `add-source` | アイデア・資料登録 |
| `draw`, `explore`, `interview-guide`, `learn` | 4工程の実行 |
| `add-interview` | 匿名化済み記録の登録。区分はreal/synthetic/unknown |
| `import-llm-response` | Manual回答の検証・取込 |
| `status` | 工程状態とデータ区分の表示 |
| `doctor [--json]` | 構文、状態、引用、パス、ジョブの診断 |
| `next [--json]` | 次に実行すべき操作を最大3件表示 |
| `report` | 現在の成果物から最終レポート生成 |

`completed`は工程の実行完了を意味し、販売可能性や市場成立を保証しません。`mixed`、`synthetic`、`unknown`はいずれも実顧客検証済み・CPF確立とは表示されません。

## ディレクトリ構成

```text
project/
  project.yaml
  idea.md
  sources/index.yaml
  personas/*.yaml
  alternatives/alternatives.yaml
  interviews/*.yaml
  manual_prompts/index.yaml
  reports/
```

## エラー時の確認

まず`needs-detector doctor --json`を実行し、`errors`、`warnings`、`next_actions`を確認してください。特に`project.yaml`、`sources/index.yaml`、引用の行番号、Manual台帳の`job_id`と`target`、レポートの古さを確認します。

## 開発・配布確認

```bash
py -m pytest -o pythonpath=src tests/ -v
py -m pytest -o pythonpath=src tests/ --cov=src/needs_detector
py -m pytest -o pythonpath=src tests/integration/test_wheel_packaging.py -v
```

wheelはFixture、テンプレート、合成デモ手順を含め、リポジトリ外かつインストール先だけを参照してCLIを検証します。

## 現在の制限事項

- 外部LLM API連携は未実装です。Manualでは利用者が別のLLMへプロンプトを渡します。
- 音声・PDFの直接解析、CRM、自動連絡は対象外です。
- CPFは証拠整理の補助であり、AIや人数だけで市場を証明しません。
