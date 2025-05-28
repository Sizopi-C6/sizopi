from django.shortcuts import render, redirect
from data_satwa_habitat.forms import SatwaForm, HabitatForm, SatwaUpdateForm, HabitatUpdatedForm
from django.db import connection, DatabaseError
import uuid

def tambah_satwa(request):
    if request.method == 'POST':
        form = SatwaForm(request.POST)
        if form.is_valid():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO hewan (id, name, species, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        str(uuid.uuid4()),
                        form.cleaned_data['name'] or None,
                        form.cleaned_data['species'],
                        form.cleaned_data['asal_hewan'],
                        form.cleaned_data['tanggal_lahir'],
                        form.cleaned_data['status_kesehatan'],
                        form.cleaned_data['nama_habitat'],
                        form.cleaned_data['url_foto'],
                    ])
                    connection.commit()
            except DatabaseError as e:
                error_message = str(e).split('CONTEXT:')[0].strip()
                form.add_error(None, error_message)
            else:
                return redirect('data_satwa_habitat:show_list_satwa')
        else:
            print(form.errors) 
    else:
        print("Masuk ke tambah_satwa")
        form = SatwaForm()

    return render(request, 'data_satwa/tambah_satwa.html', {'form': form})

def show_list_satwa(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hewan")
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    context = {
        'data_satwa': results
    }

    return render(request, 'data_satwa/list_data_satwa.html', context)

def edit_satwa(request, id):
    satwa = find_satwa_by_id(id)
    if not satwa:
        return redirect('data_satwa_habitat:list_data_satwa')

    initial_data = {
        'name': satwa['name'],
        'species': satwa['species'],
        'asal_hewan': satwa['asal_hewan'],
        'tanggal_lahir': satwa['tanggal_lahir'],
        'status_kesehatan': satwa['status_kesehatan'],
        'nama_habitat': satwa['nama_habitat'],
        'url_foto': satwa['url_foto'],
    }

    if request.method == 'POST':
        form = SatwaUpdateForm(request.POST)
        form.initial = initial_data

        # TODO: PAKE INDEX
        if form.is_valid():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE hewan
                        SET name = %s,
                            species = %s,
                            asal_hewan = %s,
                            tanggal_lahir = %s,
                            status_kesehatan = %s,
                            nama_habitat = %s,
                            url_foto = %s
                        WHERE id = %s
                    """, [ 
                        form.cleaned_data.get('name'),
                        form.cleaned_data.get('species'),
                        form.cleaned_data.get('asal_hewan'),
                        form.cleaned_data.get('tanggal_lahir'),
                        form.cleaned_data.get('status_kesehatan'),
                        form.cleaned_data.get('nama_habitat'),
                        form.cleaned_data.get('url_foto'),
                        id
                    ])
                    connection.commit()
            except Exception as e:
                form.add_error(None, f"Gagal memperbarui data: {e}")
            else:
                return redirect('data_satwa_habitat:show_list_satwa')
        else:
            print(form.errors)
    else:
        form = SatwaUpdateForm(initial=initial_data)

    return render(request, 'data_satwa/edit_satwa.html', {'form': form})

def find_satwa_by_id(satwa_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, species, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM hewan
            WHERE id = %s
        """, [str(satwa_id)])
        row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'species': row[2],
                'asal_hewan': row[3],
                'tanggal_lahir': row[4],
                'status_kesehatan': row[5],
                'nama_habitat': row[6],
                'url_foto': row[7],
            }
    return None

def delete_satwa(request, id):
    satwa = find_satwa_by_id(id)
    if not satwa:
        return redirect('data_satwa_habitat:show_list_satwa')
    
    if request.method == 'POST':
        return redirect('data_satwa_habitat:show_list_satwa')
    
    return redirect('data_satwa_habitat:show_list_satwa')

def list_habitat(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM habitat")
        columns = [col[0] for col in cursor.description]
        daftar_habitat = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'data_habitat/list_habitat.html', {
        'daftar_habitat': daftar_habitat
    })

