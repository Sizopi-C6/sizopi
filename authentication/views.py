from django.shortcuts import render, redirect

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