import numpy as np
import json
import pandas as pd
import os

# ------------------------------------------------
# 1) 計算單一物件在 DataFrame 中的軸平行邊界
# ------------------------------------------------
def get_cluster_bounds(cluster_points):
    """
    如果 cluster_points 為空回傳 None，否則回傳字典：
    { x_min, x_max, y_min, y_max, z_min, z_max }
    """
    if cluster_points.shape[0] == 0:
        return None

    x_min, x_max = float(cluster_points['x'].min()), float(cluster_points['x'].max())
    y_min, y_max = float(cluster_points['y'].min()), float(cluster_points['y'].max())
    z_min, z_max = float(cluster_points['z'].min()), float(cluster_points['z'].max())

    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max
    }

# ------------------------------------------------
# 2) 判斷兩個物件在 XZ 平面是否重疊
# ------------------------------------------------
def is_xz_overlap(box1, box2):
    """
    box1, box2 均為 { x_min, x_max, z_min, z_max, … } 格式的字典。
    只考慮 XZ 平面：
    若兩者在 X 範圍有交、且在 Z 範圍也有交，則回傳 True；否則 False。
    """
    x_overlap = not (box1['x_max'] <= box2['x_min'] or box2['x_max'] <= box1['x_min'])
    z_overlap = not (box1['z_max'] <= box2['z_min'] or box2['z_max'] <= box1['z_min'])
    return x_overlap and z_overlap

