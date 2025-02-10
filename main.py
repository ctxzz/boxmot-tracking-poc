import os
import sys
import subprocess

# 🔹 入力動画ファイルを定数で指定（videos/ フォルダ内）
VIDEO_FILE = "video.mp4"

def main():
    """BoxMOT の `track.py` を `main.py` から実行する。"""

    # プロジェクトのルートディレクトリ
    project_dir = os.path.dirname(__file__)

    # track.py のパス
    track_py = os.path.join(project_dir, "boxmot", "tracking", "track.py")

    # 必要なパスを PYTHONPATH に追加
    env = os.environ.copy()
    path_to_boxmot = os.path.join(project_dir, "boxmot")  # BoxMOTのルートディレクトリ
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = path_to_boxmot + ":" + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = path_to_boxmot

    # 使用するモデルと動画のパスを指定（相対パスを使用）
    yolo_model = os.path.join(project_dir, "yolov8n.pt")
    source_video = os.path.join(project_dir, "videos", VIDEO_FILE)

    # 出力ディレクトリ
    output_dir = os.path.join(project_dir, "runs", "track")
    
    # 🔹 拡張子を除いた動画ファイル名を取得
    output_name = os.path.splitext(VIDEO_FILE)[0]

    # トラッキングの設定 (自由に変更可能)
    tracking_method = "bytetrack"  # 例: "bytetrack", "deepocsort", "strongsort" など
    reid_model = "osnet_x1_0_msmt17.pt"  # 例: ReIDモデル (不要なら省略可)

    # 実行するコマンド
    command = [
        sys.executable, track_py,
        "--yolo-model", yolo_model,
        "--source", source_video,
        "--tracking-method", tracking_method,
        "--reid-model", reid_model,
        "--conf", "0.5",
        "--iou", "0.7",
        "--save-txt",  # 追跡結果を MOT 形式で保存
        "--project", output_dir,
        "--name", output_name,
        "--exist-ok",
        # "--classes", "0",  # 追跡するクラス (0: 人)
    ]

    print(f"[INFO] Running BoxMOT with command:\n{' '.join(command)}")

    # track.py を実行
    subprocess.run(command, check=True, env=env)

if __name__ == "__main__":
    main()
