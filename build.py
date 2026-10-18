#!/usr/bin/env python3
"""Build report.pdf and report.docx from content/report.md and local assets.
PDF uses WeasyPrint; DOCX uses python-docx. No network access is required.
"""
from __future__ import annotations
import csv, html, re, hashlib, json
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'content/report.md'
OUT_PDF=ROOT/'report.pdf'; OUT_DOCX=ROOT/'report.docx'
PAPER='#F3EBDD'; NAVY='#16243B'; RUST='#D45D45'; TEAL='#2D7775'; OCHRE='#D8A641'; MUTED='#667085'; LINE='#D6CCBA'
ACCENTS=[RUST,TEAL,OCHRE]

# -- generate technical diagrams only; no generated photographic/illustrative art --
def font(paths, size):
    for path in paths:
        if Path(path).exists():
            try: return ImageFont.truetype(path,size)
            except Exception: pass
    return ImageFont.load_default()

def draw_diagrams():
    ddir=ROOT/'images'/'figures'; ddir.mkdir(parents=True,exist_ok=True)
    sans=font(['/usr/share/fonts/opentype/inter/Inter-Regular.otf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],26)
    bold=font(['/usr/share/fonts/opentype/inter/Inter-SemiBold.otf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],28)
    small=font(['/usr/share/fonts/opentype/inter/Inter-Regular.otf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],21)
    def centered(draw, box, text, f, fill):
        x1,y1,x2,y2=box; bb=draw.multiline_textbbox((0,0),text,font=f,spacing=6,align='center')
        w=bb[2]-bb[0]; h=bb[3]-bb[1]
        draw.multiline_text((x1+(x2-x1-w)/2,y1+(y2-y1-h)/2),text,font=f,fill=fill,spacing=6,align='center')
    def box(draw, xy, text, color, textcolor=NAVY):
        draw.rounded_rectangle(xy,radius=22,fill=color,outline=NAVY,width=3); centered(draw,xy,text,bold,textcolor)
    def arrow(draw, a, b, color=NAVY):
        draw.line([a,b],fill=color,width=6)
        import math
        ang=math.atan2(b[1]-a[1],b[0]-a[0]); L=18
        p1=(b[0]-L*math.cos(ang-.55),b[1]-L*math.sin(ang-.55)); p2=(b[0]-L*math.cos(ang+.55),b[1]-L*math.sin(ang+.55))
        draw.polygon([b,p1,p2],fill=color)
    # Hybrid routing diagram
    im=Image.new('RGB',(1600,520),PAPER); dr=ImageDraw.Draw(im)
    box(dr,(40,190,270,320),'Request', '#FFFFFF')
    box(dr,(340,190,590,320),'Policy +\nrouter',OCHRE)
    box(dr,(700,65,1030,185),'Local model\n+ local RAG',TEAL,'#FFFFFF')
    box(dr,(700,335,1030,455),'Approved cloud\nadapter + budget',RUST,'#FFFFFF')
    box(dr,(1150,190,1550,320),'Validate → approve\n→ tools + trace','#FFFFFF')
    arrow(dr,(270,255),(340,255)); arrow(dr,(590,220),(700,125)); arrow(dr,(590,290),(700,395)); arrow(dr,(1030,125),(1150,220)); arrow(dr,(1030,395),(1150,290))
    dr.text((704,15),'SENSITIVE / OFFLINE',font=small,fill=TEAL); dr.text((704,468),'HARD TASK, ALLOWED BY POLICY',font=small,fill=RUST)
    im.save(ddir/'hybrid_architecture.png',dpi=(200,200),optimize=True)
    # API tool round-trip
    im=Image.new('RGB',(1600,470),PAPER); dr=ImageDraw.Draw(im)
    labels=[('Client', '#FFFFFF'),('Model API',RUST),('Tool policy',OCHRE),('Tool result',TEAL),('Model API',RUST)]
    xs=[35,350,665,980,1295]
    for x,(label,c) in zip(xs,labels): box(dr,(x,145,x+255,285),label,c,'#FFFFFF' if c in (RUST,TEAL) else NAVY)
    for x in xs[:-1]: arrow(dr,(x+255,215),(x+315,215))
    dr.text((360,70),'tool call',font=small,fill=NAVY); dr.text((674,320),'Validate name + arguments before execution',font=small,fill=NAVY)
    im.save(ddir/'cloud_tool_loop.png',dpi=(200,200),optimize=True)
    # MCP lifecycle
    im=Image.new('RGB',(1600,400),PAPER); dr=ImageDraw.Draw(im)
    labels=[('server/discover',RUST),('versions +\ncapabilities + identity',OCHRE),('each request has\n_meta metadata',TEAL),('tools/call →\nresult / error','#FFFFFF')]
    xs=[45,440,835,1230]
    for x,(label,c) in zip(xs,labels): box(dr,(x,130,x+315,260),label,c,'#FFFFFF' if c in (RUST,TEAL) else NAVY)
    for x in xs[:-1]: arrow(dr,(x+315,195),(x+395,195))
    dr.text((80,315),'2026-07-28 is stateless: no initialize/initialized handshake or Mcp-Session-Id.',font=small,fill=NAVY)
    im.save(ddir/'mcp_lifecycle.png',dpi=(200,200),optimize=True)

def slug(text:str)->str:
    s=re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')
    return 'h_'+s

def parse_blocks(text:str)->list[dict[str,Any]]:
    lines=text.splitlines(); i=0; blocks=[]; image_slot_index=0
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1; continue
        if line.strip()=='<!-- PAGEBREAK -->': blocks.append({'type':'pagebreak'}); i+=1; continue
        if line.startswith(':::image-slot'):
            brief=line[len(':::image-slot'):].strip().lstrip('|').strip()
            slot_id='cover' if image_slot_index==0 else f'ch{image_slot_index:02d}'
            blocks.append({'type':'image-slot','slot_id':slot_id,'brief':brief}); image_slot_index+=1; i+=1; continue
        if line.startswith(':::figure'):
            parts=[p.strip() for p in line[len(':::figure'):].split('|')]
            name=parts[1] if len(parts)>1 else 'hybrid_architecture'; cap=parts[2] if len(parts)>2 else name
            blocks.append({'type':'figure','name':name,'caption':cap}); i+=1
            if i<len(lines) and lines[i].strip()==':::': i+=1
            continue
        if line.strip()==':::deep-dive':
            i+=1; inner=[]
            while i<len(lines) and lines[i].strip()!=':::': inner.append(lines[i]); i+=1
            if i<len(lines): i+=1
            blocks.append({'type':'deep-dive','blocks':parse_blocks('\n'.join(inner))}); continue
        if line.startswith('```'):
            lang=line[3:].strip(); i+=1; code=[]
            while i<len(lines) and not lines[i].startswith('```'): code.append(lines[i]); i+=1
            if i<len(lines): i+=1
            blocks.append({'type':'code','lang':lang,'text':'\n'.join(code)}); continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?',c.replace(' ','')) for c in cells): rows.append(cells)
                i+=1
            blocks.append({'type':'table','rows':rows}); continue
        m=re.match(r'^(#{1,4})\s+(.*)$',line)
        if m:
            level=len(m.group(1)); title=m.group(2).strip()
            blocks.append({'type':'heading','level':level,'text':title,'id':slug(title)}); i+=1; continue
        if line.strip() in ('---','***','___'):
            blocks.append({'type':'rule'}); i+=1; continue
        if re.match(r'^\s*[-*+]\s+',line):
            items=[]
            while i<len(lines) and re.match(r'^\s*[-*+]\s+',lines[i]): items.append(re.sub(r'^\s*[-*+]\s+','',lines[i]).strip()); i+=1
            blocks.append({'type':'list','ordered':False,'items':items}); continue
        if re.match(r'^\s*\d+\.\s+',line):
            items=[]
            while i<len(lines) and re.match(r'^\s*\d+\.\s+',lines[i]): items.append(re.sub(r'^\s*\d+\.\s+','',lines[i]).strip()); i+=1
            blocks.append({'type':'list','ordered':True,'items':items}); continue
        if line.startswith('> '):
            vals=[]
            while i<len(lines) and lines[i].startswith('> '): vals.append(lines[i][2:].strip()); i+=1
            blocks.append({'type':'quote','text':' '.join(vals)}); continue
        # paragraph = join wrapped source lines until blank or another block starter
        para=[line.strip()]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','```',':::','|','> ')) and not re.match(r'^\s*([-*+]\s+|\d+\.\s+)',lines[i]) and lines[i].strip() not in ('---','***','___','<!-- PAGEBREAK -->'):
            para.append(lines[i].strip()); i+=1
        blocks.append({'type':'paragraph','text':' '.join(para)})
    return blocks

def get_slot_meta(slot_id:str, brief:str='')->dict[str,str]:
    manifest=ROOT/'images'/'slots'/'manifest.csv'
    try:
        with manifest.open(newline='',encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row.get('slot_id')==slot_id:
                    return {k:(v or '') for k,v in row.items()}
    except FileNotFoundError:
        pass
    clean=brief.split('·')[1].split('·')[0].strip() if '·' in brief else brief.strip()
    return {'slot_id':slot_id,'alt_text':clean,'caption':clean}

def get_slot_asset(slot_id:str)->Path|None:
    slots=ROOT/'images'/'slots'
    for ext in ('.jpg','.jpeg','.png','.webp'):
        candidate=slots/f'{slot_id}{ext}'
        if candidate.exists(): return candidate
    return None

def inline_html(s:str)->str:
    s=html.escape(s,quote=False)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    # markdown links
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{html.escape(m.group(2),quote=True)}">{m.group(1)}</a>',s)
    # external raw URLs that are not already part of anchors
    s=re.sub(r'(?<![="/])(https?://[^\s<)]+)',r'<a href="\1">\1</a>',s)
    return s

def block_html(b:dict, in_deep=False)->str:
    t=b['type']
    if t=='pagebreak': return '<div class="page-break"></div>'
    if t=='heading':
        tag='h1' if b['level']==1 else 'h2' if b['level']==2 else 'h3'
        return f'<{tag} id="{b["id"]}">{inline_html(b["text"])}</{tag}>'
    if t=='paragraph': return f'<p>{inline_html(b["text"])}</p>'
    if t=='table':
        if not b['rows']: return ''
        rows=b['rows']; out=['<table>']
        for ri,row in enumerate(rows):
            out.append('<tr>')
            tag='th' if ri==0 else 'td'
            for c in row: out.append(f'<{tag}>{inline_html(c)}</{tag}>')
            out.append('</tr>')
        out.append('</table>'); return ''.join(out)
    if t=='list':
        tag='ol' if b['ordered'] else 'ul'
        return '<'+tag+'>'+''.join(f'<li>{inline_html(x)}</li>' for x in b['items'])+'</'+tag+'>'
    if t=='code':
        lang=html.escape(b.get('lang','text'))
        return f'<pre><code class="language-{lang}">{html.escape(b["text"])}</code></pre>'
    if t=='quote': return f'<blockquote>{inline_html(b["text"])}</blockquote>'
    if t=='rule': return '<hr/>'
    if t=='image-slot':
        meta=get_slot_meta(b['slot_id'],b['brief']); asset=get_slot_asset(b['slot_id'])
        if asset:
            rel=asset.relative_to(ROOT).as_posix(); alt=html.escape(meta.get('alt_text') or meta.get('caption') or b['brief'],quote=True)
            caption=inline_html(meta.get('caption') or b['brief'])
            return f'<figure class="slot-photo"><img src="{rel}" alt="{alt}"/><figcaption>{caption}</figcaption></figure>'
        return f'<div class="image-slot"><span class="slot-label">REAL IMAGE SLOT · NOT DOWNLOADED</span><div>{inline_html(b["brief"])}</div><small>Slot ID: {html.escape(b["slot_id"])}</small></div>'
    if t=='figure':
        path=ROOT/'images'/'figures'/f'{b["name"]}.png'
        if not path.exists(): return f'<p><em>Diagram unavailable: {html.escape(b["name"])}</em></p>'
        rel=path.relative_to(ROOT).as_posix()
        alt=html.escape(b['caption'],quote=True)
        return f'<figure><img src="{rel}" alt="{alt}"/><figcaption>{inline_html(b["caption"])}</figcaption></figure>'
    if t=='deep-dive': return '<aside class="deep-dive">'+''.join(block_html(x,True) for x in b['blocks'])+'</aside>'
    return ''

def build_html(blocks:list[dict])->str:
    head='''<!doctype html><html><head><meta charset="utf-8"/><style>
@font-face{font-family:EBGaramond;src:url(file:///usr/share/fonts/truetype/ebgaramond/EBGaramond12-Regular.ttf)}
@font-face{font-family:Inter;src:url(file:///usr/share/fonts/opentype/inter/Inter-Regular.otf)}
@font-face{font-family:Inter;src:url(file:///usr/share/fonts/opentype/inter/Inter-Bold.otf);font-weight:700}
@font-face{font-family:Mono;src:url(file:///usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf)}
@page{size:A4;margin:12mm 13mm 14mm;background:#F3EBDD;@bottom-left{content:"THE MODERN LLM STACK · 18 OCT 2026";font-family:Inter;font-size:6.5pt;color:#667085}@bottom-right{content:counter(page) " / " counter(pages);font-family:Inter;font-size:7pt;color:#16243B}}
*{box-sizing:border-box}body{margin:0;color:#16243B;background:#F3EBDD;font-family:Inter,Arial,sans-serif;font-size:8.4pt;line-height:1.30}
h1,h2,h3{font-family:EBGaramond,Georgia,serif;color:#16243B;line-height:1.02;break-after:avoid}
h1{font-size:21pt;margin:0 0 7pt;border-bottom:1.2pt solid #D45D45;padding-bottom:4pt}
h2{font-size:13pt;margin:8pt 0 3pt}
h3{font-family:Inter,sans-serif;font-size:8.6pt;font-weight:700;margin:5pt 0 2pt;color:#2D7775;break-after:avoid}
p{margin:0 0 4pt;orphans:2;widows:2}strong{font-weight:700}a{color:#2D7775;text-decoration:underline}ul,ol{margin:2pt 0 4pt 14pt;padding:0}li{margin:0 0 2pt}table{width:100%;border-collapse:collapse;margin:4pt 0 6pt;font-size:7.2pt;line-height:1.18;break-inside:avoid}th{background:#16243B;color:#F3EBDD;text-align:left;font-weight:700}td,th{border:0.5pt solid #D6CCBA;padding:3pt 4pt;vertical-align:top}tr:nth-child(even) td{background:#FAF6EE}code{font-family:Mono,monospace;font-size:0.9em;background:#EDE7DB;padding:0 1.5pt}pre{font-family:Mono,monospace;font-size:6.4pt;line-height:1.18;background:#172338;color:#F3EBDD;padding:6pt 8pt;margin:3pt 0 2pt;white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid}pre code{background:transparent;color:inherit;padding:0;font-size:inherit}blockquote{margin:4pt 0;padding:5pt 8pt;border-left:3pt solid #D8A641;background:#F8F1E3;font-family:EBGaramond,serif;font-size:11pt}hr{border:0;border-top:1pt solid #D6CCBA;margin:6pt 0}.page-break{break-before:page;page-break-before:always;height:0}.image-slot{margin:5pt 0 6pt;padding:6pt 8pt;background:#F4EBD9;border:1pt dashed #D45D45;min-height:22pt;color:#16243B;font-size:7.0pt;break-inside:avoid}.slot-label{font-size:5.8pt;letter-spacing:1px;color:#D45D45;font-weight:700;display:block;margin-bottom:2pt}figure{margin:3pt auto 5pt;text-align:center;break-inside:avoid}figure img{width:100%;height:auto;max-height:47mm;object-fit:contain}.slot-photo img{max-height:42mm;object-fit:cover}.slot-photo figcaption{color:#16243B}figcaption{font-size:6.8pt;color:#667085;font-style:italic;margin-top:2pt}.deep-dive{background:#16243B;color:#F3EBDD;padding:7pt 9pt;margin:5pt 0;break-inside:avoid;border-left:4pt solid #D8A641}.deep-dive h2,.deep-dive h3{color:#F3EBDD}.deep-dive p{color:#F3EBDD}.deep-dive code{background:#30415A;color:#F3EBDD}.deep-dive pre{background:#0D1727;border:0.5pt solid #5A687E}.cover-page{min-height:269mm;background:#F3EBDD;padding:18mm 14mm 12mm;border-top:8pt solid #16243B;position:relative}.cover-page h1{font-size:43pt;line-height:0.95;border:0;margin:15mm 0 5mm;max-width:140mm}.cover-page h2{font-size:18pt;color:#D45D45;margin:0 0 12mm}.cover-page h3{font-size:9pt;color:#2D7775}.cover-page p{font-size:10pt;line-height:1.42;max-width:165mm;margin-bottom:7pt}.cover-page .image-slot{min-height:35mm;margin:12mm 0 8mm;padding:8mm 8mm}.cover-page .slot-label{font-size:7pt}.cover-page .page-break{display:none}.cover-page p:nth-of-type(1){font-size:12pt;font-weight:700}.cover-page h1#h_the-modern-llm-stack{letter-spacing:-1pt}.cover-page:after{content:"FIELD GUIDE / 2026";position:absolute;bottom:9mm;right:12mm;font-size:8pt;letter-spacing:2px;color:#667085}.cover-page table{font-size:8pt}.cover-page table td,.cover-page table th{padding:5pt} .chapter-jump{font-size:7.6pt}.chapter-jump a{display:inline}
</style></head><body>'''
    # Group cover until first pagebreak. Render normal content thereafter.
    out=[head]; cover=[]; seen_break=False
    for b in blocks:
        if b['type']=='pagebreak' and not seen_break:
            out.append('<section class="cover-page">'+''.join(block_html(x) for x in cover)+'</section><div class="page-break"></div>')
            seen_break=True; continue
        if not seen_break: cover.append(b)
        else: out.append(block_html(b))
    if not seen_break: out.append(''.join(block_html(x) for x in cover))
    out.append('</body></html>')
    return ''.join(out)

# DOCX utilities
def shade_cell(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=tcPr.find(qn('w:shd'))
    if shd is None: shd=OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'),fill.replace('#',''))

def set_cell_margins(cell, top=80, start=100, bottom=80, end=100):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr(); mar=tcPr.first_child_found_in('w:tcMar')
    if mar is None: mar=OxmlElement('w:tcMar'); tcPr.append(mar)
    for m,v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node=mar.find(qn('w:'+m))
        if node is None: node=OxmlElement('w:'+m); mar.append(node)
        node.set(qn('w:w'),str(v)); node.set(qn('w:type'),'dxa')

def add_bookmark(p, name, bid):
    start=OxmlElement('w:bookmarkStart'); start.set(qn('w:id'),str(bid)); start.set(qn('w:name'),name)
    end=OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'),str(bid))
    p._p.insert(0,start); p._p.append(end)

def add_hyperlink(paragraph, text, target, external=False, color='2D7775'):
    part=paragraph.part
    if external:
        rid=part.relate_to(target,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    else: rid=None
    hyperlink=OxmlElement('w:hyperlink')
    if external: hyperlink.set(qn('r:id'),rid)
    else: hyperlink.set(qn('w:anchor'),target.replace('#',''))
    run=OxmlElement('w:r'); rPr=OxmlElement('w:rPr')
    c=OxmlElement('w:color'); c.set(qn('w:val'),color); rPr.append(c)
    u=OxmlElement('w:u'); u.set(qn('w:val'),'single'); rPr.append(u)
    rfonts=OxmlElement('w:rFonts'); rfonts.set(qn('w:ascii'),'Inter'); rfonts.set(qn('w:hAnsi'),'Inter'); rPr.append(rfonts)
    run.append(rPr); txt=OxmlElement('w:t'); txt.text=text; run.append(txt); hyperlink.append(run)
    paragraph._p.append(hyperlink); return hyperlink

def add_inline(paragraph, text, color=None):
    # Keep markdown inline bold, code, links, and raw URLs; all other text stays literal.
    pattern=re.compile(r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|https?://[^\s)]+)')
    pos=0
    for m in pattern.finditer(text):
        if m.start()>pos: paragraph.add_run(text[pos:m.start()])
        token=m.group(0)
        if token.startswith('**'):
            r=paragraph.add_run(token[2:-2]); r.bold=True
        elif token.startswith('`'):
            r=paragraph.add_run(token[1:-1]); r.font.name='DejaVu Sans Mono'; r.font.size=Pt(7.4); r.font.color.rgb=RGBColor(22,36,59)
        elif token.startswith('['):
            lm=re.match(r'\[([^\]]+)\]\(([^)]+)\)',token)
            if lm:
                label,url=lm.group(1),lm.group(2)
                add_hyperlink(paragraph,label,url[1:] if url.startswith('#') else url,external=not url.startswith('#'))
            else: paragraph.add_run(token)
        else:
            url=token.rstrip('.,;:'); tail=token[len(url):]
            add_hyperlink(paragraph,url,url,external=True); paragraph.add_run(tail)
        pos=m.end()
    if pos<len(text): paragraph.add_run(text[pos:])

def add_para(doc,text,style=None,deep=False):
    p=doc.add_paragraph(style=style) if style else doc.add_paragraph()
    add_inline(p,text)
    if deep:
        for r in p.runs: r.font.color.rgb=RGBColor(243,235,221)
    return p

def create_docx(blocks):
    doc=Document(); sec=doc.sections[0]
    sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
    sec.top_margin=Inches(.48); sec.bottom_margin=Inches(.52); sec.left_margin=Inches(.58); sec.right_margin=Inches(.58)
    styles=doc.styles
    normal=styles['Normal']; normal.font.name='Inter'; normal.font.size=Pt(8.6); normal.font.color.rgb=RGBColor(22,36,59)
    normal.paragraph_format.space_after=Pt(3); normal.paragraph_format.line_spacing=1.06
    for name,size,col in [('Title',40,NAVY),('Subtitle',16,RUST),('Heading 1',21,NAVY),('Heading 2',8.5,TEAL),('Heading 3',8.2,TEAL)]:
        st=styles[name]; st.font.name='EB Garamond' if name in ('Title','Subtitle','Heading 1') else 'Inter'; st.font.size=Pt(size); st.font.color.rgb=RGBColor.from_string(col[1:] if col.startswith('#') else col)
        if name.startswith('Heading'): st.font.bold=(name!='Heading 1'); st.paragraph_format.keep_with_next=True; st.paragraph_format.space_before=Pt(6 if name!='Heading 1' else 0); st.paragraph_format.space_after=Pt(3)
    # Replace the built-in Word Title style's default blue accent rule with navy.
    title_ppr=styles['Title']._element.get_or_add_pPr()
    title_bdr=title_ppr.find(qn('w:pBdr'))
    if title_bdr is not None:
        for edge in title_bdr:
            edge.set(qn('w:color'),'16243B')
            if qn('w:themeColor') in edge.attrib: del edge.attrib[qn('w:themeColor')]
    # Warm paper page background (screen view; printer background settings still apply).
    background=OxmlElement('w:background'); background.set(qn('w:color'),'F3EBDD')
    doc._element.insert(0,background)
    # Custom code and caption styles
    if 'Code' not in styles:
        st=styles.add_style('Code',1)
    else: st=styles['Code']
    st.font.name='DejaVu Sans Mono'; st.font.size=Pt(6.7); st.font.color.rgb=RGBColor(243,235,221)
    st.paragraph_format.left_indent=Inches(.10); st.paragraph_format.right_indent=Inches(.10); st.paragraph_format.space_before=Pt(0); st.paragraph_format.space_after=Pt(0); st.paragraph_format.line_spacing=1.0
    if 'Caption' in styles: cap=styles['Caption']
    else: cap=styles.add_style('Caption',1)
    cap.font.name='Inter'; cap.font.size=Pt(7); cap.font.italic=True; cap.font.color.rgb=RGBColor(102,112,133); cap.paragraph_format.space_after=Pt(4)
    # Footer with page field
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=footer.add_run('THE MODERN LLM STACK  ·  '); r.font.name='Inter'; r.font.size=Pt(7); r.font.color.rgb=RGBColor(102,112,133)
    fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)
    bookmark_ids={}; next_id=1
    # assign an invisible bookmark to every heading used for jump links
    for b in blocks:
        if b['type']=='heading': bookmark_ids[b['id']]=next_id; next_id+=1
    in_cover=True; first_break=False
    for bi,b in enumerate(blocks):
        typ=b['type']
        if typ=='pagebreak':
            if in_cover and not first_break:
                doc.add_page_break(); in_cover=False; first_break=True
            else: doc.add_page_break()
            continue
        if typ=='heading':
            if in_cover and b['level']==1 and b['text'].strip().upper()=='THE MODERN LLM STACK':
                p=doc.add_paragraph(style='Title'); add_inline(p,b['text']); p.paragraph_format.space_before=Pt(48); p.paragraph_format.space_after=Pt(8)
            elif in_cover and b['level']==3:
                p=doc.add_paragraph(style='Subtitle'); add_inline(p,b['text']); p.paragraph_format.space_after=Pt(28)
            else:
                level=min(3,max(1,b['level']))
                # The three pipped learning layers are second-level section headings in Word.
                if level==3 and b['text'].startswith('●'): level=2
                p=doc.add_paragraph(style=f'Heading {level}'); add_inline(p,b['text'])
            add_bookmark(p,b['id'],bookmark_ids[b['id']]); continue
        if typ=='paragraph':
            # first cover description gets a little larger
            p=doc.add_paragraph(); add_inline(p,b['text'])
            if in_cover:
                p.paragraph_format.space_after=Pt(10)
                for r in p.runs: r.font.size=Pt(10)
            continue
        if typ=='image-slot':
            meta=get_slot_meta(b['slot_id'],b['brief']); asset=get_slot_asset(b['slot_id'])
            if asset:
                p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(1)
                run=p.add_run(); inline=run.add_picture(str(asset),width=Inches(6.8)); inline._inline.docPr.set('descr',meta.get('alt_text') or meta.get('caption') or b['brief'])
                cp=doc.add_paragraph(style='Caption'); add_inline(cp,meta.get('caption') or b['brief']); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            else:
                table=doc.add_table(rows=1,cols=1); table.alignment=WD_TABLE_ALIGNMENT.CENTER; cell=table.cell(0,0); shade_cell(cell,'F4EBD9'); set_cell_margins(cell,top=110,bottom=110,start=140,end=140)
                p=cell.paragraphs[0]; r=p.add_run(f"REAL IMAGE SLOT · NOT DOWNLOADED · {b['slot_id']}\n"); r.bold=True; r.font.name='Inter'; r.font.size=Pt(6.5); r.font.color.rgb=RGBColor.from_string('D45D45')
                r=p.add_run(b['brief']); r.font.name='Inter'; r.font.size=Pt(7.5); r.font.color.rgb=RGBColor.from_string('16243B')
            continue
        if typ=='figure':
            path=ROOT/'images'/'figures'/f'{b["name"]}.png'
            if path.exists():
                p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(1)
                run=p.add_run(); inline=run.add_picture(str(path),width=Inches(6.8)); inline._inline.docPr.set('descr',b['caption'])
                cp=doc.add_paragraph(style='Caption'); add_inline(cp,b['caption']); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            else: add_para(doc,'[Diagram unavailable: '+b['name']+']')
            continue
        if typ=='table':
            rows=b['rows'];
            if not rows: continue
            ncols=max(len(r) for r in rows); table=doc.add_table(rows=len(rows),cols=ncols); table.alignment=WD_TABLE_ALIGNMENT.CENTER; table.style='Table Grid'
            for ri,row in enumerate(rows):
                for ci in range(ncols):
                    val=row[ci] if ci<len(row) else ''
                    cell=table.cell(ri,ci); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_margins(cell,top=50,bottom=50,start=65,end=65)
                    if ri==0: shade_cell(cell,'16243B')
                    elif ri%2==0: shade_cell(cell,'FAF6EE')
                    p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0; add_inline(p,val)
                    for run in p.runs:
                        run.font.name='Inter'; run.font.size=Pt(7.0 if ncols>2 else 7.4)
                        if ri==0: run.bold=True; run.font.color.rgb=RGBColor.from_string('F3EBDD')
            continue
        if typ=='list':
            for item in b['items']:
                sty='List Number' if b['ordered'] else 'List Bullet'; p=doc.add_paragraph(style=sty); p.paragraph_format.space_after=Pt(1); add_inline(p,item)
            continue
        if typ=='code':
            for line in b['text'].splitlines():
                p=doc.add_paragraph(style='Code'); p.paragraph_format.keep_together=True
                pPr=p._p.get_or_add_pPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'172338'); pPr.append(shd)
                # line by line prevents very long blocks from breaking badly
                r=p.add_run(line if line else ' '); r.font.name='DejaVu Sans Mono'; r.font.size=Pt(6.7); r.font.color.rgb=RGBColor(243,235,221)
            continue
        if typ=='quote':
            p=doc.add_paragraph(style='Quote'); add_inline(p,b['text']); p.paragraph_format.left_indent=Inches(.2)
            for r in p.runs: r.font.name='EB Garamond'; r.font.size=Pt(11)
            continue
        if typ=='rule':
            p=doc.add_paragraph('─'*50); p.paragraph_format.space_after=Pt(1); continue
        if typ=='deep-dive':
            # Single-cell table makes an inverted card; paragraphs/code are kept together inside it.
            table=doc.add_table(rows=1,cols=1); table.alignment=WD_TABLE_ALIGNMENT.CENTER; cell=table.cell(0,0); shade_cell(cell,'16243B'); set_cell_margins(cell,top=100,bottom=100,start=145,end=145)
            first=True
            for ib in b['blocks']:
                it=ib['type']
                if it=='heading':
                    p=cell.paragraphs[0] if first else cell.add_paragraph(); first=False; add_inline(p,ib['text']);
                    for r in p.runs: r.bold=True; r.font.color.rgb=RGBColor.from_string('F3EBDD'); r.font.size=Pt(8.5)
                elif it=='paragraph':
                    p=cell.paragraphs[0] if first else cell.add_paragraph(); first=False; add_inline(p,ib['text']);
                    for r in p.runs: r.font.color.rgb=RGBColor.from_string('F3EBDD'); r.font.size=Pt(7.6)
                    p.paragraph_format.space_after=Pt(2)
                elif it=='code':
                    for line in ib['text'].splitlines():
                        p=cell.add_paragraph(); r=p.add_run(line if line else ' '); r.font.name='DejaVu Sans Mono'; r.font.size=Pt(6.2); r.font.color.rgb=RGBColor.from_string('F3EBDD'); p.paragraph_format.space_after=Pt(0)
                elif it=='list':
                    for item in ib['items']:
                        p=cell.add_paragraph(); add_inline(p,'• '+item)
                        for r in p.runs: r.font.color.rgb=RGBColor.from_string('F3EBDD'); r.font.size=Pt(7.3)
            continue
    # Core properties
    doc.core_properties.title='The Modern LLM Stack: cloud LLMs, self-hosted LLMs, MCP and agents'
    doc.core_properties.subject='Technical field guide, compact 25-page edition'
    doc.core_properties.author='OpenAI'
    doc.save(OUT_DOCX)

def main():
    draw_diagrams()
    source=SOURCE.read_text(encoding='utf-8')
    blocks=parse_blocks(source)
    html_doc=build_html(blocks)
    (ROOT/'content'/'rendered.html').write_text(html_doc,encoding='utf-8')
    HTML(string=html_doc,base_url=str(ROOT)).write_pdf(str(OUT_PDF),presentational_hints=True)
    create_docx(blocks)
    print(f'Built {OUT_PDF.name} ({OUT_PDF.stat().st_size:,} bytes) and {OUT_DOCX.name} ({OUT_DOCX.stat().st_size:,} bytes)')

if __name__=='__main__': main()
