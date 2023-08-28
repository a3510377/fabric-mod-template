#!/bin/bash

# for json parse
jq --version > /dev/null || apt install jq -y

output=$1

echo "## Summary" > $output
echo "| Subproject | for Minecraft | File | Size | SHA-256 |" >> $output
echo "| ---------- | ------------- | ---- | ---- | ------- |" >> $output

shopt -s extglob
for version in $(jq -r '.[]' versions.json); do
  file="*Not Found*"
  file_size="*N/A*"
  file_sha256="*N/A*"
  game_versions=$(cat gradle.properties | grep "game_versions" | cut -d "=" -f 2 | tr -d "\r " | sed "s/,/, /g")

  for filename in !(*-@(dev|sources)).jar; do
    file_size=$(du -h $filename | awk '{ print $1 }')
    file_sha256=$(sha256sum $filename | awk '{ print $1 }')
    break
  done

  if [ ! -z $filename ]; then
    file=$filename
  fi

  echo "|$version|$game_versions|$file|$file_size|$file_sha256|" >> $output
done
