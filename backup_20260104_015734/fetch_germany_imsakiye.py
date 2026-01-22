"""
Diyanet İmsakiye (https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx)
üzerinden SADECE ALMANYA için:
 - Tüm eyaletleri ve şehirleri çeker
 - Her şehir için Ramazan 1447 / 2026 imsakiye tablosunu çeker
 - Bayram namazı vaktini de yakalamaya çalışır

Çıktılar:
 - countries.json         -> Sadece ALMANYA yapısı (eyalet + şehirler)
 - imsakiye-data.json     -> Şehir bazlı imsakiye verileri
 - bayram-namazi.json     -> Şehir bazlı bayram namazı vakitleri

NOT: Tüm veriler birebir Diyanet sayfasından, form POST istekleri ile alınır;
     yaklaşık / hesaplanmış saat KESİNLİKLE kullanılmaz.
"""

import json
import re
import time
from typing import Dict, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx"

session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": BASE_URL,
    }
)


def get_form_data(soup: BeautifulSoup) -> Dict[str, str]:
    """Sayfadaki ASP.NET form gizli alanlarını (__VIEWSTATE vb.) toplar."""
    data: Dict[str, str] = {}

    for name in ("__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"):
        inp = soup.find("input", {"name": name})
        if inp:
            data[name] = inp.get("value", "")

    # ASP.NET zorunlu alanları
    data.setdefault("__EVENTTARGET", "")
    data.setdefault("__EVENTARGUMENT", "")
    data.setdefault("__LASTFOCUS", "")

    return data


def normalize_name(name: str) -> str:
    """Şehir/eyalet ismini büyük harfe çekerek Türkçe karakterleri normalize eder."""
    name = name.upper()
    tr_map = str.maketrans(
        {
            "Ü": "U",
            "Ö": "O",
            "Ş": "S",
            "İ": "I",
            "I": "I",
            "Ç": "C",
            "Ğ": "G",
            "-": " ",
        }
    )
    return name.translate(tr_map).strip()


