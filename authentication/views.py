from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import connection, transaction
from datetime import datetime, date
from decimal import Decimal
import uuid
import logging
import re
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    if len(username) < 3 or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_password(password):
    if len(password) < 6:
        return False
    return True

def validate_name(name):
    if len(name) < 1 or len(name) > 50:
        return False
    pattern = r'^[a-zA-Z\s]+$'
    return re.match(pattern, name) is not None

def validate_birth_date(birth_date_str):
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        if birth_date > date.today():
            return False, "Tanggal lahir tidak boleh di masa depan!"
        
        min_age_date = date.today() - relativedelta(years=13)
        if birth_date > min_age_date:
            return False, "Usia minimal 13 tahun untuk mendaftar!"
        
        max_age_date = date.today() - relativedelta(years=120)
        if birth_date < max_age_date:
            return False, "Tanggal lahir tidak valid!"
        
        return True, None
    except ValueError:
        return False, "Format tanggal lahir tidak valid!"

def landing_page(request):
    return render(request, 'landing.html')

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
                
        if not email or not password:
            messages.error(request, 'Email dan password harus diisi!')
            return render(request, 'login.html')
        
        if not validate_email(email):
            messages.error(request, 'Format email tidak valid!')
            return render(request, 'login.html')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.*, 
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = p.username) THEN 'pengunjung'
                        WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = p.username) THEN 'dokter_hewan'
                        WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = p.username) THEN 'penjaga_hewan'
                        WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = p.username) THEN 'pelatih_hewan'
                        WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = p.username) THEN 'staf_admin'
                        ELSE 'incomplete_registration'
                    END AS role
                    FROM pengguna p 
                    WHERE p.email = %s
                """, [email])
                
                row = cursor.fetchone()
                if row:
                    user = dict(zip([column[0] for column in cursor.description], row))
                    
                    if user.get('role') == 'incomplete_registration':
                        messages.error(request, 'Registrasi Anda belum lengkap. Silakan hubungi administrator atau daftar ulang.')
                        return render(request, 'login.html')
                    
                    for key, value in user.items():
                        if isinstance(value, (date, datetime)):
                            user[key] = value.isoformat()
                        elif isinstance(value, uuid.UUID):
                            user[key] = str(value)
                        elif isinstance(value, Decimal):
                            user[key] = float(value)
                else:
                    user = None
                
                if user and password == user.get('password'):
                    request.session['user'] = user
                    request.session.save()
                    
                    messages.success(request, f"Selamat datang, {user.get('nama_depan')} {user.get('nama_belakang')}!")
                    
                    role = user.get('role')
                    if role == 'pengunjung':
                        return redirect('dashboard') 
                    elif role == 'dokter_hewan':
                        return redirect('dashboard')  
                    elif role in ['penjaga_hewan', 'pelatih_hewan', 'staf_admin']:
                        return redirect('dashboard')  
                    else:
                        return redirect('dashboard')  
                else:
                    messages.error(request, 'Email atau password salah!')
                    
        except Exception as e:
            logger.error(f"Login error for email {email}: {str(e)}")
            messages.error(request, 'Terjadi kesalahan saat login. Silakan coba lagi.')
    
    return render(request, 'login.html')

def register_pilih(request):
    return render(request, 'register_pilih.html')

def register_pengunjung(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        konfirmasi_password = request.POST.get('konfirmasi_password', '')
        nama_depan = request.POST.get('nama_depan', '').strip()
        nama_tengah = request.POST.get('nama_tengah', '').strip()
        nama_belakang = request.POST.get('nama_belakang', '').strip()
        email = request.POST.get('email', '').strip()
        no_telepon = request.POST.get('no_telepon', '').strip()
        alamat = request.POST.get('alamat', '').strip()
        tgl_lahir = request.POST.get('tgl_lahir', '')
        
        if not all([username, password, nama_depan, nama_belakang, email, no_telepon, alamat, tgl_lahir]):
            messages.error(request, 'Semua field wajib harus diisi!')
            return render(request, 'register_pengunjung.html')
        
        if not validate_username(username):
            messages.error(request, 'Username harus 3-50 karakter dan hanya boleh mengandung huruf, angka, dan underscore!')
            return render(request, 'register_pengunjung.html')
        
        if not validate_password(password):
            messages.error(request, 'Password minimal 6 karakter!')
            return render(request, 'register_pengunjung.html')
        
        if password != konfirmasi_password:
            messages.error(request, 'Password dan konfirmasi password tidak cocok!')
            return render(request, 'register_pengunjung.html')
        
        if not validate_email(email):
            messages.error(request, 'Format email tidak valid!')
            return render(request, 'register_pengunjung.html')
        
        if not validate_name(nama_depan):
            messages.error(request, 'Nama depan hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_pengunjung.html')
        
        if not validate_name(nama_belakang):
            messages.error(request, 'Nama belakang hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_pengunjung.html')
        
        if nama_tengah and not validate_name(nama_tengah):
            messages.error(request, 'Nama tengah hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_pengunjung.html')
        
        if len(alamat) < 10:
            messages.error(request, 'Alamat minimal 10 karakter!')
            return render(request, 'register_pengunjung.html')
        
        is_valid_date, date_error = validate_birth_date(tgl_lahir)
        if not is_valid_date:
            messages.error(request, date_error)
            return render(request, 'register_pengunjung.html')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT validate_complete_registration(%s, %s, %s)
                """, [username, email, 'pengunjung'])
                
                validation_result = cursor.fetchone()[0]
                
                if validation_result.startswith('ERROR'):
                    messages.error(request, validation_result.replace('ERROR: ', ''))
                    return render(request, 'register_pengunjung.html')
                
                with transaction.atomic():
                    cursor.execute("""
                        INSERT INTO pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])
                    
                    cursor.execute("""
                        INSERT INTO pengunjung (username_p, alamat, tgl_lahir)
                        VALUES (%s, %s, %s)
                    """, [username, alamat, tgl_lahir])
                    
                    messages.success(request, 'Registrasi berhasil! Silakan login.')
                    return redirect('login')
                    
        except Exception as e:
            error_message = str(e)
            if 'sudah digunakan' in error_message:
                messages.error(request, error_message)
            else:
                logger.error(f"Pengunjung registration error: {error_message}")
                messages.error(request, f'Terjadi kesalahan: {error_message}')
    
    return render(request, 'register_pengunjung.html')

def register_dokter_hewan(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        konfirmasi_password = request.POST.get('konfirmasi_password', '')
        nama_depan = request.POST.get('nama_depan', '').strip()
        nama_tengah = request.POST.get('nama_tengah', '').strip()
        nama_belakang = request.POST.get('nama_belakang', '').strip()
        email = request.POST.get('email', '').strip()
        no_telepon = request.POST.get('no_telepon', '').strip()
        no_str = request.POST.get('no_str', '').strip()
        specializations = request.POST.getlist('specializations')
        other_specialization = request.POST.get('other_specialization', '').strip()
        
        if not all([username, password, nama_depan, nama_belakang, email, no_telepon, no_str]):
            messages.error(request, 'Semua field wajib harus diisi!')
            return render(request, 'register_dokter_hewan.html')
        
        if not validate_username(username):
            messages.error(request, 'Username harus 3-50 karakter dan hanya boleh mengandung huruf, angka, dan underscore!')
            return render(request, 'register_dokter_hewan.html')
        
        if not validate_password(password):
            messages.error(request, 'Password minimal 6 karakter!')
            return render(request, 'register_dokter_hewan.html')
        
        if password != konfirmasi_password:
            messages.error(request, 'Password dan konfirmasi password tidak cocok!')
            return render(request, 'register_dokter_hewan.html')
        
        if not validate_email(email):
            messages.error(request, 'Format email tidak valid!')
            return render(request, 'register_dokter_hewan.html')
                
        if not validate_name(nama_depan):
            messages.error(request, 'Nama depan hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_dokter_hewan.html')
        
        if not validate_name(nama_belakang):
            messages.error(request, 'Nama belakang hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_dokter_hewan.html')
        
        if nama_tengah and not validate_name(nama_tengah):
            messages.error(request, 'Nama tengah hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_dokter_hewan.html')
        
        if len(no_str) < 5:
            messages.error(request, 'Nomor STR minimal 5 karakter!')
            return render(request, 'register_dokter_hewan.html')
        
        if not specializations:
            messages.error(request, 'Minimal satu spesialisasi harus dipilih!')
            return render(request, 'register_dokter_hewan.html')
        
        if 'Lainnya' in specializations and not other_specialization:
            messages.error(request, 'Silakan jelaskan spesialisasi lainnya!')
            return render(request, 'register_dokter_hewan.html')
        
        if other_specialization and len(other_specialization) < 3:
            messages.error(request, 'Spesialisasi lainnya minimal 3 karakter!')
            return render(request, 'register_dokter_hewan.html')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT validate_complete_registration(%s, %s, %s)
                """, [username, email, 'dokter_hewan'])
                
                validation_result = cursor.fetchone()[0]
                
                if validation_result.startswith('ERROR'):
                    messages.error(request, validation_result.replace('ERROR: ', ''))
                    return render(request, 'register_dokter_hewan.html')
                
                with transaction.atomic():
                    cursor.execute("""
                        INSERT INTO pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])
                    
                    cursor.execute("""
                        INSERT INTO dokter_hewan (username_dh, no_str)
                        VALUES (%s, %s)
                    """, [username, no_str])
                    
                    specialization_count = 0
                    for specialization in specializations:
                        if specialization == 'Lainnya' and other_specialization:
                            cursor.execute("""
                                INSERT INTO spesialisasi (username_sh, nama_spesialisasi)
                                VALUES (%s, %s)
                            """, [username, other_specialization])
                            specialization_count += 1
                        elif specialization != 'Lainnya':
                            cursor.execute("""
                                INSERT INTO spesialisasi (username_sh, nama_spesialisasi)
                                VALUES (%s, %s)
                            """, [username, specialization])
                            specialization_count += 1
                    
                    if specialization_count == 0:
                        raise Exception("No valid specializations were inserted")
                    
                    messages.success(request, 'Registrasi dokter hewan berhasil! Silakan login.')
                    return redirect('login')
                    
        except Exception as e:
            error_message = str(e)
            if 'sudah digunakan' in error_message:
                messages.error(request, error_message)
            else:
                logger.error(f"Dokter hewan registration error: {error_message}")
                messages.error(request, f'Terjadi kesalahan saat registrasi: {error_message}')
    
    return render(request, 'register_dokter_hewan.html')

def register_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        konfirmasi_password = request.POST.get('konfirmasi_password', '')
        nama_depan = request.POST.get('nama_depan', '').strip()
        nama_tengah = request.POST.get('nama_tengah', '').strip()
        nama_belakang = request.POST.get('nama_belakang', '').strip()
        email = request.POST.get('email', '').strip()
        no_telepon = request.POST.get('no_telepon', '').strip()
        peran = request.POST.get('peran', '')
        
        if not all([username, password, nama_depan, nama_belakang, email, no_telepon, peran]):
            messages.error(request, 'Semua field wajib harus diisi!')
            return render(request, 'register_staff.html')
        
        if not validate_username(username):
            messages.error(request, 'Username harus 3-50 karakter dan hanya boleh mengandung huruf, angka, dan underscore!')
            return render(request, 'register_staff.html')
        
        if not validate_password(password):
            messages.error(request, 'Password minimal 6 karakter!')
            return render(request, 'register_staff.html')
        
        if password != konfirmasi_password:
            messages.error(request, 'Password dan konfirmasi password tidak cocok!')
            return render(request, 'register_staff.html')
        
        if not validate_email(email):
            messages.error(request, 'Format email tidak valid!')
            return render(request, 'register_staff.html')
                
        if not validate_name(nama_depan):
            messages.error(request, 'Nama depan hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_staff.html')
        
        if not validate_name(nama_belakang):
            messages.error(request, 'Nama belakang hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_staff.html')
        
        if nama_tengah and not validate_name(nama_tengah):
            messages.error(request, 'Nama tengah hanya boleh mengandung huruf dan spasi!')
            return render(request, 'register_staff.html')
        
        if peran not in ['Penjaga Hewan', 'Staf Administrasi', 'Pelatih Pertunjukan']:
            messages.error(request, 'Peran yang dipilih tidak valid!')
            return render(request, 'register_staff.html')
        
        id_staf = str(uuid.uuid4())
        
        try:
            with connection.cursor() as cursor:
                role_mapping = {
                    'Penjaga Hewan': 'penjaga_hewan',
                    'Staf Administrasi': 'staf_admin', 
                    'Pelatih Pertunjukan': 'pelatih_hewan'
                }
                
                cursor.execute("""
                    SELECT validate_complete_registration(%s, %s, %s)
                """, [username, email, role_mapping.get(peran, 'staff')])
                
                validation_result = cursor.fetchone()[0]
                
                if validation_result.startswith('ERROR'):
                    messages.error(request, validation_result.replace('ERROR: ', ''))
                    return render(request, 'register_staff.html')
                
                with transaction.atomic():
                    cursor.execute("""
                        INSERT INTO pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])
                    
                    if peran == 'Penjaga Hewan':
                        cursor.execute("""
                            INSERT INTO penjaga_hewan (username_jh, id_staf)
                            VALUES (%s, %s)
                        """, [username, id_staf])
                        
                    elif peran == 'Staf Administrasi':
                        cursor.execute("""
                            INSERT INTO staf_admin (username_sa, id_staf)
                            VALUES (%s, %s)
                        """, [username, id_staf])
                        
                    elif peran == 'Pelatih Pertunjukan':
                        cursor.execute("""
                            INSERT INTO pelatih_hewan (username_lh, id_staf)
                            VALUES (%s, %s)
                        """, [username, id_staf])
                    
                    messages.success(request, f'Registrasi staff berhasil! ID Staff Anda: {id_staf[:8]}... Silakan login.')
                    return redirect('login')
                    
        except Exception as e:
            error_message = str(e)
            if 'sudah digunakan' in error_message:
                messages.error(request, error_message)
            else:
                logger.error(f"Staff registration error: {error_message}")
                messages.error(request, f'Terjadi kesalahan saat registrasi: {error_message}')
    
    return render(request, 'register_staff.html')

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Anda telah berhasil logout!')
    return redirect('login')

