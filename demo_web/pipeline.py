# demo_web/pipeline.py
import os, shutil, subprocess, platform
from realsense.no_cap import no_cap
from realsense.coor_reconstruct import *
from material_segmentation.object_detect import detect_objects
from material_segmentation.run_on_image_cpu import run_on_image_cpu
from material_segmentation.dbscan2 import dbscan_clustering
from material_segmentation.build_obs import build_obs_json
from material_segmentation.fds import generate_fds

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
MATL_DIR = os.path.join(BASE_DIR, 'material_segmentation')
SENS_DIR = os.path.join(BASE_DIR, 'realsense')

def run_media_bat():
    bat = os.path.join(DEMO_DIR, 'process_media.bat')
    res = subprocess.run(['cmd','/c', bat], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    return res.stdout


def run_pipeline(pic_input: str) -> dict:
    if pic_input.endswith('.bag'):
        bag_file = pic_input
    try:
        # 1. Realsense
        # bag_file = os.path.join(SENS_DIR, 'bags', '20250311_140524.bag')
        real_out = no_cap(SENS_DIR, bag_file)
        world_coordinates(bag_file, real_out['pointcloud'])
        
        # 2. Object detection
        point_path = real_out['pointcloud']
        saved_path = os.path.join(BASE_DIR, 'material_segmentation')
        obj_out = detect_objects(point_path, saved_path)
        
        # 3. Material segmentation
        img_num = real_out['timestamp']
        img_path = real_out['projection']
        point_path = obj_out['object_csv']
        print(f'[INFO] {img_num}')
        print(f'[INFO] {img_path}')
        print(f'[INFO] {obj_out}')
        seg_out = run_on_image_cpu(MATL_DIR, img_num, img_path, point_path)
        
        # 4. DBSCAN clustering
        db_out = dbscan_clustering(seg_out['output_csv'], img_num)
        
        # 5. build obstacle json file
        js_out = build_obs_json(db_out['cluster_path'])
        
        # 6. write fds file
        static_json_file = os.path.join(MATL_DIR, 'static.json')
        fds_input = os.path.join(MATL_DIR, 'fds_output', 'room_simulation.fds')
        generate_fds(js_out['output_json'], static_json_file, fds_input)
        
        # 7. FDS init + 執行
        system = platform.system().lower()
        fds_local, fds_dir = "", ""
        if system == 'linux':
            fds_local = r"/home/huaxin/FDS-SMV/bin/fds"
            fds_dir = os.path.dirname(fds_input)
            shutil.copy2(fds_local, os.path.join(fds_dir, 'fds_local.bat'))
            cmd = f'cd {fds_dir}&& fds room_simulation.fds && smokeview -runscript room_simulation'
        elif system == 'windows':
            fds_local = r"D:\CSIE_project\FDS\FDS6\bin\fds_local.bat"
            fds_dir = os.path.dirname(fds_input)
            shutil.copy2(fds_local, os.path.join(fds_dir, 'fds'))
            cmd = f'cd {fds_dir}&& fds_local room_simulation.fds && smokeview -runscript room_simulation'
        # 先建立自動化腳本 .ssf 檔案
        ssf_path = os.path.join(fds_dir, 'room_simulation.ssf')
        with open(ssf_path, 'w') as f:
            # f.write('LOADINIFILE\n')
            # f.write(' room_simulation.ini\n')
            # f.write('SETVIEWPOINT\n')
            # f.write(' view1')
            f.write('LOAD3DSMOKE\n')
            f.write(' TEMPERATURE\n')
            # &SLCF PBY=2, QUANTITY='TEMPERATURE'
            f.write('LOADSLCF\n')
            f.write(' PBY=2, QUANTITY=TEMPERATURE\n')
            f.write('RENDERALL\n')
            f.write('1 0\n')
            f.write('room_simulation\n')
            f.write('MAKEMOVIE\n')
            f.write('movie_fire\n')
            f.write('room_simulation\n')
            f.write('10\n')

            f.write('LOAD3DSMOKE\n')
            f.write(' SOOT DENSITY\n')
            # &SLCF PBY=2, QUANTITY='TEMPERATURE'
            f.write('LOADSLCF\n')
            f.write(' PBY=2, QUANTITY=TEMPERATURE\n')
            f.write('RENDERALL\n')
            f.write('1 0\n')
            f.write('room_simulation\n')
            f.write('MAKEMOVIE\n')
            f.write('movie_smoke\n')
            f.write('room_simulation\n')
            f.write('10\n')

        # 修改執行命令，加上 -script 執行腳本
        subprocess.run(cmd, cwd=fds_dir, shell=True)

        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)

        return {'fds_log': proc.stdout, 'segmentation': seg_out, 'realsense': real_out}
    
    except Exception as e:
        raise RuntimeError(f"Pipeline 執行過程中發生錯誤: {str(e)}")

