// API Base URL - Direkt api.php kullan (mod_rewrite'a bağımlı değil)
const API_BASE = (() => {
    // Mevcut sayfanın path'ini al
    const path = window.location.pathname;
    // /imsakiye/ veya /imsakiye/index.html gibi path'lerden base'i çıkar
    let base = path.substring(0, path.lastIndexOf('/'));
    // Eğer root'taysa boş string olur
    if (base === '' || base === '/') {
        base = '';
    }
    // api.php'ye direkt path parametresi ile istek yap
    // Base boş değilse başına / ekle, değilse direkt /api.php
    let apiPath;
    if (base && base !== '/') {
        apiPath = base + '/api.php?path=';
    } else {
        apiPath = '/api.php?path=';
    }
    console.log('API Base URL oluşturuldu:', apiPath, '(base:', base, ')');
    return apiPath;
})();

// API çağrısı helper fonksiyonu
async function apiCall(endpoint) {
    // Endpoint'te zaten encode edilmiş olabilir, tekrar encode etme
    const url = API_BASE + endpoint;
    console.log('API Call - Endpoint:', endpoint);
    console.log('API Call - Full URL:', url);
    const response = await fetch(url);
    if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('API Error Response:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

// Global değişkenler
let countriesData = {}; // Cache için
let currentData = null;
let isGeneratingPDF = false; // PDF oluşturma işlemi devam ediyor mu?

// XSS koruması için HTML escape fonksiyonu
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ContentEditable alanları için XSS koruması
function sanitizeContentEditable(element) {
    if (!element) return;
    element.addEventListener('paste', function(e) {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData('text/plain');
        document.execCommand('insertText', false, text);
    });
    element.addEventListener('input', function() {
        // Script tag'lerini ve zararlı HTML'leri temizle
        const content = element.innerHTML;
        const cleaned = content
            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
            .replace(/javascript:/gi, '')
            .replace(/on\w+\s*=/gi, '');
        if (content !== cleaned) {
            element.innerHTML = cleaned;
        }
    });
}

// Sayfa yüklendiğinde
// Sabit: Almanya country code
const GERMANY_COUNTRY_CODE = 'ALMANYA';

// Sayfa yüklendiğinde çalışacak fonksiyon
async function initializeApp() {
    console.log('=== Uygulama başlatılıyor ===');
    console.log('Document ready state:', document.readyState);
    
    try {
        await loadStates(); // Direkt eyaletleri yükle (Almanya için)
        setupEventListeners();
        
        // ContentEditable alanlarına sanitization ekle
        setTimeout(() => {
            document.querySelectorAll('[contenteditable="true"]').forEach(el => {
                sanitizeContentEditable(el);
            });
        }, 100);
        
        console.log('✓ Uygulama başlatıldı');
    } catch (error) {
        console.error('✗ Uygulama başlatılırken hata:', error);
        showError('Uygulama başlatılırken bir hata oluştu: ' + error.message);
    }
}

// DOMContentLoaded event listener
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
    console.log('DOMContentLoaded event listener eklendi');
} else {
    // DOM zaten yüklenmiş
    console.log('DOM zaten yüklü, direkt başlatılıyor');
    initializeApp();
}

// Fallback: window.onload (daha güvenli)
window.addEventListener('load', function() {
    console.log('Window load event tetiklendi');
    // Eğer setupEventListeners henüz çalışmadıysa tekrar dene
    const pdfBtn = document.getElementById('print-pdf-btn');
    if (pdfBtn && !pdfBtn.hasAttribute('data-listener-added')) {
        console.log('Event listener tekrar ekleniyor (window.load fallback)');
        setupEventListeners();
        pdfBtn.setAttribute('data-listener-added', 'true');
    }
});

// Eyaletleri API'den yükle (Almanya için direkt)
async function loadStates() {
    try {
        console.log('Eyaletler yükleniyor (Almanya)...');
        console.log('GERMANY_COUNTRY_CODE:', GERMANY_COUNTRY_CODE);
        // encodeURIComponent kullanmadan direkt gönder (13 zaten güvenli)
        const endpoint = `states/${GERMANY_COUNTRY_CODE}`;
        console.log('API Endpoint:', endpoint);
        const states = await apiCall(endpoint);
        
        // Cache'e ekle
        if (!countriesData[GERMANY_COUNTRY_CODE]) {
            countriesData[GERMANY_COUNTRY_CODE] = {
                name: 'ALMANYA',
                states: {}
            };
        }
        countriesData[GERMANY_COUNTRY_CODE].states = {};
        states.forEach(state => {
            countriesData[GERMANY_COUNTRY_CODE].states[state.state_code] = { name: state.state_name };
        });
        
        console.log('✓ Eyaletler yüklendi:', states.length);
        await populateStates(states);
    } catch (error) {
        console.error('Eyaletler yüklenirken hata:', error);
        showError('Eyaletler yüklenirken bir hata oluştu: ' + error.message);
    }
}

// Eyaletleri doldur
async function populateStates(states) {
    const stateSelect = document.getElementById('state-select');
    if (!stateSelect) {
        console.error('state-select elementi bulunamadı!');
        return;
    }
    
    stateSelect.innerHTML = '<option value="">-- Eyalet Seçin --</option>';
    
    if (!states || !Array.isArray(states) || states.length === 0) {
        console.error('Eyaletler array değil veya boş:', states);
        showError('Eyaletler yüklenemedi. Lütfen sayfayı yenileyin.');
        return;
    }
    
    // Eyaletleri A'dan Z'ye sırala
    const sortedStates = [...states].sort((a, b) => {
        const nameA = (a.state_name || '').toUpperCase();
        const nameB = (b.state_name || '').toUpperCase();
        return nameA.localeCompare(nameB, 'tr');
    });
    
    sortedStates.forEach(state => {
        if (state && state.state_code && state.state_name) {
            const option = document.createElement('option');
            option.value = state.state_code;
            option.textContent = state.state_name;
            stateSelect.appendChild(option);
        }
    });
    
    console.log('✓ Eyaletler dropdown\'a eklendi:', states.length);
}

// Event listener'ları ayarla
function setupEventListeners() {
    console.log('=== setupEventListeners çağrıldı ===');
    
    // Elementlerin yüklendiğinden emin ol
    const stateSelect = document.getElementById('state-select');
    const citySelect = document.getElementById('city-select');
    const continueBtn = document.getElementById('continue-btn');
    const pdfBtn = document.getElementById('print-pdf-btn');
    const cancelBtn = document.getElementById('cancel-theme-btn');
    const themeModal = document.getElementById('theme-modal');
    
    if (stateSelect) {
        stateSelect.addEventListener('change', onStateChange);
        console.log('✓ state-select event listener eklendi');
    } else {
        console.error('✗ state-select elementi bulunamadı!');
    }
    
    if (citySelect) {
        citySelect.addEventListener('change', onCityChange);
        console.log('✓ city-select event listener eklendi');
    } else {
        console.error('✗ city-select elementi bulunamadı!');
    }
    
    // Devam Et butonu
    if (continueBtn) {
        continueBtn.addEventListener('click', onContinueClick);
        console.log('✓ continue-btn event listener eklendi');
    } else {
        console.error('✗ continue-btn elementi bulunamadı!');
    }
    
    // PDF butonuna tıklanınca tema seçim modalını göster
    if (pdfBtn) {
        // Önce mevcut event listener'ı kaldırmak için clone yap
        const newPdfBtn = pdfBtn.cloneNode(true);
        pdfBtn.parentNode.replaceChild(newPdfBtn, pdfBtn);
        
        // Yeni event listener ekle
        newPdfBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('=== PDF butonu tıklandı ===');
            console.log('currentData:', currentData);
            try {
                showThemeModal();
            } catch (error) {
                console.error('showThemeModal hatası:', error);
                showError('Modal açılırken bir hata oluştu: ' + error.message);
            }
        });
        console.log('✓ PDF butonu event listener eklendi');
    } else {
        console.error('✗ print-pdf-btn elementi bulunamadı!');
    }
    
    // Tema seçim modalı kapatma
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('İptal butonu tıklandı');
            closeThemeModal();
        });
        console.log('✓ cancel-theme-btn event listener eklendi');
    } else {
        console.error('✗ cancel-theme-btn elementi bulunamadı!');
    }
    
    // Modal dışına tıklanınca kapat ve tema seçeneklerine tıklama olayları
    if (themeModal) {
        themeModal.addEventListener('click', function(e) {
            // Modal dışına tıklanınca kapat
            if (e.target.id === 'theme-modal') {
                console.log('Modal dışına tıklandı, kapatılıyor');
                closeThemeModal();
            }
            // Tema seçeneklerine tıklama
            const themeOption = e.target.closest('.theme-option');
            if (themeOption) {
                e.preventDefault();
                e.stopPropagation(); // Event propagation'ı durdur - birden fazla tetiklenmeyi önle
                const theme = themeOption.getAttribute('data-theme');
                console.log('Tema seçildi:', theme);
                if (theme && !isGeneratingPDF) {
                    selectTheme(theme);
                } else if (isGeneratingPDF) {
                    console.log('PDF oluşturma devam ediyor, tema seçimi reddedildi');
                }
            }
        });
        console.log('✓ theme-modal event listener eklendi');
    } else {
        console.error('✗ theme-modal elementi bulunamadı!');
    }
    
    console.log('=== setupEventListeners tamamlandı ===');
}

