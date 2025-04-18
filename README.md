# **GitHub Actions：源码同步**

该存储库包含一个 GitHub Actions 工作流，用于自动从存储库中同步包。以下是设置和使用此工作流的说明。

## 目录
- [功能](#功能)
- [先决条件](#先决条件)
  - [个人访问令牌 (PAT)](#个人访问令牌-pat)
  - [存储库设置](#存储库设置)
- [工作原理](#工作原理)
- [故障排除](#故障排除)
  - [权限错误](#权限错误)
  - [无效的运行 ID](#无效的运行-id)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 功能

### 同步包
- 脚本会读取 `packages` 文件中的同步规则，并根据规则从远程仓库克隆指定的内容。
- 支持以下格式的同步规则：
  1. `https://github.com/user/repo.git;`
     - 默认将整个仓库同步到主仓库的根目录。
  2. `https://github.com/user/repo.git,src/folder;`
     - 同步仓库中的 `src/folder` 子目录。
  3. `https://github.com/user/repo.git,path=custom_path;`
     - 将整个仓库同步到主仓库的 `custom_path` 目录。
  4. `https://github.com/user/repo.git,themes/theme1,path=my_themes;`
     - 将仓库中的 `themes/theme1` 子目录同步到主仓库的 `my_themes` 目录。
- 配置文件：`packages`
  - 每行定义一条同步规则。
  - 以 `#` 开头的行会被视为注释并忽略。

### 清理旧的工作流运行记录
- GitHub 默认保留所有工作流运行记录，这可能会导致存储空间浪费和界面混乱。
- 该工作流会：
  1. 获取 `main` 分支上的所有工作流运行记录。
  2. 仅保留最新的 3 条记录。
  3. 删除较旧的运行记录。
- 手动验证清理效果：
  - 前往 **Actions** 页面，检查是否只有最新的 3 条记录。

---

## 先决条件

### 个人访问令牌 (PAT)
- 创建一个具有以下作用域的 PAT：
  - `repo`：对私有存储库的完全控制。
  - `admin:org`：对组织资源的完全控制。
- 将 PAT 存储在存储库的 Secrets 中，名称为 `SYNC_TOKEN`。

### 存储库设置
1. 进入存储库的 **Settings > Secrets and variables > Actions**。
2. 点击 **New repository secret**。
3. 设置名称为 `SYNC_TOKEN`，并粘贴您的 PAT 值。
4. 保存 Secret。

1. 进入存储库的 **Settings > Actions > General**。
2. 在 **Workflow permissions** 下，选择 **Read and write permissions**。
   - 这允许工作流推送更改并删除工作流运行记录。
3. 启用 **Allow GitHub Actions to create and approve pull requests**。
   - 这确保工作流有足够的权限执行提交更改和删除运行记录等操作。

---

## 工作原理
1. **触发工作流**：
   - 可通过 **workflow_dispatch** 事件手动触发，或在推送至 `main` 分支时自动触发。
2. **同步包**：
   - 工作流会检出存储库，设置 Python 3.10，并运行 `sync_packages.py` 脚本。
   - 脚本所做的任何更改都会通过 `SYNC_TOKEN` 提交并推回存储库。
3. **清理工作流运行记录**：
   - 工作流会获取 `main` 分支上的所有运行记录，并仅保留最新的 3 条。
   - 较旧的运行记录会被删除以减少混乱并节省存储空间。

---

## 故障排除

### 权限错误
- 如果遇到 `403 Forbidden` 错误，请按照以下步骤排查：
  1. 检查 `SYNC_TOKEN` 是否具有以下范围：
     - `repo`：对私有存储库的完全控制。
     - `admin:org`：对组织资源的完全控制。
  2. 确保存储库的 **Workflow permissions** 设置为 **Read and write permissions**。
  3. 确保启用了 **Allow GitHub Actions to create and approve pull requests**。
  4. 如果问题仍然存在，请尝试重新生成 `SYNC_TOKEN` 并更新存储库 Secrets。

### 无效的运行 ID
- 如果清理步骤跳过了某些运行 ID：
  - 检查 API 响应，确保提取了正确的 ID。
  - 添加调试日志以打印 API 响应：
    ```bash
    echo "API Response: $RESPONSE"
    ```

---

## 贡献
我们欢迎任何形式的贡献！如果您发现任何问题或有改进建议，请按照以下步骤操作：
1. **提交问题**：
   - 描述问题的具体现象。
   - 提供相关日志或截图。
2. **提交拉取请求**：
   - 确保代码通过所有测试。
   - 在 PR 描述中说明更改的内容和原因。
3. 加入我们的讨论组（如果有的话）以获取更多帮助。

---

## 许可证
本项目采用 MIT 许可证。有关详细信息，请参阅 [LICENSE](LICENSE) 文件。


---


# **GitHub Actions: Sync Packages and Clean Up Workflow Runs**

This repository contains a GitHub Actions workflow that automates the process of syncing packages from repositories and cleaning up old workflow runs. Below are the instructions for setting up and using this workflow.


## **Features**
1. **Sync Packages**:
   - Automatically run a Python script (`sync_packages.py`) to sync packages from repositories.
   - Commit and push changes back to the main branch.

2. **Clean Up Old Workflow Runs**:
   - Retain only the latest 3 workflow runs on the `main` branch.
   - Delete older workflow runs to reduce clutter and save storage space.


## **Prerequisites**

### **1. Required Permissions**
To ensure the workflow functions correctly, you need to configure the following permissions:

#### **Personal Access Token (PAT)**
- Create a PAT with the following scopes:
  - `repo`: Full control of private repositories.
  - `admin:org`: Full control of organization resources.
- Store the PAT in your repository's secrets as `SYNC_TOKEN`.

#### **Repository Settings**
1. Go to **Settings > Secrets and variables > Actions** in your repository.
2. Click **New repository secret**.
3. Set the name as `SYNC_TOKEN` and paste the value of your PAT.
4. Save the secret.

1. Go to **Settings > Actions > General** in your repository.
2. Under **Workflow permissions**, select **Read and write permissions**.
   - This allows the workflow to push changes and delete workflow runs.
3. Enable **Allow GitHub Actions to create and approve pull requests**.
   - This ensures the workflow has sufficient permissions to perform actions like committing changes and deleting runs.


## **How It Works**
1. **Triggering the Workflow**:
   - The workflow can be triggered manually via the **workflow_dispatch** event or automatically when pushing to the `main` branch.

2. **Syncing Packages**:
   - The workflow checks out the repository, sets up Python 3.10, and runs the `sync_packages.py` script.
   - Any changes made by the script are committed and pushed back to the repository using the `SYNC_TOKEN`.

3. **Cleaning Up Workflow Runs**:
   - The workflow fetches all runs on the `main` branch and retains only the latest 3 runs.
   - Older runs are deleted to reduce clutter and save storage space.


## **Troubleshooting**

### **1. Permission Errors**
- If you encounter `403 Forbidden` errors during the cleanup step:
  - Verify that the `SYNC_TOKEN` has the correct scopes (`repo` and `admin:org`).
  - Ensure **Read and write permissions** is selected under **Workflow permissions** in your repository settings.
  - Ensure **Allow GitHub Actions to create and approve pull requests** is enabled.

### **2. Invalid Run IDs**
- If the cleanup step skips Run IDs:
  - Check the API response to ensure the correct IDs are being extracted.
  - Add debug logs to print the API response:
    ```bash
    echo "API Response: $RESPONSE"
    ```


## **Contributing**
If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.


## **License**
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

