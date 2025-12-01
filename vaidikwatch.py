import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import swisseph as swe
import pytz, datetime, math

# ====================== CONFIG ======================
st.set_page_config(page_title="वेदिक ग्रह घड़ी — वेब संस्करण", layout="wide")

FONT_LARGE  = ImageFont.truetype("fonts/NotoSansDevanagari-Regular.ttf", 32)
FONT_MEDIUM = ImageFont.truetype("fonts/NotoSansDevanagari-Regular.ttf", 22)
FONT_SMALL  = ImageFont.truetype("fonts/NotoSansDevanagari-Regular.ttf", 15)

SIGNS = ["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या",
         "तुला","वृश्चिक","धनु","मकर","कुंभ","मीन"]

NAKSHATRAS = [
("अश्विनी","केतु"),("भरणी","शुक्र"),("कृत्तिका","सूर्य"),
("रोहिणी","चन्द्र"),("मृगशिरा","मंगल"),("आर्द्रा","राहु"),
("पुनर्वसु","बृहस्पति"),("पुष्य","शनि"),("आश्लेषा","बुध"),
("मघा","केतु"),("पूर्व फाल्गुनी","शुक्र"),("उत्तर फाल्गुनी","सूर्य"),
("हस्त","चन्द्र"),("चित्रा","मंगल"),("स्वाति","राहु"),
("विशाखा","बृहस्पति"),("अनुराधा","शनि"),("ज्येष्ठा","बुध"),
("मूला","केतु"),("पूर्वाषाढा","शुक्र"),("उत्तराषाढा","सूर्य"),
("श्रवण","चन्द्र"),("धनिष्ठा","मंगल"),("शतभिषा","राहु"),
("पूर्वभाद्रपदा","बृहस्पति"),("उत्तरभाद्रपदा","शनि"),("रेवती","बुध"),
]

PLANETS = [
("सूर्य", swe.SUN, "🜚"),
("चन्द्र", swe.MOON,"☽"),
("मंगल", swe.MARS,"♂"),
("बुध", swe.MERCURY,"☿"),
("बृहस्पति", swe.JUPITER,"♃"),
("शुक्र", swe.VENUS,"♀"),
("शनि", swe.SATURN,"♄"),
("राहु", swe.MEAN_NODE,"☊")
]

COL = {
"सूर्य":"#FFC06B","चन्द्र":"#CFE9FF","मंगल":"#FF8A8A",
"बुध":"#B6FF9C","बृहस्पति":"#FFD88A","शुक्र":"#F9B0FF",
"शनि":"#C0C8FF","राहु":"#FFCF66","केतु":"#FFCF66"
}

swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)

# ====================== ASTRO ======================
def get_positions(dt):
    jd = swe.julday(dt.year, dt.month, dt.day,
                    dt.hour+dt.minute/60) - 5.5/24
    pos={}

    for name,code,sym in PLANETS:
        r=swe.calc_ut(jd,code)
        ay=swe.get_ayanamsa_ut(jd)
        pos[name] = (r[0][0]-ay)%360

    pos["केतु"] = (pos["राहु"]+180)%360
    return pos

def nakshatra(lon):
    each = 13+1/3
    idx = int(lon//each)%27
    return NAKSHATRAS[idx][0]

# ====================== DRAW FUNCTIONS ======================
def draw_ring():
    img = Image.new("RGBA",(950,950),(10,12,18))
    d = ImageDraw.Draw(img)
    cx=cy=475
    R1=380
    R2=420

    for i in range(80):
        col=(30,40+i*2,110+i*2)
        d.ellipse((cx-R2+i,cy-R2+i,cx+R2-i,cy+R2-i),
                  outline=col,width=2)

    # 12 Radial Lines
    for i in range(12):
        ang=math.radians(90-i*30)
        x=cx+R1*math.cos(ang)
        y=cy-R1*math.sin(ang)
        d.line((cx,cy,x,y),fill="yellow",width=3)

    # Center text
    d.text((cx,cy-20),"वेदिक घड़ी",font=FONT_LARGE,fill="white",anchor="mm")
    d.text((cx,cy+14),"(लाहिड़ी अयनांश)",font=FONT_SMALL,fill="white",anchor="mm")

    return img

def draw_planets(img,pos):
    d = ImageDraw.Draw(img)
    cx=cy=475
    R=300

    for name,code,sym in PLANETS:
        lon=pos[name]
        ang=math.radians(90-lon)

        x=cx+R*math.cos(ang)
        y=cy-R*math.sin(ang)

        # planet circle
        d.ellipse((x-22,y-22,x+22,y+22),
                  fill=COL[name],outline="black")

        d.text((x,y),sym,font=FONT_MEDIUM,fill="black",anchor="mm")
        d.text((x,y+32),name,font=FONT_SMALL,fill="white",anchor="mm")
        d.text((x,y-32),nakshatra(lon),font=FONT_SMALL,fill="#ffeb99",anchor="mm")

    return img

# ====================== UI ======================
st.title("🪐 वेदिक ग्रह घड़ी — Streamlit")

c1,c2,c3=st.columns(3)

dt_date=c1.date_input("तारीख़ चुनें")
dt_time=c2.time_input("समय चुनें")

if c3.button("अब"):
    now=datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    dt_date=now.date()
    dt_time=now.time()

dt=datetime.datetime.combine(dt_date,dt_time)

pos=get_positions(dt)

# chart
ring=draw_ring()
full=draw_planets(ring,pos)

##########################################################################
# DISPLAY
##########################################################################

colA,colB=st.columns([2,1])

colA.image(full,use_container_width=True)

# table
st.subheader("ग्रह तालिका")
table=[]
for p,code,sym in PLANETS:
    table.append([
        p,sym,
        f"{pos[p]:.4f}°",
        SIGNS[int(pos[p]//30)],
        nakshatra(pos[p])
    ])

st.table(table)

st.success("समय (IST): "+dt.strftime("%d-%b-%Y %H:%M:%S"))