def test_fds_subprocess(pic_input: str) -> None:
    # 7. FDS init + 執行
    fds_local = r"D:\CSIE_project\FDS\FDS6\bin\fds_local.bat"
    fds_input = os.path.join(MATL_DIR, 'fds_output', 'room_simulation.fds')
    fds_dir = os.path.dirname(fds_input)
    shutil.copy2(fds_local, os.path.join(fds_dir, 'fds_local.bat'))
    # 先建立自動化腳本 .ssf 檔案
    ssf_path = os.path.join(fds_dir, 'room_simulation.ssf')
    with open(ssf_path, 'w') as f:
        # f.write('LOADINIFILE\n')
        # f.write(' room_simulation.ini\n')
        # f.write('SETVIEWPOINT\n')
        # f.write(' view1')
        f.write('LOAD3DSMOKE\n')
        f.write(' TEMPERATURE\n')
        # &SLCF PBY=2, QUANTITY='TEMPERATURE'
        f.write('LOADSLCF\n')
        f.write(' PBY=2, QUANTITY=TEMPERATURE\n')
        f.write('RENDERALL\n')
        f.write('1 0\n')
        f.write('room_simulation\n')
        f.write('MAKEMOVIE\n')
        f.write('movie_fire\n')
        f.write('room_simulation\n')
        f.write('10\n')

        f.write('LOAD3DSMOKE\n')
        f.write(' SOOT DENSITY\n')
        # &SLCF PBY=2, QUANTITY='TEMPERATURE'
        f.write('LOADSLCF\n')
        f.write(' PBY=2, QUANTITY=TEMPERATURE\n')
        f.write('RENDERALL\n')
        f.write('1 0\n')
        f.write('room_simulation\n')
        f.write('MAKEMOVIE\n')
        f.write('movie_smoke\n')
        f.write('room_simulation\n')
        f.write('10\n')
    

    # 修改執行命令，加上 -script 執行腳本
    subprocess.run(cmd, cwd=fds_dir, shell=True)

    # proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    # if proc.returncode != 0:
    #     raise RuntimeError(proc.stderr)

def test_votenet(csv_path):
    # 3. Material segmentation
    img_num = '20250329_193301'
    img_path = os.path.join(SENS_DIR, f'projections/projection_{img_num}.png')
    point_path = csv_path
    seg_out = run_on_image_cpu(MATL_DIR, img_num, img_path, point_path)
    
    # 4. DBSCAN clustering
    db_out = dbscan_clustering(seg_out['output_csv'], img_num)
    
    # 5. build obstacle json file
    js_out = build_obs_json(db_out['cluster_path'])
    
    # 6. write fds file
    static_json_file = os.path.join(MATL_DIR, 'static.json')
    fds_input = os.path.join(MATL_DIR, 'fds_output', 'room_simulation.fds')
    generate_fds(js_out['output_json'], static_json_file, fds_input)
    
    # 7. FDS init + 執行
    system = platform.system().lower()
    fds_local, fds_dir = "", ""
    if system == 'linux':
        fds_local = r"/home/huaxin/FDS-SMV/bin/fds"
        fds_dir = os.path.dirname(fds_input)
        shutil.copy2(fds_local, os.path.join(fds_dir, 'fds_local.bat'))
        cmd = f'cd {fds_dir}&& fds room_simulation.fds && smokeview -runscript room_simulation'
    elif system == 'windows':
        fds_local = r"D:\CSIE_project\FDS\FDS6\bin\fds_local.bat"
        fds_dir = os.path.dirname(fds_input)
        shutil.copy2(fds_local, os.path.join(fds_dir, 'fds'))
        cmd = f'cd {fds_dir}&& fds_local room_simulation.fds && smokeview -runscript room_simulation'
    # 先建立自動化腳本 .ssf 檔案
    ssf_path = os.path.join(fds_dir, 'room_simulation.ssf')
    with open(ssf_path, 'w') as f:
        f.write('LOAD3DSMOKE\n')
        f.write(' TEMPERATURE\n')
        # &SLCF PBY=2, QUANTITY='TEMPERATURE'
        f.write('LOADSLCF\n')
        f.write(' PBY=2, QUANTITY=TEMPERATURE\n')
        f.write('RENDERALL\n')
        f.write('1 0\n')
        f.write('room_simulation\n')
        f.write('MAKEMOVIE\n')
        f.write('movie\n')
        f.write('room_simulation\n')
        f.write('10\n')

    # 修改執行命令，加上 -script 執行腳本
    subprocess.run(cmd, cwd=fds_dir, shell=True)

    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)

    return {'fds_log': proc.stdout, 'segmentation': seg_out, 'realsense': real_out}
    

# only for testing
if __name__ == "__main__":
    # # data_path = os.path.join(DEMO_DIR, '20250311_140524.bag')
    # data_path = os.path.join(DEMO_DIR, '20250311_141600.bag')
    # # result = run_pipeline(pic_input=data_path)
    # run_pipeline(data_path)

    test_votenet(os.path.join(MATL_DIR, 'results', 'pointcloud_20250329_193301_with_objects.csv'))
