# ひなた記録 Streamlit 試作版

## 概要

スマホで開いて使う、支援記録の超ミニ試作です。

最初の機能：
- 職員名入力
- 利用者名入力
- 種別選択
- 開始ボタン
- 終了ボタン
- 録音ボタン風
- 報告メモ入力
- 記録案作成
- CSV保存

## Streamlit Community Cloudで使う流れ

1. GitHubに新しいリポジトリを作る
2. `app.py` と `requirements.txt` をアップロード
3. Streamlit Community Cloudでそのリポジトリを指定
4. Main file path に `app.py` を指定
5. Deploy

## 注意

この試作版では、まだ本物の音声録音・文字起こしは入っていません。
次の段階で、音声ファイルアップロードやWhisper連携を追加します。

個人情報を扱う場合は、公開設定・保存場所・アクセス制限に注意してください。
