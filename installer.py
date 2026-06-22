# -*- coding: utf-8 -*-
"""
Instant Mod Installer  (간편 모드 설치기 / 엔진)
==================================================
이 프로그램은 '엔진'입니다. 모드 이름/버전/주소를 하드코딩하지 않습니다.
모든 모드 정보는 GitHub에 올린 manifest.json 에서 읽어옵니다.

  - 모드를 바꾸려면 manifest.json 만 수정해서 GitHub에 push 하세요.
  - 친구는 항상 같은 exe 를 다시 실행하면 됩니다.

표준 라이브러리만 사용 (tkinter, ssl, hashlib, urllib, json) → 추가 설치 불필요.
"""

import os
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
import urllib.request
import urllib.parse
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ===========================================================================
#  설정 — 당신이 바꾸는 곳은 여기 한 줄뿐입니다.
# ===========================================================================
# 당신의 GitHub 저장소에 올린 manifest.json 의 RAW URL 로 바꾸세요.
# 예: https://raw.githubusercontent.com/<깃허브아이디>/<저장소이름>/main/manifest.json
MANIFEST_URL = "https://raw.githubusercontent.com/USER/REPO/main/manifest.json"

APP_TITLE = "간편 모드 설치기"
PROFILE_ID = "instant-modpack"          # 런처 프로파일 식별자
PROFILE_NAME = "Instant Modpack"        # 런처에 보일 프로파일 이름
MANAGED_FOLDERS = ("mods", "shaderpacks")  # 동기화로 관리하는 폴더
FABRIC_META = "https://meta.fabricmc.net/v2"
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
    req = urllib.request.Request(url, headers={"User-Agent": "InstantModInstaller"})
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
    if not isinstance(entries, list) or not entries:
        raise InstallError("manifest 에 설치할 모드(entries)가 없습니다.")
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


def create_launcher_profile(mc_dir: Path, version_id: str, log):
    """공식 런처의 launcher_profiles.json 에 프로파일 추가."""
    lp = mc_dir / "launcher_profiles.json"
    data = {"profiles": {}, "version": 3}
    if lp.exists():
        try:
            data = json.loads(lp.read_text(encoding="utf-8"))
        except Exception:
            log("기존 launcher_profiles.json 을 읽을 수 없어 새로 만듭니다.")
            data = {"profiles": {}, "version": 3}
    data.setdefault("profiles", {})
    now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    existing = data["profiles"].get(PROFILE_ID, {})
    data["profiles"][PROFILE_ID] = {
        "name": PROFILE_NAME,
        "type": "custom",
        "created": existing.get("created", now),
        "lastUsed": now,
        "lastVersionId": version_id,
        "icon": "Furnace",
    }
    lp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log(f"런처 프로파일 생성/갱신: {PROFILE_NAME}")


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


def run_install(mc_dir: Path, manifest_url, log, step, progress):
    """
    전체 설치 파이프라인.
      log(str)        : 로그 한 줄 추가
      step(str)       : 현재 단계 이름 표시
      progress(float) : 0.0~1.0 진행률
    실패 시 InstallError 를 던진다.
    """
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
    log(f"마크 버전 {mc_version} / 로더 fabric / 모드 {len(entries)}개")

    step("GPU 감지")
    gpu = detect_gpu()
    log(f"이 PC 의 GPU: {gpu}")

    # 이 PC 에 실제로 설치할 entry 만 추림
    to_install = [e for e in entries if gpu_matches(e.get("gpu"), gpu)]
    log(f"이 PC 에 설치할 항목: {len(to_install)}개 "
        f"(GPU 조건으로 {len(entries) - len(to_install)}개 제외)")

    # 동기화 기준: 폴더별 기대 파일 집합
    expected = {f: set() for f in MANAGED_FOLDERS}
    for e in to_install:
        expected[e["target"]].add(entry_filename(e))

    step("다운로드 및 검증")
    tmpdir = Path(tempfile.mkdtemp(prefix="imi_"))
    staged = []  # (data_path, target_folder, filename)
    try:
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
            shutil.move(str(stage_path), str(dest))
            log(f"설치: {target}/{fn}")

        step("동기화")
        for target in MANAGED_FOLDERS:
            sync_folder(mc_dir / target, expected[target], log)

        step("Fabric 로더 설치")
        version_id = install_fabric(mc_dir, mc_version, loader_version, log)

        step("런처 프로파일 생성")
        create_launcher_profile(mc_dir, version_id, log)

        progress(1.0)
        step("완료")
        log("✅ 모든 설치가 완료되었습니다. 공식 런처에서 "
            f"'{PROFILE_NAME}' 프로파일을 선택해 실행하세요.")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
