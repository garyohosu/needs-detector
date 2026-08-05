# Agent A Review - instruction-009 Cycle 2

- 判定: PASS
- 役割: 独立審査（実装ファイルは変更していない）

## 直接確認

- `AGENTS.md`は`.agents/AGENTS.md`と最新`instructions/instruction-*.md`への導線、承認待ち不要、最大3サイクル、commit/push規則を明記している。
- READMEの合成デモ、Manual job_id、Human Gate、real/synthetic/unknown、doctor/next、制限事項を実際のCLI手順と照合した。
- `doctor --json`は必須キーを持ち、正常プロジェクトはwarningのみで終了コード0、破損YAML・欠落source・引用不一致・Step矛盾はerrorと終了コード1になる。
- `next --json`はidea/source/工程/Manual waiting job_id・target・Human Gateを最大3件で提示し、doctor errorを最優先する。
- Mockプロジェクトのレポートに`データ区分: synthetic`と「実顧客検証ではない」警告が出ること、real登録はreal区分になることを直接確認した。
- request/response、failed job、未知target、重複job_id、AI補完参照、外部パス、stale reportをdoctorのコードで直接確認した。
- 実パイロットテンプレートは同意・匿名化・録音許可、改変しない発言、観察と解釈の分離、過去の具体的行動・時間・金額・代替品・不満を含む。
- wheel ZIPを直接検査し、Fixture、templates、examplesを確認。インストール先のみでhelp、init、doctor、next、Mock Drawを実行した。

## テスト

- `py -m pytest -o pythonpath=src tests/ -q`: 35 passed
- `py -m pytest -o pythonpath=src tests/ --cov=src/needs_detector -q`: 35 passed、TOTAL 65%
- `py -m pytest -o pythonpath=src tests/integration/test_wheel_packaging.py -v`: passed
- CLI smoke: `--help`, `init`, Mock Draw、`doctor --json`、`next --json`、`report`を実行
- 警告はpytest_freezegun由来の外部DeprecationWarningのみ

Cycle 1の指摘を修正し、Cycle 2で全必須項目を直接確認できたためPASSとする。Cycle 3/4は実施しない。
