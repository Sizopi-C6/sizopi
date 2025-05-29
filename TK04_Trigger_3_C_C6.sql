DROP TRIGGER IF EXISTS trigger_sync_medical_schedule ON catatan_medis;
DROP TRIGGER IF EXISTS trigger_add_periodic_schedules ON jadwal_pemeriksaan_kesehatan;
DROP TRIGGER IF EXISTS check_duplicate_animal_trigger ON hewan;
DROP TRIGGER IF EXISTS trigger_log_riwayat_satwa ON hewan;

DROP FUNCTION IF EXISTS sync_medical_records_schedule();
DROP FUNCTION IF EXISTS add_periodic_schedules();
DROP FUNCTION IF EXISTS set_animal_frequency(UUID, INT);
DROP FUNCTION IF EXISTS get_animal_frequency(UUID);
DROP FUNCTION IF EXISTS add_health_schedule(UUID, DATE, INT);
DROP FUNCTION IF EXISTS get_animals_for_medical_records();
DROP FUNCTION IF EXISTS get_medical_records_by_animal(UUID);
DROP FUNCTION IF EXISTS add_medical_record(UUID, VARCHAR, DATE, VARCHAR, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS update_medical_record(UUID, DATE, VARCHAR, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS delete_medical_record(UUID, DATE);
DROP FUNCTION IF EXISTS get_health_schedules_by_animal(UUID);
DROP FUNCTION IF EXISTS check_duplicate_animal();
DROP FUNCTION IF EXISTS log_riwayat_perubahan_satwa();

CREATE OR REPLACE FUNCTION sync_medical_records_schedule()
RETURNS TRIGGER AS $$
DECLARE
    next_check_date DATE;
    existing_schedule_date DATE;
    animal_name VARCHAR(100);
BEGIN
    IF NEW.status_kesehatan = 'Sakit' THEN
        next_check_date := NEW.tanggal_pemeriksaan + INTERVAL '7 days';
        
        SELECT h.name INTO animal_name FROM hewan h WHERE h.id = NEW.id_hewan;
        
        SELECT tgl_pemeriksaan_selanjutnya INTO existing_schedule_date
        FROM jadwal_pemeriksaan_kesehatan 
        WHERE id_hewan = NEW.id_hewan 
          AND tgl_pemeriksaan_selanjutnya >= NEW.tanggal_pemeriksaan
        ORDER BY tgl_pemeriksaan_selanjutnya ASC
        LIMIT 1;
        
        IF existing_schedule_date IS NOT NULL THEN
            UPDATE jadwal_pemeriksaan_kesehatan 
            SET tgl_pemeriksaan_selanjutnya = next_check_date
            WHERE id_hewan = NEW.id_hewan 
              AND tgl_pemeriksaan_selanjutnya = existing_schedule_date;
        ELSE
            INSERT INTO jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (NEW.id_hewan, next_check_date, 3);
        END IF;
        
        RAISE NOTICE 'SUKSES: Jadwal pemeriksaan hewan "%" telah diperbarui karena status kesehatan "Sakit".', animal_name;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_periodic_schedules()
RETURNS TRIGGER AS $$
DECLARE
    current_year INT;
    end_of_year DATE;
    next_schedule_date DATE;
    animal_name VARCHAR(100);
    schedule_count INT := 0;
BEGIN
    current_year := EXTRACT(YEAR FROM NEW.tgl_pemeriksaan_selanjutnya);
    end_of_year := (current_year || '-12-31')::DATE;
    
    SELECT h.name INTO animal_name FROM hewan h WHERE h.id = NEW.id_hewan;
    
    next_schedule_date := NEW.tgl_pemeriksaan_selanjutnya;
    
    LOOP
        next_schedule_date := next_schedule_date + (NEW.freq_pemeriksaan_rutin || ' months')::INTERVAL;
        
        EXIT WHEN next_schedule_date > end_of_year;
        
        IF NOT EXISTS (
            SELECT 1 FROM jadwal_pemeriksaan_kesehatan 
            WHERE id_hewan = NEW.id_hewan 
              AND tgl_pemeriksaan_selanjutnya = next_schedule_date
        ) THEN
            INSERT INTO jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (NEW.id_hewan, next_schedule_date, NEW.freq_pemeriksaan_rutin);
            schedule_count := schedule_count + 1;
        END IF;
    END LOOP;
    
    IF schedule_count > 0 THEN
        RAISE NOTICE 'SUKSES: Jadwal pemeriksaan rutin hewan "%" telah ditambahkan sesuai frekuensi.', animal_name;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_animal_frequency(
    p_animal_id UUID,
    p_frequency INT
)
RETURNS TEXT AS $$
DECLARE
    animal_name VARCHAR(100);
BEGIN
    IF p_frequency < 1 OR p_frequency > 12 THEN
        RETURN 'ERROR: Frekuensi harus antara 1-12 bulan!';
    END IF;
    
    SELECT h.name INTO animal_name FROM hewan h WHERE h.id = p_animal_id;
    IF animal_name IS NULL THEN
        RETURN 'ERROR: Hewan tidak ditemukan!';
    END IF;
    
    UPDATE jadwal_pemeriksaan_kesehatan 
    SET freq_pemeriksaan_rutin = p_frequency
    WHERE id_hewan = p_animal_id;
    
    RETURN 'SUCCESS: Frekuensi pemeriksaan untuk hewan "' || animal_name || '" berhasil diatur ke ' || p_frequency || ' bulan.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_animal_frequency(p_animal_id UUID)
RETURNS INT AS $$
DECLARE
    frequency INT;
BEGIN
    SELECT freq_pemeriksaan_rutin INTO frequency
    FROM jadwal_pemeriksaan_kesehatan 
    WHERE id_hewan = p_animal_id 
    LIMIT 1;
    
    RETURN COALESCE(frequency, 3);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_health_schedule(
    p_animal_id UUID,
    p_examination_date DATE,
    p_frequency INT DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    animal_name VARCHAR(100);
    final_frequency INT;
BEGIN
    SELECT h.name INTO animal_name FROM hewan h WHERE h.id = p_animal_id;
    IF animal_name IS NULL THEN
        RETURN 'ERROR: Hewan tidak ditemukan!';
    END IF;
    
    IF p_examination_date <= CURRENT_DATE THEN
        RETURN 'ERROR: Tanggal pemeriksaan harus di masa depan!';
    END IF;
    
    IF p_frequency IS NOT NULL THEN
        IF p_frequency < 1 OR p_frequency > 12 THEN
            RETURN 'ERROR: Frekuensi harus antara 1-12 bulan!';
        END IF;
        final_frequency := p_frequency;
    ELSE
        final_frequency := get_animal_frequency(p_animal_id);
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM jadwal_pemeriksaan_kesehatan 
        WHERE id_hewan = p_animal_id 
          AND tgl_pemeriksaan_selanjutnya = p_examination_date
    ) THEN
        RETURN 'ERROR: Jadwal pemeriksaan untuk tanggal ini sudah ada!';
    END IF;
    
    INSERT INTO jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
    VALUES (p_animal_id, p_examination_date, final_frequency);
    
    RETURN 'SUCCESS: Jadwal pemeriksaan untuk hewan "' || animal_name || '" berhasil ditambahkan.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_animals_for_medical_records()
RETURNS TABLE(
    id UUID,
    nama VARCHAR(100),
    spesies VARCHAR(100),
    asal_hewan VARCHAR(100),
    tanggal_lahir DATE,
    status_kesehatan VARCHAR(50),
    nama_habitat VARCHAR(100),
    url_foto VARCHAR(255),
    total_records BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.name::VARCHAR(100) as nama,                    
        h.species::VARCHAR(100) as spesies,  
        h.asal_hewan,
        h.tanggal_lahir,
        h.status_kesehatan,
        h.nama_habitat,
        h.url_foto,
        COUNT(cm.id_hewan) as total_records
    FROM hewan h
    LEFT JOIN catatan_medis cm ON h.id = cm.id_hewan
    GROUP BY h.id, h.name, h.species, h.asal_hewan, h.tanggal_lahir, h.status_kesehatan, h.nama_habitat, h.url_foto
    ORDER BY h.name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_medical_records_by_animal(p_animal_id UUID)
RETURNS TABLE(
    id_hewan UUID,
    username_dh VARCHAR(50),
    tanggal_pemeriksaan DATE,
    diagnosis VARCHAR(100),
    pengobatan VARCHAR(100),
    status_kesehatan VARCHAR(50),
    catatan_tindak_lanjut VARCHAR(100),
    nama_dokter VARCHAR(150),
    animal_name VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.id_hewan,
        cm.username_dh,
        cm.tanggal_pemeriksaan,
        cm.diagnosis,
        cm.pengobatan,
        cm.status_kesehatan,
        cm.catatan_tindak_lanjut,
        CONCAT(p.nama_depan, ' ', COALESCE(p.nama_tengah || ' ', ''), p.nama_belakang)::VARCHAR(150) as nama_dokter,
        h.name::VARCHAR(100) as animal_name
    FROM catatan_medis cm
    JOIN dokter_hewan dh ON cm.username_dh = dh.username_dh
    JOIN pengguna p ON dh.username_dh = p.username
    JOIN hewan h ON cm.id_hewan = h.id
    WHERE cm.id_hewan = p_animal_id
    ORDER BY cm.tanggal_pemeriksaan DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_medical_record(
    p_animal_id UUID,
    p_doctor_username VARCHAR(50),
    p_examination_date DATE,
    p_diagnosis VARCHAR(100),
    p_treatment VARCHAR(100),
    p_health_status VARCHAR(50)
)
RETURNS TEXT AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM catatan_medis 
        WHERE id_hewan = p_animal_id 
          AND tanggal_pemeriksaan = p_examination_date
    ) THEN
        RETURN 'ERROR: Sudah ada catatan medis untuk hewan ini pada tanggal tersebut!';
    END IF;
    
    INSERT INTO catatan_medis (
        id_hewan, 
        username_dh, 
        tanggal_pemeriksaan, 
        diagnosis, 
        pengobatan, 
        status_kesehatan,
        catatan_tindak_lanjut
    ) VALUES (
        p_animal_id, 
        p_doctor_username, 
        p_examination_date, 
        p_diagnosis, 
        p_treatment, 
        p_health_status,
        NULL
    );
    
    UPDATE hewan SET status_kesehatan = p_health_status WHERE id = p_animal_id;
    
    RETURN 'SUCCESS: Catatan medis berhasil ditambahkan!';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_medical_record(
    p_animal_id UUID,
    p_examination_date DATE,
    p_new_diagnosis VARCHAR(100),
    p_new_treatment VARCHAR(100),
    p_follow_up_notes VARCHAR(100)
)
RETURNS TEXT AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM catatan_medis 
        WHERE id_hewan = p_animal_id 
          AND tanggal_pemeriksaan = p_examination_date
    ) THEN
        RETURN 'ERROR: Catatan medis tidak ditemukan!';
    END IF;
    
    UPDATE catatan_medis 
    SET 
        diagnosis = p_new_diagnosis,
        pengobatan = p_new_treatment,
        catatan_tindak_lanjut = p_follow_up_notes
    WHERE id_hewan = p_animal_id 
      AND tanggal_pemeriksaan = p_examination_date;
    
    RETURN 'SUCCESS: Catatan medis berhasil diperbarui!';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_medical_record(
    p_animal_id UUID,
    p_examination_date DATE
)
RETURNS TEXT AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM catatan_medis 
        WHERE id_hewan = p_animal_id 
          AND tanggal_pemeriksaan = p_examination_date
    ) THEN
        RETURN 'ERROR: Catatan medis tidak ditemukan!';
    END IF;
    
    DELETE FROM catatan_medis 
    WHERE id_hewan = p_animal_id 
      AND tanggal_pemeriksaan = p_examination_date;
    
    RETURN 'SUCCESS: Catatan medis berhasil dihapus!';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_health_schedules_by_animal(p_animal_id UUID)
RETURNS TABLE(
    id_hewan UUID,
    tgl_pemeriksaan_selanjutnya DATE,
    freq_pemeriksaan_rutin INT,
    animal_name VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jph.id_hewan,
        jph.tgl_pemeriksaan_selanjutnya,
        jph.freq_pemeriksaan_rutin,
        h.name::VARCHAR(100) as animal_name
    FROM jadwal_pemeriksaan_kesehatan jph
    JOIN hewan h ON jph.id_hewan = h.id
    WHERE jph.id_hewan = p_animal_id
    ORDER BY jph.tgl_pemeriksaan_selanjutnya ASC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_duplicate_animal()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hewan 
        WHERE name = NEW.name 
          AND species = NEW.species 
          AND asal_hewan = NEW.asal_hewan
          AND id != NEW.id
    ) THEN
        RAISE EXCEPTION 'ERROR: Hewan dengan nama "%" spesies "%" dari "%" sudah ada!', NEW.name, NEW.species, NEW.asal_hewan;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_riwayat_perubahan_satwa()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status_kesehatan != NEW.status_kesehatan OR 
       OLD.nama_habitat != NEW.nama_habitat THEN
        
        INSERT INTO riwayat_satwa (
            id_hewan,
            tanggal_perubahan,
            jenis_perubahan,
            nilai_lama,
            nilai_baru
        ) VALUES (
            NEW.id,
            CURRENT_DATE,
            CASE 
                WHEN OLD.status_kesehatan != NEW.status_kesehatan THEN 'Status Kesehatan'
                WHEN OLD.nama_habitat != NEW.nama_habitat THEN 'Habitat'
                ELSE 'Update Data'
            END,
            CASE 
                WHEN OLD.status_kesehatan != NEW.status_kesehatan THEN OLD.status_kesehatan
                WHEN OLD.nama_habitat != NEW.nama_habitat THEN OLD.nama_habitat
                ELSE 'N/A'
            END,
            CASE 
                WHEN OLD.status_kesehatan != NEW.status_kesehatan THEN NEW.status_kesehatan
                WHEN OLD.nama_habitat != NEW.nama_habitat THEN NEW.nama_habitat
                ELSE 'N/A'
            END
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_medical_schedule
    AFTER INSERT ON catatan_medis
    FOR EACH ROW
    EXECUTE FUNCTION sync_medical_records_schedule();

CREATE TRIGGER trigger_add_periodic_schedules
    AFTER INSERT ON jadwal_pemeriksaan_kesehatan
    FOR EACH ROW
    EXECUTE FUNCTION add_periodic_schedules();

CREATE TRIGGER check_duplicate_animal_trigger
    BEFORE INSERT OR UPDATE ON hewan
    FOR EACH ROW
    EXECUTE FUNCTION check_duplicate_animal();

CREATE TRIGGER trigger_log_riwayat_satwa
    AFTER UPDATE ON hewan
    FOR EACH ROW
    EXECUTE FUNCTION log_riwayat_perubahan_satwa();