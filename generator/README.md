# コーディングエージェント設定ジェネレータ

`docs/` のセキュリティ・運用ガイドから、製品設定・コンテナ定義・受入テスト雛形・
ポリシーシートを生成する。Python 3.11+ 標準ライブラリのみ。

## 使い方
- 対話: `python generate.py --output ./generated`
- 再生: `python generate.py --profile profiles/examples/L2-team-both.json --output ./generated`
- 検証: `python generated/acceptance/selfcheck.py ./generated`

## テスト
`cd generator && python -m unittest discover -s tests`

## 注意
selfcheck は静的確認に過ぎない。実拒否は docs/15-acceptance-tests.md の受入テストで確認する。
レッドライン違反（docs/00）は既定で生成拒否。続行には --allow-redline-override と --approver。
