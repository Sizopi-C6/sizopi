from django.shortcuts import render

def rekam_medis_hewan(request):
    return render(request, 'rekam_medis_hewan.html')

def penjadwalan_pemeriksaan_kesehatan(request):
    return render(request, 'penjadwalan_pemeriksaan_kesehatan.html')