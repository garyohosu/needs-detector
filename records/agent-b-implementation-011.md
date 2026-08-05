# Agent B 実装記録: instruction-2026-08-05-011

## AutoLoop Cycle 1

- Agent: Codex (`gpt-5.6-sol`)
- 選択タスク: FR-034 法的種別付き日本語会社名候補の検出。
- AutoLoop receipt: `.runtime/receipts/cycle-001.json`
- Agent exit code: 0
- Controller decision: `continue`
- 固定検証: `[2, 1]`。専用cloneのglobal Python 3.13に`pydantic`が未導入だったため、全テストはcollection error、wheel試験はimport errorとなった。コード回帰のPASS証跡には使用しない。
- 初期実装: 株式会社・有限会社・合同会社を含む単一正規表現と株式会社の正例2件を追加。
- Cycle 1独立審査: `REVISE`。記録番号、pull失敗後継続、境界の過剰一致・検出漏れ、反証テスト不足、検証証跡の混同を指摘。

## Cycle 2修正

- `git pull --ff-only origin main`: 成功（Already up to date）。
- 今回のタスクを新しい`instruction-2026-08-05-011.md`へ分離し、完了済み010の未コミット追補を取り除いた。
- 会社名候補を法的種別の前後から抽出する保守的な規則へ変更した。
- ASCII・全角英数字、漢字、ひらがな、カタカナ、中黒、アンパサンド、ピリオド、法的種別間の空白を扱う。
- 既知の文脈接頭語、一般制度語、支店等の組織単位を除外し、全漢字で境界が曖昧な場合は部分候補を返さない。
- 株式会社・有限会社・合同会社の前置・後置、代表文字種、一般語、文脈、支店、部分一致の具体的テストを追加した。

## Cycle 2テスト

Python 3.12.10の専用`.venv`で実行した。

```text
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ -v
44 passed

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ --cov=src/needs_detector
44 passed / TOTAL 73% / anonymizer.py 96%

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/integration/test_wheel_packaging.py -v
1 passed

git diff --check
成功（改行変換warningのみ）
```

## Cycle 3修正とテスト

- Cycle 2独立審査: `REVISE`。一般制度文を逆向きの候補へ解釈する問題、通常文脈の巻き込み、法的種別の反対側から作る余計な候補、複数社名の欠落、弱い反証assertionを指摘。
- 法的種別の直後を見て前置型・後置型・候補なしのいずれかを一意に選び、同じ法的種別から両方向の候補を作らないよう修正した。
- 後置型では文脈接頭語・助詞と直前の別法人名を境界として扱い、複数社名を個別に抽出する。
- `担当者`等の役割語と`制度`等の一般語を商号として再解釈しない。
- 一般制度文、通常文脈、役割語、訪問動詞、複数社名は戻り値リスト全体を具体的にassertする反証テストへ変更した。

Python 3.12.10の専用`.venv`で再実行した。

```text
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ -v
44 passed

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ --cov=src/needs_detector
44 passed / TOTAL 73% / anonymizer.py 89%

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/integration/test_wheel_packaging.py -v
1 passed

git diff --check
成功（改行変換warningのみ）
```

## 変更ファイル

- `instructions/instruction-2026-08-05-011.md`
- `DESIGN.md`
- `QandA.md`
- `src/needs_detector/infra/scanners/anonymizer.py`
- `tests/unit/test_anonymizer.py`
- `records/agent-a-review-011-cycle-1.md`
- `records/agent-b-implementation-011.md`
- `result-2026-08-05-011.md`（最終審査後に作成）
