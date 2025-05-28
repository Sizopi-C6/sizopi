from django.shortcuts import render
from django.db import connection
from django.shortcuts import render, redirect
from django.contrib import messages

def dashboard_view(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    username = user.get('username')

    with connection.cursor() as cursor:
        # data user
        cursor.execute("""
            SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM pengguna
            WHERE username = %s
        """, [username])
        row = cursor.fetchone()

        if not row:
            messages.error(request, 'Data pengguna tidak ditemukan.')
            return redirect('login')

        # role user
        cursor.execute("""
            SELECT CASE
                WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = %s) THEN 'pengunjung'
                WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = %s) THEN 'dokter_hewan'
                WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = %s) THEN 'penjaga_hewan'
                WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = %s) THEN 'pelatih_hewan'
                WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = %s) THEN 'staf_admin'
                ELSE 'unknown'
            END AS role
        """, [username] * 5)
        role = cursor.fetchone()[0]

        formatted_role = role.replace('_', ' ').title()

        role_data = {}
        if role == 'pengunjung':
            cursor.execute("""
                SELECT alamat, tgl_lahir
                FROM pengunjung
                WHERE username_p = %s
            """, [username])
            pengunjung_row = cursor.fetchone()
            if pengunjung_row:
                role_data['alamat'] = pengunjung_row[0]
                role_data['tgl_lahir'] = pengunjung_row[1].strftime('%Y-%m-%d')
        elif role == 'staf_admin':
            cursor.execute("""
                SELECT id_staf FROM staf_admin
                WHERE username_sa = %s
            """, [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'
        elif role == 'dokter_hewan':
            cursor.execute("""
                SELECT no_str FROM dokter_hewan
                WHERE username_dh = %s
            """, [username])
            no_str = cursor.fetchone()
            role_data['no_STR'] = no_str[0] if no_str else '-'
        elif role == 'penjaga_hewan':
            cursor.execute("""
                SELECT id_staf FROM penjaga_hewan
                WHERE username_jh = %s
            """, [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'
        elif role == 'pelatih_hewan':
            cursor.execute("""
                SELECT id_staf FROM pelatih_hewan
                WHERE username_lh = %s
            """, [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'
            
    data_umum = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3] or '',
        'nama_belakang': row[4],
        'phone_number': row[5],
        'role': formatted_role
    }

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
