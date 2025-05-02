<<<<<<< HEAD
import pyrealsense2 as rs
import numpy as np
import pandas as pd
import os
import open3d as o3d

# 設定 .bag 檔案的路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bag_file = os.path.join(BASE_DIR, 'bags', '20250311_140524.bag')

# 讀取 CSV 檔案
csv_file = os.path.join(BASE_DIR, 'pointclouds', 'pointcloud_20250419_202146.csv')  # 用你的 CSV 檔案路徑
df = pd.read_csv(csv_file)

# 設定參考點
referencePoints_pixelDepth = [
    [475, 83, 691],
    [958, 130, 638],
    [330, 621, 551],
    [1395, 648, 577]
]

referencePoints_realWorld = np.array([
    [0.002, 0.3, 0.0, 1.0],
    [0.2468, 0.2415, 0.033, 1.0],
    [0.0, 0.0, 0.033, 1.0],
    [0.43, 0.0, 0.0, 1.0]
])

class ImageAndDepth2RealWorldTransformator:
    def __init__(self, intrinsics, referencePoints_pixelDepth, referencePoints_realWorld):
        self.intrinsics = intrinsics
        np_pixelDepth = np.array(referencePoints_pixelDepth)

        # Assert 檢查
        assert np_pixelDepth.shape[0] >= 4, "Array must have at least 4 rows"
        assert np_pixelDepth.shape[1] == 3, "Array must have exactly 3 columns"
        assert referencePoints_realWorld.shape[0] == np_pixelDepth.shape[0], "Arrays must have the same number of rows"
        assert referencePoints_realWorld.shape[1] == 4, "Array must have exactly 4 columns"
        assert np.all(referencePoints_realWorld[:, 3] == 1.0), "The fourth column must be 1"

        reference_points_vectorPoints = self.pixelDepth2VectorPoint_array(referencePoints_pixelDepth)

        self.realWorldHomogene = np.column_stack((referencePoints_realWorld[:, 0:3], np.ones(referencePoints_realWorld.shape[0]).T)).T

        vectorPoints_4D_with1 = np.ones(self.realWorldHomogene.shape)
        for i, p in enumerate(reference_points_vectorPoints):
            vectorPoints_4D_with1[0:3, i] = p

        self.transformationMatrixImage2RealWorld = np.dot(self.realWorldHomogene, np.linalg.pinv(vectorPoints_4D_with1))
        self.transformationMatrixRealWorld2Image = np.linalg.pinv(self.transformationMatrixImage2RealWorld)

        print("ImageAndDepth2RealWorldTransformator initialized and calibrated")
        print("transformationMatrixImage2RealWorld:\n", self.transformationMatrixImage2RealWorld)
        print("transformationMatrixRealWorld2Image:\n", self.transformationMatrixRealWorld2Image)

    def pixelDepth2VectorPoint(self, x, y, depth):
        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [x, y], depth)
        return np.array([point_x, point_y, point_z], dtype='float64')

    def pixelDepth2VectorPoint_array(self, pixelDepthArray):
        vectorPointsArray = []
        for pixelDepth in pixelDepthArray:
            vectorPointsArray.append(self.pixelDepth2VectorPoint(pixelDepth[0], pixelDepth[1], pixelDepth[2]))
        return vectorPointsArray

    def pixelDepth2RealWorld(self, x, y, depth):
        test_x, test_y, test_z = x, y, depth
        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [test_x, test_y], test_z)
        point = np.array([point_x, point_y, point_z], dtype='float64')

        vPoint = np.ones((1, 4))
        vPoint[0, 0:3] = point
        return np.dot(self.transformationMatrixImage2RealWorld, np.array(vPoint[0]))[0:3]


# 開啟 .bag 檔案
pipeline = rs.pipeline()
config = rs.config()

config.enable_device_from_file(bag_file)  # 用你的 .bag 檔案路徑
pipeline.start(config)

# 取得深度影像的內部參數
profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
depth_intrinsics = depth_profile.get_intrinsics()
color_intrinsics = color_profile.get_intrinsics()

# 初始化變換器，並傳入相機內參和參考點
imageAndDepth2RealWorldTransformator = ImageAndDepth2RealWorldTransformator(color_intrinsics, referencePoints_pixelDepth, referencePoints_realWorld)

# 創建 Open3D 點雲物件
point_cloud = o3d.geometry.PointCloud()

# 用來儲存點雲的 NumPy 陣列
points_list = []
colors_list = []

# 讀取 CSV 檔案並處理每一行
for index, row in df.iterrows():
    # 取得 CSV 中的 u, v, z (z*100)
    u = row['u']
    v = row['v']
    z = row['z'] * 100  # 這裡乘以 100 是你提到的要求
    R = row['R']
    G = row['G']
    B = row['B']

    # 將每個點的 [u, v, z*100] 當作測試點
    result = imageAndDepth2RealWorldTransformator.pixelDepth2RealWorld(u, v, z)
    # print(f"Test: {u}, {v}, {z}")
    # print("Result:", result)

    # 設置每個點的顏色 (RGB)
    color = np.array([B / 255.0, G / 255.0, R / 255.0])  # 顏色範圍 [0, 1], BGR -> RGB
    
    # 將 3D 點和顏色分別加入列表中
    points_list.append(result)
    colors_list.append(color)

