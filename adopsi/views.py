from django.shortcuts import render

def program_adopsi_admin(request):
    return render(request, 'adopsi_admin.html')

def form_adopsi_hewan(request):
    return render(request, 'form_adopsi_hewan.html')

def program_adopsi_pengunjung(request):
    return render(request, 'adopsi_pengunjung.html')

def daftar_adopter(request):
    return render(request, 'daftar_adopter.html')

def riwayat_adopter(request, adopter_id):
    return render(request, 'riwayat_adopter.html', {'adopter_id': adopter_id})