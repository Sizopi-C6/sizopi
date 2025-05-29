import json
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime

def pengunjung_data_reservasi(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                f.nama AS nama_atraksi,
                CASE
                    WHEN f.nama IN (SELECT nama_atraksi FROM atraksi) THEN 'Atraksi'
                    ELSE 'Wahana'
                END AS jenis_reservasi,
                TO_CHAR(f.jadwal, 'DD-MM-YYYY') AS tanggal_kunjungan,  -- hanya tanggal
                f.kapasitas_max,
                -- hitung kapasitas tersisa = kapasitas max - total jumlah tiket yang 'Terjadwal'
                f.kapasitas_max - COALESCE(SUM(CASE WHEN r.status = 'Terjadwal' THEN r.jumlah_tiket ELSE 0 END), 0) AS kapasitas_tersisa,
                f.kapasitas_max AS kapasitas_maksimal,
                f.nama AS id  -- pakai nama sebagai id
            FROM fasilitas f
            LEFT JOIN reservasi r
                ON f.nama = r.nama_atraksi
                AND f.jadwal::date = r.tanggal_kunjungan
            GROUP BY f.nama, f.jadwal, f.kapasitas_max
            ORDER BY f.jadwal ASC
        """)
        columns = [col[0] for col in cursor.description]
        data_reservasi = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'pengunjung_data_reservasi.html', {
        'data_reservasi': data_reservasi
    })

def pengunjung_form_reservasi(request, reservasi_id):
    user = request.session.get('user')
    if not user:
        return redirect('login_page')
    
    if isinstance(user, dict):
        user = user.get('username')

    jenis_reservasi = None
    atraksi_list = []
    wahana_list = []
    data_fasilitas = None

    if request.method == 'POST':
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah-tiket', 0))
        atraksi_pilih = request.POST.get('atraksi')
        wahana_pilih = request.POST.get('wahana')

        # Coba parse JSON jika ada
        for var_name in ['atraksi_pilih', 'wahana_pilih']:
            val = locals()[var_name]
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    locals()[var_name] = parsed.get('nama') or val
            except Exception:
                pass

        if atraksi_pilih and isinstance(atraksi_pilih, str):
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reservasi (username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, [user, atraksi_pilih, tanggal, jumlah_tiket, 'Terjadwal'])
            return redirect('pengunjung_detail_reservasi', username=user, nama_atraksi=atraksi_pilih, tanggal_kunjungan=tanggal)

        elif wahana_pilih and isinstance(wahana_pilih, str):
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reservasi (username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, [user, wahana_pilih, tanggal, jumlah_tiket, 'Terjadwal'])
            return redirect('pengunjung_detail_reservasi', username=user, nama_atraksi=wahana_pilih, tanggal_kunjungan=tanggal)


        else:
            messages.error(request, "Pilih atraksi atau wahana terlebih dahulu.")
            return redirect('pengunjung_form_reservasi', reservasi_id=reservasi_id)

        return redirect('pengunjung_detail_reservasi', reservasi_id=new_reservasi_id)

    # Jika GET, lanjutkan dengan ambil data seperti biasa
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.nama_atraksi,
                a.lokasi,
                f.jadwal,
                f.kapasitas_max
            FROM atraksi a
            JOIN fasilitas f ON a.nama_atraksi = f.nama
            WHERE a.nama_atraksi = %s
        """, [reservasi_id])
        atraksi = cursor.fetchone()

        if atraksi:
            jenis_reservasi = 'Atraksi'
            data_fasilitas = {
                'nama': atraksi[0],
                'lokasi': atraksi[1],
                'jadwal': atraksi[2],
                'kapasitas_max': atraksi[3],
            }
        else:
            cursor.execute("""
                SELECT w.nama_wahana, w.peraturan, f.jadwal, f.kapasitas_max
                FROM wahana w
                JOIN fasilitas f ON w.nama_wahana = f.nama
                WHERE w.nama_wahana = %s
            """, [reservasi_id])
            wahana = cursor.fetchone()
            if wahana:
                jenis_reservasi = 'Wahana'
                data_fasilitas = {
                    'nama': wahana[0],
                    'peraturan': wahana[1],
                    'jadwal': wahana[2],
                    'kapasitas_max': wahana[3],
                }

        # Ambil list atraksi dan wahana untuk dropdown (sama seperti sebelumnya)
        cursor.execute("""
            SELECT a.nama_atraksi, a.lokasi, f.jadwal
            FROM atraksi a
            JOIN fasilitas f ON a.nama_atraksi = f.nama
        """)
        atraksi_list = [
            {
                'nama_atraksi': row[0],
                'lokasi': row[1],
                'jam': row[2].strftime('%H:%M') if row[2] else ''
            } for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT w.nama_wahana, w.peraturan, f.jadwal
            FROM wahana w
            JOIN fasilitas f ON w.nama_wahana = f.nama
        """)
        import json
        wahana_list = []
        for row in cursor.fetchall():
            try:
                peraturan_parsed = json.loads(row[1])
            except Exception:
                peraturan_parsed = [row[1]]

            wahana_list.append({
                'nama_wahana': row[0],
                'peraturan': peraturan_parsed,
                'jam': row[2].strftime('%H:%M') if row[2] else '',
            })

    context = {
        'jenis_reservasi': jenis_reservasi,
        'reservasi_id': reservasi_id,
        'atraksi_list': atraksi_list,
        'wahana_list': wahana_list,
        'data_fasilitas': data_fasilitas,
    }

    return render(request, 'pengunjung_form_reservasi.html', context)

def pengunjung_detail_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    try:
        tanggal_obj = datetime.strptime(tanggal_kunjungan, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Format tanggal salah, harus YYYY-MM-DD")

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT r.username_p, r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
                   a.lokasi, f.jadwal, NULL as peraturan, 'Atraksi' as jenis
            FROM reservasi r
            JOIN atraksi a ON r.nama_atraksi = a.nama_atraksi
            JOIN fasilitas f ON r.nama_atraksi = f.nama
            WHERE r.username_p = %s AND r.nama_atraksi = %s AND r.tanggal_kunjungan = %s
        ''', [username, nama_atraksi, tanggal_obj])

        row = cursor.fetchone()

        if not row:
            cursor.execute('''
                SELECT r.username_p, r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
                       NULL as lokasi, f.jadwal, w.peraturan, 'Wahana' as jenis
                FROM reservasi r
                JOIN wahana w ON r.nama_atraksi = w.nama_wahana
                JOIN fasilitas f ON r.nama_atraksi = f.nama
                WHERE r.username_p = %s AND r.nama_atraksi = %s AND r.tanggal_kunjungan = %s
            ''', [username, nama_atraksi, tanggal_obj])
            row = cursor.fetchone()

    if not row:
        return HttpResponse("Reservasi tidak ditemukan")

    # Parse peraturan jika dari wahana
    import json
    try:
        peraturan = json.loads(row[7]) if row[7] else []
    except Exception:
        peraturan = [row[7]] if row[7] else []

    context = {
        'data': {
            'username_p': row[0],
            'nama_atraksi' : row[1],
            'tanggal': row[2],
            'jumlah_tiket': row[3],
            'status': row[4],
            'lokasi': row[5] or '-',  # Lokasi bisa null di wahana
            'jam': row[6].strftime('%H:%M') if row[6] else '-',
            'jenis_reservasi': row[8],
            'peraturan': peraturan
        }
    }

    return render(request, 'pengunjung_detail_reservasi.html', context)

def pengunjung_data_booking(request):
    user = request.session.get('user')
    if not user:
        return redirect('login_page')

    if isinstance(user, dict):
        username = user.get('username')
    else:
        username = user  

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                username_p,
                nama_atraksi,
                tanggal_kunjungan,
                jumlah_tiket,
                status,
                CASE 
                    WHEN nama_atraksi IN (SELECT nama_atraksi FROM atraksi) THEN 'Atraksi'
                    ELSE 'Wahana'
                END as jenis_reservasi
            FROM reservasi
            WHERE username_p = %s
            ORDER BY tanggal_kunjungan ASC
        """, [username])
        rows = cursor.fetchall()

    data_booking = []
    for row in rows:
        data_booking.append({
            'username': row[0],
            'nama_atraksi': row[1],
            'tanggal_kunjungan': row[2],
            'jumlah_tiket': row[3],
            'status': row[4],
            'jenis_reservasi': row[5],
        })
    return render(request, 'pengunjung_data_booking.html', {'data_booking': data_booking})

