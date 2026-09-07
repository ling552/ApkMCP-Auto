#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApkMCP-Auto 统一命令行工具（单服务器版）

默认管理单个统一 MCP 服务器（server.py），一个连接即可调用全部工具分组。
旧版 7 服务器分散模式保留在 --legacy 选项中以便兼容。

用法:
    python apkmcp.py status                     # 查看统一服务器状态
    python apkmcp.py list                       # 列出全部分组与工具
    python apkmcp.py config                     # 生成 Trae 配置（默认）
    python apkmcp.py config --client cursor     # 生成指定客户端配置
    python apkmcp.py config --client all        # 生成全部主流客户端配置
    python apkmcp.py install                    # 安装统一服务器核心依赖
    python apkmcp.py install --frida            # 额外安装 frida 可选依赖
    python apkmcp.py start                      # 前台启动统一服务器（stdio）
    python apkmcp.py start --http               # 前台启动统一服务器（HTTP 调试）
    python apkmcp.py stop                       # 停止后台残留的统一服务器进程
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows 控制台默认 GBK 编码会无法输出中文/符号，优先切换为 UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None and getattr(_stream, "encoding", "").lower() != "utf-8":
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 项目根目录（apkmcp.py 所在目录）
PROJECT_ROOT = Path(__file__).resolve().parent
SERVER_FILE = PROJECT_ROOT / "server.py"
TOOLS_DIR = PROJECT_ROOT / "tools"
BIN_DIR = TOOLS_DIR / "bin"

UNIFIED_SERVER_NAME = "apkmcp"
UNIFIED_DEFAULT_PORT = 8660

# 分组定义（与 server.py 保持一致，用于 list/status 展示）
GROUPS = [
    ("apktool", "APK 解码/编码与 Smali 修改", "tools/apktool/server.py"),
    ("adb", "设备管理与调试", "tools/adb/server.py"),
    ("sign", "密钥管理与 APK 签名", "tools/sign-tools/server.py"),
    ("static", "静态分析（权限/字符串/端点/SDK）", "tools/static-analyzer/server.py"),
    ("diff", "文件对比", "tools/diff/server.py"),
    ("frida", "动态插桩分析（可选依赖）", "tools/frida/server.py"),
]

# 主流 MCP 客户端配置表
# format: mcpServers（通用）、vscode（servers）、continue（yaml 片段）
CLIENTS: Dict[str, Dict[str, Any]] = {
    "trae": {
        "paths": [".trae/mcp.json", ".trae/config.json"],
        "format": "mcpServers",
        "local": True,
        "hint": "Trae 会自动读取项目 .trae/mcp.json（.trae/config.json 为旧版兼容）。",
    },
    "cursor": {
        "paths": [".cursor/mcp.json"],
        "format": "mcpServers",
        "local": True,
        "hint": "Cursor：Settings > MCP 中确认 apkmcp 已启用（项目级 .cursor/mcp.json）。",
    },
    "vscode": {
        "paths": [".vscode/mcp.json"],
        "format": "vscode",
        "local": True,
        "hint": "VS Code：需安装支持 MCP 的 Copilot 扩展，配置位于 .vscode/mcp.json。",
    },
    "cline": {
        "paths": ["mcp-configs/cline_mcp_settings.json"],
        "format": "mcpServers",
        "local": False,
        "hint": "Cline：将该文件内容合并到 Cline 的 MCP 设置（cline_mcp_settings.json）中。",
    },
    "claude-desktop": {
        "paths": ["mcp-configs/claude_desktop_config.json"],
        "format": "mcpServers",
        "local": False,
        "hint": ("Claude Desktop：将文件内容复制到全局配置后重启生效；"
                 "Windows: %APPDATA%\\Claude\\claude_desktop_config.json；"
                 "macOS: ~/Library/Application Support/Claude/claude_desktop_config.json。"),
    },
    "windsurf": {
        "paths": ["mcp-configs/windsurf_mcp_config.json"],
        "format": "mcpServers",
        "local": False,
        "hint": "Windsurf：将内容合并到 ~/.codeium/windsurf/mcp_config.json 后重启。",
    },
    "cherry-studio": {
        "paths": ["mcp-configs/cherry_studio_mcp.json"],
        "format": "mcpServers",
        "local": False,
        "hint": "Cherry Studio：在设置 > MCP 服务器中导入该 JSON 文件。",
    },
    "continue": {
        "paths": ["mcp-configs/apkmcp-continue.yaml"],
        "format": "continue",
        "local": False,
        "hint": "Continue：将该 yaml 片段合并到 ~/.continue/config.yaml 的 mcpServers 节点。",
    },
    "generic": {
        "paths": ["mcp.json"],
        "format": "mcpServers",
        "local": True,
        "hint": "通用 MCP 客户端：直接导入 mcp.json 即可。",
    },
}


