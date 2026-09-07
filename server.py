#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApkMCP 统一单服务器（Single MCP Server）

把原来 7 个分散的 MCP Server 聚合为 1 个进程对外提供服务，
一个连接即可调用全部工具分组：
  - apktool_* : APK 解码 / 编码 / Smali 修改 / 资源管理
  - adb_*     : 设备管理 / 安装 / 日志 / Shell / 截图
  - sign_*    : 密钥库 / APK 签名 / 签名验证 / zipalign
  - static_*  : 权限 / 字符串 / 端点 / SDK 识别 / 完整分析
  - diff_*    : APK / Smali / 资源 / 文本对比
  - frida_*   : 进程 / 注入 / Hook / 网络拦截 / 内存操作

说明：
  - JADX 仍由 Java 版 server.jar 独立提供（需要配合 JADX-GUI 插件），
    属于可选的第二服务器，默认单服务器配置不包含它。
  - 工具命名统一加分组前缀，避免原多服务器之间的重名冲突
    （如 health_check、get_resource_file、get_workspace_info）。
  - 使用完毕后直接断开 MCP 连接即可释放资源；HTTP 模式按 Ctrl+C 退出，
    会自动清理 Frida 会话等资源。

用法：
    python server.py                        # stdio 模式（供 MCP 客户端调用，默认）
    python server.py --http                 # HTTP 模式（调试用）
    python server.py --http --port 8660     # 指定端口
    python server.py --list-tools            # 仅打印工具清单并退出
    python server.py --disable frida,adb     # 按需裁剪分组
