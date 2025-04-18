import os
import subprocess
import shutil
from pathlib import Path

# 定义记录已同步路径的文件
SYNCED_PATHS_FILE = ".github/synced_paths"
PACKAGES_FILE = "packages"

def clean_existing_files(target_path):
    """
    清理指定的目标路径中的文件或目录。
    :param target_path: 需要清理的目标路径
    """
    print(f"Cleaning existing files and directories at {target_path}...")
    if not target_path or os.path.abspath(target_path) == os.path.abspath("."):
        print(f"Skipping removal of current working directory: {target_path}")
        return

    if os.path.exists(target_path):
        print(f"Removing existing path: {target_path}")
        try:
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
        except Exception as e:
            print(f"Error cleaning up path {target_path}: {e}")

def get_latest_commit_hash(repo_url):
    """
    获取远程仓库的最新提交哈希值。
    :param repo_url: 仓库地址
    :return: 最新提交哈希值
    """
    print(f"Fetching latest commit hash for {repo_url}...")
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo_url, "refs/heads/main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Failed to fetch commit hash for {repo_url}: {result.stderr}")
            return None
        return result.stdout.split()[0]  # 提取哈希值
    except Exception as e:
        print(f"Error fetching commit hash for {repo_url}: {e}")
        return None

def parse_line(line):
    """
    解析一行输入，提取仓库地址、子目录路径、目标路径、克隆深度和当前哈希值。
    :param line: 输入行
    :return: (repo_url, sub_dir, target_path, depth, current_hash, raw_line)
    """
    raw_line = line.strip()
    line = line.strip().rstrip(";")  # 去掉末尾的分号
    if not line or line.startswith("#"):
        return None, None, None, None, None, raw_line

    parts = line.split(",")
    repo_url = parts[0].strip()  # 第一部分：仓库地址
    sub_dir = None
    target_path = None
    depth = None  # 默认克隆深度为 None（完整克隆）
    current_hash = None  # 当前记录的哈希值

    # 遍历剩余部分，处理子目录路径、目标路径、克隆深度和哈希值
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
            elif key.strip() == "hash":
                current_hash = value.strip()
        else:
            # 如果没有 path= 或 depth=，则认为这是子目录路径
            sub_dir = part

    # 确保目标路径不会重复拼接
    if target_path and sub_dir:
        # 如果目标路径已经包含子目录的最后一部分，则不再追加
        if not target_path.endswith(os.path.basename(sub_dir)):
            target_path = os.path.join(target_path, os.path.basename(sub_dir))
    elif sub_dir:
        # 如果没有指定目标路径，则默认为目标路径为子目录的最后一部分
        target_path = os.path.basename(sub_dir)
    elif not target_path:
        # 如果没有指定目标路径和子目录路径，默认为目标路径为仓库名
        target_path = os.path.basename(repo_url).replace(".git", "")

    return repo_url, sub_dir, target_path, depth, current_hash, raw_line

def update_packages_file(packages_lines, updated_entries):
    """
    更新 packages 文件，保存最新的哈希值，同时保留注释和空行。
    :param packages_lines: 原始的 packages 文件内容（列表形式）
    :param updated_entries: 更新后的条目字典
    """
    with open(PACKAGES_FILE, "w") as file:
        for line in packages_lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                # 保留注释和空行
                file.write(line)
                continue

            # 解析当前行
            repo_url, _, _, _, _, _ = parse_line(line)
            if repo_url and repo_url in updated_entries:
                # 如果是需要更新的条目，写入新的内容
                new_entry = updated_entries[repo_url]
                file.write(f"{new_entry['repo_url']},path={new_entry['target_path']},hash={new_entry['latest_hash']}\n")
            else:
                # 否则保留原始内容
                file.write(line)

def sync_repositories():
    """
    同步 packages 文件中定义的仓库内容到主仓库。
    """
    print("Syncing repositories...")
    if not os.path.exists(PACKAGES_FILE):
        print(f"Error: {PACKAGES_FILE} not found.")
        return

    # 记录本次同步的路径
    synced_paths = []

    # 读取 packages 文件内容
    packages_lines = []
    packages_entries = []
    updated_entries = {}
    with open(PACKAGES_FILE, "r") as file:
        for line in file:
            packages_lines.append(line)  # 保留原始内容
            repo_url, sub_dir, target_path, depth, current_hash, raw_line = parse_line(line)
            if not repo_url:
                continue

            # 获取最新的提交哈希值
            latest_hash = get_latest_commit_hash(repo_url)
            if not latest_hash:
                print(f"Skipping repository {repo_url} due to missing commit hash.")
                continue

            # 检查是否需要同步
            needs_sync = False
            if not current_hash or current_hash != latest_hash:
                needs_sync = True
                print(f"Repository {repo_url} has updates. Current hash: {current_hash}, Latest hash: {latest_hash}")
            else:
                print(f"Repository {repo_url} is up-to-date.")

            # 记录条目
            packages_entries.append({
                "repo_url": repo_url,
                "sub_dir": sub_dir,
                "target_path": target_path,
                "depth": depth,
                "current_hash": current_hash,
                "latest_hash": latest_hash,
                "needs_sync": needs_sync,
                "raw_line": raw_line
            })

            # 如果需要更新，记录到更新字典中
            if needs_sync:
                updated_entries[repo_url] = {
                    "repo_url": repo_url,
                    "target_path": target_path,
                    "latest_hash": latest_hash
                }

    # 执行同步操作
    for entry in packages_entries:
        if not entry["needs_sync"]:
            continue

        repo_url = entry["repo_url"]
        sub_dir = entry["sub_dir"]
        target_path = entry["target_path"]
        depth = entry["depth"]

        # 删除旧文件（仅在需要同步时执行清理）
        clean_existing_files(target_path)

        # 克隆仓库到临时目录
        repo_name = os.path.basename(repo_url).replace(".git", "")
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

    # 更新 packages 文件
    update_packages_file(packages_lines, updated_entries)

if __name__ == "__main__":
    sync_repositories()
