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

def get_city_ramadan_data(city_name, state_name):
    """
    Belirli bir şehir için Ramazan ayı namaz vakitlerini çeker
    Selenium kullanarak JavaScript ile dinamik yüklenen içeriği çeker
    """
    print(f"\n{'='*70}")
    print(f"Şehir: {city_name}, Eyalet: {state_name}")
    print(f"{'='*70}")
    
    try:
        driver = init_driver()
        
        # Ana sayfayı yükle
        print("1. Ana sayfa yükleniyor...")
        driver.get(BASE_URL)
        time.sleep(2)
        
        # Ülke seçimi (ALMANYA = 13)
        print("2. Ülke seçimi yapılıyor (ALMANYA)...")
        country_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "country"))
        ))
        country_select.select_by_value("13")
        time.sleep(2)  # Wait for JavaScript to load states
        
        # Eyalet seçimi
        print(f"3. Eyalet seçimi yapılıyor ({state_name})...")
        state_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "state"))
        ))
        
        # Find state by name
        state_value = None
        for option in state_select.options:
            if state_name.upper() in option.text.upper():
                state_value = option.get_attribute('value')
                print(f"[OK] Eyalet bulundu: {option.text} (value: {state_value})")
                state_select.select_by_value(state_value)
                break
        
        if not state_value:
            print(f"[ERROR] Eyalet bulunamadı: {state_name}")
            return None
        
        time.sleep(2)  # Wait for JavaScript to load cities
        
        # Şehir seçimi
        print(f"4. Şehir seçimi yapılıyor ({city_name})...")
        city_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "stateRegion"))
        ))
        
        # Find city by name (normalize for matching)
        city_value = None
        city_normalized = city_name.upper().strip()
        
        # Try exact match first
        for option in city_select.options:
            option_text = option.text.upper().strip()
            option_value = option.get_attribute('value')
            
            # Skip empty or default options
            if not option_value or option_value == '-1' or not option_text:
                continue
            
            # Exact match
            if city_normalized == option_text:
                city_value = option_value
                print(f"[OK] Şehir bulundu (exact): {option.text} (value: {city_value})")
                city_select.select_by_value(city_value)
                break
        
        # If not found, try partial match
        if not city_value:
            for option in city_select.options:
                option_text = option.text.upper().strip()
                option_value = option.get_attribute('value')
                
                # Skip empty or default options
                if not option_value or option_value == '-1' or not option_text:
                    continue
                
                # Partial match
                if city_normalized in option_text or option_text in city_normalized:
                    city_value = option_value
                    print(f"[OK] Şehir bulundu (partial): {option.text} (value: {city_value})")
                    city_select.select_by_value(city_value)
                    break
        
        if not city_value:
            print(f"[ERROR] Şehir bulunamadı: {city_name}")
            return None
        
        time.sleep(3)  # Wait for page to load with prayer times
        
        # Go to page 2 for yearly table
        print("5. Sayfa 2'ye geçiliyor (Yıllık tablo)...")
        page2_clicked = False
        
        # Wait a bit more for pagination to load
        time.sleep(2)
        
        # Scroll to bottom to see pagination
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Look for paginate_button with text "2" - wait for it to be visible
        try:
            # Wait for pagination to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.paginate_button, .paginate_button"))
            )
            
            # Find all paginate buttons
            paginate_buttons = driver.find_elements(By.CSS_SELECTOR, "a.paginate_button, .paginate_button")
            print(f"   Bulunan pagination butonları: {len(paginate_buttons)}")
            
            for i, btn in enumerate(paginate_buttons):
                try:
                    # Try multiple ways to get text
                    text = btn.text.strip()
                    inner_html = btn.get_attribute('innerHTML') or ''
                    text_content = driver.execute_script("return arguments[0].textContent;", btn) or ''
                    data_page = btn.get_attribute('data-page') or ''
                    
                    # Check if it's page 2
                    is_page2 = (text == '2' or 
                               inner_html.strip() == '2' or 
                               text_content.strip() == '2' or
                               data_page == '2' or
                               '2' in inner_html and len(inner_html.strip()) <= 5)
                    
                    if is_page2:
                        print(f"   [FOUND] Sayfa 2 butonu (index {i}): text='{text}' innerHTML='{inner_html}' data-page='{data_page}'")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        # Try normal click first
                        try:
                            btn.click()
                        except:
                            # Fallback to JavaScript click
                            driver.execute_script("arguments[0].click();", btn)
                        time.sleep(3)
                        print("[OK] Sayfa 2'ye geçildi")
                        page2_clicked = True
                        break
                    else:
                        print(f"   Buton {i}: text='{text}' innerHTML='{inner_html[:20]}' data-page='{data_page}'")
                except Exception as e:
                    print(f"   Buton {i} hatası: {e}")
                    continue
        except Exception as e:
            print(f"[WARNING] Pagination bulunamadı: {e}")
        
        if not page2_clicked:
            print("[WARNING] Sayfa 2'ye geçilemedi, sayfa 1'deki tablolar kontrol edilecek")
        
        # Get page source
        html = driver.page_source
        
        # Verify city is in page
        if city_name.upper() not in html.upper():
            print(f"[WARNING] Şehir adı sayfada bulunamadı, devam ediliyor...")
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # "Yıllık Namaz Vakitleri" tablosunu bul (Tablo 3 genellikle yıllık tablo)
        print("6. Namaz vakitleri tablosu aranıyor...")
        imsakiye_data = []
        bayram_namazi = None
        
        # Tüm tabloları kontrol et
        tables = soup.find_all('table')
        print(f"   Bulunan tablo sayısı: {len(tables)}")
        
        # Tablo 3 genellikle yıllık tablo (en uzun tablo)
        yearly_table = None
        if len(tables) >= 3:
            # Tablo 3'ü kontrol et (yıllık tablo)
            yearly_table = tables[2]
            print(f"   Tablo 3 (Yıllık) kontrol ediliyor...")
        else:
            # En uzun tabloyu bul
            max_rows = 0
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > max_rows:
                    max_rows = len(rows)
                    yearly_table = table
        
        # Collect data from all pages (page 2, 3, 4, etc.) until we have all 29 days
        max_pages = 5  # Maximum pages to check
        for page_num in range(2, max_pages + 1):
            if len(imsakiye_data) >= 29:
                break
            
            # Get current page HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find table 3 (yearly table)
            tables = soup.find_all('table')
            yearly_table = tables[2] if len(tables) >= 3 else None
            
            if yearly_table:
                rows = yearly_table.find_all('tr')
                print(f"   Sayfa {page_num-1} - Tablo satır sayısı: {len(rows)}")
                
                for row_idx, row in enumerate(rows):
                    if row_idx == 0:
                        continue  # Başlık satırını atla
                    
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 7:
                        try:
                            # Hücre sırası: Miladi Tarih, Hicri Tarih, İmsak, Güneş, Öğle, İkindi, Akşam, Yatsı
                            miladi = cells[0].get_text(strip=True)
                            hicri = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            imsak = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                            gunes = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                            ogle = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                            ikindi = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                            aksam = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                            yatsi = cells[7].get_text(strip=True) if len(cells) > 7 else ''
                            
                            # Boş satırları ve başlık satırlarını atla
                            if (hicri and miladi and imsak and 
                                'HICRI' not in hicri.upper() and
                                'MILADI' not in miladi.upper() and
                                'IMSAK' not in imsak.upper() and
                                ':' in imsak):
                                
                                # Sadece Ramazan günlerini al (1-29 Ramazan 1447)
                                ramazan_match = re.search(r'(\d+)\s*RAMAZAN\s*1447', hicri.upper())
                                if ramazan_match:
                                    ramazan_day = int(ramazan_match.group(1))
                                    if 1 <= ramazan_day <= 29:
                                        # Check if already added
                                        exists = any(item['hicri'] == hicri for item in imsakiye_data)
                                        if not exists:
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
                
                print(f"   Sayfa {page_num-1}'den toplam {len(imsakiye_data)} Ramazan günü bulundu")
            
            # Go to next page if we don't have all 29 days
            if len(imsakiye_data) < 29 and page_num < max_pages:
                try:
                    # Find next page button
                    paginate_buttons = driver.find_elements(By.CSS_SELECTOR, "a.paginate_button, .paginate_button")
                    next_page_found = False
                    for btn in paginate_buttons:
                        inner_html = btn.get_attribute('innerHTML') or ''
                        if inner_html.strip() == str(page_num):
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(3)
                            print(f"   Sayfa {page_num}'ye geçildi")
                            next_page_found = True
                            break
                    if not next_page_found:
                        break
                except:
                    break
        
        if len(imsakiye_data) >= 25:
            print(f"[OK] Toplam {len(imsakiye_data)} Ramazan günü veri çekildi")
        else:
            print(f"[WARNING] Sadece {len(imsakiye_data)} Ramazan günü bulundu (29 gün gerekli)")
        
        # Eğer tablo bulunamadıysa, tüm tabloları tekrar kontrol et (farklı format)
        if len(imsakiye_data) < 25:
            print("   Yeterli veri bulunamadı, tüm tablolar tekrar kontrol ediliyor...")
            for table in tables:
                rows = table.find_all('tr')
                for row_idx, row in enumerate(rows[1:], 1):  # İlk satır başlık
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 7:
                        try:
                            # Farklı sıralama olabilir, tüm hücreleri kontrol et
                            all_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            # Tarih formatı içeren hücreleri bul
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
                                        # Zaten eklenmiş mi kontrol et
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
        
        # Bayram namazı vaktini bul
        print("7. Bayram namazı vakti aranıyor...")
        page_text = soup.get_text()
        bayram_pattern = re.compile(r'BAYRAM\s+NAMAZI\s*:?\s*(\d{1,2}:\d{2})', re.IGNORECASE)
        match = bayram_pattern.search(page_text)
        if match:
            bayram_namazi = match.group(1)
            print(f"[OK] Bayram namazı vakti bulundu: {bayram_namazi}")
        else:
            # Alternatif: Bold veya strong etiketlerinde ara
            bold_texts = soup.find_all(['b', 'strong', 'span', 'div'])
            for bold in bold_texts:
                text = bold.get_text()
                match = bayram_pattern.search(text)
                if match:
                    bayram_namazi = match.group(1)
                    print(f"[OK] Bayram namazı vakti bulundu (alternatif): {bayram_namazi}")
                    break
        
        # Sonuçları kontrol et
        if len(imsakiye_data) >= 25:
            print(f"\n[OK] Başarılı! {len(imsakiye_data)} gün veri çekildi")
            if bayram_namazi:
                print(f"[OK] Bayram namazı vakti: {bayram_namazi}")
            return {
                'imsakiye': imsakiye_data,
                'bayram': bayram_namazi,
                'city': city_name,
                'state': state_name
            }
        else:
            print(f"\n[ERROR] Yetersiz veri: Sadece {len(imsakiye_data)} gün çekildi (en az 25 gün gerekli)")
            return None
            
    except Exception as e:
        print(f"\n[ERROR] Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_all_cities_for_states():
    """
    Niedersachsen ve Bremen eyaletlerindeki tüm şehirleri al
    imsakiye-data.json dosyasından şehir listesini çıkarır
    """
    cities = {
        'NIEDERSACHSEN': [],
        'BREMEN': []
    }
    
    try:
        # imsakiye-data.json'dan şehir listesini çıkar
        with open('imsakiye-data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # JSON yapısı: { "ALMANYA": { "NIEDERSACHSEN": { "CITY": [...] }, "BREMEN": { "CITY": [...] } } }
            if 'ALMANYA' in data:
                germany_data = data['ALMANYA']
                
                # Niedersachsen şehirleri
                if 'NIEDERSACHSEN' in germany_data:
                    cities['NIEDERSACHSEN'] = list(germany_data['NIEDERSACHSEN'].keys())
                
                # Bremen şehirleri
                if 'BREMEN' in germany_data:
                    cities['BREMEN'] = list(germany_data['BREMEN'].keys())
        
        print(f"\nŞehir listesi yüklendi:")
        print(f"  Niedersachsen: {len(cities['NIEDERSACHSEN'])} şehir")
        print(f"  Bremen: {len(cities['BREMEN'])} şehir")
        
        if len(cities['NIEDERSACHSEN']) == 0 and len(cities['BREMEN']) == 0:
            print("⚠ Hiç şehir bulunamadı! JSON yapısını kontrol edin.")
            return None
        
    except FileNotFoundError:
        print("[ERROR] imsakiye-data.json bulunamadı")
        print("  Lütfen önce şehir listesini oluşturun veya manuel olarak ekleyin")
        return None
    except Exception as e:
        print(f"[ERROR] Şehir listesi yüklenirken hata: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return cities

def main():
    """
    Ana fonksiyon: Tüm şehirler için Ramazan verilerini indir
    """
    print("="*70)
    print("Diyanet Namaz Vakitleri - Ramazan Ayı Verilerini İndirme")
    print("https://namazvakitleri.diyanet.gov.tr/")
    print("Selenium ile JavaScript dinamik içerik çekiliyor")
    print("="*70)
    
    # Şehir listesini al
    cities = get_all_cities_for_states()
    if not cities:
        print("\n[ERROR] Şehir listesi alınamadı, çıkılıyor...")
        return
    
    # Tüm verileri topla
    all_data = {
        'NIEDERSACHSEN': {},
        'BREMEN': {}
    }
    
    total_cities = len(cities['NIEDERSACHSEN']) + len(cities['BREMEN'])
    processed = 0
    successful = 0
    failed = 0
    
    try:
        # Niedersachsen şehirleri
        print(f"\n{'='*70}")
        print("NIEDERSACHSEN EYALETİ")
        print(f"{'='*70}")
        
        for city_name in cities['NIEDERSACHSEN']:
            processed += 1
            print(f"\n[{processed}/{total_cities}] İşleniyor...")
            
            result = get_city_ramadan_data(city_name, 'Niedersachsen')
            
            if result and result.get('imsakiye'):
                all_data['NIEDERSACHSEN'][city_name] = {
                    'imsakiye': result['imsakiye'],
                    'bayram': result.get('bayram')
                }
                successful += 1
            else:
                failed += 1
                print(f"[ERROR] {city_name} için veri alınamadı")
            
            # Rate limiting - her şehir arasında bekle
            time.sleep(1)
        
        # Bremen şehirleri
        print(f"\n{'='*70}")
        print("BREMEN EYALETİ")
        print(f"{'='*70}")
        
        for city_name in cities['BREMEN']:
            processed += 1
            print(f"\n[{processed}/{total_cities}] İşleniyor...")
            
            result = get_city_ramadan_data(city_name, 'Bremen')
            
            if result and result.get('imsakiye'):
                all_data['BREMEN'][city_name] = {
                    'imsakiye': result['imsakiye'],
                    'bayram': result.get('bayram')
                }
                successful += 1
            else:
                failed += 1
                print(f"[ERROR] {city_name} için veri alınamadı")
            
            # Rate limiting
            time.sleep(1)
        
    finally:
        # Driver'ı kapat
        close_driver()
    
    # Sonuçları kaydet
    output_file = 'ramadan-namazvakitleri.json'
    print(f"\n{'='*70}")
    print("SONUÇLAR")
    print(f"{'='*70}")
    print(f"Toplam işlenen: {processed}")
    print(f"Başarılı: {successful}")
    print(f"Başarısız: {failed}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Veriler kaydedildi: {output_file}")
        
        # İstatistikler
        niedersachsen_count = sum(len(data.get('imsakiye', [])) for data in all_data['NIEDERSACHSEN'].values())
        bremen_count = sum(len(data.get('imsakiye', [])) for data in all_data['BREMEN'].values())
        
        print(f"\nİstatistikler:")
        print(f"  Niedersachsen: {len(all_data['NIEDERSACHSEN'])} şehir, {niedersachsen_count} gün veri")
        print(f"  Bremen: {len(all_data['BREMEN'])} şehir, {bremen_count} gün veri")
        
    except Exception as e:
        print(f"\n[ERROR] Dosya kaydedilemedi: {e}")

if __name__ == '__main__':
    main()