"""

import argparse
import importlib.util
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows 控制台默认 GBK 编码会无法输出中文，优先切换为 UTF-8
# （stdio 传输的 MCP 帧走二进制层，不受此影响）
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None and getattr(_stream, "encoding", "").lower() != "utf-8":
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 项目根目录（本文件所在目录）
PROJECT_ROOT = Path(__file__).resolve().parent
TOOLS_DIR = PROJECT_ROOT / "tools"
BIN_DIR = TOOLS_DIR / "bin"

# 默认配置
DEFAULT_HTTP_PORT = 8660
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_APKTOOL_WORKSPACE = str(TOOLS_DIR / "workspace" / "apktool")
DEFAULT_SIGN_WORKSPACE = str(TOOLS_DIR / "workspace" / "sign-tools")
DEFAULT_APKTOOL_PATH = str(BIN_DIR / "apktool.bat")
DEFAULT_ADB_PATH = str(BIN_DIR / "adb.exe")
DEFAULT_JAVA_HOME = str(BIN_DIR / "jre")

# 各分组模块定义：键 -> 文件、前缀、工具清单
# 工具清单与各 tools/*/server.py 中的 @mcp.tool() 装饰函数保持一致
MODULE_SPECS: Dict[str, Dict[str, Any]] = {
    "apktool": {
        "file": TOOLS_DIR / "apktool" / "server.py",
        "prefix": "apktool",
        "description": "APK 解码/编码与 Smali 修改",
        "tools": [
            "health_check", "decode_apk", "build_apk", "get_manifest",
            "get_apktool_yml", "list_smali_directories", "list_smali_files",
            "get_smali_file", "modify_smali_file", "list_resources",
            "get_resource_file", "modify_resource_file", "search_in_files",
            "clean_project", "analyze_project_structure", "get_workspace_info",
        ],
    },
    "adb": {
        "file": TOOLS_DIR / "adb" / "server.py",
        "prefix": "adb",
        "description": "设备管理与调试",
        "tools": [
            "health_check", "list_devices", "get_device_info", "install_apk",
            "uninstall_package", "get_package_info", "get_logcat", "clear_logcat",
            "execute_shell", "push_file", "pull_file", "screenshot",
            "list_packages", "start_activity", "force_stop_package",
        ],
    },
    "sign": {
        "file": TOOLS_DIR / "sign-tools" / "server.py",
        "prefix": "sign",
        "description": "密钥管理与 APK 签名",
        "tools": [
            "health_check", "generate_keystore", "list_keystores",
            "get_keystore_info", "sign_apk", "verify_signature",
            "zipalign_apk", "delete_keystore", "get_workspace_info",
        ],
    },
    "static": {
        "file": TOOLS_DIR / "static-analyzer" / "server.py",
        "prefix": "static",
        "description": "静态分析（权限/字符串/端点/SDK）",
        "tools": [
            "analyze_permissions", "extract_strings", "extract_endpoints",
            "identify_sdks", "full_analysis",
        ],
    },
    "diff": {
        "file": TOOLS_DIR / "diff" / "server.py",
        "prefix": "diff",
        "description": "文件对比",
        "tools": [
            "compare_apks", "compare_smali", "compare_resources",
            "compare_text_files",
        ],
    },
    "frida": {
        "file": TOOLS_DIR / "frida" / "server.py",
        "prefix": "frida",
        "description": "动态插桩分析（可选依赖 frida）",
        "tools": [
            "list_processes", "attach_process", "spawn_process",
            "resume_process", "inject_script", "hook_function",
            "intercept_network", "scan_memory", "read_memory",
            "write_memory", "get_messages", "detach_session",
            "list_sessions", "enumerate_modules", "enumerate_exports",
        ],
    },
}

# 运行时登记表：分组 -> {"module": 模块对象, "tools": [统一后的工具名]}
LOADED_GROUPS: Dict[str, Dict[str, Any]] = {}
# 加载失败记录：分组 -> 错误信息
FAILED_GROUPS: Dict[str, str] = {}


def log(msg: str) -> None:
    """向 stderr 输出日志（保持 stdout 干净，供 stdio 传输使用）。"""
    print(msg, file=sys.stderr, flush=True)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """解析统一服务器命令行参数。"""
    parser = argparse.ArgumentParser(
        description="ApkMCP 统一单服务器：一个连接调用全部逆向工具"
    )
    parser.add_argument("--http", action="store_true", default=False,
                        help="启用 HTTP 模式（默认 stdio 模式）")
    parser.add_argument("--host", default=DEFAULT_HTTP_HOST,
                        help=f"HTTP 监听地址（默认 {DEFAULT_HTTP_HOST}）")
    parser.add_argument("--port", type=int, default=DEFAULT_HTTP_PORT,
                        help=f"HTTP 监听端口（默认 {DEFAULT_HTTP_PORT}）")
    parser.add_argument("--workspace", default=DEFAULT_APKTOOL_WORKSPACE,
                        help="APKTool 工作目录")
    parser.add_argument("--sign-workspace", default=DEFAULT_SIGN_WORKSPACE,
                        help="签名工具工作目录")
    parser.add_argument("--apktool-path", default=DEFAULT_APKTOOL_PATH,
                        help="apktool 可执行文件路径")
    parser.add_argument("--adb-path", default=DEFAULT_ADB_PATH,
                        help="adb 可执行文件路径")
    parser.add_argument("--java-home", default=DEFAULT_JAVA_HOME,
                        help="Java 主目录（含 keytool）")
    parser.add_argument("--disable", default="",
                        help="禁用的分组，逗号分隔（如 frida,adb）")
    parser.add_argument("--list-tools", action="store_true", default=False,
                        help="仅打印工具清单并退出")
    return parser.parse_args(argv)


def load_submodule(group: str, file_path: Path):
    """导入子模块 server.py。

    子模块顶层会执行 argparse，为避免吞掉本进程参数，
    导入期间临时将 sys.argv 替换为仅含脚本名。
    """
    saved_argv = sys.argv
    sys.argv = [str(file_path)]
    try:
        module_name = f"apkmcp_group_{group}"
        spec = importlib.util.spec_from_file_location(module_name, str(file_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"无法创建模块加载器: {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = saved_argv


def apply_group_config(group: str, module: Any, args: argparse.Namespace) -> None:
    """把统一服务器的参数覆盖到子模块的全局配置上。"""
    if group == "apktool":
        # 工作目录与 apktool 路径
        module.WORKSPACE_DIR = args.workspace
        module.APKTOOL_EXECUTABLE = args.apktool_path
        os.makedirs(args.workspace, exist_ok=True)
    elif group == "adb":
        # adb 可执行文件路径（不存在则回退到系统 PATH 中的 adb）
        if args.adb_path and os.path.exists(args.adb_path):
            module.ADB_EXECUTABLE = args.adb_path
        elif os.path.exists(DEFAULT_ADB_PATH):
            module.ADB_EXECUTABLE = DEFAULT_ADB_PATH
        else:
            module.ADB_EXECUTABLE = "adb"
    elif group == "sign":
        # 签名工作目录与 Java 工具链
        module.WORKSPACE_DIR = args.sign_workspace
        module.KEYSTORE_DIR = os.path.join(args.sign_workspace, "keystores")
        os.makedirs(args.sign_workspace, exist_ok=True)
        os.makedirs(module.KEYSTORE_DIR, exist_ok=True)
        if args.java_home and os.path.isdir(args.java_home):
            module.JAVA_HOME = args.java_home
        try:
            # 重新初始化 keytool/apksigner/zipalign 路径
            module.init_java_paths()
        except Exception as exc:  # noqa: BLE001 - 初始化失败仅告警
            log(f"[警告] sign 分组 Java 工具路径初始化失败: {exc}")


def build_server(args: argparse.Namespace):
    """加载各分组成员并聚合成一个 FastMCP 服务器。"""
    from fastmcp import FastMCP

    # 预置环境变量，避免子模块以相对路径创建杂散目录
    os.environ.setdefault("APKTOOL_WORKSPACE", args.workspace)
    os.environ.setdefault("SIGN_TOOLS_WORKSPACE", args.sign_workspace)

    disabled = {s.strip().lower() for s in args.disable.split(",") if s.strip()}
    # 兼容旧分组名 sign-tools
    if "sign-tools" in disabled:
        disabled.add("sign")

    mcp = FastMCP("ApkMCP-Unified-Server")

    for group, spec in MODULE_SPECS.items():
        if group in disabled:
            log(f"[跳过] 分组 {group}（已通过 --disable 禁用）")
            continue
        file_path: Path = spec["file"]
        if not file_path.exists():
            FAILED_GROUPS[group] = f"文件不存在: {file_path}"
            log(f"[警告] 分组 {group} 缺少文件，已跳过: {file_path}")
            continue
        try:
            module = load_submodule(group, file_path)
        except Exception as exc:  # noqa: BLE001 - 单个分组失败不影响其他分组
            FAILED_GROUPS[group] = str(exc)
            log(f"[警告] 分组 {group} 加载失败，已跳过: {exc}")
            continue

        apply_group_config(group, module, args)

        registered: List[str] = []
        for tool_name in spec["tools"]:
            func = getattr(module, tool_name, None)
            if func is None or not callable(func):
                log(f"[警告] 分组 {group} 缺少工具函数，已跳过: {tool_name}")
                continue
            unified_name = f"{spec['prefix']}_{tool_name}"
            try:
                # 用分组前缀重新注册，保留原函数签名与文档
                mcp.tool(name=unified_name)(func)
                registered.append(unified_name)
            except Exception as exc:  # noqa: BLE001 - 单个工具失败不影响其他工具
                log(f"[警告] 工具注册失败，已跳过 {unified_name}: {exc}")

        LOADED_GROUPS[group] = {"module": module, "tools": registered,
                                "description": spec["description"]}
        log(f"[加载] 分组 {group}: {len(registered)}/{len(spec['tools'])} 个工具")

    register_meta_tools(mcp, args)
    return mcp


def register_meta_tools(mcp: Any, args: argparse.Namespace) -> None:
    """注册服务器自带的元信息工具。"""

    @mcp.tool(name="apkmcp_help")
    def apkmcp_help() -> Dict[str, Any]:
        """获取统一服务器使用帮助与全部分组工具清单。"""
        catalog = {}
        for group, info in LOADED_GROUPS.items():
            catalog[group] = {
                "description": info["description"],
                "tools": info["tools"],
            }
        return {
            "success": True,
            "server": "ApkMCP-Unified-Server",
            "transport": "http" if args.http else "stdio",
            "groups": catalog,
            "failed_groups": FAILED_GROUPS,
            "jadx_note": ("JADX 实时反编译由 Java 版 server.jar 独立提供，"
                          "需配合 JADX-GUI 使用，详见 README。"),
            "release_note": "分析完成后断开 MCP 连接即可释放资源，无需额外清理。",
        }

    @mcp.tool(name="apkmcp_status")
    async def apkmcp_status() -> Dict[str, Any]:
        """查看统一服务器各分组健康状态。"""
        result: Dict[str, Any] = {"success": True, "groups": {},
                                  "failed_groups": FAILED_GROUPS}
        # 复用各分组自带的 health_check（apktool/adb/sign 具备该工具）
        health_map = {"apktool": "apktool_health_check",
                      "adb": "adb_health_check",
                      "sign": "sign_health_check"}
        for group, info in LOADED_GROUPS.items():
            module = info["module"]
            entry: Dict[str, Any] = {"loaded_tools": len(info["tools"]),
                                     "description": info["description"]}
            check_name = health_map.get(group)
            if check_name:
                func_name = check_name.split("_", 1)[1]
                func = getattr(module, func_name, None)
                if callable(func):
                    try:
                        entry["health"] = await func() if _is_coro(func) else func()
                    except Exception as exc:  # noqa: BLE001 - 健康检查失败只记录
                        entry["health"] = {"success": False, "error": str(exc)}
            else:
                entry["health"] = {"success": True, "message": "分组已加载"}
            result["groups"][group] = entry
        # 二进制文件存在性速查
        result["binaries"] = {
            "adb": os.path.exists(args.adb_path),
            "apktool": os.path.exists(args.apktool_path),
            "java": os.path.isdir(args.java_home),
        }
        return result


def _is_coro(func: Any) -> bool:
    """判断是否为协程函数（兼容 async/sync 两类工具函数）。"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


