---
name: "apkmcp-auto"
description: "Android APK 逆向工程自动化工具套件 Skill。统一单服务器（server.py）聚合 APKTool、ADB、签名工具、静态分析器、文件对比、Frida 六组工具，一个 MCP 连接即可调用。当用户需要进行 APK 反编译、代码分析、设备调试、APK 签名或文件对比时调用此 Skill。"
---

# ApkMCP-Auto Android 逆向工程工具套件

## 项目概述

ApkMCP-Auto 是一个基于 **MCP (Model Context Protocol)** 的 Android APK 自动化逆向工程工具套件，通过 AI 助手与专业反编译工具的无缝集成，实现智能化的 APK 分析与修改。

> **架构（单服务器版）**：所有 Python 工具分组聚合在 **一个 MCP 服务器 `server.py`** 中，
> 客户端只需配置一条 `apkmcp` 记录。工具名统一带分组前缀
> （`apktool_*` / `adb_*` / `sign_*` / `static_*` / `diff_*` / `frida_*`），
> 另有 `apkmcp_help`（查清单）、`apkmcp_status`（查健康状态）两个元工具。
> JADX 实时分析由 Java 版 `tools/jadx/server.jar` 独立提供（可选，需配合 JADX-GUI）。

## 新目录结构

项目已重新整理为统一的 `tools/` 目录结构，便于 AI 统一调度：

```
ApkMCP-Auto/
├── server.py                     # ★ 统一单服务器（唯一 MCP 入口）
├── apkmcp.py                     # 统一命令行工具
├── requirements.txt              # 核心依赖（含 fastmcp）
├── mcp.json                      # 通用客户端配置（自动生成）
├── mcp-configs/                  # 各客户端配置（自动生成）
├── .trae/mcp.json                # Trae 配置（自动生成）
├── .cursor/mcp.json              # Cursor 配置（自动生成）
├── .vscode/mcp.json              # VS Code 配置（自动生成）
├── tools/                        # 工具分组实现（由统一服务器加载）
│   ├── __init__.py               # 统一调度模块（旧版兼容）
│   ├── jadx/server.jar           # JADX 服务器（Java，可选独立运行）
│   ├── apktool/server.py         # → 聚合为 apktool_* 工具
│   ├── adb/server.py             # → 聚合为 adb_* 工具
│   ├── sign-tools/server.py      # → 聚合为 sign_* 工具
│   ├── static-analyzer/server.py # → 聚合为 static_* 工具
│   ├── diff/server.py            # → 聚合为 diff_* 工具
│   ├── frida/server.py           # → 聚合为 frida_* 工具（可选依赖）
│   ├── bin/                      # 二进制工具（adb/apktool/jadx-gui/jre）
│   └── workspace/                # 工作空间（解码产物、密钥库）
└── README.md
```

## 统一调度方式

### 1. 命令行工具

使用 `apkmcp.py` 统一命令行工具管理所有工具：

```bash
# 查看统一服务器状态
python apkmcp.py status

# 列出全部分组与工具（前缀命名）
python apkmcp.py list

# 生成 MCP 配置（默认 Trae；--client all 生成 9 种主流客户端配置）
python apkmcp.py config
python apkmcp.py config --client all

# 安装核心依赖（frida 可选）
python apkmcp.py install
python apkmcp.py install --frida

# 启动统一服务器（stdio/HTTP，Ctrl+C 停止并释放资源）
python apkmcp.py start
python apkmcp.py start --http

# 停止残留进程并释放资源
python apkmcp.py stop
```

### 2. Python API 调用

在 Python 代码中使用统一调度模块：

```python
from tools import ApkMCPManager, ToolType

# 创建管理器
manager = ApkMCPManager()

# 列出所有工具
tools = manager.list_tools()
for tool in tools:
    print(f"{tool.tool_type.value}: {tool.description}")

# 获取指定工具配置
jadx_config = manager.get_tool(ToolType.JADX)
print(f"JADX 路径: {jadx_config.server_path}")

# 安装依赖
manager.install_dependencies(ToolType.APKTOOL)

# 生成 MCP 配置
config = manager.get_mcp_config()
manager.save_mcp_config(".trae/config.json")
```

### 3. 便捷函数

```python
from tools import get_manager, get_tool_config, list_all_tools

# 获取默认管理器
manager = get_manager()

# 通过名称获取工具配置
tool = get_tool_config("apktool")

# 列出所有工具
tools = list_all_tools()
```

## 核心组件

