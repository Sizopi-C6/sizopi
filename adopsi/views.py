from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import logging
import re
import psycopg2

logger = logging.getLogger(__name__)

def get_user_session(request):
    return request.session.get('user')

def get_username_from_session(request):
    user = get_user_session(request)
    return user.get('username') if user else None

def check_adopter_access(request):
    user = get_user_session(request)
    
    if not user:
        return None, None, 'Anda perlu login terlebih dahulu.'
    
    username = user.get('username')
    role = user.get('role')
    
    if not username:
        return None, None, 'Data session tidak valid.'
    
    if role != 'pengunjung':
        return None, None, 'Hanya pengunjung yang dapat mengakses fitur adopsi.'
    
    return username, user, None

def check_admin_access(request):
    user = get_user_session(request)
    
    if not user:
        return None, None, 'Anda perlu login terlebih dahulu.'
    
    username = user.get('username')
    role = user.get('role')
    
    if not username:
        return None, None, 'Data session tidak valid.'
    
    if role != 'staf_admin':
        return None, None, 'Hanya admin yang dapat mengakses fitur ini.'
    
    return username, user, None

def adopsi_redirect(request):
    user = get_user_session(request)
    
    if not user:
        messages.info(request, 'Silakan login untuk mengakses program adopsi.')
        return redirect('/login/')
    
    role = user.get('role')
    username = user.get('username')
    
    print(f"User: {username}, Role: {role}")
    
    if not username or not role:
        messages.error(request, 'Data session tidak valid. Silakan login ulang.')
        return redirect('/login/')
    
    try:
        if role == 'staf_admin':
            return redirect('adopsi:adopsi_admin')
        elif role == 'pengunjung':
            return redirect('adopsi:adopsi_pengunjung')
        elif role in ['dokter_hewan', 'penjaga_hewan', 'pelatih_hewan']:
            messages.info(request, f'Program adopsi khusus untuk admin dan pengunjung. Role Anda: {role}')
            return redirect('/dashboard/')
        else:
            messages.warning(request, f'Role "{role}" tidak memiliki akses ke program adopsi.')
            return redirect('/dashboard/')
            
    except Exception as e:
        logger.error(f"Error in adopsi_redirect: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengakses program adopsi.')
        return redirect('/dashboard/')

def program_adopsi_admin(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    h.url_foto,
                    h.status_kesehatan,
                    h.asal_hewan,
                    h.tanggal_lahir,
                    hab.nama as nama_habitat,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM adopsi a 
                            WHERE a.id_hewan = h.id 
                            AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                            AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                        ) THEN 'Diadopsi'
                        ELSE 'Tidak Diadopsi'
                    END as status_adopsi,
                    -- Data adopsi aktif jika ada
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    a.status_pembayaran,
                    -- Data adopter
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE NULL
                    END as tipe_adopter
                FROM hewan h
                LEFT JOIN habitat hab ON h.nama_habitat = hab.nama
                LEFT JOIN adopsi a ON h.id = a.id_hewan 
                    AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                    AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                LEFT JOIN adopter ad ON a.id_adopter = ad.id_adopter
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                ORDER BY h.name
            """)
            
            rows = cursor.fetchall()
            animals = []
            
            for row in rows:
                animal = dict(zip([column[0] for column in cursor.description], row))
                
                for key, value in animal.items():
                    if isinstance(value, uuid.UUID):
                        animal[key] = str(value)
                    elif isinstance(value, (date, datetime)):
                        animal[key] = value.isoformat() if value else None
                    elif isinstance(value, Decimal):
                        animal[key] = float(value) if value else 0
                
                animals.append(animal)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_hewan,
                    SUM(CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM adopsi a 
                            WHERE a.id_hewan = h.id 
                            AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                            AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                        ) THEN 1 ELSE 0 
                    END) as hewan_diadopsi,
                    COUNT(*) - SUM(CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM adopsi a 
                            WHERE a.id_hewan = h.id 
                            AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                            AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                        ) THEN 1 ELSE 0 
                    END) as hewan_tidak_diadopsi
                FROM hewan h
            """)
            
            stats_row = cursor.fetchone()
            stats = dict(zip([column[0] for column in cursor.description], stats_row))
            
            return render(request, 'adopsi_admin.html', {
                'animals': animals,
                'stats': stats,
                'user': user
            })
            
    except Exception as e:
        logger.error(f"Error in program_adopsi_admin: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data adopsi.')
        return render(request, 'adopsi_admin.html', {
            'animals': [],
            'stats': {'total_hewan': 0, 'hewan_diadopsi': 0, 'hewan_tidak_diadopsi': 0},
            'user': user
        })

def program_adopsi_pengunjung(request):
    username, user, error_msg = check_adopter_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    h.url_foto,
                    h.status_kesehatan,
                    h.nama_habitat,
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    a.status_pembayaran,
                    hab.nama as habitat_name,
                    -- Data adopter
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE 'Unknown'
                    END as tipe_adopter,
                    i.nik,
                    o.npp
                FROM adopsi a
                INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                INNER JOIN hewan h ON a.id_hewan = h.id
                LEFT JOIN habitat hab ON h.nama_habitat = hab.nama
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                WHERE ad.username_adopter = %s
                AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                ORDER BY a.tgl_mulai_adopsi DESC
            """, [username])
            
            rows = cursor.fetchall()
            adopted_animals = []
            
            for row in rows:
                animal = dict(zip([column[0] for column in cursor.description], row))
                animal['id'] = str(animal['id'])
                
                for key, value in animal.items():
                    if isinstance(value, uuid.UUID):
                        animal[key] = str(value)
                    elif isinstance(value, (date, datetime)):
                        animal[key] = value.isoformat() if value else None
                    elif isinstance(value, Decimal):
                        animal[key] = float(value) if value else 0
                
                adopted_animals.append(animal)
        
        return render(request, 'adopsi_pengunjung.html', {
            'adopted_animals': adopted_animals,
            'user': user,
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Error in program_adopsi_pengunjung: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data adopsi.')
        return render(request, 'adopsi_pengunjung.html', {
            'adopted_animals': [],
            'user': user,
            'username': username
        })

def laporan_kondisi_hewan(request):
    animal_id = request.GET.get('animal_id')
    username, user, error_msg = check_adopter_access(request)

    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if not animal_id:
        messages.error(request, 'ID hewan tidak valid.')
        return redirect('adopsi:adopsi_pengunjung')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as verification_count,
                    MIN(a.tgl_mulai_adopsi) as tgl_mulai_adopsi
                FROM adopsi a
                INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                WHERE ad.username_adopter = %s 
                AND a.id_hewan = %s
                AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                AND a.tgl_berhenti_adopsi >= CURRENT_DATE
            """, [username, animal_id])
            
            verification_result = cursor.fetchone()
            verification_count = verification_result[0]
            tgl_mulai_adopsi = verification_result[1]
            
            print(f"DEBUG - Verification count: {verification_count}")
            print(f"DEBUG - Tanggal mulai adopsi: {tgl_mulai_adopsi}")
            
            if verification_count == 0:
                messages.error(request, 'Anda tidak memiliki akses untuk melihat laporan hewan ini.')
                return redirect('adopsi:adopsi_pengunjung')
            
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    h.url_foto,
                    h.status_kesehatan,
                    h.nama_habitat,
                    hab.nama as habitat_name
                FROM hewan h
                LEFT JOIN habitat hab ON h.nama_habitat = hab.nama
                WHERE h.id = %s
            """, [animal_id])
            
            animal_row = cursor.fetchone()
            if not animal_row:
                messages.error(request, 'Hewan tidak ditemukan.')
                return redirect('adopsi:adopsi_pengunjung')
            
            animal = dict(zip([column[0] for column in cursor.description], animal_row))
            
            if isinstance(animal['id'], uuid.UUID):
                animal['id'] = str(animal['id'])
            
            print(f"DEBUG - Animal data: {animal}")
            
            cursor.execute("""
                SELECT 
                    cm.tanggal_pemeriksaan,
                    CONCAT(p.nama_depan, ' ', COALESCE(p.nama_belakang, '')) as nama_dokter,
                    cm.status_kesehatan,
                    cm.diagnosis,
                    cm.pengobatan,
                    cm.catatan_tindak_lanjut
                FROM catatan_medis cm
                INNER JOIN dokter_hewan dh ON cm.username_dh = dh.username_dh
                INNER JOIN pengguna p ON dh.username_dh = p.username
                WHERE cm.id_hewan = %s
                AND cm.tanggal_pemeriksaan >= %s
                ORDER BY cm.tanggal_pemeriksaan DESC
            """, [animal_id, tgl_mulai_adopsi])
            
            medical_records = []
            medical_rows = cursor.fetchall()
            
            for row in medical_rows:
                record = dict(zip([column[0] for column in cursor.description], row))
                
                if isinstance(record['tanggal_pemeriksaan'], date):
                    record['tanggal_pemeriksaan'] = record['tanggal_pemeriksaan']
                
                medical_records.append(record)
            
            print(f"DEBUG - Medical records count: {len(medical_records)}")
            print(f"DEBUG - Filtered from date: {tgl_mulai_adopsi}")
            
            sehat_count = sum(1 for record in medical_records if record['status_kesehatan'] == 'Sehat')
        
        return render(request, 'laporan_kondisi_hewan.html', {
            'animal': animal,
            'medical_records': medical_records,
            'user': user,
            'tgl_mulai_adopsi': tgl_mulai_adopsi,
            'sehat_count': sehat_count
        })
        
    except Exception as e:
        logger.error(f"Error in laporan_kondisi_hewan: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil laporan kondisi hewan.')
        return redirect('adopsi:adopsi_pengunjung')

def sertifikat_adopsi(request):
    animal_id = request.GET.get('animal_id')
    username, user, error_msg = check_adopter_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if not animal_id:
        messages.error(request, 'ID hewan tidak valid.')
        return redirect('adopsi:adopsi_pengunjung')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    -- Data adopter
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE 'Unknown'
                    END as tipe_adopter
                FROM adopsi a
                INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                INNER JOIN hewan h ON a.id_hewan = h.id
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                WHERE ad.username_adopter = %s 
                AND a.id_hewan = %s
                AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                AND a.tgl_berhenti_adopsi >= CURRENT_DATE
            """, [username, animal_id])
            
            row = cursor.fetchone()
            if not row:
                messages.error(request, 'Data adopsi tidak ditemukan.')
                return redirect('adopsi:adopsi_pengunjung')
            
            adoption_data = dict(zip([column[0] for column in cursor.description], row))
            
            for key, value in adoption_data.items():
                if isinstance(value, uuid.UUID):
                    adoption_data[key] = str(value)
                elif isinstance(value, (date, datetime)):
                    adoption_data[key] = value.isoformat() if value else None
                elif isinstance(value, Decimal):
                    adoption_data[key] = float(value) if value else 0
        
        return render(request, 'sertifikat_adopsi.html', {
            'adoption_data': adoption_data,
            'user': user
        })
        
    except Exception as e:
        logger.error(f"Error in sertifikat_adopsi: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil sertifikat adopsi.')
        return redirect('adopsi:adopsi_pengunjung')

def perpanjang_periode(request):
    animal_id = request.GET.get('animal_id')
    username, user, error_msg = check_adopter_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method == 'POST':
        return process_perpanjang_adopsi(request)
    
    if not animal_id:
        messages.error(request, 'ID hewan tidak valid.')
        return redirect('adopsi:adopsi_pengunjung')
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    -- Data adopter
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE 'Unknown'
                    END as tipe_adopter,
                    i.nik,
                    i.nama as nama_individu,
                    o.npp,
                    o.nama_organisasi,
                    -- Data user dari session (akan diambil dari user parameter)
                    CONCAT(p.nama_depan, ' ', COALESCE(p.nama_belakang, '')) as nama_lengkap,
                    p.no_telepon,
                    pg.alamat
                FROM adopsi a
                INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                INNER JOIN hewan h ON a.id_hewan = h.id
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                INNER JOIN pengunjung pg ON ad.username_adopter = pg.username_p
                INNER JOIN pengguna p ON pg.username_p = p.username
                WHERE ad.username_adopter = %s 
                AND a.id_hewan = %s
                AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                AND a.tgl_berhenti_adopsi >= CURRENT_DATE
            """, [username, animal_id])
            
            row = cursor.fetchone()
            
            if not row:
                messages.error(request, 'Data adopsi tidak ditemukan.')
                return redirect('adopsi:adopsi_pengunjung')
            
            adoption_data = dict(zip([column[0] for column in cursor.description], row))
            
            for key, value in adoption_data.items():
                if isinstance(value, uuid.UUID):
                    adoption_data[key] = str(value)
                elif isinstance(value, (date, datetime)):
                    adoption_data[key] = value.isoformat() if value else None
                elif isinstance(value, Decimal):
                    adoption_data[key] = float(value) if value else 0
            
            adoption_data.update({
                'user_nama_depan': user.get('nama_depan', ''),
                'user_nama_tengah': user.get('nama_tengah', ''),
                'user_nama_belakang': user.get('nama_belakang', ''),
                'user_email': user.get('email', ''),
                'user_no_telepon': user.get('no_telepon', '')
            })
        
        return render(request, 'perpanjang_periode.html', {
            'adoption_data': adoption_data,
            'user': user
        })
        
    except Exception as e:        
        logger.error(f"Error in perpanjang_periode: {str(e)}")
        messages.error(request, f'Terjadi kesalahan saat mengambil data perpanjang adopsi: {str(e)}')
        return redirect('adopsi:adopsi_pengunjung')

def process_perpanjang_adopsi(request):
    username, user, error_msg = check_adopter_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method != 'POST':
        return redirect('adopsi:adopsi_pengunjung')
        
    animal_id = request.POST.get('animal_id')
    periode = request.POST.get('periode')
    nominal = request.POST.get('nominal', '').replace('.', '').replace(',', '')
 
    if not all([animal_id, periode, nominal]):
        missing_fields = []
        if not animal_id: missing_fields.append('animal_id')
        if not periode: missing_fields.append('periode')
        if not nominal: missing_fields.append('nominal')
        
        messages.error(request, f'Field yang hilang: {", ".join(missing_fields)}')
        return redirect('adopsi:adopsi_pengunjung')
    
    try:
        nominal_value = int(nominal)
        periode_months = int(periode)

        if nominal_value <= 0:
            messages.error(request, 'Nominal kontribusi harus lebih besar dari 0!')
            return redirect('adopsi:adopsi_pengunjung')
            
        if periode_months not in [3, 6, 12]:
            messages.error(request, 'Periode adopsi tidak valid!')
            return redirect('adopsi:adopsi_pengunjung')
        
        with transaction.atomic():
            with connection.cursor() as cursor:                
                cursor.execute("""
                    SELECT 
                        a.id_adopter, 
                        a.tgl_berhenti_adopsi,
                        a.kontribusi_finansial,
                        h.name as nama_hewan
                    FROM adopsi a
                    INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                    INNER JOIN hewan h ON a.id_hewan = h.id
                    WHERE ad.username_adopter = %s 
                    AND a.id_hewan = %s
                    AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                    AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                """, [username, animal_id])
                
                row = cursor.fetchone()
                
                if not row:
                    print("DEBUG - No adoption data found")
                    messages.error(request, 'Data adopsi tidak ditemukan atau sudah tidak aktif!')
                    return redirect('adopsi:adopsi_pengunjung')
                
                adopter_id, current_end_date, current_contribution, animal_name = row
                
                if periode_months == 3:
                    new_end_date = current_end_date + timedelta(days=90)
                elif periode_months == 6:
                    new_end_date = current_end_date + timedelta(days=180)
                else: 
                    new_end_date = current_end_date + timedelta(days=365)
                
                cursor.execute("""
                    UPDATE adopsi 
                    SET tgl_berhenti_adopsi = %s,
                        kontribusi_finansial = kontribusi_finansial + %s
                    WHERE id_adopter = %s 
                    AND id_hewan = %s
                    AND tgl_mulai_adopsi <= CURRENT_DATE 
                    AND tgl_berhenti_adopsi >= CURRENT_DATE
                """, [new_end_date, nominal_value, adopter_id, animal_id])
                
                affected_rows = cursor.rowcount
                
                if affected_rows == 0:
                    messages.error(request, 'Tidak ada data yang diupdate')
                    return redirect('adopsi:adopsi_pengunjung')
                
                notices = capture_database_notices(cursor)
                
                if cursor.rowcount > 0:
                    for notice in notices:
                        if 'SUKSES:' in notice:
                            clean_message = notice.replace('SUKSES:', '').strip()
                            messages.success(request, f'{clean_message}')

                return redirect('adopsi:adopsi_pengunjung')
                
    except ValueError as ve:
        messages.error(request, f'Format data tidak valid: {str(ve)}')
        return redirect('adopsi:adopsi_pengunjung')
        
    except Exception as e:        
        logger.error(f"Error in process_perpanjang_adopsi: {str(e)}")
        messages.error(request, f'Terjadi kesalahan sistem: {str(e)}')
        return redirect('adopsi:adopsi_pengunjung')        

def berhenti_adopsi(request):
    username, user, error_msg = check_adopter_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method != 'POST':
        return redirect('adopsi:adopsi_pengunjung')
        
    animal_id = request.POST.get('animal_id')
    
    if not animal_id:
        messages.error(request, 'ID hewan tidak valid.')
        return redirect('adopsi:adopsi_pengunjung')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.status_pembayaran, h.name
                    FROM adopsi a
                    INNER JOIN adopter ad ON a.id_adopter = ad.id_adopter
                    INNER JOIN hewan h ON a.id_hewan = h.id
                    WHERE ad.username_adopter = %s 
                    AND a.id_hewan = %s
                    AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                    AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                """, [username, animal_id])
                
                row = cursor.fetchone()
                if not row:
                    messages.error(request, 'Data adopsi tidak ditemukan!')
                    return redirect('adopsi:adopsi_pengunjung')
                
                status_pembayaran, animal_name = row
                
                if status_pembayaran == 'Tertunda':
                    messages.warning(request, 'Perhatian: Status pembayaran adopsi ini masih tertunda.')
                
                cursor.execute("""
                    UPDATE adopsi 
                    SET tgl_berhenti_adopsi = CURRENT_DATE 
                    WHERE id_adopter IN (
                        SELECT id_adopter FROM adopter WHERE username_adopter = %s
                    )
                    AND id_hewan = %s
                    AND tgl_mulai_adopsi <= CURRENT_DATE 
                    AND tgl_berhenti_adopsi >= CURRENT_DATE
                """, [username, animal_id])
                
                notices = capture_database_notices(cursor)
                
                if cursor.rowcount > 0:
                    for notice in notices:
                        if 'SUKSES:' in notice:
                            clean_message = notice.replace('SUKSES:', '').strip()
                            messages.success(request, f'{clean_message}')
                    
                    messages.success(request, f'Adopsi untuk {animal_name} berhasil dihentikan')
                else:
                    messages.error(request, 'Tidak ada adopsi aktif yang dapat dihentikan!')
                    
    except Exception as e:
        logger.error(f"Error in berhenti_adopsi: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghentikan adopsi!')
    
    return redirect('adopsi:adopsi_pengunjung')

def get_animal_adoption_detail(request, animal_id):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        return JsonResponse({
            'success': False,
            'message': error_msg
        })
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.name as nama_hewan,
                    h.species,
                    h.url_foto,
                    h.status_kesehatan,
                    -- Data adopsi aktif
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    a.status_pembayaran,
                    -- Data adopter
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE NULL
                    END as tipe_adopter,
                    i.nik,
                    o.npp,
                    -- Data pengguna adopter
                    p.email as email_adopter,
                    p.no_telepon as telepon_adopter
                FROM hewan h
                LEFT JOIN adopsi a ON h.id = a.id_hewan 
                    AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                    AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                LEFT JOIN adopter ad ON a.id_adopter = ad.id_adopter
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                LEFT JOIN pengunjung pg ON ad.username_adopter = pg.username_p
                LEFT JOIN pengguna p ON pg.username_p = p.username
                WHERE h.id = %s
            """, [animal_id])
            
            row = cursor.fetchone()
            if row:
                animal_detail = dict(zip([column[0] for column in cursor.description], row))
                
                for key, value in animal_detail.items():
                    if isinstance(value, uuid.UUID):
                        animal_detail[key] = str(value)
                    elif isinstance(value, (date, datetime)):
                        animal_detail[key] = value.isoformat() if value else None
                    elif isinstance(value, Decimal):
                        animal_detail[key] = float(value) if value else 0
                
                return JsonResponse({
                    'success': True,
                    'data': animal_detail
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Hewan tidak ditemukan'
                })
                
    except Exception as e:
        logger.error(f"Error in get_animal_adoption_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil detail adopsi'
        })

def update_adoption_status(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method == 'POST':
        try:
            animal_id = request.POST.get('animal_id')
            status_pembayaran = request.POST.get('status_pembayaran')
            
            if not animal_id or not status_pembayaran:
                messages.error(request, 'Data tidak lengkap!')
                return redirect('adopsi:adopsi_admin')
            
            if status_pembayaran not in ['Lunas', 'Tertunda']:
                messages.error(request, 'Status pembayaran tidak valid!')
                return redirect('adopsi:adopsi_admin')
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE adopsi 
                        SET status_pembayaran = %s 
                        WHERE id_hewan = %s 
                        AND tgl_mulai_adopsi <= CURRENT_DATE 
                        AND tgl_berhenti_adopsi >= CURRENT_DATE
                    """, [status_pembayaran, animal_id])
                    
                    notices = capture_database_notices(cursor)
                    
                    if cursor.rowcount > 0:
                        for notice in notices:
                            if 'SUKSES:' in notice:
                                clean_message = notice.replace('SUKSES:', '').strip()
                                messages.success(request, f'{clean_message}')
                        
                        messages.success(request, f'Status pembayaran berhasil diubah menjadi {status_pembayaran}!')
                    else:
                        messages.error(request, 'Tidak ada adopsi aktif untuk hewan ini!')
            
        except Exception as e:
            logger.error(f"Error in update_adoption_status: {str(e)}")
            messages.error(request, 'Terjadi kesalahan saat mengupdate status!')
    
    return redirect('adopsi:adopsi_admin')

