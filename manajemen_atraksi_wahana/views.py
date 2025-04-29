from django.shortcuts import render

def dashboard_view(request):
    user_role = 'Staf Administrasi'
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

def data_atraksi(request):
    data_atraksi = [
        {
            'nama_atraksi': 'Wahana Safari',
            'lokasi': 'Zona A',
            'kapasitas_max': '34',
            'jadwal': '8:00',
            'nama_hewan': [
                'Sahara (Camelus dromedarius)',
                'Rocky (Ovis canadensis)',
                'Wave (Chelonia mydas)'
            ],
            'nama_depan': 'Xavier',
            'nama_tengah': 'Genesis',
            'nama_belakang': 'Patel'
        },
        {
            'nama_atraksi': 'Reptile Encounter',
            'lokasi': 'Zona E',
            'kapasitas_max': '89',
            'jadwal': '7:45',
            'nama_hewan': [
                'Polar (Ursus maritimus)'
            ],
            'nama_depan': 'Dominic',
            'nama_tengah': 'Morgan',
            'nama_belakang': 'Dixon'
        }
    ]
    
    context = {
        'data_atraksi': data_atraksi
    }
    
    return render(request, 'data_atraksi.html', context)

def tambah_atraksi(request):
    hewan_list = ["Sahara (Camelus dromedarius)", "Rocky (Ovis canadensis)", "Wave (Chelonia mydas)"] 
    pelatih_list = ["Xavier Genesis Patel", "Dominic Morgan Dixon"] 

    return render(request, 'form_tambah_atraksi.html', {
        'hewan_list': hewan_list,
        'pelatih_list': pelatih_list
    })

def edit_atraksi(request, nama_atraksi):
    data_edit_atraksi = [
        {
            'nama_atraksi': 'Wahana Safari',
            'lokasi': 'Zona A',
            'kapasitas_max': '34',
            'jadwal': '8:00',
            'nama_hewan': [
                'Sahara (Camelus dromedarius)',
                'Rocky (Ovis canadensis)',
                'Wave (Chelonia mydas)'
            ],
            'nama_depan': 'Xavier',
            'nama_tengah': 'Genesis',
            'nama_belakang': 'Patel'
        },
        {
            'nama_atraksi': 'Reptile Encounter',
            'lokasi': 'Zona E',
            'kapasitas_max': '89',
            'jadwal': '7:45:00',
            'nama_hewan': [
                'Polar (Ursus maritimus)'
            ],
            'nama_depan': 'Dominic',
            'nama_tengah': 'Morgan',
            'nama_belakang': 'Dixon'
        }
    ]

    atraksi = next((item for item in data_edit_atraksi if item['nama_atraksi'] == nama_atraksi), None)

    hewan_list = ["Harimau", "Gajah", "Kera", "Burung"]
    pelatih_list = ["Dominic Morgan Dixon", "Zavier Genasis Patel"]
    atraksi['pelatih'] = f"{atraksi['nama_depan']} {atraksi['nama_tengah']} {atraksi['nama_belakang']}"


    return render(request, 'form_edit_atraksi.html', {
        'atraksi': atraksi,
        'hewan_list': hewan_list,
        'pelatih_list': pelatih_list,
    })
    
def data_wahana(request):
    data_wahana = [
        {
            'nama_wahana': 'Komedi Putar',
            'kapasitas_max': '40',
            'jadwal': '9:00:00',
            'peraturan': [
                'Anak di bawah 5 tahun harus didampingi orang dewasa.',
                'Dilarang berdiri atau bergerak saat wahana beroperasi.',
                'Pengunjung dengan gangguan jantung disarankan tidak ikut.'
            ]
        },
        {
            'nama_wahana': 'Kereta Gantung',
            'kapasitas_max': '25',
            'jadwal': '8:30:00',
            'peraturan': [
                'Anak di bawah 5 tahun harus didampingi orang dewasa.',
                'Berat maksimum per kereta adalah 150 kg.',
                'Dilarang membuka pintu atau menggoyangkan kereta gantung.'
            ]
        }
    ]
    
    context = {
        'data_wahana': data_wahana
    }
    
    return render(request, 'data_wahana.html', context)

def tambah_wahana(request):
    return render(request, 'form_tambah_wahana.html')

def edit_wahana(request, nama_wahana):
    data_edit_wahana = [
        {
            'nama_wahana': 'Komedi Putar',
            'kapasitas_max': '40',
            'jadwal': '9:00:00',
            'peraturan': [
                'Anak di bawah 5 tahun harus didampingi orang dewasa.',
                'Dilarang berdiri atau bergerak saat wahana beroperasi.',
                'Pengunjung dengan gangguan jantung disarankan tidak ikut.'
            ]
        },
        {
            'nama_wahana': 'Kereta Gantung',
            'kapasitas_max': '25',
            'jadwal': '8:30:00',
            'peraturan': [
                'Anak di bawah 5 tahun harus didampingi orang dewasa.',
                'Berat maksimum per kereta adalah 150 kg.',
                'Dilarang membuka pintu atau menggoyangkan kereta gantung.'
            ]
        }
    ]

    wahana = next((item for item in data_edit_wahana if item['nama_wahana'] == nama_wahana), None)

    hewan_list = ["Harimau", "Gajah", "Kera", "Burung"]
    pelatih_list = ["Dominic Morgan Dixon", "Zavier Genasis Patel"]

    return render(request, 'form_edit_wahana.html', {
        'wahana': wahana,
        'hewan_list': hewan_list,
        'pelatih_list': pelatih_list,
    })