def pengunjung_edit_reservasi(request, username, nama_atraksi, tanggal_kunjungan):

    try:
        tanggal_kunjungan_obj = datetime.strptime(tanggal_kunjungan, '%Y-%m-%d').date()
    except ValueError:
        return redirect('pengunjung_data_booking')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status
            FROM reservasi
            WHERE username_p = %s AND nama_atraksi = %s AND tanggal_kunjungan = %s
        """, [username, nama_atraksi, tanggal_kunjungan_obj])
        row = cursor.fetchone()

        if not row:
            return redirect('pengunjung_data_booking')

        cursor.execute("SELECT COUNT(*) FROM atraksi WHERE nama_atraksi = %s", [nama_atraksi])
        is_atraksi = cursor.fetchone()[0] > 0

        if is_atraksi:
            jenis_reservasi = 'Atraksi'
            cursor.execute("SELECT lokasi FROM atraksi WHERE nama_atraksi = %s", [nama_atraksi])
            lokasi_row = cursor.fetchone()
            lokasi = lokasi_row[0] if lokasi_row else None
            peraturan = []
        else:
            jenis_reservasi = 'Wahana'
            lokasi = None
            cursor.execute("SELECT peraturan FROM wahana WHERE nama_wahana = %s", [nama_atraksi])
            wahana_row = cursor.fetchone()
            if wahana_row:
                peraturan_str = wahana_row[0]
                peraturan = [p.strip() for p in peraturan_str.split('\n') if p.strip()]
            else:
                peraturan = []

        # Ambil jadwal fasilitas
        cursor.execute("SELECT jadwal FROM fasilitas WHERE nama = %s", [nama_atraksi])
        fasilitas_row = cursor.fetchone()
        jam = fasilitas_row[0] if fasilitas_row else None

    # Jika POST, proses update data reservasi
    if request.method == 'POST':
        tanggal_baru_str = request.POST.get('tanggal')
        jumlah_tiket_baru = request.POST.get('jumlah_tiket')

        try:
            tanggal_baru = datetime.strptime(tanggal_baru_str, '%d/%m/%Y').date()
            jumlah_tiket_baru = int(jumlah_tiket_baru)
            if jumlah_tiket_baru < 1:
                raise ValueError('Jumlah tiket minimal 1')
        except Exception as e:
            return redirect('pengunjung_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE reservasi
                SET tanggal_kunjungan = %s, jumlah_tiket = %s
                WHERE username_p = %s AND nama_atraksi = %s AND tanggal_kunjungan = %s
            """, [tanggal_baru, jumlah_tiket_baru, username, nama_atraksi, tanggal_kunjungan_obj])

        return redirect('pengunjung_data_booking')

    reservasi = {
        'username': row[0],
        'nama_booking': row[1],
        'tanggal_kunjungan': row[2],
        'jumlah_tiket': row[3],
        'status': row[4],
        'peraturan': peraturan,
        'jam': jam,
        'lokasi': lokasi,
        'jenis_reservasi': jenis_reservasi,
    }

    return render(request, 'pengunjung_edit_reservasi.html', {'reservasi': reservasi})

