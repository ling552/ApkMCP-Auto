# Android 逆向工程 MCP 工具套件

<div align="center">

⚡ 基于 Model Context Protocol (MCP) 的 Android APK 自动化逆向工程工具套件

**一个服务器，一个连接，调用全部工具。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-17-blue)](https://openjdk.org/)
[![MCP](https://img.shields.io/badge/MCP-Single%20Server-purple)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)

</div>

---

## 项目简介

本项目是一个 Android 逆向工程工具集合，通过 **MCP (Model Context Protocol)** 协议将 AI 助手与专业的 Android 反编译工具连接起来，实现智能化的 APK 分析与修改。

### 核心设计：统一单服务器

所有 Python 工具分组聚合在 **一个 MCP 服务器进程**（`server.py`）中对外提供服务，客户端只需配置**一条**服务器记录即可调用全部 60+ 工具：

| 分组前缀 | 功能 | 工具数 |
|----------|------|--------|
| `apktool_*` | APK 解码/编码、Smali 浏览与修改、资源管理 | 16 |
| `adb_*` | 设备管理、APK 安装/卸载、日志、Shell、截图 | 15 |
| `sign_*` | 密钥库管理、APK 签名（V1/V2/V3）、签名验证、zipalign | 9 |
| `static_*` | 权限分析、字符串提取、端点提取、SDK 识别、完整分析 | 5 |
| `diff_*` | APK / Smali / 资源 / 文本对比 | 4 |
| `frida_*` | 进程管理、脚本注入、Hook、网络拦截、内存操作（可选依赖） | 15 |
| `apkmcp_*` | 元工具：`apkmcp_help`（帮助）、`apkmcp_status`（健康检查） | 2 |

> **JADX 说明**：JADX 实时反编译由 Java 版 `tools/jadx/server.jar` 独立提供（需配合 JADX-GUI 插件），属于**可选的第二服务器**，默认单服务器配置不包含它。需要时加 `--with-jadx` 生成配置即可。

工具命名统一加分组前缀，避免旧版多服务器之间的重名冲突（如 `health_check`、`get_resource_file`、`get_workspace_info`）。

---

## 支持的 MCP 客户端

一条命令生成全部主流客户端配置：

```bash
python apkmcp.py config --client all
```

| 客户端 | 配置文件 | 说明 |
|--------|----------|------|
| **Trae** | `.trae/mcp.json`（兼容旧版 `.trae/config.json`） | 自动读取，开箱即用 |
| **Cursor** | `.cursor/mcp.json` | 在 Settings > MCP 中启用 `apkmcp` |
| **VS Code** | `.vscode/mcp.json` | 需支持 MCP 的 Copilot 扩展 |
| **Cline** | `mcp-configs/cline_mcp_settings.json` | 合并到 Cline 的 MCP 设置 |
| **Claude Desktop** | `mcp-configs/claude_desktop_config.json` | 复制到全局配置后重启生效 |
| **Windsurf** | `mcp-configs/windsurf_mcp_config.json` | 合并到 `~/.codeium/windsurf/mcp_config.json` |
| **Cherry Studio** | `mcp-configs/cherry_studio_mcp.json` | 在设置 > MCP 服务器中导入 |
| **Continue** | `mcp-configs/apkmcp-continue.yaml` | 合并到 `~/.continue/config.yaml` |
| **通用** | `mcp.json` | 其他兼容 MCP 的客户端直接导入 |

生成单个客户端配置：

```bash
python apkmcp.py config --client cursor     # 仅 Cursor
python apkmcp.py config --client trae --relative  # 相对路径（便于移动项目目录）
python apkmcp.py config --client all --with-jadx  # 附带可选的 JADX 服务器
python apkmcp.py config -p                  # 仅预览不写入
```

配置示例（单服务器，默认使用绝对路径，各客户端启动目录不同也能找到）：

```json
{
  "mcpServers": {
    "apkmcp": {
      "command": "C:/Users/you/miniconda3/python.exe",
      "args": ["D:/ApkMCP-Auto/server.py"],
      "description": "ApkMCP 统一单服务器：一个连接调用全部逆向工具"
    }
  }
}
```

---

## 系统要求

| 环境 | 版本要求 |
|------|----------|
| Windows / macOS / Linux | 均可（Python 工具跨平台；`tools/bin` 内置 Windows 版 adb/apktool/JRE） |
| Python | 3.10 或更高版本 |
| Java | OpenJDK 17（已包含在 `tools/bin/jre` 中，供 apktool/签名/JADX 使用） |
| 内存 | 建议 8GB 或更高 |

---

## 快速开始

### 1. 安装依赖

```bash
# 安装统一服务器核心依赖
python apkmcp.py install

# 如需动态分析（frida_* 工具），额外安装可选依赖
python apkmcp.py install --frida
```

### 2. 生成 MCP 配置

```bash
# 生成全部主流客户端配置（推荐）
python apkmcp.py config --client all

# 或只生成正在用的客户端
python apkmcp.py config --client trae
python apkmcp.py config --client claude-desktop
```

### 3. 在 AI 客户端中使用

MCP 客户端会按配置**自动拉起**统一服务器（stdio 模式），日常使用**无需手动启动**。直接向 AI 提问即可：

```
请帮我解码 APK 文件 test.apk 并分析它的权限和第三方 SDK
```

### 4. 手动启动（仅调试需要）

```bash
# 前台启动统一服务器（HTTP 调试模式）
python apkmcp.py start --http
# 或
python server.py --http --port 8660

# Windows 快捷脚本 / macOS-Linux 脚本
start-server.bat http
./start-server.sh http

# 查看状态 / 列出工具
python apkmcp.py status
python apkmcp.py list
python server.py --list-tools

# 按需裁剪分组（例如不需要 frida/adb）
python server.py --disable frida,adb --list-tools
```

### 5. 释放资源

- **stdio 模式**：断开 MCP 连接即自动释放，无需任何操作。
- **HTTP 模式**：按 `Ctrl+C` 停止，服务器会自动清理 Frida 会话等资源。
- **残留进程**：`python apkmcp.py stop`（或 `start-server.bat stop`）可清理后台残留进程。

---

## 使用示例

### 分析 APK 文件

```
请帮我解码 APK 文件 test.apk

# AI 将调用：apktool_decode_apk → static_full_analysis → apktool_get_manifest
# 分析完成后可以查看 AndroidManifest.xml、Smali 代码、资源文件、项目结构
```

### 代码审查与安全分析

```
分析这个 APK 的权限和潜在风险，识别第三方 SDK

# AI 将调用：static_analyze_permissions → static_identify_sdks → static_extract_endpoints
```

### 设备调试

```
列出已连接的 Android 设备，并安装 test.apk

# AI 将调用：adb_list_devices → adb_install_apk → adb_get_logcat
```

### APK 修改与重打包

```
去掉这个 APK 的开屏广告，然后重新打包签名

# AI 将调用：apktool_decode_apk → apktool_search_in_files → apktool_modify_smali_file
#          → apktool_build_apk → sign_sign_apk → sign_verify_signature
#          → diff_compare_apks（对比修改前后差异）
```

### 动态分析（需 frida 依赖 + 设备端 frida-server）

```
Hook 目标应用的登录函数

# AI 将调用：frida_list_processes → frida_attach_process → frida_hook_function
```

---

## 提示词模板

本项目提供专门的 APK 逆向工程分析提示词模板（`prompt_template.md`），工具名已按统一单服务器前缀命名：

| 提示词 | 用途 | 输出报告 |
|--------|------|----------|
| 通用 APK 分析 | 全面的 APK 信息提取和分析 | `分析报告.md` |
| 广告去除专项 | 定位广告 SDK 和去除方案 | `广告分析报告.md` |
| 会员破解专项 | 分析会员验证机制 | `会员分析报告.md` |
| 加固分析专项 | 识别加固方案和脱壳建议 | `加固分析报告.md` |
| 网络分析专项 | 分析网络通信和拦截点 | `网络分析报告.md` |
| 综合逆向分析 | 完整的逆向工程流程 | `逆向分析报告.md` |

使用方法：打开 `prompt_template.md` → 选择模板 → 复制到 AI 助手 → 替换 `[APK文件路径]` 和 `[工作目录]`。

---

## 项目结构

```
ApkMCP-Auto/
├── server.py                       # ★ 统一单服务器（唯一 MCP 入口）
├── apkmcp.py                       # 统一命令行工具（状态/配置/安装/启动/停止）
├── requirements.txt                # 统一服务器核心依赖
├── requirements-frida.txt          # frida 可选依赖
├── mcp.json                        # 通用客户端配置（自动生成）
├── mcp-configs/                    # 各客户端配置（自动生成）
│   ├── claude_desktop_config.json
│   ├── cline_mcp_settings.json
│   ├── windsurf_mcp_config.json
│   ├── cherry_studio_mcp.json
│   └── apkmcp-continue.yaml
├── .trae/mcp.json                  # Trae 配置（自动生成，兼容旧版 config.json）
├── .cursor/mcp.json                # Cursor 配置（自动生成）
├── .vscode/mcp.json                # VS Code 配置（自动生成）
├── tools/                          # 工具分组（被统一服务器加载，无需单独启动）
│   ├── apktool/server.py           # APKTool 分组实现
│   ├── adb/server.py               # ADB 分组实现
│   ├── sign-tools/server.py        # 签名分组实现
│   ├── static-analyzer/server.py   # 静态分析分组实现
│   ├── diff/server.py              # 对比分组实现
│   ├── frida/server.py             # Frida 分组实现
│   ├── jadx/server.jar             # JADX 服务器（Java，可选独立运行）
│   ├── bin/                        # 内置二进制（adb/apktool/jadx-gui/jre）
│   └── workspace/                  # 工作空间（解码产物、密钥库）
├── start-server.bat / .sh          # 统一服务器快捷脚本
├── start_all_servers.py            # 旧版分散启动（已弃用，仅兼容保留）
├── prompt_template.md              # APK 逆向分析提示词模板（单服务器版）
├── AI_GUIDE.md                     # AI 助手调用指引（单服务器版）
└── README.md                       # 本文件
```

---

## 可用 MCP 工具（前缀命名）

### APKTool 分组（`apktool_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `apktool_decode_apk` | 解码 APK 文件 |
| `apktool_build_apk` | 从项目构建 APK |
| `apktool_get_manifest` | 获取 AndroidManifest.xml |
| `apktool_get_apktool_yml` | 获取 apktool.yml |
| `apktool_list_smali_directories` | 列出 Smali 目录 |
| `apktool_list_smali_files` | 列出 Smali 文件（支持分页） |
| `apktool_get_smali_file` | 获取 Smali 文件内容 |
| `apktool_modify_smali_file` | 修改 Smali 文件 |
| `apktool_list_resources` | 列出资源文件 |
| `apktool_get_resource_file` | 获取资源文件内容 |
| `apktool_modify_resource_file` | 修改资源文件 |
| `apktool_search_in_files` | 在文件中搜索 |
| `apktool_analyze_project_structure` | 分析项目结构 |
| `apktool_clean_project` | 清理项目 |
| `apktool_get_workspace_info` | 获取工作空间信息 |
| `apktool_health_check` | 健康检查 |

### ADB 分组（`adb_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `adb_list_devices` | 列出已连接设备 |
| `adb_get_device_info` | 获取设备详细信息 |
| `adb_install_apk` | 安装 APK 文件 |
| `adb_uninstall_package` | 卸载应用包 |
| `adb_get_package_info` | 获取应用包信息 |
| `adb_get_logcat` / `adb_clear_logcat` | 获取 / 清除设备日志 |
| `adb_execute_shell` | 执行 Shell 命令 |
| `adb_push_file` / `adb_pull_file` | 文件传输 |
| `adb_screenshot` | 截取屏幕 |
| `adb_list_packages` | 列出已安装应用 |
| `adb_start_activity` | 启动 Activity |
| `adb_force_stop_package` | 强制停止应用 |
| `adb_health_check` | 健康检查 |

### 签名分组（`sign_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `sign_generate_keystore` | 生成密钥库 |
| `sign_list_keystores` | 列出所有密钥库 |
| `sign_get_keystore_info` | 获取密钥库信息 |
| `sign_delete_keystore` | 删除密钥库 |
| `sign_sign_apk` | 签名 APK 文件 |
| `sign_verify_signature` | 验证 APK 签名 |
| `sign_zipalign_apk` | 对齐优化 APK |
| `sign_get_workspace_info` | 获取工作空间信息 |
| `sign_health_check` | 健康检查 |

### 静态分析分组（`static_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `static_analyze_permissions` | 分析权限（含危险权限识别） |
| `static_extract_strings` | 提取字符串资源 |
| `static_extract_endpoints` | 提取 URL/IP/API 端点 |
| `static_identify_sdks` | 识别第三方 SDK |
| `static_full_analysis` | 执行完整分析 |

### 对比分组（`diff_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `diff_compare_apks` | 对比两个 APK 文件 |
| `diff_compare_smali` | 对比两个 Smali 文件 |
| `diff_compare_resources` | 对比两个资源目录 |
| `diff_compare_text_files` | 对比两个文本文件 |

### Frida 分组（`frida_*`，需可选依赖）

| 工具名 | 功能描述 |
|--------|----------|
| `frida_list_processes` | 列出运行中的进程 |
| `frida_attach_process` / `frida_detach_session` | 附加 / 分离进程 |
| `frida_spawn_process` / `frida_resume_process` | 启动 / 恢复进程 |
| `frida_inject_script` | 注入 JavaScript 脚本 |
| `frida_hook_function` | Hook 指定函数 |
| `frida_intercept_network` | 拦截网络请求 |
| `frida_scan_memory` / `frida_read_memory` / `frida_write_memory` | 内存操作 |
| `frida_get_messages` / `frida_list_sessions` | 消息 / 会话管理 |
| `frida_enumerate_modules` / `frida_enumerate_exports` | 模块 / 导出函数枚举 |

### 元工具（`apkmcp_*`）

| 工具名 | 功能描述 |
|--------|----------|
| `apkmcp_help` | 获取全部分组工具清单与使用帮助 |
| `apkmcp_status` | 查看各分组健康状态 |

---

## 技术栈

- **Python 3.10+** - 统一服务器与各分组实现
- **FastMCP** - MCP 协议实现（单服务器聚合多分组）
- **APKTool 3.0+** - APK 反编译/重打包
- **JADX 1.5+** - Android Dex 反编译（Java 独立服务，可选）
- **Java 17** - APKTool / 签名 / JADX 运行环境（内置）
- **ADB** - Android 调试桥（内置 Windows 版）
- **Frida** - 动态插桩框架（可选依赖）

---

## 命令行参考

### apkmcp.py 统一命令行工具

| 命令 | 说明 | 示例 |
|------|------|------|
| `status` | 查看统一服务器状态 | `python apkmcp.py status` |
| `list` | 列出全部分组与工具 | `python apkmcp.py list` |
| `config --client X` | 生成客户端配置 | `python apkmcp.py config --client all` |
| `install [--frida]` | 安装依赖 | `python apkmcp.py install --frida` |
| `start [--http]` | 启动统一服务器 | `python apkmcp.py start --http` |
| `stop` | 停止残留进程并释放资源 | `python apkmcp.py stop` |

### 统一服务器参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--http` | 关闭（stdio） | 启用 HTTP 调试模式 |
| `--host` | 127.0.0.1 | HTTP 监听地址 |
| `--port` | 8660 | HTTP 监听端口 |
| `--disable` | 空 | 禁用的分组，逗号分隔（如 `frida,adb`） |
| `--workspace` | tools/workspace/apktool | APKTool 工作目录 |
| `--sign-workspace` | tools/workspace/sign-tools | 签名工作目录 |
| `--apktool-path` | tools/bin/apktool.bat | apktool 可执行文件 |
| `--adb-path` | tools/bin/adb.exe | adb 可执行文件 |
| `--list-tools` | - | 仅打印工具清单并退出 |

---

## 工作流程

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  AI 助手    │◄───►│  ApkMCP 统一单服务器  │◄───►│ APKTool/ADB/签名 │
│ (任意客户端) │ 单连接│  (server.py FastMCP) │     │ /Frida/静态分析 │
└─────────────┘     └──────────────────────┘     └─────────────────┘
        │                     │                            │
        │  1. 调用 apktool_decode_apk 等工具                │
        │─────────────────────────────────────►            │
        │                     │  2. 执行本地工具链          │
        │                     │───────────────────────────►│
        │                     │  3. 返回结果               │
        │                     │◄───────────────────────────│
        │  4. 生成分析报告     │                            │
        │◄─────────────────────────────────────            │
```

---

## 报告生成

使用提示词模板进行分析后，会自动生成结构化的 Markdown 报告：

| 报告名称 | 内容 | 保存位置 |
|----------|------|----------|
| `分析报告.md` | 通用 APK 分析报告 | `[工作目录]/分析报告.md` |
| `广告分析报告.md` | 广告 SDK 识别和去除方案 | `[工作目录]/广告分析报告.md` |
| `会员分析报告.md` | 会员验证机制分析 | `[工作目录]/会员分析报告.md` |
| `加固分析报告.md` | 加固识别和脱壳方案 | `[工作目录]/加固分析报告.md` |
| `网络分析报告.md` | 网络通信分析 | `[工作目录]/网络分析报告.md` |
| `逆向分析报告.md` | 综合逆向工程报告 | `[工作目录]/逆向分析报告.md` |

---

## 安全提示

1. **仅用于合法的安全研究和学习目的**
2. **仅分析您拥有合法权限的应用程序**
3. **不要将统一服务器绑定到公网地址（使用 `--host 0.0.0.0` 时请注意）**
4. **APK 修改后需要重新签名才能安装**
5. **分析完成后断开 MCP 连接即可释放资源；HTTP 模式用 `stop` 命令清理残留进程**

---

## 许可证

本项目采用 **Apache License 2.0** 开源许可证，详见 [LICENSE](LICENSE)。

---

## 致谢

- [JADX](https://github.com/skylot/jadx) - 优秀的 Android 反编译工具
- [APKTool](https://github.com/iBotPeaches/Apktool) - 强大的 APK 反编译/重打包工具
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) - Python MCP SDK
- [Anthropic MCP](https://github.com/anthropics/mcp) - Model Context Protocol
- [Frida](https://frida.re/) - 动态插桩工具包

---

<div align="center">

**Made with ❤️ for Android Reverse Engineering**

</div>
