# 贡献指南

感谢你对 ApkMCP-Auto 的关注！本项目欢迎 Issue 与 Pull Request。

## 基本要求

- 代码注释与交流使用**简体中文**。
- Python 代码兼容 3.10+，新增工具函数必须带类型注解。
- 统一服务器工具命名规范：`{分组前缀}_{原工具名}`（如 `apktool_decode_apk`）。

## 开发流程

```bash
# 1. 克隆并安装依赖
git clone https://github.com/ling552/ApkMCP-Auto.git
cd ApkMCP-Auto
pip install -r requirements.txt

# 2. 新建分支修改
git checkout -b feat/xxx

# 3. 自检（编译 + 工具清单 + 配置生成）
python -m py_compile server.py apkmcp.py tools/*/server.py
python server.py --disable frida --list-tools
python apkmcp.py config --client generic -p

# 4. 同步文档
# 新增/更名工具时，请同步更新 README.md、AI_GUIDE.md、
# prompt_template.md 与 .trae/skills/apkmcp-auto/SKILL.md

# 5. 提交并发起 PR
```

## 新增工具分组

1. 在 `tools/<分组>/server.py` 中用 FastMCP 实现（参考 `tools/diff/server.py` 结构）。
2. 在 `server.py` 的 `MODULE_SPECS` 中登记：文件路径、前缀、工具清单。
3. 在 `apkmcp.py` 的 `GROUPS` 中登记分组信息。
4. 更新上述 4 份文档中的工具表。

## 报告问题

- 提交 Issue 时请注明：操作系统、Python 版本、复现命令、完整报错。
- 安全漏洞请优先通过私密渠道联系维护者。
