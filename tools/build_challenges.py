"""Build traceable challenge figures from the supplied CAD review collection.

Original previews are embedded unchanged in SVG viewports; overlays and graph
views are illustrative annotations derived from case.json, not Bench outputs.
Run from the website staging folder with Python + networkx + numpy.
"""
import base64
import hashlib
import html
import json
from pathlib import Path
import networkx as nx

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'tools': ROOT = ROOT.parent
DIST = ROOT / 'dist' if (ROOT / 'dist').is_dir() else ROOT
CASE = DIST / 'review/data/cases/HARD_A06'
OUT = DIST / 'assets/challenges'
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads((CASE/'case.json').read_text(encoding='utf-8'))
sheets = {s['id']: s for s in data['sheets']}
sources = {}
ink, muted, teal, purple, blue = '#162c37', '#526575', '#087b76', '#8956b2', '#2458b4'

def text(x, y, value, size=20, color=ink, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(str(value))}</text>'

def rect(x, y, w, h, fill='#fff', stroke='#dce5e9', radius=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'

def line(x1,y1,x2,y2,color='#c1d6d9',width=1,arrow=False):
    return f'<path d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}" fill="none" stroke="{color}" stroke-width="{width}"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>'

def uri(path):
    blob = path.read_bytes()
    sources[str(path.relative_to(DIST)).replace('\\','/')] = hashlib.sha256(blob).hexdigest()
    return 'data:image/webp;base64,' + base64.b64encode(blob).decode()

def image(sheet, x,y,w,h,crop=None,thumb=False):
    path=CASE/'previews'/f'{sheet}{".thumb" if thumb else ""}.webp'
    if not crop:
        return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri(path)}" preserveAspectRatio="xMidYMid meet"/>'
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{" ".join(map(str,crop))}" preserveAspectRatio="xMidYMid meet" overflow="hidden"><image width="4800" height="3394" href="{uri(path)}"/></svg>'

