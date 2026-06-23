# -*- coding: utf-8 -*-
"""
engine.py — Astra Ducunt 설치기 엔진 (UI 와 분리된 순수 로직)
=============================================================
다운로드 / SHA-256 검증 / 동기화 / Fabric 로더 / 런처 프로파일 /
Modrinth 메타 / 설치 상태 점검 — pywebview UI 와 분리된 설치 로직.
"""

import io
import os
import re
import sys
import ssl
import json
import time
import queue
import shutil
import hashlib
import tempfile
import threading
import subprocess
import webbrowser
import urllib.request
import urllib.parse
from pathlib import Path

REPO_URL = "https://github.com/estraaa47/instantModinstaller"
MANIFEST_URL = "https://raw.githubusercontent.com/estraaa47/instantModinstaller/main/manifest.json"
LAUNCHER_UPDATE_URL = "https://raw.githubusercontent.com/estraaa47/instantModinstaller/main/launcher_version.json"
LAUNCHER_VERSION = "1.0.2"

APP_TITLE = "Astra Ducunt"              # 앱 전체 명칭
APP_TITLEBAR = "Astra Ducunt Launcher"  # 좌상단 타이틀바 표기
PROFILE_ID = "astra-ducunt"             # 런처 프로파일 식별자
PROFILE_NAME = "Astra Ducunt"           # 런처에 보일 프로파일 이름
MANAGED_FOLDERS = ("mods", "shaderpacks")  # 설치(다운로드 배치) 대상 폴더
SYNC_FOLDERS = ("mods",)  # 정리(삭제) 대상 — 셰이더팩은 건드리지 않음(기존 셰이더 보호)
FABRIC_META = "https://meta.fabricmc.net/v2"
MODRINTH_API = "https://api.modrinth.com/v2"
NETWORK_TIMEOUT = 60                     # 초

# HTTPS 강제 + 인증서 검증 유지 (제로 트러스트)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = True
SSL_CONTEXT.verify_mode = ssl.CERT_REQUIRED


# ===========================================================================
#  엔진 (GUI 와 분리된 순수 로직)
# ===========================================================================
class InstallError(Exception):
    """설치 중단을 일으키는 오류."""


def detect_minecraft_dir():
    """OS 별 기본 .minecraft 경로를 추정. 없으면 None."""
    candidates = []
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / ".minecraft")
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library" / "Application Support" / "minecraft")
    else:  # linux 등
        candidates.append(Path.home() / ".minecraft")
    for c in candidates:
        if c.exists():
            return c
    # 존재하지 않아도 가장 그럴듯한 기본값을 돌려준다(폴더 없으면 호출측에서 안내)
    return candidates[0] if candidates else None


def detect_gpu():
    """'nvidia' / 'amd' / 'other' 중 하나를 반환."""
    names = []
    try:
        if sys.platform.startswith("win"):
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_VideoController | "
                 "Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            names = out.stdout.lower().splitlines()
        elif sys.platform == "darwin":
            out = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                                 capture_output=True, text=True, timeout=20)
            names = out.stdout.lower().splitlines()
        else:
            out = subprocess.run(["bash", "-c", "lspci | grep -i vga"],
                                 capture_output=True, text=True, timeout=20)
            names = out.stdout.lower().splitlines()
    except Exception:
        names = []

    blob = " ".join(names)
    if "nvidia" in blob or "geforce" in blob or "rtx" in blob or "gtx" in blob:
        return "nvidia"
    if "amd" in blob or "radeon" in blob:
        return "amd"
    return "other"


def gpu_matches(entry_gpu, machine_gpu):
    """entry 의 gpu 조건이 이 PC 에 맞는지."""
    if entry_gpu is None:
        return True
    return str(entry_gpu).lower() == machine_gpu