// Eyalet değiştiğinde (güncellenmiş - ülke seçimi yok)
async function onStateChange(e) {
    const stateCode = e.target.value;
    const citySelect = document.getElementById('city-select');
    const continueBtn = document.getElementById('continue-btn');
    
    citySelect.innerHTML = '<option value="">-- Yükleniyor... --</option>';
    citySelect.disabled = true;
    if (continueBtn) continueBtn.disabled = true;
    
    if (!stateCode) {
        citySelect.innerHTML = '<option value="">-- Önce Eyalet Seçin --</option>';
        return;
    }
    
    try {
        const cities = await apiCall(`cities/${encodeURIComponent(GERMANY_COUNTRY_CODE)}/${encodeURIComponent(stateCode)}`);
        
        console.log('Şehirler yüklendi:', cities);
        
        citySelect.innerHTML = '<option value="">-- Şehir Seçin --</option>';
        if (cities && Array.isArray(cities) && cities.length > 0) {
            // Şehirleri A'dan Z'ye sırala
            const sortedCities = [...cities].sort((a, b) => {
                const nameA = (a || '').toUpperCase();
                const nameB = (b || '').toUpperCase();
                return nameA.localeCompare(nameB, 'tr');
            });
            
            sortedCities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
            citySelect.disabled = false;
        } else {
            citySelect.innerHTML = '<option value="">-- Şehir bulunamadı --</option>';
            console.warn('Şehirler array değil veya boş:', cities);
        }
        
        // Cache'e ekle
        if (countriesData[GERMANY_COUNTRY_CODE] && countriesData[GERMANY_COUNTRY_CODE].states[stateCode]) {
            countriesData[GERMANY_COUNTRY_CODE].states[stateCode].cities = cities;
        }
    } catch (error) {
        console.error('Şehirler yüklenirken hata:', error);
        showError('Şehirler yüklenirken bir hata oluştu: ' + error.message);
        citySelect.innerHTML = '<option value="">-- Hata --</option>';
    }
}

// Şehir değiştiğinde - Devam Et butonunu aktif et
function onCityChange(e) {
    const continueBtn = document.getElementById('continue-btn');
    if (e.target.value && continueBtn) {
        continueBtn.disabled = false;
    } else if (continueBtn) {
        continueBtn.disabled = true;
    }
}

// Devam Et butonuna tıklanınca
function onContinueClick(e) {
    e.preventDefault();
    const stateCode = document.getElementById('state-select').value;
    const cityName = document.getElementById('city-select').value;
    
    if (!stateCode || !cityName) {
        showError('Lütfen eyalet ve şehir seçin.');
        return;
    }
    
    // İmsakiye yükle ve sayfayı göster
    loadImsakiye();
}

// İmsakiye yükle
async function loadImsakiye() {
    const stateCode = document.getElementById('state-select').value;
    const cityName = document.getElementById('city-select').value;
    
    if (!stateCode || !cityName) {
        showError('Lütfen eyalet ve şehir seçin.');
        return;
    }
    
    const countryCode = GERMANY_COUNTRY_CODE; // Sabit: Almanya
    
    // Loading göster
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) loadingDiv.style.display = 'block';
    
    try {
        console.log('=== İmsakiye Yükleme ===');
        console.log('Ülke:', countryCode);
        console.log('Eyalet:', stateCode);
        console.log('Şehir:', cityName);
        
        // İmsakiye verisini API'den al
        let cityData;
        try {
            cityData = await apiCall(`imsakiye/${encodeURIComponent(countryCode)}/${encodeURIComponent(stateCode)}/${encodeURIComponent(cityName)}`);
        } catch (error) {
            if (error.message.includes('404')) {
                throw new Error('Bu şehir için veri bulunamadı.');
            }
            throw error;
        }
        
        if (!cityData || cityData.length === 0) {
            throw new Error('Veri bulunamadı.');
        }
        
        console.log('✓ Veri başarıyla yüklendi:', cityData.length, 'satır');
        
        // Bayram namazı vaktini al (opsiyonel)
        let bayramVakti = null;
        try {
            const bayramUrl = `bayram-namazi/${encodeURIComponent(countryCode)}/${encodeURIComponent(stateCode)}/${encodeURIComponent(cityName)}`;
            console.log('Bayram namazı vakti API çağrısı:', bayramUrl);
            const bayramData = await apiCall(bayramUrl);
            console.log('Bayram namazı API yanıtı:', bayramData);
            bayramVakti = bayramData.vakti;
            console.log('Bayram namazı vakti:', bayramVakti);
        } catch (err) {
            console.error('Bayram namazı vakti alınamadı (opsiyonel):', err);
        }
        
        // Cache'den ülke ve eyalet isimlerini al
        const countryName = countriesData[countryCode]?.name || 'ALMANYA';
        const stateName = countriesData[countryCode]?.states[stateCode]?.name || stateCode;
        
        currentData = {
            country: countryName,
            state: stateName,
            city: cityName,
            data: cityData,
            bayramVakti: bayramVakti
        };
        
        // Hata mesajını temizle
        const errorMsg = document.getElementById('error-message');
        if (errorMsg) {
            errorMsg.style.display = 'none';
        }
        
        // Giriş sayfasını gizle, imsakiye sayfasını göster
        const selectionPage = document.getElementById('selection-page');
        const entryHeader = document.getElementById('entry-header');
        const entryFooter = document.getElementById('entry-footer');
        const mainHeader = document.getElementById('main-header');
        const mainFooter = document.getElementById('main-footer');
        const imsakiyeContainer = document.getElementById('imsakiye-container');
        const infoNote = document.getElementById('info-note');
        
        if (selectionPage) selectionPage.style.display = 'none';
        if (entryHeader) entryHeader.style.display = 'none';
        if (entryFooter) entryFooter.style.display = 'none';
        if (mainHeader) mainHeader.style.display = 'block';
        if (mainFooter) mainFooter.style.display = 'block';
        if (imsakiyeContainer) imsakiyeContainer.style.display = 'block';
        if (infoNote) infoNote.style.display = 'block';
        
        displayImsakiye(currentData);
        
    } catch (error) {
        console.error('✗ İmsakiye yükleme hatası:', error);
        showError(`Hata: ${error.message}`);
        
        // Container'ı gizle
        const container = document.getElementById('imsakiye-container');
        if (container) {
            container.style.display = 'none';
        }
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}

