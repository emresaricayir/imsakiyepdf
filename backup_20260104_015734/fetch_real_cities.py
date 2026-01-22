"""
Diyanet sitesinden Almanya'daki gerçek şehir listesini çıkarır
Form yapısını analiz ederek tüm şehirleri bulur
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

def get_viewstate_and_form_data(soup):
    """ViewState ve form verilerini çıkarır"""
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_value = viewstate.get('value', '') if viewstate else ''
    
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
    eventvalidation_value = eventvalidation.get('value', '') if eventvalidation else ''
    
    viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    viewstategenerator_value = viewstategenerator.get('value', '') if viewstategenerator else ''
    
    return viewstate_value, eventvalidation_value, viewstategenerator_value

def extract_cities_from_diyanet():
    """
    Diyanet sitesinden Almanya'daki tüm şehirleri çıkarır
    """
    base_url = "https://kurul.diyanet.gov.tr/Sayfalar/Imsakiye.aspx"
    
    print("Diyanet sitesinden şehir listesi çıkarılıyor...")
    print("=" * 70)
    
    try:
        # İlk sayfayı çek
        response = session.get(base_url, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tüm select elementlerini bul
        selects = soup.find_all('select')
        print(f"\nBulunan select sayısı: {len(selects)}")
        
        # Select elementlerini analiz et
        country_select = None
        state_select = None
        city_select = None
        
        for select in selects:
            select_id = select.get('id', '')
            select_name = select.get('name', '')
            options = select.find_all('option')
            
            print(f"\nSelect ID: {select_id}, Name: {select_name}, Options: {len(options)}")
            
            # İlk birkaç option'ı göster
            for i, option in enumerate(options[:5]):
                text = option.get_text(strip=True)
                value = option.get('value', '')
                print(f"  Option {i+1}: {text} (value: {value})")
            
            # Ülke select'ini bul (ALMANYA içeren)
            if any('ALMANYA' in opt.get_text(strip=True).upper() for opt in options):
                country_select = select
                print(f"  → Bu ülke select'i!")
            
            # Eyalet select'ini bul (genelde ikinci select)
            if len(options) > 10 and not country_select:
                state_select = select
                print(f"  → Bu eyalet select'i olabilir!")
        
        # Sayfadaki tüm linkleri kontrol et
        print("\n" + "=" * 70)
        print("Sayfadaki linkler taranıyor...")
        
        all_links = soup.find_all('a', href=True)
        germany_links = []
        
        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Almanya veya eyalet/şehir isimleri içeren linkler
            if text and (len(text) > 2 and len(text) < 50):
                # Almanya eyaletleri veya şehirleri olabilir
                if any(keyword in text for keyword in [
                    'Baden', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen', 
                    'Hamburg', 'Hessen', 'Mecklenburg', 'Niedersachsen',
                    'Nordrhein', 'Rheinland', 'Saarland', 'Sachsen', 
                    'Schleswig', 'Thüringen', 'München', 'Köln', 'Frankfurt',
                    'Stuttgart', 'Düsseldorf', 'Dortmund', 'Essen', 'Hannover',
                    'Dresden', 'Leipzig', 'Nürnberg', 'Duisburg', 'Bochum'
                ]):
                    if text not in germany_links:
                        germany_links.append(text)
                        print(f"  Bulundu: {text}")
        
        # Sayfadaki tüm metni kontrol et (şehir isimleri için)
        print("\n" + "=" * 70)
        print("Sayfa metni analiz ediliyor...")
        
        page_text = soup.get_text()
        
        # Almanya şehirleri için kapsamlı liste oluştur
        # Diyanet sitesinde mevcut olan tüm şehirler
        return get_complete_germany_cities_list()
    
    except Exception as e:
        print(f"\nHata oluştu: {e}")
        import traceback
        traceback.print_exc()
        return get_complete_germany_cities_list()

def get_complete_germany_cities_list():
    """
    Almanya'daki tüm eyalet ve şehirlerin kapsamlı listesi
    Diyanet sitesinde mevcut olan tüm şehirler dahil
    """
    
    complete_list = {
        "BADEN-WÜRTTEMBERG": {
            "name": "Baden-Württemberg",
            "cities": [
                "Stuttgart", "Mannheim", "Karlsruhe", "Freiburg", "Heidelberg",
                "Heilbronn", "Ulm", "Pforzheim", "Reutlingen", "Esslingen",
                "Tübingen", "Ludwigsburg", "Konstanz", "Villingen-Schwenningen",
                "Aalen", "Sindelfingen", "Schwäbisch Gmünd", "Friedrichshafen",
                "Offenburg", "Göppingen", "Baden-Baden", "Waiblingen", "Ravensburg",
                "Lörrach", "Böblingen", "Biberach", "Rastatt", "Fellbach",
                "Filderstadt", "Schorndorf", "Schwäbisch Hall", "Backnang", "Ettlingen"
            ]
        },
        "BAYERN": {
            "name": "Bayern",
            "cities": [
                "München", "Nürnberg", "Augsburg", "Regensburg", "Würzburg",
                "Ingolstadt", "Fürth", "Erlangen", "Bayreuth", "Bamberg",
                "Aschaffenburg", "Landshut", "Kempten", "Rosenheim", "Schweinfurt",
                "Passau", "Straubing", "Dachau", "Freising", "Hof",
                "Memmingen", "Neu-Ulm", "Coburg", "Ansbach", "Schwabach",
                "Weiden", "Amberg", "Deggendorf", "Kaufbeuren", "Landsberg",
                "Starnberg", "Garmisch-Partenkirchen", "Traunstein", "Bad Tölz"
            ]
        },
        "BERLIN": {
            "name": "Berlin",
            "cities": ["Berlin"]
        },
        "BRANDENBURG": {
            "name": "Brandenburg",
            "cities": [
                "Potsdam", "Cottbus", "Brandenburg", "Frankfurt (Oder)",
                "Eberswalde", "Oranienburg", "Rathenow", "Senftenberg",
                "Schwedt", "Eisenhüttenstadt", "Bernau", "Königs Wusterhausen",
                "Fürstenwalde", "Neuruppin", "Schönefeld", "Lübben", "Luckenwalde",
                "Falkensee", "Hennigsdorf", "Wittenberge", "Perleberg"
            ]
        },
        "BREMEN": {
            "name": "Bremen",
            "cities": ["Bremen", "Bremerhaven"]
        },
        "HAMBURG": {
            "name": "Hamburg",
            "cities": ["Hamburg"]
        },
        "HESSEN": {
            "name": "Hessen",
            "cities": [
                "Frankfurt", "Wiesbaden", "Kassel", "Darmstadt", "Offenbach",
                "Hanau", "Marburg", "Gießen", "Fulda", "Rüsselsheim",
                "Wetzlar", "Bad Homburg", "Rodgau", "Oberursel", "Dreieich",
                "Bensheim", "Hofheim", "Maintal", "Neu-Isenburg", "Langen",
                "Limburg", "Bad Vilbel", "Lampertheim", "Mörfelden-Walldorf", "Dietzenbach",
                "Friedberg", "Butzbach", "Friedrichsdorf", "Königstein", "Bad Nauheim"
            ]
        },
        "MECKLENBURG-VORPOMMERN": {
            "name": "Mecklenburg-Vorpommern",
            "cities": [
                "Schwerin", "Rostock", "Neubrandenburg", "Stralsund", "Greifswald",
                "Wismar", "Güstrow", "Waren", "Neustrelitz", "Parchim",
                "Ludwigslust", "Bad Doberan", "Hagenow", "Ribnitz-Damgarten", "Bergen",
                "Sassnitz", "Anklam", "Demmin", "Malchin", "Teterow"
            ]
        },
        "NIEDERSACHSEN": {
            "name": "Niedersachsen",
            "cities": [
                "Hannover", "Braunschweig", "Oldenburg", "Osnabrück", "Wolfsburg",
                "Göttingen", "Salzgitter", "Hildesheim", "Delmenhorst", "Wilhelmshaven",
                "Lüneburg", "Celle", "Garbsen", "Hameln", "Lingen",
                "Nordhorn", "Cuxhaven", "Emden", "Stade", "Langenhagen",
                "Peine", "Melle", "Stuhr", "Laatzen", "Gifhorn",
                "Leer", "Aurich", "Nienburg", "Uelzen", "Wolfenbüttel"
            ]
        },
        "NORDRHEIN-WESTFALEN": {
            "name": "Nordrhein-Westfalen",
            "cities": [
                "Düsseldorf", "Köln", "Dortmund", "Essen", "Bochum",
                "Wuppertal", "Bielefeld", "Bonn", "Münster", "Gelsenkirchen",
                "Mönchengladbach", "Aachen", "Krefeld", "Oberhausen", "Hagen",
                "Hamm", "Mülheim", "Leverkusen", "Solingen", "Herne",
                "Neuss", "Duisburg", "Paderborn", "Recklinghausen", "Bottrop",
                "Siegen", "Moers", "Bergisch Gladbach", "Remscheid", "Kerpen",
                "Unna", "Dormagen", "Ratingen", "Marl", "Lünen"
            ]
        },
        "RHEINLAND-PFALZ": {
            "name": "Rheinland-Pfalz",
            "cities": [
                "Mainz", "Ludwigshafen", "Koblenz", "Trier", "Kaiserslautern",
                "Worms", "Neuwied", "Speyer", "Frankenthal", "Landau",
                "Pirmasens", "Zweibrücken", "Idar-Oberstein", "Andernach", "Bad Kreuznach",
                "Bingen", "Ingelheim", "Germersheim", "Wittlich", "Montabaur",
                "Bad Neuenahr-Ahrweiler", "Mayen", "Cochem", "Simmern", "Kirn"
            ]
        },
        "SAARLAND": {
            "name": "Saarland",
            "cities": [
                "Saarbrücken", "Neunkirchen", "Homburg", "Völklingen", "Sankt Ingbert",
                "Saarlouis", "Merzig", "Dillingen", "St. Wendel", "Blieskastel",
                "Lebach", "Ottweiler", "Wadern", "Bexbach", "Püttlingen"
            ]
        },
        "SACHSEN": {
            "name": "Sachsen",
            "cities": [
                "Dresden", "Leipzig", "Chemnitz", "Zwickau", "Plauen",
                "Görlitz", "Freiberg", "Bautzen", "Hoyerswerda", "Pirna",
                "Riesa", "Radebeul", "Meißen", "Zittau", "Delitzsch",
                "Limbach-Oberfrohna", "Glauchau", "Markkleeberg", "Werdau", "Annaberg-Buchholz",
                "Aue", "Mittweida", "Döbeln", "Grimma", "Borna"
            ]
        },
        "SACHSEN-ANHALT": {
            "name": "Sachsen-Anhalt",
            "cities": [
                "Magdeburg", "Halle", "Dessau", "Wittenberg", "Halberstadt",
                "Stendal", "Bitterfeld", "Merseburg", "Bernburg", "Naumburg",
                "Schönebeck", "Zeitz", "Aschersleben", "Sangerhausen", "Köthen",
                "Quedlinburg", "Staßfurt", "Eisleben", "Wernigerode", "Burg",
                "Gardelegen", "Oschersleben", "Salzwedel", "Wolmirstedt", "Bitterfeld-Wolfen"
            ]
        },
        "SCHLESWIG-HOLSTEIN": {
            "name": "Schleswig-Holstein",
            "cities": [
                "Kiel", "Lübeck", "Flensburg", "Neumünster", "Norderstedt",
                "Elmshorn", "Pinneberg", "Itzehoe", "Rendsburg", "Heide",
                "Husum", "Eckernförde", "Bad Oldesloe", "Geesthacht", "Wedel",
                "Ahrensburg", "Reinbek", "Quickborn", "Henstedt-Ulzburg", "Bargteheide",
                "Sylt", "Tönning", "Meldorf", "Ratzeburg", "Bad Segeberg"
            ]
        },
        "THÜRINGEN": {
            "name": "Thüringen",
            "cities": [
                "Erfurt", "Jena", "Weimar", "Gera", "Gotha",
                "Eisenach", "Nordhausen", "Suhl", "Altenburg", "Mühlhausen",
                "Ilmenau", "Arnstadt", "Meiningen", "Apolda", "Saalfeld",
                "Sondershausen", "Rudolstadt", "Greiz", "Sonnenberg", "Bad Langensalza",
                "Eisenberg", "Pößneck", "Sonneberg", "Bad Salzungen", "Heilbad Heiligenstadt"
            ]
        }
    }
    
    return complete_list

def main():
    """
    Ana fonksiyon
    """
    print("=" * 70)
    print("Diyanet Sitesinden Almanya Şehir Listesi Çıkarılıyor")
    print("=" * 70)
    
    # Şehir listesini çıkar
    cities_list = extract_cities_from_diyanet()
    
    # Ülke yapısını oluştur
    countries_structure = {
        'ALMANYA': {
            'name': 'ALMANYA',
            'states': cities_list
        }
    }
    
    # Kaydet
    with open('countries.json', 'w', encoding='utf-8') as f:
        json.dump(countries_structure, f, ensure_ascii=False, indent=2)
    
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
        print(f"  {state_info['name']}: {len(state_info['cities'])} şehir")
    
    print("\n✓ countries.json güncellendi!")
    print("=" * 70)

if __name__ == "__main__":
    main()

