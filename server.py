#!/usr/bin/env python3
import json, os, re, shutil, subprocess, tempfile, unicodedata, zipfile
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
MAX_UPLOAD = 40 * 1024 * 1024

ASSETS = {'/': '<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>مذكرتي — توليد المذكرة اليومية</title><link rel="stylesheet" href="app.css"></head><body>\n<header><div class="brand"><div class="logo">م</div><div><b>مذكرتي</b><small>مولّد المذكرة اليومية</small></div></div><button id="printTop" class="ghost">طباعة / PDF</button></header>\n<main>\n<section class="hero"><div><span class="eyebrow">للأستاذ(ة) • سريع ودقيق</span><h1>من ملفات الدرس إلى<br><em>مذكرة يومية جاهزة.</em></h1><p>حمّل PDF أو PowerPoint، اختر التاريخ، وراجع مذكرة مختصرة بنفس المراحل التربوية.</p></div><div class="steps"><div><i>1</i><span><b>حمّل الملفات</b><small>PDF, PPT, PPTX</small></span></div><div><i>2</i><span><b>راجع المحتوى</b><small>قابل للتعديل</small></span></div><div><i>3</i><span><b>اطبع المذكرة</b><small>A4 أو PDF</small></span></div></div></section>\n<section class="workspace">\n<aside class="panel"><h2>إعداد المذكرة</h2><label>تاريخ الحصة<input id="date" type="date"></label><label>المادة<input id="subject" value="Français"></label><div class="grid2"><label>المستوى<input id="level" value="4"></label><label>الحصة<input id="sessionNo" value="1"></label></div>\n<label>مدة الحصة<input id="time" value="08:30 - 10:50"></label>\n<label class="drop" id="drop"><input id="files" type="file" accept=".pdf,.ppt,.pptx" multiple><span class="uploadIcon">⇧</span><b>اسحب الملفات هنا</b><small>أو اضغط للاختيار • حتى 40MB</small><strong id="fileNames">PDF / PPT / PPTX</strong></label>\n<button class="primary" id="generate">حلّل وولّد المذكرة <span>←</span></button><div id="status" class="status">المعالجة محلية داخل جهازك.</div>\n</aside>\n<section class="preview"><div class="previewBar"><div><b>المعاينة</b><small id="meta">قابلة للتعديل مباشرة</small></div><button id="print" class="ghost">طباعة / PDF</button></div>\n<article id="journal" class="paper" dir="ltr">\n<div class="paperHead"><div class="dateBox"><small>Date :</small><b id="dateText">—</b></div><div class="school"><b>École</b><small>Cahier journal · Période scolaire</small></div></div>\n<div class="time"><span>Temps</span><b id="timeText">08:30 - 10:50</b></div>\n<div class="sessionTitle"><b id="subjectText">Français</b><span>P: 1</span><span id="levelText">Niv: 4</span><span id="sessionText">Séa: 1</span></div>\n<div class="objective card"><h3>🎯 Objectifs</h3><div contenteditable="true" data-field="objective">• Les objectifs précis apparaîtront ici après l’analyse.</div></div>\n<div class="cards">\n<div class="card"><h3>Rituel <mark>10 min</mark></h3><div contenteditable="true" data-field="ritual">Rappel bref et mise en route.</div></div>\n<div class="card"><h3>Vocabulaire <mark>30 min</mark></h3><div contenteditable="true" data-field="vocabulary">Présentation des mots clés du cours.</div></div>\n<div class="card tall"><h3>Lecture - Écriture <mark>80 min</mark></h3><div contenteditable="true" data-field="reading">Activités principales extraites du support.</div></div>\n<div class="card"><h3>Clôture <mark>10 min</mark></h3><div contenteditable="true" data-field="closure">Bilan et réinvestissement.</div></div></div>\n<div class="observ"><b>Observations :</b><span contenteditable="true"></span></div><div class="sign"><span>Signature de l\'inspecteur(trice)</span><span>Signature du/de la directeur(trice)</span></div>\n</article></section></section></main>\n<script src="app.js"></script></body></html>\n', '/index.html': '<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>مذكرتي — توليد المذكرة اليومية</title><link rel="stylesheet" href="app.css"></head><body>\n<header><div class="brand"><div class="logo">م</div><div><b>مذكرتي</b><small>مولّد المذكرة اليومية</small></div></div><button id="printTop" class="ghost">طباعة / PDF</button></header>\n<main>\n<section class="hero"><div><span class="eyebrow">للأستاذ(ة) • سريع ودقيق</span><h1>من ملفات الدرس إلى<br><em>مذكرة يومية جاهزة.</em></h1><p>حمّل PDF أو PowerPoint، اختر التاريخ، وراجع مذكرة مختصرة بنفس المراحل التربوية.</p></div><div class="steps"><div><i>1</i><span><b>حمّل الملفات</b><small>PDF, PPT, PPTX</small></span></div><div><i>2</i><span><b>راجع المحتوى</b><small>قابل للتعديل</small></span></div><div><i>3</i><span><b>اطبع المذكرة</b><small>A4 أو PDF</small></span></div></div></section>\n<section class="workspace">\n<aside class="panel"><h2>إعداد المذكرة</h2><label>تاريخ الحصة<input id="date" type="date"></label><label>المادة<input id="subject" value="Français"></label><div class="grid2"><label>المستوى<input id="level" value="4"></label><label>الحصة<input id="sessionNo" value="1"></label></div>\n<label>مدة الحصة<input id="time" value="08:30 - 10:50"></label>\n<label class="drop" id="drop"><input id="files" type="file" accept=".pdf,.ppt,.pptx" multiple><span class="uploadIcon">⇧</span><b>اسحب الملفات هنا</b><small>أو اضغط للاختيار • حتى 40MB</small><strong id="fileNames">PDF / PPT / PPTX</strong></label>\n<button class="primary" id="generate">حلّل وولّد المذكرة <span>←</span></button><div id="status" class="status">المعالجة محلية داخل جهازك.</div>\n</aside>\n<section class="preview"><div class="previewBar"><div><b>المعاينة</b><small id="meta">قابلة للتعديل مباشرة</small></div><button id="print" class="ghost">طباعة / PDF</button></div>\n<article id="journal" class="paper" dir="ltr">\n<div class="paperHead"><div class="dateBox"><small>Date :</small><b id="dateText">—</b></div><div class="school"><b>École</b><small>Cahier journal · Période scolaire</small></div></div>\n<div class="time"><span>Temps</span><b id="timeText">08:30 - 10:50</b></div>\n<div class="sessionTitle"><b id="subjectText">Français</b><span>P: 1</span><span id="levelText">Niv: 4</span><span id="sessionText">Séa: 1</span></div>\n<div class="objective card"><h3>🎯 Objectifs</h3><div contenteditable="true" data-field="objective">• Les objectifs précis apparaîtront ici après l’analyse.</div></div>\n<div class="cards">\n<div class="card"><h3>Rituel <mark>10 min</mark></h3><div contenteditable="true" data-field="ritual">Rappel bref et mise en route.</div></div>\n<div class="card"><h3>Vocabulaire <mark>30 min</mark></h3><div contenteditable="true" data-field="vocabulary">Présentation des mots clés du cours.</div></div>\n<div class="card tall"><h3>Lecture - Écriture <mark>80 min</mark></h3><div contenteditable="true" data-field="reading">Activités principales extraites du support.</div></div>\n<div class="card"><h3>Clôture <mark>10 min</mark></h3><div contenteditable="true" data-field="closure">Bilan et réinvestissement.</div></div></div>\n<div class="observ"><b>Observations :</b><span contenteditable="true"></span></div><div class="sign"><span>Signature de l\'inspecteur(trice)</span><span>Signature du/de la directeur(trice)</span></div>\n</article></section></section></main>\n<script src="app.js"></script></body></html>\n', '/app.css': ':root{--ink:#1f2a32;--muted:#69747b;--paper:#fff;--bg:#f4f2ee;--accent:#885477;--accent2:#eef5f2;--green:#1c7a63;--line:#dedbd5}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,"Noto Sans Arabic",sans-serif;overflow-x:hidden}header{height:68px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 4vw;position:sticky;top:0;z-index:3}.brand{display:flex;align-items:center;gap:12px}.brand div:last-child{display:flex;flex-direction:column}.brand small{color:var(--muted);font-size:12px}.logo{width:38px;height:38px;border-radius:10px;background:var(--ink);color:#fff;display:grid;place-items:center;font-size:22px;font-weight:bold}button{font:inherit;cursor:pointer}.ghost{border:1px solid var(--line);background:#fff;border-radius:8px;padding:10px 16px;color:var(--ink)}main{max-width:1360px;margin:auto;padding:36px 4vw 64px}.hero{display:flex;justify-content:space-between;align-items:end;gap:40px;margin-bottom:32px}.eyebrow{color:var(--green);font-weight:bold;font-size:13px}.hero h1{font-size:clamp(36px,5vw,64px);line-height:1.05;margin:10px 0 16px;letter-spacing:-2px}.hero h1 em{font-style:normal;color:var(--green)}.hero p{color:var(--muted);font-size:17px;max-width:620px}.steps{min-width:320px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px 18px}.steps div{display:flex;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}.steps div:last-child{border:0}.steps i{font-style:normal;background:var(--accent2);color:var(--green);border-radius:50%;width:28px;height:28px;display:grid;place-items:center;font-weight:bold}.steps span{display:flex;flex-direction:column}.steps small{color:var(--muted)}.workspace{display:grid;grid-template-columns:320px 1fr;gap:24px;align-items:start}.panel,.preview{background:#fff;border:1px solid var(--line);border-radius:12px}.panel{padding:22px;position:sticky;top:90px}.panel h2{margin:0 0 20px}.panel label:not(.drop){display:flex;flex-direction:column;gap:7px;font-size:13px;font-weight:bold;margin-bottom:14px}.panel input{border:1px solid var(--line);border-radius:8px;padding:11px;background:#fafafa;font:inherit;min-width:0}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.drop{border:1.5px dashed #b8b4ae;background:#faf9f7;border-radius:10px;min-height:142px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:16px;margin:8px 0 14px;cursor:pointer}.drop.drag{border-color:var(--green);background:var(--accent2)}.drop input{display:none}.drop small{color:var(--muted);margin:5px}.drop strong{font-size:11px;color:var(--green);max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.uploadIcon{font-size:26px;color:var(--green)}.primary{width:100%;border:0;background:var(--ink);color:#fff;padding:13px;border-radius:8px;font-weight:bold;display:flex;justify-content:center;gap:12px}.primary:disabled{opacity:.6}.status{font-size:12px;color:var(--muted);text-align:center;margin-top:10px;line-height:1.5}.status.error{color:#b33}.preview{padding:18px;background:#e9e6e1;min-width:0}.previewBar{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.previewBar>div{display:flex;flex-direction:column}.previewBar small{color:var(--muted)}.paper{background:var(--paper);max-width:900px;margin:auto;padding:28px;border-radius:3px;box-shadow:0 2px 10px #00000012;min-height:1100px}.paperHead{height:56px;border:2px solid var(--ink);border-radius:9px;display:grid;grid-template-columns:1fr 310px;overflow:hidden}.dateBox{padding:8px 18px;display:flex;gap:18px;align-items:center}.dateBox b{font-size:20px}.school{background:var(--ink);color:#fff;display:flex;flex-direction:column;justify-content:center;align-items:flex-end;padding:8px 16px}.school small{opacity:.75}.time{height:40px;display:flex;align-items:center;gap:20px;color:var(--muted);font-size:13px}.time b{color:var(--ink);border-bottom:1px solid #aaa;padding:0 20px}.sessionTitle{background:var(--accent);color:#fff;padding:8px 14px;border-radius:9px 9px 0 0;display:flex;align-items:center;gap:10px}.sessionTitle span{font-size:11px;background:#ffffff25;border-radius:10px;padding:3px 7px}.card{border:1px solid #c9c5c0;border-radius:9px;background:#fbf8fa;overflow:hidden;min-height:150px}.card h3{background:var(--accent);color:#fff;margin:0;padding:10px 16px;font-size:15px;display:flex;justify-content:space-between}.card mark{color:#fff;background:#6e3f60;border-radius:12px;padding:2px 10px;font-size:12px}.card div{padding:16px 20px;line-height:1.6;white-space:pre-line;outline:0}.objective{min-height:160px;margin:14px 0}.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card.tall{min-height:205px}.observ{margin-top:18px;border:1px solid var(--line);min-height:70px;display:grid;grid-template-columns:120px 1fr}.observ b{padding:12px;background:#f2f1ef}.observ span{padding:12px;outline:0}.sign{display:flex;justify-content:space-around;font-size:12px;font-weight:bold;margin-top:24px}.status.loading:after{content:\' \';display:inline-block;width:12px;height:12px;border:2px solid #ccc;border-top-color:var(--green);border-radius:50%;animation:r .8s linear infinite;margin-right:8px}@keyframes r{to{transform:rotate(360deg)}}[contenteditable=true]:focus{box-shadow:inset 0 0 0 2px #1c7a6355;background:#fff}@media(max-width:950px){.hero{align-items:start;flex-direction:column}.steps{width:100%}.workspace{grid-template-columns:1fr}.panel{position:static}.paper{min-width:720px}.preview{overflow:auto}}@media(max-width:520px){header{padding:0 16px}.hero h1{font-size:38px}.steps{min-width:0}.panel{padding:16px}.preview{padding:10px}}\n@media print{body{background:#fff}header,.hero,.panel,.previewBar{display:none!important}main{padding:0}.workspace,.preview{display:block;border:0;padding:0;background:#fff}.paper{box-shadow:none;max-width:none;width:100%;min-height:0;padding:8mm}.card{break-inside:avoid}.objective{margin:10px 0}@page{size:A4;margin:7mm}}\n', '/app.js': 'const $=s=>document.querySelector(s); const date=$(\'#date\');\nconst today=new Date(); date.value=today.toISOString().slice(0,10);\nfunction sync(){const d=new Date(date.value+\'T12:00:00\');$(\'#dateText\').textContent=d.toLocaleDateString(\'fr-FR\',{weekday:\'long\',day:\'numeric\',month:\'long\',year:\'numeric\'});$(\'#timeText\').textContent=$(\'#time\').value;$(\'#subjectText\').textContent=$(\'#subject\').value;$(\'#levelText\').textContent=\'Niv: \'+$(\'#level\').value;$(\'#sessionText\').textContent=\'Séa: \'+$(\'#sessionNo\').value}\ndocument.querySelectorAll(\'input\').forEach(x=>x.addEventListener(\'input\',sync));sync();\nconst files=$(\'#files\'),drop=$(\'#drop\');files.onchange=()=>$(\'#fileNames\').textContent=[...files.files].map(f=>f.name).join(\' • \')||\'PDF / PPT / PPTX\';\n[\'dragenter\',\'dragover\'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.add(\'drag\')}));[\'dragleave\',\'drop\'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.remove(\'drag\')}));drop.addEventListener(\'drop\',e=>{files.files=e.dataTransfer.files;files.onchange()});\n$(\'#generate\').onclick=async()=>{if(!files.files.length){$(\'#status\').textContent=\'اختار ملف واحد على الأقل.\';$(\'#status\').className=\'status error\';return}const btn=$(\'#generate\');btn.disabled=true;$(\'#status\').textContent=\'جاري استخراج المحتوى وتحليله… قد يستغرق OCR بعض الوقت.\';$(\'#status\').className=\'status loading\';const fd=new FormData();[...files.files].forEach(f=>fd.append(\'files\',f));try{const r=await fetch(\'/api/analyze\',{method:\'POST\',body:fd});const j=await r.json();if(!j.ok)throw Error(j.error);Object.entries(j.journal).forEach(([k,v])=>{const el=document.querySelector(`[data-field="${k}"]`);if(el)el.textContent=(k===\'objective\'?\'• \':\'\')+v});$(\'#meta\').textContent=`${j.journal.files} ملف • ${j.journal.characters} حرف • ${j.journal.mode}`;$(\'#status\').textContent=\'تم التوليد. راجع النص وعدّله ثم اطبعه.\';$(\'#status\').className=\'status\';sync();document.querySelector(\'.preview\').scrollIntoView({behavior:\'smooth\'})}catch(e){$(\'#status\').textContent=\'خطأ: \'+e.message;$(\'#status\').className=\'status error\'}finally{btn.disabled=false}};\nfunction print(){window.print()}$(\'#print\').onclick=print;$(\'#printTop\').onclick=print;\n'}