### 1. JADX 可选服务器（`apkmcp-jadx`，需 `--with-jadx` 启用）
- **路径**: `tools/jadx/server.jar`（Java，需配合 JADX-GUI）
- **功能**: 与 JADX-GUI 集成，提供实时反编译分析
- **主要工具**（不带前缀）:
  - `fetch_current_class` - 获取当前选中的类
  - `get_class_source` - 获取指定类源代码
  - `search_classes_by_keyword` - 按关键词搜索类
  - `get_android_manifest` - 获取 AndroidManifest.xml
  - `rename_class/method/field/variable` - 代码重构
  - `get_xrefs_to_class/method` - 交叉引用分析
  - `debug_get_stack_frames/variables` - 调试器集成

### 2. APKTool 分组（`apktool_*`，统一服务器内置）
- **实现**: `tools/apktool/server.py`（由统一服务器加载，无需单独启动）
- **功能**: APK 解码/编码与 Smali 修改
- **主要工具**:
  - `apktool_decode_apk` - 解码 APK 文件
  - `apktool_build_apk` - 从项目构建 APK
  - `apktool_get_smali_file` / `apktool_modify_smali_file` - Smali 代码操作
  - `apktool_list_resources` / `apktool_modify_resource_file` - 资源管理
  - `apktool_search_in_files` - 文件内容搜索
  - `apktool_analyze_project_structure` - 项目结构分析

### 3. ADB 分组（`adb_*`，统一服务器内置）
- **实现**: `tools/adb/server.py`
- **功能**: Android 设备管理和调试
- **主要工具**:
  - `adb_list_devices` / `adb_get_device_info` - 设备管理
  - `adb_install_apk` / `adb_uninstall_package` - 应用安装/卸载
  - `adb_get_logcat` / `adb_clear_logcat` - 日志捕获
  - `adb_execute_shell` - Shell 命令执行
  - `adb_push_file` / `adb_pull_file` - 文件传输
  - `adb_screenshot` - 屏幕截图
  - `adb_start_activity` / `adb_force_stop_package` - 应用控制

### 4. 签名分组（`sign_*`，统一服务器内置）
- **实现**: `tools/sign-tools/server.py`
- **功能**: APK 签名和密钥管理
- **主要工具**:
  - `sign_generate_keystore` - 生成密钥库
  - `sign_list_keystores` / `sign_get_keystore_info` - 密钥管理
  - `sign_sign_apk` - APK 签名（V1/V2/V3）
  - `sign_verify_signature` - 签名验证
  - `sign_zipalign_apk` - 对齐优化

### 5. 静态分析分组（`static_*`，统一服务器内置）
- **实现**: `tools/static-analyzer/server.py`
- **功能**: 静态分析增强
- **主要工具**:
  - `static_analyze_permissions` - 权限分析（含危险权限识别）
  - `static_extract_strings` - 字符串资源提取
  - `static_extract_endpoints` - URL/IP/API 端点提取
  - `static_identify_sdks` - 第三方 SDK 识别（广告、统计、社交、支付等）
  - `static_full_analysis` - 完整静态分析

### 6. 对比分组（`diff_*`，统一服务器内置）
- **实现**: `tools/diff/server.py`
- **功能**: 文件对比
- **主要工具**:
  - `diff_compare_apks` - APK 文件对比
  - `diff_compare_smali` - Smali 文件行级对比
  - `diff_compare_resources` - 资源目录对比
  - `diff_compare_text_files` - 通用文本文件对比

### 7. Frida 分组（`frida_*`，统一服务器内置，需 `install --frida`）
- **实现**: `tools/frida/server.py`
- **功能**: 动态插桩分析
- **主要工具**:
  - `frida_list_processes` / `frida_attach_process` / `frida_spawn_process` - 进程管理
  - `frida_inject_script` - JavaScript 脚本注入
  - `frida_hook_function` - 函数 Hook
  - `frida_intercept_network` - 网络请求拦截
  - `frida_scan_memory` / `frida_read_memory` / `frida_write_memory` - 内存操作
  - `frida_enumerate_modules` / `frida_enumerate_exports` - 模块枚举

## 典型工作流程

### APK 分析流程
```python
from tools import ApkMCPManager, ToolType

manager = ApkMCPManager()

# 1. 使用 APKTool 解码 APK
apktool = manager.get_tool(ToolType.APKTOOL)
# → 调用 apktool_decode_apk(apk_path)

# 2. 使用 Static Analyzer 进行静态分析
analyzer = manager.get_tool(ToolType.STATIC_ANALYZER)
# → 调用 static_full_analysis(project_dir)
# → 调用 static_analyze_permissions(project_dir)
# → 调用 static_identify_sdks(project_dir)

# 3. 使用 JADX 分析代码
jadx = manager.get_tool(ToolType.JADX)
# → 调用 get_android_manifest()
# → 调用 search_classes_by_keyword("关键词")
# → 调用 get_class_source(class_name)

# 4. 使用 Diff Tool 对比修改（如有需要）
diff = manager.get_tool(ToolType.DIFF)
# → 调用 diff_compare_apks(original_apk, modified_apk)
```