def _https_only(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise InstallError(f"HTTPS 가 아닌 주소는 거부됩니다: {url}")
    return parsed


def fetch_bytes(url, log=None, progress=None):
    """HTTPS 로 바이트를 받아서 (data, filename) 반환. 진행률 콜백 지원."""
    _https_only(url)
    req = urllib.request.Request(url, headers={"User-Agent": "AstraDucuntInstaller"})
    with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT, context=SSL_CONTEXT) as resp:
        total = resp.length or 0
        chunks = []
        read = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            chunks.append(chunk)
            read += len(chunk)
            if progress and total:
                progress(read / total)
        data = b"".join(chunks)
    # 파일명: URL 경로의 마지막 조각 (URL 디코드)
    name = urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).name)
    return data, name


def fetch_json(url):
    data, _ = fetch_bytes(url)
    return json.loads(data.decode("utf-8"))


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_key(version):
    parts = [int(p) for p in re.findall(r"\d+", str(version or ""))]
    return tuple(parts or [0])


def is_newer_version(latest, current=LAUNCHER_VERSION):
    left = list(version_key(latest))
    right = list(version_key(current))
    size = max(len(left), len(right))
    left += [0] * (size - len(left))
    right += [0] * (size - len(right))
    return tuple(left) > tuple(right)


def get_launcher_update_info():
    meta = fetch_json(LAUNCHER_UPDATE_URL)
    latest = str(meta.get("version") or "").strip()
    if not latest:
        raise InstallError("launcher_version.json 에 version 이 없습니다.")

    available = is_newer_version(latest)
    url = str(meta.get("url") or "").strip()
    digest = str(meta.get("sha256") or "").strip().lower()

    if available:
        if not url:
            raise InstallError("launcher_version.json 에 업데이트 exe URL 이 없습니다.")
        _https_only(url)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InstallError("launcher_version.json 의 sha256 값이 올바르지 않습니다.")

    return {
        "ok": True,
        "current": LAUNCHER_VERSION,
        "latest": latest,
        "update_available": available,
        "url": url,
        "sha256": digest,
        "notes": meta.get("notes") or "",
    }


def install_launcher_update(info=None, step=None, progress=None):
    if not getattr(sys, "frozen", False):
        raise InstallError("개발 실행 상태에서는 exe 셀프 업데이트를 적용할 수 없습니다.")

    info = info or get_launcher_update_info()
    if not info.get("update_available"):
        raise InstallError("이미 최신 런처입니다.")

    current_exe = Path(sys.executable).resolve()
    update_dir = Path(tempfile.mkdtemp(prefix="astra_launcher_update_"))
    update_exe = update_dir / current_exe.name
    script_path = update_dir / "apply_update.ps1"

    if step:
        step("런처 업데이트 다운로드")
    data, _ = fetch_bytes(info["url"], progress=progress)
    actual = sha256_of(data).lower()
    expected = str(info["sha256"]).lower()
    if actual != expected:
        raise InstallError(
            "런처 업데이트 체크섬이 일치하지 않습니다.\n"
            f"기대: {expected}\n실제: {actual}"
        )
    update_exe.write_bytes(data)

    script = """
param(
  [string]$Src,
  [string]$Dst,
  [int]$Pid
)
$ErrorActionPreference = "Stop"
try {
  Wait-Process -Id $Pid -ErrorAction SilentlyContinue
  Copy-Item -LiteralPath $Src -Destination $Dst -Force
  Start-Process -FilePath $Dst
} finally {
  Remove-Item -LiteralPath $Src -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
}
""".strip()
    script_path.write_text(script, encoding="utf-8")

    if step:
        step("런처 업데이트 적용 준비")
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-Src",
            str(update_exe),
            "-Dst",
            str(current_exe),
            "-Pid",
            str(os.getpid()),
        ],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        close_fds=True,
    )
    return {"ok": True, "version": info["latest"]}


