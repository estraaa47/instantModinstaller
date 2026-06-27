'use strict';

// ===== 다국어 =====
const LANG = {
  ko: {
    title:"모드팩 설치",
    install_path:"설치 위치", browse:"찾아보기",
    install:"설치", update:"업데이트", launch:"플레이", current:"최신 상태",
    checking:"확인 중", loading_mods:"모드 정보를 불러오는 중…",
    open_page:"클릭하여 모드 페이지 열기", no_mods:"표시할 모드가 없습니다",
    cancel:"취소", confirm:"계속",
    github:"GitHub", launcher_update:"런처 업데이트",
    latest_version:"최신버전입니다", launcher_download:"런처 업데이트 다운로드",
    update_available_tip:"최신 버전이 있어요",
    reinstall:"재설치", reinstall_menu:"재설치 메뉴",
    install_options:"설치 옵션", opt_shader:"셰이더 설치", opt_ram:"램 할당",
    opt_newprofile:"신규 프로필", opt_overwrite:"끄면 덮어쓰기",
    profile_target:"적용할 프로필", profile_none:"프로필 없음",
    done:"설치가 완료되었습니다!\n공식 런처에서 'Astra Ducunt' 프로파일을 실행하세요.",
    fail:"설치 실패:\n\n", path_required:"마인크래프트 경로를 먼저 지정하세요.",
    launcher_update_confirm:(v)=>`런처를 ${v} 버전으로 업데이트합니다.\n다운로드 후 런처가 자동으로 다시 시작됩니다.\n계속할까요?`,
    launcher_downloading:"런처 업데이트 다운로드 중",
    launcher_ready:"업데이트 적용을 위해 런처를 다시 시작합니다.",
    launcher_fail:"런처 업데이트 실패:\n\n",
    reinstall_confirm:(p)=>`현재 모드팩을 다시 설치합니다:\n${p}\n\nmods 폴더를 다시 동기화하고, 램 할당/프로필 옵션도 현재 설정으로 다시 반영합니다.\n계속할까요?`,
    delete_warn:(p,n,list)=>`⚠️ 기존 모드/셰이더 정리 안내\n\n설치 위치: ${p}\n\n모드팩에 없는 아래 기존 파일 ${n}개가 먼저 삭제된 뒤 모드가 설치/업데이트됩니다:\n\n${list}\n\n계속할까요?`,
    confirm_install:(p)=>`다음 경로에 설치합니다:\n${p}\n\nmods 폴더가 manifest 기준으로 동기화됩니다.\n계속할까요?`,
    // 설치/업데이트 단계 표시
    st_path:"경로 확인", st_manifest:"manifest 읽기", st_gpu:"GPU 감지",
    st_download:"다운로드 및 검증", st_install:"설치", st_sync:"동기화",
    st_fabric:"Fabric 로더 설치", st_profile:"런처 프로필 생성", st_done:"완료",
    st_lu_download:"런처 업데이트 다운로드", st_lu_apply:"런처 업데이트 적용 준비",
    fail_step:"실패 ❌", bridge_wait:"런처 브릿지 연결 대기 중…", bridge_fail:"런처 브릿지 연결 실패",
  },
  ja: {
    title:"Modpack インストール",
    install_path:"インストール先", browse:"参照",
    install:"インストール", update:"アップデート", launch:"プレイ", current:"最新",
    checking:"確認中", loading_mods:"Mod 情報を読み込み中…",
    open_page:"クリックしてMOD情報を開く", no_mods:"表示する Mod がありません",
    cancel:"キャンセル", confirm:"続行",
    github:"GitHub", launcher_update:"ランチャー更新",
    latest_version:"最新版です", launcher_download:"ランチャー更新をダウンロード",
    update_available_tip:"最新バージョンがあります",
    reinstall:"再インストール", reinstall_menu:"再インストールメニュー",
    install_options:"インストール設定", opt_shader:"シェーダーをインストール", opt_ram:"RAM割り当て",
    opt_newprofile:"新しいプロファイル", opt_overwrite:"オフ時は既存を上書き",
    profile_target:"適用するプロファイル", profile_none:"プロファイルなし",
    done:"インストールが完了しました。\n公式ランチャーで 'Astra Ducunt' を起動してください。",
    fail:"インストール失敗:\n\n", path_required:"Minecraft フォルダーを先に指定してください。",
    launcher_update_confirm:(v)=>`ランチャーを ${v} に更新します。\nダウンロード後、自動で再起動します。\n続行しますか？`,
    launcher_downloading:"ランチャー更新をダウンロード中",
    launcher_ready:"更新を適用するためランチャーを再起動します。",
    launcher_fail:"ランチャー更新失敗:\n\n",
    reinstall_confirm:(p)=>`現在の Modpack を再インストールします:\n${p}\n\nmods フォルダーを再同期し、RAM割り当て/プロファイル設定も現在の内容で反映します。\n続行しますか？`,
    delete_warn:(p,n,list)=>`⚠️ 既存 Mod / シェーダーの整理\n\nインストール先: ${p}\n\nModpack に含まれない次の既存ファイル ${n} 個を削除してから Mod をインストール/更新します:\n\n${list}\n\n続行しますか？`,
    confirm_install:(p)=>`次の場所にインストールします:\n${p}\n\nmods フォルダーが manifest に合わせて同期されます。\n続行しますか？`,
    // インストール/更新の段階表示
    st_path:"パス確認", st_manifest:"manifest 読み込み", st_gpu:"GPU 検出",
    st_download:"ダウンロードと検証", st_install:"インストール", st_sync:"同期",
    st_fabric:"Fabric ローダー導入", st_profile:"プロファイル作成", st_done:"完了",
    st_lu_download:"ランチャー更新のダウンロード", st_lu_apply:"ランチャー更新の適用準備",
    fail_step:"失敗 ❌", bridge_wait:"ランチャーブリッジ接続待機中…", bridge_fail:"ランチャーブリッジ接続失敗",
  },
};
let lang = "ko";
const t = (k)=>LANG[lang][k];
// 단계 메시지(engine 이 키로 보냄)를 현재 언어로 변환. 키가 아니면 원문 그대로.
const stepText = (m)=>{ const v = LANG[lang][m]; return (typeof v === "string") ? v : m; };
const DEFAULT_RAM_GB = 8;
const MIN_RAM_GB = 2;
let MAX_RAM_GB = 64;   // 부팅 시 시스템 총 RAM 으로 갱신
function applyI18n(){
  document.body.classList.toggle("lang-ja", lang === "ja");   // 일본어 자형용 폰트 전환
  document.querySelectorAll("[data-i18n]").forEach(el=>{
    const v = LANG[lang][el.getAttribute("data-i18n")];
    if(typeof v === "string") el.textContent = v;
  });
  document.getElementById("flag").src = `assets/flag_${lang}.png`;
  setPrimary(state.mode);
  updateLauncherButton();
  if(slides.length) renderCarousel(slides);
}

