#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYT_PY="$SCRIPT_DIR/syt.py"

if [ ! -f "$SYT_PY" ]; then
    echo "error: syt.py not found in $SCRIPT_DIR!"
    exit 1
fi

echo ""
echo "  installing syt... hold tight! :3"
echo ""

if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
elif [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

WRAPPER="$INSTALL_DIR/syt"
cat > "$WRAPPER" <<WRAPPER_EOF
#!/bin/sh
exec python3 "$SYT_PY" "\$@"
WRAPPER_EOF

chmod +x "$WRAPPER"
chmod +x "$SYT_PY"

SHELL_NAME="$(basename "$SHELL")"
case "$SHELL_NAME" in
    zsh)  RC="$HOME/.zshrc" ;;
    bash) RC="$HOME/.bashrc" ;;
    fish) RC="$HOME/.config/fish/config.fish" ;;
    *)    RC="$HOME/.profile" ;;
esac

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
    echo "  adding $INSTALL_DIR to PATH in $RC..."
    echo "" >> "$RC"
    if [ "$SHELL_NAME" = "fish" ]; then
        echo "set -gx PATH $INSTALL_DIR \$PATH" >> "$RC"
    else
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$RC"
    fi
fi

if [ "$SHELL_NAME" = "zsh" ]; then
    if ! grep -q "alias syt=" "$RC" 2>/dev/null; then
        echo "" >> "$RC"
        echo "alias syt='noglob syt'" >> "$RC"
        echo "  added noglob alias to zshrc!"
    fi
fi

echo ""
echo "  restart your terminal or run: source $RC"
echo "  to start using syt! :3"
MISSING=""
if ! command -v yt-dlp &>/dev/null; then MISSING="$MISSING yt-dlp"; fi
if ! command -v ffmpeg &>/dev/null; then MISSING="$MISSING ffmpeg"; fi

if [ -n "$MISSING" ]; then
    echo ""
    echo "  missing dependencies:$MISSING"
    echo "  install them:"
    echo "$MISSING" | grep -q "yt-dlp" && echo "    pip install yt-dlp"
    echo "$MISSING" | grep -q "ffmpeg" && {
        if [ "$(uname)" = "Darwin" ]; then
            echo "    brew install ffmpeg"
        else
            echo "    sudo apt install ffmpeg"
        fi
    }
fi

echo ""
echo "  ✓ syt installed to $WRAPPER"
echo "  usage:  syt [link]   or just   syt and enter! :3"
echo ""