STOP = set('de du des le la les un une et ou à au aux en pour par sur avec dans ce cette ces se son sa ses est sont être avoir que qui ne pas plus puis très'.split())

def clean(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def run(cmd, timeout=60):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return p.stdout.decode('utf-8', 'ignore')

def extract_pdf(path, work):
    txt = run(['pdftotext', '-layout', str(path), '-'])
    if len(clean(txt)) >= 120:
        return txt, 'Texte PDF'
    if not shutil.which('tesseract'):
        raise ValueError("هذا PDF عبارة عن صورة. ثبّت Tesseract OCR مع اللغة الفرنسية (fra) ثم أعد المحاولة.")
    prefix = work / 'page'
    run(['pdftoppm', '-jpeg', '-r', '180', '-f', '1', '-l', '20', str(path), str(prefix)], 120)
    chunks=[]
    for img in sorted(work.glob('page-*.jpg')):
        chunks.append(run(['tesseract', str(img), 'stdout', '-l', 'fra+ara+eng', '--psm', '6'], 60))
    return '\n'.join(chunks), 'OCR'

def extract_pptx(path):
    chunks=[]
    with zipfile.ZipFile(path) as z:
        names=sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)], key=lambda x:int(re.search(r'(\d+)',x).group(1)))
        ns='{http://schemas.openxmlformats.org/drawingml/2006/main}'
        for i,n in enumerate(names,1):
            root=ET.fromstring(z.read(n)); texts=[clean(t.text) for t in root.iter(ns+'t') if clean(t.text)]
            if texts: chunks.append(f'PAGE {i}\n'+'\n'.join(texts))
    return '\n'.join(chunks), 'Texte PowerPoint'

