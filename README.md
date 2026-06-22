# 간편 모드 설치기 (Instant Mod Installer)

마인크래프트 Fabric 모드를 친구들이 **더블클릭 한 번**으로 깔 수 있게 해 주는 도구입니다.
설치기(exe)는 모드 정보를 모르는 **순수 엔진**이고, 실제 모드 목록은 GitHub의
`manifest.json`에 있습니다. **모드를 바꾸려면 manifest만 고치면 됩니다.**

```
설치기 exe (엔진, 친구에게 직접 전달)
        │  실행 시 읽음
        ▼
manifest.json (GitHub, 당신이 관리)  ──▶  모드 url + sha256 + 설치폴더 목록
```

---

## 📦 1. 친구 배포용 안내 (친구에게 그대로 전달하세요)

> **모드 설치 방법**
> 1. 받은 `ModInstaller.exe`를 더블클릭하세요. (설치 창이 열립니다 — 바로 깔리지 않아요)
> 2. **마인크래프트 경로**가 자동으로 채워집니다.
>    - 비어 있으면 `찾아보기…`를 눌러 `.minecraft` 폴더를 직접 골라 주세요.
>    - 보통 위치: `C:\Users\<당신이름>\AppData\Roaming\.minecraft`
> 3. 가운데 **설치될 모드 목록**을 확인하세요.
> 4. **[설치]** 버튼을 누르면 다운로드 → 검증 → 설치가 진행됩니다. (진행률 표시)
> 5. "설치 완료" 메시지가 뜨면 **공식 마인크래프트 런처**를 열고,
>    프로파일에서 **`Instant Modpack`**을 선택해 플레이하세요.
>
> - Python이나 Java를 따로 깔 필요는 **없습니다.**
> - 인터넷 연결이 필요합니다.
> - `mods` / `shaderpacks` 폴더는 이 모드팩 기준으로 **정리(동기화)**됩니다.
>   직접 넣어둔 다른 모드가 있으면 미리 백업하세요.
> - Windows에서 "알 수 없는 게시자" 경고가 뜰 수 있어요(디지털 서명 미사용).
>   `추가 정보 → 실행`을 누르면 됩니다. 출처(당신)를 신뢰할 때만 실행하세요.

---

## 🔧 2. 내가 모드를 바꾸는 법 (관리자=당신)

모드 추가/교체/버전 변경은 **manifest.json만** 수정하면 됩니다. exe는 다시 안 만들어도 됩니다.

### 2-1. manifest.json 구조
```jsonc
{
  "manifest_version": 1,
  "minecraft_version": "1.21.1",   // 마크 버전
  "loader": "fabric",              // fabric 고정
  "loader_version": null,          // null = 최신 stable 자동, 또는 "0.16.5" 처럼 고정
  "entries": [
    {
      "name": "Fabric API",        // 목록에 보일 이름
      "url": "https://.../mod.jar",// HTTPS 다운로드 주소 (Modrinth/GitHub 등)
      "sha256": "abc123...",       // 체크섬 (필수! 없으면 설치기가 거부)
      "target": "mods",            // "mods" 또는 "shaderpacks"
      "gpu": null                  // null=모두 / "nvidia" / "amd"
    }
  ]
}
```

### 2-2. 모드 추가/변경 절차
1. Modrinth나 GitHub Releases에서 모드의 **직접 다운로드 URL**(HTTPS)을 복사.
2. `manifest.json`의 `entries`에 항목을 추가 (sha256은 `"0000...0"`으로 비워둬도 됨).
3. **해시 자동 채우기** 실행:
   ```bash
   python update_hashes.py --fill manifest.json
   ```
   - URL에서 파일을 받아 SHA-256을 계산해 자동 기입합니다.
   - 비어 있거나 `0000...`인 항목만 채웁니다. 전부 다시 계산하려면 `--force`.
   - 특정 URL 해시만 보고 싶으면: `python update_hashes.py --url https://.../mod.jar`
4. `manifest.json`을 GitHub에 **commit & push**.
5. 끝. 친구가 exe를 다시 실행하면 새 모드가 반영됩니다.

> ⚠️ `target`은 반드시 `mods` 또는 `shaderpacks`. `sha256`이 없으면 설치기가 **보안상 거부**합니다.

### 2-3. 설치기 exe 처음 만들기 (또는 MANIFEST_URL 바꿨을 때만 다시)
1. `installer.py` 상단의 `MANIFEST_URL`을 **당신의 raw 주소**로 변경:
   ```
   https://raw.githubusercontent.com/<깃허브아이디>/<저장소>/main/manifest.json
   ```
2. `build_exe.bat` 더블클릭 → `dist\ModInstaller.exe` 생성.
3. 그 exe를 친구에게 **직접 전달**(메신저/USB 등). GitHub에는 올리지 않습니다.

---

## 🔒 3. GitHub 2FA(2단계 인증) 켜기 안내

이 도구는 디지털 서명을 쓰지 않습니다. 대신 **"manifest를 올리는 GitHub 계정의 보안"**과
**"체크섬 검증"**에 신뢰가 걸려 있습니다. 계정이 털리면 악성 모드를 끼워넣을 수 있으니
**2FA는 필수**입니다.

1. GitHub 로그인 → 우상단 프로필 → **Settings**
2. 왼쪽 메뉴 **Password and authentication**
3. **Two-factor authentication → Enable two-factor authentication**
4. 인증 방식 선택:
   - **Authenticator app**(권장): Google Authenticator/Authy 등으로 QR 스캔
   - 또는 SMS
5. 화면의 **recovery codes(복구 코드)**를 안전한 곳에 저장 (휴대폰 분실 대비)
6. 완료. 이후 로그인 시 코드 입력이 필요합니다.

> 추가 권장:
> - manifest 저장소는 **본인만 push 가능**하도록 유지(공개 저장소라도 write 권한은 본인만).
> - 모드 URL은 가능하면 **Modrinth CDN**이나 **GitHub Releases** 등 신뢰할 수 있는 출처만 사용.

---

## 🛡️ 보안 설계 요약 (제로 트러스트)

- 모든 entry에 **sha256 필수** — 없으면 설치 거부.
- 다운로드는 **HTTPS만**, 인증서 검증 유지.
- 체크섬 **불일치 시 즉시 중단**(파일 폐기, fail-safe). 모두 검증된 뒤에야 실제 폴더 반영.
- 건드리는 범위는 지정한 마크 경로의 **mods / shaderpacks / 런처 프로파일**로 제한.
- 디지털 서명 미사용 → **GitHub 2FA + 체크섬 검증**에 의존.

---

## 🧰 기술 메모

- Python 표준 라이브러리만 사용(tkinter, ssl, hashlib, urllib, json) → 친구는 추가 설치 불필요.
- Fabric 로더는 **Java 없이** 설치: `meta.fabricmc.net`의 프로파일 JSON을 받아
  `versions/`에 써넣고, 공식 런처가 첫 실행 시 라이브러리를 받아옵니다.
- GPU 감지: Windows는 `Win32_VideoController` 조회로 NVIDIA/AMD/기타 구분.
