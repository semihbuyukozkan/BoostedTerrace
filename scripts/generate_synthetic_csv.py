"""
Mantıklı sentetik zaman serisi üretimi:
- Rüzgâr ↑ -> buharlaşma ↑ -> nem yavaş azalır
- Yağmur olayları -> nem ani ama kontrollü artar (azalan getiri)
- pH küçük random walk + 6.5 hedefine çekilme
Çıktı: CSV (ts, wind_speed, soil_moisture, ph)
"""

import csv
import math
import random
from datetime import datetime, timezone, timedelta
import argparse

# ==== Parametreler ====
# Yağmur
EXPECTED_RAIN_EVENTS_PER_DAY = 1.8      # günde ~1-2 olay
RAIN_COOLDOWN_SECS = 30 * 60            # yağmurdan sonra min 30 dk ara
RAIN_BOOST_MIN, RAIN_BOOST_MAX = 3.0, 8.0
RAIN_SOFT_CAP = 95.0                     # nem, pratikte %95 üstüne zor çıksın

# Buharlaşma
EVAP_PER_MIN = 0.001                     # (önceden 0.005 idi)
WIND_EVAP_FACTOR = 0.15                  # rüzgâr etkisi

# Kısıtlar / hedefler
MOISTURE_FLOOR = 7.0                     # taban nem
MOISTURE_CEIL = 100.0                    # sert üst limit (emniyet)
PH_TARGET = 6.5
PH_DRIFT = 0.006
PH_PULL = 0.02

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def rain_probability_per_tick(step_seconds: int) -> float:
    """Günlük beklenen yağmur sayısına göre tik başına olasılık."""
    ticks_per_day = max(1, int(86400 / step_seconds))
    p = EXPECTED_RAIN_EVENTS_PER_DAY / ticks_per_day
    return clamp(p, 0.0, 0.5)

def generate_series(start_ts: datetime, days: int, step_seconds: int):
    ts = start_ts
    end_ts = start_ts + timedelta(days=days)

    # başlangıç durumları
    soil_moisture = random.uniform(20.0, 40.0)   # %
    ph = PH_TARGET + random.uniform(-0.2, 0.2)
    rain_cooldown = 0
    p_rain = rain_probability_per_tick(step_seconds)

    while ts < end_ts:
        # Günlük rüzgâr paterni (sinüs) + gürültü
        seconds_in_day = ts.hour * 3600 + ts.minute * 60 + ts.second
        daily_phase = 2 * math.pi * (seconds_in_day / 86400.0)
        base_wind = 3.0 + 2.0 * math.sin(daily_phase - math.pi / 2)  # gündüz ↑, gece ↓
        gust = random.uniform(-0.8, 0.8)
        wind_speed = clamp(base_wind + gust, 0.0, 12.0)

        # Yağmur olayı (olasılık + cooldown)
        if rain_cooldown == 0 and random.random() < p_rain:
            rain_happens = True
            rain_cooldown = int(RAIN_COOLDOWN_SECS / step_seconds)
        else:
            rain_happens = False
            rain_cooldown = max(0, rain_cooldown - 1)

        # Buharlaşma (step'e ölçekli) + yüksek nemde ekstra etki
        evap_per_sec = EVAP_PER_MIN / 60.0
        high_moisture_boost = max(0.0, (soil_moisture - 80.0) / 20.0) * 0.2  # 80+ nemde %0–20 ekstra
        evap = evap_per_sec * step_seconds * (1.0 + WIND_EVAP_FACTOR * wind_speed + high_moisture_boost)

        # Yağmur etkisi: mevcut neme bağlı azalan getiri
        if rain_happens:
            base_gain = random.uniform(RAIN_BOOST_MIN, RAIN_BOOST_MAX)
            if soil_moisture >= 60.0:
                if soil_moisture >= 95.0:
                    factor = 0.2
                elif soil_moisture >= 80.0:
                    factor = 0.5
                else:
                    factor = 0.8
                gain = base_gain * factor
            else:
                gain = base_gain

            # 95'e yaklaşınca artışı iyice kırp
            if soil_moisture >= RAIN_SOFT_CAP:
                gain *= 0.2

            soil_moisture += gain

        # Buharlaşmayı uygula ve sınırla
        soil_moisture -= evap
        soil_moisture = clamp(soil_moisture, MOISTURE_FLOOR, MOISTURE_CEIL)
        if soil_moisture > RAIN_SOFT_CAP:  # yumuşak kırpma
            soil_moisture = RAIN_SOFT_CAP + 0.5 * (soil_moisture - RAIN_SOFT_CAP)

        # pH: küçük random walk + hedefe çekilme
        ph += random.uniform(-PH_DRIFT, PH_DRIFT) + PH_PULL * (PH_TARGET - ph)
        ph = clamp(ph, 4.5, 8.5)

        yield {
            "ts": ts.replace(tzinfo=timezone.utc).isoformat(),
            "wind_speed": round(wind_speed, 2),
            "soil_moisture": round(soil_moisture, 2),
            "ph": round(ph, 2),
        }
        ts += timedelta(seconds=step_seconds)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="Kaç gün üretilecek")
    ap.add_argument("--step", type=int, default=900, help="Örnekleme aralığı (saniye) [varsayılan: 900=15 dk]")
    ap.add_argument("--out", default="data/synthetic_readings.csv", help="Çıktı CSV yolu")
    args = ap.parse_args()

    start = datetime.now(timezone.utc).replace(microsecond=0)
    rows = list(generate_series(start, args.days, args.step))

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "wind_speed", "soil_moisture", "ph"])
        w.writeheader()
        w.writerows(rows)

    print(f"Successfully created: {args.out}  (rows: {len(rows)}, step={args.step}s, days={args.days})")

if __name__ == "__main__":
    main()

#Çalıştırmak için:
#python scripts/generate_synthetic_csv.py --days 7 --step 900