// Örnek veri oluştur (19 Şubat 2026 başlangıçlı)
function generateSampleData() {
    const data = [];
    const baseDate = new Date(2026, 1, 19);
    for (let i = 0; i < 30; i++) {
        const date = new Date(baseDate);
        date.setDate(baseDate.getDate() + i);
        data.push({
            hicri: `${i + 1} Ramazan 1447`,
            miladi: formatDate(date),
            imsak: formatTime(5, 30 - Math.floor(i/2)),
            gunes: formatTime(6, 50 - Math.floor(i/2)),
            ogle: "12:45",
            ikindi: "15:50",
            aksam: formatTime(18, 20 + Math.floor(i/2)),
            yatsi: formatTime(19, 45 + Math.floor(i/2))
        });
    }
    return data;
}

function formatDate(date) {
    const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
    const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
    return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()} ${days[date.getDay()]}`;
}

function formatTime(h, m) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function displayImsakiye(data) {
    console.log('=== displayImsakiye çağrıldı ===');
    console.log('Gösterilecek veri:', data);
    console.log('Veri uzunluğu:', data.data ? data.data.length : 0);
    if (data.data && data.data.length > 0) {
        console.log('İlk satır:', data.data[0]);
        console.log('Son satır:', data.data[data.data.length - 1]);
    }
    
    const container = document.getElementById('imsakiye-container');
    const title = document.getElementById('location-title');
    const tbody = document.getElementById('imsakiye-tbody');
    
    if (!container || !title || !tbody) {
        console.error('HTML elementleri bulunamadı!');
        return;
    }
    
    title.textContent = `${data.city}, ${data.state}, ${data.country}`;
    tbody.innerHTML = ''; // Tabloyu temizle
    
    console.log('Tablo temizlendi, yeni veriler ekleniyor...');
    console.log('Gösterilecek veri sayısı:', data.data ? data.data.length : 0);
    
    if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
        console.error('Veri yok veya geçersiz!');
        showError('Veri gösterilemedi. Lütfen tekrar deneyin.');
        return;
    }
    
    let rowCount = 0;
    data.data.forEach((row, index) => {
        // Veri doğrulama
        if (!row.hicri || !row.miladi || !row.imsak) {
            console.warn('Geçersiz satır atlandı:', row);
            return;
        }
        
        // Şevval ayına geçen satırı atla (son satır)
        const hicriUpper = (row.hicri || '').toUpperCase();
        if (hicriUpper.includes('ŞEVVAL') || hicriUpper.includes('SEVVAL')) {
            console.log('Şevval ayına geçen satır atlandı:', row);
            return;
        }
        
        const tr = document.createElement('tr');
        // XSS koruması: innerHTML yerine güvenli DOM oluşturma
        const cells = [
            { content: row.hicri, editable: true },
            { content: row.miladi, editable: true },
            { content: row.imsak, editable: true, className: 'imsak-cell', bold: true },
            { content: row.gunes, editable: true },
            { content: row.ogle, editable: true },
            { content: row.ikindi, editable: true },
            { content: row.aksam, editable: true, className: 'aksam-cell', bold: true },
            { content: row.yatsi, editable: true }
        ];
        
        cells.forEach(cell => {
            const td = document.createElement('td');
            if (cell.className) td.className = cell.className;
            if (cell.editable) td.setAttribute('contenteditable', 'true');
            
            if (cell.bold) {
                const strong = document.createElement('strong');
                strong.textContent = escapeHtml(cell.content || '');
                td.appendChild(strong);
            } else {
                td.textContent = cell.content || '';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
        rowCount++;
        
        // 26 Ramazan ile 27 Ramazan arasına KADİR GECESİ satırı ekle
        if (row.hicri && row.hicri.includes('26 Ramazan')) {
            const kadirRow = document.createElement('tr');
            kadirRow.className = 'kadir-gecesi-row';
            const kadirCell = document.createElement('td');
            kadirCell.colSpan = 8;
            kadirCell.className = 'kadir-gecesi-cell';
            kadirCell.textContent = 'KADİR GECEMİZ MÜBAREK OLSUN';
            kadirRow.appendChild(kadirCell);
            tbody.appendChild(kadirRow);
        }
    });
    
    console.log(`✓ ${rowCount} satır tabloya eklendi`);
    console.log('İlk satır verileri:', data.data[0]);
    console.log('Son satır verileri:', data.data[data.data.length - 1]);
    
    // Bayram namazı vaktini göster
    const bayramInfo = document.getElementById('bayram-namazi-info');
    const bayramVakti = document.getElementById('bayram-namazi-vakti');
    const bayramTarih = document.getElementById('bayram-tarih');
    
    // Bayram tarihini bul (30 Ramazan'dan sonraki gün)
    let bayramTarihText = '';
    if (data.data && data.data.length > 0) {
        // Son günü bul (30 Ramazan)
        const lastDay = data.data.find(row => row.hicri && row.hicri.includes('30 Ramazan'));
        if (lastDay) {
            // Miladi tarihi parse et ve bir gün ekle
            const tarihMatch = lastDay.miladi.match(/(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\w+)/);
            if (tarihMatch) {
                const gun = parseInt(tarihMatch[1]);
                const ay = tarihMatch[2];
                const yil = parseInt(tarihMatch[3]);
                const gunAdi = tarihMatch[4];
                
                // Ay ismini sayıya çevir
                const ayIsimleri = {
                    'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
                    'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12
                };
                const ayNumarasi = ayIsimleri[ay];
                
                if (ayNumarasi) {
                    // Bir gün sonrasını hesapla
                    const bayramTarihi = new Date(yil, ayNumarasi - 1, gun);
                    bayramTarihi.setDate(bayramTarihi.getDate() + 1);
                    
                    // Gün adını bul
                    const gunAdlari = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
                    const bayramGunAdi = gunAdlari[bayramTarihi.getDay()];
                    
                    // Ay ismini bul
                    const ayIsimleriReverse = {
                        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                        7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
                    };
                    const bayramAy = ayIsimleriReverse[bayramTarihi.getMonth() + 1];
                    
                    bayramTarihText = `${bayramTarihi.getDate()} ${bayramAy} ${bayramTarihi.getFullYear()} ${bayramGunAdi} Ramazan Bayramının 1.Günüdür`;
                }
            }
        }
    }
    
    // Eğer tarih bulunamadıysa varsayılan değer kullan
    if (!bayramTarihText) {
        bayramTarihText = '20 Mart 2026 Cuma Ramazan Bayramının 1.Günüdür';
    }
    
    // Bayram tarihini her zaman göster (bayram namazı vakti eklenmeden)
    bayramTarih.textContent = bayramTarihText;
    
    // Şehir kodlarını bul (cache'den)
    const countryCode = Object.keys(countriesData).find(code => 
        countriesData[code]?.name === data.country
    ) || document.getElementById('country-select')?.value;
    
    // Bayram namazı vaktini al (varsa) - ayrı span için
    const bayramVaktiText = data.bayramVakti || '';
    console.log('displayImsakiye - bayramVaktiText:', bayramVaktiText);
    console.log('displayImsakiye - data.bayramVakti:', data.bayramVakti);
    
    // Bayram namazı vakti varsa göster, yoksa gizle (ayrı span için)
    if (bayramVaktiText) {
        bayramVakti.textContent = bayramVaktiText;
        document.querySelector('.bayram-namazi-text').style.display = '';
    } else {
        document.querySelector('.bayram-namazi-text').style.display = 'none';
    }
    
    // Bayram bilgisini her zaman göster
    bayramInfo.style.display = 'block';
    
    // Yeni oluşturulan contentEditable alanlarına sanitization ekle
    setTimeout(() => {
        container.querySelectorAll('[contenteditable="true"]').forEach(el => {
            sanitizeContentEditable(el);
        });
    }, 50);
    
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth' });
}

// Başlık düzenleme fonksiyonu
function editTitle() {
    const titleElement = document.getElementById('location-title');
    if (titleElement) {
        titleElement.focus();
        // Metni seç
        const range = document.createRange();
        range.selectNodeContents(titleElement);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

// Tema seçim modalını göster
function showThemeModal() {
    console.log('=== showThemeModal çağrıldı ===');
    console.log('currentData:', currentData);
    
    if (!currentData) {
        console.warn('currentData yok, hata gösteriliyor');
        showError('Önce bir imsakiye yükleyin.');
        return;
    }
    
    // Eğer PDF oluşturma devam ediyorsa, modal açma
    if (isGeneratingPDF) {
        console.log('PDF oluşturma devam ediyor, modal açılmıyor');
        return;
    }
    
    const modal = document.getElementById('theme-modal');
    console.log('Modal elementi:', modal);
    
    if (!modal) {
        console.error('✗ Modal elementi bulunamadı!');
        showError('Tema seçim modalı bulunamadı. Lütfen sayfayı yenileyin.');
        return;
    }
    
    // PDF butonunu disable et
    const pdfButton = document.getElementById('print-pdf-btn');
    if (pdfButton) {
        pdfButton.disabled = true;
        pdfButton.style.opacity = '0.6';
        pdfButton.style.cursor = 'not-allowed';
    }
    
    try {
        // Hem class hem style ile göster (daha güvenli)
        modal.classList.add('show');
        modal.style.display = 'flex';
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
        
        console.log('✓ Modal gösterildi (display: flex, class: show)');
        
        // Modal'ın görünür olduğunu doğrula
        setTimeout(() => {
            const computedStyle = window.getComputedStyle(modal);
            console.log('Modal kontrol:');
            console.log('  - display:', computedStyle.display);
            console.log('  - visibility:', computedStyle.visibility);
            console.log('  - z-index:', computedStyle.zIndex);
            console.log('  - opacity:', computedStyle.opacity);
            
            if (computedStyle.display === 'none') {
                console.error('⚠ Modal hala görünmüyor! CSS override ediliyor olabilir.');
                // Zorla göster
                modal.style.setProperty('display', 'flex', 'important');
            }
        }, 100);
    } catch (error) {
        console.error('Modal gösterilirken hata:', error);
        showError('Modal açılırken bir hata oluştu: ' + error.message);
    }
}

// Tema seçim modalını kapat
function closeThemeModal() {
    console.log('closeThemeModal çağrıldı');
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        console.log('✓ Modal kapatıldı');
        
        // Eğer PDF oluşturma başlamadıysa, PDF butonunu tekrar aktif et
        if (!isGeneratingPDF) {
            const pdfButton = document.getElementById('print-pdf-btn');
            if (pdfButton) {
                pdfButton.disabled = false;
                pdfButton.style.opacity = '1';
                pdfButton.style.cursor = 'pointer';
            }
        }
    } else {
        console.error('✗ Modal elementi bulunamadı (closeThemeModal)');
    }
}

// Tema seçildiğinde PDF oluştur
function selectTheme(themeName) {
    // Eğer PDF oluşturma zaten devam ediyorsa, yeni istekleri engelle
    if (isGeneratingPDF) {
        console.log('PDF oluşturma zaten devam ediyor, yeni istek reddedildi');
        return;
    }
    
    console.log('Tema seçildi:', themeName);
    
    // Modal'ı kapat
    closeThemeModal();
    
    // Loading modal'ı göster ve mesajı güncelle
    const loadingModal = document.getElementById('loading-modal');
    const loadingMessage = document.getElementById('loading-message');
    if (loadingModal) {
        loadingModal.style.display = 'flex';
        if (loadingMessage) {
            loadingMessage.textContent = 'İmsakiyeniz Oluşturuluyor...';
        }
    }
    
    // PDF butonunu disable et
    const pdfButton = document.getElementById('print-pdf-btn');
    if (pdfButton) {
        pdfButton.disabled = true;
        pdfButton.style.opacity = '0.6';
        pdfButton.style.cursor = 'not-allowed';
    }
    
    // Body'ye tema class'ı ekle (CSS için)
    document.body.classList.remove('theme-1', 'theme-2', 'theme-3', 'theme-4', 'theme-5', 'theme-6');
    if (themeName === 'tema2') {
        document.body.classList.add('theme-2');
    } else if (themeName === 'tema3') {
        document.body.classList.add('theme-3');
    } else if (themeName === 'tema4') {
        document.body.classList.add('theme-4');
    } else if (themeName === 'tema5') {
        document.body.classList.add('theme-5');
    } else if (themeName === 'tema6') {
        document.body.classList.add('theme-6');
    } else {
        document.body.classList.add('theme-1');
    }
    
    // PDF oluşturmayı başlat
    console.log('generatePDF çağrılıyor...');
    generatePDF(themeName).catch(error => {
        console.error('PDF oluşturma hatası (selectTheme):', error);
        showError('PDF oluşturulurken bir hata oluştu: ' + error.message);
        isGeneratingPDF = false; // Hata durumunda flag'i sıfırla
        
        // Loading modal'ı gizle ve butonu tekrar aktif et
        const loadingModal = document.getElementById('loading-modal');
        if (loadingModal) loadingModal.style.display = 'none';
        if (pdfButton) {
            pdfButton.disabled = false;
            pdfButton.style.opacity = '1';
            pdfButton.style.cursor = 'pointer';
        }
    });
}

// PDF OLUŞTURMA ANA FONKSİYON - HTML2Canvas ile (arka plan desteği için)
// PDF OLUŞTURMA ANA FONKSİYON - html2pdf.js ile (daha stabil ve basit)
async function generatePDF(selectedTheme = 'tema1') {
    // Eğer PDF oluşturma zaten devam ediyorsa, yeni istekleri engelle
    if (isGeneratingPDF) {
        console.log('PDF oluşturma zaten devam ediyor, yeni istek reddedildi');
        return;
    }
    
    console.log('=== generatePDF başlatıldı ===', selectedTheme);
    
    // PDF oluşturma flag'ini set et
    isGeneratingPDF = true;
    
    if (!currentData) {
        console.error('currentData yok!');
        showError('Önce bir imsakiye yükleyin.');
        isGeneratingPDF = false;
        return;
    }
    
    // jsPDF ve html2canvas yüklü mü kontrol et
    if (typeof window.jspdf === 'undefined') {
        console.error('jsPDF yüklü değil!');
        showError('PDF kütüphanesi (jsPDF) yüklenemedi. Lütfen sayfayı yenileyin.');
        isGeneratingPDF = false;
        return;
    }
    
    if (typeof html2canvas === 'undefined') {
        console.error('html2canvas yüklü değil!');
        showError('PDF kütüphanesi (html2canvas) yüklenemedi. Lütfen sayfayı yenileyin.');
        isGeneratingPDF = false;
        return;
    }
    
    console.log('✓ Kütüphaneler yüklü');
    
    // Body'ye tema class'ı ekle (CSS renkleri için)
    document.body.classList.remove('theme-1', 'theme-2', 'theme-3', 'theme-4', 'theme-5', 'theme-6');
    if (selectedTheme === 'tema2') {
        document.body.classList.add('theme-2');
    } else if (selectedTheme === 'tema3') {
        document.body.classList.add('theme-3');
    } else if (selectedTheme === 'tema4') {
        document.body.classList.add('theme-4');
    } else if (selectedTheme === 'tema5') {
        document.body.classList.add('theme-5');
    } else if (selectedTheme === 'tema6') {
        document.body.classList.add('theme-6');
    } else {
        document.body.classList.add('theme-1');
    }
    
    // Loading modal'ı göster (eğer selectTheme'den gelmediyse)
    const loadingModal = document.getElementById('loading-modal');
    const loadingMessage = document.getElementById('loading-message');
    if (loadingModal && loadingModal.style.display === 'none') {
        loadingModal.style.display = 'flex';
        if (loadingMessage) {
            loadingMessage.textContent = 'İmsakiyeniz Oluşturuluyor...';
        }
    }
    
    // PDF butonunu, düzenle butonunu ve bilgilendirme notunu geçici olarak gizle
    const pdfButton = document.getElementById('print-pdf-btn');
    const actionButtons = document.querySelector('.action-buttons');
    const editTitleBtn = document.querySelector('.edit-title-btn');
    const infoNote = document.querySelector('.info-note');
    if (pdfButton) {
        pdfButton.style.display = 'none';
        pdfButton.disabled = true;
    }
    if (actionButtons) actionButtons.style.display = 'none';
    if (editTitleBtn) editTitleBtn.style.display = 'none';
    if (infoNote) infoNote.style.display = 'none';
    
    // HTML2Canvas ile HTML'i resme çevir
    const container = document.getElementById('imsakiye-container');
    if (!container) {
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (pdfButton) pdfButton.style.display = '';
        if (actionButtons) actionButtons.style.display = '';
        if (editTitleBtn) editTitleBtn.style.display = '';
        if (infoNote) infoNote.style.display = '';
        showError('İmsakiye içeriği bulunamadı.');
        return;
    }
    
    // Mobil cihaz tespiti (sadece log için, mantıkta kullanmıyoruz)
    const isMobile = window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    console.log('Cihaz tespiti (PDF her zaman masaüstü düzeninde üretilecek):', { isMobile, windowWidth: window.innerWidth, userAgent: navigator.userAgent });
    
    // Mobil cihazlarda masaüstü görünümü için container genişliğini sabitle
    const mainContainer = document.querySelector('.container');
    const originalContainerWidth = mainContainer ? mainContainer.style.width : '';
    const originalContainerMaxWidth = mainContainer ? mainContainer.style.maxWidth : '';
    const originalContainerStyle = container ? container.style.width : '';
    const originalContainerOverflow = container ? container.style.overflow : '';
    const originalContainerOverflowY = container ? container.style.overflowY : '';
    const originalBodyOverflow = document.body.style.overflow;
    const originalHtmlOverflow = document.documentElement.style.overflow;
    
    // Viewport ayarlarını sakla (mobil için)
    const viewport = document.querySelector('meta[name="viewport"]');
    const originalViewport = viewport ? viewport.getAttribute('content') : '';
    
    // Masaüstü genişliğini kullan (1400px) - Mobil ve masaüstü için aynı, tablo genişliği ile uyumlu
    const desktopWidth = '1400px';
    
    // Mobil cihazlarda viewport'u genişlet
    if (isMobile && viewport) {
        viewport.setAttribute('content', 'width=1400, initial-scale=0.5, maximum-scale=1.0, user-scalable=no');
        // Body ve HTML overflow'u kaldır
        document.body.style.overflow = 'visible';
        document.documentElement.style.overflow = 'visible';
    }
    
    // PDF sırasında masaüstü görünümü zorlamak için body'ye özel class ekle
    document.body.classList.add('pdf-mode');

    if (mainContainer) {
        mainContainer.style.width = desktopWidth;
        mainContainer.style.maxWidth = desktopWidth;
    }
    if (container) {
        container.style.width = desktopWidth;
        container.style.overflow = 'visible';
        container.style.overflowY = 'visible';
    }
    
    // PDF için üst boşluk ekle
    const header = container.querySelector('.imsakiye-header');
    const originalMarginTop = header ? header.style.marginTop : '';
    if (header) {
        header.style.marginTop = '450px';
    }
    
    // Container genişliklerini geri almak için helper fonksiyon
    const restoreContainerWidths = () => {
        if (mainContainer) {
            mainContainer.style.width = originalContainerWidth;
            mainContainer.style.maxWidth = originalContainerMaxWidth;
        }
        if (container) {
            container.style.width = originalContainerStyle;
            container.style.overflow = originalContainerOverflow;
            container.style.overflowY = originalContainerOverflowY;
        }
        if (header) {
            header.style.marginTop = originalMarginTop;
        }
        
        // Mobil cihazlarda viewport'u geri al
        if (isMobile && viewport && originalViewport) {
            viewport.setAttribute('content', originalViewport);
            document.body.style.overflow = originalBodyOverflow;
            document.documentElement.style.overflow = originalHtmlOverflow;
        }
        document.body.classList.remove('pdf-mode');
    };
    
    // Browser'ın reflow yapması için gecikme
    setTimeout(async () => {
        try {
            // Arka plan resmini yükle - seçilen temaya göre
            const themeFileName = selectedTheme === 'tema2' ? 'tema2.png' : 
                                 selectedTheme === 'tema3' ? 'tema3.png' : 
                                 selectedTheme === 'tema4' ? 'tema4.png' : 
                                 selectedTheme === 'tema5' ? 'tema5.png' : 
                                 selectedTheme === 'tema6' ? 'tema6.png' : 'tema1.png';
            
            // Mutlak URL oluştur
            const currentPath = window.location.pathname;
            const basePath = currentPath.substring(0, currentPath.lastIndexOf('/'));
            const themeUrl = window.location.origin + basePath + '/' + themeFileName;
            
            console.log('Arka plan resmi yükleniyor:', themeUrl);
            
            // Arka plan resmini yükle
            const bgImage = await loadImage(themeUrl);
            console.log('✓ Arka plan resmi başarıyla yüklendi:', themeUrl);
            
            // html2canvas ile HTML'i resme çevir
            // PDF çıktısının cihazdan bağımsız, masaüstü ile aynı olması için
            // scale değerini HER ZAMAN 2 kullanıyoruz.
            const canvasScale = 2;
            console.log('html2canvas ayarları (masaüstü sabit):', { isMobile, scale: canvasScale });
            
            const html2canvasOpt = {
                scale: canvasScale,
                useCORS: true,
                backgroundColor: null,
                logging: false,
                allowTaint: true,
                scrollX: 0,
                scrollY: 0,
                width: 1400,
                windowWidth: 1400,
                windowHeight: container.scrollHeight,
                removeContainer: true, // Hız için
                imageTimeout: 0,
                onclone: function(clonedDoc) {
                    const clonedBody = clonedDoc.body;
                    if (clonedBody) {
                        clonedBody.classList.remove('theme-1', 'theme-2', 'theme-3', 'theme-4', 'theme-5', 'theme-6');
                        if (selectedTheme === 'tema2') {
                            clonedBody.classList.add('theme-2');
                        } else if (selectedTheme === 'tema3') {
                            clonedBody.classList.add('theme-3');
                        } else if (selectedTheme === 'tema4') {
                            clonedBody.classList.add('theme-4');
                        } else if (selectedTheme === 'tema5') {
                            clonedBody.classList.add('theme-5');
                        } else if (selectedTheme === 'tema6') {
                            clonedBody.classList.add('theme-6');
                        } else {
                            clonedBody.classList.add('theme-1');
                        }
                    }
                    
                    // Klonlanmış dokümanda ek bir mobil ayarı yapmıyoruz,
                    // PDF her zaman masaüstü düzeninde olsun.
                }
        };
        
        // HTML'i canvas'a çevir
            console.log('html2canvas başlatılıyor...', { isMobile, scale: canvasScale });
            html2canvas(container, html2canvasOpt).then((canvas) => {
                console.log('✓ Canvas oluşturuldu:', canvas.width, 'x', canvas.height, `(scale: ${canvasScale})`);
                // PNG kalitesi - mobil için biraz düşür (dosya boyutu için)
                const pngQuality = isMobile ? 0.95 : 1.0;
                const imgData = canvas.toDataURL('image/png', pngQuality);
        const canvasWidth = canvas.width;
        const canvasHeight = canvas.height;
        
                console.log('Canvas boyutları:', { width: canvasWidth, height: canvasHeight, quality: pngQuality });
        
                // jsPDF ile PDF oluştur ve arka plan ekle
                // restoreCallback'i geç ki hata durumunda da çağrılsın
                createPDFWithBackgroundImage(imgData, canvasWidth, canvasHeight, bgImage, restoreContainerWidths, canvasScale);
            }).catch((error) => {
                console.error('HTML2Canvas hatası:', error);
                restoreContainerWidths();
            const loadingModal = document.getElementById('loading-modal');
            if (loadingModal) loadingModal.style.display = 'none';
            if (pdfButton) pdfButton.style.display = '';
            if (actionButtons) actionButtons.style.display = '';
            if (editTitleBtn) editTitleBtn.style.display = '';
            if (infoNote) infoNote.style.display = '';
                isGeneratingPDF = false; // Hata durumunda flag'i sıfırla
                showError('PDF oluşturulurken bir hata oluştu: ' + error.message);
            });
            
        } catch (error) {
            console.error('PDF oluşturma hatası:', error);
            isGeneratingPDF = false; // Hata durumunda flag'i sıfırla
            
            // Hata durumunda arka plan olmadan dene
            try {
                const opt = {
                    margin: 0,
                    filename: `imsakiye-${currentData.city}-${currentData.state}-2026.pdf`,
                    image: { type: 'png', quality: 0.98 },
                    html2canvas: { 
                        scale: 2,
                        useCORS: true,
                        backgroundColor: null,
                        logging: false,
                        onclone: function(clonedDoc) {
                            const clonedBody = clonedDoc.body;
                            if (clonedBody) {
                                clonedBody.classList.remove('theme-1', 'theme-2', 'theme-3', 'theme-4', 'theme-5', 'theme-6');
                                if (selectedTheme === 'tema2') {
                                    clonedBody.classList.add('theme-2');
                                } else if (selectedTheme === 'tema3') {
                                    clonedBody.classList.add('theme-3');
                                } else if (selectedTheme === 'tema4') {
                                    clonedBody.classList.add('theme-4');
                                } else if (selectedTheme === 'tema5') {
                                    clonedBody.classList.add('theme-5');
                                } else if (selectedTheme === 'tema6') {
                                    clonedBody.classList.add('theme-6');
                                } else {
                                    clonedBody.classList.add('theme-1');
                                }
                            }
                        }
                    },
                    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                };
                
                await html2pdf().set(opt).from(container).save();
                console.log('PDF başarıyla oluşturuldu (arka plan olmadan)');
            } catch (fallbackError) {
                console.error('Fallback PDF oluşturma hatası:', fallbackError);
                showError('PDF oluşturulurken bir hata oluştu: ' + fallbackError.message);
                isGeneratingPDF = false; // Fallback hata durumunda flag'i sıfırla
            }
            
            // Tüm stilleri geri al
            restoreContainerWidths();
            const loadingModal = document.getElementById('loading-modal');
            if (loadingModal) loadingModal.style.display = 'none';
                if (pdfButton) pdfButton.style.display = '';
                if (actionButtons) actionButtons.style.display = '';
                if (editTitleBtn) editTitleBtn.style.display = '';
                if (infoNote) infoNote.style.display = '';
            isGeneratingPDF = false; // Her durumda flag'i sıfırla
            }
    }, 300);
}

// Resim yükleme helper fonksiyonu
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Resim yüklenemedi: ${src}`));
        img.src = src;
    });
}

