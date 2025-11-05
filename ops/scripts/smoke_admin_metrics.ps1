param(
  [string]$Base = "http://localhost:8000/api/v1",
  [string]$Email = "admin@example.com",
  [string]$Password = "admin123",
  [string]$From = (Get-Date).AddDays(-7).ToString('yyyy-MM-dd'),
  [string]$To = (Get-Date).ToString('yyyy-MM-dd')
)

Write-Host "Smoke Admin Metrics — Base=$Base From=$From To=$To" -ForegroundColor Cyan

function Invoke-JsonPost($url, $body) {
  try {
    return Invoke-RestMethod -Uri $url -Method Post -ContentType 'application/json' -Body ($body | ConvertTo-Json -Depth 5)
  } catch {
    Write-Host "POST $url failed: $($_.Exception.Message)" -ForegroundColor Red
    return $null
  }
}

function Invoke-JsonGet($url, $headers) {
  try {
    $resp = Invoke-WebRequest -Uri $url -Headers $headers -Method Get
    return @{ status = $resp.StatusCode; body = $resp.Content }
  } catch {
    $status = $_.Exception.Response.StatusCode.value__
    $content = $null
    try { $content = (New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()).ReadToEnd() } catch {}
    return @{ status = $status; body = $content }
  }
}

# Login
$loginUrl = "$Base/auth/login"
$loginBody = @{ email = $Email; password = $Password }
$login = Invoke-JsonPost -url $loginUrl -body $loginBody
if (-not $login) { exit 1 }

$token = $login.access_token
if (-not $token) {
  Write-Host "Login sin token, respuesta:" -ForegroundColor Yellow
  $login | ConvertTo-Json -Depth 5 | Write-Output
  exit 1
}
$headers = @{ Authorization = "Bearer $token" }

# Daily
$dailyUrl = "$Base/admin/metrics/daily?from=$From&to=$To"
$daily = Invoke-JsonGet -url $dailyUrl -headers $headers
Write-Host "Daily: status=$($daily.status) body=$(($daily.body | Out-String).Trim().Substring(0, [Math]::Min(200, ($daily.body | Out-String).Length)))"

# Categories
$catUrl = "$Base/admin/metrics/categories?from=$From&to=$To"
$categories = Invoke-JsonGet -url $catUrl -headers $headers
Write-Host "Categories: status=$($categories.status) body=$(($categories.body | Out-String).Trim().Substring(0, [Math]::Min(200, ($categories.body | Out-String).Length)))"

# Stock
$stockUrl = "$Base/admin/metrics/stock"
$stock = Invoke-JsonGet -url $stockUrl -headers $headers
Write-Host "Stock: status=$($stock.status) body=$(($stock.body | Out-String).Trim().Substring(0, [Math]::Min(200, ($stock.body | Out-String).Length)))"

Write-Host "Smoke Admin Metrics finalizado." -ForegroundColor Green