# ------------------------------------------------
# 3) 實作 Bottom‐Left 貪婪填充法 (Greedy Fill)
# ------------------------------------------------
def build_obs_json(input_path: str, SPACE_X: float = 10.0, SPACE_Y: float = 3.0, SPACE_Z: float = 8.0) -> dict:
    # --- 讀取原始 CSV（已含歸一化後的 x,y,z, material, object_num, object_label）---
    df = pd.read_csv(input_path)

    # --- （選擇性）印出最低/最高 Y、Z 材質模式供參考 ---
    bottom_10 = df.nsmallest(int(len(df) * 0.1), 'y')
    top_10    = df.nlargest(int(len(df) * 0.1), 'y')
    fwd_10    = df.nsmallest(int(len(df) * 0.1), 'z')
    back_10   = df.nlargest(int(len(df) * 0.1), 'z')
    min_y_mat = bottom_10['material'].mode().iloc[0]
    max_y_mat = top_10   ['material'].mode().iloc[0]
    min_z_mat = fwd_10   ['material'].mode().iloc[0]
    max_z_mat = back_10  ['material'].mode().iloc[0]
    print(f"最低 10% Y 材質: {min_y_mat}, 最高 10% Y 材質: {max_y_mat}")
    print(f"最前 10% Z 材質: {min_z_mat}, 最後 10% Z 材質: {max_z_mat}")

    # --- 將原始點雲座標映射到 [0, SPACE_X] × [0, SPACE_Y] × [0, SPACE_Z] ---
    # （假設 df['x'], df['y'], df['z'] 還沒有被映射過。若已映射可跳過此段）
    x_span = df['x'].max() - df['x'].min()
    y_span = df['y'].max() - df['y'].min()
    z_span = df['z'].max() - df['z'].min()
    x_scale = SPACE_X / x_span
    y_scale = SPACE_Y / y_span
    z_scale = SPACE_Z / z_span

    df['x'] = (df['x'] - df['x'].min()) * x_scale
    df['y'] = (df['y'] - df['y'].min()) * y_scale
    df['z'] = (df['z'] - df['z'].min()) * z_scale

    # --- 準備輸出 JSON 架構 ---
    output_data = {
        "space_dimensions": {
            "x": float(SPACE_X),
            "y": float(SPACE_Y),
            "z": float(SPACE_Z)
        },
        "objects": []
    }

    # --- 載入 categories.txt（材質對照表）一次即可 ---
    cat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "categories.txt")
    with open(cat_path, "r") as f:
        categories = [line.strip() for line in f.readlines()]

    # --- 收集每個 object_num 的原始邊界（經過歸一化後）與尺寸（X 寬度、Z 深度、Y 高度）---
    unique_objs = df['object_num'].dropna().unique()
    obj_info_list = []

    for obj_id in unique_objs:
        subset = df[df['object_num'] == obj_id]
        if subset.empty:
            continue

        bb = get_cluster_bounds(subset)
        if bb is None:
            continue

        width_x  = bb['x_max'] - bb['x_min']  # 在 X 軸方向上的寬度
        depth_z  = bb['z_max'] - bb['z_min']  # 在 Z 軸方向上的深度
        height_y = bb['y_max'] - bb['y_min']  # Y 軸方向上的高度（保留但不影響填充）

        # 該物件的代表材質與索引
        mat_name = subset['material'].mode().iloc[0]
        mat_id   = categories.index(mat_name)

        obj_info_list.append({
            "object_num": int(obj_id),
            "orig_bounds": bb,
            "width_x": width_x,
            "depth_z": depth_z,
            "height_y": height_y,
            "material_id": mat_id,
            "material_name": mat_name,
            "label": subset['object_label'].iloc[0] if pd.notna(subset['object_label'].iloc[0]) else None
        })

    # --- 依照 X–Z 面積 (width_x * depth_z) 由大到小排序，讓大物件先放 ---
    obj_info_list.sort(key=lambda x: x["width_x"] * x["depth_z"], reverse=True)

    # --- 已放置物件的邊界清單，用來檢查重疊 ---
    placed_bounds = []

    # --- Bottom‐Left 貪婪填充：對每個物件找「最左下角」可行位置 ---
    for info in obj_info_list:
        w = info["width_x"]
        d = info["depth_z"]

        # 收集所有候選 x 座標（0、或已放物件的 x_max）
        candidate_xs = [0.0] + [b["x_max"] for b in placed_bounds]
        # 收集所有候選 z 座標（0、或已放物件的 z_max）
        candidate_zs = [0.0] + [b["z_max"] for b in placed_bounds]

        best_pos = None
        best_z = None
        best_x = None

        # 試所有 (x0, z0)
        for x0 in candidate_xs:
            # 當 x0 + w > 空間寬度時，不用再找更大的 x0
            if x0 + w > SPACE_X:
                continue

            for z0 in candidate_zs:
                # 當 z0 + d > 空間深度時，跳過
                if z0 + d > SPACE_Z:
                    continue

                # 建立暫時的「假想邊界」
                test_bb = {
                    "x_min": x0,
                    "x_max": x0 + w,
                    "z_min": z0,
                    "z_max": z0 + d
                }

                # 檢查是否與已放置物件重疊
                overlap = False
                for pb in placed_bounds:
                    if is_xz_overlap(test_bb, pb):
                        overlap = True
                        break
                if overlap:
                    continue

                # 如果無重疊，依照 (z0, x0) 優先選「最小 z，再最小 x」
                if best_pos is None or (z0 < best_z) or (z0 == best_z and x0 < best_x):
                    best_pos = (x0, z0)
                    best_z = z0
                    best_x = x0

        # 如果找到最佳放置點，就真正加入 placed_bounds & output_data
        if best_pos is not None:
            x0, z0 = best_pos
            new_bb = {
                "x_min": x0,
                "x_max": x0 + w,
                "y_min": info["orig_bounds"]["y_min"],
                "y_max": info["orig_bounds"]["y_max"],
                "z_min": z0,
                "z_max": z0 + d
            }

            # 加入 placed_bounds 供後續物件檢查
            placed_bounds.append({
                "x_min": new_bb["x_min"],
                "x_max": new_bb["x_max"],
                "z_min": new_bb["z_min"],
                "z_max": new_bb["z_max"]
            })

            # 真正寫入 JSON
            output_data["objects"].append({
                "object_num": info["object_num"],
                "object_label": info["label"],
                "material": {
                    "id": info["material_id"],
                    "name": info["material_name"]
                },
                "bounds": new_bb,
                "dimensions": {
                    "depth": float(w),  # FDS 中的 depth 對應 X 範圍
                    "width": float(info["orig_bounds"]["y_max"] - info["orig_bounds"]["y_min"]),  # Y 高度
                    "height": float(d)  # FDS 中的 height 對應 Z 範圍
                }
            })
        else:
            print(f"⚠️ Object {info['object_num']} 無法在 (0~{SPACE_X})×(0~{SPACE_Z}) 空間內擺放；已略過")

    # --- 將結果寫到 room_simulation.json ---
    output_path = os.path.join(os.path.dirname(os.path.dirname(input_path)), "room_simulation.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"✅ JSON 已儲存於：{output_path}")
    return { 'output_json': output_path }


# --------------------------------------------
# 若你希望直接執行此檔做測試，可使用下面區塊
# --------------------------------------------
if __name__ == "__main__":
    img_num    = '20250329_193301'
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'results', f'pointcloud_{img_num}_clustered.csv')
    build_obs_json(input_path)
