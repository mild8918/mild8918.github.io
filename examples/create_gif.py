#!/usr/bin/env python3
import os
import re
import subprocess
from PIL import Image
import glob


def create_gif_animation():
    # 获取当前目录下所有PNG文件
    png_files = glob.glob("*.png")

    # 提取ID并创建文件对
    id_pairs = {}

    for file in png_files:
        if file.endswith("_result.png"):
            # 结果文件
            id_str = file[:-11]  # 移除"_result.png"
            if id_str not in id_pairs:
                id_pairs[id_str] = {}
            id_pairs[id_str]["result"] = file
        else:
            # 原始文件
            id_str = file[:-4]  # 移除".png"
            if id_str not in id_pairs:
                id_pairs[id_str] = {}
            id_pairs[id_str]["original"] = file

    # 只保留同时有原始文件和结果文件的ID
    complete_pairs = {}
    for id_str, files in id_pairs.items():
        if "original" in files and "result" in files:
            complete_pairs[id_str] = files

    # 按ID排序（数字排序）
    def sort_key(id_str):
        # 如果是纯数字，转换为整数排序
        if id_str.isdigit():
            return int(id_str)
        # 如果包含数字，提取数字部分排序
        numbers = re.findall(r"\d+", id_str)
        if numbers:
            return int(numbers[0])
        return id_str

    sorted_ids = sorted(complete_pairs.keys(), key=sort_key)

    print(f"找到 {len(sorted_ids)} 组图片对:")
    for id_str in sorted_ids:
        print(
            f"  {id_str}: {complete_pairs[id_str]['original']} -> {complete_pairs[id_str]['result']}"
        )

    # 获取所有图片的最大尺寸
    max_width = 0
    max_height = 0

    all_images = []
    for id_str in sorted_ids:
        original_path = complete_pairs[id_str]["original"]
        result_path = complete_pairs[id_str]["result"]

        # 检查原始图片尺寸
        with Image.open(original_path) as img:
            max_width = max(max_width, img.width)
            max_height = max(max_height, img.height)

        # 检查结果图片尺寸
        with Image.open(result_path) as img:
            max_width = max(max_width, img.width)
            max_height = max(max_height, img.height)

    print(f"画布尺寸: {max_width} x {max_height}")

    # 创建GIF帧
    frames = []

    for id_str in sorted_ids:
        original_path = complete_pairs[id_str]["original"]
        result_path = complete_pairs[id_str]["result"]

        # 处理原始图片
        with Image.open(original_path) as img:
            # 创建白色背景
            frame = Image.new("RGB", (max_width, max_height), "white")

            # 计算缩放比例，按照长边适配画布
            scale_x = max_width / img.width
            scale_y = max_height / img.height
            scale = min(scale_x, scale_y)  # 选择较小的缩放比例，确保图片完全适配画布

            # 计算缩放后的尺寸
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)

            # 缩放图片到画布大小
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 计算居中位置
            x = (max_width - new_width) // 2
            y = (max_height - new_height) // 2

            # 如果是RGBA图片，需要处理透明度
            if img_resized.mode == "RGBA":
                # 创建白色背景并粘贴图片
                temp = Image.new("RGB", img_resized.size, "white")
                temp.paste(
                    img_resized,
                    mask=(
                        img_resized.split()[-1] if img_resized.mode == "RGBA" else None
                    ),
                )
                frame.paste(temp, (x, y))
            else:
                frame.paste(img_resized, (x, y))
            frames.append(frame.copy())

        # 处理结果图片
        with Image.open(result_path) as img:
            # 创建白色背景
            frame = Image.new("RGB", (max_width, max_height), "white")

            # 计算缩放比例，按照长边适配画布
            scale_x = max_width / img.width
            scale_y = max_height / img.height
            scale = min(scale_x, scale_y)  # 选择较小的缩放比例，确保图片完全适配画布

            # 计算缩放后的尺寸
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)

            # 缩放图片到画布大小
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 计算居中位置
            x = (max_width - new_width) // 2
            y = (max_height - new_height) // 2

            # 如果是RGBA图片，需要处理透明度
            if img_resized.mode == "RGBA":
                # 创建白色背景并粘贴图片
                temp = Image.new("RGB", img_resized.size, "white")
                temp.paste(
                    img_resized,
                    mask=(
                        img_resized.split()[-1] if img_resized.mode == "RGBA" else None
                    ),
                )
                frame.paste(temp, (x, y))
            else:
                frame.paste(img_resized, (x, y))
            frames.append(frame.copy())

    # 生成GIF
    if frames:
        output_path = "animation.gif"
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=750,  # 每帧750ms
            loop=0,  # 无限循环
        )
        print(f"原始GIF动画已生成: {output_path}")
        print(f"总共 {len(frames)} 帧，每帧 750ms")

        # 获取原始文件大小
        original_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"原始文件大小: {original_size:.1f}MB")

        # 使用ffmpeg压缩GIF
        print("开始使用ffmpeg压缩...")
        compress_gif_with_ffmpeg(output_path, max_width, max_height)

    else:
        print("未找到匹配的图片对，无法生成GIF")


def compress_gif_with_ffmpeg(input_path, original_width, original_height):
    """使用ffmpeg压缩GIF文件"""
    try:
        palette_path = "palette_temp.png"
        compressed_path = "animation_compressed.gif"

        # 第一步：生成优化的调色板
        print("  生成优化调色板...")
        palette_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            "fps=1.33,scale=1800:-1:flags=lanczos,palettegen",
            palette_path,
        ]

        result = subprocess.run(palette_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  调色板生成失败: {result.stderr}")
            return False

        # 第二步：使用调色板压缩GIF
        print("  压缩GIF文件...")
        compress_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-i",
            palette_path,
            "-lavfi",
            "fps=1.33,scale=1800:-1:flags=lanczos[x];[x][1:v]paletteuse",
            compressed_path,
        ]

        result = subprocess.run(compress_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  GIF压缩失败: {result.stderr}")
            return False

        # 检查压缩后的文件大小
        if os.path.exists(compressed_path):
            compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)  # MB
            original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
            compression_ratio = (compressed_size / original_size) * 100

            print(f"  压缩完成！")
            print(f"  压缩后文件: {compressed_path}")
            print(f"  压缩后大小: {compressed_size:.1f}MB")
            print(f"  压缩比例: {compression_ratio:.1f}%")
            print(
                f"  分辨率调整: 从 {original_width}x{original_height} 到 1800x相应高度"
            )

            # 清理临时文件
        if os.path.exists(palette_path):
            os.remove(palette_path)

        # 将压缩后的GIF复制到dist目录
        dist_dir = "../dist"
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)
            print(f"  创建dist目录: {dist_dir}")

        import shutil

        dist_gif_path = os.path.join(dist_dir, "animation_compressed.gif")
        shutil.copy2(compressed_path, dist_gif_path)
        print(f"  已复制到网页目录: {dist_gif_path}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"  ffmpeg命令执行失败: {e}")
        return False
    except Exception as e:
        print(f"  压缩过程出错: {e}")
        return False


if __name__ == "__main__":
    create_gif_animation()