def staf_data_atraksi(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                r.username_p, 
                r.nama_atraksi, 
                r.tanggal_kunjungan, 
                r.jumlah_tiket, 
                r.status
            FROM reservasi r
            JOIN atraksi a ON r.nama_atraksi = a.nama_atraksi
        """)
        rows = cursor.fetchall()

    data_reservasi = []
    for row in rows:
        data_reservasi.append({
            'username': row[0],
            'nama_atraksi': row[1],
            'tanggal_kunjungan': row[2],
            'tanggal_kunjungan_url': row[2].strftime('%Y-%m-%d') if hasattr(row[2], 'strftime') else row[2],
            'jumlah_tiket': row[3],
            'status': row[4],
        })

    return render(request, 'staf_data_atraksi.html', {'data_reservasi': data_reservasi})

def staf_data_wahana(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                r.username_p,
                r.nama_atraksi,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status,
                w.peraturan,
                f.jadwal
            FROM reservasi r
            JOIN wahana w ON r.nama_atraksi = w.nama_wahana
            JOIN fasilitas f ON w.nama_wahana = f.nama
        """)
        rows = cursor.fetchall()

    data_reservasi = []
    for row in rows:
        username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status, peraturan_raw, jadwal = row

        # Asumsikan peraturan disimpan sebagai teks multiline
        if peraturan_raw:
            peraturan = [p.strip() for p in peraturan_raw.strip().split('\n') if p.strip()]
        else:
            peraturan = []

        jam = jadwal.strftime('%H:%M') if jadwal else ''

        data_reservasi.append({
            'username': username_p,
            'jenis_reservasi': 'Wahana',
            'nama_atraksi': nama_atraksi,
            'tanggal_kunjungan': tanggal_kunjungan,
            'tanggal_kunjungan_url': tanggal_kunjungan.strftime('%Y-%m-%d') if hasattr(tanggal_kunjungan, 'strftime') else tanggal_kunjungan,
            'peraturan': peraturan,
            'jam': jam,
            'jumlah_tiket': jumlah_tiket,
            'status': status,
        })

    return render(request, 'staf_data_wahana.html', {'data_reservasi': data_reservasi})

