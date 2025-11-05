# Fix line length in all markdown files
Get-ChildItem -Path . -Recurse -Include *.md | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    # Split long lines
    $content = $content -replace '(.{1,120})(\s|$)', '$1$2' + [Environment]::NewLine
    Set-Content -Path $_.FullName -Value $content -NoNewline
}

# Fix heading styles and multiple H1s
Get-ChildItem -Path . -Recurse -Include *.md | ForEach-Object {
    $content = Get-Content -Path $_.FullName
    $h1Count = 0
    $newContent = @()
    
    foreach ($line in $content) {
        # Convert setext-style headings to ATX
        if ($line -match '^(.+?)\r?\n(?:=+|-+)\s*$') {
            $heading = $matches[1].Trim()
            $level = if ($line -match '^=+$') { '#' } else { '##' }
            $newContent += "$level $heading"
        }
        # Convert multiple H1s to H2
        elseif ($line -match '^#\s') {
            $h1Count++
            if ($h1Count -gt 1) {
                $newContent += $line -replace '^#', '##'
            } else {
                $newContent += $line
            }
        }
        else {
            $newContent += $line
        }
    }
    
    Set-Content -Path $_.FullName -Value $newContent
}

# Remove any merge conflict markers
Get-ChildItem -Path . -Recurse -Include *.md | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    $content = $content -replace '(?m)^<<<<<<<.*?$' -replace '(?m)^=======.*?$' -replace '(?m)^>>>>>>>.*?$'
    Set-Content -Path $_.FullName -Value $content -NoNewline
}

Write-Host "Markdown files have been formatted successfully."