function setLauncherVersion(v){
  if(v) $("appVersion").textContent = `v${v}`;   // 값 없으면 덮어쓰지 않음(잘못된 버전 표시 방지)
}

// ===== 상태 =====
let api = null;
const state = { path:"", manifest:null, mode:"checking", extras:[], launcherUpdate:null,
  backendStatus:"", installedRam:null };

const $ = (id)=>document.getElementById(id);

function setPrimary(mode){
  state.mode = mode;
  const b = $("primary");
  const map = {install:"install", update:"update", current:"launch", checking:"checking"};
  b.textContent = t(map[mode] || "install");
  b.disabled = (mode === "checking");
  updateReinstallControls();
  syncProfileWidth();   // 모드 변경 시 버튼 폭 바뀜 → 프로필 박스 폭 재동기화
}

function updateReinstallControls(){
  const group = $("primarySplit");
  const toggle = $("reinstallToggle");
  const reinstall = $("reinstallBtn");
  if(!group || !toggle || !reinstall) return;
  const show = state.mode === "current";
  group.classList.toggle("hasReinstall", show);
  if(!show) group.classList.remove("open");
  toggle.disabled = !show;
  reinstall.disabled = !show;
  toggle.title = t("reinstall_menu");
  toggle.setAttribute("aria-expanded", group.classList.contains("open") ? "true" : "false");
}

// ===== 초기화 (푸시 기반: api.start() 후 콜백으로 수신) =====
function init(){
  if(!window.pywebview || !window.pywebview.api){
    $("cMsg").classList.remove("hidden");
    $("cMsg").textContent = t("bridge_wait");
    return;
  }
  api = window.pywebview.api;
  setPrimary("checking");
  loadInitial();
}

