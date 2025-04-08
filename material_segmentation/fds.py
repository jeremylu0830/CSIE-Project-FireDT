import json
import os

# 定義材質顏色對應表（RGB值）
MATERIAL_COLORS = {
    'brick': (139, 69, 19),      # 褐色
    'carpet': (128, 0, 128),     # 紫色
    'ceramic': (220, 220, 220),  # 淺灰色
    'fabric': (255, 182, 193),   # 粉紅色
    'foliage': (34, 139, 34),    # 綠色
    'food': (255, 165, 0),       # 橘色
    'glass': (173, 216, 230),    # 淺藍色
    'hair': (101, 67, 33),       # 深褐色
    'leather': (160, 82, 45),    # 棕色
    'metal': (192, 192, 192),    # 銀色
    'mirror': (200, 200, 200),   # 反光灰
    'other': (128, 128, 128),    # 灰色
    'painted': (255, 255, 255),  # 白色
    'paper': (255, 250, 240),    # 米白色
    'plastic': (0, 191, 255),    # 深天藍
    'polishedstone': (176, 196, 222),  # 石板藍
    'skin': (255, 224, 189),     # 膚色
    'sky': (135, 206, 235),      # 天藍色
    'stone': (169, 169, 169),    # 深灰色
    'tile': (176, 224, 230),     # 粉藍色
    'wallpaper': (245, 245, 220),# 米色
    'water': (0, 191, 255),      # 深藍色
    'wood': (139, 69, 19)        # 原木色
}

