# Agent A 独立審査: instruction-2026-08-05-011 Cycle 2

- 審査対象: FR-034「法的種別付き日本語会社名候補の検出」Cycle 2差分
- 役割: 独立審査（実装、テスト、設計、QandA、instruction、resultは変更していない）
- 判定: **REVISE**

## Cycle 1指摘の解消確認

### 解消済み

- `instruction-2026-08-05-011.md` が作成され、今回のFR-034要件と010を変更しないことが明文化された。
- `result-2026-08-05-010.md` のGitオブジェクトIDは作業ツリーとHEADでともに `c5640b4d2205d4354452ccf5b41c537c1a305fc6` であり、内容上は010への追補が除去されている。
- `git pull --ff-only origin main` を独立審査でも直接実行し、`Already up to date.` で成功した。
- 株式会社・有限会社・合同会社の前置・後置、ひらがな、全角数字、法的種別との空白、ピリオドを含む正例は、対象テストと直接呼び出しで期待候補を返した。
- `顧客ABC株式会社` は `ABC株式会社`、`株式会社サンプル東京支店` は `株式会社サンプル` を返し、`株式会社DMM.com` は部分候補 `株式会社DMM` を返さないことを確認した。
- 既存メール、電話、郵便番号、URL、IPv4検出を含む全44テストは成功した。
- `records/agent-b-implementation-011.md` は、AutoLoop固定検証がglobal Python 3.13の依存未導入で `[2, 1]` となった事実と、後続Python 3.12 venvでの成功を分けて記録している。

### 未解消: 一般制度の反証テストが別方向の誤候補を見逃す

`tests/unit/test_anonymizer.py` は次だけを負にassertしている。

```python
assert "株式会社制度" not in res
```

しかし実際の戻り値は次であり、文全体が一般制度の説明であるにもかかわらず会社名候補が残る。

```text
Anonymizer.scan("一般的な株式会社制度を説明する。")
=> ["一般的な株式会社"]
```

`_scan_company_names()` が各法的種別について前置型と後置型を無条件に両方試すため、前置型の `株式会社制度` をgenericとして棄却しても、直前の「一般的な」を後置型商号として再解釈している。これは `instruction-2026-08-05-011.md` の「株式会社制度のような一般的制度説明を会社名候補として返さない」を満たさない。

新規assertionは構文上の常時真ではないが、禁止された入力に別の誤候補が残っても成功するため、この反証要件に対して実質的にno-opに近い。一般制度文では候補リストが空であること、または少なくとも法的種別を含む候補が一切ないことを具体的にassertする必要がある。

### 未解消: 通常文脈の過剰一致・双方向解釈・複数社名の検出漏れ

追加の直接確認で次を再現した。

```text
「今日はABC株式会社へ連絡した。」
=> ["今日はABC株式会社"]

「売却先のABC株式会社に確認した。」
=> ["売却先のABC株式会社"]

「ABC株式会社担当者へ連絡した。」
=> ["ABC株式会社", "株式会社担当者"]

「訪問した株式会社サンプルへ連絡した。」
=> ["訪問した株式会社", "株式会社サンプル"]

「ABC株式会社とXYZ有限会社」
=> ["ABC株式会社"]
```

既知の接頭語リストだけでは日本語文の前方境界にならず、前置・後置の両方を常に候補化するため反対側の一般語も会社名扱いする。また、同じ句内に別の法的種別があると `_normalize_company_name()` が全体を棄却し、2社目の `XYZ有限会社` を検出できない。

少なくとも次をCycle 3で修正・テストすること。

1. `株式会社制度` のように法的種別直後が明示的generic語の場合、直前文脈を後置型商号へ再解釈しない。
2. 前置型・後置型の反対側にある「担当者」や動詞を、別候補として返さない。
3. 一般的な助詞・句境界を越えて `今日は`、`売却先の` 等を後置商号へ取り込まない。
4. `ABC株式会社とXYZ有限会社` のような複数社名を個別に検出する。
5. 各反証では特定の誤文字列がないことだけでなく、戻り値全体または法的種別付き候補集合を具体的にassertする。

完全な日本語NERは要求しない。依存なしの初期実装として対象外にする曖昧表記は、正本設計に限界を明記し、誤った候補を返すより候補を省略する方針でよい。ただし、今回再現した通常文とinstructionの明示例は修正が必要である。

## result番号と検証証跡

新しいinstruction番号への分離はできているが、審査時点で `result-2026-08-05-011.md` は存在しない。このため、正本resultで010と分離されていること、およびAutoLoop固定失敗と後続venv成功を混同せず記録したことは未確認である。Cycle 3のコード修正・再検証後、011 resultを作成し、少なくとも次を別々に記録すること。

- AutoLoop receipt: agent exit 0、固定検証 `[2, 1]`、controller decision `continue`。依存未導入による失敗でありPASS証跡にはしない。
- Python 3.12 venvの再検証結果。コード修正後の実数、coverage、wheel単独試験を記録する。
- 独立審査のCycle 1/2/3各判定。
- commit/push前は`COMPLETED`としない。

## 独立再実行したテスト

Python 3.12.10の専用`.venv`で実行した。

```text
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/unit/test_anonymizer.py -vv
4 passed in 0.04s

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ -q
44 passed in 45.92s

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ --cov=src/needs_detector --cov-report=term -q
44 passed in 38.38s / TOTAL 73% / anonymizer.py 96%

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/integration/test_wheel_packaging.py -q
1 passed in 14.00s
```

全体回帰、coverage、wheel packagingは成功しているが、上記の未テスト仕様不適合を相殺しない。

## 最終判定

**REVISE**。Cycle 1の番号分離、Git同期、代表文字種、3法人種別、顧客接頭語・支店・ピリオド部分一致、検証環境の区別は改善した。一方、一般制度文の誤候補、前置・後置の双方向誤解釈、通常文脈の過剰取得、複数社名の検出漏れ、011 result未作成が残る。Cycle 3で修正し、再審査すること。Cycle 4は禁止する。
