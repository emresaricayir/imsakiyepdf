<?php
/**
 * JSON verilerini SQLite veritabanına aktar
 * Kullanım: php migrate.php
 */

$db_path = __DIR__ . '/imsakiye.db';
$countries_json = __DIR__ . '/countries.json';
$imsakiye_json = __DIR__ . '/imsakiye-data.json';
$bayram_json = __DIR__ . '/bayram-namazi.json';

echo "🔄 JSON verileri SQLite'a aktarılıyor...\n\n";

// Eski veritabanını sil (varsa)
if (file_exists($db_path)) {
    echo "⚠️  Eski veritabanı siliniyor...\n";
    unlink($db_path);
}

// Veritabanını oluştur
try {
    $db = new PDO('sqlite:' . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "✓ Veritabanı oluşturuldu: $db_path\n";
} catch (PDOException $e) {
    die("❌ Veritabanı oluşturulamadı: " . $e->getMessage() . "\n");
}

// Tabloları oluştur
try {
    $db->exec("
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            country_name TEXT NOT NULL,
            state_code TEXT NOT NULL,
            state_name TEXT NOT NULL,
            city_name TEXT NOT NULL,
            UNIQUE(country_code, state_code, city_name)
        )
    ");
    echo "✓ countries tablosu oluşturuldu\n";
    
    $db->exec("
        CREATE TABLE IF NOT EXISTS imsakiye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            state_code TEXT NOT NULL,
            city_name TEXT NOT NULL,
            hicri TEXT NOT NULL,
            miladi TEXT NOT NULL,
            imsak TEXT NOT NULL,
            gunes TEXT NOT NULL,
            ogle TEXT NOT NULL,
            ikindi TEXT NOT NULL,
            aksam TEXT NOT NULL,
            yatsi TEXT NOT NULL
        )
    ");
    echo "✓ imsakiye tablosu oluşturuldu\n";
    
    $db->exec("
        CREATE TABLE IF NOT EXISTS bayram_namazi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            state_code TEXT NOT NULL,
            city_name TEXT NOT NULL,
            vakti TEXT NOT NULL,
            UNIQUE(country_code, state_code, city_name)
        )
    ");
    echo "✓ bayram_namazi tablosu oluşturuldu\n";
    
    // İndeksler
    $db->exec("CREATE INDEX IF NOT EXISTS idx_imsakiye_location ON imsakiye(country_code, state_code, city_name)");
    $db->exec("CREATE INDEX IF NOT EXISTS idx_countries_location ON countries(country_code, state_code)");
    $db->exec("CREATE INDEX IF NOT EXISTS idx_bayram_location ON bayram_namazi(country_code, state_code, city_name)");
    $db->exec("CREATE INDEX IF NOT EXISTS idx_city_name ON countries(city_name)");
    echo "✓ İndeksler oluşturuldu\n\n";
    
} catch (PDOException $e) {
    die("❌ Tablo oluşturma hatası: " . $e->getMessage() . "\n");
}

// Countries.json yükle
if (file_exists($countries_json)) {
    echo "📂 countries.json yükleniyor...\n";
    $countriesData = json_decode(file_get_contents($countries_json), true);
    
    if ($countriesData) {
        $stmt = $db->prepare("
            INSERT OR IGNORE INTO countries 
            (country_code, country_name, state_code, state_name, city_name)
            VALUES (?, ?, ?, ?, ?)
        ");
        
        $db->beginTransaction();
        $total = 0;
        
        foreach ($countriesData as $countryCode => $country) {
            foreach ($country['states'] as $stateCode => $state) {
                foreach ($state['cities'] as $cityName) {
                    $stmt->execute([
                        $countryCode,
                        $country['name'],
                        $stateCode,
                        $state['name'],
                        $cityName
                    ]);
                    $total++;
                }
            }
        }
        
        $db->commit();
        echo "✓ $total şehir verisi eklendi\n\n";
    } else {
        echo "⚠️  countries.json boş veya geçersiz\n\n";
    }
} else {
    echo "⚠️  countries.json bulunamadı, atlanıyor...\n\n";
}

// İmsakiye verilerini yükle
if (file_exists($imsakiye_json)) {
    echo "📂 imsakiye-data.json yükleniyor...\n";
    $imsakiyeData = json_decode(file_get_contents($imsakiye_json), true);
    
    if ($imsakiyeData) {
        $stmt = $db->prepare("
            INSERT INTO imsakiye 
            (country_code, state_code, city_name, hicri, miladi, imsak, gunes, ogle, ikindi, aksam, yatsi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ");
        
        $db->beginTransaction();
        $total = 0;
        $cityCount = 0;
        
        foreach ($imsakiyeData as $countryCode => $states) {
            foreach ($states as $stateCode => $cities) {
                foreach ($cities as $cityName => $cityData) {
                    $cityCount++;
                    
                    if (is_array($cityData)) {
                        foreach ($cityData as $row) {
                            $stmt->execute([
                                $countryCode,
                                $stateCode,
                                $cityName,
                                $row['hicri'] ?? '',
                                $row['miladi'] ?? '',
                                $row['imsak'] ?? '',
                                $row['gunes'] ?? '',
                                $row['ogle'] ?? '',
                                $row['ikindi'] ?? '',
                                $row['aksam'] ?? '',
                                $row['yatsi'] ?? ''
                            ]);
                            $total++;
                        }
                    }
                }
            }
        }
        
        $db->commit();
        echo "✓ $total imsakiye satırı eklendi ($cityCount şehir)\n\n";
    } else {
        echo "⚠️  imsakiye-data.json boş veya geçersiz\n\n";
    }
} else {
    echo "⚠️  imsakiye-data.json bulunamadı, atlanıyor...\n\n";
}

// Bayram namazı verilerini yükle
if (file_exists($bayram_json)) {
    echo "📂 bayram-namazi.json yükleniyor...\n";
    $bayramData = json_decode(file_get_contents($bayram_json), true);
    
    if ($bayramData) {
        $stmt = $db->prepare("
            INSERT OR IGNORE INTO bayram_namazi 
            (country_code, state_code, city_name, vakti)
            VALUES (?, ?, ?, ?)
        ");
        
        $db->beginTransaction();
        $total = 0;
        
        foreach ($bayramData as $countryCode => $states) {
            foreach ($states as $stateCode => $cities) {
                foreach ($cities as $cityName => $vakti) {
                    $stmt->execute([$countryCode, $stateCode, $cityName, $vakti]);
                    $total++;
                }
            }
        }
        
        $db->commit();
        echo "✓ $total bayram namazı vakti eklendi\n\n";
    } else {
        echo "⚠️  bayram-namazi.json boş veya geçersiz\n\n";
    }
} else {
    echo "⚠️  bayram-namazi.json bulunamadı, atlanıyor...\n\n";
}

// İstatistikler
try {
    $stmt = $db->query('SELECT COUNT(*) as count FROM countries');
    $row = $stmt->fetch();
    echo "📊 Toplam şehir sayısı: " . $row['count'] . "\n";
    
    $stmt = $db->query('SELECT COUNT(*) as count FROM imsakiye');
    $row = $stmt->fetch();
    echo "📊 Toplam imsakiye satırı: " . $row['count'] . "\n";
    
    $stmt = $db->query('SELECT COUNT(*) as count FROM bayram_namazi');
    $row = $stmt->fetch();
    echo "📊 Toplam bayram namazı vakti: " . $row['count'] . "\n";
    
} catch (PDOException $e) {
    echo "⚠️  İstatistik hatası: " . $e->getMessage() . "\n";
}

echo "\n✅ Migrasyon tamamlandı!\n";
echo "💡 Artık api.php dosyasını kullanabilirsiniz.\n";
?>
