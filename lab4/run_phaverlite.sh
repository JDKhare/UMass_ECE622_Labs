#!/usr/bin/env bash
# Run PHAVerLite on nmos_model.pha from lab4 (no need to pre-source env).
set -euo pipefail
LAB4_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4_DIR}/../setups/env.sh"
exec phaverlite "${LAB4_DIR}/nmos_model.pha" "$@"
