"""
Sadece SACHSEN ve SACHSEN-ANHALT eyaletleri için
imsakiye verilerini Diyanet İmsakiye sayfasından
yeniden ve birebir çeker.

Diğer eyaletlere DOKUNMAZ.

Kullanım:
    py refetch_sachsen_states.py
"""

import json
import time

from fetch_germany_imsakiye import get_city_imsakiye_from_diyanet

TARGET_COUNTRY = "ALMANYA"
TARGET_STATES = ["SACHSEN", "SACHSEN-ANHALT"]


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main() -> None:
    countries = load_json("countries.json", {})
    imsakiye_data = load_json("imsakiye-data.json", {})
    bayram_data = load_json("bayram-namazi.json", {})

    if TARGET_COUNTRY not in countries:
        print(f"[HATA] countries.json içinde '{TARGET_COUNTRY}' bulunamadı.")
        return

    states_info = countries[TARGET_COUNTRY].get("states", {})

    print("======================================================")
    print("SACHSEN ve SACHSEN-ANHALT için imsakiye yeniden çekiliyor")
    print("Kaynak: https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx")
    print("Diğer eyaletlere DOKUNULMAYACAK.")
    print("======================================================\n")

    total_cities = 0
    for code in TARGET_STATES:
        state = states_info.get(code)
        if not state:
            print(f"[WARN] countries.json içinde eyalet bulunamadı: {code}")
            continue
        total_cities += len(state.get("cities", []))

    processed = 0

    imsakiye_data.setdefault(TARGET_COUNTRY, {})
    bayram_data.setdefault(TARGET_COUNTRY, {})

    for state_code in TARGET_STATES:
        state = states_info.get(state_code)
        if not state:
            continue

        state_name = state["name"]
        cities = state.get("cities", [])

        print(f"\n--- {state_name} ({state_code}) - {len(cities)} şehir ---")

        imsakiye_data[TARGET_COUNTRY].setdefault(state_code, {})
        bayram_data[TARGET_COUNTRY].setdefault(state_code, {})

        for city in cities:
            processed += 1
            print(f"  [{processed}/{total_cities}] {state_name} / {city}...", end=" ", flush=True)

            data, bayram = get_city_imsakiye_from_diyanet(city, TARGET_COUNTRY, state_code)
            if not data:
                print("[HATA] VERİ ALINAMADI - MEVCUT VERİ KORUNUYOR")
                # Eski veri varsa olduğu gibi bırakıyoruz
                continue

            imsakiye_data[TARGET_COUNTRY][state_code][city] = data
            if bayram:
                bayram_data[TARGET_COUNTRY][state_code][city] = bayram

            print(f"[OK] {len(data)} gün", end="")
            if bayram:
                print(f" (Bayram: {bayram})")
            else:
                print()

            time.sleep(0.5)

    # Sadece güncellenen/veri yüklenen halleriyle dosyaları geri yaz
    with open("imsakiye-data.json", "w", encoding="utf-8") as f:
        json.dump(imsakiye_data, f, ensure_ascii=False, indent=2)
    with open("bayram-namazi.json", "w", encoding="utf-8") as f:
        json.dump(bayram_data, f, ensure_ascii=False, indent=2)

    print("\n======================================================")
    print("SACHSEN ve SACHSEN-ANHALT için güncelleme tamamlandı.")
    print("Diğer eyalet verileri aynen korundu.")
    print("======================================================")


if __name__ == "__main__":
    main()

