from django.shortcuts import render, redirect

data_booking = [
    {
        'id': 'a79425c5-94f3-4590-bdac-bfed73b14608',
        'jenis_reservasi': 'Atraksi',
        'nama_atraksi': 'Wahana Safari',
        'lokasi': 'Zona A',
        'jam': '10:00',
        'tanggal_kunjungan': '30/04/2025',
        'jumlah_tiket': 4,
        'status': 'Terjadwal',
    },
    {
        'id': '1de99b83-49a8-44a6-b6e0-b0e9f5813914',
        'jenis_reservasi': 'Wahana',
        'nama_wahana': 'Taman Air Mini',
        'peraturan': [
            "Dilarang Berenang",
            "Dilarang membawa makanan"
        ],
        'jam': '13:00',
        'tanggal_kunjungan': '02/05/2025',
        'jumlah_tiket': 2,
        'status': 'Terjadwal',
    }
]

data_reservasi = [
        {
            'id': 'a79425c5-94f3-4590-bdac-bfed73b14608',
            'jenis_reservasi': 'Atraksi',
            'nama_atraksi': 'Pertunjukan Paus Orca',
            'tanggal_kunjungan': '12-5-2025',
            'kapasitas_tersisa': 10,
            'kapasitas_maksimal': 75
        },
        {
            'id': '1de99b83-49a8-44a6-b6e0-b0e9f5813914',
            'jenis_reservasi': 'Wahana',
            'nama_atraksi': 'Taman Bunga',
            'tanggal_kunjungan': '11-5-2025',
            'kapasitas_tersisa': 5,
            'kapasitas_maksimal': 50
        },
    ]

def pengunjung_data_booking(request):
    context = {
        'data_booking': data_booking
    }
    return render(request, 'pengunjung_data_booking.html', context)

def pengunjung_data_reservasi(request):
    context = {
        'data_reservasi': data_reservasi
    }
    return render(request, 'pengunjung_data_reservasi.html', {'data_reservasi': data_reservasi})

def pengunjung_edit_reservasi(request, reservasi_id):
    booking = next((item for item in data_booking if item['id'] == str(reservasi_id)), None)
    
    if not booking:
        return redirect('pengunjung_data_booking')
    
    atraksi_list = [
        {'nama_atraksi': 'Wahana Safari', 'lokasi': 'Zona A', 'jam': '10:00'},
        {'nama_atraksi': 'Zona Burung', 'lokasi': 'Zona E', 'jam': '07:45'}
    ]
    
    wahana_list = [
        {'nama_wahana': 'Taman Air Mini', 'jam': '13:00', 'peraturan': ["Dilarang Berenang", "Dilarang membawa makanan"]},
        {'nama_wahana': 'Area Petualangan', 'jam': '09:00', 'peraturan': ["Dilarang memanjat pagar"]}
    ]
    
    context = {
        'reservasi': booking,
        'atraksi_list': atraksi_list,
        'wahana_list': wahana_list
    }
    return render(request, 'pengunjung_edit_reservasi.html', context)

def pengunjung_form_reservasi(request, reservasi_id):
    booking = next((item for item in data_booking if item['id'] == str(reservasi_id)), None)

    if not booking:
        return redirect('pengunjung_data_booking')

    if request.method == 'POST':
        tanggal = request.POST.get('tanggal')
        jam = request.POST.get('jam')
        jumlah_tiket = request.POST.get('jumlah-tiket')

        if booking['jenis_reservasi'].lower() == 'atraksi':
            nama_atraksi = request.POST.get('atraksi')
            lokasi = request.POST.get('lokasi')
            booking.update({
                'tanggal': tanggal,
                'jam': jam,
                'jumlah_tiket': jumlah_tiket,
                'nama_atraksi': nama_atraksi,
                'lokasi': lokasi,
            })

        elif booking['jenis_reservasi'].lower() == 'wahana':
            nama_wahana = request.POST.get('wahana')
            peraturan = request.POST.get('peraturan')
            booking.update({
                'tanggal': tanggal,
                'jam': jam,
                'jumlah_tiket': jumlah_tiket,
                'nama_wahana': nama_wahana,
                'peraturan': peraturan,
            })

        return redirect('pengunjung_detail_reservasi', reservasi_id=reservasi_id)

    jenis_reservasi = booking['jenis_reservasi'].lower()

    if jenis_reservasi == 'atraksi':
        atraksi_list = [
            {'nama_atraksi': 'Wahana Safari', 'lokasi': 'Zona A', 'jam': '10:00'},
            {'nama_atraksi': 'Zona Burung', 'lokasi': 'Zona E', 'jam': '07:45'},
            {'nama_atraksi': 'Pertunjukan Paus Orca', 'lokasi': 'Zona D', 'jam': '11:30'},
        ]
        context = {
            'jenis_reservasi': 'Atraksi',
            'atraksi_list': atraksi_list,
            'reservasi_id': reservasi_id
        }

    elif jenis_reservasi == 'wahana':
        wahana_list = [
            {'nama_wahana': 'Roller Coaster', 'peraturan': ['Tinggi minimal 140cm', 'Dilarang membawa makanan'], 'jam': '13:00'},
            {'nama_wahana': 'Kolam Arus', 'peraturan': ['Usia minimal 10 tahun'], 'jam': '11:00'},
            {'nama_wahana': 'Rumah Hantu', 'peraturan': ['Tidak untuk penderita jantung'], 'jam': '16:00'},
        ]
        context = {
            'jenis_reservasi': 'Wahana',
            'wahana_list': wahana_list,
            'reservasi_id': reservasi_id
        }

    else:
        return redirect('pengunjung_data_booking')

    return render(request, 'pengunjung_form_reservasi.html', context)

