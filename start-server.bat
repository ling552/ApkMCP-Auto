@echo off
chcp 65001 >nul
title ApkMCP 统一单服务器

REM ApkMCP-Auto 统一单服务器启动脚本（单服务器版）
REM 一个连接即可调用全部工具分组，无需逐个启动 7 个服务器。
REM MCP 客户端（Trae/Cursor/Claude 等）会按配置自动拉起 stdio 模式，
REM 本脚本主要用于：HTTP 调试启动 / 状态查看 / 残留进程释放。

set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ================================================================================
echo ApkMCP 统一单服务器
echo ================================================================================
echo.

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

echo [信息] 项目根目录: %PROJECT_ROOT%
cd /d "%PROJECT_ROOT%"

if "%~1"=="" goto :show_help
if /i "%~1"=="http" goto :start_http
if /i "%~1"=="status" goto :status
if /i "%~1"=="list" goto :list_tools
if /i "%~1"=="stop" goto :stop
if /i "%~1"=="config" goto :config
if /i "%~1"=="help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--help" goto :show_help
echo [错误] 未知选项: %~1
echo.
goto :show_help

:start_http
echo [启动] 统一服务器 HTTP 模式（按 Ctrl+C 停止并释放资源）...
echo.
python server.py --http --port 8660
goto :end

:status
python apkmcp.py status
goto :end

:list_tools
python server.py --disable frida --list-tools
goto :end

:stop
python apkmcp.py stop
goto :end

:config
echo [配置] 生成全部主流客户端配置...
python apkmcp.py config --client all
goto :end

:show_help
echo 用法: start-server.bat [选项]
echo.
echo 说明: MCP 客户端按配置自动拉起 stdio 模式，日常使用无需手动启动。
echo       以下选项用于调试、查看状态与释放资源。
echo.
echo 选项:
echo   http       以 HTTP 模式启动统一服务器（调试用，端口 8660）
echo   status     查看统一服务器与各分组状态
echo   list       列出全部工具（前缀命名）
echo   stop       停止残留的服务器后台进程，释放资源
echo   config     生成全部主流客户端配置
echo   help       显示此帮助信息
echo.
echo 旧版 7 服务器分散启动仍可用（已弃用）:
echo   start-servers.bat all
echo   python start_all_servers.py
echo.
pause
goto :end

:end
echo.
echo ================================================================================
echo 操作完成（分析结束后断开 MCP 连接即释放资源）
echo ================================================================================