def generate_fds(input_json_path, static_json_path, output_fds_path):
    # 讀取 room_simulation.json 數據（來源：Realsense 坐標系）
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 讀取靜態資料表
    with open(static_json_path, 'r', encoding='utf-8') as f:
        static_table = json.load(f)
    
    # 獲取空間尺寸，注意 realsense 的空間尺寸仍使用原始數據，後續轉換在物件內進行
    space_dimensions = data['space_dimensions']
    objects = data['objects']
    
    # 開始寫入 FDS 文件
    with open(output_fds_path, 'w') as f:
        # 寫入頭部信息
        f.write("&HEAD CHID='room_simulation', TITLE='Room with detected objects' /\n\n")
        
        # 添加時間設定
        f.write("&TIME T_END=0.0 /\n\n")
        
        # 添加反應設定
        f.write("&REAC ID='POLYURETHANE'\n")
        f.write("      FUEL='REAC_FUEL'\n")
        f.write("      C=6.3\n")
        f.write("      H=7.1\n")
        f.write("      O=2.1\n")
        f.write("      N=1.0\n")
        f.write("      SOOT_YIELD=0.10\n")
        f.write("      HEAT_OF_COMBUSTION=24000.\n")
        f.write("      IDEAL=.TRUE. /\n\n")
        
        # 定義網格（此處以 room_simulation.json 的空間尺寸設定）
        f.write(f"&MESH IJK={int(space_dimensions['x'] * 10)},{int(space_dimensions['z'] * 10)},{int(space_dimensions['y'] * 10)}, XB=0.0,{space_dimensions['x']:.1f},0.0,{space_dimensions['z']:.1f},0.0,{space_dimensions['y']:.1f} /\n\n")
        print(int(space_dimensions['x'] * 10), int(space_dimensions['z'] * 10), int(space_dimensions['y'] * 10))
        
        # 定義材質表面屬性
        f.write("! Material surface definitions\n")
        
        # 添加火源表面定義
        f.write("&SURF ID='FIRE'\n")
        f.write("      HRRPUA=1000.\n")
        f.write("      COLOR='RED' /\n\n")
        
        # 添加基本材質表面定義 (範例中只定義 leather, metal, other)
        materials = ['leather', 'metal', 'other']
        for material in materials:
            rgb = MATERIAL_COLORS.get(material, (140, 140, 140))
            f.write(f"&SURF ID='{material}'\n")
            f.write(f"      RGB={rgb[0]},{rgb[1]},{rgb[2]}\n")
            f.write("      BACKING='VOID' /\n\n")
        
        # 寫入物件定義
        f.write("! Object definitions\n")
        for obj in objects:
            bounds = obj['bounds']
            object_label = obj['object_label']
            cluster_id = obj.get('cluster_id', 'N/A')
            
            # 輸出物件說明性註解
            f.write(f"! {object_label} (Cluster {cluster_id})\n")
            
            if object_label == "chair":
                # 從靜態資料表中讀取 chair 尺寸參數（單位皆假設為公尺）
                chair_params = static_table.get("chair", {})
                dims = chair_params.get("default_dimensions", {})
                seat_width   = dims.get("seat_width", 0.5)
                seat_depth   = dims.get("seat_depth", 0.5)
                seat_thick   = dims.get("seat_thickness", 0.1)
                backrest_h   = dims.get("backrest_height", 0.5)
                leg_length   = dims.get("leg_length", 0.45)
                leg_bias     = chair_params.get("leg_bias", 0.05)  # 椅腳偏移量
                
                # 根據 realsense 坐標系轉換到 FDS 坐標系：
                # FDS x 直接取 room x；FDS y 用 room 的 z；FDS z 用 room 的 y (垂直方向)
                x_center = (bounds['x_min'] + bounds['x_max']) / 2
                y_center = (bounds['z_min'] + bounds['z_max']) / 2
                z_center = (bounds['y_min'] + bounds['y_max']) / 2
                
                # 椅面 (seat)：
                # 水平平面以 x (seat 寬度) 及 y (seat 深度) 劃定，垂直方向以 z 來表示高度（座面厚度）
                x_min = x_center - seat_width / 2
                x_max = x_center + seat_width / 2
                y_min = y_center - seat_depth / 2
                y_max = y_center + seat_depth / 2
                # OBST: x: x_min ~ x_max, y: y_min ~ y_max, z: 從 z_center 到 z_center+seat_thick
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min:.3f},{y_max:.3f},"
                        f"{z_center:.3f},{z_center + seat_thick:.3f}, "
                        f"SURF_ID='leather' /\n\n")
                
                # 椅腳 (legs)：
                # 以椅面角落為基準：採用 [ (x_min, y_min), (x_min, y_max), (x_max, y_min), (x_max, y_max) ]
                # 每隻椅腳從 z: (z_center - leg_length) 到 z_center
                leg_positions = [
                    (x_min - leg_bias, y_min - leg_bias),
                    (x_min - leg_bias, y_max + leg_bias),
                    (x_max + leg_bias, y_min - leg_bias),
                    (x_max + leg_bias, y_max + leg_bias)
                ]
                for idx, (x_leg, y_leg) in enumerate(leg_positions):
                    f.write(f"&OBST XB={x_leg:.3f},{x_leg + 2*leg_bias:.3f},"
                            f"{y_leg:.3f},{y_leg + 2*leg_bias:.3f},"
                            f"{z_center - leg_length:.3f},{z_center:.3f}, "
                            f"SURF_ID='metal' /\n")
                f.write("\n")
                
                # 椅背 (backrest)：
                # 假設椅背設置於椅面後側，在 y 軸方向取較小的邊界 (y_min)：
                # 椅背厚度固定（例如 0.1 m），高度為 backrest_h，起始高度與座面上表接續：z_center + seat_thick
                back_thick = 0.1
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min - back_thick:.3f},{y_min:.3f},"
                        f"{z_center + seat_thick:.3f},{z_center + seat_thick + backrest_h:.3f}, "
                        f"SURF_ID='leather' /\n\n")
            else:
                # 非椅子物件：根據 realsense 坐標轉換到 FDS 坐標系
                # FDS XB: x：bounds['x_min']～bounds['x_max']
                #       y：用 room 的 z 軸 → bounds['z_min']～bounds['z_max']
                #       z：用 room 的 y 軸 → bounds['y_min']～bounds['y_max']
                f.write(f"&OBST XB={bounds['x_min']:.3f},{bounds['x_max']:.3f},"
                        f"{bounds['z_min']:.3f},{bounds['z_max']:.3f},"
                        f"{bounds['y_min']:.3f},{bounds['y_max']:.3f}, "
                        f"SURF_ID='other' /\n\n")
        
        # 添加火源（例如放在房間中心）
        # 此處注意空間尺寸仍採用 room_simulation.json 的座標，但仍沿用 x, y, z 概念
        f.write("! Fire source\n")
        f.write(f"&OBST XB={space_dimensions['x']/2 - 0.5:.3f},{space_dimensions['x']/2 + 0.5:.3f},"
                f"{space_dimensions['z']/2 - 0.5:.3f},{space_dimensions['z']/2 + 0.5:.3f},"
                f"0.0,0.5, COLOR='RED', SURF_ID='FIRE' /\n")
        f.write("&SLCF PBY=2, QUANTITY='TEMPERATURE' /\n\n")
        
        # 寫入結尾
        f.write("&TAIL /\n")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_json = os.path.join(BASE_DIR, "room_simulation.json")
    static_json = os.path.join(BASE_DIR, "static.json")  # 靜態資料表文件
    output_fds = os.path.join(BASE_DIR, "fds_output", "room_simulation.fds")
    generate_fds(input_json, static_json, output_fds)
