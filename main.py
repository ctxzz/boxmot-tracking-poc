import os
import sys
import subprocess

def main():
    """BoxMOT の `track.py` を `videos/` フォルダ内のすべての mp4 ファイルに対して実行する。"""
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
    
    # YOLOモデルのパス
    yolo_model = os.path.join(project_dir, "yolov8n.pt")
    
    # 入力動画フォルダ
    video_dir = os.path.join(project_dir, "videos")
    
    # 出力ディレクトリ
    output_dir = os.path.join(project_dir, "runs", "track")
    os.makedirs(output_dir, exist_ok=True)
    
    # `videos/` フォルダ内のすべての mp4 ファイルを取得
    video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    
    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        output_name = os.path.splitext(video_file)[0]
        output_path = os.path.join(output_dir, output_name)
        
        # すでに処理済みならスキップ
        if os.path.exists(output_path):
            print(f"[INFO] Skipping {video_file}, already processed.")
            continue
        
        # トラッキングの設定
        tracking_method = "bytetrack"  # 例: "bytetrack", "deepocsort", "strongsort" など
        reid_model = "osnet_x1_0_msmt17.pt"  # 例: ReIDモデル (不要なら省略可)
        
        # 実行するコマンド
        command = [
            sys.executable, track_py,
            "--yolo-model", yolo_model,
            "--source", video_path,
            "--tracking-method", tracking_method,
            "--reid-model", reid_model,
            "--conf", "0.5",
            "--iou", "0.7",
            "--save",
            "--save-txt",  # 追跡結果を MOT 形式で保存
            "--project", output_dir,
            "--name", output_name,
            "--exist-ok",
            "--classes", "0",  # 追跡するクラス (0: 人)
        ]
        
        print(f"[INFO] Running BoxMOT on {video_file} with command:\n{' '.join(command)}")
        
        # track.py を実行
        subprocess.run(command, check=True, env=env)

if __name__ == "__main__":
    main()
