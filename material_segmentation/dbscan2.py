import pandas as pd
import numpy as np
import json
import os

def dbscan_clustering(
    input_csv: str,
    img_num: str = None
) -> dict:
    """
    讀入一個包含欄位 [x, y, z, material, object_num, ...] 的 CSV 檔，
    對於每一個 object_num：
      1. 找出該 object_num 底下最常出現的 material（眾數）。
      2. 只保留屬於那個 material 的點，然後分別計算 x, y, z 的 10th 和 90th percentile：
         - x_min = 10th percentile of x
         - x_max = 90th percentile of x
         - y_min = 10th percentile of y
         - y_max = 90th percentile of y
         - z_min = 10th percentile of z
         - z_max = 90th percentile of z
      3. 將這些結果組成 dict, 並依序寫入 output_data["objects"]。

    參數：
      - input_csv (str)：輸入 CSV 的路徑，需包含欄位 'x','y','z','material','object_num'。
      - output_path (str, optional)：若提供，最後會把結果存成 JSON 到此路徑。
    
    回傳：
      - dict，格式如下：
        {
          "objects": [
            {
              "object_num": ...,
              "material": "<mode material>",
              "bounds": {
                "x_min": ...,
                "x_max": ...,
                "y_min": ...,
                "y_max": ...,
                "z_min": ...,
                "z_max": ...
              }
            },
            ...
          ]
        }
    """
    # 1. 讀取 CSV
    df = pd.read_csv(input_csv)

    # 確認必要欄位存在
    required_cols = {'x', 'y', 'z', 'material', 'object_num'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"輸入 CSV 缺少以下必要欄位：{missing}")

    output_data = { "objects": [] }

    # 2. 針對每個 object_num 群組
    for obj_id, group in df.groupby('object_num'):
        # 跳過 NaN 或空白的 object_num
        if pd.isna(obj_id):
            continue

        # 2a. 找該群組最常出現的 material
        mode_material = group['material'].mode()
        if mode_material.empty:
            # 若這個群組所有 material 都是 NaN 或空值，就跳過
            continue
        mode_material = mode_material.iloc[0]

        # 2b. 從群組中只保留該 mode_material 的點
        mat_points = group.loc[group['material'] == mode_material]
        if mat_points.empty:
            # 如果沒有任何點屬於 mode_material，就跳過
            continue

        # 2c. 計算 x,y,z 的 10th, 90th percentile
        x_vals = mat_points['x'].values
        y_vals = mat_points['y'].values
        z_vals = mat_points['z'].values

        x_min = float(np.percentile(x_vals, 10))
        x_max = float(np.percentile(x_vals, 90))
        y_min = float(np.percentile(y_vals, 10))
        y_max = float(np.percentile(y_vals, 90))
        z_min = float(np.percentile(z_vals, 10))
        z_max = float(np.percentile(z_vals, 90))

        # 2d. 將結果加入 output_data
        output_data["objects"].append({
            "object_num": int(obj_id),
            "material": mode_material,
            "bounds": {
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
                "z_min": z_min,
                "z_max": z_max
            }
        })

    # 輸出更新後的 CSV
    output_path = os.path.join(
        os.path.dirname(input_csv),
        f'pointcloud_{img_num}_clustered.csv'
    )
    df.to_csv(output_path, index=False)

    return {
        'cluster_path': output_path
    }

    return output_data


# -------------------------
# 範例使用方式
# -------------------------
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'results', 'pointcloud_20250329_193301_with_materials.csv')
    result = dbscan_clustering(data_path, '20250329_193301')
