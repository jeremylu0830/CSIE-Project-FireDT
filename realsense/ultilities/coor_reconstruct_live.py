
import pyrealsense2 as rs
import numpy as np

class ImageAndDepth2RealWorldTransformator:

    def __init__(self, intrinsics, referencePoints_pixelDepth, referencePoints_realWorld):
        # EXAMPLE
        # referencePoints_pixelDepth = [
        #     [475, 83, 691],
        #     [958, 130, 638],
        #     [330, 621, 551],
        #     [1395, 648, 577]
        # ]
        #
        # referencePoints_realWorld = np.array([  # a 1.0 is needed as fourth dimension
        #     [0.002, 0.3, 0.0, 1.0],
        #     [0.2468, 0.2415, 0.033, 1.0],
        #     [0.0, 0.0, 0.033, 1.0],
        #     [0.43, 0.0, 0.0, 1.0]
        # ])

        self.intrinsics = intrinsics
        np_pixelDepth = np.array(referencePoints_pixelDepth)

        # Assert-Anweisungen zur Überprüfung der Form
        assert np_pixelDepth.shape[0] >= 4, "Array muss mindestens 4 Zeilen haben"
        assert np_pixelDepth.shape[1] == 3, "Array muss genau 3 Spalten haben"

        assert referencePoints_realWorld.shape[0] == np_pixelDepth.shape[0], "Die Arrays müssen die gleiche Anzahl von Zeilen haben"
        assert referencePoints_realWorld.shape[1] == 4, "Das Array muss genau 4 Spalten haben"
        assert np.all(referencePoints_realWorld[:, 3] == 1.0), "Die vierte Spalte muss überall den Wert 1 haben"

        # siehe Doku in pixelDepth2VectorPoint
        reference_points_vectorPoints = self.pixelDepth2VectorPoint_array(referencePoints_pixelDepth)

        # erstellt eine Matrix, die verwendet werden kann, um homogene Koordinaten zu berechnen.
        # Der Ausdruck referencePoints_realWorld[:, 0:3] extrahiert die ersten drei Spalten der referencePoints_realWorld-Matrix, was die x-, y- und z-Koordinaten der Referenzpunkte sind. Das Resultat hat die Form (4, 3).
        # Der Ausdruck np.ones(referencePoints_realWorld.shape[0]).T erzeugt einen Vektor aus Einsen der Länge 4, der die homogenen Koordinaten darstellt.
        # np.column_stack((referencePoints_realWorld[:, 0:3], np.ones(referencePoints_realWorld.shape[0]).T)) fügt diese beiden Arrays zusammen, wobei die Einsen als vierte Spalte hinzugefügt werden. Das Resultat hat die Form (4, 4).
        # Das .T transponiert das Array, sodass die Endform (4, 4) ist. Dies ist jedoch unnötig, da es bereits in der gewünschten Form vorliegt. Das .T könnte entfernt werden, um denselben Effekt zu erzielen.
        # Ergebnis:
        # realWorldHomogene wird eine (4, 4) numpy-Array sein, die die x-, y-, z-Koordinaten und die homogene Koordinate 1.0 der Referenzpunkte enthält.
        self.realWorldHomogene = np.column_stack((referencePoints_realWorld[:, 0:3], np.ones(referencePoints_realWorld.shape[0]).T)).T

        vectorPoints_4D_with1 = np.ones(self.realWorldHomogene.shape)
        for i, p in enumerate(reference_points_vectorPoints):
            # 4. Dimension ist dann die 1
            vectorPoints_4D_with1[0:3, i] = p

        self.transformationMatrixImage2RealWorld = np.dot(self.realWorldHomogene, np.linalg.pinv(vectorPoints_4D_with1))
        self.transformationMatrixRealWorld2Image = np.linalg.pinv(self.transformationMatrixImage2RealWorld)

        print("ImageAndDepth2RealWorldTransformator initialized and calibrated")
        print("transformationMatrixImage2RealWorld:\n", self.transformationMatrixImage2RealWorld)
        print("transformationMatrixRealWorld2Image:\n", self.transformationMatrixRealWorld2Image)
        print("-------------------")
        print("Sanity Test:")
        print("ImageDepth_to_realWorld")
        for ind, pt in enumerate(vectorPoints_4D_with1.T):
            print("Expected:", referencePoints_realWorld[ind][0:3], "Result:", np.dot(self.transformationMatrixImage2RealWorld, np.array(pt))[0:3])

        print("RealWorld_to_ImageDepth")
        for ind, pt in enumerate(referencePoints_realWorld):
            pt[3] = 1
            print("Expected:", vectorPoints_4D_with1.T[ind][0:3], "Result:", np.dot(self.transformationMatrixRealWorld2Image, np.array(pt))[0:3])


    def pixelDepth2VectorPoint(self, x,y,depth):
        # Umwandeln der pixel mit depth in Vector mit depth als z
        # Um die 3D-Vectorkoordinaten (X, Y, Z) aus Pixelkoordinaten (u, v) und der Tiefe d zu berechnen:
        # X = (u - c_x) * d / f_x
        # Y = (v - c_y) * d / f_y
        # Z = d
        # wobei:
        # u, v = Pixelkoordinaten
        # d = Tiefe
        # c_x, c_y = optisches Zentrum (Principal Point) der Kamera
        # f_x, f_y = Brennweiten der Kamera in x- und y-Richtung

        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [x,y], depth)
        return np.array([point_x, point_y, point_z], dtype='float64')


    def pixelDepth2VectorPoint_array(self, pixelDepthArray):
        vectorPointsArray = []
        for pixelDepth in pixelDepthArray:
            vectorPointsArray.append(self.pixelDepth2VectorPoint(pixelDepth[0], pixelDepth[1], pixelDepth[2]))
        return vectorPointsArray

    def pixelDepth2RealWorld(self, x,y,depth):
        reference_points_vectorPoints = []
        test_x, test_y, test_z  = x, y, depth
        point_x, point_y, point_z = rs.rs2_deproject_pixel_to_point(self.intrinsics, [test_x,test_y], test_z)
        point = np.array([point_x, point_y, point_z], dtype='float64')

        vPoint = np.ones((1, 4)) #np.ones(imageAndDepth2RealWorldTransformator.realWorldHomogene.shape)
        vPoint[0, 0:3] = point
        return np.dot(self.transformationMatrixImage2RealWorld, np.array(vPoint[0]))[0:3]


