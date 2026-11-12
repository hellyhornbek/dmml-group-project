#!/bin/bash
# Downloads the full ListenBrainz dump with resume, then checks the MD5 checksum.
# Usage: ./download_listenbrainz_dump.sh "<URL of the ...-full.tar.zst file>" [target folder]
# Re-run the same command if the download stops: it continues where it ended.
set -u
URL="${1:?Give the URL of the full listens dump (.tar.zst) as the first argument}"
DIR="${2:-.}"
mkdir -p "$DIR"; cd "$DIR" || exit 1
FILE="$(basename "${URL%%\?*}")"
echo "Downloading $FILE to $(pwd)"
echo "Tip: keep the computer plugged in and awake (this script uses caffeinate on a Mac)."
if command -v caffeinate >/dev/null 2>&1; then
  caffeinate -i curl -L -C - --retry 20 --retry-delay 10 --retry-all-errors -O "$URL"
else
  curl -L -C - --retry 20 --retry-delay 10 --retry-all-errors -O "$URL"
fi
RC=$?
if [ $RC -ne 0 ]; then echo "curl stopped with code $RC. Run the same command again to resume."; exit $RC; fi
echo "Download finished. Fetching the checksum..."
curl -fsSL -O "${URL}.md5" 2>/dev/null || true
if [ -f "${FILE}.md5" ]; then
  EXPECT="$(awk '{print $1}' "${FILE}.md5")"
  echo "Computing MD5 (takes 10 to 20 minutes)..."
  if command -v md5sum >/dev/null 2>&1; then GOT="$(md5sum "$FILE" | awk '{print $1}')"; else GOT="$(md5 -q "$FILE")"; fi
  if [ "$EXPECT" = "$GOT" ]; then echo "CHECKSUM OK"; else echo "CHECKSUM DIFFERENT: expected $EXPECT got $GOT"; exit 2; fi
else
  echo "No .md5 file found next to the dump. Compare against the MD5SUMS file on the download page."
fi
