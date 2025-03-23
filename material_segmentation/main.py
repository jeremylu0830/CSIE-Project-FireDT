import numpy as np
import json

# 定義實際空間大小（單位：米）
SPACE_X = 10.0  # 深度方向
SPACE_Y = 3.0   # 水平方向
SPACE_Z = 5.0   # 垂直方向

def get_object_mask(bbox, depth_matrix, material_matrix, main_material_id, threshold=0.1):
    """使用深度值和材質生成物體遮罩"""
    y_min, y_max = bbox["y_min"], bbox["y_max"]
    x_min, x_max = bbox["x_min"], bbox["x_max"]
    
    region_depth = depth_matrix[y_min:y_max, x_min:x_max]
    region_material = material_matrix[y_min:y_max, x_min:x_max]
    
    # 使用中值深度作為參考
    median_depth = np.median(region_depth)
    
    # 結合深度和材質條件
    depth_mask = np.abs(region_depth - median_depth) < threshold
    material_mask = region_material == main_material_id
    
    return depth_mask & material_mask

def get_refined_bounds(bbox, depth_matrix, material_matrix, main_material_id):
    """獲取更精確的3D邊界"""
    mask = get_object_mask(bbox, depth_matrix, material_matrix, main_material_id)
    y_min, y_max = bbox["y_min"], bbox["y_max"]
    x_min, x_max = bbox["x_min"], bbox["x_max"]
    
    region_depth = depth_matrix[y_min:y_max, x_min:x_max]
    masked_depth = region_depth[mask]
    
    if len(masked_depth) == 0:
        return None
    
    # 使用深度值作為x座標（前後）
    x_min_3d = np.percentile(masked_depth, 5)
    x_max_3d = np.percentile(masked_depth, 95)
    
    # 計算y（左右）和z（上下）的範圍
    y_pixels = np.where(mask)[1]
    z_pixels = np.where(mask)[0]
    
    if len(y_pixels) == 0 or len(z_pixels) == 0:
        return None
    
    # 簡單的線性映射到實際空間
    y_min_3d = (x_min + np.min(y_pixels)) * (SPACE_Y / depth_matrix.shape[1])
    y_max_3d = (x_min + np.max(y_pixels)) * (SPACE_Y / depth_matrix.shape[1])
    z_min_3d = (y_min + np.min(z_pixels)) * (SPACE_Z / depth_matrix.shape[0])
    z_max_3d = (y_min + np.max(z_pixels)) * (SPACE_Z / depth_matrix.shape[0])
    
    # 確保所有值都在合理範圍內
    x_min_3d = max(0.0, min(SPACE_X, x_min_3d))
    x_max_3d = max(0.0, min(SPACE_X, x_max_3d))
    y_min_3d = max(0.0, min(SPACE_Y, y_min_3d)) + 1
    y_max_3d = max(0.0, min(SPACE_Y, y_max_3d)) + 1
    z_min_3d = max(0.0, min(SPACE_Z, z_min_3d)) + 1
    z_max_3d = max(0.0, min(SPACE_Z, z_max_3d)) + 1
    
    return {
        "x_min": float(x_min_3d),
        "x_max": float(x_max_3d),
        "y_min": float(y_min_3d),
        "y_max": float(y_max_3d),
        "z_min": float(z_min_3d),
        "z_max": float(z_max_3d)
    }

def main():
    # 讀取數據
    depth_matrix = np.load("test6_raw_depth_meter.npy")
    material_matrix = np.load("test6_labelmap.npy")
    
    with open("test6_detection_info.json", "r") as f:
        detection_info = json.load(f)
    with open("categories.txt", "r") as f:
        categories = [line.strip() for line in f.readlines()]
    
    output_data = []
    
    for obj in detection_info["objects"]:
        bbox = obj["bounding_box"]
        
        # 獲取主要材質
        region_material = material_matrix[bbox["y_min"]:bbox["y_max"], 
                                       bbox["x_min"]:bbox["x_max"]]
        unique_materials, counts = np.unique(region_material, return_counts=True)
        main_material_id = unique_materials[np.argmax(counts)]
        material_name = categories[int(main_material_id)]
        
        # 獲取3D邊界
        bounds = get_refined_bounds(bbox, depth_matrix, material_matrix, main_material_id)
        if bounds is None:
            continue
            
        output_data.append({
            "object_name": obj["class_name"],
            "confidence": obj["confidence"],
            "material": {
                "id": int(main_material_id),
                "name": material_name
            },
            "bounds": bounds,
            "dimensions": {
                "depth": float(bounds["x_max"] - bounds["x_min"]),
                "width": float(bounds["y_max"] - bounds["y_min"]),
                "height": float(bounds["z_max"] - bounds["z_min"])
            }
        })
    
    # 保存結果
    with open("room_simulation.json", "w") as f:
        json.dump(output_data, f, indent=4)

if __name__ == "__main__":
    main()
