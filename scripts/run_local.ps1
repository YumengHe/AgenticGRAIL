param([ValidateSet('viewer','mesh','scene','render','encode')][string]$Step='viewer')
$ErrorActionPreference='Stop'
$projectPath=Split-Path -Parent $PSScriptRoot
$pythonPath='C:/Users/envora/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$blenderPath='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$pnpmPath='C:/Users/envora/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd'
Push-Location $projectPath
try {
 switch($Step){
  'viewer' { & $pythonPath scripts/sync_web.py; Push-Location web; try { & $pnpmPath dev } finally {Pop-Location} }
  'mesh' { & $pythonPath scripts/meshy_pipeline.py }
  'scene' { & $blenderPath -b --python scripts/build_scene.py -- --preview }
  'render' { & $blenderPath -b output/taichi_scene.blend --python scripts/render_frames.py }
  'encode' { & $pythonPath scripts/encode_video.py; & $pythonPath scripts/sync_web.py }
 }
} finally { Pop-Location }
