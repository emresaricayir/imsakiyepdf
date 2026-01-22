<?php
/**
 * İmsakiye API - PHP Backend
 * Paylaşımlı hosting için SQLite kullanır
 * Diyanet Awqat Salah API entegrasyonu
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Diyanet API bilgileri (ŞU ANDA KULLANILMIYOR - Sadece test endpoint'leri için)
// define('DIYANET_API_BASE', 'https://awqatsalah.diyanet.gov.tr');
// define('DIYANET_USERNAME', 'mailim');
// define('DIYANET_PASSWORD', '5R%g+6cY');
// define('DIYANET_TOKEN_FILE', __DIR__ . '/.diyanet_token');

// Diyanet API Token yönetimi (ŞU ANDA KULLANILMIYOR - Sadece test endpoint'leri için)
/*
function getDiyanetToken() {
    // Token dosyasını kontrol et
    if (file_exists(DIYANET_TOKEN_FILE)) {
        $tokenData = json_decode(file_get_contents(DIYANET_TOKEN_FILE), true);
        // Token'ın geçerliliğini kontrol et (1 saat)
        if ($tokenData && isset($tokenData['expires_at']) && $tokenData['expires_at'] > time()) {
            return $tokenData['token'];
        }
    }
    
    // Yeni token al
    $loginData = [
        'email' => DIYANET_USERNAME, // API email bekliyor
        'password' => DIYANET_PASSWORD
    ];
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, DIYANET_API_BASE . '/Auth/Login');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($loginData));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Accept: application/json'
    ]);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    
    $response = curl_exec($ch);
    $curlError = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlInfo = curl_getinfo($ch);
    curl_close($ch);
    
    if ($curlError) {
        error_log('Diyanet API Login CURL hatası: ' . $curlError);
        return null;
    }
    
    // Response'u logla
    error_log('Diyanet API Login Response: HTTP ' . $httpCode . ' - ' . substr($response, 0, 500));
    
    if ($httpCode !== 200) {
        error_log('Diyanet API Login hatası: HTTP ' . $httpCode . ' - Response: ' . substr($response, 0, 500));
        return null;
    }
    
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log('Diyanet API Login JSON decode hatası: ' . json_last_error_msg() . ' - Response: ' . substr($response, 0, 200));
        return null;
    }
    
    // Token'ı kontrol et - Diyanet API data.accessToken kullanıyor
    $token = null;
    if (isset($data['data']['accessToken'])) {
        $token = $data['data']['accessToken'];
    } elseif (isset($data['accessToken'])) {
        $token = $data['accessToken'];
    } elseif (isset($data['token'])) {
        $token = $data['token'];
    } elseif (isset($data['access_token'])) {
        $token = $data['access_token'];
    } elseif (isset($data['data']['token'])) {
        $token = $data['data']['token'];
    }
    
    if (!$token) {
        error_log('Diyanet API Token alınamadı. Response yapısı: ' . json_encode($data));
        return null;
    }
    
    // Token'ı dosyaya kaydet (1 saat geçerli)
    $tokenData = [
        'token' => $token,
        'expires_at' => time() + 3600 // 1 saat
    ];
    file_put_contents(DIYANET_TOKEN_FILE, json_encode($tokenData));
    
    return $token;
}
*/

