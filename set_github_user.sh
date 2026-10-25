#!/usr/bin/env bash
# Replace the __GH_USER__ placeholder with your GitHub username in every text file of the repo
# (and in ../CV_header_line.txt if it exists). Usage:  bash set_github_user.sh <github-username>
# The github.io host name is written in lower case (GitHub Pages host names are case-insensitive).
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: bash set_github_user.sh <github-username>" >&2; exit 1; }
U="$1"; [[ "$U" =~ ^[A-Za-z0-9-]{1,39}$ ]] || { echo "invalid GitHub username: $U" >&2; exit 1; }
L="$(printf '%s' "$U" | tr '[:upper:]' '[:lower:]')"
cd "$(dirname "$0")"
files=$(grep -rIl --exclude-dir=.git --exclude-dir=.venv --exclude=set_github_user.sh "__GH_USER__" . || true)
[ -f ../CV_header_line.txt ] && grep -q "__GH_USER__" ../CV_header_line.txt && files="$files ../CV_header_line.txt"
[ -n "$files" ] || { echo "no placeholder left"; exit 0; }
for f in $files; do
  sed -i.bak -e "s/__GH_USER__\.github\.io/${L}.github.io/g" -e "s/__GH_USER__/${U}/g" "$f" && rm -f "$f.bak"
  echo "updated $f"
done