def validate_manifest(manifest):
    """manifest 구조와 보안 요건 검사. 위반 시 InstallError."""
    if not isinstance(manifest, dict):
        raise InstallError("manifest 형식이 올바르지 않습니다.")
    for key in ("minecraft_version", "loader", "entries"):
        if key not in manifest:
            raise InstallError(f"manifest 에 '{key}' 항목이 없습니다.")
    if str(manifest["loader"]).lower() != "fabric":
        raise InstallError("이 설치기는 fabric 로더만 지원합니다.")
    entries = manifest["entries"]
    if not isinstance(entries, list):
        raise InstallError("manifest 의 entries 는 목록이어야 합니다.")
    for i, e in enumerate(entries):
        name = e.get("name", f"#{i}")
        if not e.get("url"):
            raise InstallError(f"[{name}] url 이 없습니다.")
        _https_only(e["url"])                       # HTTPS 강제
        if not e.get("sha256"):                     # 체크섬 필수 (제로 트러스트)
            raise InstallError(f"[{name}] sha256 이 없습니다. 보안상 거부합니다.")
        target = e.get("target")
        if target not in MANAGED_FOLDERS:
            raise InstallError(
                f"[{name}] target 은 {MANAGED_FOLDERS} 중 하나여야 합니다 (got: {target}).")
    return manifest


def entry_filename(entry):
    """entry 에 filename 이 명시돼 있으면 그걸, 아니면 URL 에서 추출."""
    fn = entry.get("filename")
    if fn:
        return fn
    return urllib.parse.unquote(Path(urllib.parse.urlparse(entry["url"]).path).name)


# ---------------------------------------------------------------------------
#  Modrinth 메타데이터 (캐러셀 썸네일/모드 페이지용)
# ---------------------------------------------------------------------------
def modrinth_project_id(url):
    """Modrinth 다운로드 URL 에서 프로젝트 ID 를 추출. (cdn.modrinth.com/data/<ID>/...)"""
    m = re.search(r"modrinth\.com/data/([^/]+)/", url or "")
    return m.group(1) if m else None


def fetch_modrinth_meta(url):
    """Modrinth entry 의 제목/아이콘URL/페이지URL 을 가져온다. 실패 시 None."""
    pid = modrinth_project_id(url)
    if not pid:
        return None
    try:
        data = fetch_json(f"{MODRINTH_API}/project/{pid}")
    except Exception:
        return None
    slug = data.get("slug") or pid
    return {
        "title": data.get("title") or slug,
        "icon_url": data.get("icon_url") or "",
        "page": f"https://modrinth.com/mod/{slug}",
    }


def build_carousel_items(manifest):
    """manifest 의 각 entry 에 대해 슬라이드용 데이터(제목/아이콘바이트/페이지)를 모은다.
    네트워크를 쓰므로 백그라운드 스레드에서 호출할 것."""
    items = []
    for e in manifest.get("entries", []):
        meta = fetch_modrinth_meta(e.get("url"))
        title = (meta and meta["title"]) or e.get("name", "?")
        page = (meta and meta["page"]) or ""
        icon_bytes = None
        if meta and meta.get("icon_url"):
            try:
                icon_bytes, _ = fetch_bytes(meta["icon_url"])
            except Exception:
                icon_bytes = None
        items.append({"title": title, "page": page, "icon": icon_bytes})
    return items


def check_path_writable(mc_dir: Path):
    """경로 존재/쓰기 가능 여부 확인. (ok, message)"""
    try:
        mc_dir = Path(mc_dir)
    except Exception:
        return False, "경로가 올바르지 않습니다."
    if not mc_dir.exists():
        return False, f"경로가 존재하지 않습니다:\n{mc_dir}"
    if not mc_dir.is_dir():
        return False, "선택한 경로가 폴더가 아닙니다."
    # 쓰기 테스트
    try:
        test = mc_dir / ".imi_write_test.tmp"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
    except Exception:
        return False, f"이 폴더에 쓸 권한이 없습니다:\n{mc_dir}"
    return True, "쓰기 가능"


