from django.shortcuts import render

data_reservasi = [
    {
        'username': 'jdoe',
        'nama_atraksi': 'Wahana Safari',
        'lokasi': 'Zona A',      
        'jam': '10:00',          
        'tanggal_kunjungan': '30/04/2025', 
        'jumlah_tiket': 4,       
        'status': 'Terjadwal',   
    },
    {
        'username': 'asmith',
        'nama_atraksi': 'Zona Burung',
        'lokasi': 'Zona E',       
        'jam': '07:45',        
        'tanggal_kunjungan': '01/05/2025',  
        'jumlah_tiket': 5,       
        'status': 'Dibatalkan',     
    },
]

data_edit_reservasi = [
        {
            'username': 'jdoe',
            'nama_atraksi': 'Wahana Safari',
            'lokasi': 'Zona A',
            'jam': '10:00',
            'tanggal_kunjungan': '30/04/2025',
            'jumlah_tiket': 4,
            'status': 'Terjadwal',
        },
        {
            'username': 'asmith',
            'nama_atraksi': 'Zona Burung',
            'lokasi': 'Zona E',       
            'jam': '07:45',        
            'tanggal_kunjungan': '01/05/2025',  
            'jumlah_tiket': 5,       
            'status': 'Dibatalkan',     
        },
    ]

def pengunjung_reservasi_tiket(request):
    atraksi_list = data_reservasi
    return render(request, 'pengunjung_form_reservasi.html', {'atraksi_list': atraksi_list})

def pengunjung_detail_reservasi(request):    
    data = data_reservasi[0]
    return render(request, 'pengunjung_detail_reservasi.html', {'data': data})

def pengunjung_edit_reservasi(request, nama_atraksi):    
    reservasi = next((item for item in data_edit_reservasi if item['nama_atraksi'] == nama_atraksi), None)
    
    atraksi_list = data_edit_reservasi 
    return render(request, 'pengunjung_edit_reservasi.html', {
        'atraksi_list': atraksi_list,
        'reservasi': reservasi
    })

def staf_data_reservasi(request):
    return render(request, 'staf_data_reservasi.html', {'data_reservasi': data_reservasi})

def staf_edit_reservasi(request, username, nama_atraksi):
    reservasi = next((r for r in data_reservasi if r['username'] == username and r['nama_atraksi'] == nama_atraksi), None)
    atraksi_list = data_edit_reservasi
    return render(request, 'staf_edit_reservasi.html', {
        'reservasi': reservasi,
        'atraksi_list': atraksi_list
    })