def profile_settings(request):
    user_role = request.GET.get('role', 'visitor')
    
    user = {
        'username': 'johndoe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com'
    }
    
    profile = {
        'role': user_role,
        'middle_name': 'William',
        'phone_number': '08123456789',
        'address': 'Jl. Contoh No. 123, Kota Jakarta',
        'birth_date': datetime.strptime('2000-01-01', '%Y-%m-%d').date(),
        'certification_number': 'CERT-DH-2023-001',
        'specializations': ['Mamalia Besar', 'Reptil', 'Lainnya'],
        'other_specialization': 'Hewan Eksotis',
        'staff_id': 'STAFF-ZOO-2023-001'
    }
    
    if request.method == 'POST':
        if 'save_profile' in request.POST:
            first_name = request.POST.get('first_name', '')
            middle_name = request.POST.get('middle_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            
            if not phone:
                messages.error(request, 'Nomor telepon harus diisi!')
                return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
            
            if not first_name or not last_name:
                messages.error(request, 'Nama depan dan belakang harus diisi!')
                return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
            
            if user_role == 'visitor':
                address = request.POST.get('address', '')
                birth_date = request.POST.get('birth_date', '')
                
                if not address:
                    messages.error(request, 'Alamat harus diisi!')
                    return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
                
                profile['address'] = address
                if birth_date:
                    profile['birth_date'] = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
            elif user_role == 'vet':
                specializations = request.POST.getlist('specializations', [])
                other_specialization = request.POST.get('other_specialization', '')
                
                profile['specializations'] = specializations
                profile['other_specialization'] = other_specialization
            
            profile['middle_name'] = middle_name
            profile['phone_number'] = phone
            
            user['first_name'] = first_name
            user['last_name'] = last_name
            user['email'] = email
            
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('profile_settings')
    
    return render(request, 'profile_settings.html', {
        'user': user,
        'profile': profile
    })

def password_change_view(request):
    user_role = request.GET.get('role', 'visitor')
    
    profile = {
        'role': user_role,
    }
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password berhasil diubah!')
            return redirect('profile_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'ubah_password.html', {
        'form': form,
        'profile': profile
    })

def session_user(request):
    user = request.session.get('user')
    return render(request, 'navbar.html', {'session_user': user})