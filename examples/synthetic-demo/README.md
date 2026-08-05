# Synthetic demo（合成データ）

この手順はインストール後の機能確認専用です。Dataset A/BとMockのインタビュー結果は架空であり、実際の顧客検証、CPF、市場成立を証明しません。

```bash
needs-detector init synthetic-demo
cd synthetic-demo
needs-detector draw --provider mock --fixture-key dataset_a
needs-detector explore --provider mock --fixture-key dataset_a
needs-detector interview-guide --provider mock
needs-detector status
needs-detector doctor --json
needs-detector next --json
```

実顧客へインタビューする場合は、`templates/real-pilot/`を使い、匿名化済み記録を`--data-classification real`で登録してください。
