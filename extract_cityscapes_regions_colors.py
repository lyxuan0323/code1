# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import time
from pathlib import Path

# Cityscapes 彩色分割图的部分类别颜色映射（RGB）
CITYSCAPES_COLORS = {
    "unlabeld": (0, 0, 0),
    "ego vehicle": (0, 0, 0),
    "rectification border": (0, 0, 0),
    "out of roi": (0, 0, 0),
    "static": (0, 0, 0),
    "dynamic": (111, 74, 0),
    "ground": (81, 0, 81),

    "road": (128, 64, 128),
    "people walk road": (243, 35, 232),
    "people1": (238, 121, 135),
    "people2": (254, 60, 147),
    "people3": (255, 60, 147),
    "building": (70, 70, 70),
    "vegetation": (105, 142, 33),
    "car": (81, 82, 198),
    "car2": (101, 47, 200),
    "pole": (152, 152, 152),
    "traffic sign": (220, 220, 0),

    "wall": (102, 102, 156),
    "fence": (190, 153, 153),
    "traffic light": (250, 170, 30),
    "terrain": (152, 251, 152),
    "sky": (70, 130, 180),
    "rider": (255, 0, 0),

    "truck": (0, 0, 70),
    "bus": (0, 60, 100),
    "train": (0, 80, 100),
    "motorcycle": (0, 0, 230),
    "bicycle": (119, 11, 32),
    "person": (220, 20, 60),
}


def extract_region_by_color(color_seg_img, target_color, tolerance=10):
    target = np.array(target_color, dtype=np.uint8)
    lower = np.clip(target - tolerance, 0, 255)
    upper = np.clip(target + tolerance, 0, 255)
    mask = cv2.inRange(color_seg_img, lower, upper)
    return mask


def visualize_result(original_img, mask, color, alpha=0.5):
    status = True

    if mask is None:
        status = False

    if original_img.shape[:2] != mask.shape[:2]:
        mask = cv2.resize(mask, (original_img.shape[1], original_img.shape[0]))
        status = False

    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        status = False

    if np.sum(mask == 255) == 0:
        mask = np.where(mask > 0, 255, 0).astype(np.uint8)
        if np.sum(mask == 255) == 0:
            status = False

    colored_mask = np.zeros_like(original_img)
    colored_mask[mask == 255] = color

    overlay = cv2.addWeighted(original_img, 1 - alpha, colored_mask, alpha, 0)
    return overlay, status


def do_one_parse_proc(basename):
    # ===== 开始计时（单幅图像）=====
    start_time = time.perf_counter()

    print("basename:", basename)

    if basename.startswith("panorama_"):
        street_view_name = basename[9:]
    else:
        street_view_name = basename

    color_seg_path = f"gsi/area/svgdata/svg_{street_view_name}"
    original_img_path = f"gsi/area/rectdata/rectified_panorama_{street_view_name}"

    if not os.path.exists(color_seg_path) or not os.path.exists(original_img_path):
        print(f"[跳过] 文件缺失：{basename}")
        return None

    color_seg_img = cv2.imread(color_seg_path)
    if color_seg_img is None:
        return None
    color_seg_img_rgb = cv2.cvtColor(color_seg_img, cv2.COLOR_BGR2RGB)

    original_img = cv2.imread(original_img_path)
    if original_img is None:
        return None

    os.makedirs("extract_cityscapes_regions_colors", exist_ok=True)

    mask_integral = np.zeros(original_img.shape[:2], dtype=np.uint8)

    for class_name, rgb_color in CITYSCAPES_COLORS.items():
        mask = extract_region_by_color(color_seg_img_rgb, rgb_color)

        if mask is None:
            continue

        if mask_integral.shape[:2] != mask.shape[:2]:
            mask = cv2.resize(mask, (mask_integral.shape[1], mask_integral.shape[0]))

        mask_integral += mask
        cv2.imwrite(
            f"extract_cityscapes_regions_colors/{class_name}_mask_{basename}", mask
        )

        if class_name == "building":
            overlay_color = (0, 140, 255)
            overlay_alpha = 0.7
        else:
            overlay_color = (rgb_color[2], rgb_color[1], rgb_color[0])
            overlay_alpha = 0.5

        overlay, status = visualize_result(
            original_img.copy(), mask, overlay_color, alpha=overlay_alpha
        )
        if not status:
            continue

        cv2.imwrite(
            f"extract_cityscapes_regions_colors/{class_name}_overlay_{basename}",
            overlay,
        )

    cv2.imwrite(
        f"extract_cityscapes_regions_colors/mask_integral_{basename}", mask_integral
    )

    # ===== 结束计时 =====
    elapsed_time = time.perf_counter() - start_time
    print(f"[耗时] {basename} 掩膜提取与可视化完成，用时 {elapsed_time:.3f} 秒")

    return elapsed_time


def get_file_extension(filename):
    path = Path(filename)
    ext_with_dot = path.suffix
    ext_without_dot = path.suffix.lstrip(".") if ext_with_dot else ""
    return ext_with_dot, ext_without_dot


if __name__ == "__main__":
    raw_files = set(os.listdir("gsi/area/rawdata"))

    processing_times = []

    for raw_file in raw_files:
        ext_dot, ext = get_file_extension(raw_file)
        if ext.lower() not in ["jpg", "jpeg", "png"]:
            continue

        elapsed = do_one_parse_proc(raw_file)
        if elapsed is not None:
            processing_times.append(elapsed)

    if processing_times:
        times = np.array(processing_times)
        print("\n========== 掩膜提取阶段时间统计 ==========")
        print(f"图像数量            : {len(times)}")
        print(f"平均耗时（秒）      : {times.mean():.3f}")
        print(f"标准差（秒）        : {times.std():.3f}")
        print(f"最小耗时（秒）      : {times.min():.3f}")
        print(f"最大耗时（秒）      : {times.max():.3f}")
        print("========================================")
