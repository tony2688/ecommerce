# Mini-scripts cURL / PowerShell

## A) Crear preferencia tras `addresses_selected`

PowerShell (Windows):

```powershell
$token = (Invoke-RestMethod -Uri "http://backend:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (@{ email = "admin@example.com"; password = "admin123" } | ConvertTo-Json)).access_token
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://backend:8000/api/v1/payments/mp/preference" -Method Post -Headers $headers -ContentType "application/json" -Body (@{ order_number = "ORD-XXXX" } | ConvertTo-Json)
```

curl (Linux/macOS):

```bash
TOKEN=$(curl -s -X POST http://backend:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@example.com","password":"admin123"}' | jq -r '.access_token')
curl -s -X POST http://backend:8000/api/v1/payments/mp/preference \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"order_number":"ORD-XXXX"}'
```

## B) Webhook root firmado (ts,v1 + x-request-id)

PowerShell:

```powershell
$pid = "MP-TEST-123"
$ts = [int](Get-Date -UFormat %s)
$reqId = [System.Guid]::NewGuid().ToString()
$body = @{ action = "payment.updated"; data = @{ id = $pid } } | ConvertTo-Json
$secret = $env:MP_WEBHOOK_SECRET; if (-not $secret) { $secret = "dev-secret" }
$baseStr = "$reqId:$ts:$body"
$hmac = [System.BitConverter]::ToString((New-Object System.Security.Cryptography.HMACSHA256([Text.Encoding]::UTF8.GetBytes($secret))).ComputeHash([Text.Encoding]::UTF8.GetBytes($baseStr))).Replace("-", "").ToLower()
$headers = @{ "x-request-id" = $reqId; "x-signature" = "ts=$ts,v1=$hmac" }
Invoke-RestMethod -Uri "http://backend:8000/webhooks/mp" -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

curl:

```bash
PID="MP-TEST-123"; TS=$(date +%s); REQID=$(uuidgen); BODY=$(printf '{"action":"payment.updated","data":{"id":"%s"}}' "$PID")
SECRET="${MP_WEBHOOK_SECRET:-dev-secret}"; BASE="$REQID:$TS:$BODY"; V1=$(printf "%s" "$BASE" | openssl dgst -sha256 -hmac "$SECRET" -binary | xxd -p -c 256)
curl -s -X POST http://backend:8000/webhooks/mp \
  -H "x-request-id: $REQID" -H "x-signature: ts=$TS,v1=$V1" \
  -H 'Content-Type: application/json' \
  -d "$BODY"
```