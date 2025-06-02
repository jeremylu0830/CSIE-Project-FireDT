import pandas as pd
import os
from sklearn.cluster import DBSCAN

def dbscan_clustering(
    data_path: str,
    img_num: str,
    eps: float = 0.1,
    min_samples: int = 5
) -> dict:
    # 讀取原始 CSV（包含所有行，即使 object_label 為空）
    df = pd.read_csv(data_path, low_memory=False)

    # 新增一欄位放分群後的 cluster id，預設為 -1（noise）
    df['cluster'] = -1
    next_cluster_id = 0

    # 依 material 分組，對每個材質群跑 DBSCAN
    for material, sub_df in df.groupby('material'):
        # 取該材質下所有點的座標
        X = sub_df[['x', 'y', 'z']].values

        # 如果這個材質的點太少，全部先維持為 -1（noise）
        if len(X) < min_samples:
            df.loc[sub_df.index, 'cluster'] = -1
            continue

        # 在此材質子集內做 DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clustering.fit_predict(X)
        # labels 內：-1 表示 noise，其餘 0,1,2,… 是該材質內部的群集編號

        # 把這些子群集編號加上偏移量 next_cluster_id
        mapped = []
        for lbl in labels:
            if lbl == -1:
                mapped.append(-1)
            else:
                mapped.append(lbl + next_cluster_id)
        df.loc[sub_df.index, 'cluster'] = mapped

        # 更新下一個材質的偏移量（如果這個材質分出了 k 個群集，就 +k）
        max_lbl = labels.max()
        if max_lbl >= 0:
            next_cluster_id += (max_lbl + 1)

    # 最後依 material, object_label, cluster 做排序（方便人工檢查）
    df.sort_values(
        by=['material', 'object_label', 'cluster'],
        ascending=[True, False, True],
        inplace=True
    )

    # 輸出更新後的 CSV
    output_path = os.path.join(
        os.path.dirname(data_path),
        f'pointcloud_{img_num}_clustered.csv'
    )
    df.to_csv(output_path, index=False)

    return {
        'cluster_path': output_path
    }

# 範例呼叫：
if __name__ == "__main__":
    img_num = '20250329_193301'
    data_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'results',
        f'pointcloud_{img_num}_with_material.csv'
    )
    result = dbscan_clustering(data_file, img_num, eps=0.1, min_samples=5)
    print("[INFO] 分群結果已存於：", result['cluster_path'])
