import swisseph as swe 
import datetime
import requests
import matplotlib.pyplot as plt
import pandas as pd

# === Telegram Config ===
BOT_TOKEN = '8268990134:AAGJJQrPzbi_3ROJWlDzF1sOl1RJLWP1t50'
CHAT_IDS = ['5332984891']   # you can add group id as well

def send_telegram_alert(message: str):
    """Send text message to Telegram"""
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"✅ Message sent to {chat_id}")
            else:
                print(f"❌ Failed for {chat_id}: {response.text}")
        except Exception as e:
            print(f"❌ Error for {chat_id}: {e}")

def send_telegram_image(image_path: str, caption: str = ""):
    """Send image to Telegram"""
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(image_path, "rb") as img:
            files = {"photo": img}
            data = {"chat_id": chat_id, "caption": caption}
            try:
                response = requests.post(url, data=data, files=files)
                if response.status_code == 200:
                    print(f"✅ Image sent to {chat_id}")
                else:
                    print(f"❌ Failed for {chat_id}: {response.text}")
            except Exception as e:
                print(f"❌ Error sending image for {chat_id}: {e}")

# === CONFIG ===
PLANET_NAMES = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.TRUE_NODE: "North Node (Rahu)",
    swe.MEAN_NODE: "South Node (Ketu)"
}

RASHIS = [
    'Mesha (Aries)', 'Vrishabha (Taurus)', 'Mithuna (Gemini)', 'Karka (Cancer)',
    'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrischika (Scorpio)',
    'Dhanu (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)'
]

NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
    'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
    'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula',
    'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]

DISHA_SHOOL = {
    0: "East", 1: "North", 2: "North-West", 3: "South",
    4: "West", 5: "South-East", 6: "North-East"
}

CHOUGHADIYA_DAY = ["Amrit", "Shubh", "Labh", "Char", "Rog", "Kaal", "Udveg"]

# === Astro Calculations ===
def get_planet_data():
    now_utc = datetime.datetime.utcnow()
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset

    jd = swe.julday(now_ist.year, now_ist.month, now_ist.day,
                    now_ist.hour + now_ist.minute / 60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    results = []
    sun_longitude, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    moon_longitude, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)

    tithi_float = (moon_longitude[0] - sun_longitude[0]) % 360 / 12
    tithi_number = int(tithi_float) + 1
    paksha = "Shukla" if tithi_number <= 15 else "Krishna"

    tithi_names = [
        "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
        "Purnima/Amavasya"
    ]

    weekday = now_ist.weekday()
    disha_shool_today = DISHA_SHOOL.get(weekday, "Unknown")
    choghadiya_now = CHOUGHADIYA_DAY[now_ist.hour % len(CHOUGHADIYA_DAY)]

    for planet_id, planet_name in PLANET_NAMES.items():
        pos, ret = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        longitude = pos[0]
        rashi_index = int(longitude / 30)
        nakshatra_index = int(longitude / (360 / 27))
        degree_in_nakshatra = longitude % (360 / 27)
        pada_number = int(degree_in_nakshatra / ((360 / 27) / 4)) + 1

        results.append({
            "Planet": planet_name,
            "Degree": round(longitude, 2),
            "Rashi": RASHIS[rashi_index],
            "Nakshatra": NAKSHATRAS[nakshatra_index],
            "Pada": pada_number
        })

    return {
        "datetime": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "tithi": tithi_names[(tithi_number - 1) % 15],
        "paksha": paksha,
        "disha_shool": disha_shool_today,
        "choghadiya": choghadiya_now,
        "planet_data": results
    }

# === Headless Image Generation ===
def generate_panchang_image(data, filename="panchang.png"):
    df = pd.DataFrame(data["planet_data"])

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#1f1f2e")
    ax.set_axis_off()

    # Title
    plt.text(0.5, 1.1, "🌟 Planetary Positions & Panchang Details", 
             ha="center", va="center", fontsize=18, fontweight="bold", color="#f5d742", transform=ax.transAxes)

    # Sub Info
    info_text = (f"Tithi: {data['tithi']} ({data['paksha']} Paksha)\n"
                 f"Disha Shool: {data['disha_shool']}\n"
                 f"Choghadiya: {data['choghadiya']}\n\n"
                 f"IST Time: {data['datetime']}")
    plt.text(0.5, 0.95, info_text, ha="center", va="top", fontsize=12, color="#00ffcc", transform=ax.transAxes)

    # Table
    table = plt.table(cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center")

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.4)

    # Style table
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        if row == 0:
            cell.set_facecolor("#004466")
            cell.set_text_props(color="cyan", fontweight="bold")
        else:
            cell.set_facecolor("#2e2e3e")
            cell.set_text_props(color="white")

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

# === Main ===
if __name__ == "__main__":
    data = get_planet_data()

    # Text msg
    msg = (f"🪐 Panchang & Planetary Positions\n\n"
           f"⏰ {data['datetime']}\n"
           f"🌙 Tithi: {data['tithi']} ({data['paksha']})\n"
           f"🧭 Disha Shool: {data['disha_shool']}\n"
           f"📿 Choghadiya: {data['choghadiya']}")
    send_telegram_alert(msg)

    # Image
    generate_panchang_image(data, "panchang.png")
    send_telegram_image("panchang.png", caption="🌟 Panchang Snapshot")



