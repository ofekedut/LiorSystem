#!/bin/bash
while true; do
  clear
  echo "=== CPU & Memory Usage ==="
  top -l 1 | head -n 10

  sleep 2
done
