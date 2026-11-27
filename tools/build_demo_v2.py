"""CAD-led walkthrough: original geometry, recorded reader objects, bilingual voice.

No new Agent run or Bench measurement is implied. Rendering layers and highlights
are explanatory animations derived from the unchanged PDF exports / frozen graph.
"""
from pathlib import Path
from functools import lru_cache
import argparse, json, math, subprocess, hashlib, wave, zipfile
import fitz
from PIL import Image, ImageDraw, ImageFont

ap=argparse.ArgumentParser()
ap.add_argument('--case-dir',required=True);ap.add_argument('--receipt',required=True)
ap.add_argument('--work',required=True);ap.add_argument('--ffmpeg',required=True)
ap.add_argument('--stills',action='store_true');a=ap.parse_args()
C=Path(a.case_dir);WORK=Path(a.work);OUT=Path(__file__).resolve().parents[1]/'assets/demo'
WORK.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True)
W,H,FPS,DURATION=1920,1080,24,75
BG='#0d1c26';PANEL='#132935';FG='#f4faf9';SUB='#9db5bf';ACC='#50dfc1';PURPLE='#baacff'
COLORS=['#5ca7ff','#50dfc1','#baacff','#ffc37c']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt=json.loads(Path(a.receipt).read_text(encoding='utf-8-sig'))
assert sha(C/'DXF/PFD_PACKAGE_MASTER.dxf')==receipt['candidate']['sha256']
assert sha(C/'process.xml')==receipt['xml']['sha256']
assert sha(receipt['candidate_graph']['path'])==receipt['candidate_graph']['sha256']
graph=json.loads(Path(receipt['candidate_graph']['path']).read_text(encoding='utf-8'))
nodes=[n for n in graph['nodes'] if n.get('loose_node_evidence',{}).get('panel_id')=='114']
ids={n['candidate_id'] for n in nodes};edges=[e for e in graph['edges'] if e['source'] in ids and e['target'] in ids]
assert len(nodes)==10 and len(edges)==9
equipment_total=sum(n['node_type']=='equipment' for n in graph['nodes'])
panel={'source_graph_sha256':receipt['candidate_graph']['sha256'],'panel':'114','nodes':[{k:n[k] for k in ['candidate_id','bbox','equipment_type']} for n in nodes],
       'edges':[{'source':e['source'],'target':e['target'],'path_points':e['loose_edge_evidence']['path_points']} for e in edges]}
(OUT/'reader-panel114.json').write_text(json.dumps(panel,indent=2),encoding='utf-8')
narration=json.loads((WORK/'narration.json').read_text(encoding='utf-8'))
CAPTIONS=[
 ('Input → editable CAD → independent assessment','工艺输入 → 可编辑图纸 → 独立评测'),
 ('The same equipment. The same directed connection.','同一组设备，同一条有向连接。'),
 ('Symbols first. Then routes and labels.','设备符号 → 连接管线 → 完整标注。'),
 ('One process, distributed across 33 sheets.','一个工艺，分布在 33 张图纸之中。'),
 ('Follow S-120 from PFD-104 to PFD-114.','沿 S-120，从 PFD-104 追踪到 PFD-114。'),
 ('Read the CAD. Freeze the graph. Then compare.','独立读取 CAD，冻结候选图，再与任务比较。'),
 ('Four dimensions describe four different properties.','四个维度，分别衡量图纸的不同属性。'),
 ('Explore the drawings and their score evidence.','继续探索真实图纸与评分依据。')]

@lru_cache(None)
def font(n,bold=False,zh=False,mono=False):
    name='consola.ttf' if mono else ('msyhbd.ttc' if bold else 'msyh.ttc') if zh else ('seguisb.ttf' if bold else 'segoeui.ttf')
    return ImageFont.truetype('C:/Windows/Fonts/'+name,n)
def text(im,xy,s,n=30,color=FG,bold=False,zh=False,mono=False):
    ImageDraw.Draw(im).text(xy,s,font=font(n,bold,zh,mono),fill=color)
def rect(im,b,fill=PANEL,r=18,outline=None,width=2):ImageDraw.Draw(im).rounded_rectangle(b,r,fill,outline,width)
def ln(im,pts,c=ACC,w=3):ImageDraw.Draw(im).line(pts,fill=c,width=w,joint='curve')
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def lerp(a,b,p):return a+(b-a)*p
def fit(im,pic,box):
    x,y,w,h=box;s=min(w/pic.width,h/pic.height);nw,nh=round(pic.width*s),round(pic.height*s)
    pos=(round(x+(w-nw)/2),round(y+(h-nh)/2));cp=pic.resize((nw,nh),Image.Resampling.LANCZOS)
    im.paste(cp,pos,cp if cp.mode=='RGBA' else None);return pos,s
