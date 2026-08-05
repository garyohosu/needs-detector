# TESTPLAN.md - needs-detector テスト計画書

- 文書版: v0.1
- 作成日: 2026-08-05
- 著者/役割: Agent A (設計・審査担当)
- 状態: MVP実装済み・審査PASS
- ベース仕様: `memo.md` (v0.1) & `DESIGN.md` (v0.1)

---

## 1. テスト方針・目的

`needs-detector` の品質保証のため、外部APIに依存しないオフラインテスト環境（Pytestベース）を中心に設計する。
全受け入れ条件 (AC-001 〜 AC-012) および主要機能要件・非機能要件を網羅するテストケースを定義する。

### 1.1 基本原則 (NFR-007)
1. **完全オフラインテスト可能**: CI環境で API キーがなくても全ユニット/統合テストが 100% 成功すること。
2. **モックLLMプロバイダーの活用**: `MockLLMProvider` を使用し、事前定義された出力データで再現性を担保する。
3. **安全なファイル操作の検証**: プロジェクト外ディレクトリへの不正アセス防止やアトミックファイル書き込みの検証。

---

## 2. テストレベルと構成

```text
tests/
├─ conftest.py              # Pytestフィクスチャ (一時ディレクトリ、モックプロバイダー等)
├─ unit/                    # 単体テスト (ドメインロジック、ポリシー)
│  ├─ test_evidence.py      # FR-005 根拠種別
│  ├─ test_question_checker.py # FR-031 誘導質問検出
│  ├─ test_anonymizer.py    # FR-034 匿名化スキャナー
│  └─ test_cpf_evaluator.py # FR-045 CPF評価ロジック
├─ integration/             # 統合テスト (ユースケース・ファイル操作・LLMアダプター)
│  ├─ test_file_repo.py     # NFR-006 ファイル保存・パス検証
│  ├─ test_human_gate.py    # FR-061 人間確認ゲート
│  └─ test_llm_providers.py # FR-070 LLMプロバイダー分離
└─ e2e/                     # CLIエンドツーエンドテスト (CLIコマンド連続実行)
   └─ test_cli_workflow.py  # AC-001~AC-008 フルワークフロー検証
```

---

## 3. 受け入れ条件 (Acceptance Criteria) とテストケース対応

| AC ID | 受け入れ条件 | テスト識別子 | テスト種別 | 検証方法・アサーション |
| :--- | :--- | :--- | :--- | :--- |
| **AC-001** | 初期化コマンドで空ディレクトリに必要構成を生成 | `test_cli_init_success` | E2E | `needs-detector init myproj` 実行後、`project.yaml` や `sources/` が正しく生成されるか確認 |
| **AC-002** | 四段階の実行（描く、探る、聴く、学ぶ） | `test_cli_full_workflow` | E2E | サンプルデータを用いて `draw` -> `explore` -> `interview-guide` -> `add-interview` -> `learn` を順次実行し、各成果物が生成されるか確認 |
| **AC-003** | インタビュー未登録時の未検証表示 | `test_unverified_status_without_interview` | Integration | インタビュー未登録状態で `learn` または `status` を実行した際、課題が「未検証/仮説」と評価され、Step 3完了が拒否されることを検証 |
| **AC-004** | レポートにおける根拠追跡 | `test_report_evidence_traceability` | Integration | 生成された `final_report.md` 内の主張に `[src_001.md]` や `[interview_001.md:L10]` 形式の参照が存在するかアサート |
| **AC-005** | AI補完表示 | `test_ai_completion_listing` | Unit | 入力資料に無い要素をLLMが補完した際、`ai_completions` リストに抽出されてレポート/成果物に一覧表示されるか確認 |
| **AC-006** | 誘導質問警告 | `test_leading_question_warning` | Unit | 「このサービスを使いますか？」を入力した際、`QuestionChecker` が警告フラグと修正案を返すことを検証 |
| **AC-007** | 反証優先抽出 | `test_refutation_priority_extraction` | Unit/Integration | インタビュー記録内の反証発言が `refutations` リストとして最優先でレポートに組み込まれるか検証 |
| **AC-008** | CPF評価 | `test_cpf_evaluation_levels` | Unit | 3つの評価軸 (実在課題, 最初の動く人, 代替品) について「未確認」「弱い」「一部確認」「強い」が正しくロジック判定されるか確認 |
| **AC-009** | オフライン試験 | `test_offline_mock_execution` | Integration | APIキー環境変数を削除した状態で Pytest を実行し、全テストが合格することを確認 |
| **AC-010** | 秘密情報保護 | `test_secret_and_git_exclusion` | Integration | 顧客実データディレクトリおよび `.env` が `.gitignore` に含まれているかチェック |
| **AC-011** | Windows対応 | `test_windows_path_compatibility` | Integration | パス区切り文字 (`/` と `\`) や UTF-8 エンコーディングが Windows 環境で正常に動作することを確認 |
| **AC-012** | エージェント分離 | `test_agent_records_existence` | Static Check | `records/agent-a-design.md`, `records/agent-b-implementation.md` 等のログファイル記録ルールの検証 |

---

## 4. 詳細テストケース仕様 (抜粋)

### 4.1 `test_leading_question_warning` (FR-031, AC-006)
- **目的**: 非推奨な誘導質問に対する検知・警告の動作確認
- **入力**:
  1. `"このサービスを使いますか？"`
  2. `"この機能があれば便利だと思いますか？"`
  3. `"最後にその課題に直面したのはいつですか？"` (正常系)
- **期待結果**:
  - 入力1, 2: `is_warning=True`、警告理由、修正提案 (例: 「過去の行動について質問してください」) を取得。
  - 入力3: `is_warning=False`。

### 4.2 `test_human_gate_step3_blocking` (FR-061, AC-003)
- **目的**: 実際の顧客インタビューが無いまま Step 3 を完了にできない安全制御の検証
- **前提条件**: Step 1, Step 2 を完了済みのプロジェクト。`interviews/` 内は空。
- **操作**: `needs-detector learn` コマンドを実行。
- **期待結果**: エラー `HumanGateError: インタビュー記録が1件も存在しないため、Step 3を完了してStep 4へ進むことはできません` が発生し、処理が中断されること。

### 4.3 `test_anonymizer_detection` (FR-034)
- **目的**: インタビュー取り込み時の個人情報自動検出スキャン
- **入力**: `"山田太郎 (yamada@example.com, 090-1234-5678, ABC株式会社) にインタビューを実施した。"`
- **期待結果**: 氏名("山田太郎")、メールアドレス("yamada@example.com")、電話番号("090-1234-5678")、会社名("ABC株式会社") が検出候補としてフラグ付けされること。

---

## 5. テスト実行手順とCI環境設定

### 5.1 ローカルでのテスト実行
```bash
# 依存関係のインストール
pip install -e .[dev]

# オフライン全自動テストの実行
pytest tests/ -v --cov=src/needs_detector

# CLI動作検証 (E2E)
pytest tests/e2e/ -v
```

### 5.2 CI (GitHub Actions 等) 設定基準
- 環境変数 `OPENAI_API_KEY`, `GEMINI_API_KEY` 等は未設定の状態で実行する。
- 実行コマンド: `pytest tests/`
- 合格判定基準: パス率 100%, 警告なし。
