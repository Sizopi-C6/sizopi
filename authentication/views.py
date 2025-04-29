from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import datetime

def landing_page(request):
    return render(request, 'landing.html')

def login_page(request):
    return render(request, 'login.html')

def register_pilih(request):
    return render(request, 'register_pilih.html')

def register_pengunjung(request):
    if request.method == 'POST':
        return redirect('login')
    
    return render(request, 'register_pengunjung.html')

def register_dokter_hewan(request):
    if request.method == 'POST':
        return redirect('login')
    
    return render(request, 'register_dokter_hewan.html')

def register_staff(request):
    if request.method == 'POST':
        return redirect('login')
    
    return render(request, 'register_staff.html')

def logout_view(request):
    return redirect('login')

def profile_settings(request):
    # Simulasi role pengguna untuk demo
    # Dalam implementasi nyata, role akan diambil dari model database
    user_role = request.GET.get('role', 'visitor')  # Default role: visitor
    
    # Dummy user data (simulasi data dari request.user)
    user = {
        'username': 'johndoe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com'
    }
    
    # Data profil sesuai form yang ditampilkan pada template
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
            # Mengambil data dari form sesuai field pada template
            first_name = request.POST.get('first_name', '')
            middle_name = request.POST.get('middle_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            
            # Validasi data wajib
            if not phone:
                messages.error(request, 'Nomor telepon harus diisi!')
                return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
            
            if not first_name or not last_name:
                messages.error(request, 'Nama depan dan belakang harus diisi!')
                return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
            
            # Pemrosesan data khusus berdasarkan role
            if user_role == 'visitor':
                address = request.POST.get('address', '')
                birth_date = request.POST.get('birth_date', '')
                
                if not address:
                    messages.error(request, 'Alamat harus diisi!')
                    return render(request, 'profile_settings.html', {'user': user, 'profile': profile})
                
                # Update profil pengunjung
                profile['address'] = address
                if birth_date:
                    profile['birth_date'] = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
            elif user_role == 'vet':
                # Mengambil data spesialisasi
                specializations = request.POST.getlist('specializations', [])
                other_specialization = request.POST.get('other_specialization', '')
                
                # Update profil dokter hewan
                profile['specializations'] = specializations
                profile['other_specialization'] = other_specialization
            
            # Update data umum profil
            profile['middle_name'] = middle_name
            profile['phone_number'] = phone
            
            # Update data user (dalam implementasi nyata akan tersimpan ke database)
            user['first_name'] = first_name
            user['last_name'] = last_name
            user['email'] = email
            
            # Tampilkan pesan sukses
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('profile_settings')
    
    # Jika request.method GET atau form tidak valid
    return render(request, 'profile_settings.html', {
        'user': user,
        'profile': profile
    })

def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session hash untuk mencegah logout
            update_session_auth_hash(request, user)
            messages.success(request, 'Password berhasil diubah!')
            return redirect('profile_settings')
        else:
            # Jika form tidak valid, tampilkan pesan error
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'ubah_password.html', {'form': form})