// 파이썬 → JS 부팅 콜백
window.onPath = (p)=>{ state.path = p || ""; $("path").value = state.path; };
window.onManifest = (m)=>{
  if(m && m.ok) {
    $("appSub").textContent = `Fabric · ${m.version || "1.21.11"}`;
  }
  else if(m && m.error) {
    $("cMsg").classList.remove("hidden");
    $("cMsg").textContent = m.error;
  }
};
window.onState = (st)=>{
  state.extras = (st && st.extra) || [];
  state.backendStatus = (st && st.status) || "";
  applyMode();
};

// 백엔드 상태 + 옵션 변경(램)을 합쳐 최종 버튼 모드를 결정.
function applyMode(){
  const s = state.backendStatus;
  let mode;
  if(s === "current"){
    // 설치돼 있고 최신이지만 램 설정이 설치된 값과 다르면 '업데이트'
    const cur = clampRam($("optRam").value);
    mode = (state.installedRam && cur !== state.installedRam) ? "update" : "current";
  } else if(s === "update_available"){
    mode = "update";
  } else {
    mode = "install";
  }
  setPrimary(mode);
}
window.onCarousel = (items)=>renderCarousel(items);

async function loadInitial(){
  try {
    const p = await api.detect_path();
    onPath(p);
  } catch(e) {
    onPath("");
  }
  try {
    const boot = await api.load_manifest_state(state.path, currentOptions());
    if(boot.lang === "ko" || boot.lang === "ja"){ lang = boot.lang; applyI18n(); markLangSel(); }
    if(boot.system_ram) applyRamBounds(boot.system_ram);
    if(boot.launcher_version) setLauncherVersion(boot.launcher_version);
    if(boot.path) onPath(boot.path);
    applyProfileOptions(boot.profile_options);
    onManifest(boot.manifest);
    renderCarousel(boot.carousel || []);
    onState(boot.state);
    loadProfiles();
    Promise.resolve(api.get_carousel()).then(items=>renderCarousel(items || [])).catch(()=>{});
  } catch(e) {
    onManifest({ok:false, error:String(e)});
    setPrimary("install");
  }
  checkLauncherUpdate();
}

function refreshState(){
  setPrimary("checking");
  Promise.resolve(api.get_state(state.path, currentOptions()))
    .then(st=>onState(st)).catch(()=>setPrimary("install"));
}

function clampRam(value){
  return Math.max(MIN_RAM_GB, Math.min(MAX_RAM_GB, parseInt(value) || DEFAULT_RAM_GB));
}
function setRamValue(value){
  $("optRam").value = String(clampRam(value));
}
function applyRamBounds(maxGb){
  MAX_RAM_GB = Math.max(MIN_RAM_GB, parseInt(maxGb) || MAX_RAM_GB);
  const input = $("optRam");
  input.min = String(MIN_RAM_GB);
  input.max = String(MAX_RAM_GB);
  setRamValue(input.value);   // 현재 값이 범위를 벗어나면 보정
}

function applyProfileOptions(options){
  if(options && options.ram){
    setRamValue(options.ram);
    state.installedRam = clampRam(options.ram);   // 설치된 램 기준값(업데이트 판정용)
  } else {
    state.installedRam = null;
  }
}

async function loadProfileOptions(){
  try {
    const options = await api.get_profile_options(state.path);
    applyProfileOptions(options);
  } catch(e) {}
}

function currentOptions(){
  const o = {
    shaders: $("optShader").checked,
    ram: clampRam($("optRam").value),
    new_profile: $("optNew").checked,
  };
  if(!o.new_profile && selectedProfileId) o.profile_id = selectedProfileId;
  return o;
}

// ===== 프로필 선택 (신규 프로필 끔 → 덮어쓸 대상 고르기) =====
let profiles = [], selectedProfileId = "";

async function loadProfiles(){
  if(!state.path){ profiles = []; selectedProfileId = ""; renderProfiles(); return; }
  try { profiles = (await api.list_profiles(state.path)) || []; }
  catch(e){ profiles = []; }
  // 기존 선택이 아직 있으면 유지, 없으면 가장 최근(목록 첫 항목)
  if(!profiles.some(p=>p.id===selectedProfileId))
    selectedProfileId = profiles.length ? profiles[0].id : "";
  renderProfiles();
}

