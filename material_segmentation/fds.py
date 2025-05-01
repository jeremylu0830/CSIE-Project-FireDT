import json
import os

MATERIAL_COLORS = {
    'brick': (139, 69, 19),
    'carpet': (128, 0, 128),
    'ceramic': (220, 220, 220),
    'fabric': (255, 182, 193),
    'foliage': (34, 139, 34),
    'food': (255, 165, 0),
    'glass': (173, 216, 230),
    'hair': (101, 67, 33),
    'leather': (160, 82, 45),
    'metal': (192, 192, 192),
    'mirror': (200, 200, 200),
    'other': (128, 128, 128),
    'painted': (255, 255, 255),
    'paper': (255, 250, 240),
    'plastic': (0, 191, 255),
    'polishedstone': (176, 196, 222),
    'skin': (255, 224, 189),
    'sky': (135, 206, 235),
    'stone': (169, 169, 169),
    'tile': (176, 224, 230),
    'wallpaper': (245, 245, 220),
    'water': (0, 191, 255),
    'wood': (139, 69, 19)
}

def generate_fds(input_json_path, static_json_path, output_fds_path):
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(static_json_path, 'r', encoding='utf-8') as f:
        static_table = json.load(f)

    space_dimensions = data['space_dimensions']
    objects = data['objects']
    
    with open(output_fds_path, 'w') as f:
        f.write("&HEAD CHID='room_simulation', TITLE='Room with detected objects' /\n\n")
        f.write("&TIME T_END=0.0 /\n\n")
        f.write("&REAC ID='POLYURETHANE'\n")
        f.write("      FUEL='REAC_FUEL'\n")
        f.write("      C=6.3\n")
        f.write("      H=7.1\n")
        f.write("      O=2.1\n")
        f.write("      N=1.0\n")
        f.write("      SOOT_YIELD=0.10\n")
        f.write("      HEAT_OF_COMBUSTION=24000.\n")
        f.write("      IDEAL=.TRUE. /\n\n")
        f.write(f"&MESH IJK={int(space_dimensions['x'] * 10)},{int(space_dimensions['z'] * 10)},{int(space_dimensions['y'] * 10)}, XB=0.0,{space_dimensions['x']:.1f},0.0,{space_dimensions['z']:.1f},0.0,{space_dimensions['y']:.1f} /\n\n")
        print(int(space_dimensions['x'] * 10), int(space_dimensions['z'] * 10), int(space_dimensions['y'] * 10))

        f.write("! Material surface definitions\n")
        f.write("&SURF ID='FIRE'\n")
        f.write("      HRRPUA=1000.\n")
        f.write("      COLOR='RED' /\n\n")
        materials = ['leather', 'metal', 'other']
        for material in materials:
            rgb = MATERIAL_COLORS.get(material, (140, 140, 140))
            f.write(f"&SURF ID='{material}'\n")
            f.write(f"      RGB={rgb[0]},{rgb[1]},{rgb[2]}\n")
            f.write("      BACKING='VOID' /\n\n")

        f.write("! Object definitions\n")
        for obj in objects:
            bounds = obj['bounds']
            object_label = obj['object_label']
            cluster_id = obj.get('cluster_id', 'N/A')
        
            f.write(f"! {object_label} (Cluster {cluster_id})\n")
            if object_label == "chair":
                chair_params = static_table.get("chair", {})
                dims = chair_params.get("default_dimensions", {})
                seat_width   = dims.get("seat_width", 0.5)
                seat_depth   = dims.get("seat_depth", 0.5)
                seat_thick   = dims.get("seat_thickness", 0.1)
                backrest_h   = dims.get("backrest_height", 0.5)
                leg_length   = dims.get("leg_length", 0.45)
                leg_bias     = chair_params.get("leg_bias", 0.05)
                x_center = (bounds['x_min'] + bounds['x_max']) / 2
                y_center = (bounds['z_min'] + bounds['z_max']) / 2
                z_center = (bounds['y_min'] + bounds['y_max']) / 2
                
                # 椅面 (seat)
                x_min = x_center - seat_width / 2
                x_max = x_center + seat_width / 2
                y_min = y_center - seat_depth / 2
                y_max = y_center + seat_depth / 2
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min:.3f},{y_max:.3f},"
                        f"{z_center:.3f},{z_center + seat_thick:.3f}, "
                        f"SURF_ID='leather' /\n\n")
                
                # 椅腳 (legs)
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
                
                # 椅背 (backrest)
                back_thick = 0.1
                f.write(f"&OBST XB={x_min:.3f},{x_max:.3f},"
                        f"{y_min - back_thick:.3f},{y_min:.3f},"
                        f"{z_center + seat_thick:.3f},{z_center + seat_thick + backrest_h:.3f}, "
                        f"SURF_ID='leather' /\n\n")
            else:
                f.write(f"&OBST XB={bounds['x_min']:.3f},{bounds['x_max']:.3f},"
                        f"{bounds['z_min']:.3f},{bounds['z_max']:.3f},"
                        f"{bounds['y_min']:.3f},{bounds['y_max']:.3f}, "
                        f"SURF_ID='other' /\n\n")

        f.write("! Fire source\n")
        f.write(f"&OBST XB={space_dimensions['x']/2 - 0.5:.3f},{space_dimensions['x']/2 + 0.5:.3f},"
                f"{space_dimensions['z']/2 - 0.5:.3f},{space_dimensions['z']/2 + 0.5:.3f},"
                f"0.0,0.5, COLOR='RED', SURF_ID='FIRE' /\n")
        f.write("&SLCF PBY=2, QUANTITY='TEMPERATURE' /\n\n")
        f.write("&TAIL /\n")

# only for testing
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_json = os.path.join(BASE_DIR, "room_simulation.json")
    static_json = os.path.join(BASE_DIR, "static.json")
    output_fds = os.path.join(BASE_DIR, "fds_output", "room_simulation.fds")
    generate_fds(input_json, static_json, output_fds)
