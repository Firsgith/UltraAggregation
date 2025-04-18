import os
import subprocess
import shutil
from pathlib import Path

# 定义记录已同步路径的文件
SYNCED_PATHS_FILE = ".github/synced_paths"

def clean_existing_files(synced_paths):
    """
    清理主仓库中已存在的、由 .synced_paths 文件定义的文件或目录。
    :param synced_paths: 已同步的路径列表
    """
    print("Cleaning existing files and directories...")
    for target_path in synced_paths:
        target_path = os.path.join(".", target_path)
        if not target_path or os.path.abspath(target_path) == os.path.abspath("."):
            print(f"Skipping removal of current working directory: {target_path}")
            continue

        if os.path.exists(target_path):
            print(f"Removing existing path: {target_path}")
            try:
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
            except Exception as e:
                print(f"Error cleaning up path {target_path}: {e}")

def is_submodule(temp_dir, sub_dir):
    """
    检查指定的子目录是否为子模块。
    :param temp_dir: 临时目录路径
    :param sub_dir: 子目录路径
    :return: True if the subdirectory is a submodule, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "-C", temp_dir, "submodule", "status", sub_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def handle_submodule(temp_dir, sub_dir):
    """
    如果子目录是子模块，手动克隆其内容。
    :param temp_dir: 临时目录路径
    :param sub_dir: 子目录路径
    :return: None
    """
    print(f"Detected '{sub_dir}' as a submodule. Cloning its contents...")
    submodule_url = subprocess.run(
        ["git", "-C", temp_dir, "config", "--get", f"submodule.{sub_dir}.url"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout.strip()

    if not submodule_url:
        print(f"Failed to retrieve URL for submodule '{sub_dir}'.")
        return

    # Clone the submodule's content into the same directory
    subprocess.run(["git", "clone", submodule_url, f"{temp_dir}/{sub_dir}"], check=True)

def parse_line(line):
    """
    解析一行输入，提取仓库地址、子目录路径、目标路径和克隆深度。
    :param line: 输入行
    :return: (repo_url, sub_dir, target_path, depth)
    """
    line = line.strip().rstrip(";")  # 去掉末尾的分号
    if not line or line.startswith("#"):
        return None, None, None, None

    parts = line.split(",")
    repo_url = parts[0].strip()  # 第一部分：仓库地址
    sub_dir = None
    target_path = None
    depth = None  # 默认克隆深度为 None（完整克隆）

    # 提取仓库名（去掉 .git 后缀）
    repo_name = os.path.basename(repo_url).replace(".git", "")

    # 遍历剩余部分，处理子目录路径、目标路径和克隆深度
    for part in parts[1:]:
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip() == "path":
                target_path = value.strip()
            elif key.strip() == "depth":
                try:
                    depth = int(value.strip())  # 将 depth 转换为整数
                except ValueError:
                    print(f"Invalid depth value: {value}. Using default full clone.")
                    depth = None
        else:
            # 如果没有 path= 或 depth=，则认为这是子目录路径
            sub_dir = part

    # 目标路径的生成逻辑
    if target_path:
        if sub_dir:
            # 如果有子目录路径，则目标路径为 path/sub_dir的最后一部分
            target_path = os.path.join(target_path, os.path.basename(sub_dir))
        else:
            # 如果没有子目录路径，则目标路径为 path/仓库名
            target_path = os.path.join(target_path, repo_name)
    elif sub_dir:
        # 如果没有指定目标路径，则使用子目录的最后一部分
        target_path = os.path.basename(sub_dir)
    else:
        # 如果既没有目标路径也没有子目录路径，则默认为目标路径为仓库名
        target_path = repo_name

    # 如果没有子目录路径，默认同步整个仓库
    if not sub_dir:
        sub_dir = None

    return repo_url, sub_dir, target_path, depth

def sync_repositories(packages_file):
    """
    同步 packages 文件中定义的仓库内容到主仓库。
    """
    print("Syncing repositories...")
    if not os.path.exists(packages_file):
        print(f"Error: {packages_file} not found.")
        return

    # 记录本次同步的路径
    synced_paths = []

    with open(packages_file, "r") as file:
        for i, line in enumerate(file):
            repo_url, sub_dir, target_path, depth = parse_line(line)
            if not repo_url:
                continue

            # 打印解析规则前的空行（跳过第一条规则前的空行）
            if i > 0:
                print()

            # 打印解析结果
            print(f"Parsing line: {line.strip()}")
            print(f"Repo URL: {repo_url}, Sub Dir: {sub_dir}, Target Path: {target_path}, Depth: {depth}")

            # 提取仓库名称作为临时目录名
            repo_name = os.path.basename(repo_url).replace(".git", "")

            # 克隆仓库到临时目录
            temp_dir = f"/tmp/{repo_name}"
            print(f"Cloning {repo_url} with depth={depth}...")
            try:
                if depth:
                    subprocess.run(["git", "clone", "--depth", str(depth), repo_url, temp_dir], check=True)
                else:
                    subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to clone {repo_url}: {e}")
                continue

            # 删除 .git 目录
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)

            # 确定需要复制的源路径
            source_path = os.path.join(temp_dir, sub_dir) if sub_dir else temp_dir

            # 确保目标路径的父目录存在
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)

            # 清理目标路径（仅删除当前路径，不删除父目录）
            if os.path.exists(target_path):
                print(f"Cleaning up existing target path: {target_path}")
                try:
                    if os.path.isdir(target_path):
                        shutil.rmtree(target_path)
                    else:
                        os.remove(target_path)
                except Exception as e:
                    print(f"Error cleaning up target path {target_path}: {e}")

            # 复制文件到目标路径
            print(f"Copying folder {source_path} to {target_path}...")
            try:
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            except Exception as e:
                print(f"Error copying folder {source_path} to {target_path}: {e}")
                continue

            # 记录本次同步的路径
            synced_paths.append(os.path.relpath(target_path, "."))

            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"Synced {repo_name} successfully.")

    # 更新 .synced_paths 文件
    with open(SYNCED_PATHS_FILE, "w") as file:
        for path in synced_paths:
            file.write(f"{path}\n")

if __name__ == "__main__":
    # 主仓库根目录下的 packages 文件路径
    packages_file = "packages"

    # 清理已存在的内容
    if os.path.exists(SYNCED_PATHS_FILE):
        with open(SYNCED_PATHS_FILE, "r") as file:
            synced_paths = [line.strip() for line in file if line.strip()]
        clean_existing_files(synced_paths)

    # 同步新的内容
    sync_repositories(packages_file)