def get_all_germany_cities() -> Dict[str, Dict[str, object]]:
    """
    Diyanet imsakiyesi sayfasından ALMANYA için:
      - Almanya ülkesini seçer
      - Tüm eyaletleri ve bu eyaletlere bağlı şehirleri okur

    Dönüş:
      {
        "BAYERN": {
          "name": "Bayern",
          "cities": ["Aichach", "München", ...]
        },
        ...
      }
    """
    print("=" * 70)
    print("Diyanet İmsakiye - Almanya eyalet ve şehir listesi çekiliyor")
    print(f"Kaynak: {BASE_URL}")
    print("=" * 70)

    # Eyalet mapping (Diyanet'teki yazılış -> kod / gösterim adı)
    # DİKKAT: Anahtarlar normalize_name() çıktısıyla aynı formatta tutuluyor
    # (büyük harf, Türkçe karakterler sadeleştirilmiş, '-' yerine ' ').
    state_mapping: Dict[str, Dict[str, str]] = {
        "BADEN WURTTEMBERG": {"code": "BADEN-WÜRTTEMBERG", "name": "Baden-Württemberg"},
        "BADEN WÜRTTEMBERG": {"code": "BADEN-WÜRTTEMBERG", "name": "Baden-Württemberg"},
        "BAYERN": {"code": "BAYERN", "name": "Bayern"},
        "BERLIN": {"code": "BERLIN", "name": "Berlin"},
        "BRANDENBURG": {"code": "BRANDENBURG", "name": "Brandenburg"},
        "BREMEN": {"code": "BREMEN", "name": "Bremen"},
        "HAMBURG": {"code": "HAMBURG", "name": "Hamburg"},
        "HESSEN": {"code": "HESSEN", "name": "Hessen"},
        # Mecklenburg-Vorpommern tüm varyasyonlar
        "MECKLENBURG VORPOMMERN": {
            "code": "MECKLENBURG-VORPOMMERN",
            "name": "Mecklenburg-Vorpommern",
        },
        "MECKLENBURG-VORPOMMERN": {
            "code": "MECKLENBURG-VORPOMMERN",
            "name": "Mecklenburg-Vorpommern",
        },
        # Nordrhein-Westfalen
        "NORDRHEIN WESTFALEN": {"code": "NORDRHEIN-WESTFALEN", "name": "Nordrhein-Westfalen"},
        "NORDRHEIN-WESTFALEN": {"code": "NORDRHEIN-WESTFALEN", "name": "Nordrhein-Westfalen"},
        # Rheinland-Pfalz
        "RHEINLAND PFALZ": {"code": "RHEINLAND-PFALZ", "name": "Rheinland-Pfalz"},
        "RHEINLAND-PFALZ": {"code": "RHEINLAND-PFALZ", "name": "Rheinland-Pfalz"},
        "NIEDERSACHSEN": {"code": "NIEDERSACHSEN", "name": "Niedersachsen"},
        "SAARLAND": {"code": "SAARLAND", "name": "Saarland"},
        "SACHSEN": {"code": "SACHSEN", "name": "Sachsen"},
        "SACHSEN ANHALT": {"code": "SACHSEN-ANHALT", "name": "Sachsen-Anhalt"},
        "SACHSEN-ANHALT": {"code": "SACHSEN-ANHALT", "name": "Sachsen-Anhalt"},
        "SCHLESWIG HOLSTEIN": {"code": "SCHLESWIG-HOLSTEIN", "name": "Schleswig-Holstein"},
        "SCHLESWIG-HOLSTEIN": {"code": "SCHLESWIG-HOLSTEIN", "name": "Schleswig-Holstein"},
        "THURINGEN": {"code": "THÜRINGEN", "name": "Thüringen"},
        "THÜRINGEN": {"code": "THÜRINGEN", "name": "Thüringen"},
    }

    # 1) Ana sayfayı al
    print("\n1) Ana sayfa yükleniyor...")
    resp = session.get(BASE_URL, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    form_data = get_form_data(soup)

    # 2) Ülke select'inden ALMANYA'yı bul
    country_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlUlkeler"}) or soup.find(
        "select", {"name": re.compile(r"ddlUlkeler", re.I)}
    )
    germany_value: Optional[str] = None

    if not country_select:
        raise RuntimeError("Ülke select'i bulunamadı (ddlUlkeler). Diyanet sayfası değişmiş olabilir.")

    for opt in country_select.find_all("option"):
        text = opt.get_text(strip=True).upper()
        if "ALMANYA" in text:
            germany_value = opt.get("value", "")
            break

    if not germany_value:
        raise RuntimeError("Ülke listesinde ALMANYA bulunamadı.")

    # Konsol encoding sorunları yaşamamak için sadece ASCII karakter kullanalım
    print(f"   [OK] ALMANYA bulundu (value={germany_value})")

    # 3) Form POST ile ALMANYA'yı seç
    form_data["ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler"] = germany_value
    form_data["__EVENTTARGET"] = "ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler"
    form_data["__EVENTARGUMENT"] = ""

    resp = session.post(BASE_URL, data=form_data, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    form_data = get_form_data(soup)

    # 4) Eyalet select'ini (ddlSehirler) bul
    print("\n2) Eyalet listesi alınıyor...")
    state_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlSehirler"}) or soup.find(
        "select", {"name": re.compile(r"ddlSehirler", re.I)}
    )

    if not state_select:
        raise RuntimeError("Eyalet/Şehir select'i (ddlSehirler) bulunamadı.")

    states_result: Dict[str, Dict[str, object]] = {}

    options = state_select.find_all("option")
    print(f"   [OK] {len(options)} satır bulundu (ilk satır genelde '-- Şehir Seçin --')")

    for opt in options:
        state_text = opt.get_text(strip=True)
        state_val = opt.get("value", "")

        if not state_text or state_text.startswith("--"):
            continue

        key = normalize_name(state_text)
        mapping = state_mapping.get(key)
        if not mapping:
            print(f"   [WARN] Bilinmeyen eyalet ismi, atlanıyor: '{state_text}'")
            continue

        code = mapping["code"]
        display_name = mapping["name"]
        print(f"   > {display_name} ({code}) için şehirler çekiliyor...")

        cities, form_data = get_cities_for_state(form_data, state_val, display_name)
        states_result[code] = {"name": display_name, "cities": sorted(cities)}

        print(f"     [OK] {len(cities)} şehir")
        time.sleep(0.5)

    # 5) countries.json yapısı
    countries_structure = {"ALMANYA": {"name": "ALMANYA", "states": states_result}}

    with open("countries.json", "w", encoding="utf-8") as f:
        json.dump(countries_structure, f, ensure_ascii=False, indent=2)

    total_states = len(states_result)
    total_cities = sum(len(info["cities"]) for info in states_result.values())

    print("\n" + "=" * 70)
    print("Almanya eyalet/şehir listesi tamamlandı")
    print("=" * 70)
    print(f"  Toplam eyalet: {total_states}")
    print(f"  Toplam şehir:  {total_cities}")

    return states_result