# Get intrinsics of realsense camera:

print("Connected Intel Realsense Camera devices:")
context = rs.context()
for device in context.devices:
    print(f"Device {device.get_info(rs.camera_info.name)} connected")

pipeline = rs.pipeline()

config = rs.config()
config.enable_stream(rs.stream.depth, rs.format.z16, 30)
config.enable_stream(rs.stream.color, rs.format.bgr8, 30)


# Start streaming
pipeline_profile = pipeline.start(config)

# Get stream profile and camera intrinsics
profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
depth_intrinsics = depth_profile.get_intrinsics()
color_intrinsics = color_profile.get_intrinsics()

# depth and color_intrinsics are different, depending on resolution
# Choose wisely which one you are calibrating!



referencePoints_pixelDepth = [
    [475, 83, 691],  # x,y,depth
    [958, 130, 638],
    [330, 621, 551],
    [1395, 648, 577]
]

referencePoints_realWorld = np.array([   
    [0.002, 0.3, 0.0,               1.0],   #x,y,z,1    the 1 is needed as 4th dimension, just set it to 1
    [0.2468, 0.2415, 0.033,         1.0],
    [0.0, 0.0, 0.033,               1.0],
    [0.43, 0.0, 0.0,                1.0]
])



imageAndDepth2RealWorldTransformator = ImageAndDepth2RealWorldTransformator(color_intrinsics, referencePoints_pixelDepth, referencePoints_realWorld)


print("Test: 450, 631, 585   #0.02 rechts von I2 und 0.033 tiefer")
r = imageAndDepth2RealWorldTransformator.pixelDepth2RealWorld(450, 631, 585)
print("Result:", r)

print("Test: 901,138,678     #0.02 links von I1 und 0.033 tiefer")
r = imageAndDepth2RealWorldTransformator.pixelDepth2RealWorld(901, 138, 678)
print("Result:", r)


# 打印深度影像解析度
print("Depth Resolution:", depth_intrinsics.width, "x", depth_intrinsics.height)

# 打印顏色影像解析度
print("Color Resolution:", color_intrinsics.width, "x", color_intrinsics.height)
