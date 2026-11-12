#!/bin/bash
# Downloads all high-level AcousticBrainz archives (about 35 to 40 GB, 30 files) with resume,
# then checks them against the sha256sums file on the same page.
# Usage: bash download_acousticbrainz_highlevel_NOT_USED.sh "<URL of the folder that lists the 30 archives>" "<target folder>"
# Re-run the same command if it stops: finished files are skipped and partial ones continue.
set -u
URL="${1:?Give the URL of the folder that lists the archives (the page address in your browser)}"
DIR="${2:-.}"
URL="${URL%/}/"
mkdir -p "$DIR"; cd "$DIR" || exit 1
echo "Reading the file list from $URL"
LIST="$(curl -fsSL "$URL" | grep -o 'href="[^"]*\.tar\.zst"' | sed 's/^href="//; s/"$//' | xargs -n1 basename | sort -u)"
if [ -z "$LIST" ]; then echo "Found no .tar.zst links at that address. Check the URL."; exit 1; fi
echo "Archives found: $(echo "$LIST" | wc -l | tr -d ' ')"
echo "Tip: keep the computer plugged in and awake (this script uses caffeinate on a Mac)."
fetch() {
  if command -v caffeinate >/dev/null 2>&1; then
    caffeinate -i curl -L -C - --retry 20 --retry-delay 10 --retry-all-errors -O "$1"
  else
    curl -L -C - --retry 20 --retry-delay 10 --retry-all-errors -O "$1"
  fi
}
FAILED=0
for f in $LIST; do
  echo "== $f"
  fetch "${URL}${f}" || { echo "Stopped on $f. Run the same command again to resume."; FAILED=1; break; }
done
if [ $FAILED -ne 0 ]; then exit 1; fi
echo "All archives downloaded. Fetching the checksum file..."
curl -fsSL -O "${URL}sha256sums" || { echo "No sha256sums file found. Skipping the check."; exit 0; }
echo "Checking (takes a few minutes)..."
if command -v sha256sum >/dev/null 2>&1; then sha256sum -c sha256sums; else shasum -a 256 -c sha256sums; fi