def dot(im,xy,color=ACC,r=8):
    x,y=xy;d=ImageDraw.Draw(im);d.ellipse((x-r-5,y-r-5,x+r+5,y+r+5),outline=color,width=2);d.ellipse((x-r,y-r,x+r,y+r),fill=color)
def path_motion(im,pts,progress,color=ACC,width=5):
    lengths=[math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1)];remaining=sum(lengths)*max(0,min(1,progress))
    visible=[pts[0]]
    for i,length in enumerate(lengths):
        if length==0:continue
        if remaining>=length:visible.append(pts[i+1]);remaining-=length
        else:
            p=remaining/length;visible.append((lerp(pts[i][0],pts[i+1][0],p),lerp(pts[i][1],pts[i+1][1],p)));break
    if len(visible)>1:ln(im,visible,color,width)
    dot(im,visible[-1],color)

@lru_cache(4)
def pdf(name):
    with fitz.open(C/'PDF'/f'{name}.pdf') as d:
        p=d[0];pix=p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)

@lru_cache(None)
def drawing_layer(kind):
    src=fitz.open(C/'PDF/PFD-114.pdf');p=src[0];out=fitz.open();q=out.new_page(width=p.rect.width,height=p.rect.height)
    sh=q.new_shape()
    for drawing in p.get_drawings():
        blue=drawing.get('color')==(0.,0.,1.)
        if (kind=='routes')!=blue:continue
        for item in drawing['items']:
            op,*v=item
            if op=='l':sh.draw_line(*v)
            elif op=='c':sh.draw_bezier(*v)
            elif op=='re':sh.draw_rect(v[0])
            elif op=='qu':sh.draw_quad(v[0])
        sh.finish(width=drawing.get('width') or 1,color=drawing.get('color'),fill=drawing.get('fill'),
            even_odd=drawing.get('even_odd',False),closePath=drawing.get('closePath',False),
            fill_opacity=drawing.get('fill_opacity') if drawing.get('fill_opacity') is not None else 1,
            stroke_opacity=drawing.get('stroke_opacity') if drawing.get('stroke_opacity') is not None else 1,
            lineCap=max(drawing.get('lineCap') or (0,0,0)),lineJoin=drawing.get('lineJoin') or 0,dashes=drawing.get('dashes'))
    sh.commit()
    pix=q.get_pixmap(matrix=fitz.Matrix(2,2),alpha=True)
    im=Image.frombytes('RGBA',(pix.width,pix.height),pix.samples);out.close();src.close();return im

def camera(im,source,crop,box):
    # Crops are in native PDF points; the source images have two pixels per point.
    x0,y0,x1,y1=crop;part=source.crop(tuple(round(v*2) for v in crop));pos,s=fit(im,part,box)
    return lambda x,y:(pos[0]+(x-x0)*2*s,pos[1]+(y-y0)*2*s)

@lru_cache(6)
def native_crop(name,crop):
    with fitz.open(C/'PDF'/f'{name}.pdf') as d:
        px=d[0].get_pixmap(matrix=fitz.Matrix(6,6),clip=fitz.Rect(crop),alpha=False)
        return Image.frombytes('RGB',(px.width,px.height),px.samples)

def detail_camera(im,name,crop,box):
    pos,s=fit(im,native_crop(name,crop),box)
    return lambda x,y:(pos[0]+(x-crop[0])*6*s,pos[1]+(y-crop[1])*6*s)

def chrome(index):
    im=Image.new('RGB',(W,H),BG);text(im,(58,32),'PFD',32,FG,True);text(im,(140,41),'AGENT / BENCH',19,SUB,True)
    stages=['PROCESS DATA','PFD-AGENT','PFD-BENCH'];active=0 if index<2 else 1 if index<5 else 2
    for i,s in enumerate(stages):
        x=670+i*310;text(im,(x,42),s,20,ACC if i==active else SUB,True)
        if i<2:ln(im,[(x+202,56),(x+260,56)],'#314955',2)
    text(im,(1570,44),'A06 · VISUAL WALKTHROUGH',17,SUB)
    ln(im,[(55,91),(1865,91)],'#2a414b',1)
    text(im,(62,966),CAPTIONS[index][0],33,FG,True)
    text(im,(64,1018),CAPTIONS[index][1],27,SUB,zh=True)
    return im

