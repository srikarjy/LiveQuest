#!/usr/bin/env bash
FILES=(manifest.json background.js content.js popup.html popup.js)
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    echo "$f OK"
  else
    echo "$f MISSING"
  fi
done

# Validate manifest.json
if node -e "JSON.parse(require('fs').readFileSync('manifest.json','utf8'))" >/dev/null 2>&1; then
  echo "manifest.json valid"
else
  echo "manifest.json INVALID"
fi

# Test backend API
if curl -s -X POST http://localhost:3001/api/generate \
     -H "Content-Type: application/json" \
     -d '{"title":"Terminal Test","selection":"demo"}' \
     | jq . >/dev/null 2>&1; then
  echo "API OK"
else
  echo "API FAIL"
fi
