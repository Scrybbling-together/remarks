#!/bin/sh

# Usage:
#   ./download_remarkable_fonts.sh
#   remarks input output --fonts-dir fonts/

# Links found in /usr/share/remarkable/webui/assets/index.js from a Remarkable Paper
# Pro, firmware version v3.24.0.149.

mkdir -p fonts
curl https://cdn.sanity.io/files/xpujt61d/production/47ed70b8382b19b3487648982b78a7b2ada3eb3f.woff2 --output fonts/reMarkableSerifItalic.woff2
curl https://cdn.sanity.io/files/xpujt61d/production/f75f89732cba9023fa578d7fd28666798de505d0.woff2 --output fonts/reMarkableSerif.woff2
curl https://cdn.sanity.io/files/xpujt61d/production/227f58180ac8527c16669879375e917f9d5ab6e4.woff2 --output fonts/reMarkableSans.woff2

echo "Downloaded reMarkable fonts to fonts/"
echo "Use with: remarks input output --fonts-dir fonts/"