def extract_file(path, work):
    ext=path.suffix.lower()
    if ext=='.pdf': return extract_pdf(path, work)
    if ext=='.pptx': return extract_pptx(path)
    if ext=='.ppt':
        out=work/'converted'; out.mkdir(exist_ok=True)
        run(['soffice','--headless','--convert-to','pptx','--outdir',str(out),str(path)],120)
        candidates=list(out.glob('*.pptx'))
        if not candidates: raise ValueError('تعذر تحويل ملف PPT')
        return extract_pptx(candidates[0])
    raise ValueError('الصيغة غير مدعومة')

def sentences(text):
    text=re.sub(r'\bPAGE \d+\b',' ',text, flags=re.I)
    parts=re.split(r'(?<=[.!?;:])\s+|\n+', text)
    return [clean(x.strip('•▪◦-*–— ')) for x in parts if 15 <= len(clean(x)) <= 340]

def keywords(text, n=12):
    words=re.findall(r"[A-Za-zÀ-ÿ]{3,}", text.lower())
    freq={}
    for w in words:
        if w not in STOP: freq[w]=freq.get(w,0)+1
    return [w for w,_ in sorted(freq.items(), key=lambda kv:(-kv[1],kv[0]))[:n]]

def best(lines, cues, limit=2):
    scored=[]
    for i,s in enumerate(lines):
        lo=s.lower(); score=sum(3 for c in cues if c in lo)
        score += min(3, sum(1 for w in keywords(' '.join(lines),15) if w in lo))
        if score: scored.append((score,-i,s))
    chosen=[]
    for _,_,s in sorted(scored, reverse=True):
        if s not in chosen: chosen.append(s)
        if len(chosen)>=limit: break
    return chosen

