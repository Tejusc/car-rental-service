#!/usr/bin/env bash
set -e
BASE="http://localhost:8000"

echo "=== Add cars ==="
CAR1=$(curl -s -X POST "$BASE/cars" -H "Content-Type: application/json" \
  -d '{"make":"Toyota","model":"Camry","year":2022}')
CAR2=$(curl -s -X POST "$BASE/cars" -H "Content-Type: application/json" \
  -d '{"make":"Honda","model":"Civic","year":2021}')
echo "$CAR1" | python3 -m json.tool
echo "$CAR2" | python3 -m json.tool

ID1=$(echo "$CAR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo ""
echo "=== List all cars ==="
curl -s "$BASE/cars" | python3 -m json.tool

echo ""
echo "=== Filter: only available Toyotas ==="
curl -s "$BASE/cars?make=Toyota&available=true" | python3 -m json.tool

echo ""
echo "=== Rent car (Alice) ==="
curl -s -X POST "$BASE/cars/$ID1/rent" \
  -H "Content-Type: application/json" \
  -d '{"renter_name":"Alice"}' | python3 -m json.tool

echo ""
echo "=== Try double-rent (expect 409) ==="
curl -s -X POST "$BASE/cars/$ID1/rent" \
  -H "Content-Type: application/json" \
  -d '{"renter_name":"Bob"}' | python3 -m json.tool

echo ""
echo "=== Return car ==="
curl -s -X POST "$BASE/cars/$ID1/return" | python3 -m json.tool

echo ""
echo "=== List rental records ==="
curl -s "$BASE/cars/rentals" | python3 -m json.tool