# 將點和顏色轉換為 NumPy 陣列
points_array = np.array(points_list)
colors_array = np.array(colors_list)

# 將點雲的點和顏色設置到 Open3D 點雲物件中
point_cloud.points = o3d.utility.Vector3dVector(points_array)
point_cloud.colors = o3d.utility.Vector3dVector(colors_array)

# 顯示 3D 點雲
o3d.visualization.draw_geometries([point_cloud])

# 停止管道
pipeline.stop()
=======
import pyrealsense2 as rs
import numpy as np
import pandas as pd
import os
import open3d as o3d

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bag_file = os.path.join(BASE_DIR, 'bags', '20250311_140524.bag')
csv_file = os.path.join(BASE_DIR, 'pointclouds', 'pointcloud_20250419_202146.csv')
df = pd.read_csv(csv_file)
referencePoints_pixelDepth = [
    [475, 83, 691],
    [958, 130, 638],
    [330, 621, 551],
    [1395, 648, 577]
]
referencePoints_realWorld = np.array([
    [0.002, 0.3, 0.0, 1.0],
    [0.2468, 0.2415, 0.033, 1.0],
    [0.0, 0.0, 0.033, 1.0],
    [0.43, 0.0, 0.0, 1.0]
])

class ImageAndDepth2RealWorldTransformator:
    def __init__(self, intrinsics, referencePoints_pixelDepth, referencePoints_realWorld):
        self.intrinsics = intrinsics
        np_pixelDepth = np.array(referencePoints_pixelDepth)

        assert np_pixelDepth.shape[0] >= 4, "Array must have at least 4 rows"
        assert np_pixelDepth.shape[1] == 3, "Array must have exactly 3 columns"
        assert referencePoints_realWorld.shape[0] == np_pixelDepth.shape[0], "Arrays must have the same number of rows"
        assert referencePoints_realWorld.shape[1] == 4, "Array must have exactly 4 columns"
        assert np.all(referencePoints_realWorld[:, 3] == 1.0), "The fourth column must be 1"

        reference_points_vectorPoints = self.pixelDepth2VectorPoint_array(referencePoints_pixelDepth)

        self.realWorldHomogene = np.column_stack((referencePoints_realWorld[:, 0:3], np.ones(referencePoints_realWorld.shape[0]).T)).T

        vectorPoints_4D_with1 = np.ones(self.realWorldHomogene.shape)
        for i, p in enumerate(reference_points_vectorPoints):
            vectorPoints_4D_with1[0:3, i] = p

        self.transformationMatrixImage2RealWorld = np.dot(self.realWorldHomogene, np.linalg.pinv(vectorPoints_4D_with1))
        self.transformationMatrixRealWorld2Image = np.linalg.pinv(self.transformationMatrixImage2RealWorld)

        print("ImageAndDepth2RealWorldTransformator initialized and calibrated")
        print("transformationMatrixImage2RealWorld:\n", self.transformationMatrixImage2RealWorld)
        print("transformationMatrixRealWorld2Image:\n", self.transformationMatrixRealWorld2Image)

    def pixelDepth2VectorPoint(self, x, y, depth):
        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [x, y], depth)
        return np.array([point_x, point_y, point_z], dtype='float64')

    def pixelDepth2VectorPoint_array(self, pixelDepthArray):
        vectorPointsArray = []
        for pixelDepth in pixelDepthArray:
            vectorPointsArray.append(self.pixelDepth2VectorPoint(pixelDepth[0], pixelDepth[1], pixelDepth[2]))
        return vectorPointsArray

    def pixelDepth2RealWorld(self, x, y, depth):
        test_x, test_y, test_z = x, y, depth
        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [test_x, test_y], test_z)
        point = np.array([point_x, point_y, point_z], dtype='float64')

        vPoint = np.ones((1, 4))
        vPoint[0, 0:3] = point
        return np.dot(self.transformationMatrixImage2RealWorld, np.array(vPoint[0]))[0:3]

pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file)
pipeline.start(config)

profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
depth_intrinsics = depth_profile.get_intrinsics()
color_intrinsics = color_profile.get_intrinsics()

imageAndDepth2RealWorldTransformator = ImageAndDepth2RealWorldTransformator(color_intrinsics, referencePoints_pixelDepth, referencePoints_realWorld)

point_cloud = o3d.geometry.PointCloud()

points_list = []
colors_list = []
for index, row in df.iterrows():
    u = row['u']
    v = row['v']
    z = row['z'] * 100
    R = row['R']
    G = row['G']
    B = row['B']

    result = imageAndDepth2RealWorldTransformator.pixelDepth2RealWorld(u, v, z)
    # print(f"Test: {u}, {v}, {z}")
    # print("Result:", result)

    color = np.array([B / 255.0, G / 255.0, R / 255.0])
    points_list.append(result)
    colors_list.append(color)

points_array = np.array(points_list)
colors_array = np.array(colors_list)
point_cloud.points = o3d.utility.Vector3dVector(points_array)
point_cloud.colors = o3d.utility.Vector3dVector(colors_array)
o3d.visualization.draw_geometries([point_cloud])

pipeline.stop()
>>>>>>> upstream/master
