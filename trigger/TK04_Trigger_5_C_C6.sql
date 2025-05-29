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


CREATE OR REPLACE FUNCTION update_adopter_ranking()
RETURNS TEXT AS $$
DECLARE
    top_adopter_name TEXT;
    top_contribution BIGINT;
    result_message TEXT;
    adopter_count INTEGER;
BEGIN
    SELECT COUNT(DISTINCT a.id_adopter)
    INTO adopter_count
    FROM adopsi ad
    JOIN adopter a ON ad.id_adopter = a.id_adopter
    WHERE ad.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year';
    
    SELECT 
        COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
        SUM(ad.kontribusi_finansial) as total_kontribusi
    INTO top_adopter_name, top_contribution
    FROM adopsi ad
    JOIN adopter a ON ad.id_adopter = a.id_adopter
    LEFT JOIN individu i ON a.id_adopter = i.id_adopter
    LEFT JOIN organisasi o ON a.id_adopter = o.id_adopter
    WHERE ad.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
      AND ad.status_pembayaran = 'Lunas'
    GROUP BY a.id_adopter, COALESCE(i.nama, o.nama_organisasi)
    ORDER BY total_kontribusi DESC
    LIMIT 1;
    
    IF top_adopter_name IS NOT NULL AND top_contribution > 0 THEN
        result_message := 'SUKSES: Daftar Top 5 adopter satu tahun terakhir berhasil diperbarui, dengan peringkat pertama dengan nama adopter "' || 
                         top_adopter_name || '" berkontribusi sebesar ' || top_contribution || '.';
    ELSE
        result_message := 'SUKSES: Daftar Top 5 adopter satu tahun terakhir berhasil diperbarui, namun tidak ada kontribusi yang valid dalam setahun terakhir.';
    END IF;
    
    RAISE NOTICE '%', result_message;
    
    RETURN result_message;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION adopter_ranking_after_kontribusi()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_adopter_ranking();
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_adopter_ranking
    AFTER INSERT OR UPDATE OR DELETE ON ADOPSI
    FOR EACH STATEMENT
    EXECUTE FUNCTION adopter_ranking_after_kontribusi();

CREATE OR REPLACE FUNCTION top5_adopter()
RETURNS TABLE (
    ranking INTEGER,
    nama_adopter VARCHAR(100),
    total_kontribusi BIGINT,
    jumlah_adopsi BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY SUM(ad.kontribusi_finansial) DESC)::INTEGER as ranking,
        COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
        SUM(ad.kontribusi_finansial) as total_kontribusi,
        COUNT(ad.id_adopter) as jumlah_adopsi
    FROM adopsi ad
    JOIN adopter a ON ad.id_adopter = a.id_adopter
    LEFT JOIN individu i ON a.id_adopter = i.id_adopter
    LEFT JOIN organisasi o ON a.id_adopter = o.id_adopter
    WHERE ad.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
        AND ad.status_pembayaran = 'Lunas'
    GROUP BY a.id_adopter, COALESCE(i.nama, o.nama_organisasi)
    ORDER BY total_kontribusi DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;