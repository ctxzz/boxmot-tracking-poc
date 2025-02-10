# boxmot-tracking-poc

## 概要
BoxMOT を使用した物体追跡の PoC プロジェクト。YOLO による物体検出とトラッキングを適用し、MOT 形式で結果を出力する。

## セットアップ

### 仮想環境の作成
```bash
uv venv --python 3.12
```

### 依存関係のインストール
```bash
uv sync
```

## 使い方

### 動画ファイルの指定
`main.py` 内の `VIDEO_FILE` を編集し、処理する動画を指定する。
```python
VIDEO_FILE = "video.mp4"
```
デフォルトでは `videos/video.mp4` を使用する。

### トラッキングの実行
```bash
uv run main.py
```

## トラッキングモデルの変更方法
BoxMOT では複数のトラッキングアルゴリズムを使用できる。以下の設定を `main.py` で変更することで、異なる手法を試すことができる。

### 1️⃣ トラッキング手法の変更
`tracking_method` を変更することで、異なるトラッキング手法を利用できる。
```python
tracking_method = "bytetrack"  # 例: "deepocsort", "strongsort", "ocsort"
```

### 2️⃣ ReID モデルの変更（必要な場合のみ）
ReID（外観特徴を使用した追跡）を変更する場合は、`reid_model` を適切なモデルに変更する。
```python
reid_model = "osnet_x1_0_msmt17.pt"  # 例: "resnet50_msmt17.pt"
```

### 3️⃣ YOLO モデルの変更
YOLO の検出モデルを変更する場合は、以下のように設定する。
```python
yolo_model = "yolov8n.pt"  # 例: "yolov8s.pt", "yolov8m.pt"
```

### 4️⃣ 追跡対象クラスの変更
デフォルトでは「人（クラス 0）」のみを追跡しているが、他のクラスを追加することも可能である。
```python
classes = "0"  # 例: "0 2 3"（人、自転車、車）
```

## トラッキング ID の修正

### 1️⃣ 修正用の CSV ファイルの作成
特定の ID を統合したい場合、`fix_trackID/` ディレクトリに CSV ファイルを作成する。

CSV ファイルの命名規則: `{動画名}.csv`
```bash
fix_trackID/video.csv
```

CSV の内容は、統合する ID を行単位で記述する。
```csv
1, 4, 59, 200
2, 50, 66, 299
```
上記の例では、`1, 4, 59, 200` を ID `1` に統合し、`2, 50, 66, 299` を ID `2` に統合する。

### 2️⃣ 修正スクリプトの実行
```bash
uv run fix_tracking.py
```
これにより、
- `runs/track/exp/labels/` 内の `.txt` ファイルが修正される
- 統合後の ID を反映したトラッキングデータが新しい `_fixed.txt` ファイルとして保存される
- CSV に含まれない ID は `_fixed.txt` に追加されない

### 3️⃣ 修正後の動画の生成
`fix_tracking.py` の実行後、修正後のトラッキングデータをもとに動画を作成する。
```bash
uv run fix_tracking.py
```

修正後の動画は `runs/track/fixed_videos/` に保存される。

## 出力

- **トラッキング結果**: `runs/track/exp/labels/` に `.txt` 形式で保存
- **修正後のトラッキングデータ**: `_fixed.txt` 付きのファイル
- **修正後の動画**: `runs/track/fixed_videos/` に `.mp4` 形式で保存