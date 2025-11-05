$ErrorActionPreference = "Stop"

function Invoke-Json($method, $url, $body, $headers) {
  if ($null -ne $body) { $b = ($body | ConvertTo-Json -Depth 6) } else { $b = $null }
  return Invoke-RestMethod -Uri $url -Method $method -ContentType "application/json" -Headers $headers -Body $b
}

$Base = "http://backend:8000/api/v1"

Write-Host "Login admin..."
$login = Invoke-Json Post "$Base/auth/login" @{ email = "admin@example.com"; password = "admin123" } @{}
$token = $login.access_token
$auth = @{ Authorization = "Bearer $token" }

Write-Host "Catálogo y agregar al carrito..."
$products = Invoke-Json Get "$Base/catalog/products" $null $auth
if (-not $products) { throw "No hay productos" }
$pid = $products[0].id
Invoke-Json Post "$Base/cart/items" @{ product_id = $pid; qty = 1 } $auth | Out-Null
Invoke-Json Post "$Base/cart/lock" $null $auth | Out-Null

Write-Host "Iniciar checkout..."
$ck = Invoke-Json Post "$Base/checkout/start" @{} $auth
$ord = $ck.order_number
if (-not $ord) { $ord = $ck.order.order_number }
if (-not $ord) { throw "order_number no obtenido" }

Write-Host "Direcciones: listar o crear si falta..."
$list = Invoke-Json Get "$Base/checkout/$ord/addresses" $null $auth
if (-not $list.can_continue) {
  # crear shipping/billing básicas
  Invoke-Json Post "$Base/addresses" @{ kind = "shipping"; name = "Smoke User"; street = "Calle 123"; city = "CABA"; province = "Buenos Aires"; zip_code = "1000"; country = "AR"; phone = "011" } $auth | Out-Null
  Invoke-Json Post "$Base/addresses" @{ kind = "billing"; name = "Smoke User"; street = "Calle 123"; city = "CABA"; province = "Buenos Aires"; zip_code = "1000"; country = "AR"; phone = "011" } $auth | Out-Null
  $list = Invoke-Json Get "$Base/checkout/$ord/addresses" $null $auth
}
$shipId = $list.defaults.shipping_id
$billId = $list.defaults.billing_id
if (-not $shipId -or -not $billId) { throw "Faltan defaults de direcciones" }

Write-Host "Seleccionar y confirmar direcciones..."
Invoke-Json Post "$Base/checkout/$ord/addresses/select" @{ shipping_address_id = $shipId; billing_address_id = $billId } $auth | Out-Null
$confirm = Invoke-Json Post "$Base/checkout/$ord/addresses/confirm" $null $auth
if (-not $confirm.can_proceed_to_payment) { throw "No puede continuar a pago" }

Write-Host "Crear preferencia MP..."
$pref = Invoke-Json Post "$Base/payments/mp/preference" @{ order_number = $ord } $auth
Write-Host "Init point:" ($pref.init_point ?? $pref.sandbox_init_point)

Write-Host "Simular webhook firmado (root) con payment_id..."
$pid = "SMOKE-" + ([System.Guid]::NewGuid().ToString())
$ts = [int][double]((Get-Date -Date (Get-Date).ToUniversalTime()).ToFileTimeUtc() / 1e7) # usar time() más simple
$ts = [int](Get-Date -UFormat %s)
$reqId = [System.Guid]::NewGuid().ToString()
$body = @{ action = "payment.updated"; data = @{ id = $pid } } | ConvertTo-Json -Depth 6
$secret = $env:MP_WEBHOOK_SECRET
if (-not $secret) { $secret = "dev-secret" }
$baseStr = "$reqId:$ts:$body"
$hmac = [System.BitConverter]::ToString((New-Object System.Security.Cryptography.HMACSHA256([Text.Encoding]::UTF8.GetBytes($secret))).ComputeHash([Text.Encoding]::UTF8.GetBytes($baseStr))).Replace("-", "").ToLower()
$headers = @{ "x-request-id" = $reqId; "x-signature" = "ts=$ts,v1=$hmac" }
$root = Invoke-RestMethod -Uri "http://backend:8000/webhooks/mp" -Method Post -Headers $headers -ContentType "application/json" -Body $body
Write-Host "Root webhook status:" $root.status

Write-Host "Consultar estado via /api/v1/payments/mp/webhook (idempotente)..."
$api = Invoke-Json Post "$Base/payments/mp/webhook" @{ type = "payment"; data = @{ id = $pid; status = "approved" } } @{}
Write-Host "order_status=" $api.order_status " payment_status=" $api.order_payment_status

Write-Host "SMOKE DONE"