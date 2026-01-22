<?php
/**
 * Diyanet Namaz Vakitleri Scraper
 * https://namazvakitleri.diyanet.gov.tr/ adresinden veri çeker
 * Sadece Almanya - Niedersachsen ve Bremen eyaletleri için
 * Hicri 1 Ramazan - 29 Ramazan günlerini çeker
 */

// api.php'den çağrılabilir, bu yüzden require_once kontrolü yap
if (!function_exists('getDiyanetToken')) {
    // Eğer api.php'den çağrılmıyorsa, sadece komut satırından çalıştırılabilir
    if (php_sapi_name() !== 'cli' && !isset($_GET['run'])) {
        die('Bu script sadece komut satırından çalıştırılabilir veya api.php\'den çağrılmalıdır.');
    }
}

// Diyanet namaz vakitleri sitesinden imsakiye verilerini çek
// https://namazvakitleri.diyanet.gov.tr/ kullanıyoruz
function scrapeDiyanetImsakiye($cityName, $stateName) {
    $baseUrl = "https://namazvakitleri.diyanet.gov.tr/tr-TR";
    $cookieFile = sys_get_temp_dir() . '/diyanet_cookies_' . uniqid() . '.txt';
    
    error_log("=== WEB SCRAPING BAŞLATILDI ===");
    error_log("Şehir: {$cityName}, Eyalet: {$stateName}");
    
    // Ana sayfayı çek
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $baseUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_COOKIEJAR, $cookieFile);
    curl_setopt($ch, CURLOPT_COOKIEFILE, $cookieFile);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding: gzip, deflate, br',
        'Connection: keep-alive',
        'Upgrade-Insecure-Requests: 1'
    ]);
    
    $html = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode !== 200 || !$html) {
        error_log("✗ Ana sayfa yüklenemedi: HTTP $httpCode");
        @unlink($cookieFile);
        return null;
    }
    
    // DOMDocument ile parse et
    libxml_use_internal_errors(true);
    $dom = new DOMDocument();
    @$dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    $xpath = new DOMXPath($dom);
    
    // Ülke dropdown'ını bul (ALMANYA)
    $countrySelect = $xpath->query("//select[contains(@id, 'country') or contains(@name, 'country') or contains(@class, 'country')]")->item(0);
    if (!$countrySelect) {
        // Alternatif: tüm select'leri kontrol et
        $allSelects = $xpath->query("//select");
        foreach ($allSelects as $select) {
            $options = $select->getElementsByTagName('option');
            foreach ($options as $option) {
                $text = trim($option->textContent);
                if (stripos($text, 'ALMANYA') !== false || stripos($text, 'GERMANY') !== false) {
                    $countrySelect = $select;
                    break 2;
                }
            }
        }
    }
    
    if (!$countrySelect) {
        error_log("✗ Ülke dropdown bulunamadı");
        @unlink($cookieFile);
        return null;
    }
    
    // ALMANYA'yı seç
    $options = $countrySelect->getElementsByTagName('option');
    $countryValue = '';
    foreach ($options as $option) {
        $text = trim($option->textContent);
        if (stripos($text, 'ALMANYA') !== false || stripos($text, 'GERMANY') !== false) {
            $countryValue = $option->getAttribute('value') ?: $text;
            error_log("✓ Ülke bulundu: ALMANYA (value: $countryValue)");
            break;
        }
    }
    
    if (!$countryValue) {
        error_log("✗ ALMANYA bulunamadı");
        @unlink($cookieFile);
        return null;
    }
    
    // Ülke seçimi için form gönder (eğer JavaScript gerektiriyorsa, direkt URL'ye gidebiliriz)
    // Alternatif: URL parametreleri ile direkt şehir sayfasına git
    // https://namazvakitleri.diyanet.gov.tr/tr-TR/{country}/{state}/{city} formatı olabilir
    
    // Önce eyalet dropdown'ını bul (Niedersachsen veya Bremen)
    // Ülke seçildikten sonra eyaletler yüklenecek
    // JavaScript ile yükleniyorsa, direkt API endpoint'i kullanabiliriz
    
    // Alternatif yaklaşım: Aylık namaz vakitleri tablosunu direkt parse et
    // URL formatı: https://namazvakitleri.diyanet.gov.tr/tr-TR/{country}/{state}/{city}
    // veya form POST ile
    
    // Şimdilik basit yaklaşım: URL'yi oluştur ve direkt git
    $normalizedStateName = strtoupper(str_replace(['-', 'Ü', 'Ö', 'Ş', 'İ', 'Ç', 'Ğ', ' '], ['', 'U', 'O', 'S', 'I', 'C', 'G', '-'], $stateName));
    $normalizedCityName = strtoupper(str_replace(['Ü', 'Ö', 'Ş', 'İ', 'Ç', 'Ğ', ' '], ['U', 'O', 'S', 'I', 'C', 'G', '-'], $cityName));
    
    // URL formatını dene
    $possibleUrls = [
        $baseUrl . '/' . urlencode($normalizedStateName) . '/' . urlencode($normalizedCityName),
        $baseUrl . '?country=' . urlencode('ALMANYA') . '&state=' . urlencode($stateName) . '&city=' . urlencode($cityName),
        $baseUrl . '/ulkeler/' . urlencode('ALMANYA') . '/' . urlencode($stateName) . '/' . urlencode($cityName)
    ];
    
    $html = null;
    foreach ($possibleUrls as $url) {
        error_log("URL deneniyor: $url");
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_COOKIEJAR, $cookieFile);
        curl_setopt($ch, CURLOPT_COOKIEFILE, $cookieFile);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        
        $html = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200 && $html && stripos($html, $cityName) !== false) {
            error_log("✓ URL başarılı: $url");
            break;
        }
    }
    
    if (!$html || $httpCode !== 200) {
        error_log("✗ Şehir sayfası yüklenemedi: HTTP $httpCode");
        @unlink($cookieFile);
        return null;
    }
    
    // HTML'i parse et
    @$dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    $xpath = new DOMXPath($dom);
    
    $imsakiyeData = [];
    $bayramNamazi = null;
    
    // "Aylık Namaz Vakitleri" tablosunu bul
    // Tablo formatı: | Miladi Tarih | Hicri Tarih | İmsak | Güneş | Öğle | İkindi | Akşam | Yatsı |
    $tables = $xpath->query("//table");
    foreach ($tables as $table) {
        $tableText = $table->textContent;
        // Aylık veya Ramazan içeren tabloyu bul
        if (stripos($tableText, 'Ramazan') !== false || stripos($tableText, 'Aylık') !== false) {
            $rows = $xpath->query(".//tr", $table);
            foreach ($rows as $rowIndex => $row) {
                if ($rowIndex === 0) continue; // Başlık satırını atla
                
                $cells = $xpath->query(".//td | .//th", $row);
                if ($cells->length >= 7) {
                    // Hücre sırası: Miladi Tarih, Hicri Tarih, İmsak, Güneş, Öğle, İkindi, Akşam, Yatsı
                    $miladi = trim($cells->item(0)->textContent);
                    $hicri = trim($cells->item(1)->textContent);
                    $imsak = trim($cells->item(2)->textContent);
                    $gunes = trim($cells->item(3)->textContent);
                    $ogle = trim($cells->item(4)->textContent);
                    $ikindi = trim($cells->item(5)->textContent);
                    $aksam = trim($cells->item(6)->textContent);
                    $yatsi = $cells->length > 7 ? trim($cells->item(7)->textContent) : '';
                    
                    // Boş satırları ve başlık satırlarını atla
                    if ($hicri && $miladi && $imsak && 
                        stripos($hicri, 'hicri') === false &&
                        stripos($miladi, 'miladi') === false &&
                        stripos($imsak, 'imsak') === false &&
                        strpos($imsak, ':') !== false) {
                        
                        // Sadece Ramazan günlerini al (1-29 Ramazan)
                        if (preg_match('/(\d+)\s*Ramazan/i', $hicri, $matches)) {
                            $ramazanDay = (int)$matches[1];
                            if ($ramazanDay >= 1 && $ramazanDay <= 29) {
                                $imsakiyeData[] = [
                                    'hicri' => $hicri,
                                    'miladi' => $miladi,
                                    'imsak' => $imsak,
                                    'gunes' => $gunes,
                                    'ogle' => $ogle,
                                    'ikindi' => $ikindi,
                                    'aksam' => $aksam,
                                    'yatsi' => $yatsi
                                ];
                            }
                        }
                    }
                }
            }
            break; // İlk uygun tabloyu bulduk
        }
    }
    
    // Eğer tablo bulunamadıysa, tüm tabloları kontrol et
    if (count($imsakiyeData) === 0) {
        error_log("⚠ Aylık tablo bulunamadı, tüm tablolar kontrol ediliyor...");
        foreach ($tables as $table) {
            $rows = $xpath->query(".//tr", $table);
            foreach ($rows as $rowIndex => $row) {
                if ($rowIndex === 0) continue;
                
                $cells = $xpath->query(".//td | .//th", $row);
                if ($cells->length >= 7) {
                    $miladi = trim($cells->item(0)->textContent);
                    $hicri = trim($cells->item(1)->textContent);
                    $imsak = trim($cells->item(2)->textContent);
                    $gunes = trim($cells->item(3)->textContent);
                    $ogle = trim($cells->item(4)->textContent);
                    $ikindi = trim($cells->item(5)->textContent);
                    $aksam = trim($cells->item(6)->textContent);
                    $yatsi = $cells->length > 7 ? trim($cells->item(7)->textContent) : '';
                    
                    if ($hicri && $miladi && $imsak && strpos($imsak, ':') !== false) {
                        if (preg_match('/(\d+)\s*Ramazan/i', $hicri, $matches)) {
                            $ramazanDay = (int)$matches[1];
                            if ($ramazanDay >= 1 && $ramazanDay <= 29) {
                                $imsakiyeData[] = [
                                    'hicri' => $hicri,
                                    'miladi' => $miladi,
                                    'imsak' => $imsak,
                                    'gunes' => $gunes,
                                    'ogle' => $ogle,
                                    'ikindi' => $ikindi,
                                    'aksam' => $aksam,
                                    'yatsi' => $yatsi
                                ];
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Bayram namazı vaktini bul
    $pageText = $dom->textContent;
    if (preg_match('/Bayram\s+Namazı\s*:?\s*(\d{1,2}:\d{2})/i', $pageText, $matches)) {
        $bayramNamazi = $matches[1];
    }
    
    @unlink($cookieFile);
    
    // Sadece 1-29 Ramazan günlerini döndür
    if (count($imsakiyeData) >= 25) {
        error_log("✓ Web scraping başarılı: " . count($imsakiyeData) . " gün veri çekildi");
        return ['imsakiye' => $imsakiyeData, 'bayram' => $bayramNamazi];
    }
    
    error_log("✗ Web scraping başarısız: Sadece " . count($imsakiyeData) . " gün veri çekildi (en az 25 gün gerekli)");
    return null;
}

// Test için
if (php_sapi_name() === 'cli') {
    echo "Diyanet Scraper Test\n";
    echo "===================\n\n";
    
    // Test: Hannover, Niedersachsen
    echo "Test: Hannover, Niedersachsen\n";
    $result = scrapeDiyanetImsakiye('Hannover', 'Niedersachsen');
    if ($result) {
        echo "✓ Başarılı! " . count($result['imsakiye']) . " gün veri çekildi.\n";
        if ($result['bayram']) {
            echo "Bayram namazı: " . $result['bayram'] . "\n";
        }
        echo "\nİlk 3 gün:\n";
        foreach (array_slice($result['imsakiye'], 0, 3) as $day) {
            echo "  " . $day['hicri'] . " - " . $day['miladi'] . " - İmsak: " . $day['imsak'] . "\n";
        }
    } else {
        echo "✗ Veri çekilemedi.\n";
    }
}
?>
