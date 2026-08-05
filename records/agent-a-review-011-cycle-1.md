# Agent A 独立審査: instruction-2026-08-05-011 Cycle 1

- 審査対象: AutoLoop Cycle 1 / FR-034「法的種別付き日本語会社名候補の検出」
- 役割: 独立審査（実装、テスト、設計、QandA、resultは変更していない）
- 判定: **REVISE**

## 修正必須事項

### 1. 完了済み010へ別タスクを追補しており、結果記録の規約と一致しない

`.agents/AGENTS.md` は、完了済み指示書を勝手に再実行しないこと、個別指示と対応する result の番号を一致させることを求めている。`instruction-2026-08-05-010.md` は009の source、next、raw引用、分類、doctor是正を対象とし、既に Cycle 2 PASS、commit `e0a81a4`、push SUCCESSとして完了している。今回のFR-034会社名追加は010に定義された是正ではないため、既存の `result-2026-08-05-010.md` へ「追加実行」として記録する根拠がない。

追補専用の新しい instruction/result の組、または完了済み010への追補を明示的に許可する正本指示が必要である。010の既存完了記録は保持し、今回の未コミット追補を別タスクの記録へ移すこと。また、AutoLoopプロンプトどおりcommit/pushを禁止した実行について、リポジトリ全体の完了条件と混同して `COMPLETED` と記録しないこと。

加えて、AutoLoop実行時の `git pull --ff-only origin main` は `.git/FETCH_HEAD` の permission denied で失敗している。`.agents/AGENTS.md` はpull失敗時に作業を続行しないよう要求しているため、「安全に継続できる」と独自に上書きした扱いも是正が必要である。

### 2. 正規表現が通常文を会社名候補として過剰取得し、代表的な法的種別付き商号を検出漏れする

`src/needs_detector/infra/scanners/anonymizer.py` の文字集合と境界には次の再現可能な問題がある。

```text
「一般的な株式会社制度を説明する。」     -> ["株式会社制度"]
「顧客ABC株式会社へ連絡した。」          -> ["顧客ABC株式会社"]
「株式会社サンプル東京支店へ連絡した。」 -> ["株式会社サンプル東京支店"]
「株式会社はてなへ連絡した。」           -> []
「株式会社１２３へ連絡した。」           -> []
「株式会社 日本へ連絡した。」            -> []
「株式会社DMM.comへ連絡した。」          -> ["株式会社DMM"]
```

QandAとDESIGNは「依存追加なしの保守的な正規表現」「法的種別が明示された会社名」を選択しているが、現在の実装は会社制度の一般論まで候補化し、前後の説明語・支店名を商号へ取り込む一方、ひらがな、全角英数字、空白、ピリオドを含む実在し得る商号を未検出または部分検出にする。候補警告であるため完全なNER精度は不要だが、この境界を「誤検出を抑えた初期対象」としてPASSにはできない。

法的種別前後の取得境界と対応文字種を仕様化して実装を修正し、少なくとも株式会社・有限会社・合同会社の前置・後置、ひらがなまたは全角文字を含む代表例、一般語の「株式会社制度」、前後文脈の過剰取得、部分一致を回帰テストに追加すること。意図的に対象外とする表記は、設計と結果に限界を明記すること。

### 3. 追加テストだけでは実装上の主張を裏付けられない

`tests/unit/test_anonymizer.py` の新規assertionは、実際の戻り値に依存しており常時真になるno-opではない。既存URLの `A or B` も弱い許容ではあるが、両方偽になり得るためno-opではない。

一方、新規テストは株式会社の前置・後置各1件と、法的種別ではない単語「会社」だけを確認する。実装・QandA・resultが対応済みと述べる有限会社・合同会社、文字種の境界、過剰取得、部分一致を検証していない。負例「会社の課題」は法的種別パターンの誤一致をほとんど反証しない。上記境界ケースを、候補内容まで具体的にassertする必要がある。

### 4. AutoLoop固定検証と後続venv検証を分けて事実どおり記録する必要がある

`.runtime/receipts/cycle-001.json` は次を示す。

- agent exit code: 0
- verification exit codes: `[2, 1]`
- decision: `continue`
- 全テスト: global Python 3.13に`pydantic`がなくcollection error
- wheel試験: 同じく`pydantic`未導入で失敗

したがってAutoLoopの固定検証自体は成功していない。これは今回のコード回帰を示す失敗ではなく検証環境の依存未導入だが、receiptをPASS証跡として扱うことはできない。

その後作成された `.venv`（Python 3.12.10、依存導入済み）では、独立審査で次を直接再実行し、すべて成功した。

```text
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ -q
42 passed in 43.85s

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/ --cov=src/needs_detector --cov-report=term -q
42 passed in 55.11s / TOTAL 71%

.venv\Scripts\python.exe -m pytest -p no:cacheprovider -o pythonpath=src tests/integration/test_wheel_packaging.py -q
1 passed in 13.03s
```

`result-2026-08-05-010.md` の追補にある「全テスト未実施」「Python 3.12環境で未確認」は現在の証拠と一致しない。修正版の正しいresultには、(a) AutoLoop固定コマンドは依存未導入環境で失敗したこと、(b) 後続のPython 3.12 venvで全42件・coverage 71%・wheel単独試験が成功したことを、別々の証跡として記録すること。コード修正後は同じ3系統を再実行すること。

## 直接確認したその他の事項

- `git diff --check`: エラーなし（改行変換warningのみ）。
- 変更対象外の既存メール、電話、郵便番号、URL、IPv4検出は、全42テスト成功の範囲では回帰なし。
- AutoLoop receiptのchanged_filesと実際の差分は一致している。
- review以外の実装・テスト・設計・QandA・resultファイルは本審査で変更していない。

## 最終判定

**REVISE**。全回帰・coverage・wheelの後続venv検証は成功しているが、完了済み010への追補手順、正規表現の過剰一致・不足、テスト境界、resultの証跡記載を修正後に Cycle 2 再審査とする。
