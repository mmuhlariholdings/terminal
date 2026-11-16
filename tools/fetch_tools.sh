#!/usr/bin/env bash
# Fetch third-party programs the board scripts need but that are too large to keep in git.
# Usage: tools/fetch_tools.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$here/bin"
jar="$here/bin/freerouting-2.0.1.jar"
if [ ! -f "$jar" ]; then
  echo "Downloading Freerouting 2.0.1 (autorouter, GPL-3.0, https://github.com/freerouting/freerouting)..."
  curl -fL "https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar" -o "$jar"
fi
echo "Freerouting: $jar (needs Java 21 or later: java -version)"
