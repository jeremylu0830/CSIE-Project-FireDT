import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(BASE_DIR, 'demo_web')
MATL_DIR = os.path.join(BASE_DIR, 'material_segmentation')
SENS_DIR = os.path.join(BASE_DIR, 'realsense')
FILE_DIR = os.path.join(DEMO_DIR, 'results')

MATERIAL_COLORS = {
    'brick': (139, 69, 19),
    'carpet': (128, 0, 128),
    'ceramic': (220, 220, 220),
    'fabric': (255, 182, 193),
    'foliage': (34, 139, 34),
    'food': (255, 165, 0),
    'glass': (0, 255, 255),
    'hair': (101, 67, 33),
    'leather': (51, 0, 102),
    'metal': (192, 192, 192),
    'mirror': (200, 200, 200),
    'other': (128, 128, 128),
    'painted': (255, 255, 255),
    'paper': (255, 250, 240),
    'plastic': (0, 0, 0),
    'polishedstone': (176, 196, 222),
    'skin': (255, 224, 189),
    'sky': (135, 206, 235),
    'stone': (169, 169, 169),
    'tile': (176, 224, 230),
    'wallpaper': (245, 245, 220),
    'water': (0, 191, 255),
    'wood': (160, 82, 45)
}

# 依序是：註解、比熱、導熱率、密度、放射率、燃燒熱
MATL_PARAM = {
    'Leather': ['pyrosim Fabric', 1.0, 0.1, 100, 0, 15000],
    'Metal': ['pyrosim Steel', 0.46, 45.8, 7850, 0.95, 0],
    'Plastic': ['pyrosim PVC', 1.0, 0.1, 1380, 0.95, 13000],
    'Wood': ['pyrosim Yello Pine', 2.85, 0.14, 640, 0, 0],
    'Ceramic': ['pyrosim Gypsum', 1.09, 0.17, 930, 0, 0],
    'Foam': ['pyrosim Foam', 1.0, 0.05, 40, 0, 30000],
    'Glass': ['pyrosim Glass', 0.835, 1.4, 2225, 0, 0],
}

# SURF 可將複合種 MATL 套用到實際表面
SURF_PARAM = {
    'upholstery': {
        'rgb': (70, 93, 228),
        'burn_away': True,
        'backing': 'INSULATED',
        'layers': [
            {'matl_id': 'Leather', 'mass_fraction': 1.0, 'thickness': 0.001},
            {'matl_id': 'Foam',   'mass_fraction': 1.0, 'thickness': 1.0}
        ]
    },
    'metal': {
        'rgb': MATERIAL_COLORS['metal'],
        'burn_away': False,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Metal', 'mass_fraction': 1.0, 'thickness': 0.01}
        ]
    },
    'plastic': {
        'rgb': MATERIAL_COLORS['plastic'],
        'burn_away': True,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Plastic', 'mass_fraction': 1.0, 'thickness': 0.011}
        ]
    },
    'wood': {
        'rgb': MATERIAL_COLORS['wood'],
        'burn_away': False,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Wood', 'mass_fraction': 1.0, 'thickness': 0.01}
        ]
    },
    'ceramic': {
        'rgb': MATERIAL_COLORS['ceramic'],
        'burn_away': False,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Ceramic', 'mass_fraction': 1.0, 'thickness': 0.013}
        ]
    },
    'foam': {
        'rgb': (200, 200, 200),
        'burn_away': False,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Foam', 'mass_fraction': 1.0, 'thickness': 0.05}
        ]
    },
    'glass': {
        'rgb': MATERIAL_COLORS['glass'],
        'burn_away': False,
        'backing': 'VOID',
        'layers': [
            {'matl_id': 'Glass', 'mass_fraction': 1.0, 'thickness': 0.01}
        ]
    }
}

