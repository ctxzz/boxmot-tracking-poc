import os
import glob
import csv
import cv2
import numpy as np

# 🔹 入力動画ファイル（拡張子なしの動画名を取得）
VIDEO_FILE = "video.mp4"
VIDEO_NAME = os.path.splitext(VIDEO_FILE)[0]  # "video"

# 🔹 トラッキングデータのディレクトリ
TRACKING_DIR = f"runs/track/{VIDEO_NAME}/labels"
FIX_TRACK_DIR = "fix_trackID"  # マージ用CSVを保存するディレクトリ
VIDEO_DIR = "videos"  # 元動画のディレクトリ
OUTPUT_VIDEO_DIR = "runs/track/fixed_videos"  # 修正後の動画の出力先

# 出力ディレクトリを作成
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)


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
    csv_file = os.path.join(FIX_TRACK_DIR, f"{VIDEO_NAME}.csv")

    if not os.path.exists(csv_file):
        print(f"[WARNING] {csv_file} が見つかりません。IDの統合は行われません。")
        return

    fix_map = load_fix_map(csv_file)  # ここでfix_mapを作成
    txt_files = [f for f in glob.glob(os.path.join(TRACKING_DIR, "*.txt")) if not f.endswith("_fixed.txt")]

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
                    continue  # マージ対象でない ID はスキップ

                new_track_id = fix_map[track_id]
                modified_lines.append(f"{class_id} {x_center} {y_center} {width} {height} {new_track_id}\n")

        if not modified_lines:
            print(f"[INFO] ({i+1}/{len(txt_files)}) 一致するIDなし: {file_path}（スキップ）")
            continue

        with open(fixed_path, "w") as f:
            f.writelines(modified_lines)

        print(f"[INFO] ({i+1}/{len(txt_files)}) 修正済み: {fixed_path} （{len(modified_lines)} 行）")

    print("[INFO] トラッキングデータの修正が完了しました！")

    # 修正後のバウンディングボックス付き動画を作成（fix_mapを引数として渡す）
    create_fixed_video(fix_map)


def create_fixed_video(fix_map):
    """修正後のIDを使用して、元の動画にバウンディングボックスを描画し、トラッキングIDごとにマスク処理した動画も保存"""
    video_path = os.path.join(VIDEO_DIR, f"{VIDEO_NAME}.mp4")
    output_video_path = os.path.join(OUTPUT_VIDEO_DIR, f"{VIDEO_NAME}_fixed.mp4")

    if not os.path.exists(video_path):
        print(f"[ERROR] 動画ファイル {video_path} が見つかりません")
        return

    # 🔹 修正後の動画がすでに存在する場合はスキップ
    if os.path.exists(output_video_path):
        print(f"[INFO] すでに修正済みの動画が存在: {output_video_path}（スキップ）")
        return

    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (frame_width, frame_height))

    # トラッキングIDごとの動画を保存するディレクトリとライターを準備
    trackers = {track_id: cv2.VideoWriter(
        os.path.join(OUTPUT_VIDEO_DIR, f"{VIDEO_NAME}_ID{track_id}_masked.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"), fps, (frame_width, frame_height))
        for track_id in fix_map.values()
    }

    print(f"[INFO] {total_frames} フレームの動画を処理中...")

    for frame_id in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        txt_file = os.path.join(TRACKING_DIR, f"{VIDEO_NAME}_{frame_id}_fixed.txt")

        # 🔹 すべてのトラッキングIDについて、黒いフレームを作成
        empty_frame = np.zeros_like(frame, dtype=np.uint8)

        masks = {track_id: empty_frame.copy() for track_id in fix_map.values()}

        unique_track_ids = set()  # ここで空のセットを定義

        # **バウンディングボックスを描画する前にマスク動画を書き込む**
        if os.path.exists(txt_file):
            with open(txt_file, "r") as f:
                lines = f.readlines()

                for line in lines:
                    parts = line.strip().split()
                    if len(parts) == 6:
                        class_id, x_center, y_center, width, height, track_id = parts
                        x_center, y_center, width, height = map(float, [x_center, y_center, width, height])
                        track_id = int(track_id)

                        if track_id in unique_track_ids:
                            continue  # 同じIDの二重書き込みを防ぐ

                        unique_track_ids.add(track_id)

                        # バウンディングボックスの座標変換
                        x1 = int((x_center - width / 2) * frame_width)
                        y1 = int((y_center - height / 2) * frame_height)
                        x2 = int((x_center + width / 2) * frame_width)
                        y2 = int((y_center + height / 2) * frame_height)

                        # **マスク動画にはバウンディングボックスを描画する前の画像を保存**
                        masks[track_id][y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        for track_id, writer in trackers.items():
            writer.write(masks[track_id])  # すべてのフレームを書き込む

        out.write(frame)

        print(f"[INFO] 処理中: {frame_id + 1}/{total_frames} フレーム")

    cap.release()
    out.release()

    for writer in trackers.values():
        writer.release()

    print(f"[INFO] 修正後の動画を保存しました: {output_video_path}")


if __name__ == "__main__":
    merge_tracking_ids()
