#!/usr/bin/env bash
# ApkMCP-Auto 统一单服务器启动脚本（macOS / Linux）
# MCP 客户端按配置自动拉起 stdio 模式，日常使用无需手动启动；
# 本脚本用于 HTTP 调试启动 / 状态查看 / 残留进程释放。
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

usage() {
  cat <<'EOF'
用法: ./start-server.sh [选项]

说明: MCP 客户端按配置自动拉起 stdio 模式，日常使用无需手动启动。

选项:
  http       以 HTTP 模式启动统一服务器（调试用，端口 8660）
  status     查看统一服务器与各分组状态
  list       列出全部工具（前缀命名）
  stop       停止残留的服务器后台进程，释放资源
  config     生成全部主流客户端配置
  help       显示此帮助信息
EOF
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "[错误] 未找到 python3，请先安装 Python 3.10+"
  exit 1
fi

case "${1:-help}" in
  http)
    echo "[启动] 统一服务器 HTTP 模式（按 Ctrl+C 停止并释放资源）..."
    exec python3 server.py --http --port 8660
    ;;
  status)
    python3 apkmcp.py status
    ;;
  list)
    python3 server.py --disable frida --list-tools
    ;;
  stop)
    python3 apkmcp.py stop
    ;;
  config)
    python3 apkmcp.py config --client all
    ;;
  help|-h|--help|*)
    usage
    ;;
esac

echo "操作完成（分析结束后断开 MCP 连接即释放资源）"
