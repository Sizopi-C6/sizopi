-- Pemeriksaan Satwa Duplikat saat Pendaftaran
CREATE OR REPLACE FUNCTION check_duplicate_animal()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM HEWAN H 
        WHERE H.name = NEW.name 
          AND H.species = NEW.species 
          AND H.asal_hewan = NEW.asal_hewan
    ) THEN
        RAISE EXCEPTION 'Data satwa atas nama "%", spesies "%", dan berasal dari "%" sudah terdaftar.', 
                        NEW.name, NEW.species, NEW.asal_hewan;
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

CREATE OR REPLACE FUNCTION log_riwayat_perubahan_satwa()
RETURNS TRIGGER AS $$
DECLARE
    msg TEXT := 'SUKSES:';
    field TEXT := '';
    before TEXT := '';
    after TEXT := '';
BEGIN
    IF OLD.status_kesehatan IS DISTINCT FROM NEW.status_kesehatan THEN
        field := 'status_kesehatan';
        before := OLD.status_kesehatan;
        after := NEW.status_kesehatan;
        msg := msg || ' Riwayat perubahan status kesehatan dari "' || OLD.status_kesehatan || '" menjadi "' || NEW.status_kesehatan || '"';
    END IF;

    IF OLD.nama_habitat IS DISTINCT FROM NEW.nama_habitat THEN
        IF field <> '' THEN
            msg := msg || ' atau';
        END IF;
        field := field || (CASE WHEN field = '' THEN '' ELSE ', ' END) || 'nama_habitat';
        before := before || (CASE WHEN before = '' THEN '' ELSE ', ' END) || OLD.nama_habitat;
        after := after || (CASE WHEN after = '' THEN '' ELSE ', ' END) || NEW.nama_habitat;
        msg := msg || ' habitat dari "' || OLD.nama_habitat || '" menjadi "' || NEW.nama_habitat || '"';
    END IF;

    IF field <> '' THEN
        msg := msg || ' telah dicatat.';
        INSERT INTO RIWAYAT_SATWA(id_hewan, field_berubah, nilai_sebelum, nilai_sesudah, pesan)
        VALUES (NEW.id, field, before, after, msg);
        RAISE NOTICE '%', msg;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_riwayat_satwa
AFTER UPDATE ON HEWAN
FOR EACH ROW
EXECUTE FUNCTION log_riwayat_perubahan_satwa();