# ==================== 统一服务器配置生成 ====================

def build_server_entry(use_relative: bool = False, with_jadx: bool = False,
                       http_mode: bool = False,
                       extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """构建单服务器 MCP 条目（stdio 默认，http 可选）。"""
    python_exe = sys.executable
    if http_mode:
        entry: Dict[str, Any] = {
            "url": f"http://127.0.0.1:{UNIFIED_DEFAULT_PORT}/mcp",
            "description": "ApkMCP 统一单服务器（HTTP 模式，需先运行 python server.py --http）",
        }
        return {UNIFIED_SERVER_NAME: entry}

    if use_relative:
        server_path = "server.py"
    else:
        server_path = str(SERVER_FILE)
        python_exe = str(Path(sys.executable).resolve())

    args = [server_path] + (extra_args or [])
    servers = {
        UNIFIED_SERVER_NAME: {
            "command": python_exe,
            "args": args,
            "description": "ApkMCP 统一单服务器：一个连接调用全部逆向工具（apktool/adb/sign/static/diff/frida）",
        }
    }
    if with_jadx:
        # JADX 由 Java 版 server.jar 独立提供（配合 JADX-GUI 插件），可选启用
        java_exe = str(BIN_DIR / "jre" / "bin" / "java.exe")
        jar_path = str(TOOLS_DIR / "jadx" / "server.jar")
        if use_relative:
            java_exe = "tools/bin/jre/bin/java.exe"
            jar_path = "tools/jadx/server.jar"
        servers["apkmcp-jadx"] = {
            "command": java_exe,
            "args": ["-jar", jar_path],
            "description": "JADX MCP 服务器（可选，需配合 JADX-GUI 使用）",
        }
    return servers


def render_client_file(client: str, servers: Dict[str, Any]) -> str:
    """按客户端格式渲染配置文件内容。"""
    fmt = CLIENTS[client]["format"]
    if fmt == "vscode":
        # VS Code MCP 规范使用 servers 节点
        adapted = {}
        for name, entry in servers.items():
            if "url" in entry:
                adapted[name] = {"type": "http", "url": entry["url"]}
            else:
                adapted[name] = {"type": "stdio", "command": entry["command"],
                                 "args": entry["args"]}
        return json.dumps({"servers": adapted}, indent=2, ensure_ascii=False)
    if fmt == "continue":
        # Continue 的 config.yaml 片段（手写 yaml，避免新增依赖）
        lines = ["# 合并到 ~/.continue/config.yaml 的 mcpServers 节点", "mcpServers:"]
        for name, entry in servers.items():
            if "url" in entry:
                lines += [f"  - name: {name}", f"    url: {entry['url']}"]
            else:
                lines += [f"  - name: {name}",
                          f"    command: {entry['command']}"]
                lines.append("    args:")
                for a in entry["args"]:
                    lines.append(f"      - {a}")
        return "\n".join(lines) + "\n"
    # 通用 mcpServers 格式（含 trae/cursor/cline/claude/windsurf/cherry/generic）
    payload = {"mcpServers": {}}
    for name, entry in servers.items():
        item: Dict[str, Any] = {}
        if "url" in entry:
            item["url"] = entry["url"]
        else:
            item["command"] = entry["command"]
            item["args"] = entry["args"]
        if client == "trae":
            # 兼容旧版 Trae 配置字段
            item["type"] = "stdio" if "url" not in entry else "http"
            item["enabled"] = True
        if "description" in entry:
            item["description"] = entry["description"]
        payload["mcpServers"][name] = item
    return json.dumps(payload, indent=2, ensure_ascii=False)


def write_client_config(client: str, content: str) -> List[str]:
    """写入客户端配置文件，返回写入路径列表。"""
    written = []
    for rel in CLIENTS[client]["paths"]:
        path = PROJECT_ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # 合并策略：若目标已存在且为 mcpServers 格式，则合并而非覆盖
        if path.exists() and CLIENTS[client]["format"] in ("mcpServers", "vscode"):
            try:
                merged = merge_config_file(path, content, CLIENTS[client]["format"])
                if merged is not None:
                    content_to_write = merged
                else:
                    content_to_write = content
            except Exception:
                content_to_write = content
        else:
            content_to_write = content
        path.write_text(content_to_write, encoding="utf-8")
        written.append(str(path))
    return written


def merge_config_file(path: Path, new_content: str, fmt: str) -> Optional[str]:
    """把新服务器条目合并进已有配置文件（保留用户其他服务器）。"""
    old = json.loads(path.read_text(encoding="utf-8"))
    new = json.loads(new_content)
    if fmt == "vscode":
        node_old = old.get("servers", {})
        node_old.update(new.get("servers", {}))
        old["servers"] = node_old
    else:
        node_old = old.get("mcpServers", {})
        node_old.update(new.get("mcpServers", {}))
        old["mcpServers"] = node_old
    return json.dumps(old, indent=2, ensure_ascii=False)


# ==================== 命令实现 ====================

def cmd_status(_args) -> int:
    """查看统一服务器状态。"""
    print("\n" + "=" * 72)
    print("ApkMCP 统一单服务器状态")
    print("=" * 72)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"统一服务器: {'存在' if SERVER_FILE.exists() else '缺失'} ({SERVER_FILE.name})")

    # 核心依赖检查
    try:
        import fastmcp  # noqa: F401
        print("核心依赖 fastmcp: 已安装")
        fastmcp_ok = True
    except ImportError:
        print("核心依赖 fastmcp: 未安装（运行 python apkmcp.py install）")
        fastmcp_ok = False

    print("\n分组模块:")
    all_ok = SERVER_FILE.exists() and fastmcp_ok
    for group, desc, rel in GROUPS:
        exists = (PROJECT_ROOT / rel).exists()
        flag = "✓" if exists else "✗"
        extra = ""
        if group == "frida":
            try:
                import frida  # noqa: F401
                extra = "（frida 已安装）"
            except ImportError:
                extra = "（frida 未安装，可选，见 install --frida）"
        print(f"  [{flag}] {group:<10} {desc}{extra}")
        all_ok = all_ok and (exists or group == "frida")

    # 二进制文件
    print("\n二进制文件:")
    for name, rel in [("adb", "tools/bin/adb.exe"),
                      ("apktool", "tools/bin/apktool.jar"),
                      ("jadx-gui", "tools/bin/jadx-gui.exe"),
                      ("jre", "tools/bin/jre/bin/java.exe")]:
        exists = (PROJECT_ROOT / rel).exists()
        print(f"  [{'✓' if exists else '✗'}] {name:<10} {rel}")

    print("\n使用: python apkmcp.py config --client all 生成各客户端配置，")
    print("      python apkmcp.py start 启动统一服务器（断开连接即释放资源）。")
    print("=" * 72)
    return 0 if all_ok else 1


