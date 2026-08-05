# Agent A Review - instruction-010 Cycle 1

- 判定: REVISE
- 役割: 独立審査（実装ファイルは変更していない）

## 直接確認

- 正常add-source後のsource診断、indexのみのnext、path traversal拒否、raw保存、引用、混在分類の回帰テストを確認した。
- 41テスト中40件は成功したが、Windows環境でrawを`atomic_write`経由保存したため、入力LFがCRLFへ変換され、`source_sha256`が保存rawの実バイト列と一致しないことを実際に検出した。
- wheel配布試験のインストール先CLI拡張は一時的な文字列エスケープ不備で失敗した。

## 必須修正

1. rawは入力バイト列をそのまま保存し、そのバイト列でSHA-256を計算する。
2. wheelインストール後のadd-source、real interview、doctor、next、report試験を有効なスクリプトとして再実行する。
