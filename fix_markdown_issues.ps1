# Fix line length and indentation in Markdown files
$files = Get-ChildItem -Path . -Recurse -Include *.md | Where-Object { $_.FullName -notlike '*\node_modules\*' }

foreach ($file in $files) {
    $content = Get-Content -Path $file.FullName -Raw
    
    # Fix line length (MD013)
    $lines = $content -split "`r?`n"
    $newContent = @()
    
    foreach ($line in $lines) {
        # Skip code blocks
        if ($line -match '^\s*```') { 
            $newContent += $line
            continue 
        }
        
        # Fix line length
        if ($line.Length -gt 120) {
            $words = $line -split ' '
            $newLine = ""
            foreach ($word in $words) {
                if (($newLine + " " + $word).Length -gt 120) {
                    $newContent += $newLine.Trim()
                    $newLine = "  $word"  # Add two spaces for markdown line break
                } else {
                    $newLine += " $word"
                }
            }
            $newContent += $newLine.Trim()
        } else {
            $newContent += $line
        }
    }
    
    # Fix list indentation (MD005)
    $content = $newContent -join "`n"
    $content = $content -replace '(?m)^(\s*)-\s+\*\*', '$1  - **'  # Fix bold list items
    $content = $content -replace '(?m)^(\s{6,})\*', '$1  *'        # Fix nested list indentation
    
    # Save the file
    Set-Content -Path $file.FullName -Value $content -NoNewline
}

Write-Host "Markdown files have been formatted successfully."
