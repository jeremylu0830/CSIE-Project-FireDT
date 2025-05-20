import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cv2
from ultralytics import YOLO

# ----------------- 重建圖片 -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(BASE_DIR, 'results', '')
df = pd.read_csv('pointcloud_20250329_193301.csv')
width, height = 640, 480
image = np.zeros((height, width, 3), dtype=np.uint8)

for idx, row in df.iterrows():
    u, v = int(row['u']), int(row['v'])
    R, G, B = int(row['R']), int(row['G']), int(row['B'])
    if 0 <= u < width and 0 <= v < height:
        image[v, u] = [R, G, B]

# ----------------- YOLOv8 物件偵測 -----------------
# 載入預訓練模型（YOLOv8n 是最輕量版，也可以換成 yolov8s, yolov8m, yolov8l...）
model = YOLO("yolov8l.pt")

# YOLO 預測（模型會回傳一組結果清單）
results = model(image)[0]

# 解析結果：包含類別、信心值與邊界框座標
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

# 依面積排序
detection_results = pd.DataFrame(detection_results)
detection_results = detection_results.sort_values(by="area", ascending=True)
print("YOLOv8 偵測結果：")
print(detection_results)

# ----------------- 更新原始 CSV -----------------
df["object_label"] = ""
df["bbox_x1"] = np.nan
df["bbox_y1"] = np.nan
df["bbox_x2"] = np.nan
df["bbox_y2"] = np.nan

for _, det in detection_results.iterrows():
    x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
    label = det["label"]
    mask = (df["u"] >= x1) & (df["u"] <= x2) & (df["v"] >= y1) & (df["v"] <= y2) & (df["object_label"] == "")
    df.loc[mask, "object_label"] = label
    df.loc[mask, "bbox_x1"] = round(x1, 2)
    df.loc[mask, "bbox_y1"] = round(y1, 2)
    df.loc[mask, "bbox_x2"] = round(x2, 2)
    df.loc[mask, "bbox_y2"] = round(y2, 2)

df.to_csv("pointcloud_with_objects.csv", index=False)
print("更新後的 CSV 檔案已儲存為 pointcloud_with_objects.csv")

# ----------------- 顯示 YOLO 結果 -----------------
# 將結果畫在圖像上
annotated_image = results.plot()

plt.imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
plt.title("YOLOv8 Detection")
plt.axis('off')
plt.show()