def cmd_list(_args) -> int:
    """列出全部分组与工具（前缀命名）。"""
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from server import MODULE_SPECS
    except ImportError as exc:
        print(f"错误: 无法加载统一服务器定义: {exc}")
        return 1
    print("\n" + "=" * 72)
    print("ApkMCP 统一单服务器工具清单（调用时使用前缀名）")
    print("=" * 72)
    total = 0
    for group, spec in MODULE_SPECS.items():
        print(f"\n[{group}] {spec['description']}")
        for tool in spec["tools"]:
            print(f"  - {spec['prefix']}_{tool}")
            total += 1
    print(f"\n另有元工具: apkmcp_help（帮助）、apkmcp_status（健康检查）")
    print(f"共 {total} 个分组工具 + 2 个元工具。JADX 由 Java 版独立提供（可选）。")
    print("=" * 72)
    return 0


def cmd_config(args) -> int:
    """生成 MCP 客户端配置。"""
    clients: List[str]
    if args.client == "all":
        clients = list(CLIENTS.keys())
    else:
        if args.client not in CLIENTS:
            print(f"错误: 未知客户端 '{args.client}'")
            print(f"可用客户端: {', '.join(list(CLIENTS.keys()) + ['all'])}")
            return 1
        clients = [args.client]

    # 兼容旧版：--legacy 生成 7 服务器分散配置
    if args.legacy:
        return cmd_config_legacy(args)

    extra_args: List[str] = []
    if args.disable:
        extra_args += ["--disable", args.disable]
    servers = build_server_entry(use_relative=args.relative,
                                 with_jadx=args.with_jadx,
                                 http_mode=args.http,
                                 extra_args=extra_args)

    if args.preview or args.output:
        # 预览 / 输出通用格式到指定文件
        content = render_client_file("generic", servers)
        if args.preview:
            print("\n配置预览（generic 格式）:")
            print(content)
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
            print(f"\n已保存到: {out}")
        if args.preview or args.output:
            if not args.client or args.client == "generic":
                return 0

    print(f"\n正在生成 {len(clients)} 个客户端配置（统一单服务器）…")
    for client in clients:
        content = render_client_file(client, servers)
        written = write_client_config(client, content)
        for path in written:
            print(f"  ✓ [{client}] {path}")
        print(f"    提示: {CLIENTS[client]['hint']}")
    print("\n全部使用相对/绝对路径说明:")
    print("  默认使用绝对路径（最稳妥，各客户端启动目录不同也能找到）；")
    print("  如需移动项目目录，加 --relative 重新生成即可。")
    return 0