def generate_object_fds(obj, static_table, f):
    label = obj['object_label']
    bounds = obj['bounds']
    tmpl = static_table['object_templates'].get(label)
    if not tmpl:
        return

    # 計算中心點
    x_center = (bounds['x_min'] + bounds['x_max']) / 2
    y_center = (bounds['z_min'] + bounds['z_max']) / 2
    z_center = (bounds['y_min'] + bounds['y_max']) / 2

    defaults = tmpl['default_dimensions']
    comps = tmpl['components']
    z_offset = 0
    if "legs" in comps:
        z_offset = abs(comps["legs"]["dimensions"]["height"])

    for name, comp in comps.items():
        # 支援單一或多重 offset
        offsets = comp.get('position_offsets') or [comp.get('position_offset', [0,0,0])]
        # 讀取尺寸（若未定義則 fallback 到 default_dimensions）
        dims = comp.get('dimensions', {})
        w = dims.get('width', defaults.get(f"{name}_width", 1.0))
        d = dims.get('depth', defaults.get(f"{name}_depth", 1.0))
        h = dims.get('height', defaults.get(f"{name}_height", 1.0))

        # 試著從 defaults 取半尺寸，找不到就自己算
        half_w = defaults.get(f"{name}_half_width", w / 2)
        half_d = defaults.get(f"{name}_half_depth", d / 2)

        # offsets 的元素數量: 代表這個 comp 有幾份 
        for off in offsets:
            x_pos = x_center + off[0]
            y_pos = y_center + off[1]
            z_pos = z_center + off[2]

            # 計算六個邊界
            x_min = x_pos - half_w
            x_max = x_pos + half_w
            y_min = y_pos - half_d
            y_max = y_pos + half_d
            z_min = z_offset
            z_max = z_offset + h
            
            # 如果是窗，則 z 軸的 min/max 需要調整
            if label == 'window' and name == 'frame':
                z_min = 0.95
                z_max = 1.0
            elif label == 'window':
                z_min = 1.0
                z_max = 2.0

            # 替換模板
            code = comp['FDS_template']
            code = code.replace("{{x_pos_min}}", f"{x_min:.3f}")
            code = code.replace("{{x_pos_max}}", f"{x_max:.3f}")
            code = code.replace("{{y_pos_min}}", f"{y_min:.3f}")
            code = code.replace("{{y_pos_max}}", f"{y_max:.3f}")
            code = code.replace("{{z_pos_min}}", f"{z_min:.3f}")
            code = code.replace("{{z_pos_max}}", f"{z_max:.3f}")
            f.write(code + "\n")

    f.write(code + "\n")