def terminate_adoption(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method == 'POST':
        try:
            animal_id = request.POST.get('animal_id')
            
            if not animal_id:
                messages.error(request, 'ID hewan tidak valid!')
                return redirect('adopsi:adopsi_admin')
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE adopsi 
                        SET tgl_berhenti_adopsi = CURRENT_DATE 
                        WHERE id_hewan = %s 
                        AND tgl_mulai_adopsi <= CURRENT_DATE 
                        AND tgl_berhenti_adopsi >= CURRENT_DATE
                    """, [animal_id])
                    
                    notices = capture_database_notices(cursor)
                    
                    if cursor.rowcount > 0:
                        for notice in notices:
                            if 'SUKSES:' in notice:
                                clean_message = notice.replace('SUKSES:', '').strip()
                                messages.success(request, f'✅ {clean_message}')
                        
                        cursor.execute("""
                            SELECT name FROM hewan WHERE id = %s
                        """, [animal_id])
                        
                        animal_name = cursor.fetchone()
                        if animal_name:
                            messages.success(request, f'Adopsi untuk {animal_name[0]} berhasil dihentikan!')
                        else:
                            messages.success(request, 'Adopsi berhasil dihentikan!')
                    else:
                        messages.error(request, 'Tidak ada adopsi aktif untuk hewan ini!')
            
        except Exception as e:
            logger.error(f"Error in terminate_adoption: {str(e)}")
            messages.error(request, 'Terjadi kesalahan saat menghentikan adopsi!')
    
    return redirect('adopsi:adopsi_admin')

def form_adopsi_hewan(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    animal_id = request.GET.get('animal_id')
    selected_animal = None
    
    try:
        with connection.cursor() as cursor:
            if animal_id:
                cursor.execute("""
                    SELECT h.id, h.name, h.species, h.url_foto, h.status_kesehatan
                    FROM hewan h
                    WHERE h.id = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM adopsi a 
                        WHERE a.id_hewan = h.id 
                        AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                        AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                    )
                """, [animal_id])
                
                animal_row = cursor.fetchone()
                if animal_row:
                    selected_animal = dict(zip([column[0] for column in cursor.description], animal_row))
                    if isinstance(selected_animal['id'], uuid.UUID):
                        selected_animal['id'] = str(selected_animal['id'])
                else:
                    messages.error(request, 'Hewan tidak ditemukan atau sudah diadopsi!')
                    return redirect('adopsi:adopsi_admin')
            
            cursor.execute("""
                SELECT 
                    p.username,
                    p.nama_depan,
                    p.nama_belakang,
                    p.no_telepon,
                    p.email,
                    pg.alamat
                FROM pengguna p
                INNER JOIN pengunjung pg ON p.username = pg.username_p
                ORDER BY p.nama_depan, p.nama_belakang
            """)
            
            pengunjung_rows = cursor.fetchall()
            pengunjung_list = []
            
            for row in pengunjung_rows:
                pengunjung = dict(zip([column[0] for column in cursor.description], row))
                pengunjung_list.append(pengunjung)
            
            return render(request, 'form_adopsi_hewan.html', {
                'selected_animal': selected_animal,
                'pengunjung_list': pengunjung_list,
                'user': user
            })
            
    except Exception as e:
        logger.error(f"Error in form_adopsi_hewan: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data.')
        return render(request, 'form_adopsi_hewan.html', {
            'selected_animal': None,
            'pengunjung_list': [],
            'user': user
        })

def verify_adopter_account(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        return JsonResponse({
            'success': False,
            'message': error_msg
        })
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Username harus diisi!'
            })
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.username,
                        p.nama_depan,
                        p.nama_tengah, 
                        p.nama_belakang,
                        p.no_telepon,
                        p.email,
                        pg.alamat,
                        pg.tgl_lahir
                    FROM pengguna p
                    INNER JOIN pengunjung pg ON p.username = pg.username_p
                    WHERE p.username = %s
                """, [username])
                
                row = cursor.fetchone()
                if not row:
                    return JsonResponse({
                        'success': False,
                        'message': 'Username tidak ditemukan atau bukan akun pengunjung!'
                    })
                
                user_data = dict(zip([column[0] for column in cursor.description], row))
                
                if user_data['tgl_lahir']:
                    user_data['tgl_lahir'] = user_data['tgl_lahir'].isoformat()
                
                cursor.execute("""
                    SELECT id_adopter FROM adopter WHERE username_adopter = %s
                """, [username])
                
                adopter_row = cursor.fetchone()
                
                if adopter_row:
                    adopter_id = adopter_row[0]
                    
                    cursor.execute("""
                        SELECT nik, nama FROM individu WHERE id_adopter = %s
                    """, [adopter_id])
                    
                    individual_row = cursor.fetchone()
                    if individual_row:
                        user_data['existing_nik'] = individual_row[0]
                        user_data['existing_individual_name'] = individual_row[1]
                    
                    cursor.execute("""
                        SELECT npp, nama_organisasi FROM organisasi WHERE id_adopter = %s
                    """, [adopter_id])
                    
                    organization_row = cursor.fetchone()
                    if organization_row:
                        user_data['existing_npp'] = organization_row[0]
                        user_data['existing_org_name'] = organization_row[1]
                
                return JsonResponse({
                    'success': True,
                    'data': user_data
                })
                    
        except Exception as e:
            logger.error(f"Error in verify_adopter_account: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Terjadi kesalahan saat verifikasi akun!'
            })
            
