from django.shortcuts import render

def dashboard_view(request):
    # Data dummy user jdoe
    user_role = 'Pengunjung'
    data_umum = {
        'nama_depan': 'John',
        'nama_tengah': 'Michael',
        'nama_belakang': 'Doe',
        'username': 'jdoe',
        'email': 'jdoe@example.com',
        'phone_number': '081234567890',
        'role': user_role,
    }

    role_data = {}

    if user_role == 'Pengunjung':
        role_data = {
            'alamat': 'Jl. Mawar No. 1, Jakarta',
            'tgl_lahir': '1990-05-15',
            'riwayat_kunjungan': [
                'Wahana Safari - Zona A - 03/04/2025 11:11:33',
                'Kolam Reptil - Zona C - 25/01/2025 1:27:46'
            ],
            'info_tiket_dibeli': [
                'Zona Burung - 2 Tiket',
                'Petting Zoo - 3 Tiket'
            ]
        }
    elif user_role == 'Dokter Hewan':
        role_data = {
            'no_STR': 'STR001', 
            'nama_spesialisasi': ['Bedah Hewan'],  
            'jumlah_hewan_ditangani': 10
        }
    elif user_role == 'Penjaga Hewan':
        role_data = {
            'id_staf': 'b3c6f8e2-3b7a-4b6c-92e1-bb8c8f729e01',
            'jumlah_hewan_diberi_pakan': 25
        }
    elif user_role == 'Staf Administrasi':
        role_data = {
            'id_staf': 'b3c6f8e2-3b7a-4b6c-92e1-bb8c8f729e01',
            'ringkasan_penjualan_tiket': {
                'tiket_dewasa': 150,
                'tiket_anak': 50,
                'total_pendapatan': 5000000
            },
            'jumlah_pengunjung_hari_ini': 200,
                'laporan_pendapatan_mingguan': {
                'senin': 4500000,
                'selasa': 3800000,
                'rabu': 4200000,
                'kamis': 5100000,
                'jumat': 7000000,
                'sabtu': 10500000,
                'minggu': 11100000
            },
        }
    elif user_role == 'Staf Pelatih Pertunjukan':
        role_data = {
            'id_staf': 'b3c6f8e2-3b7a-4b6c-92e1-bb8c8f729e01',
            'jadwal_pertunjukan_hari_ini': {'10:00 - Pertunjukan Lumba-Lumba', '14:00 - Pertunjukan Burung'},
            'daftar_hewan_dilatih': {'Lumba-Lumba (Dolly)', 'Kakatua (Coco)'},
            'status_latihan_terakhir': 'Berhasil: 2023-11-15'
        }
    else:
        role_data = {}

    context = {
        'data_umum': data_umum,
        'role_data': role_data
    }
    return render(request, 'dashboard.html', context)
