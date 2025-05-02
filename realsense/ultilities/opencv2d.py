<<<<<<< HEAD:realsense/opencv2d.py
"""
Only used when you have Intel Realsense.
Get depth image and color image.
"""

import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'colordepth'), exist_ok=True)
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())  # 16-bit
        color_image = np.asanyarray(color_frame.get_data())  # BGR

        depth_colormap = cv2.applyColorMap(                  # 深度顏色圖
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )

        # 拼接後顯示
        images = np.hstack((color_image, depth_colormap))
        cv2.imshow('RealSense', images)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # 按下 'q' 離開迴圈
            break
        elif key == ord('s'):
            # 按下 's' 儲存
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            color_filename = os.path.join(BASE_DIR, 'colordepth', f"color_{timestamp}.png")
            depth_filename = os.path.join(BASE_DIR, 'colordepth', f"depth_colormap_{timestamp}.png")
            cv2.imwrite(color_filename, color_image)
            cv2.imwrite(depth_filename, depth_colormap)
            print(f"[INFO] 已儲存 {color_filename} 與 {depth_filename}")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
=======
"""
Only used when you have Intel Realsense.
Get depth image and color image.
"""

import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'colordepth'), exist_ok=True)
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())  # 16-bit
        color_image = np.asanyarray(color_frame.get_data())  # BGR

        depth_colormap = cv2.applyColorMap(                  # 深度顏色圖
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )

        # 拼接後顯示
        images = np.hstack((color_image, depth_colormap))
        cv2.imshow('RealSense', images)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # 按下 'q' 離開迴圈
            break
        elif key == ord('s'):
            # 按下 's' 儲存
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            color_filename = os.path.join(BASE_DIR, 'colordepth', f"color_{timestamp}.png")
            depth_filename = os.path.join(BASE_DIR, 'colordepth', f"depth_colormap_{timestamp}.png")
            cv2.imwrite(color_filename, color_image)
            cv2.imwrite(depth_filename, depth_colormap)
            print(f"[INFO] 已儲存 {color_filename} 與 {depth_filename}")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
>>>>>>> upstream/master:realsense/ultilities/opencv2d.py