function renderProfiles(){
  const menu = $("profileMenu"); menu.innerHTML = "";
  profiles.forEach(p=>{
    const it = document.createElement("div");
    it.className = "profileItem" + (p.id===selectedProfileId ? " sel" : "");
    it.setAttribute("role", "option");
    it.innerHTML = `<span class="pname">${escapeHtml(p.name)}</span>`
      + (p.ram ? `<span class="pram">${p.ram}G</span>` : "");
    it.onclick = (e)=>{ e.stopPropagation(); selectProfile(p.id); };
    menu.appendChild(it);
  });
  const empty = profiles.length === 0;
  const sel = profiles.find(p=>p.id===selectedProfileId);
  $("profileName").textContent = empty ? t("profile_none") : (sel ? sel.name : "—");
  $("profileDrop").classList.toggle("empty", empty);   // 선택 불가(목록 없음)
  updateProfilePickVisibility();
}

function selectProfile(id){
  selectedProfileId = id;
  const sel = profiles.find(p=>p.id===id);
  if(sel && sel.ram) setRamValue(sel.ram);   // 선택 프로필의 램 값 반영
  closeProfileMenu();
  renderProfiles();
}

function updateProfilePickVisibility(){
  const show = !$("optNew").checked;   // 덮어쓰기 모드면 항상 표시(없으면 '프로필 없음')
  $("profilePick").classList.toggle("hidden", !show);
  if(!show) closeProfileMenu();
  syncProfileWidth();
}

// 프로필 박스 폭을 플레이 버튼 그룹(화살표 포함) 실제 폭에 맞춘다.
function syncProfileWidth(){
  const split = $("primarySplit"), drop = $("profileDrop");
  if(!split || !drop) return;
  const w = Math.round(split.getBoundingClientRect().width);
  if(w > 0) drop.style.width = w + "px";
}

function toggleProfileMenu(e){
  e.stopPropagation();
  if(profiles.length === 0) return;    // 프로필 없으면 펼치지 않음
  const drop = $("profileDrop");
  const open = !drop.classList.contains("open");
  drop.classList.toggle("open", open);
  $("profileMenu").classList.toggle("hidden", !open);
  $("profileHead").setAttribute("aria-expanded", open ? "true" : "false");
}

function closeProfileMenu(){
  $("profileDrop").classList.remove("open");
  $("profileMenu").classList.add("hidden");
  $("profileHead").setAttribute("aria-expanded", "false");
}

