from django.shortcuts import render, redirect
from data_satwa_habitat.forms import SatwaForm, HabitatForm

daftar_habitat = [
    {'nama': 'Savannah Besar', 'luas_area': 8746.09, 'kapasitas': 10, 'status': 'Perlu Perbaikan'},
    {'nama': 'Hutan Tropis', 'luas_area': 2872.59, 'kapasitas': 33, 'status': 'Baik'},
    {'nama': 'Gurun Panas', 'luas_area': 8352.91, 'kapasitas': 48, 'status': 'Sedang Direstorasi'},
    {'nama': 'Gunung Salju', 'luas_area': 3426.45, 'kapasitas': 29, 'status': 'Perlu Perbaikan'},
    {'nama': 'Padang Rumput', 'luas_area': 1041.87, 'kapasitas': 13, 'status': 'Sedang Direstorasi'},
]

data_satwa = [
    {
        "id": "341980a8-f002-4c07-8553-33338371b297",
        "name": "Manny",
        "species": "Loxodonta africana",
        "asal_hewan": "Tanzania",
        "tanggal_lahir": "2015-05-31",
        "status_kesehatan": "Sehat",
        "nama_habitat": "Savannah Besar",
        "url_foto": "https://upload.wikimedia.org/wikipedia/commons/3/37/African_Bush_Elephant.jpg"
    },
    {
        "id": "64a99631-3623-48ef-90c6-ad2df48a141a",
        "name": "Shere Khan",
        "species": "Panthera tigris",
        "asal_hewan": "India",
        "tanggal_lahir": "2015-10-28",
        "status_kesehatan": "Dalam Pemantauan",
        "nama_habitat": "Hutan Tropis",
        "url_foto": "https://upload.wikimedia.org/wikipedia/commons/0/06/Tigre_de_Sumatra.jpg"
    },
    {
        "id": "bcce867f-2b20-4da1-9105-91cb5ba64988",
        "name": "Baloo",
        "species": "Ursus arctos",
        "asal_hewan": "Indonesia",
        "tanggal_lahir": "2016-03-26",
        "status_kesehatan": "Sehat",
        "nama_habitat": "Hutan Tropis",
        "url_foto": "https://upload.wikimedia.org/wikipedia/commons/e/e2/Grizzlybear55.jpg"
    },
    {
        "id": "29c035c7-a531-473b-9de9-f6dae2bde6f6",
        "name": "Rajah",
        "species": "Panthera tigris",
        "asal_hewan": "India",
        "tanggal_lahir": "2016-08-23",
        "status_kesehatan": "Sakit",
        "nama_habitat": "Hutan Tropis",
        "url_foto": "https://upload.wikimedia.org/wikipedia/commons/1/1c/Tigress_at_Jim_Corbett_National_Park.jpg"
    },
    {
        "id": "5f2b4591-7a02-4e96-a95c-074b1719eba8",
        "name": "Sahara",
        "species": "Camelus dromedarius",
        "asal_hewan": "Mesir",
        "tanggal_lahir": "2017-01-20",
        "status_kesehatan": "Sehat",
        "nama_habitat": "Gurun Panas",
        "url_foto": "https://upload.wikimedia.org/wikipedia/commons/b/b7/Camel_in_Mongolia.jpg"
    }
]

def tambah_satwa(request):
    if request.method == 'POST':
        form = SatwaForm(request.POST)
        if form.is_valid():
            return redirect('tambah_satwa')
    else:
        form = SatwaForm()
    
    return render(request, 'data_satwa/tambah_satwa.html', {'form': form})

def show_list_satwa(request):
    return render(request, 'data_satwa/list_data_satwa.html', {'data_satwa': data_satwa})

def edit_satwa(request, id):
    satwa = find_satwa_by_id(id)
    if not satwa:
        return redirect('data_satwa_habitat:list_data_satwa')
    
    if request.method == 'POST':
        form = SatwaForm(request.POST, edit_mode=True)
        if form.is_valid():
            satwa['asal_hewan'] = form.cleaned_data['asal_hewan']
            satwa['status_kesehatan'] = form.cleaned_data['status_kesehatan']
            return redirect('data_satwa_habitat:list_data_satwa')
    else:
        form = SatwaForm(
            initial={
                'nama_individu': satwa['name'],
                'spesies': satwa['species'],
                'asal_hewan': satwa['asal_hewan'],
                'tanggal_lahir': satwa['tanggal_lahir'],
                'status_kesehatan': satwa['status_kesehatan'],
                'nama_habitat': satwa['nama_habitat'],
                'url_foto': satwa['url_foto'],
            },
            edit_mode=True
        )

    return render(request, 'data_satwa/edit_satwa.html', {'form': form})

def find_satwa_by_id(satwa_id):
    for satwa in data_satwa:
        if satwa['id'] == str(satwa_id):
            return satwa
    return None

def delete_satwa(request, id):
    satwa = find_satwa_by_id(id)
    if not satwa:
        return redirect('data_satwa_habitat:show_list_satwa')
    
    if request.method == 'POST':
        return redirect('data_satwa_habitat:show_list_satwa')
    
    return redirect('data_satwa_habitat:show_list_satwa')

def list_habitat(request):
    return render(request, 'data_habitat/list_habitat.html', {
        'daftar_habitat': daftar_habitat
    })

def tambah_habitat(request):
    if request.method == 'POST':
        form = HabitatForm(request.POST)
        if form.is_valid():
            new_habitat = {
                'nama': form.cleaned_data['nama'],
                'luas_area': form.cleaned_data['luas_area'],
                'kapasitas': form.cleaned_data['kapasitas'],
                'status': form.cleaned_data['status'],
            }
            daftar_habitat.append(new_habitat)
            return redirect('data_satwa_habitat:list_habitat')
    else:
        form = HabitatForm()

    return render(request, 'data_habitat/tambah_habitat.html', {'form': form})

def edit_habitat(request, habitat_nama):
    habitat = find_habitat_by_name(habitat_nama)
    
    if not habitat:
        return redirect('data_satwa_habitat:list_habitat')
    
    if request.method == 'POST':
        form = HabitatForm(request.POST, edit_mode=True)
        if form.is_valid():
            habitat['kapasitas'] = form.cleaned_data['kapasitas']
            habitat['status'] = form.cleaned_data['status']
            return redirect('data_satwa_habitat:list_habitat')
    else:
        form = HabitatForm(
            initial={
                'nama': habitat['nama'],
                'luas_area': habitat['luas_area'],
                'kapasitas': habitat['kapasitas'],
                'status': habitat['status'],
            },
            edit_mode=True
        )

    return render(request, 'data_habitat/edit_habitat.html', {'form': form})

def find_habitat_by_name(habitat_nama):
    for habitat in daftar_habitat:
        if habitat['nama'] == habitat_nama:
            return habitat
    return None


def detail_habitat(request, habitat_nama):
    habitat = next((h for h in daftar_habitat if h['nama'] == habitat_nama), None)
    if habitat is None:
        return render(request, 'data_satwa_habitat:list_habitat')

    hewan_dalam_habitat = [hewan for hewan in data_satwa if hewan['nama_habitat'] == habitat_nama]

    context = {
        'habitat': habitat,
        'hewan_list': hewan_dalam_habitat,
    }
    return render(request, 'data_habitat/detail_habitat.html', context)

def delete_habitat(request, habitat_nama):
    habitat = find_habitat_by_name(habitat_nama)
    if not habitat:
        return redirect('data_satwa_habitat:list_habitat')
    
    if request.method == 'POST':
        return redirect('data_satwa_habitat:list_habitat')
    
    return redirect('data_satwa_habitat:list_habitat')