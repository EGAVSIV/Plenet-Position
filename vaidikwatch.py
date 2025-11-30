import streamlit as st
import swisseph as swe
import datetime, pytz, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="वेदिक ग्रह घड़ी — Web", layout="wide")

# =========================================================
# CONSTANTS / CONFIG
# =========================================================
LAT = 19.0760
LON = 72.8777
ELEV = 14

SIGNS = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

NAKSHATRAS = [
    ("अश्विनी", "केतु"), ("भरणी", "शुक्र"), ("कृत्तिका", "सूर्य"),
    ("रोहिणी", "चन्द्र"), ("मृगशिरा", "मंगल"), ("आर्द्रा", "राहु"),
    ("पुनर्वसु", "बृहस्पति"), ("पुष्य", "शनि"), ("आश्लेषा", "बुध"),
    ("मघा", "केतु"), ("पूर्व फाल्गुनी", "शुक्र"), ("उत्तर फाल्गुनी", "सूर्य"),
    ("हस्त", "चन्द्र"), ("चित्रा", "मंगल"), ("स्वाति", "राहु"),
    ("विशाखा", "बृहस्पति"), ("अनुराधा", "शनि"), ("ज्येष्ठा", "बुध"),
    ("मूला", "केतु"), ("पूर्वाषाढा", "शुक्र"), ("उत्तराषाढा", "सूर्य"),
    ("श्रवण", "चन्द्र"), ("धनिष्ठा", "मंगल"), ("शतभिषा", "राहु"),
    ("पूर्वभाद्रपदा", "बृहस्पति"), ("उत्तरभाद्रपदा", "शनि"), ("रेवती", "बुध"),
]

# same order as Tk app
PLANETS = [
    ("सूर्य", swe.SUN, "🜚"),
    ("चन्द्र", swe.MOON, "☽"),
    ("मंगल", swe.MARS, "♂"),
    ("बुध", swe.MERCURY, "☿"),
    ("बृहस्पति", swe.JUPITER, "♃"),
    ("शुक्र", swe.VENUS, "♀"),
    ("शनि", swe.SATURN, "♄"),
    ("राहु", swe.TRUE_NODE, "☊"),
]

PLANET_SYMBOL = {
    "सूर्य": "🜚", "चन्द्र": "☽", "मंगल": "♂", "बुध": "☿",
    "बृहस्पति": "♃", "शुक्र": "♀", "शनि": "♄", "राहु": "☊", "केतु": "☋"
}

PLANET_COLOR = {
    "सूर्य": "#FFB86B", "चन्द्र": "#BFE9FF", "मंगल": "#FF8A8A",
    "बुध": "#B6FF9C", "बृहस्पति": "#FFD88A", "शुक्र": "#F9B0FF",
    "शनि": "#C0C8FF", "राहु": "#FFCF66", "केतु": "#FFCF66"
}

swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

IST = pytz.timezone("Asia/Kolkata")

# try Devanagari font if available, else default
def get_font(size):
    try:
        return ImageFont.truetype("NotoSansDevanagari-Regular.ttf", size)
    except Exception:
        return ImageFont.load_default()


# =========================================================
# ASTRONOMY HELPERS
# =========================================================
def compute_positions_for_dt(dt_ist: datetime.datetime):
    """
    dt_ist: datetime in IST
    returns positions (sidereal long), retro flags, dt_ist
    """
    hour = dt_ist.hour + dt_ist.minute / 60.0 + dt_ist.second / 3600.0
    jd_ut = swe.julday(dt_ist.year, dt_ist.month, dt_ist.day, hour) - (5.5 / 24.0)

    positions = {}
    retro = {}

    for name, code, sym in PLANETS:
        res = swe.calc_ut(jd_ut, code)
        arr = res[0] if isinstance(res[0], (list, tuple)) else res
        lon = arr[0]
        speed = arr[3] if len(arr) > 3 else 0.0
        ayan = swe.get_ayanamsa_ut(jd_ut)
        sid = (lon - ayan) % 360.0
        positions[name] = sid
        retro[name] = (speed < 0)

    # Ketu opposite Rahu
    if "राहु" in positions:
        positions["केतु"] = (positions["राहु"] + 180.0) % 360.0
        retro["केतु"] = retro["राहु"]

    return positions, retro


