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
    reinstall:"재설치", reinstall_menu:"재설치 메뉴",
    install_options:"설치 옵션", opt_shader:"셰이더 설치", opt_ram:"램 할당",
    opt_newprofile:"신규 프로필", opt_overwrite:"끄면 덮어쓰기",
    done:"설치가 완료되었습니다!\n공식 런처에서 'Astra Ducunt' 프로파일을 실행하세요.",
    fail:"설치 실패:\n\n", path_required:"마인크래프트 경로를 먼저 지정하세요.",
    launcher_update_confirm:(v)=>`런처를 ${v} 버전으로 업데이트합니다.\n다운로드 후 런처가 자동으로 다시 시작됩니다.\n계속할까요?`,
    launcher_downloading:"런처 업데이트 다운로드 중",
    launcher_ready:"업데이트 적용을 위해 런처를 다시 시작합니다.",
    launcher_fail:"런처 업데이트 실패:\n\n",
    reinstall_confirm:(p)=>`현재 모드팩을 다시 설치합니다:\n${p}\n\nmods 폴더를 다시 동기화하고, 램 할당/프로필 옵션도 현재 설정으로 다시 반영합니다.\n계속할까요?`,
    delete_warn:(p,n,list)=>`⚠️ 기존 모드/셰이더 정리 안내\n\n설치 위치: ${p}\n\n모드팩에 없는 아래 기존 파일 ${n}개가 먼저 삭제된 뒤 모드가 설치/업데이트됩니다:\n\n${list}\n\n계속할까요?`,
    confirm_install:(p)=>`다음 경로에 설치합니다:\n${p}\n\nmods 폴더가 manifest 기준으로 동기화됩니다.\n계속할까요?`,
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
    reinstall:"再インストール", reinstall_menu:"再インストールメニュー",
    install_options:"インストール設定", opt_shader:"シェーダーをインストール", opt_ram:"RAM割り当て",
    opt_newprofile:"新しいプロファイル", opt_overwrite:"オフ時は既存を上書き",
    done:"インストールが完了しました。\n公式ランチャーで 'Astra Ducunt' を起動してください。",
    fail:"インストール失敗:\n\n", path_required:"Minecraft フォルダーを先に指定してください。",
    launcher_update_confirm:(v)=>`ランチャーを ${v} に更新します。\nダウンロード後、自動で再起動します。\n続行しますか？`,
    launcher_downloading:"ランチャー更新をダウンロード中",
    launcher_ready:"更新を適用するためランチャーを再起動します。",
    launcher_fail:"ランチャー更新失敗:\n\n",
    reinstall_confirm:(p)=>`現在の Modpack を再インストールします:\n${p}\n\nmods フォルダーを再同期し、RAM割り当て/プロファイル設定も現在の内容で反映します。\n続行しますか？`,
    delete_warn:(p,n,list)=>`⚠️ 既存 Mod / シェーダーの整理\n\nインストール先: ${p}\n\nModpack に含まれない次の既存ファイル ${n} 個を削除してから Mod をインストール/更新します:\n\n${list}\n\n続行しますか？`,
    confirm_install:(p)=>`次の場所にインストールします:\n${p}\n\nmods フォルダーが manifest に合わせて同期されます。\n続行しますか？`,
  },
};
let lang = "ko";
const t = (k)=>LANG[lang][k];
function applyI18n(){
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
const state = { path:"", manifest:null, mode:"checking", extras:[], launcherUpdate:null };

const $ = (id)=>document.getElementById(id);

function setPrimary(mode){
  state.mode = mode;
  const b = $("primary");
  const map = {install:"install", update:"update", current:"launch", checking:"checking"};
  b.textContent = t(map[mode] || "install");
  b.disabled = (mode === "checking");
  updateReinstallControls();
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
    $("cMsg").textContent = "런처 브릿지 연결 대기 중…";
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
  const s = st && st.status;
  if(s === "current") setPrimary("current");
  else if(s === "update_available") setPrimary("update");
  else setPrimary("install");
};
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
    if(boot.launcher_version) setLauncherVersion(boot.launcher_version);
    if(boot.path) onPath(boot.path);
    onManifest(boot.manifest);
    renderCarousel(boot.carousel || []);
    onState(boot.state);
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

function currentOptions(){
  return {
    shaders: $("optShader").checked,
    ram: Math.max(1, Math.min(64, parseInt($("optRam").value) || 4)),
    new_profile: $("optNew").checked,
  };
}

// ===== 캐러셀 =====
let slides = [], cur = 0, timer = null;
function renderCarousel(items){
  slides = items || [];
  const track = $("cTrack"); track.innerHTML = "";
  const dots = $("cDots"); dots.innerHTML = "";
  $("cMsg").classList.remove("hidden");
  if(!slides.length){ $("cMsg").textContent = t("no_mods"); return; }
  $("cMsg").classList.add("hidden");
  slides.forEach((s,i)=>{
    const el = document.createElement("div"); el.className = "slide";
    el.innerHTML = `${s.icon?`<img src="${s.icon}">`:`<div class="thumbMissing"></div>`}
      <div><div class="stitle">${escapeHtml(s.title)}</div>${s.page?`<div class="shint">${t("open_page")}</div>`:""}</div>`;
    el.onclick = ()=>{ if(s.page) api.open_url(s.page); };
    track.appendChild(el);
    const d = document.createElement("i"); if(i===0) d.className="on"; dots.appendChild(d);
  });
  cur = 0; go(0); restartTimer();
}
function go(i){
  if(!slides.length) return;
  cur = (i + slides.length) % slides.length;
  $("cTrack").style.transform = `translateX(${-cur*100}%)`;
  document.querySelectorAll("#cDots i").forEach((d,j)=>d.classList.toggle("on", j===cur));
}
function restartTimer(){
  clearInterval(timer);
  if(slides.length > 1) timer = setInterval(()=>go(cur+1), 4500);
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
  } else {
    b.classList.remove("isReady");
    b.setAttribute("aria-disabled", "true");
    b.title = t("latest_version");
  }
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
window.onStep = (m)=>{ $("step").textContent = m; };
window.onProgress = (f)=>{ $("progressBar").style.width = Math.round(f*100)+"%"; };
window.onDone = async ()=>{
  $("step").textContent = "완료 ✅";
  await showModal(t("done"));
  $("progressWrap").classList.add("hidden");
  refreshState();
};
window.onFail = async (msg)=>{
  $("step").textContent = "실패 ❌";
  $("progressWrap").classList.add("hidden");
  await showModal(t("fail")+msg);
  refreshState();
};
window.onLauncherUpdateStep = (m)=>{ $("step").textContent = m; };
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
    if(p){ state.path = p; $("path").value = p; refreshState(); }
  };
  $("path").addEventListener("change", ()=>{ state.path = $("path").value.trim(); refreshState(); });
  $("optShader").addEventListener("change", refreshState);
  $("optRam").addEventListener("change", refreshState);
  $("optNew").addEventListener("change", refreshState);

  // 언어 메뉴
  $("lang").onclick = (e)=>{ e.stopPropagation(); $("langMenu").classList.toggle("hidden"); };
  document.addEventListener("click", ()=>{
    $("langMenu").classList.add("hidden");
    $("primarySplit").classList.remove("open");
    $("reinstallToggle").setAttribute("aria-expanded", "false");
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
    $("cMsg").textContent = "런처 브릿지 연결 실패";
    setPrimary("install");
  }
}, 50);

