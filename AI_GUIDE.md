# ApkMCP-Auto AI 项目指引

> 本文档专为 AI 助手设计，说明如何在本项目中调用 Skill 和 MCP 工具
> 架构：统一单服务器（`server.py`），一个连接调用全部工具分组。

---

## 快速判断

当用户提出以下需求时，**立即调用 `apkmcp-auto` Skill**：

| 用户意图 | 触发关键词 |
|---------|-----------|
| APK 反编译/分析 | "反编译 APK"、"分析 APK"、"查看 APK 代码" |
| Smali 修改 | "修改 Smali"、"改代码"、"去广告"、"破解" |
| APK 打包/签名 | "打包 APK"、"签名"、"重新编译" |
| 设备调试 | "连接手机"、"安装 APK"、"查看日志"、"adb" |
| 代码对比 | "对比 APK"、"比较文件差异"、"diff" |
| 动态分析 | "Hook"、"Frida"、"动态调试"、"拦截请求" |
| 静态分析 | "分析权限"、"提取字符串"、"识别 SDK" |

---

## 调用 Skill

### 方式一：直接调用 Skill 工具（推荐）

当识别到 APK 相关任务时，**立即执行**：

```
调用 Skill: apkmcp-auto
```

Skill 会自动加载并指导后续操作。

### 方式二：使用 apkmcp.py 命令行工具

```bash
# 查看统一服务器状态
python apkmcp.py status

# 生成全部主流客户端配置
python apkmcp.py config --client all

# 安装核心依赖（frida 可选）
python apkmcp.py install
python apkmcp.py install --frida

# 列出全部分组与工具
python apkmcp.py list
```

---

## MCP 配置说明（单服务器）

项目默认只暴露 **1 个 MCP 服务器 `apkmcp`**（`server.py`，stdio 模式，客户端自动拉起）。
用 `python apkmcp.py config --client all` 可生成 Trae / Cursor / VS Code / Cline /
Claude Desktop / Windsurf / Cherry Studio / Continue / 通用共 9 种客户端配置。

| 工具分组 | 前缀 | 功能 | 何时调用 |
|---------|------|------|---------|
| APKTool | `apktool_*` | APK 解码/编码 | 需要反编译 APK 为 Smali、修改资源、重新打包 |
| ADB | `adb_*` | 设备管理和调试 | 需要连接设备、安装 APK、获取日志、执行 Shell |
| Sign | `sign_*` | APK 签名和密钥管理 | 需要生成密钥、签名 APK、验证签名 |
| Static | `static_*` | 静态分析 | 需要分析权限、提取字符串、识别第三方 SDK |
| Diff | `diff_*` | 文件对比 | 需要对比两个 APK 或 Smali 文件的差异 |
| Frida | `frida_*` | 动态插桩分析 | 需要 Hook 函数、拦截网络、内存操作 |
| Meta | `apkmcp_*` | 帮助与状态 | `apkmcp_help` 查清单，`apkmcp_status` 查健康状态 |

> **JADX 可选服务器**：JADX 实时反编译由 Java 版 `tools/jadx/server.jar` 独立提供，
> 需配合 JADX-GUI 使用。如需启用，加 `--with-jadx` 重新生成配置，会多出一条
> `apkmcp-jadx` 服务器记录（工具名不带前缀，如 `get_class_source`）。

---

## 典型任务处理流程

### 任务 1：完整 APK 分析

```
用户：分析这个 APK 文件

AI 处理步骤：
1. 调用 Skill: apkmcp-auto
2. 使用 apktool_decode_apk 解码 APK
3. 使用 static_full_analysis 进行静态分析
4. 使用 apktool_get_manifest 分析 Manifest
5. 使用 apktool_search_in_files 定位关键代码
6. 生成分析报告
```

### 任务 2：去除广告

```
用户：帮我去掉这个 APK 的广告

AI 处理步骤：
1. 调用 Skill: apkmcp-auto
2. 使用 apktool_decode_apk 解码 APK
3. 使用 static_identify_sdks 识别广告 SDK
4. 使用 apktool_search_in_files 定位广告代码
5. 使用 apktool_modify_smali_file 修改 Smali 代码
6. 使用 apktool_build_apk 重新构建 APK
7. 使用 sign_sign_apk 签名 APK
8. 使用 diff_compare_apks 对比修改前后的差异
```

### 任务 3：设备调试

```
用户：连接我的手机并安装 APK

AI 处理步骤：
1. 调用 Skill: apkmcp-auto
2. 使用 adb_list_devices 列出设备
3. 使用 adb_install_apk 安装 APK
4. 使用 adb_get_logcat 获取日志
```

### 任务 4：动态分析

```
用户：Hook 这个应用的登录函数

AI 处理步骤：
1. 调用 Skill: apkmcp-auto
2. 使用 frida_list_processes 列出进程
3. 使用 frida_attach_process 附加到目标进程
4. 使用 frida_hook_function Hook 目标函数
5. 使用 frida_get_messages 获取消息
```

---

## MCP 工具详细说明（单服务器前缀命名）

### 1. APKTool 分组（`apktool_*`）

**用途**：APK 解码、修改、重打包

**常用工具**：
- `apktool_decode_apk` - 解码 APK
- `apktool_build_apk` - 构建 APK
- `apktool_get_smali_file` / `apktool_modify_smali_file` - Smali 操作
- `apktool_list_resources` / `apktool_modify_resource_file` - 资源管理
- `apktool_search_in_files` - 文件搜索

