#!/bin/bash
# senior_analyst 在线升级脚本
# 用法: ./upgrade.sh 或通过 /senior_analyst --upgrade 调用
# 功能: 从 GitHub 拉取最新版本，更新本地安装（支持 Claude Code 和 Codex CLI 双路径）

set -e

REPO_URL="https://github.com/rrred0324/senior-analyst.git"
SKILL_NAME="senior_analyst"
CONFIG_DIR="$HOME/.config/senior_analyst"
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR" 2>/dev/null || true
}
trap cleanup EXIT

echo "========================================="
echo "  Senior Analyst 在线升级"
echo "========================================="
echo ""

# Step 1: 读取当前版本 + 探测已安装路径
CURRENT_VERSION="unknown"
TARGETS=()

# 收集所有已安装的路径（Claude + Codex）
if [ -f "$HOME/.claude/skills/$SKILL_NAME/VERSION" ]; then
    CURRENT_VERSION="$(tr -d '[:space:]' < "$HOME/.claude/skills/$SKILL_NAME/VERSION")"
    TARGETS+=("$HOME/.claude/skills/$SKILL_NAME")
fi
if [ -f "$HOME/.agents/skills/$SKILL_NAME/VERSION" ]; then
    _CODEX_VER="$(tr -d '[:space:]' < "$HOME/.agents/skills/$SKILL_NAME/VERSION")"
    # 如果 Claude 路径没找到版本，用 Codex 的版本
    if [ "$CURRENT_VERSION" = "unknown" ]; then
        CURRENT_VERSION="$_CODEX_VER"
    fi
    TARGETS+=("$HOME/.agents/skills/$SKILL_NAME")
fi

echo "[1/6] 当前版本: $CURRENT_VERSION"
echo "  已安装路径: ${TARGETS[*]}"

if [ ${#TARGETS[@]} -eq 0 ]; then
    echo ""
    echo "  未找到已有安装。请先运行 ./setup.sh 或 ./install.sh"
    exit 1
fi

# Step 2: 备份当前安装
echo ""
echo "[2/6] 备份当前安装..."
_BACKUP_DIR=$(mktemp -d /tmp/senior-analyst-backup-XXXXXXXX)
for _TARGET in "${TARGETS[@]}"; do
    _BASENAME="$(basename "$_TARGET")"
    _PARENT="$(dirname "$_TARGET")"
    cp -r "$_TARGET" "$_BACKUP_DIR/$_BASENAME" 2>/dev/null || true
    echo "  已备份: $_TARGET → $_BACKUP_DIR/$_BASENAME"
done

# Step 3: 克隆最新代码
echo ""
echo "[3/6] 从 GitHub 拉取最新版本..."
if ! git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" 2>/dev/null; then
    echo "  错误: 无法连接 GitHub。请检查网络后重试。"
    echo "  正在恢复备份..."
    for _TARGET in "${TARGETS[@]}"; do
        _BASENAME="$(basename "$_TARGET")"
        if [ -d "$_BACKUP_DIR/$_BASENAME" ]; then
            rm -rf "$_TARGET"
            cp -r "$_BACKUP_DIR/$_BASENAME" "$_TARGET"
            echo "  已恢复: $_TARGET"
        fi
    done
    rm -rf "$_BACKUP_DIR"
    echo "  备选方案: 手动执行 git pull 后运行 ./setup.sh"
    exit 1
fi
echo "  拉取成功 ✓"

# Step 4: 读取新版本
NEW_VERSION="unknown"
if [ -f "$TEMP_DIR/repo/VERSION" ]; then
    NEW_VERSION="$(tr -d '[:space:]' < "$TEMP_DIR/repo/VERSION")"
fi

if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
    echo ""
    echo "  已是最新版本 ($NEW_VERSION)，无需升级。"
    rm -rf "$_BACKUP_DIR"
    exit 0
fi

echo ""
echo "[4/6] 新版本: $NEW_VERSION"
echo "  更新内容: $CURRENT_VERSION → $NEW_VERSION"

# Step 5: 更新每个已安装路径
echo ""
echo "[5/6] 更新 skill 文件..."
for _TARGET in "${TARGETS[@]}"; do
    cp -r "$TEMP_DIR/repo/skill/"* "$_TARGET/"
    cp "$TEMP_DIR/repo/VERSION" "$_TARGET/"
    # 同步 bin 脚本到 skill 父级 bin 目录（如果有）
    if [ -d "$_TARGET/../bin" ]; then
        cp -r "$TEMP_DIR/repo/bin/"* "$_TARGET/../bin/" 2>/dev/null || true
    fi
    echo "  已更新: $_TARGET ✓"
done

# 部署 update-check 到 ~/.local/bin
mkdir -p "$HOME/.local/bin"
cp "$TEMP_DIR/repo/bin/senior_analyst-update-check" "$HOME/.local/bin/" 2>/dev/null || true
chmod +x "$HOME/.local/bin/senior_analyst-update-check" 2>/dev/null || true
echo "  Update checker deployed to ~/.local/bin ✓"

# Step 6: 写 marker + 清理 snooze + 展示 What's New
mkdir -p "$CONFIG_DIR"
echo "$CURRENT_VERSION" > "$CONFIG_DIR/just-upgraded-from"
rm -f "$CONFIG_DIR/update-snoozed"

echo ""
echo "[6/6] What's New in v$NEW_VERSION:"
echo "─────────────────────────────────────"
if [ -f "$TEMP_DIR/repo/CHANGELOG.md" ]; then
    sed -n "/^## \[${NEW_VERSION}\]/,/^## \[/{/^## \[/!p}" "$TEMP_DIR/repo/CHANGELOG.md" | head -40
else
    echo "  See: https://github.com/rrred0324/senior-analyst/releases/tag/v${NEW_VERSION}"
fi
echo "─────────────────────────────────────"

# 清理：立即删除 git clone 临时目录，备份 5 分钟后清理
rm -rf "$TEMP_DIR"
(sleep 300 && rm -rf "$_BACKUP_DIR" 2>/dev/null || true) &

echo ""
echo "========================================="
echo "  升级完成!"
echo "========================================="
echo ""
echo "  $CURRENT_VERSION → $NEW_VERSION"
echo ""
echo "  请重启 Claude Code 使更新生效。"
echo ""