def get_cities_for_state(
    form_data: Dict[str, str], state_value: str, state_name: str
) -> Tuple[List[str], Dict[str, str]]:
    """Belirli bir eyalet seçili iken, ilgili şehir/ilçe listesini döndürür."""
    local_form = dict(form_data)
    local_form["ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler"] = state_value
    local_form["__EVENTTARGET"] = "ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler"
    local_form["__EVENTARGUMENT"] = ""

    resp = session.post(BASE_URL, data=local_form, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    city_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlIlceler"}) or soup.find(
        "select", {"name": re.compile(r"ddlIlceler", re.I)}
    )

    cities: List[str] = []
    if city_select:
        for opt in city_select.find_all("option"):
            name = opt.get_text(strip=True)
            if name and not name.startswith("--"):
                cities.append(name)

    return cities, get_form_data(soup)


def get_city_imsakiye_from_diyanet(
    city_name: str, country_code: str = "ALMANYA", state_code: Optional[str] = None
) -> Tuple[Optional[List[Dict[str, str]]], Optional[str]]:
    """
    Tek bir şehir için Diyanet imsakiyesini çeker.
    Tamamen form POST ile çalışır, ek API veya hesaplama YOK.
    """
    try:
        # 1) Ana sayfa
        resp = session.get(BASE_URL, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        form_data = get_form_data(soup)

        # 2) Ülke (ALMANYA)
        country_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlUlkeler"}) or soup.find(
            "select", {"name": re.compile(r"ddlUlkeler", re.I)}
        )
        if not country_select:
            raise RuntimeError("Ülke select'i bulunamadı (ddlUlkeler).")

        country_value = None
        for opt in country_select.find_all("option"):
            text = opt.get_text(strip=True).upper()
            if country_code.upper() in text or "ALMANYA" in text:
                country_value = opt.get("value", "")
                break
        if not country_value:
            raise RuntimeError("ALMANYA ülke seçeneklerinde bulunamadı.")

        form_data["ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler"] = country_value
        form_data["__EVENTTARGET"] = "ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler"
        form_data["__EVENTARGUMENT"] = ""

        resp = session.post(BASE_URL, data=form_data, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        form_data = get_form_data(soup)
        time.sleep(0.3)

        # 3) Eyalet (state_code verilmişse)
        if state_code:
            state_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlSehirler"}) or soup.find(
                "select", {"name": re.compile(r"ddlSehirler", re.I)}
            )
            if not state_select:
                raise RuntimeError("Eyalet select'i (ddlSehirler) bulunamadı.")

            norm_target = normalize_name(state_code)
            state_value = None
            for opt in state_select.find_all("option"):
                text = opt.get_text(strip=True)
                if not text or text.startswith("--"):
                    continue
                if normalize_name(text) == norm_target:
                    state_value = opt.get("value", "")
                    break

            if not state_value:
                raise RuntimeError(f"Eyalet bulunamadı: {state_code}")

            form_data["ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler"] = state_value
            form_data["__EVENTTARGET"] = "ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler"
            form_data["__EVENTARGUMENT"] = ""

            resp = session.post(BASE_URL, data=form_data, timeout=30)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            form_data = get_form_data(soup)
            time.sleep(0.3)

        # 4) Şehir (ddlIlceler)
        city_select = soup.find("select", {"id": "cphMainSlider_solIcerik_ddlIlceler"}) or soup.find(
            "select", {"name": re.compile(r"ddlIlceler", re.I)}
        )
        if not city_select:
            raise RuntimeError("Şehir/İlçe select'i (ddlIlceler) bulunamadı.")

        norm_target_city = normalize_name(city_name)
        city_value = None
        city_display_name = None
        for opt in city_select.find_all("option"):
            text = opt.get_text(strip=True)
            if not text or text.startswith("--"):
                continue
            if normalize_name(text) == norm_target_city:
                city_value = opt.get("value", "")
                city_display_name = text
                break

        if not city_value:
            raise RuntimeError(f"Şehir bulunamadı: {city_name}")

        form_data["ctl00$ctl00$cphMainSlider$solIcerik$ddlIlceler"] = city_value
        form_data["__EVENTTARGET"] = "ctl00$ctl00$cphMainSlider$solIcerik$ddlIlceler"
        form_data["__EVENTARGUMENT"] = ""

        resp = session.post(BASE_URL, data=form_data, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        time.sleep(0.3)

        # 5) Tabloyu oku
        imsakiye_data: List[Dict[str, str]] = []
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            for row in rows[1:]:  # başlığı atla
                cells = row.find_all(["td", "th"])
                if len(cells) < 7:
                    continue

                hicri = cells[0].get_text(strip=True)
                miladi = cells[1].get_text(strip=True)
                imsak = cells[2].get_text(strip=True)
                gunes = cells[3].get_text(strip=True)
                ogle = cells[4].get_text(strip=True)
                ikindi = cells[5].get_text(strip=True)
                aksam = cells[6].get_text(strip=True)
                yatsi = cells[7].get_text(strip=True) if len(cells) > 7 else ""

                # Boş / başlık satırlarını ayıkla
                if not (hicri and miladi and imsak):
                    continue
                if "HİCRİ" in hicri.upper() or "MİLADİ" in miladi.upper():
                    continue
                if "IMSAK" in imsak.upper():
                    continue
                if ":" not in imsak:
                    continue

                if "RAMAZAN" not in hicri.upper():
                    # Sadece Ramazan günleri isteniyor; diğer ayları at
                    continue

                imsakiye_data.append(
                    {
                        "hicri": hicri,
                        "miladi": miladi,
                        "imsak": imsak,
                        "gunes": gunes,
                        "ogle": ogle,
                        "ikindi": ikindi,
                        "aksam": aksam,
                        "yatsi": yatsi,
                    }
                )

        # 6) Gün sayısı ve Ramazan günü kontrolü (29 veya 30 olmalı)
        if not imsakiye_data:
            return None, None

        # Hicri gün numaralarını yakala
        day_nums: List[int] = []
        for row in imsakiye_data:
            m = re.search(r"(\d+)\s*RAMAZAN", row["hicri"].upper())
            if m:
                day_nums.append(int(m.group(1)))

        unique_days = sorted(set(day_nums))
        if not unique_days:
            return None, None

        max_day = max(unique_days)
        if max_day not in (29, 30):
            # Diyanet Ramazan tablosu değilse güvenmeyelim
            return None, None

        # 7) Bayram namazı (varsa)
        page_text = soup.get_text(" ", strip=True)
        bayram_pattern = re.compile(r"Bayram\s+Namazı\s*:?\s*(\d{1,2}:\d{2})", re.IGNORECASE)
        m = bayram_pattern.search(page_text)
        bayram_namazi = m.group(1) if m else None

        # Son bir güvenlik: satır sayısı ile gün sayısı uyuşmalı
        if len(unique_days) < 25:
            # Ramazan neredeyse hiç yok; güvenmeyelim
            return None, None

        return imsakiye_data, bayram_namazi

    except Exception as e:
        print(f"      [HATA] {city_name}: {str(e)[:80]}")
        return None, None


def fetch_imsakiye_for_all_germany(states: Dict[str, Dict[str, object]]) -> None:
    """
    Verilen Almanya eyalet/şehir yapısı için tüm imsakiye verilerini çeker
    ve imsakiye-data.json + bayram-namazi.json olarak kaydeder.
    """
    imsakiye_data: Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]] = {"ALMANYA": {}}
    bayram_data: Dict[str, Dict[str, Dict[str, str]]] = {"ALMANYA": {}}

    total_cities = sum(len(info["cities"]) for info in states.values())
    processed = 0

    print("\n" + "=" * 70)
    print("Almanya için TÜM şehirlerin Ramazan imsakiye verileri çekiliyor")
    print("=" * 70)

    for state_code, state_info in states.items():
        state_name = state_info["name"]
        cities: List[str] = state_info["cities"]  # type: ignore

        print(f"\n--- EYALET: {state_name} ({state_code}) - {len(cities)} şehir ---")

        imsakiye_data["ALMANYA"].setdefault(state_code, {})
        bayram_data["ALMANYA"].setdefault(state_code, {})

        for city in cities:
            processed += 1
            print(f"  [{processed}/{total_cities}] {city}...", end=" ", flush=True)

            data, bayram = get_city_imsakiye_from_diyanet(city, "ALMANYA", state_code)
            if not data:
                print("[ERROR] VERİ ALINAMADI (DURDURULDU)")
                raise RuntimeError(
                    f"{state_name} / {city} için Diyanet imsakiyesi alınamadı. "
                    "Lütfen siteyi ve scripti kontrol edin."
                )

            imsakiye_data["ALMANYA"][state_code][city] = data
            if bayram:
                bayram_data["ALMANYA"][state_code][city] = bayram

            print(f"[OK] {len(data)} gün", end="")
            if bayram:
                print(f" (Bayram: {bayram})")
            else:
                print()

            time.sleep(0.5)

        # Her eyalet sonunda ara kayıt
        with open("imsakiye-data.json", "w", encoding="utf-8") as f:
            json.dump(imsakiye_data, f, ensure_ascii=False, indent=2)
        with open("bayram-namazi.json", "w", encoding="utf-8") as f:
            json.dump(bayram_data, f, ensure_ascii=False, indent=2)
        print(f"  -> {state_name} tamamlandı, ara kayıt yapıldı.")

    print("\n" + "=" * 70)
    print("TÜM ŞEHİRLER BAŞARIYLA ÇEKİLDİ")
    print("=" * 70)


def main() -> None:
    """
    Ana akış:
      1) Almanya için eyalet + şehir listesini Diyanet'ten güncel olarak çek
      2) Bu listeyi countries.json olarak kaydet
      3) Her şehir için imsakiye tablosunu çek ve JSON'lara yaz

    Çalıştırma:
      python fetch_germany_imsakiye.py
    """
    # 1) Almanya eyalet / şehir listesi
    states = get_all_germany_cities()

    # 2) Tüm şehirler için imsakiye verileri
    fetch_imsakiye_for_all_germany(states)


if __name__ == "__main__":
    main()

