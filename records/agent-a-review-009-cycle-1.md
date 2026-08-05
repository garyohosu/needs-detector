# Agent A Review - instruction-009 Cycle 1

- 判定: REVISE
- 役割: 独立審査（実装ファイルは変更していない）

## 直接確認

- root `AGENTS.md`、README、doctor/next、データ区分、テンプレート、合成デモを確認した。
- 35テスト中、通常テストは通過したがwheelのZIP検査でrootテンプレートと合成デモが配布物に入っていないことを実際に検出した。
- Mock Draw後のレポートが合成データの警告を出すことを確認したが、分類集計がインタビューだけを見ており、project.yamlのsyntheticをレポートへ反映していなかった。

## 必須修正

1. Hatchの`force-include`で`templates/`と`examples/`をwheelへ同梱する。
2. データ区分集計がプロジェクト設定のsynthetic/realを後方互換に参照する。
3. failed Manual job、request内容不一致、成果物全体を基準にしたstale reportもdoctor/nextで直接診断する。
