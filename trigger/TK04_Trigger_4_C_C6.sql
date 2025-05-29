-- =====================================================
-- BLUE FEATURE
-- =====================================================

-------- 1
CREATE OR REPLACE FUNCTION cek_kapasitas_reservasi()
RETURNS TRIGGER AS $$
DECLARE
    kapasitas_max INT;
    total_terpesan INT;
    sisa INT;
BEGIN
    -- Ambil kapasitas maksimal dari fasilitas (atraksi/wahana)
    SELECT kapasitas_max INTO kapasitas_max FROM fasilitas WHERE nama = NEW.nama_atraksi;
    
    -- Hitung total tiket yang sudah dipesan pada tanggal yang sama, kecuali untuk update pada baris yang sama
    SELECT COALESCE(SUM(jumlah_tiket), 0)
    INTO total_terpesan
    FROM reservasi
    WHERE nama_atraksi = NEW.nama_atraksi
      AND tanggal_kunjungan = NEW.tanggal_kunjungan
      AND NOT (username_p = NEW.username_p AND tanggal_kunjungan = NEW.tanggal_kunjungan AND nama_atraksi = NEW.nama_atraksi);

    sisa := kapasitas_max - total_terpesan;
    
    IF NEW.jumlah_tiket > sisa THEN
        RAISE EXCEPTION 'ERROR: Kapasitas tersisa "%s" tiket, atraksi tidak mencukupi untuk sejumlah "%s" tiket yang diminta.', sisa, NEW.jumlah_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cek_kapasitas_reservasi ON reservasi;

CREATE TRIGGER trg_cek_kapasitas_reservasi
BEFORE INSERT OR UPDATE ON reservasi
FOR EACH ROW
EXECUTE FUNCTION cek_kapasitas_reservasi();

---------- 2 
CREATE OR REPLACE FUNCTION cek_rotasi_pelatih()
RETURNS TRIGGER AS $$
DECLARE
    pelatih RECORD;
    durasi INTERVAL;
BEGIN
    FOR pelatih IN
        SELECT jp.nama_pelatih, jp.tanggal_mulai, COALESCE(jp.tanggal_selesai, CURRENT_DATE) AS tanggal_selesai
        FROM jadwal_penugasan jp
        WHERE jp.nama_atraksi = NEW.nama_atraksi
    LOOP
        durasi := pelatih.tanggal_selesai - pelatih.tanggal_mulai;
        IF durasi >= INTERVAL '3 months' THEN
            RAISE NOTICE 'SUKSES: Pelatih "%" telah bertugas lebih dari 3 bulan di atraksi "%" dan akan diganti.', pelatih.nama_pelatih, NEW.nama_atraksi;
            -- Logika rotasi atau penggantian pelatih bisa dilakukan di aplikasi atau trigger lain
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_rotasi_pelatih ON atraksi;

CREATE TRIGGER trg_rotasi_pelatih
AFTER UPDATE ON atraksi
FOR EACH ROW
EXECUTE FUNCTION cek_rotasi_pelatih();

