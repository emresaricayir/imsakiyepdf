"""
Diyanet sitesinden Almanya'daki TÜM şehirleri çıkarır
Her eyalet için ayrı ayrı şehir listesini alır
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx'
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

def get_cities_for_state(base_url, form_data, state_value, state_name):
    """
    Belirli bir eyalet için şehir listesini çıkarır
    """
    try:
        # Eyaleti seç
        form_data['ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler'] = state_value
        form_data['__EVENTTARGET'] = 'ctl00$ctl00$cphMainSlider$solIcerik$ddlSehirler'
        form_data['__EVENTARGUMENT'] = ''
        
        # POST isteği gönder
        response = session.post(base_url, data=form_data, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # İlçe/Şehir select'ini bul (eyalet seçildikten sonra şehirler burada olabilir)
        city_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlIlceler'})
        if not city_select:
            city_select = soup.find('select', {'name': re.compile(r'ddlIlceler', re.I)})
        
        cities = []
        
        if city_select:
            options = city_select.find_all('option')
            for option in options:
                city_name = option.get_text(strip=True)
                if city_name and city_name not in ['-- İlçe Seçin --', '-- Şehir Seçin --', '']:
                    cities.append(city_name)
        
        # Eğer ilçe select'inde şehir yoksa, şehir select'ini tekrar kontrol et
        if not cities:
            city_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlSehirler'})
            if city_select:
                options = city_select.find_all('option')
                for option in options:
                    city_name = option.get_text(strip=True)
                    if city_name and city_name not in ['-- Şehir Seçin --', '']:
                        # Eyalet isimlerini atla
                        if city_name.upper() not in ['BADEN WURTTEMBERG', 'BAYERN', 'BERLIN', 
                                                      'BRANDENBURG', 'BREMEN', 'HAMBURG', 'HESSEN',
                                                      'MECKLENBURG-VORPOMMERN', 'NIEDERSACHSEN',
                                                      'NORDRHEIN-WESTFALEN', 'RHEINLAND-PFALZ',
                                                      'SAARLAND', 'SACHSEN', 'SACHSEN-ANHALT',
                                                      'SCHLESWIG-HOLSTEIN', 'THÜRINGEN']:
                            cities.append(city_name)
        
        return cities, get_form_data(soup)  # Yeni form verilerini döndür
    
    except Exception as e:
        print(f"      ✗ Hata: {str(e)[:50]}")
        return [], form_data

def get_all_germany_cities():
    """
    Diyanet sitesinden Almanya'daki tüm şehirleri çıkarır
    """
    base_url = "https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx"
    
    print("=" * 70)
    print("Diyanet Sitesinden Almanya - TÜM Şehirler Çıkarılıyor")
    print("=" * 70)
    
    # Eyalet mapping (Diyanet sitesindeki isimler)
    state_mapping = {
        "BADEN WURTTEMBERG": {"code": "BADEN-WÜRTTEMBERG", "name": "Baden-Württemberg"},
        "BAYERN": {"code": "BAYERN", "name": "Bayern"},
        "BERLIN": {"code": "BERLIN", "name": "Berlin"},
        "BRANDENBURG": {"code": "BRANDENBURG", "name": "Brandenburg"},
        "BREMEN": {"code": "BREMEN", "name": "Bremen"},
        "HAMBURG": {"code": "HAMBURG", "name": "Hamburg"},
        "HESSEN": {"code": "HESSEN", "name": "Hessen"},
        "MECKLENBURG-VORPOMMERN": {"code": "MECKLENBURG-VORPOMMERN", "name": "Mecklenburg-Vorpommern"},
        "NIEDERSACHSEN": {"code": "NIEDERSACHSEN", "name": "Niedersachsen"},
        "NORDRHEIN-WESTFALEN": {"code": "NORDRHEIN-WESTFALEN", "name": "Nordrhein-Westfalen"},
        "RHEINLAND-PFALZ": {"code": "RHEINLAND-PFALZ", "name": "Rheinland-Pfalz"},
        "SAARLAND": {"code": "SAARLAND", "name": "Saarland"},
        "SACHSEN": {"code": "SACHSEN", "name": "Sachsen"},
        "SACHSEN ANHALT": {"code": "SACHSEN-ANHALT", "name": "Sachsen-Anhalt"},
        "SACHSEN-ANHALT": {"code": "SACHSEN-ANHALT", "name": "Sachsen-Anhalt"},
        "SCHLESWIG HOLSTEIN": {"code": "SCHLESWIG-HOLSTEIN", "name": "Schleswig-Holstein"},
        "SCHLESWIG-HOLSTEIN": {"code": "SCHLESWIG-HOLSTEIN", "name": "Schleswig-Holstein"},
        "THURINGEN": {"code": "THÜRINGEN", "name": "Thüringen"},
        "THÜRINGEN": {"code": "THÜRINGEN", "name": "Thüringen"}
    }
    
    try:
        # 1. Ana sayfayı çek
        print("\n1. Ana sayfa yükleniyor...")
        response = session.get(base_url, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        form_data = get_form_data(soup)
        
        # 2. Almanya'yı seç
        country_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlUlkeler'})
        germany_value = None
        
        if country_select:
            options = country_select.find_all('option')
            for option in options:
                if 'ALMANYA' in option.get_text(strip=True).upper():
                    germany_value = option.get('value', '')
                    break
        
        if not germany_value:
            print("✗ ALMANYA bulunamadı!")
            return {}
        
        print(f"   ✓ ALMANYA bulundu (value: {germany_value})")
        
        # Almanya'yı seç
        form_data['ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler'] = germany_value
        form_data['__EVENTTARGET'] = 'ctl00$ctl00$cphMainSlider$solIcerik$ddlUlkeler'
        
        response = session.post(base_url, data=form_data, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        form_data = get_form_data(soup)
        
        # 3. Eyaletleri al
        print("\n2. Eyaletler alınıyor...")
        city_select = soup.find('select', {'id': 'cphMainSlider_solIcerik_ddlSehirler'})
        
        if not city_select:
            print("✗ Şehir select'i bulunamadı!")
            return {}
        
        state_options = city_select.find_all('option')
        states_data = {}
        
        print(f"   ✓ {len(state_options)} eyalet bulundu\n")
        
        # 4. Her eyalet için şehirleri çek
        result = {}
        
        for idx, state_option in enumerate(state_options, 1):
            state_name_diyanet = state_option.get_text(strip=True)
            state_value = state_option.get('value', '')
            
            if not state_name_diyanet or state_name_diyanet in ['-- Şehir Seçin --', '']:
                continue
            
            # Eyalet mapping'ini bul
            state_info = state_mapping.get(state_name_diyanet.upper())
            if not state_info:
                print(f"   [{idx}] ⚠ Bilinmeyen eyalet: {state_name_diyanet}")
                continue
            
            state_code = state_info['code']
            state_display_name = state_info['name']
            
            print(f"   [{idx}/16] {state_display_name}...", end=" ", flush=True)
            
            # Bu eyalet için şehirleri çek
            cities, form_data = get_cities_for_state(base_url, form_data, state_value, state_display_name)
            
            if cities:
                result[state_code] = {
                    "name": state_display_name,
                    "cities": sorted(cities)  # Alfabetik sırala
                }
                print(f"✓ {len(cities)} şehir")
            else:
                print(f"⚠ Şehir bulunamadı")
                # En azından boş liste ekle
                result[state_code] = {
                    "name": state_display_name,
                    "cities": []
                }
            
            # Rate limiting
            time.sleep(0.5)
        
        return result
    
    except Exception as e:
        print(f"\n✗ Hata: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    """
    Ana fonksiyon
    """
    # Tüm şehirleri çıkar
    cities_list = get_all_germany_cities()
    
    if not cities_list:
        print("\n✗ Şehir listesi alınamadı!")
        return
    
    # Ülke yapısını oluştur
    countries_structure = {
        'ALMANYA': {
            'name': 'ALMANYA',
            'states': cities_list
        }
    }
    
    # Kaydet
    print("\n" + "=" * 70)
    print("Veriler kaydediliyor...")
    with open('countries.json', 'w', encoding='utf-8') as f:
        json.dump(countries_structure, f, ensure_ascii=False, indent=2)
    print("✓ countries.json kaydedildi")
    
    # İstatistikler
    total_states = len(cities_list)
    total_cities = sum(len(state_info['cities']) for state_info in cities_list.values())
    
    print("\n" + "=" * 70)
    print("ÖZET")
    print("=" * 70)
    print(f"  Toplam eyalet: {total_states}")
    print(f"  Toplam şehir: {total_cities}")
    
    print("\nEyaletler ve şehir sayıları:")
    for state_code, state_info in sorted(cities_list.items()):
        city_count = len(state_info['cities'])
        print(f"  {state_info['name']}: {city_count} şehir")
        if city_count == 0:
            print(f"    ⚠ Bu eyalet için şehir bulunamadı!")
    
    print("\n" + "=" * 70)
    print("✓ Tamamlandı!")
    print("=" * 70)

if __name__ == "__main__":
    main()

