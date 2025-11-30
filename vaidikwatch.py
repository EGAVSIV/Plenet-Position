import streamlit as st
import numpy as np
import pygame
import pygame.freetype
import swisseph as swe
import pytz, datetime, math

st.set_page_config(page_title="वेदिक ग्रह घड़ी", layout="wide")

# auto refresh
st.markdown("""
<script>
setTimeout(function(){ window.location.reload(); }, 60000);
</script>
""",unsafe_allow_html=True)

# ---------------- FONT FIX ----------------
FONT_HINDI = "fonts/NotoSansDevanagari-Regular.ttf"

# ---------------- CONFIG ----------------
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

PLANETS = {
"सूर्य":(swe.SUN,"🜚"),"चन्द्र":(swe.MOON,"☽"),
"मंगल":(swe.MARS,"♂"),"बुध":(swe.MERCURY,"☿"),
"बृहस्पति":(swe.JUPITER,"♃"),"शुक्र":(swe.VENUS,"♀"),
"शनि":(swe.SATURN,"♄"),"राहु":(swe.TRUE_NODE,"☊")
}

PLANET_SYMBOL={"सूर्य":"🜚","चन्द्र":"☽","मंगल":"♂","बुध":"☿",
               "बृहस्पति":"♃","शुक्र":"♀","शनि":"♄","राहु":"☊","केतु":"☋"}

PLANET_COLOR={"सूर्य":"#FFB86B","चन्द्र":"#BFE9FF","मंगल":"#FF8A8A",
              "बुध":"#B6FF9C","बृहस्पति":"#FFD88A","शुक्र":"#F9B0FF",
              "शनि":"#C0C8FF","राहु":"#FFCF66","केतु":"#FFCF66"}

swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)

# ---------------- FUNC ----------------
def compute_positions(dt):
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60) - (5.5/24)
    pos={}; retro={}
    for pname,(code,_) in PLANETS.items():
        r=swe.calc_ut(jd,code)
        lon=r[0][0]; sp=r[0][3]; ay=swe.get_ayanamsa_ut(jd)
        pos[pname]=(lon-ay)%360
        retro[pname]=(sp<0)
    pos["केतु"]=(pos["राहु"]+180)%360
    retro["केतु"]=retro["राहु"]
    return pos,retro

def nakshatra_info(lon):
    each=13+1/3
    idx=int(lon//each)%27
    pad=int((lon%each)//(each/4))+1
    return *NAKSHATRAS[idx], pad

pygame.init(); pygame.freetype.init()

def draw_chart(pos,retro):
    SIZE=900; R=330
    surf=pygame.Surface((SIZE,SIZE),pygame.SRCALPHA)
    cx=cy=SIZE//2

    f  = pygame.freetype.Font(FONT_HINDI,28)
    f2 = pygame.freetype.Font(FONT_HINDI,20)

    # zodiac labels
    for i in range(12):
        ang=math.radians(90-i*30)
        x=cx+(R+40)*math.cos(ang)
        y=cy-(R+40)*math.sin(ang)
        f.render_to(surf,(x,y),SIGNS[i],(255,255,255))

    # planets
    for p in pos:
        sid=pos[p]
        ang=math.radians(90-sid)
        x=cx+(R-20)*math.cos(ang)
        y=cy-(R-20)*math.sin(ang)

        pygame.draw.circle(surf,pygame.Color(PLANET_COLOR[p]),(int(x),int(y)),28)
        f.render_to(surf,(x-18,y-20),PLANET_SYMBOL[p],(0,0,0))

        nak,lord,pada = nakshatra_info(sid)
        f2.render_to(surf,(x-55,y-65),nak,(255,240,200))

    return surf


# ---------------- UI ----------------
st.markdown("<h1 style='color:yellow'>वेदिक ग्रह घड़ी</h1>",unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)

sel_date=c1.date_input("Date")
sel_time=c2.time_input("Time")

if c3.button("Now"):
    now=datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    sel_date=now.date()
    sel_time=now.time()

dt=datetime.datetime.combine(sel_date, sel_time)

pos,retro=compute_positions(dt)

surface=draw_chart(pos,retro)
arr=np.rot90(pygame.surfarray.array3d(surface))

st.image(arr,use_container_width=True)