# ---------------------------------------------------------------------------
#  Fabric 로더 설치 (Java 불필요 — Meta API 의 프로파일 JSON 만 써넣음)
# ---------------------------------------------------------------------------
def install_fabric(mc_dir: Path, mc_version: str, loader_version: str | None, log):
    if not loader_version:
        loaders = fetch_json(f"{FABRIC_META}/versions/loader/{mc_version}")
        stable = [l for l in loaders if l.get("loader", {}).get("stable")]
        pick = (stable or loaders)
        if not pick:
            raise InstallError(f"{mc_version} 용 Fabric 로더를 찾지 못했습니다.")
        loader_version = pick[0]["loader"]["version"]

    version_id = f"fabric-loader-{loader_version}-{mc_version}"
    profile_url = f"{FABRIC_META}/versions/loader/{mc_version}/{loader_version}/profile/json"
    log(f"Fabric 로더 프로파일 다운로드: {version_id}")
    profile_json = fetch_json(profile_url)

    vdir = mc_dir / "versions" / version_id
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{version_id}.json").write_text(
        json.dumps(profile_json, indent=2), encoding="utf-8")
    log(f"Fabric 로더 설치 완료: {version_id}")
    return version_id


def _unique_profile_name(profiles, base):
    names = {p.get("name") for p in profiles.values()}
    if base not in names:
        return base
    i = 2
    while f"{base} {i}" in names:
        i += 1
    return f"{base} {i}"


def create_launcher_profile(mc_dir: Path, version_id: str, log,
                            ram_gb=None, new_profile=False):
    """공식 런처의 launcher_profiles.json 에 프로파일 추가.
    ram_gb: 지정 시 -Xmx{N}G 자바 인자 설정.
    new_profile: True=항상 새 프로파일(고유 id), False=기존 astra-ducunt 덮어쓰기."""
    lp = mc_dir / "launcher_profiles.json"
    data = {"profiles": {}, "version": 3}
    if lp.exists():
        try:
            data = json.loads(lp.read_text(encoding="utf-8"))
        except Exception:
            log("기존 launcher_profiles.json 을 읽을 수 없어 새로 만듭니다.")
            data = {"profiles": {}, "version": 3}
    profiles = data.setdefault("profiles", {})
    now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    if new_profile and PROFILE_ID in profiles:
        pid = f"{PROFILE_ID}-{int(time.time())}"
        name = _unique_profile_name(profiles, PROFILE_NAME)
        created = now
    else:
        pid = PROFILE_ID
        name = PROFILE_NAME
        created = profiles.get(PROFILE_ID, {}).get("created", now)

    entry = {
        "name": name,
        "type": "custom",
        "created": created,
        "lastUsed": now,
        "lastVersionId": version_id,
        "icon": "Furnace",
    }
    if ram_gb:
        try:
            entry["javaArgs"] = f"-Xmx{int(ram_gb)}G"
        except (TypeError, ValueError):
            pass
    profiles[pid] = entry
    lp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log(f"런처 프로파일 {'생성' if new_profile else '갱신'}: {name}"
        + (f" (RAM {int(ram_gb)}G)" if ram_gb else ""))


def launch_minecraft_launcher():
    """공식 마인크래프트 런처를 실행한다. (독립형 exe → MS Store UWP 순). 성공 여부 반환."""
    # 1) 독립형(클래식) 런처 exe
    for env in ("ProgramFiles(x86)", "ProgramW6432", "ProgramFiles"):
        base = os.environ.get(env)
        if not base:
            continue
        exe = Path(base) / "Minecraft Launcher" / "MinecraftLauncher.exe"
        try:
            if exe.exists():
                os.startfile(str(exe))  # noqa: P204 (Windows 전용)
                return True
        except Exception:
            pass
    # 2) MS Store(UWP) 런처 — AppsFolder AUMID 로 실행
    if sys.platform == "win32":
        try:
            subprocess.Popen(
                ["explorer.exe",
                 r"shell:AppsFolder\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft"])
            return True
        except Exception:
            pass
    return False


def sync_folder(folder: Path, expected_names: set, log):
    """manifest 에 없는 파일을 관리 폴더에서 삭제."""
    if not folder.exists():
        return
    for child in folder.iterdir():
        if child.is_file() and child.name not in expected_names:
            log(f"동기화: 불필요한 파일 삭제 → {child.name}")
            try:
                child.unlink()
            except Exception as ex:
                log(f"  (삭제 실패: {ex})")