def tambah_habitat(request):
    if request.method == 'POST':
        form = HabitatForm(request.POST)
        if form.is_valid():
            nama = form.cleaned_data['nama']
            luas_area = form.cleaned_data['luas_area']
            kapasitas = form.cleaned_data['kapasitas']
            status = form.cleaned_data['status']

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO habitat (nama, luas_area, kapasitas, status)
                    VALUES (%s, %s, %s, %s)
                """, [nama, luas_area, kapasitas, status])

            return redirect('data_satwa_habitat:list_habitat')
    else:
        form = HabitatForm()

    return render(request, 'data_habitat/tambah_habitat.html', {'form': form})

def edit_habitat(request, habitat_nama):
    with connection.cursor() as cursor:
        cursor.execute("SELECT nama, luas_area, kapasitas, status FROM habitat WHERE nama = %s", [habitat_nama])
        row = cursor.fetchone()
        if not row:
            return redirect('data_satwa_habitat:list_habitat')

    initial_data = {
        'nama': row[0],
        'luas_area': float(row[1]),
        'kapasitas': row[2],
        'status': row[3],
    }
    print("INITIAL: " + str(initial_data))

    if request.method == 'POST':
        form = HabitatUpdatedForm(request.POST)
        form.initial = initial_data
        print("POST data:", request.POST)
        print("Form data:", form.data)
        if form.is_valid():
            print("cleaned_data:", form.cleaned_data)
            nama = form.cleaned_data['nama'] or initial_data['nama']
            luas_area = form.cleaned_data['luas_area'] if form.cleaned_data['luas_area'] is not None else initial_data['luas_area']
            kapasitas = form.cleaned_data['kapasitas'] if form.cleaned_data['kapasitas'] is not None else initial_data['kapasitas']
            status = form.cleaned_data['status'] or initial_data['status']

            print("DEBUG:", nama, luas_area, kapasitas, status)
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE habitat SET
                        nama = %s,
                        luas_area = %s,
                        kapasitas = %s,
                        status = %s
                    WHERE nama = %s
                """, [nama, luas_area, kapasitas, status, habitat_nama])

            return redirect('data_satwa_habitat:list_habitat')
    else:
        form = HabitatUpdatedForm(initial=initial_data)

    return render(request, 'data_habitat/edit_habitat.html', {'form': form, 'habitat_nama': habitat_nama})

def find_habitat_by_name(habitat_nama):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama, luas_area, kapasitas, status 
            FROM habitat 
            WHERE nama = %s
        """, [habitat_nama])
        row = cursor.fetchone()
        if row:
            return {
                'nama': row[0],
                'luas_area': row[1],
                'kapasitas': row[2],
                'status': row[3],
            }
        return None

def detail_habitat(request, habitat_nama):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM habitat WHERE nama = %s", [habitat_nama])
        data_habitat = cursor.fetchone()

        if data_habitat is None:
            return render(request, 'data_habitat/list_habitat.html', {
                'daftar_habitat': []
            })
        print(data_habitat)

        habitat = {
            'nama': data_habitat[0],
            'luas_area': data_habitat[1],
            'status': data_habitat[3],
            'kapasitas': data_habitat[2],
        }

        cursor.execute("SELECT name, species, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto FROM hewan WHERE nama_habitat = %s", [habitat_nama])
        hewan_rows = cursor.fetchall()

        hewan_list = []
        for h in hewan_rows:
            hewan_list.append({
                'name': h[0],
                'species': h[1],
                'asal_hewan': h[2],
                'tanggal_lahir': h[3],
                'status_kesehatan': h[4],
                'nama_habitat': h[5],
                'url_foto': h[6],
            })

    return render(request, 'data_habitat/detail_habitat.html', {
        'habitat': habitat,
        'hewan_list': hewan_list
    })

def delete_habitat(request, habitat_nama):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM habitat WHERE nama = %s", [habitat_nama])

        return redirect('data_satwa_habitat:list_habitat')
    else:
        print("wlee")
    return redirect('data_satwa_habitat:list_habitat')