def heading(im,kicker,headline):text(im,(62,122),kicker,18,ACC,True);text(im,(60,153),headline,44,FG,True)
def small_label(im,xy,s):
    x,y=xy;width=ImageDraw.Draw(im).textlength(s,font=font(21,True))+28
    rect(im,(x,y,x+width,y+40),PANEL,8);text(im,(x+14,y+6),s,21,ACC,True)
def paper(im,box):x,y,w,h=box;rect(im,(x,y,x+w,y+h),'#ffffff',16)

SHEETS=sorted((C/'PDF').glob('PFD-1*.pdf'))
MOSAIC=Image.new('RGB',(1820,650),BG)
for i,p in enumerate(SHEETS):
    x=(i%11)*165;y=(i//11)*216;rect(MOSAIC,(x,y,x+153,y+204),'white',9)
    with fitz.open(p) as d:
        px=d[0].get_pixmap(matrix=fitz.Matrix(.35,.35),alpha=False)
        thumb=Image.frombytes('RGB',(px.width,px.height),px.samples)
    fit(MOSAIC,thumb,(x+5,y+8,143,165));text(MOSAIC,(x+32,y+179),p.stem,19,'#324653',True)

def bench_geometry(im,box,progress=1):
    x,y,w,h=box;bounds=[11880,-1410,12400,-940]
    sc=min(w/(bounds[2]-bounds[0]),h/(bounds[3]-bounds[1]));ox=x+(w-sc*(bounds[2]-bounds[0]))/2;oy=y+(h-sc*(bounds[3]-bounds[1]))/2
    def tr(p):return ox+(p[0]-bounds[0])*sc,oy+(bounds[3]-p[1])*sc
    for e in edges:
        pts=e['loose_edge_evidence']['path_points']
        if len(pts)>1:ln(im,[tr(p) for p in pts],'#6b8590',2)
    count=max(1,round(len(nodes)*progress))
    for i,n in enumerate(sorted(nodes,key=lambda n:(-n['bbox'][3],n['bbox'][0]))[:count]):
        b=n['bbox'];u=tr((b[0],b[3]));v=tr((b[2],b[1]));rect(im,(*u,*v),'#d9f5ee',4,TEAL:='#0d8578',2)
        # Keep the measured boxes in their native positions; a compact ID avoids
        # overlapping type labels on densely spaced equipment.
        label=str(i+1)
        text(im,(u[0]+3,u[1]+1),label,14,'#175d53',True)
    return tr

def render(t):
    idx=max(i for i,s in enumerate(narration) if t>=s['start']);s=narration[idx];p=(t-s['start'])/(s['end']-s['start']);im=chrome(idx)
    if idx==0:
        text(im,(65,193),'From process data',58,FG,True);text(im,(65,270),'to readable CAD.',58,ACC,True)
        text(im,(68,376),'GENERATE  /  READ  /  ASSESS',22,SUB,True)
        text(im,(68,565),'Real drawings.',40,FG,True);text(im,(68,625),'Traceable scores.',40,FG,True)
        text(im,(68,818),'Original CAD · Animated explanation',21,SUB)
        paper(im,(780,145,1080,750));camera(im,pdf('PFD-114'),(205,120,990,715),(800,164,1040,712))
        small_label(im,(808,169),'PFD-114')
    elif idx==1:
        heading(im,'01 / INPUT','A connection in the data becomes a connection in CAD.')
        text(im,(66,289),'process.xml → CAD IDs',26,ACC,True)
        for i,(label,value) in enumerate([('EQUIPMENT','M-101  →  SEP-101'),('STREAM','S-030'),('SOURCE ID','A100.A100DRYR.102')]):
            y=368+i*129;text(im,(66,y),label,17,SUB,True);text(im,(65,y+32),value,28 if i<2 else 23,FG,True)
        ln(im,[(65,797),(430,797)],'#2a414b',2);text(im,(66,817),'Mapped names. Preserved direction.',22,SUB)
        paper(im,(500,263,1362,638));tr=detail_camera(im,'PFD-114',(330,192,525,286),(529,289,1304,584))
        pts=[tr(424.16,248.24),tr(482.48,248.24),tr(482.48,244.4),tr(492.56,244.4)]
        if p>.24:path_motion(im,pts,ease((p-.24)/.56),'#008d76',5)
    elif idx==2:
        heading(im,'02 / GENERATION','Watch the drawing take shape.')
        for i,label in enumerate(['PLACE SYMBOLS','CONNECT PORTS','ADD LABELS']):
            x=63+i*278;active=min(2,int(p*3))==i;text(im,(x,235),label,21,ACC if active else SUB,True)
            if active:ln(im,[(x,269),(x+210,269)],ACC,3)
        text(im,(1440,238),'Saved geometry · animated reveal',19,SUB)
        paper(im,(60,293,1802,615))
        # Native vector paths are separated by original stroke color, then restored to the full PDF.
        crop=(180,110,1040,715);target=(83,311,1756,575)
        camera(im,drawing_layer('body'),crop,target)
        if p>.25:
            route=drawing_layer('routes').copy();route.putalpha(route.getchannel('A').point(lambda v:round(v*ease((p-.25)/.23))))
            camera(im,route,crop,target)
        if p>.57:
            overlay=im.copy();camera(overlay,pdf('PFD-114'),crop,target);im=Image.blend(im,overlay,ease((p-.57)/.22))
        small_label(im,(86,318),'PFD-114 / 10 equipment nodes')
    elif idx==3:
        heading(im,'03 / SCALE','One connected process. Thirty-three sheets.')
        # Scroll a real sheet mosaic gently; all images belong to the scored package.
        im.paste(MOSAIC,(54,254))
        focus=min(32,int(p*33));x=54+(focus%11)*165;y=254+(focus//11)*216
        ImageDraw.Draw(im).rounded_rectangle((x-2,y-2,x+155,y+206),10,outline=ACC,width=5)
        text(im,(66,914),'445 input nodes  ·  656 process streams  ·  DWG / DXF / PDF',21,SUB)
    elif idx==4:
        heading(im,'04 / CROSS-SHEET CONTINUITY','A page boundary is not the end of a stream.')
        left=(62,279,824,581);right=(1040,279,824,581);paper(im,left);paper(im,right)
        text(im,(89,302),'PFD-104  /  OUT',28,'#173642',True);text(im,(1067,302),'PFD-114  /  IN',28,'#173642',True)
        tl=detail_camera(im,'PFD-104',(408,320,564,378),(89,392,766,310))
        tr=detail_camera(im,'PFD-114',(203,581,395,682),(1066,373,771,407))
        small_label(im,(91,786),'TO PFD-114 / S-120');small_label(im,(1067,786),'FROM PFD-104 / S-120')
        x0,y0=tl(459.8,350.72);x1,y1=tl(514.52,350.72);x2,y2=tr(296.36,618.68);x3,y3=tr(351.08,618.68)
        # Explanatory trace follows the two native terminal halves and their recorded sheet pairing.
        pts=[(x0,y0),(x1,y1),(945,y1),(975,y2),(x2,y2),(x3,y3)]
        path_motion(im,pts,ease(p*.95), '#0ca892',5)
        rect(im,(904,449,1021,497),PANEL,9);text(im,(917,458),'S-120',25,ACC,True)
    elif idx==5:
        heading(im,'05 / INDEPENDENT READING','From delivered geometry to a frozen candidate graph.')
        paper(im,(62,274,838,590));paper(im,(1024,274,838,590))
        text(im,(88,294),'DELIVERED CAD',22,'#173642',True);text(im,(1050,294),'BENCH-EXTRACTED OBJECTS',22,'#173642',True)
        camera(im,pdf('PFD-114'),(180,110,1040,715),(80,346,799,495));bench_geometry(im,(1052,356,780,450),ease(p*1.7))
        path_motion(im,[(921,553),(1001,553)],(p*1.5)%1,ACC,3)
        text(im,(69,890),'PFD-114 / native PDF export',22,SUB);text(im,(1036,890),f'10 objects on this page  ·  {equipment_total} in the master DXF',22,ACC)
        if p>.73:small_label(im,(1287,797),'GRAPH FROZEN BEFORE TASK MATCHING')
    elif idx==6:
        heading(im,'06 / FOUR-DIMENSION ASSESSMENT','Each score answers a different question.')
        paper(im,(62,270,1120,639));camera(im,pdf('PFD-114'),(180,110,1040,715),(80,293,1082,596))
        labels=[('Inventory F1','Are equipment types accounted for?','equipment_extraction_score'),('Symbol','Is symbol geometry consistent?','symbol_score'),('Matched topology','Are matched connections preserved?','topology_score'),('Local layout','How are local objects arranged?','layout_score')]
        for i,(label,question,key) in enumerate(labels):
            x,y=1240,284+i*153;active=min(3,int(p*4))==i
            text(im,(x,y),label,29,COLORS[i],True);text(im,(1690,y-10),f'{receipt["scores"][key]:.2f}',47,COLORS[i],True)
            text(im,(x,y+51),question,21,SUB);ln(im,[(x,y+96),(1845,y+96)],'#2a414b',7)
            ln(im,[(x,y+96),(x+605*receipt['scores'][key]/100*ease(p*4-i),y+96)],COLORS[i],7)
            if active:ImageDraw.Draw(im).ellipse((1204,y+14,1217,y+27),fill=COLORS[i])
        text(im,(67,918),'A06 package-level scores / 0–100 / reader r010',19,SUB)
    else:
        text(im,(64,173),'Draw it.',73,FG,True);text(im,(64,259),'Read it.',73,FG,True);text(im,(64,345),'Measure it.',73,ACC,True)
        text(im,(67,512),'PFD-Agent & PFD-Bench',31,FG,True);text(im,(67,571),'Explore the complete project',27,SUB)
        text(im,(67,696),'zihengfan07.github.io/',28,ACC,True);text(im,(67,738),'pfd-agent-bench/',28,ACC,True)
        paper(im,(865,159,994,738));camera(im,pdf('PFD-114'),(180,110,1040,715),(884,180,956,696))
        text(im,(67,852),'Shanghai Jiao Tong University',21,SUB)
    ln(im,[(62,1064),(1858,1064)],'#27414d',3);ln(im,[(62,1064),(62+1796*t/DURATION,1064)],ACC,3)
    return im

TIMES=[3,10,19,23,27,32,43,54,65]
for t in TIMES:
    render(t).save(WORK/f'frame-{t:02d}.jpg',quality=94)
    print('STILL',t,flush=True)
contact=Image.new('RGB',(1440,810),BG)
for i,t in enumerate(TIMES):fit(contact,render(t),((i%3)*480,(i//3)*270,480,270))
contact.save(WORK/'storyboard.jpg',quality=94)
render(3).save(OUT/'poster-v2.jpg',quality=94)
if a.stills:print('STILLS_READY',flush=True);raise SystemExit()

ff=a.ffmpeg
# Align the two locally synthesized narration tracks to the same visual edit.
for lang in ['en','zh']:
    cmd=[ff,'-y','-loglevel','error'];filters=[]
    for i,s in enumerate(narration):
        wav=WORK/f'{lang}-{i}.wav'
        with wave.open(str(wav),'rb') as f:duration=f.getnframes()/f.getframerate()
        target=s['end']-s['start'];rate=max(1,duration/(target-.55))
        assert rate<1.65,(lang,i,duration,target)
        cmd+=['-i',str(wav)]
        filters.append(f'[{i}:a]atempo={rate:.6f},adelay=160,apad,atrim=duration={target},asetpts=PTS-STARTPTS[a{i}]')
    filters.append(''.join(f'[a{i}]' for i in range(len(narration)))+f'concat=n={len(narration)}:v=0:a=1,loudnorm=I=-18:TP=-2:LRA=8[out]')
    cmd+=['-filter_complex',';'.join(filters),'-map','[out]','-ar','48000',str(WORK/f'narration-{lang}.wav')]
    subprocess.run(cmd,check=True)

silent=WORK/'visuals-v2.mp4'
cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
with (WORK/'encode.log').open('wb') as log:
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
    for n in range(FPS*DURATION):
        p.stdin.write(render(n/FPS).tobytes())
        if n%(10*FPS)==0:print(f'ENCODING {n//FPS}/{DURATION}s',flush=True)
    p.stdin.close();assert p.wait()==0
for lang in ['en','zh']:
    subprocess.run([ff,'-y','-loglevel','error','-i',str(silent),'-i',str(WORK/f'narration-{lang}.wav'),'-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart','-t',str(DURATION),str(OUT/f'pfd-workflow-demo-v2-{lang}.mp4')],check=True)
print('VIDEOS_READY',flush=True)
