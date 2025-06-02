"""
Correctly get 2d-image from pointclouds information, NO NEED of Intel Realsense when running this program.
Input:  .bag
Output: .csv and .png (projection image of pointclouds)
"""
import pyrealsense2 as rs
import numpy as np
import pandas as pd
import cv2
import time
import os


def no_cap(base_dir: str, bag_file: str) -> dict:
    os.makedirs(os.path.join(base_dir, 'bags'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'output_frames'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'videos'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'pointclouds'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'projections'), exist_ok=True)

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(bag_file, False)
    pipeline.start(config)

    current_frame = 0
    try:
        while True:
            frames = pipeline.wait_for_frames()
            if not frames:
                print("[INFO] No more frames available, exiting.")
                break
            current_frame += 1
            if current_frame < 320:
                continue

            align = rs.align(rs.stream.color)
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            pc = rs.pointcloud()
            pc.map_to(color_frame)
            points = pc.calculate(depth_frame)

            # vtx = xyz of pointclouds
            vtx = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
            tex = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
            valid_mask = vtx[:, 2] > 0
            vtx = vtx[valid_mask]
            tex = tex[valid_mask]
            img_h, img_w = color_image.shape[:2]
            tex_x = np.clip((tex[:, 0] * (img_w - 1)).astype(int), 0, img_w - 1)
            tex_y = np.clip((tex[:, 1] * (img_h - 1)).astype(int), 0, img_h - 1)

            colors = color_image[tex_y, tex_x]
            blank_image = np.zeros((img_h, img_w, 3), dtype=np.uint8)
            for i in range(len(tex_x)):
                r, g, b = colors[i]
                r, g, b = b, g, r
                cv2.circle(blank_image, (tex_x[i], tex_y[i]), 2, (int(r), int(g), int(b)), -1)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            projection_path = os.path.join(base_dir, 'projections', f"projection_{timestamp}.png")
            cv2.imwrite(projection_path, color_image[:, :, ::-1])
            print(f"[INFO] saved projection_{timestamp}.png")

            data = {
                'x': vtx[:, 0],
                'y': vtx[:, 1],
                'z': vtx[:, 2],
                'u': tex_x,
                'v': tex_y,
                'R': colors[:, 2],
                'G': colors[:, 1],
                'B': colors[:, 0]
            }
            df = pd.DataFrame(data)
            pointcloud_path = os.path.join(base_dir, 'pointclouds', f"pointcloud_{timestamp}.csv")
            df.to_csv(pointcloud_path, index=False)
            print(f"[INFO] saved pointcloud_{timestamp}.csv")

            return {
                'projection': projection_path,
                'pointcloud': pointcloud_path,
                'timestamp': timestamp,
            }

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()


# only for testing
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bag_file = os.path.join(base_dir, 'bags', '20250311_141600.bag')
    print(bag_file)
    real_out = no_cap(base_dir, bag_file)