### APK 修改与重打包流程
```python
from tools import ApkMCPManager, ToolType

manager = ApkMCPManager()

# 1. 解码 APK
apktool = manager.get_tool(ToolType.APKTOOL)
# → decode_apk(apk_path)

# 2. 修改 Smali 代码
# → get_smali_file(class_name)
# → modify_smali_file(class_name, new_content)

# 3. 修改资源文件
# → get_resource_file(resource_type, resource_name)
# → modify_resource_file(resource_type, resource_name, new_content)

# 4. 构建 APK
# → build_apk(project_dir)

# 5. 签名 APK
sign = manager.get_tool(ToolType.SIGN_TOOLS)
# → sign_apk(apk_path, keystore_name, keystore_password, key_alias)

# 6. 验证签名
# → verify_signature(signed_apk_path)
```

### 设备调试流程
```python
from tools import ApkMCPManager, ToolType

manager = ApkMCPManager()
adb = manager.get_tool(ToolType.ADB)

# 1. 连接设备
# → list_devices()

# 2. 安装 APK
# → install_apk(apk_path, device_id)

# 3. 获取日志
# → get_logcat(device_id, package_name, max_lines)

# 4. 执行调试命令
# → execute_shell(command, device_id)
```

### 动态分析流程（Frida）
```python
from tools import ApkMCPManager, ToolType

manager = ApkMCPManager()
frida = manager.get_tool(ToolType.FRIDA)

# 1. 列出进程
# → list_processes()

# 2. 附加到目标进程
# → attach_process(target)

# 3. Hook 函数
# → hook_function(session_id, class_name, method_name)

# 4. 拦截网络请求
# → intercept_network(session_id, filter_url)

# 5. 获取消息
# → get_messages(session_id)
```

## 配置说明

### 自动生成 MCP 配置

使用命令行工具自动生成配置：

```bash
python apkmcp.py config
```

这将生成 `.trae/config.json`：

```json
{
  "mcpServers": {
    "apkmcp": {
      "command": "C:/Users/you/miniconda3/python.exe",
      "args": ["D:/ApkMCP-Auto/server.py"],
      "type": "stdio",
      "enabled": true,
      "description": "ApkMCP 统一单服务器：一个连接调用全部逆向工具"
    }
  }
}
```

用 `python apkmcp.py config --client all` 可生成 Trae / Cursor / VS Code / Cline /
Claude Desktop / Windsurf / Cherry Studio / Continue / 通用共 9 种客户端配置。
旧版 7 服务器分散配置可用 `config --legacy` 生成（已弃用）。

## 使用示例

### 示例 1: 完整 APK 分析
```
用户: 分析 APK 文件 E:/test.apk

AI: 我将帮您全面分析这个 APK 文件。让我按步骤进行：

1. 首先使用 APKTool 解码 APK
2. 进行静态分析（权限、SDK、字符串）
3. 使用 JADX 分析代码结构

[调用 MCP 工具执行分析...]
```

### 示例 2: 去除广告
```
用户: 帮我去除这个 APK 中的广告

AI: 我将帮您分析并去除广告。步骤如下：

1. 解码 APK
2. 识别广告 SDK
3. 定位广告相关代码
4. 修改 Smali 代码禁用广告
5. 重新打包并签名

[调用相关 MCP 工具...]
```

### 示例 3: 调试应用
```
用户: 连接设备并安装 APK

AI: 我来帮您连接设备和安装 APK：

1. 列出已连接设备
2. 安装 APK 到设备
3. 启动应用并获取日志

[调用 ADB MCP Server 工具...]
```

## 注意事项

1. **合法性**: 仅用于合法的安全研究和学习目的
2. **权限**: 仅分析您拥有合法权限的应用程序
3. **安全**: 不要将 MCP Server 绑定到公网地址
4. **签名**: APK 修改后需要重新签名才能安装
5. **资源释放**: 分析完成后关闭 MCP 工具连接

## 技术栈

- **Python 3.10+** - MCP Server 开发
- **FastMCP** - MCP 协议实现
- **APKTool 3.0+** - APK 反编译/重打包
- **JADX 1.5+** - Android Dex 反编译
- **Java 17** - JADX 运行环境
- **ADB** - Android 调试桥
- **Frida** - 动态插桩框架

## 报告生成

使用提示词模板进行分析后，会自动生成结构化报告：
- `分析报告.md` - 通用 APK 分析报告
- `广告分析报告.md` - 广告 SDK 识别和去除方案
- `会员分析报告.md` - 会员验证机制分析
- `加固分析报告.md` - 加固识别和脱壳方案
- `网络分析报告.md` - 网络通信分析
- `逆向分析报告.md` - 综合逆向工程报告
