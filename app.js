let TOPO = null, STATE = null, panZoom = null;

// Canvas e mapeamento
const W = 1600, H = 900, M = 40;
const VP_ID = "vp";     // grupo que servirá de viewport para pan/zoom
let mapPoint = null;

// Modal / alvo atual
let TARGET = { type: null, name: null };

// ---------- util ----------
function log(msg){
  const el = document.getElementById("log");
  const time = new Date().toLocaleTimeString();
  el.innerHTML = `[${time}] ${msg}<br>` + el.innerHTML;
}
async function fetchJSON(url, options){
  const r = await fetch(url, options);
  if(!r.ok){ throw new Error(`${r.status} ${await r.text()}`); }
  return r.json();
}

// ---------- boot ----------
async function loadAll(){
  try{
    TOPO = await fetchJSON("/api/topology");
    buildMapper(TOPO.buses);
    await refreshState();
    buildSelectors();
    prepareSVG();      // cria <g id="vp"> e fundo
    draw();            // desenha tudo DENTRO do #vp

    if (panZoom) panZoom.destroy();
    panZoom = svgPanZoom('#view', {
      viewportSelector: `#${VP_ID}`,   // <- SEMPRE usa este grupo
      controlIconsEnabled: true,
      fit: true,
      center: true,
      dblClickZoomEnabled: true
    });
  }catch(e){ log("Falha ao iniciar: " + e.message); }
}

async function refreshState(){ STATE = await fetchJSON("/api/state"); }
function buildSelectors(){
  const lines = TOPO.lines.map(x=>x[0]);
  document.getElementById("selLine").innerHTML  = lines.map(n=>`<option>${n}</option>`).join("");
  document.getElementById("selFault").innerHTML = lines.map(n=>`<option>${n}</option>`).join("");
}

// ---------- geometria ----------
function prepareSVG(){
  const svg = document.getElementById("view");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  // zera e cria grupo viewport fixo
  svg.innerHTML = "";
  const vp = document.createElementNS("http://www.w3.org/2000/svg", "g");
  vp.setAttribute("id", VP_ID);
  svg.appendChild(vp);

  // fundo dentro do viewport (para pan/zoom junto)
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x",0); bg.setAttribute("y",0);
  bg.setAttribute("width",W); bg.setAttribute("height",H);
  bg.setAttribute("fill","#000");
  vp.appendChild(bg);
}

function buildMapper(buses){
  let minLng=Infinity,maxLng=-Infinity,minLat=Infinity,maxLat=-Infinity;
  Object.values(buses).forEach(([lng,lat])=>{
    minLng = Math.min(minLng,lng); maxLng = Math.max(maxLng,lng);
    minLat = Math.min(minLat,lat); maxLat = Math.max(maxLat,lat);
  });
  const dLng = Math.max(maxLng-minLng, 1e-9);
  const dLat = Math.max(maxLat-minLat, 1e-9);
  const s = Math.min((W-2*M)/dLng, (H-2*M)/dLat);
  mapPoint = (name)=>{
    const [lng,lat] = TOPO.buses[name];
    const x = M + (lng - minLng)*s;
    const y = H - (M + (lat - minLat)*s);
    return [x,y];
  };
}
function tri(cx, cy, s=8){
  const h = s * Math.sqrt(3)/2;
  return `${cx},${cy-h} ${cx-s/2},${cy+h/2} ${cx+s/2},${cy+h/2}`;
}

// ---------- desenho ----------
function draw(){
  const svg = document.getElementById("view");
  const vp  = document.getElementById(VP_ID);

  // limpa TUDO dentro do viewport e recria o fundo
  vp.innerHTML = "";
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x",0); bg.setAttribute("y",0);
  bg.setAttribute("width",W); bg.setAttribute("height",H);
  bg.setAttribute("fill","#000");
  vp.appendChild(bg);

  const lines = TOPO.lines;
  const trafos = TOPO.trafos || [];

  // Linhas/religadores
  lines.forEach(([lname,a,b])=>{
    const A = mapPoint(a), B = mapPoint(b);
    const st = (STATE.lines && STATE.lines[lname]) || {open:false, energized:false, fault:false};

    const L = document.createElementNS("http://www.w3.org/2000/svg", "line");
    L.setAttribute("x1",A[0]); L.setAttribute("y1",A[1]);
    L.setAttribute("x2",B[0]); L.setAttribute("y2",B[1]);
    const color = (st.open||st.fault) ? "#ff5163" : (st.energized ? "#00e676" : "#6b7280");
    L.setAttribute("stroke",color); L.setAttribute("stroke-width",3);
    L.addEventListener("click", ()=> openModalForLine(lname));
    L.addEventListener("contextmenu",(e)=>{e.preventDefault(); openModalForLine(lname);});
    vp.appendChild(L);

    const Mpt = [(A[0]+B[0])/2,(A[1]+B[1])/2];
    const S = document.createElementNS("http://www.w3.org/2000/svg","rect");
    const size=12;
    S.setAttribute("x",Mpt[0]-size/2); S.setAttribute("y",Mpt[1]-size/2);
    S.setAttribute("width",size); S.setAttribute("height",size);
    S.classList.add("sw"); S.classList.add(st.open ? "open" : "closed");
    S.addEventListener("click",(e)=>{e.stopPropagation(); openModalForLine(lname);});
    vp.appendChild(S);

    const T = document.createElementNS("http://www.w3.org/2000/svg","text");
    T.setAttribute("x",Mpt[0]); T.setAttribute("y",Mpt[1]-10);
    T.setAttribute("class","lbl"); T.textContent = lname;
    vp.appendChild(T);
  });

  // Transformadores (visuais)
  trafos.forEach(([tname,mv,lv])=>{
    const A = mapPoint(mv), B = mapPoint(lv);

    const L = document.createElementNS("http://www.w3.org/2000/svg","line");
    L.setAttribute("x1",A[0]); L.setAttribute("y1",A[1]);
    L.setAttribute("x2",B[0]); L.setAttribute("y2",B[1]);
    L.setAttribute("stroke","#9ca3af"); L.setAttribute("stroke-width",1.5);
    L.setAttribute("stroke-dasharray","4 3");
    vp.appendChild(L);

    const P = document.createElementNS("http://www.w3.org/2000/svg","polygon");
    P.setAttribute("points", tri(B[0],B[1],10));
    P.setAttribute("fill","#e5e7eb"); P.setAttribute("stroke","#9ca3af"); P.setAttribute("stroke-width",1);
    vp.appendChild(P);

    const T = document.createElementNS("http://www.w3.org/2000/svg","text");
    T.setAttribute("x",B[0]); T.setAttribute("y",B[1]-12);
    T.setAttribute("class","lbl"); T.textContent = tname;
    vp.appendChild(T);
  });
}

