import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 读取 NDVI 文件
file_path = "data/ndvi_kaisha_fixed.tiff"

with rasterio.open(file_path) as src:
    ndvi_data = src.read(1)  # 读取第一个波段
    ndvi_meta = src.meta  # 获取元数据（分辨率、投影等）

# 查看 NDVI 数据信息
print(f"NDVI 数据维度: {ndvi_data.shape}")
print(f"影像元数据: {ndvi_meta}")