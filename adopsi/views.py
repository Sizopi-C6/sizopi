from django.shortcuts import render

def program_adopsi_admin(request):
    return render(request, 'adopsi_admin.html')

def program_adopsi_pengunjung(request):
    return render(request, 'adopsi_pengunjung.html')

def daftar_adopter(request):
    return render(request, 'daftar_adopter.html')