// ---------- modal ----------
function openModalForLine(name){
  TARGET = {type:"line", name};
  const st = (STATE.lines && STATE.lines[name]) || {open:false, fault:false, energized:false, from:"?", to:"?"};
  document.getElementById("modTitle").textContent = `Ações – ${name}`;
  document.getElementById("modStatus").textContent =
    `Estado: ${st.open ? "ABERTA" : "FECHADA"} • ${st.energized ? "energizada" : "desenergizada"} • defeito: ${st.fault ? "SIM" : "não"}  |  (${st.from} → ${st.to})`;

  document.getElementById("mOpen").disabled  = st.open;
  document.getElementById("mClose").disabled = !st.open;
  document.getElementById("mFault").disabled = st.fault;
  document.getElementById("mClear").disabled = !st.fault;

  showModal();
}
function showModal(){
  const ov = document.getElementById("overlay");
  const md = document.getElementById("modal");
  ov.classList.remove("hidden"); md.classList.remove("hidden");
  requestAnimationFrame(()=> ov.style.opacity = 1);
}
function closeModal(){
  const ov = document.getElementById("overlay");
  const md = document.getElementById("modal");
  ov.style.opacity = 0; ov.classList.add("hidden"); md.classList.add("hidden");
  TARGET = {type:null, name:null};
}
document.getElementById("overlay").addEventListener("click", closeModal);
document.getElementById("mCancel").addEventListener("click", closeModal);
document.addEventListener("keydown", (e)=>{ if(e.key==="Escape") closeModal(); });

document.getElementById("mOpen").addEventListener("click", async ()=>{
  if(TARGET.type!=="line") return;
  await fetchJSON("/api/switch",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:TARGET.name, action:"open"})});
  await refreshState(); draw(); log("ABRIR " + TARGET.name); openModalForLine(TARGET.name);
});
document.getElementById("mClose").addEventListener("click", async ()=>{
  if(TARGET.type!=="line") return;
  await fetchJSON("/api/switch",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:TARGET.name, action:"close"})});
  await refreshState(); draw(); log("FECHAR " + TARGET.name); openModalForLine(TARGET.name);
});
document.getElementById("mFault").addEventListener("click", async ()=>{
  if(TARGET.type!=="line") return;
  await fetchJSON("/api/fault",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:TARGET.name, action:"apply"})});
  await refreshState(); draw(); log("DEFEITO " + TARGET.name); openModalForLine(TARGET.name);
});
document.getElementById("mClear").addEventListener("click", async ()=>{
  if(TARGET.type!=="line") return;
  await fetchJSON("/api/fault",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:TARGET.name, action:"clear"})});
  await refreshState(); draw(); log("LIMPAR DEFEITO " + TARGET.name); openModalForLine(TARGET.name);
});

// ---------- botões laterais (mantidos) ----------
document.getElementById("btnOpen").addEventListener("click", async ()=>{
  const n = document.getElementById("selLine").value;
  await fetchJSON("/api/switch",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:n, action:"open"})});
  await refreshState(); draw(); log("ABRIR " + n);
});
document.getElementById("btnClose").addEventListener("click", async ()=>{
  const n = document.getElementById("selLine").value;
  await fetchJSON("/api/switch",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:n, action:"close"})});
  await refreshState(); draw(); log("FECHAR " + n);
});
document.getElementById("btnApplyFault").addEventListener("click", async ()=>{
  const n = document.getElementById("selFault").value;
  await fetchJSON("/api/fault",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:n, action:"apply"})});
  await refreshState(); draw(); log("DEFEITO " + n);
});
document.getElementById("btnClearFault").addEventListener("click", async ()=>{
  const n = document.getElementById("selFault").value;
  await fetchJSON("/api/fault",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name:n, action:"clear"})});
  await refreshState(); draw(); log("LIMPAR DEFEITO " + n);
});
document.getElementById("btnReset").addEventListener("click", async ()=>{
  await fetchJSON("/api/reset",{method:"POST"});
  await refreshState(); draw(); log("RESET");
});

// init
loadAll().catch(e=>log("Falha ao iniciar: " + e.message));