def submit_adoption_form(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method == 'POST':
        try:
            adopter_username = request.POST.get('adopter_username', '').strip()
            animal_id = request.POST.get('animal_id', '')
            tipe_adopter = request.POST.get('tipe_adopter', '')
            nominal = request.POST.get('nominal', '').replace('.', '').replace(',', '')
            periode = request.POST.get('periode', '')
            
            if not all([adopter_username, animal_id, tipe_adopter, nominal, periode]):
                messages.error(request, 'Semua field wajib harus diisi!')
                return redirect(f'/adopsi/form/?animal_id={animal_id}')
            
            try:
                nominal_value = int(nominal)
                if nominal_value < 100000:
                    messages.error(request, 'Nominal kontribusi minimal Rp 100.000!')
                    return redirect(f'/adopsi/form/?animal_id={animal_id}')
            except ValueError:
                messages.error(request, 'Format nominal tidak valid!')
                return redirect(f'/adopsi/form/?animal_id={animal_id}')
            
            try:
                periode_months = int(periode)
                if periode_months not in [3, 6, 12]:
                    messages.error(request, 'Periode adopsi tidak valid!')
                    return redirect(f'/adopsi/form/?animal_id={animal_id}')
            except ValueError:
                messages.error(request, 'Format periode tidak valid!')
                return redirect(f'/adopsi/form/?animal_id={animal_id}')
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT h.name FROM hewan h
                        WHERE h.id = %s
                        AND NOT EXISTS (
                            SELECT 1 FROM adopsi a 
                            WHERE a.id_hewan = h.id 
                            AND a.tgl_mulai_adopsi <= CURRENT_DATE 
                            AND a.tgl_berhenti_adopsi >= CURRENT_DATE
                        )
                    """, [animal_id])
                    
                    hewan_row = cursor.fetchone()
                    if not hewan_row:
                        messages.error(request, 'Hewan tidak tersedia atau sudah diadopsi!')
                        return redirect('adopsi:adopsi_admin')
                    
                    nama_hewan = hewan_row[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM pengunjung 
                        WHERE username_p = %s
                    """, [adopter_username])
                    
                    if cursor.fetchone()[0] == 0:
                        messages.error(request, 'Pengunjung tidak ditemukan!')
                        return redirect(f'/adopsi/form/?animal_id={animal_id}')
                    
                    cursor.execute("""
                        SELECT id_adopter FROM adopter WHERE username_adopter = %s
                    """, [adopter_username])
                    
                    adopter_row = cursor.fetchone()
                    
                    if adopter_row:
                        adopter_id = adopter_row[0]
                        cursor.execute("""
                            UPDATE adopter 
                            SET total_kontribusi = total_kontribusi + %s 
                            WHERE id_adopter = %s
                        """, [nominal_value, adopter_id])
                    else:
                        adopter_id = str(uuid.uuid4())
                        cursor.execute("""
                            INSERT INTO adopter (id_adopter, username_adopter, total_kontribusi)
                            VALUES (%s, %s, %s)
                        """, [adopter_id, adopter_username, nominal_value])
                    
                    if tipe_adopter == 'individu':
                        cursor.execute("""
                            SELECT nik, nama FROM individu WHERE id_adopter = %s
                        """, [adopter_id])
                        
                        existing_individual = cursor.fetchone()
                        
                        if existing_individual:
                            nama_adopter = existing_individual[1]
                        else:
                            
                            nik = request.POST.get('nik', '').strip()
                            
                            if not nik:
                                messages.error(request, 'NIK harus diisi untuk adopter individu!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                            
                            if len(nik) != 16 or not nik.isdigit():
                                messages.error(request, 'NIK harus 16 digit angka!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                            
                            cursor.execute("""
                                SELECT COUNT(*) FROM individu 
                                WHERE nik = %s AND id_adopter != %s
                            """, [nik, adopter_id])
                            
                            if cursor.fetchone()[0] > 0:
                                messages.error(request, 'NIK sudah terdaftar untuk adopter lain!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                            
                            cursor.execute("""
                                SELECT nama_depan, nama_belakang FROM pengguna 
                                WHERE username = %s
                            """, [adopter_username])
                            
                            nama_row = cursor.fetchone()
                            if nama_row:
                                nama_lengkap = f"{nama_row[0]} {nama_row[1] or ''}".strip()
                            else:
                                nama_lengkap = "Unknown"
                            
                            cursor.execute("""
                                INSERT INTO individu (nik, nama, id_adopter)
                                VALUES (%s, %s, %s)
                            """, [nik, nama_lengkap, adopter_id])
                            
                            nama_adopter = nama_lengkap
                        
                    elif tipe_adopter == 'organisasi':
                        cursor.execute("""
                            SELECT npp, nama_organisasi FROM organisasi WHERE id_adopter = %s
                        """, [adopter_id])
                        
                        existing_organization = cursor.fetchone()
                        
                        if existing_organization:
                            nama_adopter = existing_organization[1]
                        else:
                            nama_organisasi = request.POST.get('nama_organisasi', '').strip()
                            npp = request.POST.get('npp', '').strip()
                            
                            if not nama_organisasi or not npp:
                                messages.error(request, 'Nama organisasi dan NPP harus diisi!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                                
                            if len(npp) != 8 or not npp.isdigit():
                                messages.error(request, 'NPP harus 8 digit angka!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                            
                            cursor.execute("""
                                SELECT COUNT(*) FROM organisasi 
                                WHERE npp = %s AND id_adopter != %s
                            """, [npp, adopter_id])
                            
                            if cursor.fetchone()[0] > 0:
                                messages.error(request, 'NPP sudah terdaftar untuk adopter lain!')
                                return redirect(f'/adopsi/form/?animal_id={animal_id}')
                            
                            cursor.execute("""
                                INSERT INTO organisasi (npp, nama_organisasi, id_adopter)
                                VALUES (%s, %s, %s)
                            """, [npp, nama_organisasi, adopter_id])
                            
                            nama_adopter = nama_organisasi
                    
                    tgl_mulai = date.today()
                    
                    if periode_months == 3:
                        tgl_berhenti = tgl_mulai + timedelta(days=90)
                    elif periode_months == 6:
                        tgl_berhenti = tgl_mulai + timedelta(days=180)
                    else:
                        tgl_berhenti = tgl_mulai + timedelta(days=365)
                    
                    cursor.execute("""
                        INSERT INTO adopsi (id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [adopter_id, animal_id, 'Tertunda', tgl_mulai, tgl_berhenti, nominal_value])
                    
                    notices = capture_database_notices(cursor)
                    
                    for notice in notices:
                        if 'SUKSES:' in notice:
                            clean_message = notice.replace('SUKSES:', '').strip()
                            messages.success(request, f'{clean_message}')
                    
                    messages.success(request, f'Adopsi {nama_hewan} oleh {nama_adopter} berhasil didaftarkan dengan kontribusi Rp {nominal_value:,} untuk periode {periode_months} bulan!')
                    return redirect('adopsi:adopsi_admin')
                    
        except Exception as e:
            logger.error(f"Error in submit_adoption_form: {str(e)}")
            messages.error(request, f'Terjadi kesalahan saat menyimpan data adopsi: {str(e)}')
            
            animal_id = request.POST.get('animal_id', '')
            if animal_id:
                return redirect(f'/adopsi/form/?animal_id={animal_id}')
    
    return redirect('adopsi:adopsi_admin')

def daftar_adopter(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    SUM(CASE WHEN a.status_pembayaran = 'Lunas' THEN a.kontribusi_finansial ELSE 0 END) as total_kontribusi_setahun
                FROM adopter ad
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                LEFT JOIN adopsi a ON ad.id_adopter = a.id_adopter
                WHERE a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
                AND a.status_pembayaran = 'Lunas'
                GROUP BY ad.id_adopter, i.nama, o.nama_organisasi
                HAVING SUM(CASE WHEN a.status_pembayaran = 'Lunas' THEN a.kontribusi_finansial ELSE 0 END) > 0
                ORDER BY total_kontribusi_setahun DESC
                LIMIT 5
            """)
            
            top_contributors = []
            for row in cursor.fetchall():
                contributor = dict(zip([column[0] for column in cursor.description], row))
                if isinstance(contributor['total_kontribusi_setahun'], Decimal):
                    contributor['total_kontribusi_setahun'] = float(contributor['total_kontribusi_setahun'])
                top_contributors.append(contributor)
            
            cursor.execute("""
                SELECT 
                    ad.id_adopter,
                    i.nama as nama_adopter,
                    i.nik,
                    -- Total kontribusi dari semua adopsi dengan status Lunas
                    COALESCE(SUM(CASE WHEN a.status_pembayaran = 'Lunas' THEN a.kontribusi_finansial ELSE 0 END), 0) as total_kontribusi,
                    -- Cek apakah ada adopsi aktif
                    COUNT(CASE WHEN a.tgl_mulai_adopsi <= CURRENT_DATE AND a.tgl_berhenti_adopsi >= CURRENT_DATE THEN 1 END) as adopsi_aktif_count,
                    -- Data kontak dari pengguna
                    p.no_telepon,
                    pg.alamat
                FROM adopter ad
                INNER JOIN individu i ON ad.id_adopter = i.id_adopter
                INNER JOIN pengunjung pg ON ad.username_adopter = pg.username_p
                INNER JOIN pengguna p ON pg.username_p = p.username
                LEFT JOIN adopsi a ON ad.id_adopter = a.id_adopter
                GROUP BY ad.id_adopter, i.nama, i.nik, p.no_telepon, pg.alamat
                ORDER BY total_kontribusi DESC
            """)
            
            adopter_individu = []
            for row in cursor.fetchall():
                adopter = dict(zip([column[0] for column in cursor.description], row))
                
                if isinstance(adopter['id_adopter'], uuid.UUID):
                    adopter['id_adopter'] = str(adopter['id_adopter'])
                if isinstance(adopter['total_kontribusi'], Decimal):
                    adopter['total_kontribusi'] = float(adopter['total_kontribusi'])
                
                adopter['dapat_dihapus'] = adopter['adopsi_aktif_count'] == 0
                
                adopter_individu.append(adopter)
            
            cursor.execute("""
                SELECT 
                    ad.id_adopter,
                    o.nama_organisasi as nama_adopter,
                    o.npp,
                    -- Total kontribusi dari semua adopsi dengan status Lunas
                    COALESCE(SUM(CASE WHEN a.status_pembayaran = 'Lunas' THEN a.kontribusi_finansial ELSE 0 END), 0) as total_kontribusi,
                    -- Cek apakah ada adopsi aktif
                    COUNT(CASE WHEN a.tgl_mulai_adopsi <= CURRENT_DATE AND a.tgl_berhenti_adopsi >= CURRENT_DATE THEN 1 END) as adopsi_aktif_count,
                    -- Data kontak dari pengguna
                    p.no_telepon,
                    pg.alamat
                FROM adopter ad
                INNER JOIN organisasi o ON ad.id_adopter = o.id_adopter
                INNER JOIN pengunjung pg ON ad.username_adopter = pg.username_p
                INNER JOIN pengguna p ON pg.username_p = p.username
                LEFT JOIN adopsi a ON ad.id_adopter = a.id_adopter
                GROUP BY ad.id_adopter, o.nama_organisasi, o.npp, p.no_telepon, pg.alamat
                ORDER BY total_kontribusi DESC
            """)
            
            adopter_organisasi = []
            for row in cursor.fetchall():
                adopter = dict(zip([column[0] for column in cursor.description], row))
                
                if isinstance(adopter['id_adopter'], uuid.UUID):
                    adopter['id_adopter'] = str(adopter['id_adopter'])
                if isinstance(adopter['total_kontribusi'], Decimal):
                    adopter['total_kontribusi'] = float(adopter['total_kontribusi'])
                
                adopter['dapat_dihapus'] = adopter['adopsi_aktif_count'] == 0
                
                adopter_organisasi.append(adopter)
            
            return render(request, 'daftar_adopter.html', {
                'top_contributors': top_contributors,
                'adopter_individu': adopter_individu,
                'adopter_organisasi': adopter_organisasi,
                'user': user
            })
            
    except Exception as e:
        logger.error(f"Error in daftar_adopter: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data adopter.')
        return render(request, 'daftar_adopter.html', {
            'top_contributors': [],
            'adopter_individu': [],
            'adopter_organisasi': [],
            'user': user
        })

def riwayat_adopter(request, adopter_id):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    try:
        with connection.cursor() as cursor:            
            cursor.execute("""
                SELECT 
                    ad.id_adopter,
                    ad.username_adopter,
                    COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                    CASE 
                        WHEN i.nik IS NOT NULL THEN 'Individu'
                        WHEN o.npp IS NOT NULL THEN 'Organisasi'
                        ELSE 'Unknown'
                    END as tipe_adopter,
                    i.nik,
                    o.npp
                FROM adopter ad
                LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                WHERE ad.id_adopter = %s
            """, [adopter_id])
            
            adopter_row = cursor.fetchone()
            if not adopter_row:
                messages.error(request, 'Data adopter tidak ditemukan.')
                return redirect('adopsi:daftar_adopter')
            
            adopter_data = dict(zip([column[0] for column in cursor.description], adopter_row))
            
            if isinstance(adopter_data['id_adopter'], uuid.UUID):
                adopter_data['id_adopter'] = str(adopter_data['id_adopter'])
            
            cursor.execute("""
                SELECT 
                    p.no_telepon,
                    p.email,
                    pg.alamat,
                        CONCAT(p.nama_depan, ' ', 
                            CASE WHEN p.nama_tengah IS NOT NULL THEN CONCAT(p.nama_tengah, ' ') ELSE '' END,
                            p.nama_belakang) as nama_lengkap
                FROM adopter ad
                INNER JOIN pengunjung pg ON ad.username_adopter = pg.username_p
                INNER JOIN pengguna p ON pg.username_p = p.username
                WHERE ad.id_adopter = %s
            """, [adopter_id])
            
            contact_row = cursor.fetchone()
            if contact_row:
                contact_data = dict(zip([column[0] for column in cursor.description], contact_row))
                adopter_data.update(contact_data)
            
            cursor.execute("""
                SELECT 
                    h.id as id_hewan,
                    h.name as nama_hewan,
                    h.species as jenis_hewan,
                    a.tgl_mulai_adopsi,
                    a.tgl_berhenti_adopsi,
                    a.kontribusi_finansial,
                    a.status_pembayaran
                FROM adopsi a
                INNER JOIN hewan h ON a.id_hewan = h.id
                WHERE a.id_adopter = %s
                ORDER BY a.tgl_mulai_adopsi DESC
            """, [adopter_id])
            
            riwayat_adopsi = []
            for row in cursor.fetchall():
                adopsi = dict(zip([column[0] for column in cursor.description], row))
                
                if isinstance(adopsi['id_hewan'], uuid.UUID):
                    adopsi['id_hewan'] = str(adopsi['id_hewan'])
                if isinstance(adopsi['kontribusi_finansial'], Decimal):
                    adopsi['kontribusi_finansial'] = float(adopsi['kontribusi_finansial'])
                
                today = date.today()
                if adopsi['tgl_mulai_adopsi'] <= today <= adopsi['tgl_berhenti_adopsi']:
                    adopsi['status_adopsi'] = 'Sedang Berlangsung'
                elif adopsi['tgl_berhenti_adopsi'] < today:
                    adopsi['status_adopsi'] = 'Selesai'
                else:
                    adopsi['status_adopsi'] = 'Belum Dimulai'
                
                adopsi['dapat_dihapus'] = (adopsi['status_adopsi'] == 'Selesai' and 
                                        adopsi['status_pembayaran'] == 'Lunas')
                
                riwayat_adopsi.append(adopsi)
            
            total_kontribusi_lunas = 0
            for adopsi in riwayat_adopsi:
                if adopsi['status_pembayaran'] == 'Lunas':
                    total_kontribusi_lunas += adopsi['kontribusi_finansial']
            
            return render(request, 'riwayat_adopter.html', {
                'adopter_data': adopter_data,
                'riwayat_adopsi': riwayat_adopsi,
                'total_kontribusi_lunas': total_kontribusi_lunas,
                'user': user
            })
            
    except Exception as e:
        logger.error(f"Error in riwayat_adopter: {str(e)}")        
        messages.error(request, f'Terjadi kesalahan saat mengambil riwayat adopsi: {str(e)}')
        return redirect('adopsi:daftar_adopter')

def delete_riwayat_adopsi(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method != 'POST':
        return redirect('adopsi:daftar_adopter')
    
    adopter_id = request.POST.get('adopter_id')
    id_hewan = request.POST.get('id_hewan')
    tgl_mulai_adopsi = request.POST.get('tgl_mulai_adopsi')
    
    if not all([adopter_id, id_hewan, tgl_mulai_adopsi]):
        messages.error(request, 'Data tidak lengkap.')
        return redirect('adopsi:daftar_adopter')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        h.name as nama_hewan,
                        a.tgl_berhenti_adopsi,
                        a.status_pembayaran
                    FROM adopsi a
                    INNER JOIN hewan h ON a.id_hewan = h.id
                    WHERE a.id_adopter = %s 
                    AND a.id_hewan = %s 
                    AND a.tgl_mulai_adopsi = %s
                """, [adopter_id, id_hewan, tgl_mulai_adopsi])
                
                result = cursor.fetchone()
                if not result:
                    messages.error(request, 'Data adopsi tidak ditemukan!')
                    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')
                
                nama_hewan, tgl_berhenti, status_pembayaran = result
                
                today = date.today()
                if tgl_berhenti >= today:
                    messages.error(request, 'Tidak dapat menghapus adopsi yang masih aktif!')
                    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')
                
                cursor.execute("""
                    DELETE FROM adopsi 
                    WHERE id_adopter = %s 
                    AND id_hewan = %s 
                    AND tgl_mulai_adopsi = %s
                """, [adopter_id, id_hewan, tgl_mulai_adopsi])
                
                notices = capture_database_notices(cursor)
                
                if cursor.rowcount > 0:
                    for notice in notices:
                        if 'SUKSES:' in notice:
                            clean_message = notice.replace('SUKSES:', '').strip()
                            messages.success(request, f'{clean_message}')
                    
                    messages.success(request, f'Riwayat adopsi {nama_hewan} berhasil dihapus!')
                else:
                    messages.error(request, 'Gagal menghapus riwayat adopsi!')
                    
    except Exception as e:
        logger.error(f"Error in delete_riwayat_adopsi: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus riwayat adopsi!')
    
    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')


def delete_adopter(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method != 'POST':
        return redirect('adopsi:daftar_adopter')
    
    adopter_id = request.POST.get('adopter_id')
    
    if not adopter_id:
        messages.error(request, 'ID adopter tidak valid.')
        return redirect('adopsi:daftar_adopter')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as active_adoptions
                    FROM adopsi 
                    WHERE id_adopter = %s 
                    AND tgl_mulai_adopsi <= CURRENT_DATE 
                    AND tgl_berhenti_adopsi >= CURRENT_DATE
                """, [adopter_id])
                
                active_count = cursor.fetchone()[0]
                
                if active_count > 0:
                    messages.error(request, 'Tidak dapat menghapus adopter yang masih memiliki adopsi aktif!')
                    return redirect('adopsi:daftar_adopter')
                
                cursor.execute("""
                    SELECT COALESCE(i.nama, o.nama_organisasi) as nama_adopter
                    FROM adopter ad
                    LEFT JOIN individu i ON ad.id_adopter = i.id_adopter
                    LEFT JOIN organisasi o ON ad.id_adopter = o.id_adopter
                    WHERE ad.id_adopter = %s
                """, [adopter_id])
                
                adopter_name_row = cursor.fetchone()
                adopter_name = adopter_name_row[0] if adopter_name_row else 'Unknown'
                
                cursor.execute("""
                    DELETE FROM adopter WHERE id_adopter = %s
                """, [adopter_id])
                
                if cursor.rowcount > 0:
                    messages.success(request, f'Data adopter {adopter_name} berhasil dihapus beserta riwayat adopsinya!')
                else:
                    messages.error(request, 'Data adopter tidak ditemukan!')
                    
    except Exception as e:
        logger.error(f"Error in delete_adopter: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus data adopter!')
    
    return redirect('adopsi:daftar_adopter')

def delete_riwayat_adopsi(request):
    username, user, error_msg = check_admin_access(request)
    
    if not username:
        messages.error(request, error_msg)
        return redirect('/login/')
    
    if request.method != 'POST':
        return redirect('adopsi:daftar_adopter')
    
    adopter_id = request.POST.get('adopter_id')
    id_hewan = request.POST.get('id_hewan')
    tgl_mulai_adopsi = request.POST.get('tgl_mulai_adopsi')
    
    if not all([adopter_id, id_hewan, tgl_mulai_adopsi]):
        messages.error(request, 'Data tidak lengkap.')
        return redirect('adopsi:daftar_adopter')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as count,
                        h.name as nama_hewan,
                        CASE 
                            WHEN tgl_mulai_adopsi <= CURRENT_DATE AND tgl_berhenti_adopsi >= CURRENT_DATE THEN true
                            ELSE false
                        END as is_active
                    FROM adopsi a
                    INNER JOIN hewan h ON a.id_hewan = h.id
                    WHERE a.id_adopter = %s 
                    AND a.id_hewan = %s 
                    AND a.tgl_mulai_adopsi = %s
                    GROUP BY h.name, is_active
                """, [adopter_id, id_hewan, tgl_mulai_adopsi])
                
                result = cursor.fetchone()
                if not result:
                    messages.error(request, 'Data adopsi tidak ditemukan!')
                    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')
                
                count, nama_hewan, is_active = result
                
                if is_active:
                    messages.error(request, 'Tidak dapat menghapus adopsi yang masih aktif!')
                    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')
                
                cursor.execute("""
                    DELETE FROM adopsi 
                    WHERE id_adopter = %s 
                    AND id_hewan = %s 
                    AND tgl_mulai_adopsi = %s
                """, [adopter_id, id_hewan, tgl_mulai_adopsi])
                
                if cursor.rowcount > 0:
                    cursor.execute("""
                        UPDATE adopter 
                        SET total_kontribusi = (
                            SELECT COALESCE(SUM(kontribusi_finansial), 0)
                            FROM adopsi 
                            WHERE id_adopter = %s 
                            AND status_pembayaran = 'Lunas'
                        )
                        WHERE id_adopter = %s
                    """, [adopter_id, adopter_id])
                    
                    messages.success(request, f'Riwayat adopsi {nama_hewan} berhasil dihapus!')
                else:
                    messages.error(request, 'Gagal menghapus riwayat adopsi!')
                    
    except Exception as e:
        logger.error(f"Error in delete_riwayat_adopsi: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus riwayat adopsi!')
    
    return redirect(f'/adopsi/adopter/{adopter_id}/riwayat/')

def capture_database_notices(cursor):
    notices = []
    try:
        if hasattr(cursor.db.connection, 'connection') and hasattr(cursor.db.connection.connection, 'notices'):
            while cursor.db.connection.connection.notices:
                notice = cursor.db.connection.connection.notices.pop(0)
                
                if hasattr(notice, 'message'):
                    notices.append(notice.message.strip())
                elif hasattr(notice, 'msg'):
                    notices.append(notice.msg.strip())
                elif isinstance(notice, str):
                    notices.append(notice.strip())
                else:
                    notices.append(str(notice).strip())
                    
        elif hasattr(cursor.db.connection, 'notices'):
            while cursor.db.connection.notices:
                notice = cursor.db.connection.notices.pop(0)
                
                if hasattr(notice, 'message'):
                    notices.append(notice.message.strip())
                elif hasattr(notice, 'msg'):
                    notices.append(notice.msg.strip())
                elif isinstance(notice, str):
                    notices.append(notice.strip())
                else:
                    notices.append(str(notice).strip())
            
    except Exception as e:
        print(f"Error capturing notices: {e}")
        
    return notices