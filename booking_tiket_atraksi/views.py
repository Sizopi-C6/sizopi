from django.http import Http404
from django.shortcuts import redirect, render

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

def reservasi_tiket(request):
    atraksi_list = data_reservasi
    return render(request, 'form_reservasi.html', {'atraksi_list': atraksi_list})

def detail_reservasi(request):    
    data = data_reservasi[0]
    return render(request, 'detail_reservasi.html', {'data': data})

def pengunjung_edit_reservasi(request, nama_atraksi):
    selected_data = next((d for d in data_reservasi if d['nama_atraksi'] == nama_atraksi), None)
    if not selected_data:
        return render(request, 'not_found.html', status=404)
    return render(request, 'pengunjung_edit_reservasi.html', {'data': selected_data})

def daftar_reservasi(request):
    return render(request, 'data_reservasi.html', {'data_reservasi': data_reservasi})

def staf_edit_reservasi(request, username, nama_atraksi, tanggal):
    reservasi = next((r for r in data_reservasi if r['username'] == username and r['nama_atraksi'] == nama_atraksi and r['tanggal'] == tanggal), None)
    
    if not reservasi:
        raise Http404("Reservasi tidak ditemukan.")

    return render(request, 'staf_edit_reservasi.html', {'reservasi': reservasi})

def hapus_reservasi(request, username, nama_atraksi, tanggal):
    global data_reservasi
    before = len(data_reservasi)
    data_reservasi = [
        r for r in data_reservasi
        if not (
            r['username'] == username and
            r['nama_atraksi'] == nama_atraksi and
            r['tanggal'] == tanggal
        )
    ]
    if len(data_reservasi) == before:
        raise Http404("Reservasi tidak ditemukan.")
    return redirect('daftar_reservasi')