def expected_entries_for_machine(manifest, machine_gpu=None):
    """현재 PC 조건에 맞춰 실제 설치 대상 entry 만 추린다."""
    if machine_gpu is None:
        machine_gpu = detect_gpu()
    entries = manifest.get("entries", [])
    return [e for e in entries if gpu_matches(e.get("gpu"), machine_gpu)], machine_gpu


def expected_files_by_target(entries):
    expected = {f: set() for f in MANAGED_FOLDERS}
    for e in entries:
        expected[e["target"]].add(entry_filename(e))
    return expected


def fabric_version_prefix(manifest):
    mc_version = manifest.get("minecraft_version", "")
    loader_version = manifest.get("loader_version")
    if loader_version:
        return f"fabric-loader-{loader_version}-{mc_version}"
    return f"fabric-loader-", f"-{mc_version}"


def has_fabric_profile(mc_dir: Path, manifest):
    mc_dir = Path(mc_dir)
    versions = mc_dir / "versions"
    if not versions.exists():
        return False

    marker = fabric_version_prefix(manifest)
    if isinstance(marker, tuple):
        prefix, suffix = marker
        found_version = any(
            child.is_dir()
            and child.name.startswith(prefix)
            and child.name.endswith(suffix)
            and (child / f"{child.name}.json").exists()
            for child in versions.iterdir()
        )
    else:
        found_version = (
            (versions / marker).is_dir()
            and (versions / marker / f"{marker}.json").exists()
        )
    if not found_version:
        return False

    lp = mc_dir / "launcher_profiles.json"
    if not lp.exists():
        return False
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
        profile = data.get("profiles", {}).get(PROFILE_ID)
    except Exception:
        return False
    return bool(profile and profile.get("lastVersionId", "").startswith("fabric-loader-"))


def inspect_install_state(mc_dir: Path, manifest, include_shaders=True):
    """manifest 기준으로 현재 설치 상태를 확인한다."""
    mc_dir = Path(mc_dir)
    ok, msg = check_path_writable(mc_dir)
    if not ok:
        return {
            "status": "path_error",
            "message": msg,
            "missing": [],
            "changed": [],
            "extra": [],
            "total": 0,
            "gpu": "unknown",
        }

    to_install, gpu = expected_entries_for_machine(manifest)
    if not include_shaders:
        to_install = [e for e in to_install if e.get("target") != "shaderpacks"]
    expected = expected_files_by_target(to_install)
    missing = []
    changed = []
    extra = []
    fabric_ready = has_fabric_profile(mc_dir, manifest)

    for e in to_install:
        fn = entry_filename(e)
        path = mc_dir / e["target"] / fn
        label = f"{e['target']}/{fn}"
        if not path.exists():
            missing.append(label)
            continue
        if not path.is_file():
            changed.append(label)
            continue
        try:
            actual = sha256_of(path.read_bytes())
        except Exception:
            changed.append(label)
            continue
        if actual.lower() != str(e["sha256"]).lower():
            changed.append(label)

    if to_install:
        for target in SYNC_FOLDERS:
            folder = mc_dir / target
            if not folder.exists():
                continue
            for child in folder.iterdir():
                if child.is_file() and child.name not in expected[target]:
                    extra.append(f"{target}/{child.name}")

    all_missing = (len(missing) == len(to_install))
    if not fabric_ready and all_missing:
        # 우리 팩(Fabric 프로파일 + 우리 모드)이 전혀 없음 → 첫 설치 상태.
        # 폴더에 무관한 다른 모드(extra)가 있어도 '설치'로 본다.
        status = "not_installed"
    elif fabric_ready and not missing and not changed and not extra:
        status = "current"
    else:
        status = "update_available"

    return {
        "status": status,
        "message": "",
        "missing": missing,
        "changed": changed,
        "extra": extra,
        "total": len(to_install),
        "gpu": gpu,
    }


