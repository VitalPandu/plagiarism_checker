#!/bin/bash

echo "Testing Kong Rate Limiting..."
echo "========================================"

for i in {1..20}; do
  echo ""
  echo "Request #$i:"

  response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST http://localhost:8000/api/plagiarism/check \
    -F "original=@original.txt" \
    -F "submission=@submission.txt")

  http_code=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)

  echo "Status: $http_code"

  if [ "$http_code" == "429" ]; then
    echo "⚠️  Rate limit hit!"
  elif [ "$http_code" == "200" ]; then
    echo "✅ Success"
  fi

  sleep 2
done

echo ""
echo "========================================"
echo "Test completed!"