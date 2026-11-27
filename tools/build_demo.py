"""Render an evidence-bound, bilingual artifact walkthrough (no simulated live run).

Requires Pillow, PyMuPDF and FFmpeg. See assets/demo/README.txt for inputs.
Run with --case-dir, --receipt, --ffmpeg and --work; use --stills for a quick preview.
"""
from pathlib import Path
import argparse, hashlib, json, math, subprocess, zipfile
from functools import lru_cache
import fitz
from PIL import Image, ImageDraw, ImageFont

P = argparse.ArgumentParser()
P.add_argument('--case-dir', required=True); P.add_argument('--receipt', required=True)
P.add_argument('--ffmpeg', required=True); P.add_argument('--work', required=True)
P.add_argument('--stills', action='store_true')
A = P.parse_args()
CASE, WORK = Path(A.case_dir), Path(A.work)
OUT = Path(__file__).resolve().parents[1] / 'assets/demo'
OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
W, H, FPS, DURATION = 1920, 1080, 24, 90
BG, INK, MUTED, TEAL = '#f5f7f6', '#142e35', '#597078', '#087f80'
COLORS = ['#356ac3', '#087f80', '#7954bb', '#bd7028']
receipt = json.loads(Path(A.receipt).read_text(encoding='utf-8-sig'))
mapping = json.loads((CASE/'identifier_mapping.json').read_text(encoding='utf-8-sig'))
status = json.loads((CASE/'share_status.json').read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(CASE/'DXF/PFD_PACKAGE_MASTER.dxf') == receipt['candidate']['sha256']
assert sha(CASE/'process.xml') == receipt['xml']['sha256']
freeze = json.loads(Path(receipt['candidate_freeze']['path']).read_text())
assert freeze['candidate_source_sha256'] == receipt['candidate']['sha256']
assert freeze['task_graph_parsed_before_freeze'] is False
assert sha(Path(receipt['vector']['path'])) == receipt['vector']['sha256']
SHEETS = sorted((CASE/'PDF').glob('PFD-1*.pdf'))
assert len(SHEETS) == 33

@lru_cache(None)
def font(size, bold=False, mono=False):
    name = 'consola.ttf' if mono else ('msyhbd.ttc' if bold else 'msyh.ttc')
    return ImageFont.truetype('C:/Windows/Fonts/'+name, size)

def txt(im, pos, text, size=30, fill=INK, bold=False, mono=False):
    ImageDraw.Draw(im).text(pos, text, font=font(size,bold,mono), fill=fill)

def box(im, rect, fill='white', radius=24, outline=None, width=2):
    ImageDraw.Draw(im).rounded_rectangle(rect, radius, fill, outline, width)

def line(im, pts, color=TEAL, width=4):
    ImageDraw.Draw(im).line(pts, fill=color, width=width, joint='curve')

def arrow(im, x1,y1,x2,y2, color=TEAL, width=4):
    line(im,[(x1,y1),(x2,y2)],color,width)
    a=math.atan2(y2-y1,x2-x1)
    p=[(x2,y2),(x2-15*math.cos(a-.48),y2-15*math.sin(a-.48)),(x2-15*math.cos(a+.48),y2-15*math.sin(a+.48))]
    ImageDraw.Draw(im).polygon(p,fill=color)

def fitpaste(im, src, rect):
    x,y,w,h=map(int,rect); cp=src.copy();cp.thumbnail((w,h),Image.Resampling.LANCZOS)
    im.paste(cp,(x+(w-cp.width)//2,y+(h-cp.height)//2))

@lru_cache(None)
def pdf_image(name, scale=2.0):
    with fitz.open(CASE/'PDF'/f'{name}.pdf') as doc:
        px=doc[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
        return Image.frombytes('RGB',(px.width,px.height),px.samples)

def crop_pdf(name, needle):
    with fitz.open(CASE/'PDF'/f'{name}.pdf') as doc:
        matches=doc[0].search_for(needle); assert matches, (name,needle)
        r=matches[0]; r=fitz.Rect(r.x0-120,r.y0-115,r.x1+95,r.y1+130)&doc[0].rect
        px=doc[0].get_pixmap(matrix=fitz.Matrix(3.2,3.2),clip=r,alpha=False)
        return Image.frombytes('RGB',(px.width,px.height),px.samples)

SCENES = [
 (0,8,'From process data to assessed CAD','从工艺数据到可评测 CAD',
  'One complex process. A connected path from structured input to independent assessment.',
  '以一个复杂工艺案例，展示结构化输入、图纸生成与独立评测的完整路径。'),
 (8,20,'01  Read the process','01  读取工艺数据',
  'The XML specifies equipment, ports and directed streams. It supplies no saved drawing layout.',
  'XML 提供设备、端口与有向物流关系，不采用已有图纸布局。'),
 (20,32,'02  Organize the generation','02  组织生成过程',
  'Functional organization, page assignment, placement and routing connect intent to geometry.',
  '通过功能组织、分页、设备放置与布线，把工艺关系转化为图纸几何。'),
 (32,44,'03  Deliver editable drawings','03  输出可编辑图纸',
  'The saved A06 package contains 33 process sheets, with native DWG, DXF and PDF artifacts.',
  '该版本 A06 保存了 33 张流程图纸，并提供原生 DWG、DXF 和 PDF 文件。'),
 (44,56,'Across sheets, the process continues','跨越图纸，流程保持连续',
  'Stream S-120 links PFD-104 to PFD-114. Both terminal labels are visible in the original PDFs.',
  '物流 S-120 从 PFD-104 指向 PFD-114；两端标记均来自原始 PDF。'),
 (56,69,'04  Read the delivered CAD independently','04  独立读取交付 CAD',
  'Bench freezes the CAD-derived candidate graph before parsing the task specification.',
  'Bench 先独立读取 CAD 并冻结候选图，再解析任务规范进行结构匹配。'),
 (69,83,'05  Measure four dimensions','05  四维评价',
  'These are this A06 artifact’s recorded scores, on a 0–100 scale, under frozen reader r010.',
  '这里展示该 A06 图纸在冻结读取器 r010 下的实际记录分数，范围为 0–100。'),
 (83,90,'Explore the evidence','探索图纸与评分依据',
  'Inspect the drawings, follow connections and compare the benchmark results on the project site.',
  '在项目网页中浏览图纸、追踪连接，并查看 Bench 的对比结果。')]

def base(index):
    s=SCENES[index]; im=Image.new('RGB',(W,H),BG)
    txt(im,(72,36),'PFD-AGENT / PFD-BENCH',25,TEAL,True)
    txt(im,(1255,38),'HARD_A06  ·  ARTIFACT WALKTHROUGH',22,MUTED)
    line(im,[(72,92),(1848,92)],'#d9e4e4',2)
    txt(im,(72,116),s[2],49,INK,True);txt(im,(74,184),s[3],29,TEAL)
    txt(im,(74,942),s[4],29,INK);txt(im,(74,992),s[5],28,MUTED)
    return im

def flow_card(im,x,y,num,en,zh,desc,color=TEAL,w=510,h=315):
    box(im,(x,y,x+w,y+h));txt(im,(x+28,y+25),num,25,color,True)
    txt(im,(x+28,y+79),en,35,INK,True);txt(im,(x+28,y+130),zh,26,color)
    for i,st in enumerate(desc):txt(im,(x+28,y+205+i*38),st,24,MUTED)

def scene0():
    im=base(0)
    for i,(en,zh,desc) in enumerate([
      ('Process data','工艺数据',['Equipment · Ports · Streams','XML / directed process graph']),
      ('PFD-Agent','图纸生成',['Organization · Placement · Routing','Editable DWG / DXF / PDF']),
      ('PFD-Bench','独立评测',['CAD reading · Structural matching','Four dimensions + evidence'])]):
        x=72+i*605;flow_card(im,x,310,f'0{i+1}',en,zh,desc,w=565,h=330)
        if i<2:arrow(im,x+575,475,x+596,475)
    box(im,(72,696,1848,872),'#e4efed')
    txt(im,(106,729),'445 equipment nodes     /     656 process streams     /     33 CAD sheets',34,TEAL,True)
    txt(im,(106,793),'Saved-artifact replay  ·  Stage animations explain the workflow; they are not live execution.',25,MUTED)
    return im

def scene1():
    im=base(1);box(im,(72,258,1080,893),'#163339');txt(im,(108,284),'process.xml  /  actual input excerpt',25,'#86d5cb')
    code=['<BlockMixer name="A100.A100DRYR.C-104">','  <IN_STRMID>','    <Value>A100.101</Value>','  </IN_STRMID>','  <OUT_STRMID>','    <Value>A100.A100DRYR.102</Value>','  </OUT_STRMID>','</BlockMixer>','','<BlockFlash2 name="A100.A100DRYR.M-104A">','  ...','</BlockFlash2>']
    for i,st in enumerate(code):txt(im,(108,344+i*40),st,27,'#e1edec',mono=True)
    txt(im,(1140,280),'A directed process',35,INK,True);txt(im,(1140,334),'设备及其输入、输出关系',26,TEAL)
    for y,label,detail in [(428,'M-101','A100.A100DRYR.C-104'),(660,'SEP-101','A100.A100DRYR.M-104A')]:
        box(im,(1140,y,1815,y+128));txt(im,(1170,y+15),label,32,TEAL,True);txt(im,(1170,y+69),detail,24,MUTED,mono=True)
    arrow(im,1460,560,1460,651);txt(im,(1505,584),'S-030',27,TEAL)
    txt(im,(1140,829),'Source identifiers → drawing identifiers',24,MUTED)
    return im

def scene2():
    im=base(2)
    for i,(en,zh,desc) in enumerate([
        ('Functional organization','功能组织',['Use the directed process graph','Identify related equipment']),
        ('Page assignment','分页与接口',['Allocate local drawing regions','Represent cross-sheet relations']),
        ('Placement & routing','设备放置与布线',['Position symbols and ports','Route orthogonal connections'])]):
        x=72+i*605;flow_card(im,x,272,str(i+1),en,zh,desc,w=565,h=313)
        if i<2:arrow(im,x+574,430,x+596,430)
    txt(im,(83,615),'Recorded assignment from this package',27,TEAL,True)
    nodes=[e for e in mapping['equipment'] if 'PFD-114' in e['sheet_ids']]
    for i,e in enumerate(nodes):
        x=85+(i%5)*348;y=673+(i//5)*88
        box(im,(x,y,x+325,y+66),'#e3eeec');txt(im,(x+19,y+12),e['equipment_id']+'  /  PFD-114',24,INK)
    txt(im,(85,869),'Method schematic above; saved identifier mapping below.',23,MUTED)
    return im

def scene3():
    im=base(3)
    for i,p in enumerate(SHEETS):
        x=72+(i%11)*163;y=270+(i//11)*194
        box(im,(x,y,x+151,y+178));fitpaste(im,pdf_image(p.stem,0.3),(x+5,y+10,141,135));txt(im,(x+20,y+147),p.stem,19,MUTED)
    txt(im,(74,871),'Original PDF exports · Same package as the scored master DXF',25,TEAL)
    return im

def scene4():
    im=base(4)
    for i,(name,needle) in enumerate([('PFD-104','TO PFD-114 / S-120'),('PFD-114','FROM PFD-104 / S-120')]):
        x=72+i*924;box(im,(x,265,x+852,849));txt(im,(x+30,285),name,32,TEAL,True)
        fitpaste(im,crop_pdf(name,needle),(x+20,343,812,425));txt(im,(x+30,794),needle,28,INK,True)
    arrow(im,941,565,978,565);txt(im,(78,876),'Original CAD export crops. The stream identifier ties the two pages together.',25,MUTED)
    return im

def scene5():
    im=base(5)
    stages=[('Delivered DXF','交付图纸'),('Read & freeze','读取并冻结'),('Compare with XML','与工艺规范比较')]
    for i,(en,zh) in enumerate(stages):
        x=72+i*605;box(im,(x,278,x+565,461));txt(im,(x+27,305),en,34,INK,True);txt(im,(x+27,372),zh,27,TEAL)
        if i<2:arrow(im,x+575,370,x+596,370)
    box(im,(72,512,1848,875),'#163339')
    entries=[('candidate_source_sha256',receipt['candidate']['sha256'][:32]+'…'),('candidate_graph_sha256',freeze['candidate_graph_sha256'][:32]+'…'),('task_graph_parsed_before_freeze','false'),('reader_release','bench-reader-runtime-20261124-r010')]
    txt(im,(104,537),'Recorded freeze certificate',28,'#86d5cb',True)
    for i,(k,v) in enumerate(entries):
        txt(im,(104,598+i*60),k,25,'#b6cecc',mono=True);txt(im,(835,598+i*60),v,25,'#ffffff',mono=True)
    return im

def scene6():
    im=base(6)
    labels=[('Inventory F1','设备类型盘点','equipment_extraction_score'),('Symbol','符号几何','symbol_score'),('Matched topology','匹配范围拓扑','topology_score'),('Local layout','局部布局','layout_score')]
    for i,(en,zh,key) in enumerate(labels):
        x=72+i*451;box(im,(x,282,x+423,691));txt(im,(x+25,315),en,30,INK,True);txt(im,(x+25,370),zh,25,COLORS[i]);txt(im,(x+25,449),f'{receipt["scores"][key]:.2f}',69,COLORS[i],True);txt(im,(x+28,549),'/ 100',28,MUTED)
        box(im,(x+25,622,x+398,634),'#e5ebeb',6)
    box(im,(72,733,1848,890),'#e4efed')
    txt(im,(102,756),'A06 case result  ·  CAD-structure assessment  ·  Reader r010',29,TEAL,True)
    txt(im,(102,808),'Topology: matched relation scope. Layout: local geometry. Scores are not engineering approval.',25,MUTED)
    txt(im,(102,848),'拓扑与布局均有明确评价范围；分数不等同于工程验收。',23,MUTED)
    return im

def scene7():
    im=base(7)
    txt(im,(75,284),'Generate. Inspect. Measure.',66,INK,True)
    txt(im,(78,380),'生成可编辑图纸 · 检查结构关系 · 形成四维评价',36,TEAL)
    for i,(en,zh) in enumerate([('Input + CAD package','查看演示案例文件'),('Bench evidence','核对评分记录'),('Interactive project site','浏览交互式项目网页')]):
        x=72+i*605;box(im,(x,491,x+565,660));txt(im,(x+28,520),en,31,INK,True);txt(im,(x+28,584),zh,26,TEAL)
    txt(im,(76,740),'zihengfan07.github.io/pfd-agent-bench/',42,TEAL,True)
    txt(im,(76,820),'Shanghai Jiao Tong University  /  School of Artificial Intelligence',29,MUTED)
    return im

BASES=[fn() for fn in [scene0,scene1,scene2,scene3,scene4,scene5,scene6,scene7]]

def smooth(v):return .5-.5*math.cos(math.pi*max(0,min(1,v)))

def frame(t):
    idx=max(i for i,s in enumerate(SCENES) if t>=s[0]);start,end=SCENES[idx][:2];p=(t-start)/(end-start)
    im=BASES[idx].copy()
    if idx in (0,2,5):
        step=min(2,int(p*3)); x=72+step*605
        top,bottom=(310,640) if idx==0 else ((272,585) if idx==2 else (278,461))
        ImageDraw.Draw(im).rounded_rectangle((x,top,x+565,bottom),24,outline=TEAL,width=4)
    if idx==1:
        y=560+91*((p*2)%1)
        ImageDraw.Draw(im).ellipse((1452,y-8,1468,y+8),fill=TEAL)
    # A real saved sheet fills the view after the package overview, via a slow camera zoom.
    if idx==3 and p>.35:
        alpha=smooth((p-.35)/.13);overlay=Image.new('RGB',(W,H),BG)
        overlay.paste(BASES[idx]);box(overlay,(72,257,1848,853))
        src=pdf_image('PFD-104');zoom=1+.16*smooth((p-.48)/.52)
        sw,sh=src.size;cw,ch=int(sw/zoom),int(sh/zoom)
        crop=src.crop(((sw-cw)//2,(sh-ch)//2,(sw+cw)//2,(sh+ch)//2))
        fitpaste(overlay,crop,(84,265,1752,581));txt(overlay,(101,274),'PFD-104',25,TEAL,True)
        im=Image.blend(im,overlay,alpha)
    if idx==6:
        for i,key in enumerate(['equipment_extraction_score','symbol_score','topology_score','layout_score']):
            x=72+i*451;v=receipt['scores'][key]/100*smooth(p*3)
            box(im,(x+25,622,x+25+max(12,373*v),634),COLORS[i],6)
    # Chapter tracker reflects presentation time only, not generation wall time.
    for i,(a,b,*_) in enumerate(SCENES):
        x0=72+(a/DURATION)*1776;x1=72+(b/DURATION)*1776-5
        line(im,[(x0,1058),(x1,1058)],'#d5e2e1',6)
        if t>a:line(im,[(x0,1058),(min(x1,72+(t/DURATION)*1776),1058)],TEAL,6)
    if idx>0 and t-start<.45:
        im=Image.blend(BASES[idx-1],im,smooth((t-start)/.45))
    return im

for t in [4,13,25,35,41,50,62,76,86]:frame(t).save(WORK/f'frame-{t:02d}.jpg',quality=92)
poster=frame(4);poster.save(OUT/'poster.jpg',quality=94)
contact=Image.new('RGB',(1440,810),'white')
for i,t in enumerate([4,13,25,35,41,50,62,76,86]):
    im=frame(t);im.thumbnail((480,270));contact.paste(im,((i%3)*480,(i//3)*270))
contact.save(WORK/'storyboard.jpg',quality=92)

def stamp(s):return f'00:{int(s)//60:02d}:{int(s)%60:02d}.000'
for lang,slot in [('en',4),('zh',5)]:
    vtt='WEBVTT\n\n'+'\n\n'.join(f'{i+1}\n{stamp(s[0])} --> {stamp(s[1])}\n{s[slot]}' for i,s in enumerate(SCENES))+'\n'
    (OUT/f'captions-{lang}.vtt').write_text(vtt,encoding='utf-8')
transcript='PFD-Agent / PFD-Bench — bilingual demo transcript\n\nSaved-artifact walkthrough, not a live screen recording. Stage diagrams summarize the method.\nThe supplied A06 run was a saved-evidence recovery with source status draft_with_issues; this video makes no claim of fresh end-to-end execution or engineering approval.\n\n'
for s in SCENES:transcript+=f'{int(s[0]):02d}–{int(s[1]):02d}s | {s[2]} / {s[3]}\n{s[4]}\n{s[5]}\n\n'
transcript+='This historical demonstration has 33 process sheets. The separately versioned online review gallery has 34 A06 sheets; its files are not assigned these scores.\n本演示历史版本含 33 张流程图纸；在线审阅图库的 A06 为另一个 34 页版本，未将本演示评分移用于该版本。\n'
(OUT/'transcript.txt').write_text(transcript,encoding='utf-8')
public={
 'schema':'pfd-demo-evidence.v1','case':'HARD_A06','mode':'saved-artifact walkthrough',
 'duration_seconds':DURATION,'resolution':[W,H],'fps':FPS,'audio':False,
 'selection':'Large process with all four recorded dimensions and original native PDF exports; not selected by highest score.',
 'source_package':'PFD_50题_XML与CAD_20261104结果_20261105整理.zip',
 'generation_source_run_id':status['source_run_id'],'recovery_run_id':status['run_id'],
 'source_status':status['status'],'source_fresh_fullrun':status['fresh_fullrun'],
 'source_execution_complete':status['execution_complete'],'equipment_mapping_nodes':445,'source_streams':656,'process_sheets':33,
 'candidate_sha256':receipt['candidate']['sha256'],'xml_sha256':receipt['xml']['sha256'],
 'scores':receipt['scores'],'score_scale':[0,100], 'scores_scope':{'inventory':'type multiset F1','symbol':'mapped symbol geometry','topology':'matched relation scope','layout':'local geometry'},
 'receipt_id':receipt['id'],'evaluation_time':receipt['finished_at'],'reader':freeze['runtime_identity']['release'],
 'candidate_reading_freeze':freeze,'source_attribution':'https://www.nlr.gov/extranet/biorefinery/aspen-models',
 'license_note':'Case source: GNU General Public License; source page does not specify version. Retain source attribution. Original artifacts remain unchanged.',
 'rendering':'Original supplied PDF exports rasterized by PyMuPDF; no CAD entity or text edits. Camera crop, zoom and original-pixel scaling only.',
 'figure_scope':'Stage diagrams are method schematics. Source-derived identifiers are generation-side evidence, not Bench inputs.',
 'gallery_version_note':'This 33-sheet historical scored package differs from the 34-sheet current review gallery.',
 'source_files':{str(p.relative_to(CASE)).replace('\\','/'):sha(p) for p in [CASE/'process.xml',CASE/'DXF/PFD_PACKAGE_MASTER.dxf',CASE/'identifier_mapping.json',CASE/'PDF/PFD-104.pdf',CASE/'PDF/PFD-114.pdf']}}
(OUT/'evidence.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/'A06-demo-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in public['source_files']:z.write(CASE/name,'HARD_A06/'+name)
    z.write(OUT/'evidence.json','evidence.json');z.write(OUT/'transcript.txt','transcript.txt')
readme='PFD demo / 90-second bilingual artifact walkthrough\n\nPublic evidence: evidence.json and A06-demo-evidence.zip.\nThe master DXF and input XML hashes are checked against receipt p0119 before rendering.\nNo model API calls or new Agent execution are performed by this video builder.\nThe source is the saved A06 recovery package, with 33 process sheets.\nCaptions are burned in English and Chinese; optional WebVTT tracks and transcript are also provided.\n\nRebuild: Python + Pillow + PyMuPDF + FFmpeg.\npython tools/build_demo.py --case-dir <original HARD_A06 folder> --receipt <original p0119.json> --ffmpeg <ffmpeg executable> --work <temporary frame directory>\nThe original receipt must still point to its frozen score vector and reading-freeze record. Windows fonts: Microsoft YaHei and Consolas.\n'
(OUT/'README.txt').write_text(readme,encoding='utf-8')
if A.stills:print('STILLS_READY',WORK,flush=True);raise SystemExit()
command=[A.ffmpeg,'-y','-loglevel','warning','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-threads','4','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'pfd-workflow-demo.mp4')]
with (WORK/'encode.log').open('wb') as log:
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
    for n in range(DURATION*FPS):
        proc.stdin.write(frame(n/FPS).tobytes())
        if n%(FPS*10)==0:print(f'ENCODING {n//FPS}/{DURATION}s',flush=True)
    proc.stdin.close();ret=proc.wait();assert ret==0,ret
print('VIDEO_READY',OUT/'pfd-workflow-demo.mp4',flush=True)
