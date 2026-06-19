#!/bin/bash
# senior_analyst 一键安装脚本
# 用法: git clone https://github.com/rrred0324/senior-analyst.git && cd senior-analyst && ./setup.sh

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
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ -n "$PY_VER" ]; then
            PY_MAJOR=$($cmd -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            PY_MINOR=$($cmd -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
                PYTHON="$cmd"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "错误: 未找到 Python 3.10+。请安装后重试。"
    echo "  macOS: brew install python@3.12"
    echo "  Ubuntu: sudo apt install python3.12"
    exit 1
fi

echo "  Python $PY_VER (via $PYTHON) ✓"

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
cp "$SCRIPT_DIR/VERSION" "$SKILL_TARGET_DIR/"
echo "  Skill 文件已安装到 $SKILL_TARGET_DIR ✓"

# Step 5.5: 部署 update-check 脚本
echo "  部署升级检测脚本..."
mkdir -p "$HOME/.local/bin"
cp "$SCRIPT_DIR/bin/senior_analyst-update-check" "$HOME/.local/bin/" 2>/dev/null || true
chmod +x "$HOME/.local/bin/senior_analyst-update-check" 2>/dev/null || true
echo "  Update checker 已部署到 ~/.local/bin ✓"

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

# Step 7: 创建 CLI 包装脚本到 bin/
mkdir -p "$SCRIPT_DIR/bin"
DOCTOR_BIN="$SCRIPT_DIR/bin/senior_analyst-doctor"
SETUP_BIN="$SCRIPT_DIR/bin/senior_analyst-setup-keys"
cat > "$DOCTOR_BIN" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec "$SCRIPT_DIR/venv/bin/python" -m cli.doctor "$@"
EOF
cat > "$SETUP_BIN" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec "$SCRIPT_DIR/venv/bin/python" -m cli.setup_keys "$@"
EOF
chmod +x "$DOCTOR_BIN" "$SETUP_BIN"
echo "  CLI 工具已就绪："
echo "    $DOCTOR_BIN"
echo "    $SETUP_BIN"
echo ""

# Step 8: 自检
echo "[自检] 运行 senior_analyst doctor..."
if "$DOCTOR_BIN"; then
    echo ""
else
    echo ""
    echo "  ⚠️  部分 Tier 0 数据源不健康（见上方 ✗ 标记）"
    echo "  这通常是网络问题，多数情况下可忽略；如持续失败请检查 ~/.config/senior_analyst/.env"
    echo ""
fi

echo "  使用方式:"
echo "    /senior_analyst 滴滴             → 在 Claude Code 中分析"
echo "    /senior_analyst                  → 引导模式"
echo "    $DOCTOR_BIN                      → 健康自检（任何时候）"
echo "    $SETUP_BIN                       → 配置 API key（FRED 免费推荐）"
echo ""
echo "  如果这是首次安装，请重启 Claude Code 使 MCP 服务器生效。"
echo ""