def cleanup_resources() -> None:
    """释放资源：清理 Frida 会话等。"""
    try:
        info = LOADED_GROUPS.get("frida")
        if not info:
            return
        module = info["module"]
        manager = getattr(module, "session_manager", None) or getattr(module, "SESSIONS", None)
        if manager is None:
            return
        # 兼容 SessionManager / 字典两种实现
        sessions = None
        if hasattr(manager, "list_sessions"):
            try:
                sessions = manager.list_sessions()
            except Exception:  # noqa: BLE001 - 清理阶段忽略异常
                sessions = None
        if isinstance(sessions, dict):
            for sid in list(sessions.keys()):
                try:
                    if hasattr(manager, "remove_session"):
                        manager.remove_session(sid)
                    elif hasattr(manager, "detach_session"):
                        manager.detach_session(sid)
                except Exception:  # noqa: BLE001
                    pass
        elif isinstance(manager, dict):
            for sid, sess in list(manager.items()):
                try:
                    sess.detach()
                except Exception:  # noqa: BLE001
                    pass
    except Exception as exc:  # noqa: BLE001 - 清理失败仅记录
        log(f"[警告] 资源清理异常: {exc}")


def print_catalog() -> None:
    """打印已加载的工具清单（ human 可读）。"""
    total = 0
    print("=" * 72)
    print("ApkMCP 统一单服务器工具清单")
    print("=" * 72)
    for group, info in LOADED_GROUPS.items():
        print(f"\n[{group}] {info['description']}（{len(info['tools'])} 个）")
        for name in info["tools"]:
            print(f"  - {name}")
            total += 1
    if FAILED_GROUPS:
        print("\n[加载失败的分组]")
        for group, err in FAILED_GROUPS.items():
            print(f"  - {group}: {err}")
    print(f"\n共 {total} 个工具。JADX 由 Java 版 server.jar 独立提供（可选）。")
    print("=" * 72)


