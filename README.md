# İmsakiye PDF Oluşturucu

2026 Yılı Ramazan İmsakiyesi PDF oluşturma uygulaması. DİTİB (Diyanet İşleri Türk İslam Birliği) için geliştirilmiştir.

## 📋 Özellikler

- **Eyalet ve Şehir Seçimi**: Almanya'daki tüm eyaletler ve şehirler için imsakiye oluşturma
- **PDF Oluşturma**: 6 farklı tema seçeneği ile özelleştirilebilir PDF çıktısı
- **Düzenlenebilir İçerik**: Başlık ve namaz vakitlerini düzenleme imkanı
- **Bayram Namazı Vakti**: Bayram namazı vaktini otomatik gösterim
- **Kadir Gecesi**: 26-27 Ramazan arası Kadir Gecesi bilgisi
- **Responsive Tasarım**: Mobil ve masaüstü cihazlarda çalışır

## 🚀 Kurulum

### Gereksinimler

- PHP 7.4 veya üzeri
- SQLite3 desteği
- Web sunucusu (Apache/Nginx) veya PHP built-in server
- Modern web tarayıcısı

### Adımlar

1. Projeyi klonlayın veya indirin:
```bash
git clone https://github.com/kullanici/imsakiyepdf.git
cd imsakiyepdf
```

2. Veritabanının mevcut olduğundan emin olun:
   - `imsakiye.db` dosyası proje kök dizininde olmalıdır

3. Web sunucusunu başlatın:

**PHP Built-in Server (Geliştirme için):**
```bash
php -S localhost:8000
```

**Apache/Nginx:**
   - Projeyi web sunucunuzun root dizinine kopyalayın
   - Apache için `.htaccess` dosyası gerekebilir

4. Tarayıcıda açın:
   - `http://localhost:8000` (PHP built-in server için)
   - Veya sunucunuzun URL'si

## 📁 Proje Yapısı

```
imsakiyepdf/
├── api.php              # PHP Backend API
├── index.html           # Ana HTML sayfası
├── app.js               # Frontend JavaScript
├── styles.css           # CSS stilleri
├── imsakiye.db          # SQLite veritabanı
├── logo.webp            # DİTİB logosu
├── bg.jpg               # Arka plan resmi
├── tema1.png - tema6.png # PDF tema arka planları
└── backup_20260104_015734/ # Yedek dosyalar
```

## 🗄️ Veritabanı Yapısı

Uygulama SQLite veritabanı kullanır. Ana tablolar:

- `countries`: Ülke, eyalet ve şehir bilgileri
- `imsakiye`: Ramazan ayı namaz vakitleri
- `bayram_namazi`: Bayram namazı vakitleri

## 🔌 API Endpoints


## 🎨 Tema Seçenekleri

Uygulama 6 farklı PDF teması sunar:
- **Tema 1**: Varsayılan tema
- **Tema 2-6**: Alternatif arka plan tasarımları

## 🛠️ Kullanım

1. **Eyalet Seçimi**: Dropdown menüden bir eyalet seçin
2. **Şehir Seçimi**: Seçilen eyalete göre şehirler yüklenecektir
3. **İmsakiye Oluştur**: "İmsakiye Oluştur" butonuna tıklayın
4. **Düzenleme**: 
   - Başlığı düzenlemek için başlığa tıklayın
   - Namaz vakitlerini düzenlemek için hücrelere tıklayın
5. **PDF Oluştur**: 
   - "PDF Olarak Yazdır" butonuna tıklayın
   - Bir tema seçin
   - PDF otomatik olarak indirilecektir

## 🔒 Güvenlik

- XSS koruması: ContentEditable alanlarında güvenlik kontrolleri
- Input validation: API endpoint'lerinde parametre doğrulama
- SQL injection koruması: PDO prepared statements kullanımı

## 📝 Notlar

- PDF oluşturma işlemi tarayıcıda gerçekleşir (client-side)
- Büyük veri setleri için PDF oluşturma süresi artabilir
- Mobil cihazlarda PDF her zaman masaüstü düzeninde oluşturulur



MIT License

## 👤 Geliştirici

Emre Sarıçayır

## 📞 İletişim

004917683254886



