param(
  [string]$Base = "http://localhost:8000/api/v1",
  [string]$Email = "admin@example.com",
  [string]$Password = "admin123",
  [string]$SessionId = "smoke5"
)

Write-Host "→ Smoke checkout: $Base ($Email)" -ForegroundColor Cyan

# Login
$login = Invoke-RestMethod -Uri "$Base/auth/login" -Method Post -ContentType "application/json" -Body (@{ email=$Email; password=$Password } | ConvertTo-Json)
$token = $login.access_token
if (-not $token) { throw "Login failed: no access_token" }
$auth = @{ Authorization = "Bearer $token" }
$headers = @{ Authorization = "Bearer $token"; Cookie = "session_id=$SessionId" }

# Cart + Checkout
$products = Invoke-RestMethod -Uri "$Base/catalog/products" -Method Get -Headers $auth
if (-not $products -or $products.Count -eq 0) { throw "No products available" }
$productId = $products[0].id
Invoke-RestMethod -Uri "$Base/cart/items" -Method Post -Headers $headers -ContentType "application/json" -Body (@{ product_id=$productId; qty=1 } | ConvertTo-Json) | Out-Null
Invoke-RestMethod -Uri "$Base/cart/lock" -Method Post -Headers $headers | Out-Null
$start = Invoke-RestMethod -Uri "$Base/checkout/start" -Method Post -Headers $headers -ContentType "application/json" -Body (@{ } | ConvertTo-Json)
$ord = $start.order_number
if (-not $ord) { throw "Checkout start failed: no order_number" }

# Addresses (usar trailing slash)
$addresses = Invoke-RestMethod -Uri "$Base/addresses/" -Method Get -Headers $auth
$shipId = ($addresses | Where-Object { $_.kind -eq "shipping" } | Select-Object -First 1).id
$billId = ($addresses | Where-Object { $_.kind -eq "billing" } | Select-Object -First 1).id
if (-not $shipId -or -not $billId) { throw "Address list incomplete: shipping=$shipId billing=$billId" }

# Select + Confirm
Invoke-RestMethod -Uri "$Base/checkout/$ord/addresses/select" -Method Post -Headers $auth -ContentType "application/json" -Body (@{ shipping_address_id=$shipId; billing_address_id=$billId } | ConvertTo-Json) | Out-Null
$confirm = Invoke-RestMethod -Uri "$Base/checkout/$ord/addresses/confirm" -Method Post -Headers $auth

$result = [pscustomobject]@{
  orderNumber = $ord
  canProceedToPayment = $confirm.can_proceed_to_payment
}
$result | ConvertTo-Json -Depth 3