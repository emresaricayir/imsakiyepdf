"""
Diyanet İşleri Başkanlığı İmsakiye Verilerini İndirme Scripti
Tüm şehirler için orijinal verileri çeker
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime, timedelta

# Session oluştur (cookie'ler için)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
})

def get_form_data(soup):
    """Form verilerini çıkarır"""
    data = {}
    
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    if viewstate:
        data['__VIEWSTATE'] = viewstate.get('value', '')
    
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
    if eventvalidation:
        data['__EVENTVALIDATION'] = eventvalidation.get('value', '')
    
    viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    if viewstategenerator:
        data['__VIEWSTATEGENERATOR'] = viewstategenerator.get('value', '')
    
    data['__EVENTTARGET'] = ''
    data['__EVENTARGUMENT'] = ''
    data['__LASTFOCUS'] = ''
    
    return data

def get_city_imsakiye_from_diyanet(city_name, country_code="ALMANYA", state_code=None):
    """
    Diyanet sitesinden belirli bir şehir için imsakiye verilerini çeker
    Bayram namazı vaktini de çeker
    Form POST istekleri ile şehir seçimi yapar
    """
    base_url = "https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx"
    
    try:
        # Önce ana sayfayı çek (viewstate ve diğer form verileri için)
        response = session.get(base_url, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        form_data = get_form_data(soup)
        
        # Ülke seçimi (ALMANYA)
        country_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlUlkeler'})
        if not country_select:
            country_select = soup.find('select', {'name': re.compile(r'ddlUlkeler', re.I)})
        
        if country_select:
            options = country_select.find_all('option')
            country_value = None
            for option in options:
                if country_code.upper() in option.get_text(strip=True).upper() or 'ALMANYA' in option.get_text(strip=True).upper():
                    country_value = option.get('value', '')
                    break
            
            if country_value:
                form_data['ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler'] = country_value
                form_data['__EVENTTARGET'] = 'ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler'
                form_data['__EVENTARGUMENT'] = ''
                response = session.post(base_url, data=form_data, timeout=30)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                form_data = get_form_data(soup)
                time.sleep(0.5)
        
        # Eyalet seçimi
        if state_code:
            state_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlSehirler'})
            if not state_select:
                state_select = soup.find('select', {'name': re.compile(r'ddlSehirler', re.I)})
            
            if state_select:
                options = state_select.find_all('option')
                state_value = None
                
                # Eyalet isimlerini normalize et (tire -> boşluk, ü -> u, ö -> o, ş -> s, ı -> i)
                def normalize_state_name(name):
                    name = name.upper()
                    name = name.replace('-', ' ')
                    name = name.replace('Ü', 'U').replace('Ö', 'O').replace('Ş', 'S').replace('İ', 'I')
                    name = name.replace('Ç', 'C').replace('Ğ', 'G')
                    return name.strip()
                
                normalized_state_code = normalize_state_name(state_code)
                
                for option in options:
                    option_text = option.get_text(strip=True)
                    normalized_option = normalize_state_name(option_text)
                    
                    # Normalize edilmiş isimleri karşılaştır
                    if normalized_state_code == normalized_option or normalized_state_code in normalized_option or normalized_option in normalized_state_code:
                        state_value = option.get('value', '')
                        print(f"      [DEBUG] Eyalet eşleşti: '{state_code}' -> '{option_text}' (value: {state_value})")
                        break
                
                if state_value:
                    form_data['ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler'] = state_value
                    form_data['__EVENTTARGET'] = 'ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler'
                    form_data['__EVENTARGUMENT'] = ''
                    response = session.post(base_url, data=form_data, timeout=30)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    form_data = get_form_data(soup)
                    time.sleep(0.5)
        
        # Şehir seçimi
        city_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlIlceler'})
        if not city_select:
            city_select = soup.find('select', {'name': re.compile(r'ddlIlceler', re.I)})
        
        if city_select:
            options = city_select.find_all('option')
            city_value = None
            
            # Şehir isimlerini normalize et
            def normalize_city_name(name):
                name = name.upper()
                name = name.replace('Ü', 'U').replace('Ö', 'O').replace('Ş', 'S').replace('İ', 'I')
                name = name.replace('Ç', 'C').replace('Ğ', 'G')
                return name.strip()
            
            normalized_city_name = normalize_city_name(city_name)
            
            for option in options:
                option_text = option.get_text(strip=True)
                normalized_option = normalize_city_name(option_text)
                
                # Normalize edilmiş isimleri karşılaştır
                if normalized_city_name == normalized_option or normalized_city_name in normalized_option or normalized_option in normalized_city_name:
                    city_value = option.get('value', '')
                    break
            
            if city_value:
                # Form field ismini tam olarak kullan
                form_data['ctl00$ctl00$cphMainSlider$solIcerik$ddlIlceler'] = city_value
                form_data['__EVENTTARGET'] = 'ctl00$ctl00$cphMainSlider$solIcerik$ddlIlceler'
                form_data['__EVENTARGUMENT'] = ''
                response = session.post(base_url, data=form_data, timeout=30)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                time.sleep(0.5)  # Biraz daha bekle
        
        # İmsakiye tablosunu bul
        tables = soup.find_all('table')
        imsakiye_data = []
        bayram_namazi = None
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # İlk satır başlık
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 7:
                    try:
                        hicri = cells[0].get_text(strip=True)
                        miladi = cells[1].get_text(strip=True)
                        imsak = cells[2].get_text(strip=True)
                        gunes = cells[3].get_text(strip=True)
                        ogle = cells[4].get_text(strip=True)
                        ikindi = cells[5].get_text(strip=True)
                        aksam = cells[6].get_text(strip=True)
                        yatsi = cells[7].get_text(strip=True) if len(cells) > 7 else ""
                        
                        # Boş satırları ve başlık satırlarını atla
                        if (hicri and miladi and imsak and imsak != '' and 
                            hicri.lower() not in ['hicri tarih', 'hicri'] and
                            miladi.lower() not in ['miladi tarih', 'miladi'] and
                            imsak.lower() not in ['imsak', '']):
                            # Saat formatını kontrol et (HH:MM formatında olmalı)
                            if ':' in imsak and len(imsak.split(':')) == 2:
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
        
        # Bayram namazı vaktini bul
        page_text = soup.get_text()
        bayram_pattern = re.compile(r'Bayram\s+Namazı\s*:?\s*(\d{1,2}:\d{2})', re.IGNORECASE)
        match = bayram_pattern.search(page_text)
        if match:
            bayram_namazi = match.group(1)
        else:
            # Alternatif: Bold veya strong etiketlerinde ara
            bold_texts = soup.find_all(['b', 'strong'])
            for bold in bold_texts:
                text = bold.get_text()
                if 'Bayram Namazı' in text:
                    match = bayram_pattern.search(text)
                    if match:
                        bayram_namazi = match.group(1)
                        break
        
        # Eğer veri bulunduysa döndür
        if imsakiye_data and len(imsakiye_data) >= 20:  # En az 20 gün veri varsa gerçek veri sayılır
            return imsakiye_data, bayram_namazi
        
        return None, None
    
    except Exception as e:
        print(f"      [HATA] Hata: {str(e)[:50]}")
        return None, None

def fetch_city_imsakiye_via_api(city_name, state_name):
    """
    Diyanet API'sini kullanarak şehir için imsakiye verilerini çeker
    Alternatif yöntem: Namaz vakitleri API'si
    """
    try:
        # Diyanet'in namaz vakitleri API'si
        # Not: Bu API endpoint'i gerçekte mevcut olmayabilir, test edilmeli
        api_url = "https://vakithesaplama.diyanet.gov.tr/api/vakitler"
        
        # Şehir koordinatları veya ID'si gerekebilir
        # Şimdilik bu yöntemi kullanmıyoruz
        
        return None
    except:
        return None

def calculate_imsakiye_for_city(city_name, state_name, base_lat=None, base_lon=None):
    """
    Şehir için astronomik hesaplamalarla imsakiye verisi oluşturur
    Gerçek veriler için Diyanet API'si tercih edilir
    """
    from datetime import datetime, timedelta
    
    data = []
    base_date = datetime(2026, 2, 19)  # 19 Şubat 2026 - Ramazan başlangıcı
    
    # Almanya şehirleri için yaklaşık koordinatlar ve zaman farkları
    city_coords = {
        'Berlin': (52.52, 13.405, 0),
        'München': (48.1351, 11.5820, 0),
        'Hamburg': (53.5511, 9.9937, 0),
        'Köln': (50.9375, 6.9603, 0),
        'Frankfurt': (50.1109, 8.6821, 0),
        'Stuttgart': (48.7758, 9.1829, 0),
        'Düsseldorf': (51.2277, 6.7735, 0),
        'Dortmund': (51.5136, 7.4653, 0),
        'Essen': (51.4556, 7.0116, 0),
        'Leipzig': (51.3397, 12.3731, 0),
        'Bremen': (53.0793, 8.8017, 0),
        'Dresden': (51.0504, 13.7373, 0),
        'Hannover': (52.3759, 9.7320, 0),
        'Nürnberg': (49.4521, 11.0767, 0),
        'Duisburg': (51.4344, 6.7623, 0),
        'Bochum': (51.4818, 7.2162, 0),
        'Wuppertal': (51.2562, 7.1508, 0),
        'Bielefeld': (52.0201, 8.5325, 0),
        'Bonn': (50.7374, 7.0982, 0),
        'Münster': (51.9625, 7.6256, 0),
    }
    
    # Şehir için koordinat al (varsayılan: Berlin)
    lat, lon, offset = city_coords.get(city_name, (52.52, 13.405, 0))
    
    # Basit zaman hesaplaması (gerçek hesaplama için astronomik kütüphane gerekir)
    # Şubat-Mart ayları için yaklaşık değerler
    for i in range(30):
        date = base_date + timedelta(days=i)
        
        # Gün geçtikçe imsak erkenleşir (kıştan bahara geçiş)
        # Şubat-Mart için yaklaşık değerler
        base_imsak_hour = 5
        base_imsak_min = 30
        
        # Günlük değişim (her gün ~1-2 dakika erkenleşir)
        imsak_minute_offset = int(i * 1.2)
        imsak_hour = base_imsak_hour
        imsak_min = base_imsak_min - imsak_minute_offset
        
        # Negatif olursa saati düşür
        while imsak_min < 0:
            imsak_min += 60
            imsak_hour -= 1
        
        # Güneş imsaktan yaklaşık 1.5 saat sonra
        gunes_hour = imsak_hour + 1
        gunes_min = imsak_min + 30
        if gunes_min >= 60:
            gunes_min -= 60
            gunes_hour += 1
        
        # Öğle genelde 12:30 civarı
        ogle_hour = 12
        ogle_min = 30 + (i % 3)
        
        # İkindi öğleden ~3-4 saat sonra
        ikindi_hour = 15
        ikindi_min = 45 + (i // 5)
        if ikindi_min >= 60:
            ikindi_min -= 60
            ikindi_hour += 1
        
        # Akşam güneş batışı, gün geçtikçe geçleşir
        aksam_hour = 18
        aksam_min = 15 + (i // 2)
        if aksam_min >= 60:
            aksam_min -= 60
            aksam_hour += 1
        
        # Yatsı akşamdan ~1.5 saat sonra
        yatsi_hour = aksam_hour + 1
        yatsi_min = aksam_min + 30
        if yatsi_min >= 60:
            yatsi_min -= 60
            yatsi_hour += 1
        
        # Tarih formatla
        days_tr = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        months_tr = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                     'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
        miladi_str = f"{date.day} {months_tr[date.month-1]} {date.year} {days_tr[date.weekday()]}"
        
        data.append({
            'hicri': f"{i+1} Ramazan 1447",
            'miladi': miladi_str,
            'imsak': f"{imsak_hour:02d}:{imsak_min:02d}",
            'gunes': f"{gunes_hour:02d}:{gunes_min:02d}",
            'ogle': f"{ogle_hour:02d}:{ogle_min:02d}",
            'ikindi': f"{ikindi_hour:02d}:{ikindi_min:02d}",
            'aksam': f"{aksam_hour:02d}:{aksam_min:02d}",
            'yatsi': f"{yatsi_hour:02d}:{yatsi_min:02d}"
        })
    
    return data

def fetch_imsakiye_data(country_code, state_code, city_name):
    """
    Şehir için imsakiye verilerini çeker
    SADECE gerçek verileri çeker - hesaplanmış veri kullanmaz
    Bayram namazı vaktini de döndürür
    """
    # Diyanet sitesinden gerçek veriyi çek
    real_data, bayram_namazi = get_city_imsakiye_from_diyanet(city_name, country_code, state_code)
    
    if real_data and len(real_data) >= 25:
        # Gerçek veri kontrolü - Ramazan içermeli
        first_row = real_data[0] if real_data else {}
        if 'Ramazan' in first_row.get('hicri', ''):
            return real_data, bayram_namazi
    
    # Gerçek veri bulunamadı - None döndür (hesaplanmış veri kullanma)
    return None, None

def get_countries_and_cities():
    """
    Ülke ve eyalet yapısını countries.json dosyasından yükler
    """
    try:
        with open('countries.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print("[INFO] countries.json bulunamadi, bos yapi donduruluyor")
        return {}
    except Exception as e:
        print(f"[HATA] countries.json yuklenirken hata: {e}")
        return {}

def main():
    """
    Ana fonksiyon - tüm şehirler için SADECE gerçek verileri çeker
    Hata olursa script durur
    """
    print("=" * 70)
    print("Diyanet İşleri Başkanlığı - İmsakiye Verileri İndirme")
    print("=" * 70)
    print("\nTüm şehirler için SADECE gerçek veriler çekilecek...")
    print("Hesaplanmış veri kullanılmayacak!")
    print("Hata olursa script durdurulacak!")
    print("Eyalet eyalet, adım adım işlem yapılacak.\n")
    
    # Ülke ve eyalet yapısını al
    countries_structure = get_countries_and_cities()
    
    # Mevcut verileri yükle (varsa)
    imsakiye_data = {}
    bayram_namazi_data = {}  # Bayram namazı vakitleri için ayrı yapı
    total_real_data = 0
    total_calculated_data = 0
    
    # Mevcut JSON dosyalarını yükle (devam etmek için)
    try:
        with open('imsakiye-data.json', 'r', encoding='utf-8') as f:
            imsakiye_data = json.load(f)
            print("[OK] Mevcut imsakiye verileri yuklendi")
            # Mevcut verilerden sayıları hesapla
            for country_code in imsakiye_data:
                for state_code in imsakiye_data[country_code]:
                    for city_name in imsakiye_data[country_code][state_code]:
                        city_data = imsakiye_data[country_code][state_code][city_name]
                        if isinstance(city_data, list) and len(city_data) >= 25:
                            first_row = city_data[0] if city_data else {}
                            if 'Ramazan' in first_row.get('hicri', ''):
                                total_real_data += 1
                            else:
                                total_calculated_data += 1
                        else:
                            total_calculated_data += 1
    except FileNotFoundError:
        print("[INFO] Mevcut imsakiye verisi bulunamadi, sifirdan baslaniyor")
    except Exception as e:
        print(f"[HATA] Mevcut veriler yuklenirken hata: {e}")
    
    try:
        with open('bayram-namazi.json', 'r', encoding='utf-8') as f:
            bayram_namazi_data = json.load(f)
            print("[OK] Mevcut bayram namazi verileri yuklendi")
    except FileNotFoundError:
        print("[INFO] Mevcut bayram namazi verisi bulunamadi")
    except Exception as e:
        print(f"[HATA] Bayram namazi verileri yuklenirken hata: {e}")
    
    for country_code, country_info in countries_structure.items():
        print(f"\n{'='*70}")
        print(f"ÜLKE: {country_info['name']}")
        print(f"{'='*70}\n")
        imsakiye_data[country_code] = {}
        
        states_list = list(country_info['states'].items())
        
        # Mevcut verileri kontrol et - hangi eyaletler çekilmiş?
        mevcut_eyaletler = set()
        if country_code in imsakiye_data:
            mevcut_eyaletler = set(imsakiye_data[country_code].keys())
        
        # Çekilmemiş eyaletleri bul
        cekilmemis_eyaletler = []
        for state_code, state_info in states_list:
            if state_code not in mevcut_eyaletler:
                cekilmemis_eyaletler.append((state_code, state_info))
        
        if cekilmemis_eyaletler:
            print(f"\n[NOT] {len(cekilmemis_eyaletler)} eyalet için veri çekilecek...")
            print(f"[NOT] Mevcut {len(mevcut_eyaletler)} eyalet atlanacak.\n")
            states_list = cekilmemis_eyaletler
        else:
            print(f"\n[NOT] Tüm eyaletler zaten çekilmiş! ({len(mevcut_eyaletler)} eyalet)\n")
            continue
        
        for state_idx, (state_code, state_info) in enumerate(states_list, 1):
            print(f"\n[{state_idx}/{len(states_list)}] EYALET: {state_info['name']}")
            print(f"{'-'*70}")
            
            # Eyalet verisi yoksa oluştur
            if country_code not in imsakiye_data:
                imsakiye_data[country_code] = {}
            if state_code not in imsakiye_data[country_code]:
                imsakiye_data[country_code][state_code] = {}
            
            # Eyalet bazlı sayaçları sıfırla
            state_real_data = 0
            state_calculated_data = 0
            
            cities_list = state_info['cities']
            
            for city_idx, city in enumerate(cities_list, 1):
                # Şehir ismini normalize et (büyük harf olabilir)
                city_normalized = city.title() if city.isupper() else city
                print(f"  [{city_idx}/{len(cities_list)}] {city_normalized}...", end=" ", flush=True)
                
                # Veri çek - SADECE gerçek veriler
                try:
                    city_data, bayram_namazi = fetch_imsakiye_data(country_code, state_code, city_normalized)
                    
                    if not city_data:
                        raise Exception(f"Gercek veri bulunamadi")
                    
                    if len(city_data) < 25:
                        raise Exception(f"Veri yetersiz (sadece {len(city_data)} gun)")
                    
                    # Gerçek veri kontrolü - Ramazan içermeli
                    first_row = city_data[0]
                    if 'Ramazan' not in first_row.get('hicri', ''):
                        raise Exception(f"Veri formati gecersiz - Ramazan bilgisi yok")
                    
                    # Gerçek veri bulundu - kaydet
                    imsakiye_data[country_code][state_code][city] = city_data
                    
                    # Bayram namazı vaktini ayrı bir dosyaya kaydet
                    if bayram_namazi:
                        if country_code not in bayram_namazi_data:
                            bayram_namazi_data[country_code] = {}
                        if state_code not in bayram_namazi_data[country_code]:
                            bayram_namazi_data[country_code][state_code] = {}
                        bayram_namazi_data[country_code][state_code][city] = bayram_namazi
                    
                    bayram_info = f" (Bayram: {bayram_namazi})" if bayram_namazi else ""
                    print(f"[OK] {len(city_data)} gun (ORIJINAL){bayram_info}")
                    total_real_data += 1
                    state_real_data += 1
                        
                except Exception as e:
                    print(f"[HATA] {city_normalized} icin gercek veri cekilemedi: {str(e)}")
                    print(f"[DURDUR] Script durduruluyor...")
                    # Hata durumunda scripti durdur
                    raise Exception(f"KRITIK HATA: {city_normalized} sehri icin gercek veri cekilemedi. Script durduruldu.")
                
                # Rate limiting - sunucuya yük bindirmemek için
                time.sleep(0.5)
            
            # Eyalet tamamlandı, ara kayıt yap
            print(f"\n  -> {state_info['name']} eyaleti tamamlandi!")
            print(f"  Toplam: {len(cities_list)} sehir, {state_real_data} orijinal veri, {state_calculated_data} hesaplanmis veri")
            
            # Her eyalet sonrası ara kayıt
            try:
                with open('imsakiye-data.json', 'w', encoding='utf-8') as f:
                    json.dump(imsakiye_data, f, ensure_ascii=False, indent=2)
                with open('bayram-namazi.json', 'w', encoding='utf-8') as f:
                    json.dump(bayram_namazi_data, f, ensure_ascii=False, indent=2)
                print(f"  [OK] Veriler kaydedildi")
            except Exception as e:
                print(f"  [HATA] Kaydetme hatasi: {e}")
            
            # Otomatik devam et (kullanıcı onayı bekleme)
            if state_idx < len(states_list):
                print(f"\n{'='*70}")
                print(f"EYALET TAMAMLANDI: {state_info['name']}")
                print(f"{'='*70}")
                print(f"\nSonraki eyalet: {states_list[state_idx][1]['name']}")
                print(f"\n5 saniye sonra otomatik devam edilecek... (Ctrl+C ile durdurabilirsiniz)")
                try:
                    time.sleep(5)
                    print(f"\n{states_list[state_idx][1]['name']} eyaleti baslatiliyor...\n")
                except KeyboardInterrupt:
                    print("\n\nCikis yapiliyor...")
                    break
    
    # Final kayıt
    print("\n" + "=" * 70)
    print("Veriler kaydediliyor...")
    print("=" * 70)
    
    with open('countries.json', 'w', encoding='utf-8') as f:
        json.dump(countries_structure, f, ensure_ascii=False, indent=2)
    print("[OK] countries.json kaydedildi")
    
    with open('imsakiye-data.json', 'w', encoding='utf-8') as f:
        json.dump(imsakiye_data, f, ensure_ascii=False, indent=2)
    print("[OK] imsakiye-data.json kaydedildi")
    
    with open('bayram-namazi.json', 'w', encoding='utf-8') as f:
        json.dump(bayram_namazi_data, f, ensure_ascii=False, indent=2)
    print("[OK] bayram-namazi.json kaydedildi")
    
    # İstatistikler
    total_states = sum(len(country['states']) for country in countries_structure.values())
    total_cities = sum(
        sum(len(state_info['cities']) for state_info in country['states'].values())
        for country in countries_structure.values()
    )
    
    print("\n" + "=" * 70)
    print("ÖZET")
    print("=" * 70)
    print(f"  Toplam ülke: {len(countries_structure)}")
    print(f"  Toplam eyalet: {total_states}")
    print(f"  Toplam şehir: {total_cities}")
    print(f"  Gercek veri: {total_real_data} sehir")
    print(f"  Hesaplanmis veri: {total_calculated_data} sehir (sadece mevcut verilerden)")
    print("\nNot: Tum yeni veriler Diyanet sitesinden gercek olarak cekilmistir.")
    print("Hesaplanmis veri kullanilmamistir.")
    print("=" * 70)

if __name__ == "__main__":
    main()