def nakshatra_info(sid_lon: float):
    each = 13 + 1/3
    idx = int(sid_lon // each) % 27
    nak_name, nak_lord = NAKSHATRAS[idx]
    pada = int((sid_lon % each) // (each / 4.0)) + 1
    return nak_name, pada, nak_lord


# =========================================================
# IMAGE HELPERS  (Dynamic ring + background)
# =========================================================
def radial_gradient_image(size, inner_color, outer_color):
    w, h = size
    cx, cy = w / 2, h / 2
    maxr = math.hypot(cx, cy)
    img = Image.new("RGBA", (w, h), outer_color + (255,))
    draw = ImageDraw.Draw(img)

    steps = 120
    for i in range(steps, 0, -1):
        f = i / steps
        r = int(f * maxr)
        col = tuple(
            int(inner_color[c] * f + outer_color[c] * (1 - f))
            for c in range(3)
        ) + (255,)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    img = img.filter(ImageFilter.GaussianBlur(12))
    return img


def glossy_ring_image(size, ring_radius, ring_thickness):
    w, h = size
    cx, cy = w // 2, h // 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    outer = ring_radius + ring_thickness // 2
    inner = ring_radius - ring_thickness // 2

    # metallic blue ring
    for i in range(ring_thickness):
        t = i / max(1, ring_thickness)
        r = int(20 + 50 * t)
        g = int(40 + 80 * t)
        b = int(90 + 155 * t)
        color = (r, g, b, 255)
        draw.ellipse(
            [cx - outer + i, cy - outer + i, cx + outer - i, cy + outer - i],
            outline=color,
            width=1,
        )

    # outer glow
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for gsz in range(4):
        gc = (60, 120, 255, int(70 - gsz * 15))
        gdraw.ellipse(
            [cx - outer - gsz * 4, cy - outer - gsz * 4,
             cx + outer + gsz * 4, cy + outer + gsz * 4],
            outline=gc,
            width=4,
        )

    glow = glow.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img, glow)
    return img


# =========================================================
# DRAW MAIN CHART
# =========================================================
def draw_chart(positions, retro_flags, theme="Dark", size=720):
    center = size // 2
    radius = int(size * 0.36)

    if theme == "Dark":
        bg = radial_gradient_image(
            (size, size),
            inner_color=(24, 28, 40),
            outer_color=(8, 10, 16),
        )
        sign_color = (246, 244, 230)
        nak_color = (255, 235, 153)
        center_text_col1 = (255, 255, 255)
        center_text_col2 = (221, 221, 221)
        planet_name_col = (238, 238, 238)
    else:
        bg = radial_gradient_image(
            (size, size),
            inner_color=(250, 245, 240),
            outer_color=(220, 215, 210),
        )
        sign_color = (32, 32, 32)
        nak_color = (136, 34, 0)
        center_text_col1 = (30, 30, 30)
        center_text_col2 = (60, 60, 60)
        planet_name_col = (30, 30, 30)

    ring = glossy_ring_image((size, size), ring_radius=radius + 8, ring_thickness=60)
    img = Image.alpha_composite(bg, ring)
    draw = ImageDraw.Draw(img)

    sign_font = get_font(18)
    planet_font = get_font(20)
    nak_font = get_font(13)
    center_font_big = get_font(22)
    center_font_small = get_font(14)
    planet_name_font = get_font(12)

    # 12 rāśi names + radial lines
    for i in range(12):
        ang_deg = 90 - i * 30
        ang = math.radians(ang_deg)
        x = center + (radius + 18) * math.cos(ang)
        y = center - (radius + 18) * math.sin(ang)

        # small shadow
        draw.text((x + 2, y + 2), SIGNS[i], font=sign_font, fill=(0, 0, 0))
        draw.text((x, y), SIGNS[i], font=sign_font, fill=sign_color)

        x2 = center + (radius - 20) * math.cos(ang)
        y2 = center - (radius - 20) * math.sin(ang)
        draw.line((center, center, x2, y2), fill="yellow", width=2)

    # center labels
    draw.text(
        (center, center - 8),
        "वेदिक घड़ी",
        font=center_font_big,
        fill=center_text_col1,
        anchor="mm",
    )
    draw.text(
        (center, center + 14),
        "(लाहिड़ी अयनांश)",
        font=center_font_small,
        fill=center_text_col2,
        anchor="mm",
    )

    # offsets to spread planets like your Tk code
    offsets = {
        "सूर्य": 0, "चन्द्र": -18, "मंगल": 18, "बुध": -32,
        "बृहस्पति": 42, "शुक्र": -54, "शनि": 64, "राहु": -76, "केतु": 76
    }

    # draw planets
    for name, _, sym in PLANETS + [("केतु", None, "☋")]:
        if name not in positions:
            continue
        sid = positions[name]
        ang_deg = 90 - sid
        ang = math.radians(ang_deg)
        r = radius + offsets.get(name, 0)

        x = center + r * math.cos(ang)
        y = center - r * math.sin(ang)

        # planet circle
        color_hex = PLANET_COLOR.get(name, "#FFFFFF")
        fill_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
        draw.ellipse((x-14, y-14, x+14, y+14), fill=fill_rgb, outline=(51, 51, 51), width=2)

        # symbol
        draw.text((x, y-2), PLANET_SYMBOL.get(name, sym),
                  font=planet_font, fill=(10, 10, 10), anchor="mm")

        # planet name (Hindi)
        draw.text((x, y+20), name, font=planet_name_font,
                  fill=planet_name_col, anchor="mm")

        # nakshatra label
        nak_name, pada, lord = nakshatra_info(sid)
        draw.text((x, y-26), nak_name, font=nak_font, fill=nak_color, anchor="mm")

        # retro glow
        if retro_flags.get(name, False):
            for rad in (22, 27, 32):
                draw.ellipse(
                    (x-rad, y-rad, x+rad, y+rad),
                    outline=(255, 80, 80, 180),
                    width=1,
                )

    return img


# =========================================================
# CLOSE-UP IMAGE
# =========================================================
def draw_closeup(planet_name, sid_lon, retro_flag, theme="Dark", size=320):
    cx = cy = size // 2
    if theme == "Dark":
        bg = radial_gradient_image((size, size),
                                   inner_color=(40, 44, 54),
                                   outer_color=(10, 10, 12))
        text_col = (255, 255, 255)
    else:
        bg = radial_gradient_image((size, size),
                                   inner_color=(245, 245, 240),
                                   outer_color=(220, 220, 215))
        text_col = (20, 20, 20)

    draw = ImageDraw.Draw(bg)
    big_font = get_font(40)
    text_font = get_font(14)
    title_font = get_font(16)

    # white sphere
    radius = int(size * 0.13)
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
                 fill=(250, 250, 250), outline=(200, 200, 200))

    # planet symbol
    draw.text((cx, cy-2), PLANET_SYMBOL.get(planet_name, planet_name[0]),
              font=big_font, fill=(10, 10, 10), anchor="mm")

    sign_idx = int(sid_lon // 30)
    sign_name = SIGNS[sign_idx]
    deg_in_sign = sid_lon % 30
    deg = int(deg_in_sign)
    mins = int((deg_in_sign - deg) * 60)
    nak_name, pada, nak_lord = nakshatra_info(sid_lon)
    motion = "Retrograde" if retro_flag else "Direct"

    ist_now = datetime.datetime.now(IST)

    info_lines = [
        f"ग्रह: {planet_name}",
        f"Longitude: {sid_lon:.4f}°",
        f"स्थिति: {deg:02d}° {sign_name} {mins:02d}′",
        f"नक्षत्र: {nak_name} (Pd{pada}) स्वामी: {nak_lord}",
        f"Motion: {motion}",
        f"समय: {ist_now.strftime('%d-%b-%Y %H:%M:%S')} IST",
    ]

    # box
    box_x1, box_y1 = 18, size - 140
    box_x2, box_y2 = size - 18, size - 18
    draw.rectangle((box_x1, box_y1, box_x2, box_y2),
                   fill=(0, 0, 0, 170) if theme == "Dark" else (255, 255, 255, 220),
                   outline=(80, 80, 80), width=1)

    y = box_y1 + 12
    for line in info_lines:
        draw.text((box_x1 + 12, y), line, font=text_font, fill=text_col, anchor="ls")
        y += 18

    draw.text((cx, box_y1 - 10), "विस्तृत जानकारी", font=title_font,
              fill=text_col, anchor="mm")

    return bg


# =========================================================
# TABLE RENDER (HTML)
# =========================================================
def build_table_html(positions, retro_flags):
    rows = []
    for name, _, _ in PLANETS:
        if name not in positions:
            continue
        sid = positions[name]
        sign_idx = int(sid // 30)
        sign_name = SIGNS[sign_idx]
        nak_name, pada, nak_lord = nakshatra_info(sid)
        motion = "Retrograde" if retro_flags.get(name, False) else "Direct"
        rows.append({
            "planet": name,
            "symbol": PLANET_SYMBOL.get(name, ""),
            "lon": f"{sid:.4f}°",
            "rashi": sign_name,
            "nak": nak_name,
            "motion": motion,
            "retro": retro_flags.get(name, False),
        })

    # HTML
    html = """
    <style>
    table.vedic-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 13px;
    }
    table.vedic-table th, table.vedic-table td {
        border: 1px solid #444;
        padding: 6px 8px;
        text-align: center;
    }
    table.vedic-table th {
        background: #222;
        color: #fff;
    }
    tr.row-direct {
        background: #111;
        color: #fff;
    }
    tr.row-retro {
        background: #2b0000;
        color: #ffdcdc;
    }
    </style>
    <table class="vedic-table">
      <tr>
        <th>ग्रह</th>
        <th>प्रतीक</th>
        <th>Longitude</th>
        <th>राशि</th>
        <th>नक्षत्र</th>
        <th>Motion</th>
      </tr>
    """
    for r in rows:
        cls = "row-retro" if r["retro"] else "row-direct"
        html += f"""
        <tr class="{cls}">
            <td>{r['planet']}</td>
            <td>{r['symbol']}</td>
            <td>{r['lon']}</td>
            <td>{r['rashi']}</td>
            <td>{r['nak']}</td>
            <td>{r['motion']}</td>
        </tr>
        """
    html += "</table>"
    return html


# =========================================================
# STREAMLIT UI
# =========================================================
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

ist_now = datetime.datetime.now(IST)
if "sel_date" not in st.session_state:
    st.session_state.sel_date = ist_now.date()
if "sel_time" not in st.session_state:
    st.session_state.sel_time = ist_now.time()
if "selected_planet" not in st.session_state:
    st.session_state.selected_planet = "चन्द्र"  # default

st.markdown(
    "<h2 style='color:yellow; margin-bottom:0;'>वेदिक ग्रह घड़ी — Web</h2>",
    unsafe_allow_html=True,
)

top1, top2, top3, top4 = st.columns([1, 1, 1, 3])

if top1.button("रिफ्रेश करें"):
    st.experimental_rerun()

if top2.button("थीम बदलें"):
    st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"

if top3.button("NOW (IST)"):
    ist_now = datetime.datetime.now(IST)
    st.session_state.sel_date = ist_now.date()
    st.session_state.sel_time = ist_now.time()

top4.markdown(
    f"**Last updated:** {ist_now.strftime('%d-%b-%Y %H:%M:%S')} IST"
)

colA, colB = st.columns(2)
date_val = colA.date_input("तारीख (IST)", key="sel_date")
time_val = colB.time_input("समय (IST)", key="sel_time")

dt_ist = datetime.datetime.combine(date_val, time_val)

positions, retro_flags = compute_positions_for_dt(dt_ist)

# layout like Tk: left chart, right table+closeup
col_left, col_right = st.columns([1.4, 1])

# chart
with col_left:
    chart_img = draw_chart(positions, retro_flags, theme=st.session_state.theme, size=720)
    st.image(np.array(chart_img), use_container_width=True)

with col_right:
    st.markdown("### ग्रह तालिका")
    table_html = build_table_html(positions, retro_flags)
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### विस्तृत ग्रह जानकारी")
    planet_names = [p[0] for p in PLANETS] + (["केतु"] if "केतु" in positions else [])
    # default selected planet from session
    if st.session_state.selected_planet not in planet_names:
        st.session_state.selected_planet = planet_names[0]

    sel_planet = st.selectbox(
        "ग्रह चुनें",
        options=planet_names,
        index=planet_names.index(st.session_state.selected_planet),
    )
    st.session_state.selected_planet = sel_planet

    sid_lon = positions[sel_planet]
    close_img = draw_closeup(sel_planet, sid_lon, retro_flags.get(sel_planet, False),
                             theme=st.session_state.theme, size=320)
    st.image(np.array(close_img), use_column_width=True)
