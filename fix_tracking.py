import os
import glob
import csv
import cv2
import numpy as np

def load_fix_map(csv_file):
    """CSVファイルを読み込み、IDの変換マップを作成"""
    fix_map = {}

    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            min_id = min(map(int, row))  # 最小の値を統合IDにする
            for track_id in map(int, row):
                fix_map[track_id] = min_id  # すべての値を最小値に統合

    return fix_map

def merge_tracking_ids():
    """トラッキング結果のIDを統合する"""
    video_dir = "videos"
    fix_track_dir = "fix_trackID"
    output_video_dir = "runs/track/fixed_videos"
    os.makedirs(output_video_dir, exist_ok=True)
    
    video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    
    for video_file in video_files:
        video_name = os.path.splitext(video_file)[0]
        tracking_dir = f"runs/track/{video_name}/labels"
        csv_file = os.path.join(fix_track_dir, f"{video_name}.csv")

        if not os.path.exists(csv_file):
            print(f"[WARNING] {csv_file} が見つかりません。IDの統合は行われません。")
            continue

        fix_map = load_fix_map(csv_file)
        txt_files = [f for f in glob.glob(os.path.join(tracking_dir, "*.txt")) if not f.endswith("_fixed.txt")]

        print(f"[INFO] {len(txt_files)} 件のトラッキングデータを処理中...")

        for i, file_path in enumerate(txt_files):
            fixed_path = file_path.replace(".txt", "_fixed.txt")

            if os.path.exists(fixed_path):
                print(f"[INFO] ({i+1}/{len(txt_files)}) すでに修正済み: {fixed_path}（スキップ）")
                continue

            with open(file_path, "r") as f:
                lines = f.readlines()

            modified_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 6:
                    class_id, x_center, y_center, width, height, track_id = parts
                    track_id = int(track_id)

                    if track_id not in fix_map:
                        continue

                    new_track_id = fix_map[track_id]
                    modified_lines.append(f"{class_id} {x_center} {y_center} {width} {height} {new_track_id}\n")

            if not modified_lines:
                print(f"[INFO] ({i+1}/{len(txt_files)}) 一致するIDなし: {file_path}（スキップ）")
                continue

            with open(fixed_path, "w") as f:
                f.writelines(modified_lines)

            print(f"[INFO] ({i+1}/{len(txt_files)}) 修正済み: {fixed_path} （{len(modified_lines)} 行）")

        create_fixed_video(video_name, fix_map, tracking_dir, output_video_dir)
    
    print("[INFO] トラッキングデータの修正が完了しました！")

def create_fixed_video(video_name, fix_map, tracking_dir, output_video_dir):
    """修正後のIDを使用して、元の動画にバウンディングボックスを描画し、トラッキングIDごとにマスク処理した動画も保存"""
    video_dir = "videos"
    video_path = os.path.join(video_dir, f"{video_name}.mp4")
    output_video_path = os.path.join(output_video_dir, f"{video_name}_fixed.mp4")

    if not os.path.exists(video_path):
        print(f"[ERROR] 動画ファイル {video_path} が見つかりません")
        return
    
    if os.path.exists(output_video_path):
        print(f"[INFO] すでに修正済みの動画が存在: {output_video_path}（スキップ）")
        return

    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (frame_width, frame_height))
    trackers = {track_id: cv2.VideoWriter(
        os.path.join(output_video_dir, f"{video_name}_ID{track_id}_masked.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"), fps, (frame_width, frame_height))
        for track_id in fix_map.values()
    }

    print(f"[INFO] {total_frames} フレームの動画を処理中...")

    for frame_id in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        masks = {track_id: np.zeros_like(frame) for track_id in fix_map.values()}
        txt_file = os.path.join(tracking_dir, f"{video_name}_{frame_id}_fixed.txt")
        unique_track_ids = set()
        if os.path.exists(txt_file):
            with open(txt_file, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 6:
                        _, x_center, y_center, width, height, track_id = parts
                        track_id = int(track_id)
                        unique_track_ids.add(track_id)
                        x1 = int((float(x_center) - float(width) / 2) * frame_width)
                        y1 = int((float(y_center) - float(height) / 2) * frame_height)
                        x2 = int((float(x_center) + float(width) / 2) * frame_width)
                        y2 = int((float(y_center) + float(height) / 2) * frame_height)
                        masks[track_id][y1:y2, x1:x2] = frame[y1:y2, x1:x2]
        
        for track_id, writer in trackers.items():
            writer.write(masks[track_id])
        
        for track_id in unique_track_ids:
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        out.write(frame)
        print(f"[INFO] 処理中: {frame_id + 1}/{total_frames} フレーム")

    
    cap.release()
    out.release()
    for writer in trackers.values():
        writer.release()
    print(f"[INFO] 修正後の動画を保存しました: {output_video_path}")

if __name__ == "__main__":
    merge_tracking_ids()
