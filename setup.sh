#!/bin/bash
# senior_analyst 一键安装脚本
# 用法: git clone https://github.com/<user>/senior-analyst.git && cd senior-analyst && ./setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="senior_analyst"
SKILL_TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"

echo "========================================="
echo "  Senior Analyst 安装程序"
echo "========================================="
echo ""

# Step 1: 检测 Python 3.10+
echo "[1/6] 检测 Python 环境..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "错误: 未找到 Python。请安装 Python 3.10+ 后重试。"
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "错误: Python 版本过低 ($PY_VERSION)。需要 Python 3.10+。"
    exit 1
fi
echo "  Python $PY_VERSION ✓"

# Step 2: 创建 venv
echo "[2/6] 创建虚拟环境..."
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
    echo "  虚拟环境已创建 ✓"
else
    echo "  虚拟环境已存在，跳过 ✓"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# Step 3: 安装依赖
echo "[3/6] 安装依赖包..."
$VENV_PYTHON -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "  依赖安装完成 ✓"

# Step 4: 注册 MCP 服务器
echo "[4/6] 注册 MCP 服务器..."
if command -v claude &>/dev/null; then
    # 移除旧注册（如有）
    claude mcp remove "$SKILL_NAME" -s user 2>/dev/null || true
    claude mcp add -s user "$SKILL_NAME" "$VENV_PYTHON" "$SCRIPT_DIR/server.py"
    echo "  MCP 服务器已注册 ✓"
else
    echo "  警告: 未找到 claude CLI，跳过 MCP 注册。"
    echo "  请手动运行: claude mcp add -s user $SKILL_NAME $VENV_PYTHON $SCRIPT_DIR/server.py"
fi

# Step 5: 安装 skill 文件
echo "[5/6] 安装 skill 文件..."
mkdir -p "$SKILL_TARGET_DIR"
cp -r "$SCRIPT_DIR/skill/"* "$SKILL_TARGET_DIR/"
echo "  Skill 文件已安装到 $SKILL_TARGET_DIR ✓"

# Step 6: 验证
echo "[6/6] 验证安装..."
if command -v claude &>/dev/null; then
    STATUS=$(claude mcp get "$SKILL_NAME" 2>/dev/null | grep "Status" | head -1 || echo "")
    if echo "$STATUS" | grep -q "Connected"; then
        echo "  MCP 服务器连接正常 ✓"
    else
        echo "  MCP 服务器状态: $STATUS"
        echo "  请重启 Claude Code 后重试。"
    fi
else
    echo "  跳过验证（claude CLI 不可用）"
fi

echo ""
echo "========================================="
echo "  安装完成!"
echo "========================================="
echo ""
echo "  使用方式:"
echo "    /senior_analyst 滴滴    → 直接分析"
echo "    /senior_analyst         → 引导模式"
echo ""
echo "  如果这是首次安装，请重启 Claude Code 使 MCP 服务器生效。"
echo ""
