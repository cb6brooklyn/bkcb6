from PIL import Image, ImageDraw, ImageFont
import sys
F='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
OR=(252,136,14);BK=(6,1,3);WH=(255,255,255);GH=(235,234,233)
def font(s,w=700):
    f=ImageFont.truetype('/root/bkcb6/tools/fonts/LeagueSpartan[wght].ttf',s); f.set_variation_by_axes([w]); return f
def ghosts():
    g=Image.open('/mnt/user-data/attachments/db888a3b-5da4-52bd-894d-4c3141ef9c96/9ca483c9-image.png').convert('RGBA').crop((460,20,585,140))
    px=g.load()
    for y in range(g.height):
        for x in range(g.width):
            r,gg,b,a=px[x,y]; l=(r+gg+b)/3
            px[x,y]=(r,gg,b,0 if l<40 else min(255,int((l-40)*255/150)))
    return g
def ctext(d,cx,y,t,f,fill):
    w=d.textlength(t,font=f); d.text((cx-w/2,y),t,font=f,fill=fill)
def fit(d,t,maxw,start):
    s=start
    while d.textlength(t,font=font(s))>maxw: s-=2
    return font(s)
def make(day,mdate,year,out):
    W,H=1400,400;B=10
    im=Image.new('RGB',(W,H),OR);d=ImageDraw.Draw(im)
    L0,L1=B,400;M0,M1=410,1050;R0,R1=1060,W-B
    for a,b in((L0,L1),(M0,M1),(R0,R1)): d.rectangle([a,B,b,H-B-1],fill=BK)
    # left spooky block
    cx=(L0+L1)/2
    fc=font(190,800); ctext(d,cx-12,62,'CB6',fc,OR)
    ctext(d,cx,262,'BROOKLYN',font(40),WH)
    ctext(d,cx,308,'COMMUNITY BOARD 6',fit(d,'COMMUNITY BOARD 6',L1-L0-30,36),WH)
    g=ghosts().resize((68,65));im.paste(g,(L1-72,14),g)
    # middle date
    x=M0+50
    d.text((x,44),day,font=font(108),fill=WH)
    d.text((x,162),mdate,font=fit(d,mdate,M1-M0-80,108),fill=WH)
    d.text((x,280),year,font=font(108),fill=OR)
    # right sticker
    cx=(R0+R1)/2
    ctext(d,cx,30,'Ongoing...',font(32),WH)
    cy=225;r=150
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=OR);d.ellipse([cx-r+12,cy-r+12,cx+r-12,cy+r-12],fill=BK)
    f=font(44);lines=[[('IN ',OR),('2026',WH)],[('I VOTED',WH)],[('IN',OR)],[('BKCB6',WH)]]
    y=cy-102
    for ln in lines:
        w=sum(d.textlength(t,font=f) for t,_ in ln);xx=cx-w/2
        for t,c in ln: d.text((xx,y),t,font=f,fill=c);xx+=d.textlength(t,font=f)
        y+=58
    g2=ghosts().resize((62,60));im.paste(g2,(int(R1-70),int(H-B-72)),g2)
    im.save(out,quality=92)
make(*sys.argv[1:5])
