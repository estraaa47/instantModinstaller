# -*- coding: utf-8 -*-
"""
app.py — Astra Ducunt Launcher (pywebview UI 진입점)
====================================================
화면은 web/ (HTML/CSS/JS), 로직은 engine.py.
무거운 작업(네트워크/검증)은 백그라운드 스레드에서 처리하고 결과만 JS 로 푸시 →
GUI 스레드가 절대 멈추지 않음(응답없음 방지).
"""

import os
import sys
import json
import base64
import time
import threading
from pathlib import Path

import webview

import engine


def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _data_url(raw: bytes) -> str:
    if not raw:
        return ""
    sig = raw[:12]
    if sig[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif sig[:4] == b"RIFF" and sig[8:12] == b"WEBP":
        mime = "image/webp"
    elif sig[:2] == b"\xff\xd8":
        mime = "image/jpeg"
    elif sig[:4] == b"GIF8":
        mime = "image/gif"
    else:
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def _basic_carousel_items(manifest):
    items = []
    for entry in (manifest or {}).get("entries", []):
        title = entry.get("name") or "?"
        items.append({"title": title, "page": "", "icon": ""})
    return items


class Api:
    """JS ↔ Python 브릿지. 무거운 메서드는 즉시 반환 + 백그라운드에서 JS 로 푸시."""

    def __init__(self):
        self._window = None
        self._manifest = None
        self._installing = False
        self._launcher_updating = False

    def _js(self, fn, *args):
        if not self._window:
            return
        try:
            self._window.evaluate_js(
                f"window.{fn} && window.{fn}.apply(null,"
                f"{json.dumps(args, ensure_ascii=False)})")
        except Exception:
            pass

    # ---- 즉시 반환되는 가벼운 호출 ----
    def minimize(self):
        if self._window:
            self._window.minimize()

    def close(self):
        if self._window:
            self._window.destroy()

    def open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        return True

    def play(self):
        return bool(engine.launch_minecraft_launcher())

    def github_url(self):
        return engine.REPO_URL

    def launcher_version(self):
        return engine.LAUNCHER_VERSION

    def check_launcher_update(self):
        try:
            return engine.get_launcher_update_info()
        except Exception as ex:
            return {
                "ok": False,
                "current": engine.LAUNCHER_VERSION,
                "latest": engine.LAUNCHER_VERSION,
                "update_available": False,
                "error": str(ex),
            }

    def detect_path(self):
        try:
            d = engine.detect_minecraft_dir()
            return str(d) if d else ""
        except Exception:
            return ""

    def _load_manifest(self):
        if not self._manifest:
            m = engine.fetch_json(engine.MANIFEST_URL)
            engine.validate_manifest(m)
            self._manifest = m
        return self._manifest

    def _state_payload(self, path, options=None):
        if not path:
            return {"status": "path_error", "extra": [], "total": 0}
        options = options or {}
        include_shaders = bool(options.get("shaders", True))
        st = engine.inspect_install_state(
            Path(path), self._manifest, include_shaders=include_shaders)
        return {"status": st["status"], "total": st["total"], "extra": st["extra"]}

    def load_manifest_state(self, path=None, options=None):
        path = path or self.detect_path()
        m = self._load_manifest()
        return {
            "path": path,
            "launcher_version": engine.LAUNCHER_VERSION,
            "manifest": {"ok": True, "version": m["minecraft_version"],
                         "count": len(m["entries"])},
            "state": self._state_payload(path, options),
            "carousel": _basic_carousel_items(m),
        }

    def get_state(self, path, options=None):
        self._load_manifest()
        return self._state_payload(path or "", options)

    def get_carousel(self):
        m = self._load_manifest()
        items = []
        for it in engine.build_carousel_items(m):
            items.append({"title": it["title"], "page": it["page"],
                          "icon": _data_url(it.get("icon"))})
        return items

    def browse(self):
        # 폴더 선택 다이얼로그(모달). 선택 경로 반환.
        try:
            res = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if res:
                return res[0] if isinstance(res, (list, tuple)) else res
        except Exception:
            pass
        return None

    # ---- 부팅: 즉시 반환, 백그라운드에서 전부 처리 후 JS 로 푸시 ----
    def start(self):
        threading.Thread(target=self._boot_worker, daemon=True).start()
        return True

    def _boot_worker(self):
        import os as _os
        if _os.environ.get("IMI_NOBOOT"):
            return
        # 1) 경로 자동 감지
        try:
            d = engine.detect_minecraft_dir()
            path = str(d) if d else ""
        except Exception:
            path = ""
        self._js("onPath", path)
        # 2) manifest
        try:
            m = engine.fetch_json(engine.MANIFEST_URL)
            engine.validate_manifest(m)
            self._manifest = m
            self._js("onManifest", {"ok": True, "version": m["minecraft_version"],
                                    "count": len(m["entries"])})
            self._js("onCarousel", _basic_carousel_items(m))
        except Exception as ex:
            self._js("onManifest", {"ok": False, "error": str(ex)})
            return
        # 3) 설치 상태
        self._push_state(path)
        # 4) 캐러셀(썸네일)
        items = []
        try:
            for it in engine.build_carousel_items(self._manifest):
                items.append({"title": it["title"], "page": it["page"],
                              "icon": _data_url(it.get("icon"))})
        except Exception:
            items = []
        self._js("onCarousel", items)

    def _push_state(self, path):
        try:
            if not path:
                self._js("onState", {"status": "path_error", "extra": [], "total": 0})
                return
            st = engine.inspect_install_state(Path(path), self._manifest)
            self._js("onState", {"status": st["status"], "total": st["total"],
                                 "extra": st["extra"]})
        except Exception:
            self._js("onState", {"status": "path_error", "extra": [], "total": 0})

    def refresh(self, path):
        """경로 변경 시 상태 재점검(백그라운드)."""
        def work(p):
            if not self._manifest:
                try:
                    m = engine.fetch_json(engine.MANIFEST_URL)
                    engine.validate_manifest(m)
                    self._manifest = m
                except Exception:
                    pass
            self._push_state(p or "")
        threading.Thread(target=work, args=(path,), daemon=True).start()
        return True

    # ---- 설치 (백그라운드 + 진행 푸시) ----
    def install(self, path, options=None):
        if self._installing or not path:
            return False
        self._installing = True
        threading.Thread(target=self._install_worker, args=(path, options or {}),
                         daemon=True).start()
        return True

    def install_launcher_update(self):
        if self._launcher_updating:
            return False
        self._launcher_updating = True
        threading.Thread(target=self._launcher_update_worker, daemon=True).start()
        return True

    def _launcher_update_worker(self):
        try:
            engine.install_launcher_update(
                step=lambda m: self._js("onLauncherUpdateStep", m),
                progress=lambda f: self._js("onLauncherUpdateProgress", f),
            )
            self._js("onLauncherUpdateReady")
            time.sleep(1.0)
            if self._window:
                self._window.destroy()
            os._exit(0)
        except engine.InstallError as ex:
            self._js("onLauncherUpdateFail", str(ex))
        except Exception as ex:
            self._js("onLauncherUpdateFail", f"예상치 못한 오류: {ex}")
        finally:
            self._launcher_updating = False

    def _install_worker(self, path, options):
        try:
            engine.run_install(
                path, engine.MANIFEST_URL,
                log=lambda m: self._js("onLog", m),
                step=lambda m: self._js("onStep", m),
                progress=lambda f: self._js("onProgress", f),
                options=options,
            )
            self._js("onDone")
        except engine.InstallError as ex:
            self._js("onFail", str(ex))
        except Exception as ex:
            self._js("onFail", f"예상치 못한 오류: {ex}")
        finally:
            self._installing = False


def main():
    api = Api()
    window = webview.create_window(
        engine.APP_TITLEBAR,
        url=resource_path("web", "index.html"),
        width=900, height=600,
        frameless=True, easy_drag=True,
        resizable=False,
        background_color="#0E1014",
        js_api=api,
    )
    api._window = window
    webview.start()


if __name__ == "__main__":
    main()