def cmd_config_legacy(args) -> int:
    """生成旧版 7 服务器分散配置（兼容模式）。"""
    from pathlib import Path as _Path

    def _rel(*parts) -> str:
        return str(_Path(*parts)).replace("\\", "/")

    if args.relative:
        java_cmd = "tools/bin/jre/bin/java.exe"
    else:
        java_cmd = str(BIN_DIR / "jre" / "bin" / "java.exe")
    python_cmd = "python" if args.relative else str(Path(sys.executable).resolve())

    def _p(*parts) -> str:
        return _rel(*parts) if args.relative else str(PROJECT_ROOT.joinpath(*parts))

    servers = {
        "jadx-mcp-server": {"command": java_cmd, "args": ["-jar", _p("tools", "jadx", "server.jar")]},
        "apktool-mcp-server": {"command": python_cmd, "args": [_p("tools", "apktool", "server.py"), "--workspace", _p("tools", "workspace", "apktool"), "--apktool-path", _p("tools", "bin", "apktool.bat")]},
        "adb-mcp-server": {"command": python_cmd, "args": [_p("tools", "adb", "server.py"), "--adb-path", _p("tools", "bin", "adb.exe")]},
        "sign-tools-mcp-server": {"command": python_cmd, "args": [_p("tools", "sign-tools", "server.py"), "--workspace", _p("tools", "workspace", "sign-tools")]},
        "static-analyzer": {"command": python_cmd, "args": [_p("tools", "static-analyzer", "server.py")]},
        "diff-tool": {"command": python_cmd, "args": [_p("tools", "diff", "server.py")]},
        "frida-mcp-server": {"command": python_cmd, "args": [_p("tools", "frida", "server.py")]},
    }
    payload = {"mcpServers": {}}
    for name, entry in servers.items():
        item = dict(entry)
        item["type"] = "stdio"
        item["enabled"] = True
        payload["mcpServers"][name] = item
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.preview:
        print(content)
    out = Path(args.output) if args.output else PROJECT_ROOT / ".trae" / "config.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"\n旧版分散配置已保存到: {out}")
    return 0


def cmd_install(args) -> int:
    """安装统一服务器依赖。"""
    req = PROJECT_ROOT / "requirements.txt"
    if not req.exists():
        print(f"错误: 找不到 {req}")
        return 1
    print("正在安装统一服务器核心依赖…")
    ret = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)])
    if ret.returncode != 0:
        print("✗ 核心依赖安装失败")
        return 1
    print("✓ 核心依赖安装成功")
    if args.frida:
        req_f = PROJECT_ROOT / "requirements-frida.txt"
        print("\n正在安装 frida 可选依赖…")
        ret = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_f)])
        if ret.returncode != 0:
            print("✗ frida 依赖安装失败（frida_* 工具将不可用，可稍后重试）")
            return 1
        print("✓ frida 依赖安装成功")
    else:
        print("\n提示: 如需动态分析（frida_* 工具），运行 python apkmcp.py install --frida")
    return 0


