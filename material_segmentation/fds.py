import json

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

def generate_fds(input_json_path, output_fds_path):
    # 讀取JSON數據
    with open(input_json_path, 'r') as f:
        objects = json.load(f)

    # 開始寫入FDS文件
    with open(output_fds_path, 'w') as f:
        # 寫入頭部信息
        f.write("&HEAD CHID='room_simulation', TITLE='Room with detected objects' /\n\n")
        
        # # 添加時間設定 - 改為10秒
        # f.write("&TIME T_END=10.0 /\n\n")
        
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
        
        # 定義網格
        f.write("&MESH IJK=100,50,30, XB=0.0,10.0,0.0,5.0,0.0,3.0 /\n\n")
        
        # 定義材質表面屬性
        f.write("! Material surface definitions\n")
        written_materials = set()
        
        # 添加火源表面定義
        f.write("&SURF ID='FIRE'\n")
        f.write("      RGB=255,0,0\n")
        f.write("      HRRPUA=1000.0\n")
        f.write("      RAMP_Q='FIRE_RAMP' /\n\n")
        
        # 添加火源的時間曲線 - 調整為10秒內的變化
        f.write("&RAMP ID='FIRE_RAMP', T=0.0, F=0.0 /\n")
        f.write("&RAMP ID='FIRE_RAMP', T=2.0, F=1.0 /\n")
        f.write("&RAMP ID='FIRE_RAMP', T=8.0, F=1.0 /\n")
        f.write("&RAMP ID='FIRE_RAMP', T=10.0, F=0.0 /\n\n")
        
        # 定義其他材質
        for obj in objects:
            material_name = obj['material']['name']
            if material_name not in written_materials:
                rgb = MATERIAL_COLORS.get(material_name, (140, 140, 140))
                f.write(f"&SURF ID='{material_name}'\n")
                f.write(f"      RGB={rgb[0]},{rgb[1]},{rgb[2]}\n")
                f.write("      BACKING='VOID' /\n\n")
                written_materials.add(material_name)
        for material_name in ['leather', 'metal']:
            # 從 MATERIAL_COLORS 字典中獲取材質對應的 RGB 顏色值
            # 如果材質不在字典中,則使用默認灰色 (140,140,140)
            if material_name not in written_materials:
                rgb = MATERIAL_COLORS.get(material_name, (140, 140, 140))
                f.write(f"&SURF ID='{material_name}'\n")
                f.write(f"      RGB={rgb[0]},{rgb[1]},{rgb[2]}\n")
                f.write("      BACKING='VOID' /\n\n")
            
        # 寫入物件
        f.write("! Object definitions\n")
        for obj in objects:
            bounds = obj['bounds']
            material_name = obj['material']['name']
            object_name = obj['object_name']
            
            # 寫入物件註釋
            f.write(f"! {object_name} - {material_name}\n")
            x_center = (bounds['x_min'] + bounds['x_max']) / 2
            y_center = (bounds['y_min'] + bounds['y_max']) / 2
            z_center = (bounds['z_min'] + bounds['z_max']) / 2
            
            # bound
            bound = 0.25
            bias = 0.05
            x_min = x_center - bound
            x_max = x_center + bound
            y_min = y_center - bound
            y_max = y_center + bound

            if object_name == "chair":
                # 椅面
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min:.3f},{y_max:.3f},"
                        f"{z_center:.3f},{z_center+0.1:.3f}, "
                        f"SURF_ID='{material_name}' /\n\n")
                # 4 legs
                f.write(f"&OBST XB={x_min-bias:.3f},{x_min+bias:.3f},"
                       f"{y_min-bias:.3f},{y_min+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_min-bias:.3f},{x_min+bias:.3f},"
                       f"{y_max-bias:.3f},{y_max+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_max-bias:.3f},{x_max+bias:.3f},"
                       f"{y_min-bias:.3f},{y_min+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_max-bias:.3f},{x_max+bias:.3f},"
                       f"{y_max-bias:.3f},{y_max+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                # 椅背
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min:.3f},{y_min+0.1:.3f},"
                        f"{z_center+0.1:.3f},{z_center+0.1+0.6:.3f}, "
                        f"SURF_ID='leather' /\n\n")
            elif object_name == "dining table":
                # 桌面
                x_bound = 2
                y_bound = 1
                f.write(f"&OBST XB={x_center-x_bound:.3f},{x_center+x_bound:.3f},"
                        f"{y_center-y_bound:.3f},{y_center+y_bound:.3f},"
                        f"{z_center:.3f},{z_center+0.1:.3f}, "
                        f"SURF_ID='{material_name}' /\n")
                # 4 legs
                f.write(f"&OBST XB={x_center-x_bound-bias:.3f},{x_center-x_bound+bias:.3f},"
                       f"{y_center-y_bound-bias:.3f},{y_center-y_bound+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_center-x_bound-bias:.3f},{x_center-x_bound+bias:.3f},"
                       f"{y_center+y_bound-bias:.3f},{y_center+y_bound+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_center+x_bound-bias:.3f},{x_center+x_bound+bias:.3f},"
                       f"{y_center-y_bound-bias:.3f},{y_center-y_bound+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n")
                f.write(f"&OBST XB={x_center+x_bound-bias:.3f},{x_center+x_bound+bias:.3f},"
                       f"{y_center+y_bound-bias:.3f},{y_center+y_bound+bias:.3f},"
                       f"{0.0:.3f},{z_center:.3f}, "
                       f"SURF_ID='metal' /\n\n")
            else:
                f.write(f"&OBST XB={bounds['x_min']:.3f},{bounds['x_max']:.3f},"
                        f"{bounds['y_min']:.3f},{bounds['y_max']:.3f},"
                        f"{bounds['z_min']:.3f},{bounds['z_max']:.3f}, "
                        f"SURF_ID='{material_name}' /\n\n")
            
        
        # 添加火源（在房間中心位置）
        f.write("! Fire source\n")
        f.write("&OBST XB=4.5,5.5,2.0,3.0,0.0,0.5, COLOR='RED', SURF_ID='FIRE' /\n")
        f.write("&SLCF PBY = 2, QUANTITY='TEMPERATURE' /\n\n")
        # 寫入結尾
        f.write("&TAIL /")

if __name__ == "__main__":
    input_json = "room_simulation.json"
    output_fds = "fds_output\\room_simulation.fds"
    generate_fds(input_json, output_fds)