def generate_fds(input_json_path, static_json_path, output_fds_path):
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(static_json_path, 'r', encoding='utf-8') as f:
        static_table = json.load(f)

    space_dimensions = data['space_dimensions']
    objects = data['objects']
    
    # 檢查是否有門或窗，若沒有則預設添加一個
    has_door = any(obj['object_label'] == 'door' for obj in objects)
    has_window = any(obj['object_label'] == 'window' for obj in objects)

    # 相當於在 build_obs.py 中的物件位置，所以 z_min 和 z_max 其實是 fds 的 y軸
    door_position = {'x_min': space_dimensions['x']-1.11, 'x_max': space_dimensions['x']-0.12, 'y_min': 0.0, 'y_max': 2.0, 'z_min': 0.0, 'z_max': 0.2}
    window_position = {'x_min': space_dimensions['x'] / 2 - 0.75, 'x_max': space_dimensions['x'] / 2 + 0.75, 
                       'y_min': 0.0, 'y_max': 0.0, 
                       'z_min': space_dimensions['z'], 'z_max': space_dimensions['z'] - 0.3}
    if not has_door:
        objects.append({'object_label': 'door', 'bounds': door_position, 'cluster_id': 'N/A'})
    if not has_window:
        objects.append({'object_label': 'window', 'bounds': window_position, 'cluster_id': 'N/A'})

    with open(output_fds_path, 'w') as f:
        # --- HEAD & TIME 區塊 (假設這裡已經有了) ---
        f.write("&HEAD CHID='room_simulation', TITLE='Room with detected objects' /\n\n")
        f.write("&TIME T_END=1.0 /\n\n")

        # --- DUMP 區塊 ---
        f.write("&DUMP COLUMN_DUMP_LIMIT=.TRUE., DT_RESTART=100.0, DT_SL3D=0.25 /\n\n")

        # --- RADI 區塊 ---
        f.write("&RADI RADTMP=300.0 /\n\n")

        # --- MESH 區塊 (使用動態空間尺寸) ---
        # 這裡假設 space_dimensions['x']、['y']、['z'] 分別是房間的 X、Y、Z 長度 (公尺)
        nx = int(space_dimensions['x'] * 10)
        ny = int(space_dimensions['y'] * 10)
        nz = int(space_dimensions['z'] * 10)
        f.write(f"&MESH ID='Meshes', IJK={nx},{nz},{ny}, "
                f"XB=0.0,{space_dimensions['x']:.1f},"
                f"0.0,{space_dimensions['z']:.1f},"
                f"0.0,{space_dimensions['y']:.1f} /\n\n")

        # --- SPEC 區塊 (固定七種 gas + PVC + AIR + PRODUCTS) ---
        f.write("&SPEC ID='OXYGEN',             LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='CARBON MONOXIDE',    LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='CARBON DIOXIDE',     LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='HYDROGEN CHLORIDE',  LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='SOOT',               LUMPED_COMPONENT_ONLY=.TRUE., FORMULA='C' /\n")
        f.write("&SPEC ID='NITROGEN',           LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='WATER VAPOR',        LUMPED_COMPONENT_ONLY=.TRUE. /\n")
        f.write("&SPEC ID='PVC',                FORMULA='C2H3Cl' /\n")
        f.write("&SPEC ID='AIR',               BACKGROUND=.TRUE.,\n")
        f.write("      SPEC_ID(1)='NITROGEN', SPEC_ID(2)='OXYGEN',\n")
        f.write("      VOLUME_FRACTION(1)=5.76, VOLUME_FRACTION(2)=1.53 /\n")
        f.write("&SPEC ID='PRODUCTS',\n")
        f.write("      SPEC_ID(1)='CARBON DIOXIDE', SPEC_ID(2)='CARBON MONOXIDE',\n")
        f.write("      SPEC_ID(3)='HYDROGEN CHLORIDE', SPEC_ID(4)='NITROGEN',\n")
        f.write("      SPEC_ID(5)='SOOT', SPEC_ID(6)='WATER VAPOR',\n")
        f.write("      VOLUME_FRACTION(1)=0.96, VOLUME_FRACTION(2)=0.14,\n")
        f.write("      VOLUME_FRACTION(3)=1.0,  VOLUME_FRACTION(4)=5.76,\n")
        f.write("      VOLUME_FRACTION(5)=0.9,  VOLUME_FRACTION(6)=1.0 /\n\n")

        # --- REAC 區塊 (PVC 燃燒反應) ---
        f.write("&REAC ID='PVC',\n")
        f.write("      HEAT_OF_COMBUSTION=1.64E4,\n")
        f.write("      FUEL='PVC',\n")
        f.write("      SPEC_ID_NU='PVC','AIR','PRODUCTS',\n")
        f.write("      NU=-1.0,-1.0,1.0 /\n\n")

        # --- DEVC 區塊 (共13 個探測器：12 個溫度 + 1 個輻射熱通量) ---
        # 前面 12 個 Device01~Device12 是量測不同座標的溫度
        device_coords = [
            (2.6, 1.9, 2.1), (2.6, 1.9, 1.8), (2.6, 1.9, 1.5),
            (2.6, 1.9, 1.2), (2.6, 1.9, 0.9), (2.6, 1.9, 0.6),
            (5.5, 1.8, 2.1), (5.5, 1.8, 1.8), (5.5, 1.8, 1.5),
            (5.5, 1.8, 1.2), (5.5, 1.8, 0.9), (5.5, 1.8, 0.6),
        ]
        for i, (x, y, z) in enumerate(device_coords, start=1):
            f.write(f"&DEVC ID='Device{str(i).zfill(2)}', QUANTITY='TEMPERATURE', XYZ={x},{y},{z} /\n")
        # Device19: 量測輻射熱通量
        f.write("&DEVC ID='Device19', QUANTITY='RADIATIVE HEAT FLUX', XYZ=2.6,1.9,0.0, IOR=3 /\n\n")

        # --- MATL ---
        f.write("! Material definitions\n")
        for matl_name, params in MATL_PARAM.items():
            f.write(f"&MATL ID='{matl_name}',\n")
            f.write(f"      FYI='{params[0]}',\n")
            f.write(f"      SPECIFIC_HEAT={params[1]},\n")
            f.write(f"      CONDUCTIVITY={params[2]},\n")
            f.write(f"      DENSITY={params[3]},\n")
            f.write(f"      EMISSIVITY={params[4]},\n") if params[4] else None
            f.write(f"      HEAT_OF_COMBUSTION={params[5]},\n") if params[5] else None
            f.write("      /\n\n")
            
        # --- SURF ---
        f.write("! Surface definitions\n")
        f.write("&SURF ID='FIRE',\n")
        f.write("      HRRPUA=1000.0,\n")
        f.write("      COLOR='RED' /\n\n")
        f.write("&SURF ID='exhaust', VOLUME_FLOW=1, COLOR='BLUE' /\n")
        for surf_name, params in SURF_PARAM.items():
            r, g, b = params['rgb']
            burn_away_flag = ".TRUE." if params['burn_away'] else ".FALSE."
            backing = params['backing']
            layers = params['layers']
            f.write(f"&SURF ID='{surf_name}',\n")
            f.write(f"      RGB={r},{g},{b},\n")
            if params['burn_away']:
                f.write(f"      BURN_AWAY={burn_away_flag},\n")
            f.write(f"      BACKING='{backing}',\n")
            # 如果有多層，就 chain 出 MATL_ID、MATL_MASS_FRACTION、THICKNESS
            # FDS 要求：MATL_ID(i,1)、MATL_MASS_FRACTION(i,1)、THICKNESS(i)
            # 例如一層： MATL_ID(1,1)='GYPSUM', MATL_MASS_FRACTION(1,1)=1.0, THICKNESS(1)=0.013
            for idx, layer in enumerate(layers, start=1):
                matl_id       = layer['matl_id']
                mass_frac     = layer['mass_fraction']
                thickness     = layer['thickness']
                f.write(f"      MATL_ID({idx},1)='{matl_id}',\n")
                f.write(f"      MATL_MASS_FRACTION({idx},1)={mass_frac},\n")
                f.write(f"      THICKNESS({idx})={thickness}")
                f.write(",\n" if idx < len(layers) else " /\n\n")

        # --- objects --- 
        f.write("! Object definitions\n")
        f.write("! Walls\n")
        f.write(f"&OBST XB=0,{space_dimensions['x']},0,0.1,0,{space_dimensions['y']}, SURF_ID='ceramic' /\n")
        f.write(f"&OBST XB=0,{space_dimensions['x']},{space_dimensions['z']-0.11},{space_dimensions['z']-0.01},0,{space_dimensions['y']}, SURF_ID='ceramic' /\n")
        f.write(f"&OBST XB=0.01,0.11,0,{space_dimensions['z']},0,{space_dimensions['y']}, SURF_ID='ceramic' /\n")
        f.write(f"&OBST XB={space_dimensions['x']-0.11},{space_dimensions['x']-0.01},0,{space_dimensions['z']},0,{space_dimensions['y']}, SURF_ID='ceramic' /\n\n")
        
        for obj in objects:
            bounds = obj['bounds']
            object_label = obj['object_label']
            cluster_id = obj.get('object_num', 'N/A')

            if object_label is not None:
                f.write(f"! {object_label} (Object {cluster_id})\n")

            generate_object_fds(obj, static_table, f)

        # # --- VENT ---
        # if not has_door:
        #     f.write(f"&VENT ID='VentDoor',\n")
        #     f.write(f"      XB={door_position['x_min']},{door_position['x_max']},{door_position['y_min']},{door_position['y_max']},{door_position['z_min']},{door_position['z_max']},\n")
        #     f.write(f"      SURF_ID='exhaust' /\n")
        # if not has_window:
        #     f.write(f"&VENT ID='VentWindow',\n")
        #     f.write(f"      XB={window_position['x_min']},{window_position['x_max']},{window_position['y_min']},{window_position['y_max']},{window_position['z_min']},{window_position['z_max']},\n")
        #     f.write(f"      SURF_ID='exhaust' /\n")
        
        # --- Fire Source / SLCF / TAIL ... ---
        f.write("! Fire source\n")
        f.write(f"&OBST XB={space_dimensions['x']/2 - 0.5:.3f},"
                f"{space_dimensions['x']/2 + 0.5:.3f},"
                f"{space_dimensions['z']/2 - 0.5:.3f},"
                f"{space_dimensions['z']/2 + 0.5:.3f},"
                f"0.0,0.5, COLOR='RED', SURF_ID='FIRE' /\n")

        f.write("&SLCF PBY=2, QUANTITY='TEMPERATURE' /\n\n")
        f.write("&TAIL /\n")

        
    print(f"[INFO] FDS 檔案已生成於：{output_fds_path}")

# only for testing
if __name__ == "__main__":
    input_json = os.path.join(FILE_DIR, 'test', "room_simulation.json")
    static_json = os.path.join(MATL_DIR, "static.json")
    output_fds = os.path.join(MATL_DIR, "fds_output", "room_simulation.fds")
    generate_fds(input_json, static_json, output_fds)