// ===== 캐러셀 =====
const SLIDE_MS = 4500;
let slides = [], cur = 0, timer = null;
function renderCarousel(items){
  slides = items || [];
  const track = $("cTrack"); track.innerHTML = "";
  $("cGauge").style.display = "none";
  $("cMsg").classList.remove("hidden");
  if(!slides.length){ $("cMsg").textContent = t("no_mods"); return; }
  $("cMsg").classList.add("hidden");
  slides.forEach((s,i)=>{
    const el = document.createElement("div"); el.className = "slide";
    el.innerHTML = `${s.icon?`<img src="${s.icon}">`:`<div class="thumbMissing"></div>`}
      <div><div class="stitle">${escapeHtml(s.title)}</div>${s.page?`<div class="shint">${t("open_page")}</div>`:""}</div>`;
    el.onclick = ()=>{ if(s.page) api.open_url(s.page); };
    track.appendChild(el);
  });
  if(slides.length > 1) $("cGauge").style.display = "";
  cur = 0; go(0); restartTimer();
}
function go(i){
  if(!slides.length) return;
  cur = (i + slides.length) % slides.length;
  $("cTrack").style.transform = `translateX(${-cur*100}%)`;
  if(slides.length > 1) animGauge();
}
function animGauge(){
  const fill = $("cGaugeFill");
  if(!fill) return;
  fill.style.transition = "none";
  fill.style.width = "0%";
  void fill.offsetWidth;            // 리플로우로 애니메이션 재시작
  fill.style.transition = `width ${SLIDE_MS}ms linear`;
  fill.style.width = "100%";
}
function restartTimer(){
  clearInterval(timer);
  if(slides.length > 1) timer = setInterval(()=>go(cur+1), SLIDE_MS);
}
function escapeHtml(s){return (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

// ===== 설치 흐름 =====
function showModal(text){
  return new Promise(res=>{
    $("modalText").textContent = text;
    $("modalBack").classList.remove("hidden");
    const ok=$("modalOk"), cancel=$("modalCancel");
    const done=(v)=>{ $("modalBack").classList.add("hidden"); ok.onclick=cancel.onclick=null; res(v); };
    ok.onclick=()=>done(true); cancel.onclick=()=>done(false);
  });
}

async function onPrimary(){
  if(state.mode === "current"){ api.play(); return; }
  await confirmAndInstall(false);
}

async function confirmAndInstall(forceReinstall){
  if(!state.path){ await showModal(t("path_required")); return; }
  let msg;
  if(forceReinstall){
    msg = t("reinstall_confirm")(state.path);
  } else if(state.extras.length){
    const shown = state.extras.slice(0,14).map(x=>" • "+x).join("\n");
    const more = state.extras.length>14 ? `\n…(+${state.extras.length-14})` : "";
    msg = t("delete_warn")(state.path, state.extras.length, shown+more);
  } else {
    msg = t("confirm_install")(state.path);
  }
  if(!await showModal(msg)) return;
  $("primarySplit").classList.remove("open");
  $("reinstallToggle").setAttribute("aria-expanded", "false");
  startInstall();
}

async function onReinstall(){
  await confirmAndInstall(true);
}

function toggleReinstallMenu(e){
  e.stopPropagation();
  if(state.mode !== "current") return;
  const group = $("primarySplit");
  group.classList.toggle("open");
  $("reinstallToggle").setAttribute("aria-expanded", group.classList.contains("open") ? "true" : "false");
}

function startInstall(){
  $("primary").disabled = true;
  $("reinstallToggle").disabled = true;
  $("reinstallBtn").disabled = true;
  $("progressWrap").classList.remove("hidden");
  $("progressBar").style.width = "0%";
  api.install(state.path, currentOptions());
}

async function checkLauncherUpdate(){
  try {
    const info = await api.check_launcher_update();
    if(info && info.current) setLauncherVersion(info.current);
    state.launcherUpdate = (info && info.update_available) ? info : null;
  } catch(e) {
    state.launcherUpdate = null;
  }
  updateLauncherButton();
}

function updateLauncherButton(){
  const b = $("launcherUpdate");
  if(!b) return;
  b.disabled = false;
  if(state.launcherUpdate){
    b.classList.add("isReady");
    b.setAttribute("aria-disabled", "false");
    b.title = `${t("launcher_download")} ${state.launcherUpdate.latest}`;
    flashUpdateTip();
  } else {
    b.classList.remove("isReady");
    b.setAttribute("aria-disabled", "true");
    b.title = t("latest_version");
  }
}

// 업데이트가 있을 때 버튼 옆 말풍선을 한 번 잠깐 띄웠다 사라지게 한다.
let _updateTipShown = false, _updateTipTimer = null;
function flashUpdateTip(){
  const tip = $("updateTip");
  if(!tip || _updateTipShown) return;
  _updateTipShown = true;
  tip.classList.remove("hidden");
  requestAnimationFrame(()=>tip.classList.add("show"));
  clearTimeout(_updateTipTimer);
  _updateTipTimer = setTimeout(()=>{
    tip.classList.remove("show");
    setTimeout(()=>tip.classList.add("hidden"), 300);
  }, 4000);
}

async function onLauncherUpdate(){
  if(!state.launcherUpdate) return;
  if(!await showModal(t("launcher_update_confirm")(state.launcherUpdate.latest))) return;
  $("launcherUpdate").disabled = true;
  $("primary").disabled = true;
  $("progressWrap").classList.remove("hidden");
  $("progressBar").style.width = "0%";
  $("step").textContent = t("launcher_downloading");
  api.install_launcher_update();
}

// 파이썬 → JS 콜백 (window.* 로 노출)
window.onLog = (m)=>{ /* 필요시 콘솔/로그 패널 */ console.log("[log]", m); };
window.onStep = (m)=>{ $("step").textContent = stepText(m); };
window.onProgress = (f)=>{ $("progressBar").style.width = Math.round(f*100)+"%"; };
window.onDone = async ()=>{
  $("step").textContent = "";
  await showModal(t("done"));
  $("progressWrap").classList.add("hidden");
  await loadProfileOptions();   // 설치된 램 기준값 갱신 → 버튼 플레이로 복귀
  refreshState();
  loadProfiles();   // 새 프로필이 생겼을 수 있으니 목록 갱신
};
window.onFail = async (msg)=>{
  $("step").textContent = t("fail_step");
  $("progressWrap").classList.add("hidden");
  await showModal(t("fail")+msg);
  refreshState();
};
window.onLauncherUpdateStep = (m)=>{ $("step").textContent = stepText(m); };
window.onLauncherUpdateProgress = (f)=>{ $("progressBar").style.width = Math.round(f*100)+"%"; };
window.onLauncherUpdateReady = ()=>{ $("step").textContent = t("launcher_ready"); };
window.onLauncherUpdateFail = async (msg)=>{
  $("progressWrap").classList.add("hidden");
  $("launcherUpdate").disabled = false;
  await showModal(t("launcher_fail")+msg);
  setPrimary(state.mode);
};

// ===== 유휴(마우스 이탈) → 패널 확장 (배너는 줌 없이 팬) =====
document.addEventListener("mouseleave", ()=>document.body.classList.add("idle"));
document.addEventListener("mouseenter", ()=>document.body.classList.remove("idle"));

// ===== 이벤트 바인딩 =====
function bind(){
  $("btnMin").onclick = ()=>api.minimize();
  $("btnClose").onclick = ()=>api.close();
  $("primary").onclick = onPrimary;
  $("reinstallToggle").onclick = toggleReinstallMenu;
  $("reinstallBtn").onclick = (e)=>{ e.stopPropagation(); onReinstall(); };
  $("githubBtn").onclick = ()=>api.open_url("https://github.com/estraaa47/instantModinstaller");
  $("launcherUpdate").onclick = onLauncherUpdate;
  $("cPrev").onclick = ()=>{ go(cur-1); restartTimer(); };
  $("cNext").onclick = ()=>{ go(cur+1); restartTimer(); };
  $("browse").onclick = async ()=>{
    const p = await api.browse();
    if(p){
      state.path = p;
      $("path").value = p;
      await loadProfileOptions();
      await loadProfiles();
      refreshState();
    }
  };
  $("path").addEventListener("change", async ()=>{
    state.path = $("path").value.trim();
    await loadProfileOptions();
    await loadProfiles();
    refreshState();
  });
  $("optShader").addEventListener("change", refreshState);
  $("optRam").addEventListener("change", ()=>{ setRamValue($("optRam").value); applyMode(); });
  $("optNew").addEventListener("change", ()=>{ updateProfilePickVisibility(); refreshState(); });
  $("profileHead").onclick = toggleProfileMenu;

  // 언어 메뉴
  $("lang").onclick = (e)=>{ e.stopPropagation(); $("langMenu").classList.toggle("hidden"); };
  document.addEventListener("click", ()=>{
    $("langMenu").classList.add("hidden");
    $("primarySplit").classList.remove("open");
    $("reinstallToggle").setAttribute("aria-expanded", "false");
    closeProfileMenu();
  });
  document.querySelectorAll(".langItem").forEach(it=>{
    it.onclick = (e)=>{ e.stopPropagation(); lang = it.getAttribute("data-code");
      $("langMenu").classList.add("hidden"); applyI18n(); markLangSel(); };
  });
  markLangSel();
}
function markLangSel(){
  document.querySelectorAll(".langItem").forEach(it=>
    it.classList.toggle("sel", it.getAttribute("data-code")===lang));
}

// 브리지가 '완전히' 준비됐는지 = api 객체뿐 아니라 실제 메서드까지 붙었는지 확인
function bridgeReady(){
  return !!(window.pywebview && window.pywebview.api &&
            typeof window.pywebview.api.load_manifest_state === "function");
}
let _started = false;
function boot(){
  if(_started || !bridgeReady()) return;   // 메서드 안 붙었으면 대기(폴이 재시도)
  _started = true; bind(); init();
}
window.addEventListener("pywebviewready", boot);
boot();   // 이미 준비됐으면 즉시
let _bridgeTries = 0;
const _bridgeTimer = setInterval(()=>{
  boot();
  if(_started){ clearInterval(_bridgeTimer); return; }
  if(++_bridgeTries > 200){   // ~10초
    clearInterval(_bridgeTimer);
    $("cMsg").classList.remove("hidden");
    $("cMsg").textContent = t("bridge_fail");
    setPrimary("install");
  }
}, 50);
