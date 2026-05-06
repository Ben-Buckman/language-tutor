# start_expo.ps1 — run this after start_dev.ps1 in a separate terminal
Set-Location "$PSScriptRoot\mobile"
npx expo start --tunnel
