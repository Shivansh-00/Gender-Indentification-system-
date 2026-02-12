
$ErrorActionPreference = "Stop"

function Fix-File {
    param (
        [string]$Path,
        [string]$Marker,
        [string]$AppendPath
    )

    Write-Host "Fixing $Path..."
    
    if (-not (Test-Path $Path)) {
        Write-Error "File not found: $Path"
        return
    }

    try {
        # Read file content as string first to find the marker position
        # We use a permissive encoding or try to read safely
        # Actually, reading as raw bytes is safest to avoid decoding errors on bad data
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        $text = [System.Text.Encoding]::UTF8.GetString($bytes)
        
        $idx = $text.LastIndexOf($Marker)
        
        if ($idx -ge 0) {
            $endPos = $idx + $Marker.Length
            
            # Truncate
            $cleanText = $text.Substring(0, $endPos) + "`r`n`r`n"
            
            # Read clean append content
            if (Test-Path $AppendPath) {
                # Read append file (assume valid UTF8)
                $appendBytes = [System.IO.File]::ReadAllBytes($AppendPath)
                $appendText = [System.Text.Encoding]::UTF8.GetString($appendBytes)
                
                $finalText = $cleanText + $appendText
                
                # Write back
                [System.IO.File]::WriteAllText($Path, $finalText, [System.Text.Encoding]::UTF8)
                Write-Host "Successfully fixed $Path"
            } else {
                Write-Error "Append file not found: $AppendPath"
            }
        } else {
            Write-Error "Marker '$Marker' not found in $Path"
        }
    } catch {
        Write-Error "Failed to fix $Path : $_"
    }
}

# Fix utils.py
Fix-File -Path "utils.py" -Marker "return teams" -AppendPath "C:\Users\rajve\Desktop\SkillIssues\TeamBalancer.py"

# Fix glasstry.py
# Marker is 'elif st.session_state.page == "view_folders": view_folders()'
# NOTE: Need to be careful with quotes in PowerShell string
$marker = 'elif st.session_state.page == "view_folders": view_folders()'
Fix-File -Path "glasstry.py" -Marker $marker -AppendPath "C:\Users\rajve\Desktop\SkillIssues\TeamUI.py"
