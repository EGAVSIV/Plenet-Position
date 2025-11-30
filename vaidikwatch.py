import streamlit as st
import numpy as np
import pygame
import pygame.freetype
import swisseph as swe
import pytz, datetime, math

st.set_page_config(page_title="Vedic ग्रह घड़ी", layout="wide")

# ------------------------------------
# Load Devanagari font
# ------------------------------------
FONT = "fonts/NotoSansDevanagari-Regular.ttf"

# ------------------------------------
# Auto Refresh every 60s
# ------------------------------------
st.markdown("""
<script>
setTimeout(function(){ window.location.reload(); }, 60000);
</script>
""", unsafe_allow_html=True)

# ------------------------------------
# Astrology Config
# ------------------------------------
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
("राहु", swe.TRUE_NODE,"☊")
]

COL = {
"सूर्य":"#FFC06B","चन्द्र":"#CFE9FF","मंगल":"#FF8A8A",
"बुध":"#B6FF9C","बृहस्पति":"#FFD88A","शुक्र":"#F9B0FF",
"शनि":"#C0C8FF","राहु":"#FFCF66","केतु":"#FFCF66"
}

swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)

# --------------------------------------
# Astrology Functions
# --------------------------------------
def get_positions(dt):
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour+dt.minute/60) - 5.5/24
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

# --------------------------------------
# Drawing
# --------------------------------------
pygame.init()
pygame.freetype.init()

def draw_chart(pos):
    SIZE = 950
    R_sign  = 380
    R_planet= 300

    surf = pygame.Surface((SIZE,SIZE),pygame.SRCALPHA)
    cx=cy=SIZE//2

    f  = pygame.freetype.Font(FONT,34)
    f2 = pygame.freetype.Font(FONT,22)

    # Draw Ring
    pygame.draw.circle(surf,(0,0,255),(cx,cy),R_sign+25,50)

    # Draw 12 Zodiac
    for i in range(12):
        ang = math.radians(90 - i*30)
        x = cx + R_sign * math.cos(ang)
        y = cy - R_sign * math.sin(ang)
        f.render_to(surf,(x-25,y-15),SIGNS[i],(255,255,255))

    # Draw Planets
    for name,code,sym in PLANETS:
        lon = pos[name]
        ang = math.radians(90 - lon)

        x = cx + R_planet * math.cos(ang)
        y = cy - R_planet * math.sin(ang)

        pygame.draw.circle(surf,pygame.Color(COL[name]),(int(x),int(y)),30)
        f.render_to(surf,(x-15,y-20),sym,(0,0,0))

        f2.render_to(surf,(x-55,y+35),nakshatra(lon),(255,240,200))

    return surf

# --------------------------------------
# UI
# --------------------------------------
st.markdown("<h1 style='color:yellow'>वेदिक ग्रह घड़ी</h1>",unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
d=c1.date_input("Date")
t=c2.time_input("Time (IST)")

if c3.button("NOW"):
    now=datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    d=now.date(); t=now.time()

dt=datetime.datetime.combine(d,t)

pos=get_positions(dt)
surf=draw_chart(pos)

# show image as-is (no rotation)
arr = pygame.surfarray.array3d(surf)
arr = np.transpose(arr,(1,0,2))

st.image(arr,use_container_width=True)