// HTML2Canvas ile oluşturulan resmi PDF'e ekle (arka plan ile)
function createPDFWithBackgroundImage(htmlImageData, canvasWidth, canvasHeight, bgImage, restoreCallback, canvasScale = 2) {
    const loadingDiv = document.getElementById('loading');
    const pdfButton = document.getElementById('print-pdf-btn');
    const actionButtons = document.querySelector('.action-buttons');
    const editTitleBtn = document.querySelector('.edit-title-btn');
    const infoNote = document.querySelector('.info-note');
    
    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4',
            compress: false // Sıkıştırmayı kapat - daha yüksek kalite için
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        
        // Arka plan resmini hazırla (yüksek kalite)
        let bgData = null;
        if (bgImage) {
            try {
                const bgCanvas = document.createElement('canvas');
                bgCanvas.width = bgImage.width;
                bgCanvas.height = bgImage.height;
                const bgCtx = bgCanvas.getContext('2d');
                // Yüksek kaliteli rendering için image smoothing ayarları
                bgCtx.imageSmoothingEnabled = true;
                bgCtx.imageSmoothingQuality = 'high';
                bgCtx.drawImage(bgImage, 0, 0);
                // PNG kalitesi maksimum
                bgData = bgCanvas.toDataURL('image/png', 1.0);
            } catch (e) {
                console.warn('Arka plan eklenirken hata:', e);
            }
        }
        
        // HTML resminin boyutlarını hesapla (piksel'den mm'ye çevir)
        // html2canvas scale değeri parametre olarak geliyor (mobil: 1.5, masaüstü: 2)
        // 1 inch = 25.4mm, scale için efektif DPI = 96 * scale
        // PDF'e eklerken scale'i dikkate alarak normalize ediyoruz
        const baseDPI = 96; // Tarayıcının varsayılan DPI'si
        const effectiveDPI = baseDPI * canvasScale; // Scale'e göre DPI
        const pixelsToMm = 25.4 / effectiveDPI; // Scale'i dikkate alarak mm'ye çevir
        const imgWidthMm = (canvasWidth * pixelsToMm);
        const imgHeightMm = (canvasHeight * pixelsToMm);
        
        console.log('Boyut hesaplamaları:', {
            canvasScale,
            effectiveDPI,
            pixelsToMm: pixelsToMm.toFixed(4),
            imgWidthMm: imgWidthMm.toFixed(2),
            imgHeightMm: imgHeightMm.toFixed(2)
        });
        
        // PDF sayfasına sığdır - daha büyük ve ortalanmış
        const margin = 5; // Küçük margin
        const availableWidth = pageWidth - (2 * margin);
        const availableHeight = pageHeight - (2 * margin);
        
        // HTML resmini ekle - tam ortalanmış, üstte boşluk için Y pozisyonunu artır
        let topMargin = 70; // PDF'de üst boşluk (mm cinsinden) - tabloyu aşağı almak için artırıldı
        let position = margin + topMargin;
        
        // Aspect ratio'yu koru - tabloyu orantılı küçült
        // Önce maksimum boyutu hesapla (tek sayfaya sığacak şekilde)
        const maxAllowedHeight = pageHeight - topMargin - margin * 2;
        const maxAllowedWidth = availableWidth;
        
        const scaleX = maxAllowedWidth / imgWidthMm;
        const scaleY = maxAllowedHeight / imgHeightMm;
        const pdfScale = Math.min(scaleX, scaleY); // Tek sayfaya sığdır (1.08 kaldırıldı)
        
        const finalWidth = imgWidthMm * pdfScale;
        const finalHeight = imgHeightMm * pdfScale;
        
        // Tam ortalamak için X pozisyonunu hesapla
        const xPos = (pageWidth - finalWidth) / 2;
        
        console.log('Resim boyutları:', {
            canvas: `${canvasWidth}x${canvasHeight}`,
            mm: `${imgWidthMm.toFixed(2)}x${imgHeightMm.toFixed(2)}`,
            final: `${finalWidth.toFixed(2)}x${finalHeight.toFixed(2)}`,
            pdfScale: pdfScale.toFixed(2),
            xPos: xPos.toFixed(2)
        });
        
        // Her sayfaya arka plan ekle (hız için 'FAST' kullan)
        if (bgData) {
            // İlk sayfaya arka plan ekle
            doc.addImage(bgData, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST');
            
            // Eğer içerik birden fazla sayfaya sığarsa, diğer sayfalara da arka plan ekle
            const totalHeight = finalHeight + position;
            if (totalHeight > pageHeight) {
                const totalPages = Math.ceil(totalHeight / pageHeight);
                for (let i = 2; i <= totalPages; i++) {
            doc.addPage();
                doc.addImage(bgData, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST');
                }
            }
            }
            
        // İçeriği ekle - tek sayfaya sığacak şekilde (hız için 'FAST' kullan)
            doc.addImage(htmlImageData, 'PNG', xPos, position, finalWidth, finalHeight, undefined, 'FAST');
        
        // PDF'i kaydet
        const fileName = `imsakiye-${currentData.city}-${currentData.state}-2026.pdf`;
        console.log('PDF kaydediliyor:', fileName);
        
        try {
        doc.save(fileName);
            console.log('✓ PDF başarıyla kaydedildi:', fileName);
        } catch (saveError) {
            console.error('PDF kaydetme hatası:', saveError);
            // Alternatif: Blob olarak indir
            try {
                const pdfBlob = doc.output('blob');
                const url = URL.createObjectURL(pdfBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                console.log('✓ PDF blob olarak indirildi:', fileName);
            } catch (blobError) {
                console.error('PDF blob indirme hatası:', blobError);
                showError('PDF kaydedilemedi. Lütfen tarayıcı konsolunu kontrol edin.');
            }
        }
        
    } catch (error) {
        console.error('PDF oluşturma hatası:', error);
        showError('PDF oluşturulurken bir hata oluştu: ' + error.message);
    } finally {
        // Tüm stilleri geri al
        if (restoreCallback) {
            restoreCallback();
        }
        // Loading modal'ı gizle ve butonları geri göster
        const loadingModal = document.getElementById('loading-modal');
        if (loadingModal) loadingModal.style.display = 'none';
        if (pdfButton) {
            pdfButton.style.display = '';
            pdfButton.disabled = false;
            pdfButton.style.opacity = '1';
            pdfButton.style.cursor = 'pointer';
        }
        if (actionButtons) actionButtons.style.display = '';
        if (editTitleBtn) editTitleBtn.style.display = '';
        if (infoNote) infoNote.style.display = '';
        // PDF oluşturma flag'ini sıfırla
        isGeneratingPDF = false;
    }
}

// Manuel PDF Çizimi ve Arka Plan Yerleşimi (Yedek yöntem)
function createPDFWithBackground(bgImageData) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 18; // Kenarlardan içe doğru pay
    const contentWidth = pageWidth - (2 * margin);

    // 1. Arka Planı Çiz
    if (bgImageData) {
        doc.addImage(bgImageData, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST');
    }

    // 2. Başlık Alanı (Tablonun üzerine binmemesi için yPos 35-40 civarı)
    let yPos = 38;
    doc.setFontSize(22);
    doc.setTextColor(44, 62, 80);
    addText(doc, 'RAMAZAN İMSAKİYESİ', pageWidth / 2, yPos, { align: 'center' });
    
    yPos += 10;
    doc.setFontSize(14);
    addText(doc, `${currentData.city} / ${currentData.country}`, pageWidth / 2, yPos, { align: 'center' });
    
    yPos += 7;
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);
    addText(doc, 'Hicri 1447 - Miladi 2026', pageWidth / 2, yPos, { align: 'center' });

    // 3. Tablo Ayarları
    yPos += 20; 
    const colWidths = [24, 44, 15, 15, 15, 15, 15, 15]; // Toplam 158mm - sütunlar genişletildi
    const headers = ['Hicri', 'Miladi Tarih', 'İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı'];

    // Tablo başlık arka planı (okunabilirlik için)
    let xPos = (pageWidth - colWidths.reduce((a, b) => a + b, 0)) / 2; // Tabloyu yatayda tam ortala
    const tableStartX = xPos;
    
    // Tablo Başlık Rengi - Her zaman görünür olmalı
    doc.setFillColor(102, 126, 234);
    doc.setTextColor(255, 255, 255);
    doc.setFont(undefined, 'bold');
    doc.setFontSize(8);

    headers.forEach((header, i) => {
        // Mavi arka plan ile başlık hücresi
        doc.rect(xPos, yPos, colWidths[i], 8, 'F');
        // Metni ekle
        addText(doc, header, xPos + colWidths[i] / 2, yPos + 5.5, { align: 'center' });
        xPos += colWidths[i];
    });

    yPos += 8;

    // 4. Veri Satırları
    currentData.data.forEach((row, index) => {
        if (yPos > pageHeight - 25) {
            doc.addPage();
            if (bgImageData) doc.addImage(bgImageData, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST');
            yPos = 30;
            
            // Yeni sayfada tablo başlıklarını tekrar çiz
            doc.setFillColor(102, 126, 234);
            doc.setTextColor(255, 255, 255);
            doc.setFont(undefined, 'bold');
            doc.setFontSize(8);
            
            xPos = tableStartX;
            headers.forEach((header, i) => {
                // Mavi arka plan ile başlık hücresi
                doc.rect(xPos, yPos, colWidths[i], 8, 'F');
                // Metni ekle
                addText(doc, header, xPos + colWidths[i] / 2, yPos + 5.5, { align: 'center' });
                xPos += colWidths[i];
            });
            
            yPos += 8;
            doc.setTextColor(0, 0, 0);
            doc.setFont(undefined, 'normal');
        }

        xPos = tableStartX;
        const rowData = [row.hicri, row.miladi, row.imsak, row.gunes, row.ogle, row.ikindi, row.aksam, row.yatsi];
        const rowHeight = 6.2;

        // Satır Arka Planı (Okunabilirlik için yarı saydam beyaz)
        doc.setFillColor(255, 255, 255);
        doc.setGState(doc.GState({opacity: 0.8}));
        doc.rect(tableStartX, yPos, colWidths.reduce((a, b) => a + b, 0), rowHeight, 'F');
        doc.setGState(doc.GState({opacity: 1.0}));

        // Varsayılan font boyutu
        doc.setFontSize(7);

        rowData.forEach((cell, i) => {
            // İmsak sütunu için kırmızı arka plan
            if (i === 2) {
                doc.setFillColor(220, 53, 69); // Kırmızı arka plan
                doc.setGState(doc.GState({opacity: 1.0}));
                doc.rect(xPos, yPos, colWidths[i], rowHeight, 'F');
                doc.setFont(undefined, 'bold');
                doc.setTextColor(255, 255, 255); // Beyaz metin
                doc.setFontSize(8); /* Bir karakter büyük */
            } else {
                // Diğer hücreler için normal arka plan (zaten satır arka planı var)
                doc.setFont(undefined, 'normal');
                doc.setTextColor(0, 0, 0);
                // 2. sütun (Miladi Tarih) için biraz küçük font
                if (i === 1) {
                    doc.setFontSize(7.5); /* Bir karakter büyük */
                } else {
                    doc.setFontSize(8); /* Bir karakter büyük */
                }
            }
            
            // Hücre çerçevesi
            doc.setDrawColor(200, 200, 200);
            doc.rect(xPos, yPos, colWidths[i], rowHeight, 'S');

            // Akşam sütunu için kırmızı metin (arka plan yok)
            if (i === 6) {
                doc.setFont(undefined, 'bold');
                doc.setTextColor(190, 0, 0);
            }

            let text = String(cell);
            // 2. sütun (Miladi Tarih) için Türkçe karakterleri koru - kısaltma yapma
            // Tüm Türkçe karakterler korunmalı: Şubat, Perşembe, Çarşamba, vb.

            addText(doc, text, xPos + colWidths[i] / 2, yPos + 4.2, { align: 'center' });
            xPos += colWidths[i];
        });
        yPos += rowHeight;
    });

    // 5. Kaydet ve Kapat
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) loadingDiv.style.display = 'none';
    doc.save(`imsakiye-2026-${currentData.city}.pdf`);
}

// Türkçe Karakter Destekli Metin Ekleme
function addText(doc, text, x, y, options = {}) {
    if (!text) return;
    
    // Türkçe karakterleri koruyarak metni ekle
    try {
        // jsPDF UTF-8 desteği ile direkt ekle
        const textStr = String(text);
        doc.text(textStr, x, y, options);
    } catch (e) {
        // Hata durumunda fallback - Türkçe karakterleri ASCII'ye çevir
        console.warn('Türkçe karakter hatası, fallback kullanılıyor:', e);
        const map = {
            'İ':'I', 'ı':'i', 'Ş':'S', 'ş':'s', 
            'Ğ':'G', 'ğ':'g', 'Ü':'U', 'ü':'u', 
            'Ö':'O', 'ö':'o', 'Ç':'C', 'ç':'c'
        };
        const fallback = text.replace(/[İıŞşĞğÜüÖöÇç]/g, m => map[m] || m);
        try {
            doc.text(fallback, x, y, options);
        } catch (e2) {
            console.error('Metin eklenemedi:', e2);
        }
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => errorDiv.style.display = 'none', 5000);
}