def run_install(mc_dir: Path, manifest_url, log, step, progress, options=None):
    """
    전체 설치 파이프라인.
      options: {"shaders":bool, "ram":int(GB), "new_profile":bool}
    실패 시 InstallError 를 던진다.
    """
    options = options or {}
    want_shaders = options.get("shaders", True)
    ram_gb = options.get("ram")
    new_profile = bool(options.get("new_profile", False))
    mc_dir = Path(mc_dir)

    step("경로 확인")
    ok, msg = check_path_writable(mc_dir)
    if not ok:
        raise InstallError(msg)
    log(f"마인크래프트 경로: {mc_dir}")

    step("manifest 읽기")
    log(f"manifest 다운로드: {manifest_url}")
    manifest = fetch_json(manifest_url)
    validate_manifest(manifest)
    mc_version = manifest["minecraft_version"]
    loader_version = manifest.get("loader_version")  # 없으면 최신 stable
    entries = manifest["entries"]
    log(f"버전 {mc_version} / 로더 fabric / 모드 {len(entries)}개")

    step("GPU 감지")
    gpu = detect_gpu()
    log(f"이 PC 의 GPU: {gpu}")

    # 이 PC 에 실제로 설치할 entry 만 추림
    to_install, _ = expected_entries_for_machine(manifest, gpu)
    if not want_shaders:
        before = len(to_install)
        to_install = [e for e in to_install if e.get("target") != "shaderpacks"]
        if before != len(to_install):
            log(f"셰이더 설치 꺼짐 → 셰이더 {before - len(to_install)}개 제외")
    log(f"이 PC 에 설치할 항목: {len(to_install)}개 "
        f"(GPU 조건으로 {len(entries) - len(to_install)}개 제외)")

    # 동기화 기준: 폴더별 기대 파일 집합
    expected = expected_files_by_target(to_install)

    tmpdir = Path(tempfile.mkdtemp(prefix="imi_"))
    staged = []  # (data_path, target_folder, filename)
    try:
        if to_install:
            step("다운로드 및 검증")
            for idx, e in enumerate(to_install, 1):
                name = e.get("name", entry_filename(e))
                log(f"[{idx}/{len(to_install)}] 다운로드: {name}")
                base = idx - 1

                def p(frac, _base=base):
                    progress((_base + frac) / max(len(to_install), 1))

                data, _fn = fetch_bytes(e["url"], log=log, progress=p)
                actual = sha256_of(data)
                if actual.lower() != str(e["sha256"]).lower():
                    # 불일치 → 파일 폐기 + 전체 중단 (fail-safe)
                    raise InstallError(
                        f"[{name}] 체크섬 불일치!\n"
                        f"  기대: {e['sha256']}\n  실제: {actual}\n"
                        f"파일을 폐기하고 설치를 중단합니다.")
                log(f"    SHA-256 검증 통과")
                fn = entry_filename(e)
                stage_path = tmpdir / f"{idx}_{fn}"
                stage_path.write_bytes(data)
                staged.append((stage_path, e["target"], fn))
                progress(idx / max(len(to_install), 1))

            # 모두 검증된 뒤에야 실제 폴더에 반영 (원자성 ↑)
            step("설치")
            for target in MANAGED_FOLDERS:
                (mc_dir / target).mkdir(parents=True, exist_ok=True)
            for stage_path, target, fn in staged:
                dest = mc_dir / target / fn
                if dest.exists():
                    dest.unlink()
                shutil.move(str(stage_path), str(dest))
                log(f"설치: {target}/{fn}")

            step("동기화")
            for target in SYNC_FOLDERS:
                sync_folder(mc_dir / target, expected[target], log)
        else:
            log("설치할 모드가 없어 Fabric 로더만 설치합니다.")

        step("Fabric 로더 설치")
        version_id = install_fabric(mc_dir, mc_version, loader_version, log)

        step("런처 프로파일 생성")
        create_launcher_profile(mc_dir, version_id, log,
                                ram_gb=ram_gb, new_profile=new_profile)

        progress(1.0)
        step("완료")
        log("✅ 모든 설치가 완료되었습니다. 공식 런처에서 "
            f"'{PROFILE_NAME}' 프로파일을 선택해 실행하세요.")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