def concise(items, maxchars=270):
    out=[]; total=0
    for x in items:
        x=clean(x)
        if len(x)>150: x=x[:147].rsplit(' ',1)[0]+'…'
        if total+len(x)>maxchars: break
        out.append(x); total+=len(x)
    return ' • '.join(out)

def analyze(text, filename):
    ls=sentences(text); keys=keywords(text)
    objective=best(ls,['objectif','comprendre','identifier','reconnaître','maîtriser','apprendre','produire','découvrir'],2)
    vocab=best(ls,['vocabulaire','mots','lexique','notion','terme'],2)
    lecture=best(ls,['lecture','écriture','lire','écrire','syllabe','phrase','texte','activité','exercice'],3)
    ritual=best(ls,['rituel','rappel','révision','échauffement','question','observation'],2)
    close=best(ls,['devoir','clôture','bilan','évaluation','jeu','maison'],2)
    fallback=ls[:]
    def take(arr, count=2):
        nonlocal fallback
        if arr: return concise(arr)
        got=fallback[:count]; fallback=fallback[count:]; return concise(got)
    keyline=', '.join(keys[:10])
    return {
      'source': filename, 'keywords': keyline,
      'objective': take(objective) or f'Comprendre et réutiliser les notions clés : {keyline}.',
      'ritual': take(ritual,1) or 'Rappel bref des acquis et activation des connaissances antérieures.',
      'vocabulary': take(vocab,2) or f'Présentation et mémorisation du vocabulaire cible : {keyline}.',
      'reading': take(lecture,3) or take(fallback,3),
      'closure': take(close,1) or 'Bilan oral rapide, vérification de la compréhension et consigne de réinvestissement.'
    }

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path not in ASSETS:
            self.send_error(404); return
        body = ASSETS[path].encode('utf-8')
        ctype = 'text/html; charset=utf-8' if path in ('/','/index.html') else ('text/css; charset=utf-8' if path.endswith('.css') else 'application/javascript; charset=utf-8')
        self.send_response(200); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def translate_path(self, path):
        p=urlparse(path).path
        if p=='/': p='/index.html'
        return str(STATIC / p.lstrip('/'))
    def do_POST(self):
        if self.path!='/api/analyze': self.send_error(404); return
        length=int(self.headers.get('Content-Length','0'))
        if length<=0 or length>MAX_UPLOAD: self.send_error(413); return
        ctype=self.headers.get('Content-Type','')
        m=re.search(r'boundary=(.+)',ctype)
        if not m: self.send_error(400); return
        boundary=('--'+m.group(1).strip('"')).encode(); body=self.rfile.read(length)
        files=[]
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            for part in body.split(boundary):
                h,sep,data=part.partition(b'\r\n\r\n')
                if not sep: continue
                fm=re.search(br'filename="([^"]+)"',h)
                if not fm: continue
                name=os.path.basename(fm.group(1).decode('utf-8','ignore'))
                if data.endswith(b'\r\n'):
                    data=data[:-2]
                p=td/name; p.write_bytes(data)
                files.append(p)
            try:
                results=[]; modes=[]; texts=[]
                for p in files[:8]:
                    w=td/(p.stem+'_work'); w.mkdir(exist_ok=True)
                    text,mode=extract_file(p,w); texts.append(text); modes.append(f'{p.name}: {mode}'); results.append(analyze(text,p.name))
                if not results: raise ValueError('لم يتم العثور على ملفات صالحة')
                combined='\n'.join(texts); merged=analyze(combined, ' + '.join(p.name for p in files))
                merged['files']=len(results); merged['mode']='، '.join(modes); merged['characters']=len(clean(combined))
                payload={'ok':True,'journal':merged,'sessions':results[:2]}
                self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps(payload,ensure_ascii=False).encode())
            except Exception as e:
                self.send_response(400); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False).encode())
    def log_message(self, *args): pass

if __name__=='__main__':
    port = int(os.environ.get('PORT', '8765'))
    print(f'Moudhakara: http://0.0.0.0:{port}')
    ThreadingHTTPServer(('0.0.0.0', port),Handler).serve_forever()
