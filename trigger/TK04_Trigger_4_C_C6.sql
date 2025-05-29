-- =====================================================
-- 1. Pemeriksaan Kapasitas Atraksi saat Reservasi
-- =====================================================
CREATE OR REPLACE FUNCTION cek_kapasitas_reservasi() RETURNS trigger AS $$
DECLARE
    kapasitas_max INTEGER;
    total_tiket_terpesan INTEGER;
    jumlah_tiket_lama INTEGER;
    sisa_tiket INTEGER;
BEGIN
    SELECT f.kapasitas_max INTO kapasitas_max
    FROM fasilitas f
    WHERE f.nama = NEW.nama_atraksi;

    IF kapasitas_max IS NULL THEN
        RAISE EXCEPTION 'ERROR: Atraksi/fasilitas "%" tidak ditemukan di tabel fasilitas.', NEW.nama_atraksi;
    END IF;

    SELECT COALESCE(SUM(jumlah_tiket), 0) INTO total_tiket_terpesan
    FROM reservasi
    WHERE nama_atraksi = NEW.nama_atraksi
      AND tanggal_kunjungan = NEW.tanggal_kunjungan
      AND status = 'Terjadwal';

    IF TG_OP = 'UPDATE' THEN
        jumlah_tiket_lama := OLD.jumlah_tiket;
        total_tiket_terpesan := total_tiket_terpesan - jumlah_tiket_lama;
    END IF;

    sisa_tiket := kapasitas_max - total_tiket_terpesan;

    IF sisa_tiket < NEW.jumlah_tiket THEN
        RAISE EXCEPTION 'ERROR: Kapasitas tersisa "%" tiket, atraksi tidak mencukupi untuk sejumlah "%" tiket yang diminta.', sisa_tiket, NEW.jumlah_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cek_kapasitas_reservasi
BEFORE INSERT OR UPDATE ON reservasi
FOR EACH ROW EXECUTE FUNCTION cek_kapasitas_reservasi();

-- =====================================================
-- 2. Rotasi Otomatis Pelatih Hewan untuk Atraksi
-- =====================================================
CREATE OR REPLACE FUNCTION rotasi_pelatih_hewan() RETURNS trigger AS $$
DECLARE
    tgl_terlama TIMESTAMP;
    durasi INTERVAL;
BEGIN
    SELECT MIN(tgl_penugasan) INTO tgl_terlama
    FROM jadwal_penugasan
    WHERE username_lh = NEW.username_lh
      AND nama_atraksi = NEW.nama_atraksi;

    IF tgl_terlama IS NOT NULL THEN
        durasi := NOW() - tgl_terlama;
        IF durasi >= INTERVAL '3 months' THEN
            RAISE NOTICE 'SUKSES: Pelatih "%" telah bertugas lebih dari 3 bulan di atraksi "%" dan akan diganti.',
                NEW.username_lh, NEW.nama_atraksi;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rotasi_pelatih_hewan
AFTER INSERT OR UPDATE ON jadwal_penugasan
FOR EACH ROW EXECUTE FUNCTION rotasi_pelatih_hewan();