// Diyanet API çağrısı (ŞU ANDA KULLANILMIYOR - Sadece test endpoint'leri için)
/*
function callDiyanetAPI($endpoint, $method = 'GET', $data = null) {
    $token = getDiyanetToken();
    if (!$token) {
        error_log("✗ callDiyanetAPI: Token alınamadı ($endpoint)");
        return null;
    }
    
    $ch = curl_init();
    $url = DIYANET_API_BASE . $endpoint;
    
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Accept: application/json',
        'Authorization: Bearer ' . $token
    ]);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    
    if ($method === 'POST' && $data) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }
    
    $response = curl_exec($ch);
    $curlError = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($curlError) {
        error_log("✗ Diyanet API CURL hatası ($endpoint): " . $curlError);
        return null;
    }
    
    if ($httpCode !== 200) {
        $errorMsg = "Diyanet API hatası ($endpoint): HTTP $httpCode";
        $responseData = null;
        if ($response) {
            $errorMsg .= " - " . substr($response, 0, 200);
            // Response'u decode et ve mesajı çıkar
            $responseData = json_decode($response, true);
            if ($responseData && isset($responseData['message'])) {
                $errorMsg .= " | Mesaj: " . $responseData['message'];
            }
        }
        error_log("✗ " . $errorMsg);
        
        // 406 (Not Acceptable) hatası - Kota aşıldı
        if ($httpCode === 406) {
            error_log("⚠⚠⚠ DİKKAT: Diyanet API kota limiti aşıldı! ($endpoint)");
            if ($responseData && isset($responseData['message'])) {
                error_log("API Mesajı: " . $responseData['message']);
            }
        }
        
        return null;
    }
    
    $decoded = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log("✗ Diyanet API JSON decode hatası ($endpoint): " . json_last_error_msg() . " - Response: " . substr($response, 0, 200));
        return null;
    }
    
    // Diyanet API response formatı: { "data": [...], "success": true, "message": null }
    // Eğer success false ise hata var demektir
    if (isset($decoded['success']) && $decoded['success'] === false) {
        $errorMsg = isset($decoded['message']) ? $decoded['message'] : 'Bilinmeyen hata';
        error_log("✗ Diyanet API hatası ($endpoint): " . $errorMsg);
        return null;
    }
    
    // data içindeki veriyi döndür
    if (isset($decoded['data'])) {
        error_log("✓ callDiyanetAPI başarılı ($endpoint): " . count($decoded['data']) . " kayıt");
        return $decoded['data'];
    }
    
    // Eğer data yoksa direkt decoded'i döndür
    error_log("✓ callDiyanetAPI başarılı ($endpoint): data yok, direkt decoded döndürülüyor");
    return $decoded;
}
*/

// OPTIONS isteği için
if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Veritabanı yolu - Ana veritabanı
$db_path = __DIR__ . '/imsakiye.db';
// $cache_db_path = __DIR__ . '/imsakiye_cache.db'; // ŞU ANDA KULLANILMIYOR (Sadece test endpoint'leri için)

// Ana veritabanı bağlantısı
function getDB() {
    global $db_path;
    try {
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        return $db;
    } catch (PDOException $e) {
        error_log('DB hatası: ' . $e->getMessage());
        return null;
    }
}

// Veritabanı bağlantısı (Cache için) - ŞU ANDA KULLANILMIYOR (Sadece test endpoint'leri için)
/*
function getCacheDB() {
    global $cache_db_path;
try {
    $db = new PDO('sqlite:' . $cache_db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        
        // Cache tablosunu oluştur
        $db->exec("CREATE TABLE IF NOT EXISTS prayer_times_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER NOT NULL,
            city_name TEXT NOT NULL,
            state_id INTEGER NOT NULL,
            country_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            eid_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            UNIQUE(city_id, state_id, country_id)
        )");
        
        return $db;
} catch (PDOException $e) {
        error_log('Cache DB hatası: ' . $e->getMessage());
        return null;
    }
}
*/

// URL'den endpoint'i al
$path = '';

// Önce query string'den path'i al (RewriteRule'dan gelen veya manuel çağrı)
if (isset($_GET['path'])) {
    $path = $_GET['path'];
} elseif (isset($_SERVER['REQUEST_URI'])) {
    // REQUEST_URI'den path'i çıkar
    $request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    
    // /imsakiye/api/... formatını handle et
    if (preg_match('#/api/(.+)$#', $request_uri, $matches)) {
        $path = $matches[1];
    }
    // /api/... formatını handle et (root'tan)
    elseif (preg_match('#^/api/(.+)$#', $request_uri, $matches)) {
        $path = $matches[1];
    }
}

$path = trim($path, '/');

// Debug: Path'i logla
error_log("API Path alındı: " . $path);
error_log("GET path: " . (isset($_GET['path']) ? $_GET['path'] : 'yok'));
error_log("REQUEST_URI: " . (isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : 'yok'));

// Route'ları ayır
$segments = !empty($path) ? explode('/', $path) : [];
error_log("Segments: " . json_encode($segments));

// Input validation helper
function validateInput($input, $maxLength = 100) {
    $input = trim($input);
    if (empty($input) || strlen($input) > $maxLength) {
        return false;
    }
    // Sadece alfanumerik, boşluk, tire, alt çizgi, parantez ve slash karakterlerine izin ver
    return preg_match('/^[a-zA-Z0-9\s\-_üÜöÖçÇşŞğĞıİ()\/]+$/u', $input);
}

