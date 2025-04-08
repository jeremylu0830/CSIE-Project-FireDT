import pandas as pd
import os
from sklearn.cluster import DBSCAN

# 讀取原始 CSV 檔案，並設定 low_memory=False 以避免型態警告
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
img_num = '20250329_193301'
data_path = os.path.join(os.path.dirname(BASE_DIR), 'realsense', 'pointclouds', f'pointcloud_{img_num}_with_material.csv')
data = pd.read_csv(data_path, low_memory=False)

# 如果需要可以篩選特定的 label，例如：
labels_to_extract = ['chair', 'tv', 'person']
data = data[data['object_label'].isin(labels_to_extract)]

# 提取 x, y, z 特徵用於分群
X = data[['x', 'y', 'z']]

# 設定 DBSCAN 參數，eps 表示鄰域半徑，min_samples 表示每個鄰域內的最小點數
dbscan = DBSCAN(eps=0.1, min_samples=5)
clusters = dbscan.fit_predict(X)

# 將分群結果加入原始資料中
data['cluster'] = clusters
data.sort_values(by=['object_label', 'cluster'], ascending=[True, False], inplace=True)

# 將帶有分群結果的資料存成新的 CSV 檔案
data.to_csv(data_path, index=False)
