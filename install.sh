#!/usr/bin/env bash
# Senior Analyst Installer
# Usage:
#   For Claude Code: ./install.sh
#   For Codex CLI:   ./install.sh codex
#   Via curl:        curl -fsSL https://raw.githubusercontent.com/rrred0324/senior-analyst/main/install.sh | bash -s codex

set -e

PLATFORM="${1:-claude}"  # default to claude for backward compat
SKILL_DIR=""
REPO_PATH="$(pwd)"  # Detect current directory as repo location

# Validate platform
if [[ "$PLATFORM" != "codex" && "$PLATFORM" != "claude" ]]; then
  echo "❌ Unknown platform: $PLATFORM"
  echo "Usage: $0 [claude|codex]"
  exit 1
fi

# Set paths based on platform
if [[ "$PLATFORM" == "codex" ]]; then
  SKILL_DIR="$HOME/.agents/skills/senior_analyst"
  ADAPTER_SRC="adapters/codex"
elif [[ "$PLATFORM" == "claude" ]]; then
  SKILL_DIR="$HOME/.claude/skills/senior_analyst"
  ADAPTER_SRC="skill"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Senior Analyst Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Platform: $PLATFORM"
echo "Target:   $SKILL_DIR"
echo "Source:   $REPO_PATH"
echo ""

# Check if we're in the right directory
if [[ ! -f "VERSION" || ! -f "server.py" ]]; then
  echo "❌ Error: Not in senior-analyst repository root"
  echo "Please cd to the senior-analyst directory first"
  exit 1
fi

# Create skill directory
mkdir -p "$SKILL_DIR"

# Copy adapter-specific files (SKILL.md, agents/, references/)
echo "📦 Copying adapter files..."
cp -r "$ADAPTER_SRC"/* "$SKILL_DIR/"

# Hardcopy shared content
echo "📦 Copying shared content..."
cp -r skill/playbooks "$SKILL_DIR/"
cp -r skill/rubrics "$SKILL_DIR/"
cp -r skill/knowledge "$SKILL_DIR/"
cp -r skill/templates "$SKILL_DIR/"
cp VERSION "$SKILL_DIR/"

# Codex-specific: Replace path placeholders in openai.yaml and .mcp.json
if [[ "$PLATFORM" == "codex" ]]; then
  echo "🔧 Configuring MCP paths..."
  sed -i '' "s|__SENIOR_ANALYST_HOME__|$REPO_PATH|g" \
    "$SKILL_DIR/agents/openai.yaml"
  sed -i '' "s|__SENIOR_ANALYST_HOME__|$REPO_PATH|g" \
    "$SKILL_DIR/.mcp.json"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Installation complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Installed to: $SKILL_DIR"
echo ""
echo "Next steps:"
if [[ "$PLATFORM" == "codex" ]]; then
  echo "  1. Register MCP server:"
  echo "       codex mcp add senior_analyst -- $REPO_PATH/venv/bin/python $REPO_PATH/server.py"
  echo ""
  echo "  2. Configure API keys (optional):"
  echo "       cd $REPO_PATH"
  echo "       ./bin/senior_analyst-setup-keys"
  echo ""
  echo "  3. Restart Codex CLI"
  echo ""
  echo "  4. Test the skill:"
  echo "       Ask Codex: 'analyze Apple's financials'"
else
  echo "  1. Register MCP server:"
  echo "       claude mcp add senior_analyst"
  echo ""
  echo "  2. Configure API keys (optional):"
  echo "       cd $REPO_PATH"
  echo "       ./bin/senior_analyst-setup-keys"
  echo ""
  echo "  3. Restart Claude Code"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