// Endpoint routing
$request_method = isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'GET';

if ($request_method === 'GET') {
    try {
        // Health check
        if (empty($segments) || !isset($segments[0]) || $segments[0] === 'health' || $segments[0] === '') {
            // Basit health check - veritabanı bağlantısını kontrol et
            $db = getDB();
            if ($db) {
                echo json_encode(['status' => 'ok', 'database' => 'connected']);
            } else {
                echo json_encode(['status' => 'error', 'database' => 'connection_failed']);
            }
            exit;
        }
        
        // TEST ENDPOINT'LERİ - ŞU ANDA KULLANILMIYOR (Yorum satırına alındı)
        /*
        // Vakit test endpoint - Belirli bir şehir için vakitleri test et
        if (isset($segments[0]) && $segments[0] === 'test-vakit' && isset($segments[1]) && isset($segments[2]) && isset($segments[3])) {
            $countryCode = urldecode($segments[1]);
            $stateCode = urldecode($segments[2]);
            // Şehir ismi birden fazla segment olabilir (örn: BABENHAUSEN/BAVAIRA)
            // Tüm kalan segment'leri birleştir
            $cityName = urldecode(implode('/', array_slice($segments, 3)));
            
            try {
                // Almanya'nın ID'sini kullan
                $germanyId = $countryCode;
                $states = callDiyanetAPI('/api/Place/States/' . $germanyId);
                if (!$states || !is_array($states)) {
                    echo json_encode(['error' => 'Eyaletler alınamadı']);
                    exit;
                }
                
                // Eyalet ID'sini bul
                $stateId = null;
                if (is_numeric($stateCode)) {
                    foreach ($states as $state) {
                        if ((string)$state['id'] === (string)$stateCode) {
                            $stateId = $state['id'];
                            break;
                        }
                    }
                }
                
                if (!$stateId) {
                    echo json_encode(['error' => 'Eyalet bulunamadı']);
                    exit;
                }
                
                // Şehirleri al
                $cities = callDiyanetAPI('/api/Place/Cities/' . $stateId);
                if (!$cities || !is_array($cities)) {
                    echo json_encode(['error' => 'Şehirler alınamadı']);
                    exit;
                }
                
                // Şehir ID'sini bul
                $cityId = null;
                $cityNameUpper = strtoupper(trim($cityName));
                foreach ($cities as $city) {
                    $apiCityName = strtoupper(trim($city['name'] ?? ''));
                    if ($apiCityName === $cityNameUpper) {
                        $cityId = $city['id'];
                        break;
                    }
                }
                
                if (!$cityId) {
                    echo json_encode(['error' => 'Şehir bulunamadı: ' . $cityName]);
                    exit;
                }
                
                // Cache'den kontrol et
                $db = getCacheDB();
                $fromCache = false;
                $cachedData = null;
                
                if ($db) {
                    try {
                        $stmt = $db->prepare("SELECT data, eid_data, created_at, expires_at FROM prayer_times_cache 
                                               WHERE city_id = ? AND state_id = ? AND country_id = ? 
                                               AND expires_at > datetime('now')");
                        $stmt->execute([$cityId, $stateId, $germanyId]);
                        $cache = $stmt->fetch();
                        
                        if ($cache) {
                            $fromCache = true;
                            $cachedData = json_decode($cache['data'], true);
                        }
                    } catch (PDOException $e) {
                        error_log('Cache okuma hatası: ' . $e->getMessage());
                    }
                }
                
                // API'den al
                if (!$cachedData) {
                    $ramadanData = callDiyanetAPI('/api/PrayerTime/Ramadan/' . $cityId);
                    $eidData = callDiyanetAPI('/api/PrayerTime/Eid/' . $cityId);
                } else {
                    $ramadanData = $cachedData;
                    $eidData = json_decode($cache['eid_data'], true);
                }
                
                // Bugünün tarihini bul
                $today = new DateTime();
                $todayStr = $today->format('Y-m-d');
                
                // Bugünün vakitlerini bul
                $todayPrayer = null;
                foreach ($ramadanData as $day) {
                    if (isset($day['gregorianDateShortIso8601'])) {
                        $dayDate = new DateTime($day['gregorianDateShortIso8601']);
                        if ($dayDate->format('Y-m-d') === $todayStr) {
                            $todayPrayer = $day;
                            break;
                        }
                    }
                }
                
                // Test sonuçları
                $testResult = [
                    'city_name' => $cityName,
                    'city_id' => $cityId,
                    'state_id' => $stateId,
                    'country_id' => $germanyId,
                    'from_cache' => $fromCache,
                    'cache_created' => $fromCache ? $cache['created_at'] : null,
                    'cache_expires' => $fromCache ? $cache['expires_at'] : null,
                    'total_days' => count($ramadanData),
                    'first_day' => $ramadanData[0] ?? null,
                    'last_day' => $ramadanData[count($ramadanData) - 1] ?? null,
                    'today_date' => $todayStr,
                    'today_prayer' => $todayPrayer,
                    'eid_prayer' => $eidData ?? null,
                    'field_mapping' => [
                        'fajr' => 'imsak',
                        'sunrise' => 'gunes',
                        'dhuhr' => 'ogle',
                        'asr' => 'ikindi',
                        'maghrib' => 'aksam',
                        'isha' => 'yatsi'
                    ],
                    'sample_days' => array_slice($ramadanData, 0, 3) // İlk 3 gün
                ];
                
                echo json_encode($testResult, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
                exit;
                
            } catch (Exception $e) {
                echo json_encode(['error' => $e->getMessage()]);
                exit;
            }
        }
        */
        
        // TEST ENDPOINT'LERİ - ŞU ANDA KULLANILMIYOR (Yorum satırına alındı)
        /*
        // Test endpoint - API'de veri var mı kontrol et
        if (isset($segments[0]) && $segments[0] === 'test') {
            $testResults = [
                'timestamp' => date('Y-m-d H:i:s'),
                'token_status' => 'unknown',
                'countries' => null,
                'germany_states' => null,
                'test_city' => null
            ];
            
            // Token kontrolü
            $token = getDiyanetToken();
            if ($token) {
                $testResults['token_status'] = 'ok';
                $testResults['token_length'] = strlen($token);
                
                // Ülkeleri test et
                try {
                    $countries = callDiyanetAPI('/api/Place/Countries');
                    if ($countries && is_array($countries)) {
                        $testResults['countries'] = [
                            'count' => count($countries),
                            'sample' => array_slice($countries, 0, 3) // İlk 3 ülke
                        ];
                        
                        // Almanya'yı bul
                        $germany = null;
                        foreach ($countries as $country) {
                            if (is_array($country)) {
                                $name = strtoupper($country['name'] ?? '');
                                if (strpos($name, 'ALMANYA') !== false || strpos($name, 'GERMANY') !== false) {
                                    $germany = $country;
                                    break;
                                }
                            }
                        }
                        
                        if ($germany) {
                            $testResults['germany_found'] = true;
                            $testResults['germany_id'] = $germany['id'] ?? null;
                            $testResults['germany_name'] = $germany['name'] ?? null;
                            
                            // Almanya eyaletlerini test et
                            if (isset($germany['id'])) {
                                $states = callDiyanetAPI('/api/Place/States/' . $germany['id']);
                                if ($states && is_array($states)) {
                                    $testResults['germany_states'] = [
                                        'count' => count($states),
                                        'sample' => array_slice($states, 0, 3) // İlk 3 eyalet
                                    ];
                                    
                                    // İlk eyaletin şehirlerini test et
                                    if (count($states) > 0 && isset($states[0]['id'])) {
                                        $cities = callDiyanetAPI('/api/Place/Cities/' . $states[0]['id']);
                                        if ($cities && is_array($cities)) {
                                            $testResults['test_city'] = [
                                                'state_name' => $states[0]['name'] ?? '',
                                                'cities_count' => count($cities),
                                                'sample_cities' => array_slice($cities, 0, 5) // İlk 5 şehir
                                            ];
                                            
                                            // İlk şehrin vakitlerini test et
                                            if (count($cities) > 0 && isset($cities[0]['id'])) {
                                                $cityId = $cities[0]['id'];
                                                $cityName = $cities[0]['name'] ?? '';
                                                
                                                // Ramazan vakitlerini test et
                                                $ramadanData = callDiyanetAPI('/api/PrayerTime/Ramadan/' . $cityId);
                                                if ($ramadanData && is_array($ramadanData) && count($ramadanData) > 0) {
                                                    $testResults['prayer_times'] = [
                                                        'city_name' => $cityName,
                                                        'city_id' => $cityId,
                                                        'ramadan_days_count' => count($ramadanData),
                                                        'first_day' => $ramadanData[0] ?? null,
                                                        'last_day' => $ramadanData[count($ramadanData) - 1] ?? null
                                                    ];
                                                } else {
                                                    $testResults['prayer_times'] = [
                                                        'city_name' => $cityName,
                                                        'city_id' => $cityId,
                                                        'error' => 'Ramazan vakitleri alınamadı',
                                                        'response' => $ramadanData
                                                    ];
                                                }
                                                
                                                // Bayram namazı vaktini test et
                                                $eidData = callDiyanetAPI('/api/PrayerTime/Eid/' . $cityId);
                                                if ($eidData && is_array($eidData)) {
                                                    $testResults['eid_prayer'] = [
                                                        'city_name' => $cityName,
                                                        'data' => $eidData
                                                    ];
                                                } else {
                                                    $testResults['eid_prayer'] = [
                                                        'city_name' => $cityName,
                                                        'error' => 'Bayram namazı vakti alınamadı',
                                                        'response' => $eidData
                                                    ];
                                                }
                                            }
                                        } else {
                                            $testResults['test_city'] = ['error' => 'Şehirler alınamadı'];
                                        }
                                    }
                                } else {
                                    $testResults['germany_states'] = ['error' => 'Eyaletler alınamadı'];
                                }
                            }
                        } else {
                            $testResults['germany_found'] = false;
                        }
                    } else {
                        $testResults['countries'] = ['error' => 'Ülkeler alınamadı'];
                    }
                } catch (Exception $e) {
                    $testResults['countries'] = ['error' => $e->getMessage()];
                }
            } else {
                $testResults['token_status'] = 'failed';
            }
            
            echo json_encode($testResults, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
            exit;
        }
        
        // Debug endpoint - Token test (ŞU ANDA KULLANILMIYOR)
        /*
        if (isset($segments[0]) && $segments[0] === 'debug-token') {
            // Token dosyasını kontrol et
            $tokenFileExists = file_exists(DIYANET_TOKEN_FILE);
            $tokenFileContent = $tokenFileExists ? file_get_contents(DIYANET_TOKEN_FILE) : null;
            
            // Yeni token almayı dene
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, DIYANET_API_BASE . '/Auth/Login');
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
                'email' => DIYANET_USERNAME, // API email bekliyor
                'password' => DIYANET_PASSWORD
            ]));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Accept: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
            curl_setopt($ch, CURLOPT_TIMEOUT, 30);
            
            $response = curl_exec($ch);
            $curlError = curl_error($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            echo json_encode([
                'status' => $httpCode === 200 ? 'ok' : 'error',
                'http_code' => $httpCode,
                'curl_error' => $curlError ?: null,
                'response_preview' => substr($response, 0, 500),
                'token_file_exists' => $tokenFileExists,
                'token_file_content' => $tokenFileContent ? substr($tokenFileContent, 0, 100) : null
            ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
            exit;
        }
        */
        
        // Ülkeleri getir - Veritabanından
        if (isset($segments[0]) && $segments[0] === 'countries') {
            try {
                error_log("=== ÜLKELER İSTENİYOR (Veritabanından) ===");
                
                $db = getDB();
                if (!$db) {
                    throw new Exception('Veritabanı bağlantısı kurulamadı');
                }
                
                // Veritabanından ülkeleri çek
                $stmt = $db->query("SELECT DISTINCT country_code, country_name FROM countries ORDER BY country_name");
                $countries = $stmt->fetchAll();
                
                if (empty($countries)) {
                    // Fallback: Sadece Almanya'yı döndür
                    $formattedCountries = [[
                        'country_code' => '13',
                        'country_name' => 'ALMANYA'
                    ]];
                } else {
                    $formattedCountries = array_map(function($row) {
                        return [
                            'country_code' => $row['country_code'],
                            'country_name' => $row['country_name']
                        ];
                    }, $countries);
                }
                
                error_log("✓ Ülkeler döndürülüyor: " . count($formattedCountries) . " ülke");
                echo json_encode($formattedCountries);
                exit;
            } catch (Exception $e) {
                error_log('✗ Ülkeler hatası: ' . $e->getMessage());
                error_log('Stack trace: ' . $e->getTraceAsString());
                // Hata olsa bile fallback olarak Almanya'yı döndür
                $formattedCountries = [[
                    'country_code' => '13',
                    'country_name' => 'ALMANYA'
                ]];
                echo json_encode($formattedCountries);
                exit;
            } catch (Error $e) {
                error_log('✗✗✗ FATAL ERROR: Ülkeler fatal hatası: ' . $e->getMessage());
                error_log('Stack trace: ' . $e->getTraceAsString());
                // Fatal hata olsa bile fallback olarak Almanya'yı döndür
                $formattedCountries = [[
                    'country_code' => '13',
                    'country_name' => 'ALMANYA'
                ]];
                echo json_encode($formattedCountries);
                exit;
            }
        }
        
        // Eyaletleri getir - Veritabanından
        if (isset($segments[0]) && $segments[0] === 'states' && isset($segments[1])) {
            $countryCode = urldecode($segments[1]);
            if (!validateInput($countryCode, 10)) {
                http_response_code(400);
                echo json_encode(['error' => 'Geçersiz ülke kodu']);
                exit;
            }
            try {
                error_log("=== EYALETLER İSTENİYOR (Veritabanından) ===");
                error_log("CountryCode: {$countryCode}");
                
                $db = getDB();
                if (!$db) {
                    throw new Exception('Veritabanı bağlantısı kurulamadı');
                }
                
                // Veritabanından eyaletleri çek
                $stmt = $db->prepare("SELECT DISTINCT state_code, state_name FROM countries WHERE country_code = ? ORDER BY state_name");
                $stmt->execute([$countryCode]);
                $states = $stmt->fetchAll();
                
                if (empty($states)) {
                    error_log("✗ Veritabanında eyalet bulunamadı");
                    http_response_code(404);
                    echo json_encode(['error' => 'Bu ülke için eyalet bulunamadı']);
                    exit;
                }
                
                $formattedStates = array_map(function($row) {
                    return [
                        'state_code' => $row['state_code'],
                        'state_name' => $row['state_name']
                    ];
                }, $states);
                
                error_log("✓ Veritabanından eyaletler alındı: " . count($formattedStates) . " eyalet");
                echo json_encode($formattedStates);
                exit;
            } catch (Exception $e) {
                error_log('✗✗✗ EXCEPTION: Eyaletler hatası: ' . $e->getMessage());
                error_log('Stack trace: ' . $e->getTraceAsString());
                http_response_code(500);
                echo json_encode(['error' => 'Eyaletler alınamadı: ' . $e->getMessage()]);
                exit;
            } catch (Error $e) {
                error_log('✗✗✗ FATAL ERROR: Eyaletler fatal hatası: ' . $e->getMessage());
                error_log('Stack trace: ' . $e->getTraceAsString());
                http_response_code(500);
                echo json_encode(['error' => 'Eyaletler alınamadı: ' . $e->getMessage()]);
                exit;
            }
        }
        
        // Şehirleri getir - Veritabanından
        if (isset($segments[0]) && $segments[0] === 'cities' && isset($segments[1]) && isset($segments[2])) {
            $countryCode = urldecode($segments[1]);
            $stateCode = urldecode($segments[2]);
            
            error_log("=== ŞEHİRLER İSTENİYOR (Veritabanından) ===");
            error_log("CountryCode: {$countryCode}, StateCode: {$stateCode}");
            
            // validateInput'u sadece boş olmayan ve çok uzun olmayan değerler için kontrol et
            // StateCode için 30 karakter limit (MECKLENBURG-VORPOMMERN gibi uzun isimler için)
            if (empty($countryCode) || empty($stateCode) || strlen($countryCode) > 10 || strlen($stateCode) > 30) {
                error_log("✗ Geçersiz parametreler: CountryCode length=" . strlen($countryCode) . ", StateCode length=" . strlen($stateCode));
                http_response_code(400);
                echo json_encode(['error' => 'Geçersiz parametreler']);
                exit;
            }
            
            try {
                $db = getDB();
                if (!$db) {
                    throw new Exception('Veritabanı bağlantısı kurulamadı');
                }
                
                // Veritabanından şehirleri çek
                $stmt = $db->prepare("SELECT DISTINCT city_name FROM countries WHERE country_code = ? AND state_code = ? ORDER BY city_name");
                $stmt->execute([$countryCode, $stateCode]);
                $cities = $stmt->fetchAll();
                
                if (empty($cities)) {
                    error_log("✗ Veritabanında şehir bulunamadı");
                    http_response_code(404);
                    echo json_encode(['error' => 'Bu eyalet için şehir bulunamadı']);
                    exit;
                }
                
                $cityNames = array_map(function($row) {
                    return $row['city_name'];
                }, $cities);
                
                error_log("✓ Veritabanından şehirler yüklendi: " . count($cityNames) . " şehir");
                error_log("İlk 5 şehir: " . implode(', ', array_slice($cityNames, 0, 5)));
                
                echo json_encode($cityNames);
                exit;
            } catch (Exception $e) {
                error_log('Şehirler hatası: ' . $e->getMessage());
                http_response_code(500);
                echo json_encode(['error' => 'Şehirler alınamadı: ' . $e->getMessage()]);
                exit;
            } catch (Error $e) {
                error_log('Şehirler fatal hatası: ' . $e->getMessage());
                // FALLBACK KODU KALDIRILDI - ramadan-namazvakitleri.json backup'a taşındı
                // Eğer veritabanı hatası varsa, direkt hata döndür
                http_response_code(500);
                echo json_encode(['error' => 'Şehirler alınamadı: ' . $e->getMessage()]);
                exit;
            }
        }
        
        // İmsakiye verisini getir - Veritabanından
        if (isset($segments[0]) && $segments[0] === 'imsakiye' && isset($segments[1]) && isset($segments[2]) && isset($segments[3])) {
            $countryCode = urldecode($segments[1]);
            $stateCode = urldecode($segments[2]);
            // Şehir ismi birden fazla segment olabilir (örn: BABENHAUSEN/BAVAIRA)
            // Tüm kalan segment'leri birleştir
            $cityName = urldecode(implode('/', array_slice($segments, 3)));
            // Uzunluk kontrolleri - validateInput yerine direkt kontrol (uzun eyalet isimleri için)
            if (empty($countryCode) || empty($stateCode) || empty($cityName) || 
                strlen($countryCode) > 20 || strlen($stateCode) > 30 || strlen($cityName) > 100) {
                http_response_code(400);
                echo json_encode(['error' => 'Geçersiz parametreler']);
                exit;
            }
            
            try {
                error_log("=== İMSAKİYE İSTENİYOR (Veritabanından) ===");
                error_log("CountryCode: {$countryCode}, StateCode: {$stateCode}, CityName: {$cityName}");
                
                $db = getDB();
                if (!$db) {
                    throw new Exception('Veritabanı bağlantısı kurulamadı');
                }
                
                // Veritabanından imsakiye verilerini çek
                $stmt = $db->prepare("SELECT hicri, miladi, imsak, gunes, ogle, ikindi, aksam, yatsi
                                      FROM imsakiye 
                                      WHERE country_code = ? AND state_code = ? AND city_name = ?");
                $stmt->execute([$countryCode, $stateCode, $cityName]);
                $rows = $stmt->fetchAll();
                
                if (empty($rows)) {
                    error_log("✗ Veritabanında imsakiye verisi bulunamadı");
                    http_response_code(404);
                    echo json_encode(['error' => "Bu şehir için imsakiye verisi bulunamadı: {$cityName}"]);
                    exit;
                }
                
                // Hicri tarihten Ramazan gününü çıkarıp sayısal olarak sırala (1 Ramazan'dan başlamalı)
                usort($rows, function($a, $b) {
                    // Hicri tarihten Ramazan gününü çıkar (örn: "1 Ramazan 1447" -> 1)
                    $getRamazanGunu = function($hicri) {
                        if (preg_match('/^(\d+)\s+Ramazan/', $hicri, $matches)) {
                            return (int)$matches[1];
                        }
                        return 999; // Eğer parse edilemezse en sona koy
                    };
                    
                    $gunA = $getRamazanGunu($a['hicri'] ?? '');
                    $gunB = $getRamazanGunu($b['hicri'] ?? '');
                    
                    return $gunA <=> $gunB; // Artan sıralama (1, 2, 3, ...)
                });
                
                // Veritabanı formatını API formatına çevir
                $formattedData = array_map(function($row) {
                    return [
                        'hicri' => $row['hicri'] ?? '',
                        'miladi' => $row['miladi'] ?? '',
                        'imsak' => $row['imsak'] ?? '',
                        'gunes' => $row['gunes'] ?? '',
                        'ogle' => $row['ogle'] ?? '',
                        'ikindi' => $row['ikindi'] ?? '',
                        'aksam' => $row['aksam'] ?? '',
                        'yatsi' => $row['yatsi'] ?? ''
                    ];
                }, $rows);
                
                error_log("✓ Veritabanından imsakiye verisi alındı: " . count($formattedData) . " gün");
                
                echo json_encode($formattedData);
                exit;
                
            } catch (Exception $e) {
                error_log('Diyanet API hatası: ' . $e->getMessage());
                http_response_code(500);
                echo json_encode(['error' => 'API hatası: ' . $e->getMessage()]);
                exit;
            }
        }
        
        // Bayram namazı vaktini getir - Veritabanından
        if (isset($segments[0]) && $segments[0] === 'bayram-namazi' && isset($segments[1]) && isset($segments[2]) && isset($segments[3])) {
            $countryCode = urldecode($segments[1]);
            $stateCode = urldecode($segments[2]);
            // Şehir ismi birden fazla segment olabilir (örn: BABENHAUSEN/BAVAIRA)
            // Tüm kalan segment'leri birleştir
            $cityName = urldecode(implode('/', array_slice($segments, 3)));
            // Uzunluk kontrolleri - validateInput yerine direkt kontrol (uzun eyalet isimleri için)
            if (empty($countryCode) || empty($stateCode) || empty($cityName) || 
                strlen($countryCode) > 20 || strlen($stateCode) > 30 || strlen($cityName) > 100) {
                http_response_code(400);
                echo json_encode(['error' => 'Geçersiz parametreler']);
                exit;
            }
            
            try {
                error_log("=== BAYRAM NAMAZI İSTENİYOR (Veritabanından) ===");
                error_log("CountryCode: {$countryCode}, StateCode: {$stateCode}, CityName: {$cityName}");
                
                $db = getDB();
                if (!$db) {
                    throw new Exception('Veritabanı bağlantısı kurulamadı');
                }
                
                // Veritabanından bayram namazı vaktini çek
                $stmt = $db->prepare("SELECT vakti FROM bayram_namazi WHERE country_code = ? AND state_code = ? AND city_name = ?");
                $stmt->execute([$countryCode, $stateCode, $cityName]);
                $row = $stmt->fetch();
                
                if ($row && isset($row['vakti']) && !empty($row['vakti'])) {
                    $vakti = $row['vakti'];
                    // Saat formatını kontrol et (HH:MM veya HH:MM:SS)
                    if (preg_match('/^(\d{1,2}):(\d{2})(?::\d{2})?$/', $vakti, $matches)) {
                        $vakti = $matches[1] . ':' . $matches[2]; // Sadece saat:dakika
                        error_log("✓ Veritabanından bayram namazı vakti alındı: {$cityName} - {$vakti}");
                        echo json_encode(['vakti' => $vakti]);
                    } else {
                        error_log("✗ Geçersiz saat formatı (bayram): {$vakti}");
                        echo json_encode(['vakti' => null]);
                    }
                } else {
                    error_log("✗ Veritabanında bayram namazı vakti bulunamadı");
                    echo json_encode(['vakti' => null]);
                }
                exit;
                
            } catch (Exception $e) {
                error_log('Diyanet API bayram hatası: ' . $e->getMessage());
                echo json_encode(['vakti' => null]);
                exit;
            }
        }
        
        // Bilinmeyen endpoint
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint bulunamadı']);
        
    } catch (Exception $e) {
        error_log('Genel API hatası: ' . $e->getMessage());
        error_log('Stack trace: ' . $e->getTraceAsString());
        http_response_code(500);
        echo json_encode(['error' => 'Sunucu hatası: ' . $e->getMessage()]);
    } catch (Error $e) {
        error_log('Fatal API hatası: ' . $e->getMessage());
        http_response_code(500);
        echo json_encode(['error' => 'Fatal hata: ' . $e->getMessage()]);
    }
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>
