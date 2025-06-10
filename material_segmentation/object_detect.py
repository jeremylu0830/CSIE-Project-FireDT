import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(BASE_DIR, 'demo_web')
MATL_DIR = os.path.join(BASE_DIR, 'material_segmentation')
SENS_DIR = os.path.join(BASE_DIR, 'realsense')
FILE_DIR = os.path.join(DEMO_DIR, 'results')

def detect_objects(csv_file: str, saved_path: str, model_path: str = "yolo12x.pt") -> dict:
    # ----------------- 重建圖片 -----------------
    df = pd.read_csv(csv_file)
    width, height = 640, 480
    image = np.zeros((height, width, 3), dtype=np.uint8)

    for idx, row in df.iterrows():
        u, v = int(row['u']), int(row['v'])
        R, G, B = int(row['R']), int(row['G']), int(row['B'])
        if 0 <= u < width and 0 <= v < height:
            image[v, u] = [R, G, B]

    # ----------------- YOLOv12 物件偵測 -----------------
    model = YOLO(model_path)
    results = model(image)[0]

    detection_results = []
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cls_id = int(box.cls[0].item())
        score = float(box.conf[0].item())
        label = model.names[cls_id]
        area = (x2 - x1) * (y2 - y1)
        detection_results.append({
            "label": label,
            "score": score,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "area": area
        })

    # 依面積排序（由小到大）
    detection_results = pd.DataFrame(detection_results)
    detection_results = detection_results.sort_values(by="area", ascending=True).reset_index(drop=True)
    print("YOLOv12 偵測結果：")
    print(detection_results)

    # ----------------- 更新原始 CSV -----------------
    df["object_label"] = ""
    df["object_num"] = np.nan
    df["bbox_x1"] = np.nan
    df["bbox_y1"] = np.nan
    df["bbox_x2"] = np.nan
    df["bbox_y2"] = np.nan

    # 為每個框分配一個 object_num（從 1 開始編號）
    for obj_id, (_, det) in enumerate(detection_results.iterrows(), start=1):
        x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
        label = det["label"]

        mask = (
            (df["u"] >= x1) & (df["u"] <= x2) &
            (df["v"] >= y1) & (df["v"] <= y2) &
            (df["object_label"] == "")
        )

        df.loc[mask, "object_label"] = label
        df.loc[mask, "object_num"] = obj_id
        df.loc[mask, "bbox_x1"] = round(x1, 2)
        df.loc[mask, "bbox_y1"] = round(y1, 2)
        df.loc[mask, "bbox_x2"] = round(x2, 2)
        df.loc[mask, "bbox_y2"] = round(y2, 2)

    output_file = os.path.join(saved_path, os.path.basename(csv_file).replace(".csv", "_with_objects.csv"))
    df.to_csv(output_file, index=False)
    print(f"更新後的 CSV 檔案已儲存為 {output_file}")

    # ----------------- 顯示 YOLO 結果 -----------------
    annotated_image = results.plot()
    plt.imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
    plt.title("YOLOv12 Detection")
    plt.axis('off')
    # plt.show()
    plt.savefig(os.path.join(saved_path, 'yolo_detection_result.png'), bbox_inches='tight', pad_inches=0.1)

    return {
        'object_csv': output_file,
    }

# only for testing
if __name__ == "__main__":
    csv_file = os.path.join(FILE_DIR, 'test', 'pointcloud.csv')
    saved_path = os.path.join(FILE_DIR, 'test')
    detect_objects(csv_file, saved_path)
