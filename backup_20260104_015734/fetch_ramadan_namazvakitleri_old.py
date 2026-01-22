"""
Diyanet Namaz Vakitleri - Ramazan Ayı Verilerini İndirme Scripti
https://namazvakitleri.diyanet.gov.tr/ adresinden veri çeker
Sadece Almanya - Niedersachsen ve Bremen eyaletleri için
Selenium kullanarak JavaScript ile dinamik yüklenen içeriği çeker
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import sys
import io

# Windows console encoding sorununu çöz
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR"

# Global driver - reuse for all cities
driver = None

def init_driver():
    """Chrome driver'ı başlat"""
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
    return driver

def close_driver():
    """Chrome driver'ı kapat"""
    global driver
    if driver:
        driver.quit()
        driver = None

def normalize_name(name):
    """Ä°sim normalizasyonu (karÅŸÄ±laÅŸtÄ±rma iÃ§in)"""
    name = name.upper()
    # TÃ¼rkÃ§e karakterleri normalize et
    replacements = {
        'Ãœ': 'U', 'Ã–': 'O', 'Å': 'S', 'Ä°': 'I', 'Ã‡': 'C', 'Ä': 'G',
        '-': ' ', '_': ' ', '.': ' ', ',': ' '
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Ã‡oklu boÅŸluklarÄ± tek boÅŸluÄŸa Ã§evir
    name = ' '.join(name.split())
    return name.strip()

def get_city_ramadan_data(city_name, state_name):
    """
    Belirli bir ÅŸehir iÃ§in Ramazan ayÄ± namaz vakitlerini Ã§eker
    """
    print(f"\n{'='*70}")
    print(f"Åehir: {city_name}, Eyalet: {state_name}")
    print(f"{'='*70}")
    
    try:
        # Ana sayfayÄ± Ã§ek
        print("1. Ana sayfa yÃ¼kleniyor...")
        response = session.get(BASE_URL, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"[ERROR] Ana sayfa yÃ¼klenemedi: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ãœlke dropdown'Ä±nÄ± bul (ALMANYA)
        print("2. Ãœlke seÃ§imi yapÄ±lÄ±yor (ALMANYA)...")
        country_select = None
        
        # TÃ¼m select'leri kontrol et
        all_selects = soup.find_all('select')
        for select in all_selects:
            options = select.find_all('option')
            for option in options:
                text = option.get_text(strip=True)
                if 'ALMANYA' in text.upper() or 'GERMANY' in text.upper():
                    country_select = select
                    break
            if country_select:
                break
        
        if not country_select:
            print("[ERROR] Ãœlke dropdown bulunamadÄ±")
            return None
        
        # ALMANYA'yÄ± seÃ§
        options = country_select.find_all('option')
        country_value = None
        for option in options:
            text = option.get_text(strip=True)
            if 'ALMANYA' in text.upper() or 'GERMANY' in text.upper():
                country_value = option.get('value', '') or text
                print(f"[OK] Ulke bulundu: {text} (value: {country_value})")
                break
        
        if not country_value:
            print("[ERROR] ALMANYA bulunamadÄ±")
            return None
        
        # Ãœlke seÃ§imi iÃ§in form gÃ¶nder (eÄŸer JavaScript gerektiriyorsa)
        # Alternatif: URL parametreleri ile direkt ÅŸehir sayfasÄ±na git
        # Ã–nce farklÄ± URL formatlarÄ±nÄ± dene
        
        normalized_state = normalize_name(state_name).replace(' ', '-')
        normalized_city = normalize_name(city_name).replace(' ', '-')
        
        # ALMANYA country_id = 13
        possible_urls = [
            f"{BASE_URL}/13/{normalized_state}/{normalized_city}",  # 13 = ALMANYA
            f"{BASE_URL}/ALMANYA/{normalized_state}/{normalized_city}",
            f"{BASE_URL}/{normalized_state}/{normalized_city}",
            f"{BASE_URL}?country=13&state={normalized_state}&city={normalized_city}",
            f"{BASE_URL}?country=ALMANYA&state={normalized_state}&city={normalized_city}",
        ]
        
        html = None
        successful_url = None
        
        for attempt in range(3):  # Her URL için 3 deneme
            for url in possible_urls:
                print(f"3. URL deneniyor (deneme {attempt+1}/3): {url}")
                try:
                    response = session.get(url, timeout=30, allow_redirects=True)
                    response.encoding = 'utf-8'
                    
                    # Sayfa içeriğini kontrol et
                    if response.status_code == 200:
                        page_text = response.text.upper()
                        city_upper = city_name.upper()
                        
                        # Şehir adı, tablo, namaz veya ramazan kelimeleri geçiyorsa başarılı
                        if (city_upper in page_text or 'TABLO' in page_text or 
                            'NAMAZ' in page_text or 'RAMAZAN' in page_text or
                            'AYLIK' in page_text or 'IMSAKIYE' in page_text):
                            html = response.text
                            successful_url = url
                            print(f"[OK] URL başarılı: {url}")
                            break
                    
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"[ERROR] URL hatası: {e}")
                    time.sleep(2)  # Hata durumunda bekle
                    continue
            
            if html:
                break
            
            # Tüm URL'ler başarısız olduysa, biraz bekle ve tekrar dene
            if attempt < 2:
                print(f"   Tüm URL'ler başarısız, {3*(attempt+1)} saniye bekleniyor...")
                time.sleep(3 * (attempt + 1))
        
        if not html:
            print("[ERROR] Åehir sayfasÄ± yÃ¼klenemedi")
            return None
        
        # HTML'i parse et
        soup = BeautifulSoup(html, 'html.parser')
        
        # "AylÄ±k Namaz Vakitleri" tablosunu bul
        print("4. Namaz vakitleri tablosu aranÄ±yor...")
        imsakiye_data = []
        bayram_namazi = None
        
        # TÃ¼m tablolarÄ± kontrol et
        tables = soup.find_all('table')
        print(f"   Bulunan tablo sayÄ±sÄ±: {len(tables)}")
        
        for table_idx, table in enumerate(tables):
            table_text = table.get_text()
            
            # Ramazan veya AylÄ±k iÃ§eren tabloyu bul
            if 'RAMAZAN' in table_text.upper() or 'AYLIK' in table_text.upper() or 'NAMAZ' in table_text.upper():
                print(f"   Tablo {table_idx + 1} kontrol ediliyor (Ramazan/AylÄ±k iÃ§eriyor)...")
                
                rows = table.find_all('tr')
                print(f"   Tablo satÄ±r sayÄ±sÄ±: {len(rows)}")
                
                for row_idx, row in enumerate(rows):
                    if row_idx == 0:
                        continue  # BaÅŸlÄ±k satÄ±rÄ±nÄ± atla
                    
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 7:
                        try:
                            # HÃ¼cre sÄ±rasÄ±: Miladi Tarih, Hicri Tarih, Ä°msak, GÃ¼neÅŸ, Ã–ÄŸle, Ä°kindi, AkÅŸam, YatsÄ±
                            miladi = cells[0].get_text(strip=True)
                            hicri = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            imsak = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                            gunes = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                            ogle = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                            ikindi = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                            aksam = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                            yatsi = cells[7].get_text(strip=True) if len(cells) > 7 else ''
                            
                            # BoÅŸ satÄ±rlarÄ± ve baÅŸlÄ±k satÄ±rlarÄ±nÄ± atla
                            if (hicri and miladi and imsak and 
                                'HICRI' not in hicri.upper() and
                                'MILADI' not in miladi.upper() and
                                'IMSAK' not in imsak.upper() and
                                ':' in imsak):
                                
                                # Sadece Ramazan gÃ¼nlerini al (1-29 Ramazan)
                                ramazan_match = re.search(r'(\d+)\s*RAMAZAN', hicri.upper())
                                if ramazan_match:
                                    ramazan_day = int(ramazan_match.group(1))
                                    if 1 <= ramazan_day <= 29:
                                        imsakiye_data.append({
                                            'hicri': hicri,
                                            'miladi': miladi,
                                            'imsak': imsak,
                                            'gunes': gunes,
                                            'ogle': ogle,
                                            'ikindi': ikindi,
                                            'aksam': aksam,
                                            'yatsi': yatsi
                                        })
                        except Exception as e:
                            continue
                
                if len(imsakiye_data) >= 25:
                    print(f"[OK] Tablo {table_idx + 1}'den {len(imsakiye_data)} gÃ¼n veri Ã§ekildi")
                    break
        
        # EÄŸer tablo bulunamadÄ±ysa, tÃ¼m tablolarÄ± tekrar kontrol et (farklÄ± format)
        if len(imsakiye_data) < 25:
            print("   Yeterli veri bulunamadÄ±, tÃ¼m tablolar tekrar kontrol ediliyor...")
            for table in tables:
                rows = table.find_all('tr')
                for row_idx, row in enumerate(rows[1:], 1):  # Ä°lk satÄ±r baÅŸlÄ±k
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 7:
                        try:
                            # FarklÄ± sÄ±ralama olabilir, tÃ¼m hÃ¼creleri kontrol et
                            all_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            # Tarih formatÄ± iÃ§eren hÃ¼creleri bul
                            date_cell = None
                            time_cells = []
                            
                            for text in all_texts:
                                if 'RAMAZAN' in text.upper() or re.search(r'\d{1,2}\s*[A-Z]+\s*\d{4}', text):
                                    date_cell = text
                                elif re.search(r'\d{1,2}:\d{2}', text):
                                    time_cells.append(text)
                            
                            if date_cell and len(time_cells) >= 5:
                                ramazan_match = re.search(r'(\d+)\s*RAMAZAN', date_cell.upper())
                                if ramazan_match:
                                    ramazan_day = int(ramazan_match.group(1))
                                    if 1 <= ramazan_day <= 29:
                                        # Zaten eklenmiÅŸ mi kontrol et
                                        exists = any(item['hicri'] == date_cell for item in imsakiye_data)
                                        if not exists:
                                            imsakiye_data.append({
                                                'hicri': date_cell,
                                                'miladi': all_texts[0] if len(all_texts) > 0 else '',
                                                'imsak': time_cells[0] if len(time_cells) > 0 else '',
                                                'gunes': time_cells[1] if len(time_cells) > 1 else '',
                                                'ogle': time_cells[2] if len(time_cells) > 2 else '',
                                                'ikindi': time_cells[3] if len(time_cells) > 3 else '',
                                                'aksam': time_cells[4] if len(time_cells) > 4 else '',
                                                'yatsi': time_cells[5] if len(time_cells) > 5 else ''
                                            })
                        except Exception as e:
                            continue
        
        # Bayram namazÄ± vaktini bul
        print("5. Bayram namazÄ± vakti aranÄ±yor...")
        page_text = soup.get_text()
        bayram_pattern = re.compile(r'BAYRAM\s+NAMAZI\s*:?\s*(\d{1,2}:\d{2})', re.IGNORECASE)
        match = bayram_pattern.search(page_text)
        if match:
            bayram_namazi = match.group(1)
            print(f"[OK] Bayram namazÄ± vakti bulundu: {bayram_namazi}")
        else:
            # Alternatif: Bold veya strong etiketlerinde ara
            bold_texts = soup.find_all(['b', 'strong', 'span', 'div'])
            for bold in bold_texts:
                text = bold.get_text()
                match = bayram_pattern.search(text)
                if match:
                    bayram_namazi = match.group(1)
                    print(f"[OK] Bayram namazÄ± vakti bulundu (alternatif): {bayram_namazi}")
                    break
        
        # SonuÃ§larÄ± kontrol et
        if len(imsakiye_data) >= 25:
            print(f"\n[OK] BaÅŸarÄ±lÄ±! {len(imsakiye_data)} gÃ¼n veri Ã§ekildi")
            if bayram_namazi:
                print(f"[OK] Bayram namazÄ± vakti: {bayram_namazi}")
            return {
                'imsakiye': imsakiye_data,
                'bayram': bayram_namazi,
                'city': city_name,
                'state': state_name
            }
        else:
            print(f"\n[ERROR] Yetersiz veri: Sadece {len(imsakiye_data)} gÃ¼n Ã§ekildi (en az 25 gÃ¼n gerekli)")
            return None
            
    except Exception as e:
        print(f"\n[ERROR] Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_all_cities_for_states():
    """
    Niedersachsen ve Bremen eyaletlerindeki tÃ¼m ÅŸehirleri al
    imsakiye-data.json dosyasÄ±ndan ÅŸehir listesini Ã§Ä±karÄ±r
    """
    cities = {
        'NIEDERSACHSEN': [],
        'BREMEN': []
    }
    
    try:
        # imsakiye-data.json'dan ÅŸehir listesini Ã§Ä±kar
        with open('imsakiye-data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # JSON yapÄ±sÄ±: { "ALMANYA": { "NIEDERSACHSEN": { "CITY": [...] }, "BREMEN": { "CITY": [...] } } }
            if 'ALMANYA' in data:
                germany_data = data['ALMANYA']
                
                # Niedersachsen ÅŸehirleri
                if 'NIEDERSACHSEN' in germany_data:
                    cities['NIEDERSACHSEN'] = list(germany_data['NIEDERSACHSEN'].keys())
                
                # Bremen ÅŸehirleri
                if 'BREMEN' in germany_data:
                    cities['BREMEN'] = list(germany_data['BREMEN'].keys())
        
        print(f"\nÅehir listesi yÃ¼klendi:")
        print(f"  Niedersachsen: {len(cities['NIEDERSACHSEN'])} ÅŸehir")
        print(f"  Bremen: {len(cities['BREMEN'])} ÅŸehir")
        
        if len(cities['NIEDERSACHSEN']) == 0 and len(cities['BREMEN']) == 0:
            print("âš  HiÃ§ ÅŸehir bulunamadÄ±! JSON yapÄ±sÄ±nÄ± kontrol edin.")
            return None
        
    except FileNotFoundError:
        print("[ERROR] imsakiye-data.json bulunamadÄ±")
        print("  LÃ¼tfen Ã¶nce ÅŸehir listesini oluÅŸturun veya manuel olarak ekleyin")
        return None
    except Exception as e:
        print(f"[ERROR] Åehir listesi yÃ¼klenirken hata: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return cities

def main():
    """
    Ana fonksiyon: TÃ¼m ÅŸehirler iÃ§in Ramazan verilerini indir
    """
    print("="*70)
    print("Diyanet Namaz Vakitleri - Ramazan AyÄ± Verilerini Ä°ndirme")
    print("https://namazvakitleri.diyanet.gov.tr/")
    print("="*70)
    
    # Åehir listesini al
    cities = get_all_cities_for_states()
    if not cities:
        print("\n[ERROR] Åehir listesi alÄ±namadÄ±, Ã§Ä±kÄ±lÄ±yor...")
        return
    
    # TÃ¼m verileri topla
    all_data = {
        'NIEDERSACHSEN': {},
        'BREMEN': {}
    }
    
    total_cities = len(cities['NIEDERSACHSEN']) + len(cities['BREMEN'])
    processed = 0
    successful = 0
    failed = 0
    
    # Niedersachsen ÅŸehirleri
    print(f"\n{'='*70}")
    print("NIEDERSACHSEN EYALETÄ°")
    print(f"{'='*70}")
    
    for city_name in cities['NIEDERSACHSEN']:
        processed += 1
        print(f"\n[{processed}/{total_cities}] Ä°ÅŸleniyor...")
        
        result = get_city_ramadan_data(city_name, 'Niedersachsen')
        
        if result and result.get('imsakiye'):
            all_data['NIEDERSACHSEN'][city_name] = {
                'imsakiye': result['imsakiye'],
                'bayram': result.get('bayram')
            }
            successful += 1
        else:
            failed += 1
            print(f"[ERROR] {city_name} iÃ§in veri alÄ±namadÄ±")
        
        # Rate limiting
        time.sleep(2)
    
    # Bremen ÅŸehirleri
    print(f"\n{'='*70}")
    print("BREMEN EYALETÄ°")
    print(f"{'='*70}")
    
    for city_name in cities['BREMEN']:
        processed += 1
        print(f"\n[{processed}/{total_cities}] Ä°ÅŸleniyor...")
        
        result = get_city_ramadan_data(city_name, 'Bremen')
        
        if result and result.get('imsakiye'):
            all_data['BREMEN'][city_name] = {
                'imsakiye': result['imsakiye'],
                'bayram': result.get('bayram')
            }
            successful += 1
        else:
            failed += 1
            print(f"[ERROR] {city_name} iÃ§in veri alÄ±namadÄ±")
        
        # Rate limiting
        time.sleep(2)
    
    # SonuÃ§larÄ± kaydet
    output_file = 'ramadan-namazvakitleri.json'
    print(f"\n{'='*70}")
    print("SONUÃ‡LAR")
    print(f"{'='*70}")
    print(f"Toplam iÅŸlenen: {processed}")
    print(f"BaÅŸarÄ±lÄ±: {successful}")
    print(f"BaÅŸarÄ±sÄ±z: {failed}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Veriler kaydedildi: {output_file}")
        
        # Ä°statistikler
        niedersachsen_count = sum(len(data.get('imsakiye', [])) for data in all_data['NIEDERSACHSEN'].values())
        bremen_count = sum(len(data.get('imsakiye', [])) for data in all_data['BREMEN'].values())
        
        print(f"\nÄ°statistikler:")
        print(f"  Niedersachsen: {len(all_data['NIEDERSACHSEN'])} ÅŸehir, {niedersachsen_count} gÃ¼n veri")
        print(f"  Bremen: {len(all_data['BREMEN'])} ÅŸehir, {bremen_count} gÃ¼n veri")
        
    except Exception as e:
        print(f"\n[ERROR] Dosya kaydedilemedi: {e}")

if __name__ == '__main__':
    main()

