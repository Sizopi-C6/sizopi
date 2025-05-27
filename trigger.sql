-- Pemeriksaan Satwa Duplikat saat Pendaftaran
CREATE OR REPLACE FUNCTION check_duplicate_animal()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM HEWAN H WHERE (H.nama_individu = NEW.nama_individu) AND (H.spesies = NEW.spesies) AND (H.asal_hewan = NEW.asal_hewan) THEN
        RAISE EXCEPTION 'Data satwa atas nama "%" , spesies "%" , dan berasal dari hewan "%" sudah terdaftar.', NEW.nama_individu, NEW.spesies, NEW.asal_hewan;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk memanggil fungsi pemeriksaan duplikat saat melakukan INSERT pada tabel HEWAN
CREATE TRIGGER check_duplicate_animal_trigger
BEFORE INSERT ON HEWAN
FOR EACH ROW EXECUTE PROCEDURE check_duplicate_animal();

-- RIWAYAT SATWA
CREATE TABLE RIWAYAT_SATWA (
    id SERIAL PRIMARY KEY,
    id_hewan UUID NOT NULL,
    waktu TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    field_berubah VARCHAR(50) NOT NULL,
    nilai_sebelum TEXT,
    nilai_sesudah TEXT,
    pesan TEXT,
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Trigger untuk mencatat perubahan pada tabel HEWAN
CREATE OR REPLACE FUNCTION log_riwayat_perubahan_satwa()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO RIWAYAT_SATWA(id_hewan, field_berubah, nilai_sebelum, nilai_sesudah, pesan)
    VALUES (NEW.id, 'status_kesehatan', OLD.status_kesehatan, NEW.status_kesehatan, 'SUKSES: Riwayat perubahan status kesehatan dari "' || OLD.status_kesehatan || '" menjadi "' || NEW.status_kesehatan || '" telah dicatat.'
    );

    INSERT INTO RIWAYAT_SATWA(id_hewan, field_berubah, nilai_sebelum, nilai_sesudah, pesan)
    VALUES (NEW.id, 'nama_habitat', OLD.nama_habitat, NEW.nama_habitat, 'SUKSES: Riwayat perubahan habitat dari "' || OLD.nama_habitat ||  '" menjadi "' || NEW.nama_habitat || '" telah dicatat.'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_riwayat_satwa
AFTER UPDATE ON HEWAN
FOR EACH ROW WHEN (OLD.status_kesehatan IS DISTINCT FROM NEW.status_kesehatan OR OLD.nama_habitat IS DISTINCT FROM NEW.nama_habitat OR OLD.status_kesehatan = NEW.status_kesehatan OR OLD.nama_habitat = NEW.nama_habitat)
EXECUTE FUNCTION log_riwayat_perubahan_satwa();