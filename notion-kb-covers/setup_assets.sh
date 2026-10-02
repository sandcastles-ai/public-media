#!/usr/bin/env bash
set -euo pipefail

KIT="$(cd "$(dirname "$0")" && pwd)"
APP_PUBLIC="${SANDCASTLES_REPO:?set SANDCASTLES_REPO to your clone of harmeetdhingra/sandcastles}/sandcastles-app/public"

mkdir -p "$KIT/fonts" "$KIT/icons" "$KIT/assets" "$KIT/out"

curl -fsSL -o "$KIT/fonts/InterVariable.woff2" "https://rsms.me/inter/font-files/InterVariable.woff2?v=4.1"
curl -fsSL -o "$KIT/fonts/JetBrainsMono-500.woff2" "https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbY2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8-qxTOlOV.woff2"

HEROICONS="academic-cap adjustments-horizontal arrow-down-tray arrow-path arrow-path-rounded-square arrow-right
arrow-top-right-on-square arrow-up-tray arrows-right-left at-symbol banknotes bolt bookmark briefcase calendar chart-bar
chart-pie chat-bubble-left-right check-circle circle-stack clock cloud-arrow-down code-bracket cog-6-tooth command-line
credit-card cursor-arrow-rays document-chart-bar document-duplicate document-text eye film fire folder funnel globe-alt
hand-thumb-up hashtag heart identification inbox key light-bulb link list-bullet lock-closed magnifying-glass megaphone
microphone newspaper paper-airplane pencil-square photo play-circle presentation-chart-line puzzle-piece
question-mark-circle queue-list rectangle-stack rocket-launch scale shield-check sparkles square-2-stack
square-3-stack-3d squares-2x2 star swatch tag trash trophy user-group user-plus users video-camera wrench-screwdriver"
for name in $HEROICONS; do
  curl -fsSL -o "$KIT/icons/$name.svg" "https://unpkg.com/heroicons@2.1.5/24/outline/$name.svg"
done
curl -fsSL -o "$KIT/icons/claude.svg" "https://cdn.jsdelivr.net/npm/simple-icons@16.33.0/icons/claude.svg"
curl -fsSL -o "$KIT/icons/lh-openai.svg" "https://unpkg.com/@lobehub/icons-static-svg@1.95.1/icons/openai.svg"
curl -fsSL -o "$KIT/icons/lh-grok.svg" "https://unpkg.com/@lobehub/icons-static-svg@1.95.1/icons/grok.svg"

python3 - "$KIT" "$APP_PUBLIC" <<'EOF'
import glob, os, re, sys
kit, public = sys.argv[1], sys.argv[2]
for f in glob.glob(os.path.join(kit, 'icons', '*.svg')):
    ds = re.findall(r' d="([^"]+)"', open(f).read())
    open(f[:-4] + '.d', 'w').write('|'.join(ds))
svg = open(os.path.join(public, 'logo-banner-dark-mode.svg')).read()
open(os.path.join(kit, 'logo_paths.txt'), 'w').write('\n'.join(re.findall(r'<path d="([^"]+)"', svg)[:4]))
EOF

for f in youtube tiktok instagram logo-icon; do
  cp "$APP_PUBLIC/$f.png" "$KIT/assets/$f.png"
done

echo "assets ready: $(ls "$KIT/icons"/*.d | wc -l) icons, $(ls "$KIT/fonts" | wc -l) fonts, $(ls "$KIT/assets" | wc -l) images"
