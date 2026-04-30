#!/bin/bash
# senior_analyst 在线升级脚本
# 用法: ./upgrade.sh 或通过 /senior_analyst --upgrade 调用
# 功能: 从 GitHub 拉取最新版本，更新本地安装

set -e

REPO_URL="https://github.com/rrred0324/senior-analyst.git"
SKILL_NAME="senior_analyst"
SKILL_TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR" 2>/dev/null || true
}
trap cleanup EXIT

echo "========================================="
echo "  Senior Analyst 在线升级"
echo "========================================="
echo ""

# Step 1: 读取当前版本
CURRENT_VERSION="unknown"
if [ -f "$SKILL_TARGET_DIR/VERSION" ]; then
    CURRENT_VERSION=$(cat "$SKILL_TARGET_DIR/VERSION" | tr -d '[:space:]')
fi
echo "[1/5] 当前版本: $CURRENT_VERSION"

# Step 2: 克隆最新代码
echo "[2/5] 从 GitHub 拉取最新版本..."
if ! git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" 2>/dev/null; then
    echo "  错误: 无法连接 GitHub。请检查网络后重试。"
    echo "  备选方案: 手动执行 git pull 后运行 ./setup.sh"
    exit 1
fi
echo "  拉取成功 ✓"

# Step 3: 读取新版本
NEW_VERSION="unknown"
if [ -f "$TEMP_DIR/repo/VERSION" ]; then
    NEW_VERSION=$(cat "$TEMP_DIR/repo/VERSION" | tr -d '[:space:]')
fi

if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
    echo ""
    echo "  已是最新版本 ($NEW_VERSION)，无需升级。"
    exit 0
fi

echo "[3/5] 新版本: $NEW_VERSION"
echo "  更新内容: $CURRENT_VERSION → $NEW_VERSION"

# Step 4: 更新 skill 文件
echo "[4/5] 更新 skill 文件..."
if [ ! -d "$SKILL_TARGET_DIR" ]; then
    echo "  未找到已有安装，执行全新安装..."
    mkdir -p "$SKILL_TARGET_DIR"
fi
cp -r "$TEMP_DIR/repo/skill/"* "$SKILL_TARGET_DIR/"
cp "$TEMP_DIR/repo/VERSION" "$SKILL_TARGET_DIR/"
echo "  Skill 文件已更新到 $SKILL_TARGET_DIR ✓"

# Step 5: 更新 Python 依赖和 MCP 注册
echo "[5/5] 检查依赖更新..."
# 查找已安装的 venv（可能在原 clone 目录或当前目录）
VENV_FOUND=false

# 方案A: 查找已有安装路径（从 MCP 配置中提取）
if command -v claude &>/dev/null; then
    MCP_CMD=$(claude mcp get "$SKILL_NAME" -s user 2>/dev/null | grep -E "command|args" | head -2 || true)
    if [ -n "$MCP_CMD" ]; then
        # 尝试从 MCP 配置中提取 python 路径
        MCP_PYTHON=$(echo "$MCP_CMD" | grep -oE '/[^ ]*senior-analyst[^ ]*python[^ ]*' | head -1 || true)
        if [ -n "$MCP_PYTHON" ] && [ -x "$MCP_PYTHON" ]; then
            VENV_DIR=$(dirname "$(dirname "$MCP_PYTHON")")
            VENV_FOUND=true
        fi
    fi
fi

# 方案B: 如果 venv 在当前目录
if [ "$VENV_FOUND" = "false" ] && [ -d "./venv" ] && [ -f "./venv/bin/python" ]; then
    VENV_DIR="./venv"
    VENV_FOUND=true
fi

# 方案C: 如果用户之前 clone 过
if [ "$VENV_FOUND" = "false" ]; then
    for candidate in "$HOME/senior-analyst" "$HOME/projects/senior-analyst" "$HOME/ai-project/senior-analyst"; do
        if [ -d "$candidate/venv" ] && [ -f "$candidate/venv/bin/python" ]; then
            VENV_DIR="$candidate/venv"
            VENV_FOUND=true
            break
        fi
    done
fi

if [ "$VENV_FOUND" = "true" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python"
    echo "  找到虚拟环境: $VENV_DIR"

    # 更新依赖
    $VENV_PYTHON -m pip install -q -r "$TEMP_DIR/repo/requirements.txt" 2>/dev/null && echo "  依赖已更新 ✓" || echo "  依赖更新跳过（非关键）"

    # 重新注册 MCP（确保 server.py 路径正确）
    if command -v claude &>/dev/null; then
        # 从 venv 路径推导 repo 路径
        REPO_DIR=$(dirname "$VENV_DIR")
        if [ -f "$REPO_DIR/server.py" ]; then
            claude mcp remove "$SKILL_NAME" -s user 2>/dev/null || true
            claude mcp add -s user "$SKILL_NAME" "$VENV_PYTHON" "$REPO_DIR/server.py"
            echo "  MCP 服务器已重新注册 ✓"
        else
            echo "  server.py 未找到，MCP 注册保持不变"
        fi
    fi
else
    echo "  未找到虚拟环境，跳过依赖更新"
    echo "  如需完整更新，请到原安装目录运行: git pull && ./setup.sh"
fi

echo ""
echo "========================================="
echo "  升级完成!"
echo "========================================="
echo ""
echo "  $CURRENT_VERSION → $NEW_VERSION"
echo ""
echo "  请重启 Claude Code 使更新生效。"
echo ""