def pengunjung_detail_reservasi(request, reservasi_id):
    reservasi_id_str = str(reservasi_id)  
    data = next((item for item in data_booking if item['id'] == reservasi_id_str), None)
    
    if not data:
        return render(request, '404.html', status=404)
    return render(request, 'pengunjung_detail_reservasi.html', {'data': data})

def staf_data_atraksi(request):
    data_reservasi = [
        {   
            'id': 'a79425c5-94f3-4590-bdac-bfed73b14608',
            'username': 'Arif',
            'nama_atraksi': 'Pertunjukan lumba-lumba',
            'tanggal_kunjungan': '12-5-2025',
            'jumlah_tiket': 10,
            'status': 'Terjadwal'
        },
        {
            'id': '1de99b83-49a8-44a6-b6e0-b0e9f5813914',
            'username': 'Winnie',
            'nama_atraksi': 'Feeding time harimau',
            'tanggal_kunjungan': '11-5-2025',
            'jumlah_tiket': 3,
            'status': 'Dibatalkan'
        },
    ]
    return render(request, 'staf_data_atraksi.html', {'data_reservasi': data_reservasi})

def staf_data_wahana(request):
    data_reservasi = [
        {
            'id': '1de99b83-49a8-44a6-b6e0-b0e9f5813914',
            'username': 'Budi',
            'jenis_reservasi': 'Wahana',
            'nama_wahana': 'Taman Air Mini',
            'peraturan': [
                "Dilarang Berenang",
                "Dilarang membawa makanan"
            ],
            'jam': '13:00',
            'tanggal_kunjungan': '02/05/2025',
            'jumlah_tiket': 2,
            'status': 'Terjadwal',
        },
        {
            'id': '7fa33b0e-49bc-45a3-b1d7-91e71e04c801',
            'username': 'Dina',
            'jenis_reservasi': 'Wahana',
            'nama_wahana': 'Roller Coaster Jungle',
            'peraturan': [
                "Usia minimum 12 tahun",
                "Tidak disarankan untuk ibu hamil"
            ],
            'jam': '15:00',
            'tanggal_kunjungan': '05/05/2025',
            'jumlah_tiket': 4,
            'status': 'Selesai',
        }
    ]
    return render(request, 'staf_data_wahana.html', {'data_reservasi': data_reservasi})

def staf_edit_reservasi(request, reservasi_id):
    reservasi_id_str = str(reservasi_id)
    reservasi = next((r for r in data_reservasi if r['id'] == reservasi_id_str), None)
    
    if not reservasi:
        return redirect('staf_data_atraksi')
    
    atraksi_list = [
        {'nama_atraksi': 'Pertunjukan lumba-lumba', 'lokasi': 'Zona C', 'jam': '10:30'},
    ]
    wahana_list = [
        {'nama_wahana': 'Wahana Air', 'jam': '09:00', 'peraturan': ["Tidak boleh bawa makanan", "Gunakan pelampung"]},
    ]

    if request.method == 'POST':
        if reservasi['jenis_reservasi'].lower() == 'atraksi':
            reservasi['nama_atraksi'] = request.POST.get('atraksi')
            atraksi = next((a for a in atraksi_list if a['nama_atraksi'] == reservasi['nama_atraksi']), {})
            reservasi['lokasi'] = atraksi.get('lokasi', '')
            reservasi['jam'] = atraksi.get('jam', '')
        else:
            reservasi['nama_wahana'] = request.POST.get('wahana')
            wahana = next((w for w in wahana_list if w['nama_wahana'] == reservasi['nama_wahana']), {})
            reservasi['jam'] = wahana.get('jam', '')
            reservasi['peraturan'] = wahana.get('peraturan', [])

        reservasi['tanggal_kunjungan'] = request.POST.get('tanggal')
        reservasi['jumlah_tiket'] = int(request.POST.get('jumlah_tiket'))

        return redirect('staf_data_atraksi')

    return render(request, 'staf_edit_reservasi.html', {
        'reservasi': reservasi,
        'atraksi_list': atraksi_list,
        'wahana_list': wahana_list,
    })
