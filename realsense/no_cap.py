"""
Correctly get 2d-image from pointclouds information, NO NEED of Intel Realsense when running this program.
Input:  .csv
Output: projection image of pointclouds.

TO-DO: 顏色都是錯的，感覺是 bag 的問題 
"""
import pyrealsense2 as rs
import numpy as np
import pandas as pd
import cv2
import time
import os

# 設定檔案路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'bags'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'output_frames'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'videos'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'pointclouds'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'projections'), exist_ok=True)

# 設定 .bag 檔案的路徑
bag_file = os.path.join(BASE_DIR, 'bags', '20250311_140524.bag')
pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file)
pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()

        # **確保深度影像與 RGB 影像同步**
        align = rs.align(rs.stream.color)
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # 讀取 BGR 影像
        color_image = np.asanyarray(color_frame.get_data())

        # **計算點雲**
        pc = rs.pointcloud()
        pc.map_to(color_frame)  # **確保點雲對應到 color_frame**
        points = pc.calculate(depth_frame)  # 取得點雲

        # 讀取點雲 XYZ 座標
        vtx = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)

        # 讀取點雲的 UV 紋理座標
        tex = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)

        # 過濾無效點 (Z <= 0)
        valid_mask = vtx[:, 2] > 0
        vtx = vtx[valid_mask]
        tex = tex[valid_mask]

        # **修正 UV 轉換**
        img_h, img_w = color_image.shape[:2]
        tex_x = np.clip((tex[:, 0] * (img_w - 1)).astype(int), 0, img_w - 1)
        tex_y = np.clip((tex[:, 1] * (img_h - 1)).astype(int), 0, img_h - 1)

        # 取得點對應的顏色
        colors = color_image[tex_y, tex_x]  # **從 color_image 擷取對應顏色**

        # **建立一張全黑的影像來顯示 3D 點雲投影**
        blank_image = np.zeros((img_h, img_w, 3), dtype=np.uint8)

        # **在全黑背景上畫出投射完的點雲**
        for i in range(len(tex_x)):
            r, g, b = colors[i]
            cv2.circle(blank_image, (tex_x[i], tex_y[i]), 2, (int(r), int(g), int(b)), -1)

        # # **合併影像**
        # combined_image = np.hstack((color_image, blank_image))

        # # **顯示影像**
        # cv2.imshow('RealSense - Left: RGB | Right: 3D Projection', combined_image)

        # 儲存影像和點雲資料
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(os.path.join(BASE_DIR, 'projections', f"color_{timestamp}.png"), color_image)
        cv2.imwrite(os.path.join(BASE_DIR, 'projections', f"projection_{timestamp}.png"), blank_image)
        print(f"[INFO] saved color_{timestamp}.png and projection_{timestamp}.png")

        data = {
            'x': vtx[:, 0],
            'y': vtx[:, 1],
            'z': vtx[:, 2],
            'u': tex_x,
            'v': tex_y,
            'R': colors[:, 2],  # OpenCV 使用 BGR 格式，R 在第 2 列
            'G': colors[:, 1],
            'B': colors[:, 0]
        }
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(BASE_DIR, 'pointclouds', f"pointcloud_{timestamp}.csv"), index=False)
        print(f"[INFO] saved pointcloud_{timestamp}.csv")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
