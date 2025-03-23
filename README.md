# Indoor Fire Simulation System based on Digital Twin
> Capstone Project -- Department of Computer Science

## Overview

This project aims to integrate material segmentation, image processing, and 3D visualization using depth and color streams from a Realsense camera. It includes modules for material estimation, segmentation, and point cloud visualization. The project is structured into multiple components:

- **demo_web**: A Flask web application for uploading media files and processing them.
- **material_segmentation**: Contains the material segmentation code and pre-trained models for identifying and estimating materials in images.
- **realsense**: Contains scripts for handling point cloud data and projecting 3D information using Intel Realsense devices.


## Prequisites

Before we start, make sure you have installed Anaconda.

## Installation

To run this project, first change directory to this repository, then run command below:
```
conda env create -f environment.yml
```
```
conda activate fire-dt
```

## Material Segmentation
The material segmentation code can be run on images to detect different materials. The segmentation model is based on Googlenet and can be executed either on CPU or GPU.

To run the segmentation on an image by CPU-based segmentation:
```
python material_segmentation/run_on_image_cpu.py
```