def staf_edit_reservasi(request, username, nama_atraksi, tanggal_kunjungan):

    try:
        tanggal_kunjungan_obj = datetime.strptime(tanggal_kunjungan, '%Y-%m-%d').date()
    except ValueError:
        return redirect('staf_data_atraksi')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status
            FROM reservasi
            WHERE username_p = %s AND nama_atraksi = %s AND tanggal_kunjungan = %s
        """, [username, nama_atraksi, tanggal_kunjungan_obj])
        row = cursor.fetchone()

        if not row:
            return redirect('staf_data_atraksi')

        cursor.execute("SELECT COUNT(*) FROM atraksi WHERE nama_atraksi = %s", [nama_atraksi])
        is_atraksi = cursor.fetchone()[0] > 0

        if is_atraksi:
            jenis_reservasi = 'Atraksi'
            cursor.execute("SELECT lokasi FROM atraksi WHERE nama_atraksi = %s", [nama_atraksi])
            lokasi_row = cursor.fetchone()
            lokasi = lokasi_row[0] if lokasi_row else None
            peraturan = []
        else:
            jenis_reservasi = 'Wahana'
            lokasi = None
            cursor.execute("SELECT peraturan FROM wahana WHERE nama_wahana = %s", [nama_atraksi])
            wahana_row = cursor.fetchone()
            if wahana_row:
                peraturan_str = wahana_row[0]
                peraturan = [p.strip() for p in peraturan_str.split('\n') if p.strip()]
            else:
                peraturan = []

        cursor.execute("SELECT jadwal FROM fasilitas WHERE nama = %s", [nama_atraksi])
        fasilitas_row = cursor.fetchone()
        jam = fasilitas_row[0] if fasilitas_row else None

    # Jika POST, proses update data reservasi
    if request.method == 'POST':
        tanggal_baru_str = request.POST.get('tanggal')
        jumlah_tiket_baru = request.POST.get('jumlah_tiket')

        try:
            tanggal_baru = datetime.strptime(tanggal_baru_str, '%d/%m/%Y').date()
            jumlah_tiket_baru = int(jumlah_tiket_baru)
            if jumlah_tiket_baru < 1:
                raise ValueError('Jumlah tiket minimal 1')
        except Exception as e:
            return redirect('staf_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE reservasi
                SET tanggal_kunjungan = %s, jumlah_tiket = %s
                WHERE username_p = %s AND nama_atraksi = %s AND tanggal_kunjungan = %s
            """, [tanggal_baru, jumlah_tiket_baru, username, nama_atraksi, tanggal_kunjungan_obj])

        if is_atraksi:
            return redirect('staf_data_atraksi')
        else:
            return redirect('staf_data_wahana')
        

    reservasi = {
        'username': row[0],
        'nama_booking': row[1],
        'tanggal_kunjungan': row[2],
        'jumlah_tiket': row[3],
        'status': row[4],
        'peraturan': peraturan,
        'jam': jam,
        'lokasi': lokasi,
        'jenis_reservasi': jenis_reservasi,
    }

    return render(request, 'staf_edit_reservasi.html', {'reservasi': reservasi})

def batalkan_reservasi(request):
    try:
        data = json.loads(request.body)
        username = data['username']
        nama_atraksi = data['nama_atraksi']
        tanggal_kunjungan = data['tanggal_kunjungan']  
        

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE reservasi
                SET status = 'Dibatalkan'
                WHERE username_p = %s AND nama_atraksi = %s AND tanggal_kunjungan = %s
            """, [username, nama_atraksi, tanggal_kunjungan])

        return JsonResponse({'message': 'Reservasi berhasil dibatalkan'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)