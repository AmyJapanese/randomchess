# Random Chess (Tkinter)

Python + Tkinterで動くチェス実装。  
通常チェス（固定初期配置）に加えて、Random Chess（下4段=白 / 上4段=黒でランダム配置）を生成して遊べます。

## Features

- Tkinter GUI（クリック操作）
- 通常初期配置（Standard）
- Random Chess初期配置生成
  - 白：下4段（row 4〜7）に16駒をランダム配置
  - 黒：上4段（row 0〜3）に16駒をランダム配置
  - 初期チェックなし、両者が1手以上指せることを保証
  - （任意）白の「初手メイト-in-1」を禁止
- 合法手判定（自分キングがチェックになる手は表示されない）
- チェック表示、チェックメイト判定、ステイルメイト判定（Draw）
- FEN対応（読み込み・書き出し）
  - 盤面 / 手番 / キャスリング権 / アンパッサンまで対応
- 特殊ルール
  - キャスリング（通常チェス想定の権利文字KQkqをサポート）
  - アンパッサン
  - ポーン昇格（暫定で自動クイーン）

## Requirements

- Python 3.10+（推奨：3.11+）
- 標準ライブラリのみ（Tkinter同梱）

## Run

```bash
python main.py
````

## Controls

* 駒をクリック → 合法手がハイライト
* 移動先をクリック → 移動
* 終局（Checkmate / Draw）後は盤クリックが無効になります

## FEN

GUIのFEN欄に入力して `Load` で局面を読み込みできます。
`Copy` で現在局面のFENをクリップボードにコピーします。

### Example (checkmate position)

```
7k/6Q1/7K/8/8/8/8/8 b - - 0 1
```

## Random Chess Notes

* Random Chess生成ではキャスリングは無効（castling="-") です
  ※ ランダム配置だと通常のキャスリング前提（キングe列、ルーク角）が崩れるため

## Project Structure

* `main.py` : 起動用（ハブ）
* `gui.py`  : Tkinter GUI
* `board.py`: 盤面データ、合法手フィルタ、チェック/メイト判定、FEN、Random生成
* `piece.py`: 駒の動き（候補手生成）、攻撃マス判定（チェック判定用）

## Known Limitations / TODO

* ポーン昇格は自動でクイーン（選択式は未実装）
* halfmove/fullmove はFENで固定値（0 1）
* Random Chess用のキャスリング（Chess960的ルール）は未対応
* 盤の見た目（テーマ/配色/駒画像）は今後改善可能