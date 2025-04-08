import numpy as np
import json
import pandas as pd
import os

# 定義實際空間大小（單位：米）
SPACE_X = 10.0  # 向右方向
SPACE_Y = 3.0   # 向下方向
SPACE_Z = 8.0   # 向前方向
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_cluster_bounds(cluster_points):
    """根據聚類點計算邊界"""
    if len(cluster_points) == 0:
        return None
    
    # 計算邊界
    x_min, x_max = np.min(cluster_points['x']), np.max(cluster_points['x'])
    y_min, y_max = np.min(cluster_points['y']), np.max(cluster_points['y'])
    z_min, z_max = np.min(cluster_points['z']), np.max(cluster_points['z'])
    
    return {
        "x_min": float(x_min),
        "x_max": float(x_max),
        "y_min": float(y_min),
        "y_max": float(y_max),
        "z_min": float(z_min),
        "z_max": float(z_max)
    }

def main():
    df = pd.read_csv(os.path.join(BASE_DIR, "results/clustered_points.csv"))
    
    # 計算縮放比例
    x_scale = SPACE_X / (df['x'].max() - df['x'].min())
    y_scale = SPACE_Y / (df['y'].max() - df['y'].min())
    z_scale = SPACE_Z / (df['z'].max() - df['z'].min())
    
    # 對每個座標進行縮放
    df['x'] = (df['x'] - df['x'].min()) * x_scale
    df['y'] = (df['y'] - df['y'].min()) * y_scale
    df['z'] = (df['z'] - df['z'].min()) * z_scale
    
    """
    # 修正座標系 (RealSense → Open3D)
    flip_transform = np.array([
        [1,  0,  0, 0],
        [0, -1,  0, 0],
        [0,  0, -1, 0],
        [0,  0,  0, 1]
    ])
    
    # 將DataFrame中的點轉換為numpy數組
    points = df[['x', 'y', 'z']].values
    # 添加齊次坐標
    points_homo = np.column_stack((points, np.ones(points.shape[0])))
    # 應用變換
    transformed_points = (flip_transform @ points_homo.T).T[:, :3]
    
    # 更新DataFrame中的坐標
    df['x'] = transformed_points[:, 0]
    df['y'] = transformed_points[:, 1]
    df['z'] = transformed_points[:, 2]
    """
    
    # with open("categories.txt", "r") as f:
    #     categories = [line.strip() for line in f.readlines()]
    
    output_data = {
        "space_dimensions": {
            "x": float(SPACE_X),
            "y": float(SPACE_Y),
            "z": float(SPACE_Z)
        },
        "objects": []
    }
    
    # 對每個聚類進行處理
    unique_clusters = df['cluster'].unique()
    for cluster_id in unique_clusters:
        if cluster_id == -1:  # 跳過噪聲點
            continue
            
        # 獲取當前聚類的所有點
        cluster_points = df[df['cluster'] == cluster_id]
        
        if len(cluster_points) == 0:
            continue
            
        # # 獲取該聚類的主要材質
        # main_material_id = cluster_points['material_id'].mode().iloc[0]
        
        # 計算邊界
        bounds = get_cluster_bounds(cluster_points)
        if bounds is None:
            continue
            
        """
        # 確保所有值都在合理範圍內
        bounds["x_min"] = max(0.0, min(SPACE_X, bounds["x_min"]))
        bounds["x_max"] = max(0.0, min(SPACE_X, bounds["x_max"]))
        bounds["y_min"] = max(0.0, min(SPACE_Y, bounds["y_min"]))
        bounds["y_max"] = max(0.0, min(SPACE_Y, bounds["y_max"]))
        bounds["z_min"] = max(0.0, min(SPACE_Z, bounds["z_min"]))
        bounds["z_max"] = max(0.0, min(SPACE_Z, bounds["z_max"]))
        """
        
        output_data["objects"].append({
            "cluster_id": int(cluster_id),
            "object_label": cluster_points['object_label'].iloc[0],
            # "material": {
            #     "id": int(main_material_id),
            #     "name": categories[int(main_material_id)]
            # },
            "bounds": bounds,
            "dimensions": {
                "depth": float(bounds["x_max"] - bounds["x_min"]),
                "width": float(bounds["y_max"] - bounds["y_min"]),
                "height": float(bounds["z_max"] - bounds["z_min"])
            }
        })
    
    # 保存結果
    with open(os.path.join(BASE_DIR, "room_simulation.json"), "w") as f:
        json.dump(output_data, f, indent=4)

if __name__ == "__main__":
    main()
