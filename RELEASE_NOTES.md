# ApkMCP-Auto v2.0.0（统一单服务器版）发布说明

## 本次更新

### ★ 统一单服务器

- 新增 `server.py`：把 6 个 Python 工具分组（apktool / adb / sign / static / diff / frida）
  聚合为**一个 MCP 服务器进程**，一个连接调用全部 60+ 工具。
- 工具统一加分组前缀（如 `apktool_decode_apk`），解决旧版多服务器重名冲突。
- 内置 `apkmcp_help`（查清单）、`apkmcp_status`（查健康状态）元工具。
- stdio / HTTP 双模式；Ctrl+C 或断开连接自动释放资源（含 Frida 会话清理）。
- 按需裁剪：`--disable frida,adb`。

### ★ 主流客户端全支持

- `python apkmcp.py config --client all` 一键生成 9 种客户端配置：
  Trae / Cursor / VS Code / Cline / Claude Desktop / Windsurf / Cherry Studio / Continue / 通用。
- 旧版仅支持 Trae；旧版 7 服务器配置可用 `config --legacy` 生成（已弃用）。

### ★ 启动与释放

- 日常使用无需手动启动（客户端按配置自动拉起 stdio 模式）。
- 新增 `start-server.bat` / `start-server.sh` 快捷脚本（HTTP 调试 / 状态 / 停止）。
- 新增 `apkmcp.py stop` 清理残留进程；旧版 `start_all_servers.py` 标记弃用保留兼容。

### ★ 文档同步

- README.md、AI_GUIDE.md 重写为单服务器版；prompt_template.md、SKILL.md 工具名同步加前缀。

### ★ Git 工程文件

- 新增 `.gitignore`、`.gitattributes`（LFS 预留）、`LICENSE`（Apache-2.0）、
  `CONTRIBUTING.md`、` .github/workflows/ci.yml` 冒烟测试。

## 升级指南（v1.x → v2.0）

1. `pip install -r requirements.txt`（frida 用户另加 `requirements-frida.txt`）
2. `python apkmcp.py config --client all` 重新生成配置
3. 客户端中删除旧的 7 条服务器记录，只保留 `apkmcp`
4. 提示词中的旧工具名改为前缀命名（如 `decode_apk` → `apktool_decode_apk`）

## 备注

- JADX 实时分析仍由 Java 版 `tools/jadx/server.jar` 独立提供（可选，需配合 JADX-GUI），
  生成配置时加 `--with-jadx` 即可附带。
