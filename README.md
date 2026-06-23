# Astra Ducunt

Minecraft Fabric modpack installer and launcher helper for Astra Ducunt.

The desktop app is a Python + pywebview launcher. The UI lives in `web/`, while the install and update logic lives in `engine.py`.

## Current Structure

- `app.py`: pywebview entry point and JavaScript bridge
- `engine.py`: Minecraft path detection, Fabric profile install, mod download, hash check, profile update, launcher self-update logic
- `web/`: HTML/CSS/JS UI and runtime assets
- `manifest.json`: modpack manifest fetched by the launcher
- `launcher_version.json`: launcher self-update metadata
- `AstraDucunt-web.spec`: active PyInstaller spec
- `build_exe.bat`: builds `dist\Astra Ducunt.exe`

Legacy tkinter installer files have been removed. The webview launcher is the main app.

## Modpack Updates

For mod changes, update `manifest.json` and push it to GitHub. The launcher reads:

```text
https://raw.githubusercontent.com/estraaa47/instantModinstaller/main/manifest.json
```

Each entry should use a direct HTTPS download URL without tracking query parameters.

Required fields:

```json
{
  "name": "Fabric API",
  "url": "https://cdn.modrinth.com/data/.../fabric-api.jar",
  "sha256": "...",
  "target": "mods"
}
```

Then fill or refresh hashes:

```powershell
python update_hashes.py --fill manifest.json
```

Use `--force` when you want to recalculate existing hashes.

## Building

```powershell
.\build_exe.bat
```

Output:

```text
dist\Astra Ducunt.exe
```

Do not commit `dist/`, `build/`, or `.exe` files to the repository. Publish the exe through GitHub Releases when needed.

## Launcher Self-Update

The launcher checks:

```text
https://raw.githubusercontent.com/estraaa47/instantModinstaller/main/launcher_version.json
```

When releasing a new exe:

1. Build `dist\Astra Ducunt.exe`.
2. Upload the exe to GitHub Releases.
3. Calculate its SHA-256.
4. Update `launcher_version.json`:

```json
{
  "version": "1.0.1",
  "url": "https://github.com/estraaa47/instantModinstaller/releases/download/v1.0.1/Astra.Ducunt.exe",
  "sha256": "...",
  "notes": ""
}
```

5. Commit and push `launcher_version.json`.

## Install Behavior

The installer:

- Detects the default `.minecraft` path.
- Installs or updates the Fabric launcher profile for Minecraft `1.21.11`.
- Downloads required mod files into `mods`.
- Verifies every downloaded file with SHA-256.
- Applies RAM/profile options again when reinstalling.
- Leaves build artifacts and local diagnostics out of Git via `.gitignore`.