def save(name, lang, width, height, body, title, desc):
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="{teal}"/></marker></defs>
<rect width="100%" height="100%" fill="#fff"/>
<g font-family="Segoe UI,Microsoft YaHei,Arial,sans-serif">{''.join(body)}</g></svg>'''
    (OUT/f'{name}-{lang}.svg').write_text(svg,encoding='utf-8')

# Process graph includes junctions referenced by the source stream index.
graph=nx.DiGraph()
graph.add_nodes_from(e['id'] for e in data['equipment'])
for stream in data['streams']:
    a,b=stream['source']['id'],stream['target']['id']
    if a and b: graph.add_edge(a,b,id=stream['id'])
position=nx.spring_layout(graph,seed=17,iterations=150)
xs=[float(p[0]) for p in position.values()]; ys=[float(p[1]) for p in position.values()]
position={n:(45+(float(p[0])-min(xs))/(max(xs)-min(xs))*490,
             121+(float(p[1])-min(ys))/(max(ys)-min(ys))*355) for n,p in position.items()}
largest=max(nx.strongly_connected_components(graph),key=len)
cycle=['J-002','J-003','E-145','T-102','UNK-115','P-104']
cycle_edges=[]
for a,b in zip(cycle,cycle[1:]+cycle[:1]):
    st=next(s for s in data['streams'] if s['source']['id']==a and s['target']['id']==b)
    cycle_edges.append(st)
assert [s['id'] for s in cycle_edges]==['S-199','S-200','S-201','S-196','S-197','S-198']
assert sheets['PFD-102']['connectors'][next(i for i,c in enumerate(sheets['PFD-102']['connectors']) if c['stream_id']=='S-117')]['direction']=='incoming'

for lang in ['en','zh']:
    tr=lambda en,zh: zh if lang=='zh' else en
    title=tr('One process, many coupled drawings','一个流程，多页协同')
    b=[text(28,39,title,27,weight=650),text(28,73,tr('A06 · 445 indexed equipment nodes · 656 streams · 34 CAD sheets','A06 · 445 个索引设备节点 · 656 条物流 · 34 张 CAD 图纸'),18,muted),line(28,91,1172,91)]
    b += [rect(24,108,538,405,'#f8fbfc',radius=6)]
    for a,c in graph.edges:
        b.append(line(*position[a],*position[c], '#af88c6' if a in largest and c in largest else '#bdd3d6',1.1))
    for node,(x,y) in position.items():
        color=purple if node in largest else teal
        b.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.1" fill="{color}"/>')
    b += [text(38,538,tr('Exported process relations','导出的流程连接关系'),19,weight=600),text(38,564,tr('Purple: 46 nodes in one strongly connected component','紫色：同一强连通分量中的 46 个节点'),16,muted)]
    for i,sheet in enumerate(data['sheets']):
        col,row=i%6,i//6; x=602+col*94; y=111+row*73
        b.extend([rect(x,y,87,62,stroke='#cddde2',radius=2),image(sheet['id'],x+1,y+1,85,49,thumb=True),text(x+43.5,y+58,sheet['id'],10.5,muted,anchor='middle')])
    b.append(text(602,564,tr('All 34 delivered sheets, not a single-page illustration','完整的 34 张交付图纸，而非单页示意'),17,weight=600))
    b += [line(28,584,1172,584),text(28,609,tr('Network: source index including junctions; boundary streams omitted. Thumbnails: original CAD previews.','网络来自含分流节点的源索引，未画外部边界物流；缩略图为原始 CAD 预览。'),16,muted)]
    save('scale',lang,1200,630,b,title,'HARD_A06 source-index process graph and all 34 unmodified CAD sheet thumbnails.')

    title=tr('A cycle does not end at a page boundary','循环不会在页面边界处结束')
    b=[text(26,40,title,26,weight=650),text(26,75,tr('A06 · one six-node directed cycle in the source index','A06 · 源索引中的一个六节点有向循环'),17,muted),rect(25,103,454,368,'#f3f9f8'),rect(494,103,201,368,'#f7f4fb')]
    b += [text(47,133,'PFD-122',18,teal,650),text(516,133,'PFD-123',18,purple,650)]
    xy={'J-002':(105,209),'J-003':(293,209),'E-145':(430,209),'T-102':(592,209),'UNK-115':(430,385),'P-104':(253,385)}
    for i,st in enumerate(cycle_edges):
        a,c=cycle[i],cycle[(i+1)%6]; x1,y1=xy[a]; x2,y2=xy[c]
        if a=='T-102':
            b.append(f'<path d="M592 239V385H485" stroke="{teal}" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>')
            b.append(text(605,310,st['id'],15,teal))
        elif c=='J-002':
            b.append(f'<path d="M{x1-55} {y1}H105V239" stroke="{teal}" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>')
            b.append(text(128,364,st['id'],15,teal))
        else:
            if x1==x2: y1+=30; y2-=30
            elif x2>x1: x1+=55; x2-=55
            else: x1-=55; x2+=55
            b.append(line(x1,y1,x2,y2,teal,2.5,True))
            b.append(text((x1+x2)/2+ (33 if x1==x2 else 0),(y1+y2)/2-(40 if y1==y2 else 13),st['id'],15,teal,anchor='middle'))
    for n,(x,y) in xy.items():
        b += [rect(x-55,y-27,110,54,stroke=purple if x>490 else teal,radius=5),text(x,y+6,n,18,weight=600,anchor='middle')]
    b += [text(26,509,tr('Stream identity and direction must survive both page crossings.','两次跨页后，物流的身份与方向都需要保持。'),18,weight=500),text(26,543,tr('Graph schematic from supplied metadata; inspect the CAD separately.','图结构由随包元数据生成；CAD 图纸可独立查看。'),15,muted)]
    save('cycle',lang,720,565,b,title,'Actual source-index cycle: J-002 to J-003 to E-145 to T-102 to UNK-115 to P-104 to J-002. Page assignment follows supplied layout metadata.')

    title=tr('One stream, two sheets, a specific inlet','同一物流，两张图纸，一个明确的入口')
    b=[text(28,39,title,27,weight=650),text(28,75,tr('A06 · S-117 links the R-112 outlet to the M-117 upper inlet','A06 · S-117 从 R-112 出口连接到 M-117 上部入口'),18,muted)]
    b += [rect(25,98,550,411),rect(625,98,550,411),text(44,129,'PFD-120 · R-112',19,teal,650),text(644,129,'PFD-102 · M-117',19,teal,650)]
    b += [image('PFD-120',40,145,520,350,[2050,1400,1450,1000]),image('PFD-102',640,145,520,350,[1550,1290,1300,875])]
    # Coordinate-preserving overlay circles at the connector and equipment inlet.
    # Image fit is xMidYMid meet, so use the same viewport transform.
    for x,y,w,h,crop,points in [(40,145,520,350,[2050,1400,1450,1000],[(2584.547,2347.47)]),(640,145,520,350,[1550,1290,1300,875],[(1991.56,1438.006),(1991.56,1620.015),(1991.56,1736.298),(2277.38,1678.157)])]:
        a,z,cw,ch=crop; scale=min(w/cw,h/ch); ox=x+(w-cw*scale)/2; oy=y+(h-ch*scale)/2
        for px,py in points:
            b.append(f'<circle cx="{ox+(px-a)*scale:.3f}" cy="{oy+(py-z)*scale:.3f}" r="9" fill="none" stroke="{teal}" stroke-width="2.2"/>')
    b += [line(579,305,617,305,teal,2.5,True),rect(25,527,1150,71,'#edf7f5',stroke='#b9dcd5')]
    b += [text(45,556,tr('R-112 outlet','R-112 出口'),18,weight=600),text(328,556,'S-117',18,teal,650),line(215,551,300,551,teal,2,True),line(404,551,483,551,teal,2,True),text(503,556,tr('M-117 upper inlet','M-117 上部入口'),18,weight=600),text(45,583,tr('M-117 also receives S-118 at its lower inlet and emits S-119 at its outlet.','M-117 的下部入口另接收 S-118，出口则连接 S-119。'),17,muted)]
    b += [text(28,629,tr('Original CAD crops, unchanged. Circles locate supplied connector / port coordinates; they are not Bench detections.','原始 CAD 裁切展示，内容未改动。圆圈标出随包接口与端口坐标，不代表 Bench 检测。'),16,muted)]
    save('interfaces',lang,1200,653,b,title,'Unmodified original CAD crops from HARD_A06 PFD-120 and PFD-102, linked by stream S-117. Annotation coordinates are supplied metadata.')

record={
 'schema':'pfd-website-challenge-figures.v1','case':'HARD_A06',
 'source_case_sha256':hashlib.sha256((CASE/'case.json').read_bytes()).hexdigest(),
 'sources':sources,'counts':data['stats'],
 'network':{'vertices_including_junctions':len(graph),'internal_edges_after_DiGraph_coalescing':graph.number_of_edges(),'largest_scc_nodes':len(largest),'layout_seed':17},
 'cycle_nodes':cycle,'cycle_streams':[s['id'] for s in cycle_edges],
 'interface':{'stream':'S-117','source':'R-112','source_sheet':'PFD-120','target':'M-117','target_sheet':'PFD-102','target_port':'upper_inlet'},
 'interpretation':'Source-index and layout-metadata illustration; original previews are embedded unchanged. Not independent Bench extraction, engineering approval, or a new score.',
 'outputs':[p.name for p in sorted(OUT.glob('*.svg'))]
}
(OUT/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':record['outputs'],'network':record['network'],'source_images':len(sources)},ensure_ascii=False))
