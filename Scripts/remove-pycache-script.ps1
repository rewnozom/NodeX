# Använd den aktuella mappen som startpunkt
$startPath = ".\"

# Hitta alla __pycache__ mappar
$pycacheFolders = Get-ChildItem -Path $startPath -Filter "__pycache__" -Directory -Recurse

# Loopa igenom varje hittad mapp och ta bort den
foreach ($folder in $pycacheFolders) {
    try {
        Remove-Item -Path $folder.FullName -Recurse -Force
        Write-Host "Borttagen: $($folder.FullName)"
    }
    catch {
        Write-Host "Kunde inte ta bort: $($folder.FullName). Fel: $_"
    }
}

Write-Host "Klart! Alla __pycache__ mappar har tagits bort."