import open3d as o3d
import numpy as np
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_csv_to_pcd(csv_file):
    """
    讀取 CSV 檔案，CSV 必須包含 x, y, z, R, G, B 欄位。
    回傳 Open3D 點雲，顏色歸一化至 [0, 1] 範圍。
    """
    df = pd.read_csv(csv_file)
    points = df[['x', 'y', 'z']].to_numpy()
    colors = df[['R', 'G', 'B']].to_numpy() / 255.0  # 將 0-255 轉成 0-1
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def pairwise_registration(source, target, voxel_size):
    """
    對兩個點雲進行配準，回傳 ICP 得到的變換矩陣與配準結果評估值。
    """
    # 進行體素下採樣
    source_down = source.voxel_down_sample(voxel_size)
    target_down = target.voxel_down_sample(voxel_size)

    # 估計法線，供 ICP 演算法使用
    radius_normal = voxel_size * 2.0
    source_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    target_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))

    # 執行點對點 ICP 配準
    max_corr_distance = voxel_size * 4.0
    result_icp = o3d.pipelines.registration.registration_icp(
        source_down, target_down, max_corr_distance, np.identity(4),
        o3d.pipelines.registration.TransformationEstimationPointToPoint())
    
    return result_icp.transformation, result_icp

def register_point_clouds(pcds, voxel_size=0.02):
    """
    將多個點雲依序配準並融合到一起，
    這裡假設點雲序列有部分重疊，可以利用 pairwise ICP 進行初步配準。
    """
    print("開始點雲配準與融合...")
    # 以第一個點雲作為全局點雲的初始值
    accumulated_pcd = pcds[0]
    transformation_global = np.identity(4)
    
    # 將其他點雲依序與當前全局點雲做 ICP 配準
    for i in range(1, len(pcds)):
        print(f"配準第 {i} 幀點雲...")
        source = pcds[i]
        # 以目前累積的全局點雲作為 target
        transformation_icp, icp_result = pairwise_registration(source, accumulated_pcd, voxel_size)
        print(f"Frame {i} ICP 變換矩陣:\n", transformation_icp)
        # 更新來源點雲：將 source 轉到全局坐標系
        source.transform(transformation_icp)
        # 融合進累積點雲
        accumulated_pcd += source
        # 為了避免點雲數量過多，做一次體素下採樣
        accumulated_pcd = accumulated_pcd.voxel_down_sample(voxel_size)
    
    return accumulated_pcd

if __name__ == '__main__':
    # 指定儲存 CSV 檔案的資料夾（請根據實際路徑修改）
    csv_folder = os.path.join(BASE_DIR, 'pointclouds')
    csv_files = sorted([os.path.join(csv_folder, f) for f in os.listdir(csv_folder) if f.endswith('.csv')])
    
    if len(csv_files) == 0:
        print("找不到 CSV 檔案，請確認資料夾內有點雲 CSV 檔。")
        exit(0)

    # 讀取所有 CSV 並轉換成 Open3D 點雲
    pcds = []
    for csv_file in csv_files:
        print(f"載入 {csv_file} ...")
        pcd = load_csv_to_pcd(csv_file)
        print(f"{csv_file} 點數: {np.asarray(pcd.points).shape[0]}")
        pcds.append(pcd)
    
    # 配準並融合所有點雲，voxel_size 可根據資料密度調整
    voxel_size = 0.02  # 例如 2 公分
    merged_pcd = register_point_clouds(pcds, voxel_size)
    
    # 儲存最終融合的點雲 (ply 格式)
    output_file = os.path.join(BASE_DIR, "world_coordinates.ply")
    o3d.io.write_point_cloud(output_file, merged_pcd)
    print(f"融合點雲已儲存為: {output_file}")
    
    # 選擇性地顯示結果
    o3d.visualization.draw_geometries([merged_pcd])