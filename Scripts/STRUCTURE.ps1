# Get current directory path
$currentPath = Get-Location

function Get-FileIcon {
    param (
        [string]$Extension
    )
    
    $icons = @{
        # Web Development
        '.html'     = '🌐'
        '.htm'      = '🌐'
        '.css'      = '🎨'
        '.scss'     = '🎨'
        '.sass'     = '🎨'
        '.less'     = '🎨'
        '.js'       = '📜'
        '.jsx'      = '⚛️'
        '.ts'       = '📘'
        '.tsx'      = '⚛️'
        '.vue'      = '💚'
        '.svelte'   = '🔥'

        # Backend & Programming
        '.py'       = '🐍'
        '.java'     = '☕'
        '.class'    = '☕'
        '.rb'       = '💎'
        '.php'      = '🐘'
        '.cs'       = '#️⃣'
        '.cpp'      = '⚙️'
        '.c'        = '⚙️'
        '.go'       = '🐹'
        '.rs'       = '🦀'
        '.swift'    = '🕊️'
        '.kt'       = '📱'

        # Data & Config
        '.json'     = '📋'
        '.yaml'     = '⚙️'
        '.yml'      = '⚙️'
        '.xml'      = '📰'
        '.csv'      = '📊'
        '.sql'      = '🗄️'
        '.db'       = '🗄️'
        '.env'      = '🔒'
        '.toml'     = '⚙️'
        '.ini'      = '⚙️'
        '.config'   = '⚙️'
        '.lock'     = '🔒'

        # Documentation
        '.md'       = '📝'
        '.mdx'      = '📝'
        '.txt'      = '📄'
        '.pdf'      = '📕'
        '.doc'      = '📘'
        '.docx'     = '📘'
        '.xls'      = '📗'
        '.xlsx'     = '📗'

        # Images & Media
        '.jpg'      = '🖼️'
        '.jpeg'     = '🖼️'
        '.png'      = '🖼️'
        '.gif'      = '🖼️'
        '.svg'      = '🎨'
        '.ico'      = '🖼️'
        '.mp4'      = '🎥'
        '.mp3'      = '🎵'
        '.wav'      = '🎵'

        # Development Tools
        '.git'      = '📦'
        '.gitignore' = '👁️'
        '.dockerignore' = '🐳'
        '.dockerfile' = '🐳'
        '.eslintrc'  = '🔍'
        '.prettierrc' = '✨'
        '.babelrc'   = '🔧'
        '.npmrc'     = '📦'
        '.nvmrc'     = '📦'
    }

    $ext = [System.IO.Path]::GetExtension($Extension).ToLower()
    if ($icons.ContainsKey($ext)) {
        return $icons[$ext]
    }
    return '📄'
}

function Get-DirectoryTree {
    param (
        [string]$Path = $currentPath,
        [int]$IndentLevel = 0,
        [string[]]$ExcludeDirs = @(
            "venv", "__pycache__", "node_modules", ".git", 
            "bin", "obj", "build", "dist", "coverage",
            ".next", ".nuxt", ".output", ".cache",
            "target", "out", ".idea", ".vscode"
        ),
        [string[]]$ExcludeFiles = @(
            ".DS_Store", "*.pyc", "*.pyo", "*.pyd",
            ".env.local", ".env.*.local",
            "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*",
            "*.log", "*.swp", "*.swo",
            ".eslintcache", ".tsbuildinfo"
        )
    )

    if ($IndentLevel -eq 0) {
        Write-Output "`n📁 $(Split-Path $Path -Leaf)"
    }

    $items = Get-ChildItem -Path $Path

    foreach ($item in $items) {
        $shouldSkip = $false
        
        if ($item.PSIsContainer) {
            if ($ExcludeDirs -contains $item.Name) {
                $shouldSkip = $true
            }
        } else {
            foreach ($pattern in $ExcludeFiles) {
                if ($item.Name -like $pattern) {
                    $shouldSkip = $true
                    break
                }
            }
        }

        if ($shouldSkip) { continue }

        $indent = "    " * $IndentLevel

        if ($item.PSIsContainer) {
            Write-Output "$indent├── 📁 $($item.Name)"
            Get-DirectoryTree -Path $item.FullName -IndentLevel ($IndentLevel + 1) -ExcludeDirs $ExcludeDirs -ExcludeFiles $ExcludeFiles
        } else {
            $icon = Get-FileIcon -Extension $item.Name
            Write-Output "$indent├── $icon $($item.Name)"
        }
    }
}

# Run the function immediately for current directory
Get-DirectoryTree