def main(argv: Optional[List[str]] = None) -> int:
    """统一服务器入口。"""
    args = parse_args(argv)

    # 日志全部走 stderr，避免污染 stdio 传输
    import logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    mcp = build_server(args)

    if args.list_tools:
        print_catalog()
        return 0 if LOADED_GROUPS else 1

    def _on_signal(signum, _frame):
        log(f"\n收到信号 {signum}，正在释放资源并退出…")
        cleanup_resources()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _on_signal)
        signal.signal(signal.SIGTERM, _on_signal)
    except Exception:  # noqa: BLE001 - 某些平台不支持 SIGTERM 注册
        pass

    try:
        if args.http:
            if args.host not in ("127.0.0.1", "localhost", "::1"):
                log(f"[安全警告] 监听非本地地址 {args.host}，"
                    "MCP 服务无鉴权，仅可在可信网络使用！")
            log(f"[启动] ApkMCP 统一服务器 HTTP 模式: http://{args.host}:{args.port}")
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        else:
            log("[启动] ApkMCP 统一服务器 stdio 模式（断开连接即释放资源）")
            mcp.run()
    except KeyboardInterrupt:
        log("\n用户中断，正在释放资源…")
    finally:
        cleanup_resources()
    return 0


if __name__ == "__main__":
    sys.exit(main())