def cmd_start(args) -> int:
    """前台启动统一服务器（Ctrl+C 停止并释放资源）。"""
    if not SERVER_FILE.exists():
        print("错误: 找不到统一服务器 server.py")
        return 1
    cmd = [sys.executable, str(SERVER_FILE)]
    if args.http:
        cmd += ["--http", "--host", args.host, "--port", str(args.port)]
    if args.disable:
        cmd += ["--disable", args.disable]
    if args.workspace:
        cmd += ["--workspace", args.workspace]
    print("正在启动 ApkMCP 统一单服务器…")
    print(f"命令: {' '.join(cmd)}")
    print("按 Ctrl+C 停止并释放资源。")
    try:
        ret = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        return ret.returncode
    except KeyboardInterrupt:
        print("\n已停止，资源已释放。")
        return 0


def cmd_stop(_args) -> int:
    """停止残留的统一服务器后台进程（释放端口与资源）。"""
    print("正在查找残留的统一服务器进程（server.py）…")
    killed = 0
    try:
        if os.name == "nt":
            # Windows：用 wmic 按命令行匹配
            out = subprocess.run(
                ["wmic", "process", "where", "commandline like '%server.py%'",
                 "get", "processid"],
                capture_output=True, text=True)
            pids = [p.strip() for p in out.stdout.split() if p.strip().isdigit()]
            # 排除当前进程
            pids = [p for p in pids if int(p) != os.getpid()]
            for pid in pids:
                r = subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    print(f"  ✓ 已停止 PID {pid}")
                    killed += 1
        else:
            r = subprocess.run(["pkill", "-f", "server.py"],
                               capture_output=True, text=True)
            killed = 1 if r.returncode == 0 else 0
    except FileNotFoundError:
        print("  未找到系统进程管理命令，请手动关闭服务器窗口。")
        return 1
    if killed == 0:
        print("  未发现残留进程，无需处理。")
    else:
        print(f"  共停止 {killed} 个进程，资源已释放。")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """主函数。"""
    parser = argparse.ArgumentParser(
        description="ApkMCP-Auto 统一命令行工具（单服务器版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                              # 查看统一服务器状态
  %(prog)s list                                # 列出全部分组与工具
  %(prog)s config                              # 生成 Trae 配置（默认）
  %(prog)s config --client cursor              # 生成 Cursor 配置
  %(prog)s config --client all                 # 生成全部主流客户端配置
  %(prog)s config --client all --with-jadx     # 附带可选的 JADX 服务器
  %(prog)s install                             # 安装核心依赖
  %(prog)s install --frida                     # 附带安装 frida 可选依赖
  %(prog)s start                               # 启动统一服务器（stdio）
  %(prog)s start --http --port 8660            # 启动统一服务器（HTTP 调试）
  %(prog)s stop                                # 停止残留进程并释放资源
        """,
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    p = sub.add_parser("status", help="查看统一服务器状态")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="列出全部分组与工具")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("config", help="生成 MCP 客户端配置")
    p.add_argument("--client", default="trae",
                   help="目标客户端: trae/cursor/vscode/cline/claude-desktop/windsurf/cherry-studio/continue/generic/all（默认 trae）")
    p.add_argument("-o", "--output", help="额外保存通用格式到指定文件")
    p.add_argument("-p", "--preview", action="store_true", help="预览配置内容")
    p.add_argument("--relative", action="store_true", help="使用相对路径（便于移动项目目录）")
    p.add_argument("--with-jadx", action="store_true", help="附带可选的 JADX 服务器条目")
    p.add_argument("--http", action="store_true", help="生成 HTTP 模式配置（需先运行 server.py --http）")
    p.add_argument("--disable", default="", help="透传给服务器的禁用分组（如 frida,adb）")
    p.add_argument("--legacy", action="store_true", help="生成旧版 7 服务器分散配置（兼容）")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("install", help="安装依赖")
    p.add_argument("--frida", action="store_true", help="同时安装 frida 可选依赖")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("start", help="启动统一服务器")
    p.add_argument("--http", action="store_true", help="HTTP 模式（默认 stdio）")
    p.add_argument("--host", default="127.0.0.1", help="HTTP 监听地址")
    p.add_argument("--port", type=int, default=UNIFIED_DEFAULT_PORT, help="HTTP 监听端口")
    p.add_argument("--disable", default="", help="禁用的分组，逗号分隔")
    p.add_argument("--workspace", default="", help="APKTool 工作目录（覆盖默认）")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("stop", help="停止残留进程并释放资源")
    p.set_defaults(func=cmd_stop)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
