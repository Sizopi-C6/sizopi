
-- Sinkronisasi total kontribusi adopter dengan data adopsi
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


-- Pemeringkatan adopter dengan total kontribusi tertinggi selama setahun terakhir
DO $$
DECLARE
    duplicate_record RECORD;
    keep_record RECORD;
BEGIN
    FOR duplicate_record IN
        SELECT id_adopter, COUNT(*) as cnt
        FROM individu 
        GROUP BY id_adopter 
        HAVING COUNT(*) > 1
    LOOP
        SELECT nik, nama 
        INTO keep_record
        FROM individu 
        WHERE id_adopter = duplicate_record.id_adopter
        ORDER BY LENGTH(nama) DESC, nama DESC
        LIMIT 1;
        
        DELETE FROM individu 
        WHERE id_adopter = duplicate_record.id_adopter 
        AND nik != keep_record.nik;
    END LOOP;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_adopter_per_individual' 
        AND table_name = 'individu'
    ) THEN
        ALTER TABLE individu ADD CONSTRAINT unique_adopter_per_individual UNIQUE (id_adopter);
    END IF;
END $$;

CREATE OR REPLACE FUNCTION top5_adopter()
RETURNS TABLE(
    nama_adopter TEXT,
    total_kontribusi_setahun DECIMAL(15,2),
    total_kontribusi_all_time DECIMAL(15,2),
    jumlah_adopsi_aktif INTEGER,
    tipe_adopter TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH unique_adopter_data AS (
        SELECT DISTINCT ON (ad.id_adopter)
            ad.id_adopter,
            CASE 
                WHEN i.nama IS NOT NULL THEN i.nama
                WHEN o.nama_organisasi IS NOT NULL THEN o.nama_organisasi
                ELSE 'Unknown Adopter'
            END as nama_adopter,
            CASE 
                WHEN i.nik IS NOT NULL THEN 'Individu'
                WHEN o.npp IS NOT NULL THEN 'Organisasi'
                ELSE 'Unknown'
            END as tipe_adopter
        FROM adopter ad
        LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
        LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
        ORDER BY ad.id_adopter, (CASE WHEN i.nik IS NOT NULL THEN 1 ELSE 2 END)
    ),
    adopter_contributions AS (
        SELECT 
            uad.id_adopter,
            uad.nama_adopter,
            uad.tipe_adopter,
            COALESCE(SUM(CASE 
                WHEN a.status_pembayaran = 'Lunas' 
                AND a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year' 
                THEN a.kontribusi_finansial 
                ELSE 0 
            END), 0) as total_kontribusi_setahun,
            COALESCE(SUM(CASE 
                WHEN a.status_pembayaran = 'Lunas' 
                THEN a.kontribusi_finansial 
                ELSE 0 
            END), 0) as total_kontribusi_all_time,
            COUNT(CASE 
                WHEN a.tgl_mulai_adopsi <= CURRENT_DATE 
                AND a.tgl_berhenti_adopsi >= CURRENT_DATE 
                THEN 1 
            END) as jumlah_adopsi_aktif
        FROM unique_adopter_data uad
        LEFT JOIN adopsi a ON uad.id_adopter = a.id_adopter
        GROUP BY uad.id_adopter, uad.nama_adopter, uad.tipe_adopter
    )
    SELECT 
        ac.nama_adopter::TEXT,
        ac.total_kontribusi_setahun::DECIMAL(15,2),
        ac.total_kontribusi_all_time::DECIMAL(15,2),
        ac.jumlah_adopsi_aktif::INTEGER,
        ac.tipe_adopter::TEXT
    FROM adopter_contributions ac
    WHERE ac.total_kontribusi_setahun > 0
    ORDER BY ac.total_kontribusi_setahun DESC, ac.total_kontribusi_all_time DESC, ac.nama_adopter ASC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_adopter_ranking()
RETURNS TEXT AS $$
DECLARE
    top_adopter_name TEXT;
    top_contribution DECIMAL(15,2);
    result_message TEXT;
    adopter_count INTEGER;
    total_updated INTEGER;
BEGIN
    WITH adopter_totals AS (
        SELECT 
            ad.id_adopter,
            COALESCE(SUM(CASE 
                WHEN a.status_pembayaran = 'Lunas' 
                THEN a.kontribusi_finansial 
                ELSE 0 
            END), 0) as new_total
        FROM adopter ad
        LEFT JOIN adopsi a ON ad.id_adopter = a.id_adopter
        GROUP BY ad.id_adopter
    )
    UPDATE adopter 
    SET total_kontribusi = at.new_total
    FROM adopter_totals at
    WHERE adopter.id_adopter = at.id_adopter;
    
    GET DIAGNOSTICS total_updated = ROW_COUNT;
    
    WITH recent_contributors AS (
        SELECT DISTINCT ad.id_adopter
        FROM adopter ad
        INNER JOIN adopsi a ON ad.id_adopter = a.id_adopter
        WHERE a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
        AND a.status_pembayaran = 'Lunas'
        AND a.kontribusi_finansial > 0
    )
    SELECT COUNT(*) INTO adopter_count FROM recent_contributors;
    
    WITH unique_adopter_names AS (
        SELECT DISTINCT ON (ad.id_adopter)
            ad.id_adopter,
            CASE 
                WHEN i.nama IS NOT NULL THEN i.nama
                WHEN o.nama_organisasi IS NOT NULL THEN o.nama_organisasi
                ELSE 'Unknown Adopter'
            END as nama_adopter
        FROM adopter ad
        LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
        LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
        ORDER BY ad.id_adopter, (CASE WHEN i.nik IS NOT NULL THEN 1 ELSE 2 END)
    ),
    top_contributor AS (
        SELECT 
            uan.nama_adopter,
            SUM(a.kontribusi_finansial) as total_kontribusi
        FROM adopsi a
        INNER JOIN unique_adopter_names uan ON a.id_adopter = uan.id_adopter
        WHERE a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
        AND a.status_pembayaran = 'Lunas'
        AND a.kontribusi_finansial > 0
        GROUP BY uan.id_adopter, uan.nama_adopter
        ORDER BY total_kontribusi DESC
        LIMIT 1
    )
    SELECT tc.nama_adopter, tc.total_kontribusi 
    INTO top_adopter_name, top_contribution
    FROM top_contributor tc;
    
    IF top_adopter_name IS NOT NULL AND top_contribution > 0 THEN
        result_message := 'SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, dengan peringkat pertama dengan nama adopter "' || 
                         top_adopter_name || '" berkontribusi sebesar "Rp' || 
                         TO_CHAR(top_contribution, 'FM999,999,999') || '".';
    ELSE
        result_message := 'SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, namun tidak ada kontribusi yang valid dalam setahun terakhir.';
    END IF;
    
    RETURN result_message;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION adopter_ranking_after_kontribusi()
RETURNS TRIGGER AS $$
DECLARE
    affected_adopter_id UUID;
    new_total DECIMAL(15,2);
BEGIN
    IF TG_OP = 'DELETE' THEN
        affected_adopter_id := OLD.id_adopter;
    ELSE
        affected_adopter_id := NEW.id_adopter;
    END IF;
    
    SELECT COALESCE(SUM(CASE 
        WHEN status_pembayaran = 'Lunas' 
        THEN kontribusi_finansial 
        ELSE 0 
    END), 0)
    INTO new_total
    FROM adopsi 
    WHERE id_adopter = affected_adopter_id;
    
    UPDATE adopter 
    SET total_kontribusi = new_total
    WHERE id_adopter = affected_adopter_id;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_adopter_ranking
    AFTER INSERT OR UPDATE OF kontribusi_finansial, status_pembayaran OR DELETE 
    ON adopsi
    FOR EACH ROW
    EXECUTE FUNCTION adopter_ranking_after_kontribusi();

WITH adopter_totals AS (
    SELECT 
        ad.id_adopter,
        COALESCE(SUM(CASE 
            WHEN a.status_pembayaran = 'Lunas' 
            THEN a.kontribusi_finansial 
            ELSE 0 
        END), 0) as new_total
    FROM adopter ad
    LEFT JOIN adopsi a ON ad.id_adopter = a.id_adopter
    GROUP BY ad.id_adopter
)
UPDATE adopter 
SET total_kontribusi = at.new_total
FROM adopter_totals at
WHERE adopter.id_adopter = at.id_adopter;