#  GUI (tkinter)
# ===========================================================================
class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("640x560")
        self.minsize(560, 480)
        self.msg_queue = queue.Queue()
        self.worker = None
        self.manifest_cache = None

        self._build_widgets()
        self._autodetect_path()
        self.after(100, self._drain_queue)

    # ---- UI 구성 ----
    def _build_widgets(self):
        pad = {"padx": 10, "pady": 4}

        head = ttk.Label(self, text=APP_TITLE, font=("", 15, "bold"))
        head.pack(anchor="w", padx=10, pady=(10, 0))
        ttk.Label(self, text="마인크래프트 경로를 확인하고 [설치] 를 누르세요.",
                  foreground="#555").pack(anchor="w", padx=10)

        # 경로 줄
        pf = ttk.Frame(self)
        pf.pack(fill="x", **pad)
        ttk.Label(pf, text="마인크래프트 경로:").pack(side="left")
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(pf, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(pf, text="찾아보기…", command=self._browse).pack(side="left")

        # 미리보기 줄
        prev_head = ttk.Frame(self)
        prev_head.pack(fill="x", padx=10)
        ttk.Label(prev_head, text="설치될 모드 미리보기:").pack(side="left")
        ttk.Button(prev_head, text="목록 새로고침",
                   command=self._load_preview).pack(side="right")

        self.preview = tk.Listbox(self, height=8)
        self.preview.pack(fill="both", expand=False, padx=10, pady=4)

        # 진행률
        self.step_var = tk.StringVar(value="대기 중")
        ttk.Label(self, textvariable=self.step_var).pack(anchor="w", padx=10)
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=1.0)
        self.progress.pack(fill="x", padx=10, pady=4)

        # 로그
        self.log_box = tk.Text(self, height=9, state="disabled", wrap="word",
                               font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=4)

        # 버튼 줄
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=10, pady=(0, 10))
        self.install_btn = ttk.Button(bf, text="설치", command=self._on_install)
        self.install_btn.pack(side="right")
        ttk.Button(bf, text="닫기", command=self._on_close).pack(side="right", padx=6)

    # ---- 동작 ----
    def _autodetect_path(self):
        d = detect_minecraft_dir()
        if d and Path(d).exists():
            self.path_var.set(str(d))
            self._log(f"마인크래프트 경로 자동 감지: {d}")
            self._load_preview()
        else:
            self.path_var.set("")
            self._log("마인크래프트 경로를 자동으로 찾지 못했습니다. "
                      "[찾아보기]로 .minecraft 폴더를 직접 지정하세요.")

    def _browse(self):
        start = self.path_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(initialdir=start,
                                         title=".minecraft 폴더 선택")
        if chosen:
            self.path_var.set(chosen)

    def _load_preview(self):
        self.preview.delete(0, tk.END)
        self.preview.insert(tk.END, "manifest 불러오는 중…")
        threading.Thread(target=self._load_preview_worker, daemon=True).start()

    def _load_preview_worker(self):
        try:
            manifest = fetch_json(MANIFEST_URL)
            validate_manifest(manifest)
            self.manifest_cache = manifest
            self.msg_queue.put(("preview", manifest))
        except Exception as ex:
            self.msg_queue.put(("preview_err", str(ex)))

    def _on_install(self):
        if self.worker and self.worker.is_alive():
            return
        mc_dir = self.path_var.get().strip()
        if not mc_dir:
            messagebox.showwarning(APP_TITLE, "마인크래프트 경로를 먼저 지정하세요.")
            return
        ok, msg = check_path_writable(Path(mc_dir))
        if not ok:
            messagebox.showerror(APP_TITLE, msg)
            return
        if not messagebox.askokcancel(
                APP_TITLE,
                f"다음 경로에 설치합니다:\n{mc_dir}\n\n"
                "mods / shaderpacks 폴더가 manifest 기준으로 동기화됩니다.\n계속할까요?"):
            return

        self.install_btn.config(state="disabled")
        self.progress["value"] = 0
        self.worker = threading.Thread(
            target=self._install_worker, args=(mc_dir,), daemon=True)
        self.worker.start()

    def _install_worker(self, mc_dir):
        def log(m):
            self.msg_queue.put(("log", m))

        def step(m):
            self.msg_queue.put(("step", m))

        def progress(f):
            self.msg_queue.put(("progress", f))

        try:
            run_install(mc_dir, MANIFEST_URL, log, step, progress)
            self.msg_queue.put(("done", None))
        except InstallError as ex:
            self.msg_queue.put(("fail", str(ex)))
        except Exception as ex:
            self.msg_queue.put(("fail", f"예상치 못한 오류: {ex}"))

    # ---- 큐 처리 (워커 → GUI 스레드) ----
    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "step":
                    self.step_var.set(f"단계: {payload}")
                elif kind == "progress":
                    self.progress["value"] = payload
                elif kind == "preview":
                    self._render_preview(payload)
                elif kind == "preview_err":
                    self.preview.delete(0, tk.END)
                    self.preview.insert(tk.END, f"manifest 오류: {payload}")
                elif kind == "done":
                    self.install_btn.config(state="normal")
                    self.step_var.set("단계: 완료 ✅")
                    messagebox.showinfo(APP_TITLE, "설치가 완료되었습니다!\n"
                                        f"공식 런처에서 '{PROFILE_NAME}' 프로파일을 실행하세요.")
                elif kind == "fail":
                    self.install_btn.config(state="normal")
                    self.step_var.set("단계: 실패 ❌")
                    self._log("❌ " + payload)
                    messagebox.showerror(APP_TITLE, "설치 실패:\n\n" + payload)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _render_preview(self, manifest):
        self.preview.delete(0, tk.END)
        mv = manifest.get("minecraft_version", "?")
        self.preview.insert(tk.END, f"[마크 {mv} / fabric] 모드 {len(manifest['entries'])}개")
        for e in manifest["entries"]:
            gpu = e.get("gpu")
            tag = f" (GPU: {gpu})" if gpu else ""
            self.preview.insert(tk.END, f"  • {e.get('name','?')} → {e.get('target')}{tag}")

    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def _on_close(self):
        if self.worker and self.worker.is_alive():
            if not messagebox.askokcancel(APP_TITLE, "설치가 진행 중입니다. 정말 닫을까요?"):
                return
        self.destroy()


def main():
    if "USER/REPO" in MANIFEST_URL:
        # 배포 전 설정 누락 방지용 안내 (친구에게 가기 전 당신이 보게 됨)
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            APP_TITLE,
            "MANIFEST_URL 이 아직 설정되지 않았습니다.\n"
            "installer.py 상단의 MANIFEST_URL 을 당신의 GitHub raw 주소로 바꾼 뒤 "
            "다시 빌드하세요.")
        root.destroy()
    app = InstallerGUI()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