**调用示例**：
```python
# 解码 APK
apktool_decode_apk(apk_path="D:/test.apk")

# 获取 Smali 文件
apktool_get_smali_file(project_dir="tools/workspace/apktool/test",
                       class_name="com.example.MainActivity")

# 修改 Smali 文件
apktool_modify_smali_file(project_dir="...", class_name="...", content="...")

# 构建 APK
apktool_build_apk(project_dir="tools/workspace/apktool/test")
```

### 2. ADB 分组（`adb_*`）

**用途**：设备管理和调试

**常用工具**：
- `adb_list_devices` - 列出设备
- `adb_install_apk` / `adb_uninstall_package` - 应用管理
- `adb_get_logcat` - 获取日志
- `adb_execute_shell` - 执行 Shell 命令
- `adb_screenshot` - 截图

**调用示例**：
```python
# 列出设备
adb_list_devices()

# 安装 APK
adb_install_apk(apk_path="D:/test.apk", device_id="xxx")

# 获取日志
adb_get_logcat(package_name="com.example.app", max_lines=100)
```

### 3. 签名分组（`sign_*`）

**用途**：APK 签名管理

**常用工具**：
- `sign_generate_keystore` - 生成密钥库
- `sign_sign_apk` - 签名 APK
- `sign_verify_signature` - 验证签名
- `sign_zipalign_apk` - 对齐优化

**调用示例**：
```python
# 生成密钥库
sign_generate_keystore(name="mykey", password="123456", alias="key0")

# 签名 APK
sign_sign_apk(apk_path="D:/test.apk", keystore_name="mykey",
              keystore_password="123456", key_alias="key0")
```

### 4. 静态分析分组（`static_*`）

**用途**：静态代码分析

**常用工具**：
- `static_analyze_permissions` - 权限分析
- `static_extract_strings` - 提取字符串
- `static_extract_endpoints` - 提取 URL/API
- `static_identify_sdks` - 识别第三方 SDK
- `static_full_analysis` - 完整分析

**调用示例**：
```python
# 完整分析
static_full_analysis(input_path="tools/workspace/apktool/test")

# 识别 SDK
static_identify_sdks(input_path="tools/workspace/apktool/test")
```

### 5. 对比分组（`diff_*`）

**用途**：文件对比

**常用工具**：
- `diff_compare_apks` - 对比 APK
- `diff_compare_smali` - 对比 Smali 文件
- `diff_compare_resources` - 对比资源

**调用示例**：
```python
# 对比两个 APK
diff_compare_apks(apk_path1="D:/original.apk", apk_path2="D:/modified.apk")
```

### 6. Frida 分组（`frida_*`）

**用途**：动态插桩分析（需 `install --frida` + 设备端 frida-server）

**常用工具**：
- `frida_list_processes` - 列出进程
- `frida_attach_process` - 附加进程
- `frida_hook_function` - Hook 函数
- `frida_intercept_network` - 拦截网络
- `frida_scan_memory` / `frida_read_memory` - 内存操作

**调用示例**：
```python
# 列出进程
frida_list_processes()

# 附加进程
frida_attach_process(target="com.example.app")

# Hook 函数
frida_hook_function(session_id="xxx", class_name="com.example.Login",
                    method_name="checkPassword")
```

---

## 工作目录结构

```
ApkMCP-Auto/
├── server.py                      # ★ 统一单服务器（唯一 MCP 入口）
├── apkmcp.py                      # 统一命令行工具
├── requirements.txt               # 核心依赖
├── requirements-frida.txt         # frida 可选依赖
├── mcp.json                       # 通用客户端配置（自动生成）
├── mcp-configs/                   # 各客户端配置（自动生成）
├── .trae/mcp.json                 # Trae 配置（自动生成）
├── .cursor/mcp.json               # Cursor 配置（自动生成）
├── .vscode/mcp.json               # VS Code 配置（自动生成）
├── tools/                         # 工具分组实现（由统一服务器加载）
│   ├── bin/                       # 二进制工具（adb/apktool/jadx-gui/jre）
│   ├── apktool/ adb/ sign-tools/
│   ├── static-analyzer/ diff/ frida/
│   ├── jadx/server.jar            # JADX（Java，可选独立运行）
│   └── workspace/                 # 工作空间（解码产物、密钥库）
└── AI_GUIDE.md                    # 本文件
```

---

## 重要提示

1. **单服务器**：默认只有 `apkmcp` 一个 MCP 连接，工具名均带分组前缀
2. **参数确认**：调用前可用 `apkmcp_help` 查看工具清单，不确定参数时先小步试探
3. **依赖安装**：首次使用前运行 `python apkmcp.py install`（frida 另加 `--frida`）
4. **配置生成**：运行 `python apkmcp.py config --client all` 生成各客户端配置
5. **资源释放**：分析完成后断开 MCP 连接即可；HTTP 模式按 Ctrl+C 或运行 `stop`
6. **合法性**：仅用于合法的安全研究和学习目的，仅分析拥有合法权限的应用

---

## 快速参考卡

| 我想做... | 调用... | 关键工具链 |
|----------|--------|-----------|
| 查看 APK 代码 | static + apktool | static_full_analysis → apktool_get_smali_file |
| 修改 APK | apktool | apktool_decode_apk → apktool_modify_smali_file → apktool_build_apk |
| 签名 APK | sign | sign_sign_apk → sign_verify_signature |
| 连接设备 | adb | adb_list_devices → adb_install_apk |
| 分析权限 | static | static_analyze_permissions |
| 对比文件 | diff | diff_compare_apks |
| Hook 函数 | frida | frida_attach_process → frida_hook_function |
| 查帮助/状态 | meta | apkmcp_help / apkmcp_status |

---

**文档版本**: 2.0（单服务器版）
**适用项目**: ApkMCP-Auto
