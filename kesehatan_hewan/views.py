from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
from datetime import datetime, date, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

def check_doctor_access(request):
    if 'user' not in request.session:
        return False, redirect('login')
    
    user = request.session['user']
    if user.get('role') != 'dokter_hewan':
        messages.error(request, 'Akses ditolak! Halaman ini hanya untuk dokter hewan.')
        return False, redirect('dashboard')
    
    return True, user

def check_keeper_access(request):
    if 'user' not in request.session:
        return False, redirect('login')
    
    user = request.session['user']
    if user.get('role') != 'penjaga_hewan':
        messages.error(request, 'Akses ditolak! Halaman ini hanya untuk penjaga hewan.')
        return False, redirect('dashboard')
    
    return True, user

def daftar_hewan(request):
    if 'user' not in request.session:
        return redirect('login')
    
    user = request.session['user']
    
    if user.get('role') not in ['dokter_hewan', 'penjaga_hewan']:
        messages.error(request, 'Akses ditolak! Anda tidak memiliki izin untuk mengakses halaman ini.')
        return redirect('dashboard')
    
    try:
        with connection.cursor() as cursor:
            if user.get('role') == 'dokter_hewan':
                cursor.execute("SELECT * FROM get_animals_for_medical_records()")
                animals = []
                for row in cursor.fetchall():
                    animals.append({
                        'id': str(row[0]),
                        'nama': row[1],
                        'spesies': row[2],
                        'asal_hewan': row[3],
                        'tanggal_lahir': row[4],
                        'status_kesehatan': row[5],
                        'nama_habitat': row[6],
                        'url_foto': row[7],
                        'total_records': row[8]
                    })
            else:
                cursor.execute("""
                    SELECT id, name, species, asal_hewan, tanggal_lahir, 
                           status_kesehatan, nama_habitat, url_foto
                    FROM hewan 
                    ORDER BY name
                """)
                animals = []
                for row in cursor.fetchall():
                    animals.append({
                        'id': str(row[0]),
                        'nama': row[1],
                        'spesies': row[2],
                        'asal_hewan': row[3],
                        'tanggal_lahir': row[4],
                        'status_kesehatan': row[5],
                        'nama_habitat': row[6],
                        'url_foto': row[7],
                    })
    except Exception as e:
        logger.error(f"Error fetching animals: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data hewan.')
        animals = []
    
    return render(request, 'daftar_hewan.html', {
        'animals': animals,
        'user': user
    })

def rekam_medis_hewan(request, animal_id):
    has_access, user = check_doctor_access(request)
    if not has_access:
        return user
    
    try:
        animal_uuid = animal_id
    except ValueError:
        messages.error(request, 'ID hewan tidak valid!')
        return redirect('daftar_hewan')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            return handle_add_medical_record(request, animal_uuid, user)
        elif action == 'edit':
            return handle_edit_medical_record(request, animal_uuid)
        elif action == 'delete':
            return handle_delete_medical_record(request, animal_uuid)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_medical_records_by_animal(%s)", [animal_uuid])
            medical_records = []
            animal_name = None
            
            for row in cursor.fetchall():
                if not animal_name:
                    animal_name = row[8] 
                
                medical_records.append({
                    'id_hewan': str(row[0]),
                    'username_dh': row[1],
                    'tanggal_pemeriksaan': row[2],
                    'diagnosis': row[3],
                    'pengobatan': row[4],
                    'status_kesehatan': row[5],
                    'catatan_tindak_lanjut': row[6],
                    'nama_dokter': row[7]
                })
            
            if not animal_name:
                cursor.execute("SELECT name FROM hewan WHERE id = %s", [animal_uuid])
                result = cursor.fetchone()
                animal_name = result[0] if result else "Hewan Tidak Ditemukan"
                
    except Exception as e:
        logger.error(f"Error fetching medical records: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data rekam medis.')
        medical_records = []
        animal_name = "Error"
    
    return render(request, 'rekam_medis_hewan.html', {
        'medical_records': medical_records,
        'animal_id': animal_id,
        'animal_name': animal_name,
        'user': user
    })

def handle_add_medical_record(request, animal_uuid, user):
    tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
    status_kesehatan = request.POST.get('status_kesehatan')
    diagnosis = request.POST.get('diagnosis', '')
    pengobatan = request.POST.get('pengobatan', '')
    
    if not tanggal_pemeriksaan or not status_kesehatan:
        messages.error(request, 'Tanggal pemeriksaan dan status kesehatan harus diisi!')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        exam_date = datetime.strptime(tanggal_pemeriksaan, '%Y-%m-%d').date()
        if exam_date > date.today():
            messages.error(request, 'Tanggal pemeriksaan tidak boleh di masa depan!')
            return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    except ValueError:
        messages.error(request, 'Format tanggal tidak valid!')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    if status_kesehatan == 'Sakit':
        if not diagnosis or not pengobatan:
            messages.error(request, 'Diagnosis dan pengobatan harus diisi jika status hewan sakit!')
            return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM hewan WHERE id = %s", [animal_uuid])
            animal_result = cursor.fetchone()
            animal_name = animal_result[0] if animal_result else "Hewan"
            
            cursor.execute("""
                SELECT add_medical_record(%s, %s, %s, %s, %s, %s)
            """, [animal_uuid, user['username'], exam_date, diagnosis, pengobatan, status_kesehatan])
            
            result = cursor.fetchone()[0]
            if result.startswith('SUCCESS'):
                
                if status_kesehatan == 'Sakit':
                    cursor.execute("""
                        SELECT COUNT(*) FROM jadwal_pemeriksaan_kesehatan 
                        WHERE id_hewan = %s 
                        AND tgl_pemeriksaan_selanjutnya = %s
                    """, [animal_uuid, exam_date + timedelta(days=7)])
                    
                    if cursor.fetchone()[0] > 0:
                        messages.success(request, f'SUKSES: Jadwal pemeriksaan hewan "{animal_name}" telah diperbarui karena status kesehatan "Sakit".')

                else:
                    messages.success(request, 'Rekam medis berhasil ditambahkan!')

            else:
                messages.error(request, result.replace('ERROR: ', ''))
                
    except Exception as e:
        logger.error(f"Error adding medical record: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menambahkan rekam medis.')
    
    return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))

def handle_edit_medical_record(request, animal_uuid):
    tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
    diagnosis_baru = request.POST.get('diagnosis_baru')
    pengobatan_baru = request.POST.get('pengobatan_baru')
    catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')
    
    print(f"Edit request - tanggal_pemeriksaan: '{tanggal_pemeriksaan}'") 
    
    if not all([tanggal_pemeriksaan, diagnosis_baru, pengobatan_baru]):
        messages.error(request, 'Tanggal, diagnosis baru, dan pengobatan baru harus diisi!')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        exam_date = None
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
        
        for date_format in date_formats:
            try:
                if ' ' in tanggal_pemeriksaan and ':' in tanggal_pemeriksaan:
                    date_part = tanggal_pemeriksaan.split(' ')[0]
                    exam_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                else:
                    exam_date = datetime.strptime(tanggal_pemeriksaan, date_format).date()
                break
            except ValueError:
                continue
        
        if exam_date is None:
            raise ValueError("No valid date format found")
                
    except ValueError:
        print(f"Date parsing failed for: '{tanggal_pemeriksaan}'") 
        messages.error(request, f'Format tanggal tidak valid: {tanggal_pemeriksaan}')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT update_medical_record(%s, %s, %s, %s, %s)
            """, [animal_uuid, exam_date, diagnosis_baru, pengobatan_baru, catatan_tindak_lanjut])
            
            result = cursor.fetchone()[0]
            if result.startswith('SUCCESS'):
                messages.success(request, 'Rekam medis berhasil diperbarui!')
            else:
                messages.error(request, result.replace('ERROR: ', ''))
                
    except Exception as e:
        logger.error(f"Error updating medical record: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat memperbarui rekam medis.')
    
    return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))

def handle_delete_medical_record(request, animal_uuid):
    tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
    
    print(f"Delete request - tanggal_pemeriksaan: '{tanggal_pemeriksaan}'")  
    
    if not tanggal_pemeriksaan:
        messages.error(request, 'Tanggal pemeriksaan harus diisi!')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        exam_date = None
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
        
        for date_format in date_formats:
            try:
                if ' ' in tanggal_pemeriksaan and ':' in tanggal_pemeriksaan:
                    date_part = tanggal_pemeriksaan.split(' ')[0]
                    exam_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                else:
                    exam_date = datetime.strptime(tanggal_pemeriksaan, date_format).date()
                break
            except ValueError:
                continue
        
        if exam_date is None:
            raise ValueError("No valid date format found")
            
        print(f"Parsed date: {exam_date}") 
        
    except ValueError:
        print(f"Date parsing failed for: '{tanggal_pemeriksaan}'") 
        messages.error(request, f'Format tanggal tidak valid: {tanggal_pemeriksaan}')
        return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT delete_medical_record(%s, %s)
            """, [animal_uuid, exam_date])
            
            result = cursor.fetchone()[0]
            if result.startswith('SUCCESS'):
                messages.success(request, 'Rekam medis berhasil dihapus!')
            else:
                messages.error(request, result.replace('ERROR: ', ''))
                
    except Exception as e:
        logger.error(f"Error deleting medical record: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus rekam medis.')
    
    return redirect('kesehatan:rekam_medis_hewan', animal_id=str(animal_uuid))

def penjadwalan_pemeriksaan_kesehatan(request, animal_id):
    has_access, user = check_doctor_access(request)
    if not has_access:
        return user
    
    animal_uuid = animal_id
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'set_frequency':
            return handle_set_frequency(request, animal_uuid)
        elif action == 'add_schedule':
            return handle_add_schedule(request, animal_uuid)
        elif action == 'edit_schedule':
            return handle_edit_schedule(request, animal_uuid)
        elif action == 'delete_schedule':
            return handle_delete_schedule(request, animal_uuid)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_health_schedules_by_animal(%s)", [animal_uuid])
            schedules = []
            animal_name = None
            frequency = 3 
            
            for row in cursor.fetchall():
                if not animal_name:
                    animal_name = row[3] 
                    frequency = row[2]  
                
                schedules.append({
                    'id_hewan': str(row[0]),
                    'tgl_pemeriksaan_selanjutnya': row[1],
                    'freq_pemeriksaan_rutin': row[2]
                })
            
            if not animal_name:
                cursor.execute("SELECT name FROM hewan WHERE id = %s", [animal_uuid])
                result = cursor.fetchone()
                animal_name = result[0] if result else "Hewan Tidak Ditemukan"
                
                cursor.execute("SELECT get_animal_frequency(%s)", [animal_uuid])
                frequency = cursor.fetchone()[0]
                
    except Exception as e:
        logger.error(f"Error fetching health schedules: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data jadwal pemeriksaan.')
        schedules = []
        animal_name = "Error"
        frequency = 3
    
    return render(request, 'penjadwalan_pemeriksaan_kesehatan.html', {
        'schedules': schedules,
        'animal_id': str(animal_id), 
        'animal_name': animal_name,
        'frequency': frequency,
        'user': user
    })

def handle_set_frequency(request, animal_uuid):
    new_frequency = request.POST.get('new_frequency')
    
    if not new_frequency:
        messages.error(request, 'Frekuensi pemeriksaan harus diisi!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        frequency = int(new_frequency)
        if frequency < 1 or frequency > 12:
            messages.error(request, 'Frekuensi harus antara 1-12 bulan!')
            return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    except ValueError:
        messages.error(request, 'Frekuensi harus berupa angka!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_animal_frequency(%s, %s)", [animal_uuid, frequency])
            result = cursor.fetchone()[0]
            
            if result.startswith('SUCCESS'):
                messages.success(request, result.replace('SUCCESS: ', ''))
            else:
                messages.error(request, result.replace('ERROR: ', ''))
                
    except Exception as e:
        logger.error(f"Error setting frequency: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengatur frekuensi pemeriksaan.')
    
    return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))


def handle_add_schedule(request, animal_uuid):
    tgl_pemeriksaan = request.POST.get('tgl_pemeriksaan')
    
    if not tgl_pemeriksaan:
        messages.error(request, 'Tanggal pemeriksaan harus diisi!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        exam_date = datetime.strptime(tgl_pemeriksaan, '%Y-%m-%d').date()
        if exam_date <= date.today():
            messages.error(request, 'Tanggal pemeriksaan harus di masa depan!')
            return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    except ValueError:
        messages.error(request, 'Format tanggal tidak valid!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM hewan WHERE id = %s", [animal_uuid])
            animal_result = cursor.fetchone()
            animal_name = animal_result[0] if animal_result else "Hewan"
            
            cursor.execute("SELECT get_animal_frequency(%s)", [animal_uuid])
            frequency = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM jadwal_pemeriksaan_kesehatan 
                WHERE id_hewan = %s AND EXTRACT(YEAR FROM tgl_pemeriksaan_selanjutnya) = %s
            """, [animal_uuid, exam_date.year])
            schedules_before = cursor.fetchone()[0]
            
            cursor.execute("SELECT add_health_schedule(%s, %s)", [animal_uuid, exam_date])
            result = cursor.fetchone()[0]
            
            if result.startswith('SUCCESS'):
                messages.success(request, 'Jadwal pemeriksaan berhasil ditambahkan!')
                
                # Count schedules after adding to see if additional schedules were created
                cursor.execute("""
                    SELECT COUNT(*) FROM jadwal_pemeriksaan_kesehatan 
                    WHERE id_hewan = %s AND EXTRACT(YEAR FROM tgl_pemeriksaan_selanjutnya) = %s
                """, [animal_uuid, exam_date.year])
                schedules_after = cursor.fetchone()[0]
                
                if schedules_after > schedules_before + 1:
                    messages.success(request, f'SUKSES: Jadwal pemeriksaan rutin hewan "{animal_name}" telah ditambahkan sesuai frekuensi.')
                elif schedules_after == schedules_before + 1:
                    messages.success(request, f'Jadwal pemeriksaan untuk hewan "{animal_name}" berhasil ditambahkan.')
            else:
                messages.error(request, result.replace('ERROR: ', ''))
                
    except Exception as e:
        logger.error(f"Error adding schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menambahkan jadwal pemeriksaan.')
    
    return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))

def handle_edit_schedule(request, animal_uuid):
    old_date = request.POST.get('old_date')
    new_date = request.POST.get('new_date')
    
    if not all([old_date, new_date]):
        messages.error(request, 'Tanggal lama dan baru harus diisi!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        old_exam_date = datetime.strptime(old_date, '%Y-%m-%d').date()
        new_exam_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        
        if new_exam_date <= date.today():
            messages.error(request, 'Tanggal pemeriksaan baru harus di masa depan!')
            return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    except ValueError:
        messages.error(request, 'Format tanggal tidak valid!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM jadwal_pemeriksaan_kesehatan 
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                  AND tgl_pemeriksaan_selanjutnya != %s
            """, [animal_uuid, new_exam_date, old_exam_date])
            
            if cursor.fetchone()[0] > 0:
                messages.error(request, 'Jadwal pemeriksaan untuk tanggal baru sudah ada!')
                return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
            
            cursor.execute("""
                UPDATE jadwal_pemeriksaan_kesehatan 
                SET tgl_pemeriksaan_selanjutnya = %s
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
            """, [new_exam_date, animal_uuid, old_exam_date])
            
            if cursor.rowcount > 0:
                messages.success(request, 'Jadwal pemeriksaan berhasil diperbarui!')
            else:
                messages.error(request, 'Jadwal pemeriksaan tidak ditemukan!')
                
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat memperbarui jadwal pemeriksaan.')
    
    return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))

def handle_edit_frequency(request, animal_uuid):
    new_frequency = request.POST.get('new_frequency')
    
    if not new_frequency:
        messages.error(request, 'Frekuensi pemeriksaan harus diisi!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        frequency = int(new_frequency)
        if frequency < 1 or frequency > 12:
            messages.error(request, 'Frekuensi harus antara 1-12 bulan!')
            return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    except ValueError:
        messages.error(request, 'Frekuensi harus berupa angka!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE jadwal_pemeriksaan_kesehatan 
                SET freq_pemeriksaan_rutin = %s
                WHERE id_hewan = %s
            """, [frequency, animal_uuid])
            
        messages.success(request, 'Frekuensi pemeriksaan berhasil diperbarui!')
                
    except Exception as e:
        logger.error(f"Error updating frequency: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat memperbarui frekuensi pemeriksaan.')
    
    return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))

def handle_delete_schedule(request, animal_uuid):
    date_to_delete = request.POST.get('date_to_delete')
    
    if not date_to_delete:
        messages.error(request, 'Tanggal pemeriksaan harus diisi!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        exam_date = datetime.strptime(date_to_delete, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Format tanggal tidak valid!')
        return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM jadwal_pemeriksaan_kesehatan 
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
            """, [animal_uuid, exam_date])
            
            if cursor.rowcount > 0:
                messages.success(request, 'Jadwal pemeriksaan berhasil dihapus!')
            else:
                messages.error(request, 'Jadwal pemeriksaan tidak ditemukan!')
                
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus jadwal pemeriksaan.')
    
    return redirect('penjadwalan_pemeriksaan_kesehatan', animal_id=str(animal_uuid))

def pemberian_pakan(request, animal_id):
    has_access, user = check_keeper_access(request)
    if not has_access:
        return user
    
    try:
        animal_uuid = animal_id
    except ValueError:
        messages.error(request, 'ID hewan tidak valid!')
        return redirect('daftar_hewan')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            return handle_add_feeding_for_animal(request, animal_uuid, user)
        elif action == 'edit':
            return handle_edit_feeding(request, user)
        elif action == 'delete':
            return handle_delete_feeding(request, user)
        elif action == 'mark_fed':
            return handle_mark_fed(request, user)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_hewan, p.jadwal, p.jenis, p.jumlah, p.status
                FROM pakan p
                WHERE p.id_hewan = %s
                ORDER BY p.jadwal DESC
            """, [animal_uuid])
            
            feeding_schedules = []
            for row in cursor.fetchall():
                feeding_schedules.append({
                    'id_hewan': str(row[0]),
                    'jadwal': row[1],
                    'jenis': row[2],
                    'jumlah': row[3],
                    'status': row[4]
                })
            
            cursor.execute("""
                SELECT h.name, h.species, h.asal_hewan, h.tanggal_lahir, h.nama_habitat, h.status_kesehatan,
                       p.jenis, p.jumlah, p.jadwal
                FROM memberi m
                JOIN pakan p ON m.id_hewan = p.id_hewan AND m.jadwal = p.jadwal
                JOIN hewan h ON m.id_hewan = h.id
                WHERE m.username_jh = %s AND m.id_hewan = %s
                ORDER BY p.jadwal DESC
            """, [user['username'], animal_uuid])
            
            feeding_history = []
            for row in cursor.fetchall():
                feeding_history.append({
                    'nama_hewan': row[0],
                    'spesies': row[1],
                    'asal_hewan': row[2],
                    'tanggal_lahir': row[3],
                    'nama_habitat': row[4],
                    'status_kesehatan': row[5],
                    'jenis_pakan': row[6],
                    'jumlah_pakan': row[7],
                    'jadwal': row[8]
                })
            
            cursor.execute("SELECT name FROM hewan WHERE id = %s", [animal_uuid])
            result = cursor.fetchone()
            animal_name = result[0] if result else "Hewan Tidak Ditemukan"
                
    except Exception as e:
        logger.error(f"Error fetching feeding data: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat mengambil data pemberian pakan.')
        feeding_schedules = []
        feeding_history = []
        animal_name = "Error"
    
    return render(request, 'pemberian_pakan.html', {
        'feeding_schedules': feeding_schedules,
        'feeding_history': feeding_history,
        'animal_id': animal_id,
        'animal_name': animal_name,
        'user': user
    })

def handle_add_feeding_for_animal(request, animal_uuid, user):
    jenis_pakan = request.POST.get('jenis_pakan')
    jumlah_pakan = request.POST.get('jumlah_pakan')
    jadwal = request.POST.get('jadwal')
    
    if not all([jenis_pakan, jumlah_pakan, jadwal]):
        messages.error(request, 'Semua field harus diisi!')
        return redirect('pemberian_pakan', animal_id=str(animal_uuid))
    
    try:
        jumlah = int(jumlah_pakan)
        if jumlah <= 0:
            messages.error(request, 'Jumlah pakan harus lebih dari 0!')
            return redirect('pemberian_pakan', animal_id=str(animal_uuid))
            
        jadwal_datetime = datetime.strptime(jadwal, '%Y-%m-%dT%H:%M')
        if jadwal_datetime <= datetime.now():
            messages.error(request, 'Jadwal pemberian pakan harus di masa depan!')
            return redirect('pemberian_pakan', animal_id=str(animal_uuid))
            
    except (ValueError, TypeError):
        messages.error(request, 'Format data tidak valid!')
        return redirect('pemberian_pakan', animal_id=str(animal_uuid))
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM pakan 
                WHERE id_hewan = %s AND jadwal = %s
            """, [animal_uuid, jadwal_datetime])
            
            if cursor.fetchone()[0] > 0:
                messages.error(request, 'Sudah ada jadwal pemberian pakan untuk waktu ini!')
                return redirect('pemberian_pakan', animal_id=str(animal_uuid))
            
            cursor.execute("""
                INSERT INTO pakan (id_hewan, jadwal, jenis, jumlah, status)
                VALUES (%s, %s, %s, %s, %s)
            """, [animal_uuid, jadwal_datetime, jenis_pakan, jumlah, 'Menunggu Pemberian'])
            
            messages.success(request, 'Jadwal pemberian pakan berhasil ditambahkan!')
                
    except Exception as e:
        logger.error(f"Error adding feeding schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menambahkan jadwal pemberian pakan.')
    
    return redirect('pemberian_pakan', animal_id=str(animal_uuid))

def handle_edit_feeding(request, user):
    """Handle editing feeding schedule"""
    id_hewan = request.POST.get('id_hewan')
    old_jadwal = request.POST.get('old_jadwal')
    jenis_pakan_baru = request.POST.get('jenis_pakan_baru')
    jumlah_pakan_baru = request.POST.get('jumlah_pakan_baru')
    jadwal_baru = request.POST.get('jadwal_baru')
    
    if not all([id_hewan, old_jadwal, jenis_pakan_baru, jumlah_pakan_baru, jadwal_baru]):
        messages.error(request, 'Semua field harus diisi!')
        return redirect('pemberian_pakan')
    
    try:
        animal_uuid = id_hewan
        jumlah = int(jumlah_pakan_baru)
        if jumlah <= 0:
            messages.error(request, 'Jumlah pakan harus lebih dari 0!')
            return redirect('pemberian_pakan')
            
        old_jadwal_datetime = datetime.strptime(old_jadwal, '%Y-%m-%d %H:%M:%S')
        new_jadwal_datetime = datetime.strptime(jadwal_baru, '%Y-%m-%dT%H:%M')
        
    except (ValueError, TypeError):
        messages.error(request, 'Format data tidak valid!')
        return redirect('pemberian_pakan')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE pakan 
                SET jenis = %s, jumlah = %s, jadwal = %s
                WHERE id_hewan = %s AND jadwal = %s
            """, [jenis_pakan_baru, jumlah, new_jadwal_datetime, animal_uuid, old_jadwal_datetime])
            
            if cursor.rowcount > 0:
                messages.success(request, 'Jadwal pemberian pakan berhasil diperbarui!')
            else:
                messages.error(request, 'Jadwal pemberian pakan tidak ditemukan!')
                
    except Exception as e:
        logger.error(f"Error updating feeding schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat memperbarui jadwal pemberian pakan.')
    
    return redirect('pemberian_pakan', animal_id=str(animal_uuid))

def handle_delete_feeding(request, user):
    """Handle deleting feeding schedule"""
    id_hewan = request.POST.get('id_hewan')
    jadwal = request.POST.get('jadwal')
    
    if not all([id_hewan, jadwal]):
        messages.error(request, 'Data tidak lengkap!')
        return redirect('pemberian_pakan')
    
    try:
        animal_uuid = id_hewan
        jadwal_datetime = datetime.strptime(jadwal, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        messages.error(request, 'Format data tidak valid!')
        return redirect('pemberian_pakan')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM pakan 
                WHERE id_hewan = %s AND jadwal = %s
            """, [animal_uuid, jadwal_datetime])
            
            if cursor.rowcount > 0:
                messages.success(request, 'Jadwal pemberian pakan berhasil dihapus!')
            else:
                messages.error(request, 'Jadwal pemberian pakan tidak ditemukan!')
                
    except Exception as e:
        logger.error(f"Error deleting feeding schedule: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat menghapus jadwal pemberian pakan.')
    
    return redirect('pemberian_pakan', animal_id=str(animal_uuid))

def handle_mark_fed(request, user):
    """Handle marking feeding as completed"""
    id_hewan = request.POST.get('id_hewan')
    jadwal = request.POST.get('jadwal')
    
    if not all([id_hewan, jadwal]):
        messages.error(request, 'Data tidak lengkap!')
        return redirect('pemberian_pakan')
    
    try:
        animal_uuid = id_hewan
        jadwal_datetime = datetime.strptime(jadwal, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        messages.error(request, 'Format data tidak valid!')
        return redirect('pemberian_pakan')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE pakan 
                SET status = 'Selesai Diberikan'
                WHERE id_hewan = %s AND jadwal = %s
            """, [animal_uuid, jadwal_datetime])
            
            if cursor.rowcount > 0:
                cursor.execute("""
                    INSERT INTO memberi (id_hewan, jadwal, username_jh)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id_hewan, jadwal) DO NOTHING
                """, [animal_uuid, jadwal_datetime, user['username']])
                
                messages.success(request, 'Status pemberian pakan berhasil diperbarui!')
            else:
                messages.error(request, 'Jadwal pemberian pakan tidak ditemukan!')
                
    except Exception as e:
        logger.error(f"Error marking feeding as completed: {str(e)}")
        messages.error(request, 'Terjadi kesalahan saat memperbarui status pemberian pakan.')
    
    return redirect('pemberian_pakan', animal_id=str(animal_uuid))