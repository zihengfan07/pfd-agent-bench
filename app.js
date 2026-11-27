'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const data = window.PFD_DATA;
  let lang = 'en', selectedCase = data.cases[0], sheet, view, pointer = null;
  const t = (en, zh) => lang === 'zh' ? zh : en;
  const ns = 'http://www.w3.org/2000/svg';
  function reviewURL() { return `review/开始审阅.html?case=${encodeURIComponent(selectedCase.id)}&sheet=${encodeURIComponent(sheet.id)}`; }
  function updateView() { $('cad-viewer').setAttribute('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`); }
  function fit() { view = {x:0,y:0,w:sheet.width,h:sheet.height}; updateView(); }
  function zoom(factor) {
    const w = Math.max(sheet.width/6, Math.min(sheet.width*1.15, view.w*factor));
    const h = w*sheet.height/sheet.width;
    view = {x:view.x+(view.w-w)/2,y:view.y+(view.h-h)/2,w,h}; updateView();
  }
  function chooseCase(id) {
    selectedCase = data.cases.find(c => c.id === id) || data.cases[0];
    renderCase(); chooseSheet(selectedCase.featured);
  }
  function renderTabs() {
    $('case-tabs').replaceChildren();
    for (const c of data.cases) {
      const b = document.createElement('button'); b.className='case-tab';
      b.textContent=c.id.replace('HARD_','').replace('ZEN_LIGNIN_FIRST_MVR',t('Lignin MVR','木质素 MVR'))+' · '+(lang==='zh'?c.focus_zh:c.focus_en);
      b.setAttribute('aria-pressed', String(c.id===selectedCase.id));
      b.addEventListener('click',()=>chooseCase(c.id)); $('case-tabs').append(b);
    }
  }
  function renderCase() {
    renderTabs(); $('case-id').textContent=selectedCase.id;
    $('case-title').textContent=selectedCase[lang]; $('case-focus').textContent=selectedCase['focus_'+lang];
    for (const k of ['equipment','streams','sheets']) $('case-'+k).textContent=selectedCase.stats[k];
    $('case-status').textContent=selectedCase.status==='NOT_DELIVERABLE'
      ? t('Source delivery status: not deliverable; retained for review.','原始交付状态：不可交付，保留用于审阅。')
      : t('Source delivery status: review required.','原始交付状态：需要复核。');
    $('sheet-select').replaceChildren();
    for (const s of selectedCase.sheets) { const o=document.createElement('option');o.value=s.id;o.textContent=s.id;$('sheet-select').append(o); }
  }
  function chooseSheet(id, from=null) {
    sheet=selectedCase.sheets.find(s=>s.id===id)||selectedCase.sheets[0];
    $('sheet-select').value=sheet.id;
    $('cad-image').setAttribute('href',sheet.image); $('cad-image').setAttribute('width',sheet.width); $('cad-image').setAttribute('height',sheet.height);
    $('cad-viewer').setAttribute('aria-label',`${selectedCase[lang]}, ${sheet.id}`);
    $('sheet-pdf').href=sheet.pdf; $('review-link').href=reviewURL();
    $('sheet-detail').textContent=t(`${sheet.equipment} equipment nodes on this sheet`, `本页 ${sheet.equipment} 个设备节点`);
    $('trace-select').replaceChildren(); $('cad-hotspots').replaceChildren();
    sheet.connectors.forEach((c,i)=>{
      const o=document.createElement('option');o.value=String(i);o.textContent=`${c.stream_id} · ${c.target_sheet_id}`;$('trace-select').append(o);
    });
    if(!sheet.connectors.length){const o=document.createElement('option');o.textContent=t('No cross-sheet target on this sheet','本页无跨页跳转目标');$('trace-select').append(o);}
    $('trace-go').disabled=!sheet.connectors.length; $('trace-select').disabled=!sheet.connectors.length;
    $('trace-state').textContent=from?t(`Followed ${from.stream} from ${from.sheet}.`,`已沿 ${from.stream} 从 ${from.sheet} 跳转。`):t('Select an interface to highlight its terminal.','选择接口可高亮其连接符。');
    fit(); highlightConnector();
  }
  function highlightConnector() {
    $('cad-hotspots').replaceChildren(); const c=sheet.connectors[Number($('trace-select').value)]; if(!c)return;
    const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',c.x);circle.setAttribute('cy',c.y);circle.setAttribute('r',Math.max(28,sheet.width*.008));circle.setAttribute('class','hotspot');
    const title=document.createElementNS(ns,'title');title.textContent=c.label;circle.append(title);
    circle.addEventListener('click',()=>follow());$('cad-hotspots').append(circle);
  }
  function follow() {const c=sheet.connectors[Number($('trace-select').value)];if(c&&selectedCase.sheets.some(s=>s.id===c.target_sheet_id)){chooseSheet(c.target_sheet_id,{stream:c.stream_id,sheet:sheet.id});}}
  function renderResults() {
    const colors=['inventory','symbol','topology','layout']; $('result-rows').replaceChildren();
    data.results.forEach((r,idx)=>{
      const tr=document.createElement('tr');if(r.ours)tr.classList.add('ours');if(r.ours&&!data.results[idx-1]?.ours)tr.classList.add('ours-start');
      const name=document.createElement('td');name.textContent=r.label;tr.append(name);
      [...r.metrics,{mean:r.average,valid_N:r.joint_N}].forEach((v,i)=>{
        const td=document.createElement('td');if(colors[i])td.className=colors[i];
        const n=document.createElement('span');n.className='value';n.textContent=typeof v.mean==='number'?v.mean.toFixed(2):'—';
        const count=document.createElement('small');count.textContent=`(${v.valid_N})`;td.append(n,count);
        td.title=t(`${v.valid_N} valid tasks out of 50`,`50 题中有 ${v.valid_N} 题具有有效评分`);tr.append(td);
      });$('result-rows').append(tr);
    });
  }
  function setLanguage(next) {
    lang=next;document.documentElement.lang=lang==='zh'?'zh-CN':'en';document.body.classList.toggle('zh',lang==='zh');
    document.querySelectorAll('[data-en][data-zh]').forEach(el=>el.textContent=el.dataset[lang]);
    document.querySelectorAll('[data-figure]').forEach(el=>{const path=`assets/challenges/${el.dataset.figure}-${lang}.svg`;el.setAttribute(el.tagName==='IMG'?'src':'href',path);});
    try {localStorage.setItem('pfd-language',lang);} catch (_) {}
    $('language').textContent=lang==='en'?'中文':'EN';$('language').setAttribute('aria-label',lang==='en'?'Switch to Chinese':'切换到英文');
    const current=sheet?.id;renderCase();chooseSheet(current||selectedCase.featured);renderResults();
  }
  $('language').addEventListener('click',()=>setLanguage(lang==='en'?'zh':'en'));
  $('sheet-select').addEventListener('change',e=>chooseSheet(e.target.value));
  $('trace-select').addEventListener('change',highlightConnector);$('trace-go').addEventListener('click',follow);
  $('fit').addEventListener('click',fit);$('zoom-in').addEventListener('click',()=>zoom(.72));$('zoom-out').addEventListener('click',()=>zoom(1/.72));
  const svg=$('cad-viewer');
  svg.addEventListener('pointerdown',e=>{if(e.target.closest('.hotspot'))return; if(e.pointerType==='touch')return;pointer={x:e.clientX,y:e.clientY,view:{...view}};svg.setPointerCapture(e.pointerId);svg.classList.add('dragging');});
  svg.addEventListener('pointermove',e=>{if(!pointer)return;const box=svg.getBoundingClientRect();const scale=Math.max(view.w/box.width,view.h/box.height);view.x=pointer.view.x-(e.clientX-pointer.x)*scale;view.y=pointer.view.y-(e.clientY-pointer.y)*scale;updateView();});
  for(const evt of ['pointerup','pointercancel','lostpointercapture']) svg.addEventListener(evt,()=>{pointer=null;svg.classList.remove('dragging');});
  svg.addEventListener('keydown',e=>{if(e.key==='+')zoom(.72);else if(e.key==='-')zoom(1/.72);else if(e.key==='0')fit();else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();view.x+=(e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0)*view.w*.1;view.y+=(e.key==='ArrowDown'?1:e.key==='ArrowUp'?-1:0)*view.h*.1;updateView();}});
  document.querySelectorAll('.inspect-challenge').forEach(link=>link.addEventListener('click',()=>{chooseCase(link.dataset.case);chooseSheet(link.dataset.sheet);}));
  const demo = $('workflow-video');
  document.querySelectorAll('[data-demo-time]').forEach(button => button.addEventListener('click', () => {
    demo.currentTime = Number(button.dataset.demoTime);
    demo.play().catch(() => { demo.focus(); });
  }));
  let initialLang = new URLSearchParams(location.search).get('lang');
  if(!initialLang) {try {initialLang=localStorage.getItem('pfd-language');}catch (_) {}}
  setLanguage(initialLang==='zh'?'zh':'en');
})();
