CREATE OR REPLACE FUNCTION update_total_kontribusi_adopter()
RETURNS TRIGGER AS $$
DECLARE
    adopter_id UUID;
    nama_adopter TEXT;
    total_baru INT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        adopter_id := OLD.id_adopter;
    ELSE
        adopter_id := NEW.id_adopter;
    END IF;
    
    SELECT COALESCE(SUM(kontribusi_finansial), 0)
    INTO total_baru
    FROM ADOPSI
    WHERE id_adopter = adopter_id 
    AND status_pembayaran = 'Lunas';
    
    UPDATE ADOPTER
    SET total_kontribusi = total_baru
    WHERE id_adopter = adopter_id;
    
    SELECT nama INTO nama_adopter
    FROM INDIVIDU
    WHERE id_adopter = adopter_id;
    
    IF nama_adopter IS NULL THEN
        SELECT nama_organisasi INTO nama_adopter
        FROM ORGANISASI
        WHERE id_adopter = adopter_id;
    END IF;
    
    IF nama_adopter IS NULL THEN
        SELECT COALESCE(username_adopter, 'Unknown') INTO nama_adopter
        FROM ADOPTER
        WHERE id_adopter = adopter_id;
    END IF;
    
    RAISE NOTICE 'SUKSES: Total kontribusi adopter "%" telah diperbarui', nama_adopter;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_kontribusi_adopter
    AFTER INSERT OR UPDATE OR DELETE ON ADOPSI
    FOR EACH ROW
    EXECUTE FUNCTION update_total_kontribusi_adopter();