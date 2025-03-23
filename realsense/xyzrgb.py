"""
Get pointclouds information and saved to csv, no need Intel Realsense when running this program.
Input:  .bag (with color + depth stream)
Output: .csv
"""
import pyrealsense2 as rs
import numpy as np
import pandas as pd
import os

# 指定 .bag 檔案路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'bags'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'output_frames'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'videos'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'pointclouds'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'projections'), exist_ok=True)
framename = "20250311_140524"
bag_file = os.path.join(BASE_DIR, 'bags', f'{framename}.bag')

# 建立 RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file)

# 啟動 pipeline
pipeline.start(config)

# 建立對齊物件，對齊深度和顏色影像
align_to = rs.stream.color
align = rs.align(align_to)

try:
    # 取得一幀影像
    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)

    # 取得對齊後的彩色和深度影像
    color_frame = aligned_frames.get_color_frame()
    depth_frame = aligned_frames.get_depth_frame()

    if not color_frame or not depth_frame:
        raise ValueError("未找到彩色或深度影像。")

    # 取得影像內部參數
    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics

    # 轉換影像為 numpy 陣列
    color_image = np.asanyarray(color_frame.get_data())
    depth_image = np.asanyarray(depth_frame.get_data())

    # 影像尺寸
    height, width = depth_image.shape

    # 儲存 XYZ 和 RGB 資料
    data = []
    for y in range(height):
        for x in range(width):
            # 取得深度值 (單位為米)
            depth = depth_frame.get_distance(x, y)

            # 將像素座標轉換為 XYZ 空間座標
            if depth > 0:
                point = rs.rs2_deproject_pixel_to_point(depth_intrin, [x, y], depth)
                X, Y, Z = point

                # 取得 RGB 值
                R, G, B = color_image[y, x]

                # 儲存資料
                data.append({'X': X, 'Y': Y, 'Z': Z, 'R': R, 'G': G, 'B': B})

    # 將資料轉換為 DataFrame
    df = pd.DataFrame(data)

    # 儲存為 CSV 檔案
    points_csv_path = os.path.join(BASE_DIR, 'pointclouds', f'xyz_rgb_values.csv')
    df.to_csv(points_csv_path, index=False)
    print("XYZ and RGB values saved to xyz_rgb_values.csv")

finally:
    # 停止 pipeline
    pipeline.stop()
