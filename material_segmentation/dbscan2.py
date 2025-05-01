import pandas as pd
import os
from sklearn.cluster import DBSCAN

def dbscan_clustering(data_path: str, img_num: str, labels_to_extract: list = None, eps: float = 0.1, min_samples: int = 5) -> dict:
    data = pd.read_csv(data_path, low_memory=False)
    # specific label extracting
    if labels_to_extract:
        data = data[data['object_label'].isin(labels_to_extract)]
    else:
        data = data[~data['object_label'].isna()]

    X = data[['x', 'y', 'z']]
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    clusters = dbscan.fit_predict(X)

    data['cluster'] = clusters
    data.sort_values(by=['object_label', 'cluster'], ascending=[True, False], inplace=True)
    output_data_path = os.path.join(os.path.dirname(data_path), f'pointcloud_{img_num}_clustered.csv')
    data.to_csv(output_data_path, index=False)
    
    return {
        'cluster_path': output_data_path,
    }

# only for testing
if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'pointcloud_with_objects.csv')
    img_num = '20250329_193301'
    labels_to_extract = ['chair', 'tv', 'person']
    dbscan_clustering(base_dir, img_num, labels_to_extract)

