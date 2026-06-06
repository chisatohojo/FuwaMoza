# ふわもざ / FuwaMoza

ふわもざは、画像の任意の場所にモザイクまたはぼかしをブラシ感覚で追加できる Windows 向けの軽量画像加工アプリです。スクリーンショットや写真に写った個人情報、顔、ナンバープレート、不要な文字などをすばやく隠せます。

## 必要環境

- Windows
- Python 3.11 以降
- PySide6
- Pillow

## インストール

```bash
pip install -r requirements.txt
```

## 実行

```bash
python main.py
```

## 使い方

1. 画像をウィンドウにドラッグ＆ドロップするか、「開く」ボタンで読み込みます。
2. 効果を「モザイク」または「ぼかし」から選びます。
3. 太さと強さをスライダーで調整します。
4. 画像上に表示されるブラシ円を見ながら、クリックまたはドラッグして加工します。
5. 画面下部のステータスバーで、読み込み画像・現在の効果・太さ・強さ・保存結果を確認できます。
6. 必要に応じて Undo、クリアを使います。
7. 「保存」で元画像と同じフォルダに `_fuwamoza` 付きのファイル名で保存します。

保存例:

- `sample.png` -> `sample_fuwamoza.png`
- `photo.jpg` -> `photo_fuwamoza.jpg`
- `screenshot.webp` -> `screenshot_fuwamoza.webp`

同名ファイルがある場合は `_2`, `_3` のように連番が付きます。

## ショートカット

- `Ctrl + O`: 画像を開く
- `Ctrl + S`: 保存
- `Ctrl + Z`: Undo
- `Esc`: ドラッグ中の操作をキャンセル

## exe 化

推奨ビルド:

```bash
pyinstaller --clean FuwaMoza.spec
```

`FuwaMoza.spec` は exe のファイルアイコンに `assets/icon.ico` を指定し、実行時のウィンドウアイコン用に `assets/icon.png` も同梱します。

PowerShell からビルドスクリプトを使う場合:

```powershell
.\build_exe.ps1
```

コマンドで直接指定する場合:

```bash
pyinstaller --noconsole --onefile --name FuwaMoza --icon assets/icon.ico main.py
```

## アイコン設定

アプリのアイコンを差し替える場合は、`assets` フォルダ内のファイルを置き換えてください。

- `assets/icon.ico`: exe のファイルアイコンとウィンドウアイコンに優先使用されます。
- `assets/icon.png`: `icon.ico` がない場合のウィンドウアイコンとして使用されます。

`assets` フォルダがない場合は作成し、同じファイル名で配置してください。exe 化するときは、推奨の `pyinstaller --clean FuwaMoza.spec` を使うとアイコン素材も同梱されます。

## 注意事項

- 対応形式は PNG, JPG, JPEG, BMP, WEBP です。
- 保存時に元画像は上書きしません。
- 出力画像は元画像と同じ幅・高さ・画像形式で保存されます。
- アニメーション WEBP など複数フレーム画像は先頭フレームを対象にします。
- 編集後に新しい画像を開く、クリアする、アプリを終了する場合は未保存確認が表示されます。
