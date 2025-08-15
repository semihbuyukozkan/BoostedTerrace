# scripts/load_csv_to_db.py
"""
generate_synthetic_csv.py ile üretilen CSV'yi DB'ye yazar.
Yükleme öncesi temizleme davranışı:
  - varsayılan: sadece source="synthetic" kayıtları siler
  - --truncate all : tüm SensorReading tablosunu siler
  - --truncate none: hiç silmez, ekler (append)

Çalıştırma (önerilen):
  python -m scripts.load_csv_to_db --path data/synthetic_readings.csv
  python -m scripts.load_csv_to_db --truncate synthetic
"""

import csv
import argparse
from datetime import datetime
from typing import Optional

from database.db import SessionLocal, Base, engine
from database.orm_models import SensorReading

def parse_ts(ts_str: str) -> Optional[datetime]:
    try:
        # ISO 8601 -> datetime; "Z" varsa +00:00'a çevir
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None

def truncate_data(mode: str) -> int:
    """
    mode: 'synthetic' | 'all' | 'none'
    Dönüş: silinen satır sayısı
    """
    if mode not in {"synthetic", "all", "none"}:
        raise ValueError("truncate mode must be one of: synthetic, all, none")

    if mode == "none":
        return 0

    with SessionLocal() as s:
        if mode == "all":
            deleted = s.query(SensorReading).delete()
        else:  # synthetic
            deleted = s.query(SensorReading).filter(SensorReading.source == "synthetic").delete()
        s.commit()
        return deleted

def load_csv(path: str, batch_size: int = 1000) -> int:
    """
    CSV'yi batch halinde DB'ye yazar. Dönüş: eklenen satır sayısı.
    """
    inserted = 0
    with SessionLocal() as s, open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            rec = SensorReading(
                soil_moisture=float(row["soil_moisture"]),
                ph=float(row["ph"]),
                wind_speed=float(row["wind_speed"]),
                ts=parse_ts(row["ts"]),
                source="synthetic",
            )
            batch.append(rec)
            if len(batch) >= batch_size:
                s.add_all(batch)
                s.commit()
                inserted += len(batch)
                batch.clear()

        if batch:
            s.add_all(batch)
            s.commit()
            inserted += len(batch)
    return inserted

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="data/synthetic_readings.csv", help="CSV dosya yolu")
    ap.add_argument("--batch-size", type=int, default=1000)
    ap.add_argument("--truncate", choices=["synthetic", "all", "none"], default="synthetic",
                    help="Yüklemeden önce neyi sileceğini seç")
    args = ap.parse_args()

    # tablo garanti
    Base.metadata.create_all(bind=engine)

    deleted = truncate_data(args.truncate)
    if deleted:
        print(f"Temizlendi: {deleted} satır ({args.truncate})")

    inserted = load_csv(args.path, args.batch_size)
    print(f"✓ DB'ye yazıldı: {inserted} satır (kaynak: synthetic)")

if __name__ == "__main__":
    main()
