from collections import defaultdict
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.db import connection
from django.shortcuts import render, redirect
from django.contrib import messages

def dashboard_view(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    username = user.get('username')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM pengguna
            WHERE username = %s
        """, [username])
        row = cursor.fetchone()

        if not row:
            messages.error(request, 'Data pengguna tidak ditemukan.')
            return redirect('login')

        cursor.execute("""
            SELECT CASE
                WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = %s) THEN 'pengunjung'
                WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = %s) THEN 'dokter_hewan'
                WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = %s) THEN 'penjaga_hewan'
                WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = %s) THEN 'pelatih_hewan'
                WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = %s) THEN 'staf_admin'
                ELSE 'unknown'
            END AS role
        """, [username] * 5)
        role = cursor.fetchone()[0]
        formatted_role = role.replace('_', ' ').title()

        role_data = {}
        if role == 'pengunjung':
            cursor.execute("""
                SELECT alamat, tgl_lahir
                FROM pengunjung
                WHERE username_p = %s
            """, [username])
            pengunjung_row = cursor.fetchone()
            if pengunjung_row:
                role_data['alamat'] = pengunjung_row[0]
                role_data['tgl_lahir'] = pengunjung_row[1].strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT nama_atraksi, jumlah_tiket
                FROM reservasi
                WHERE username_p = %s AND status = 'Terjadwal'
            """, [username])
            tiket_rows = cursor.fetchall()
            if tiket_rows:
                role_data['info_tiket_dibeli'] = [
                    f"{row[0]} - {row[1]} tiket" for row in tiket_rows
                ]
            else:
                role_data['info_tiket_dibeli'] = ["Tidak ada"]

            today = date.today()
            cursor.execute("""
                SELECT tanggal_kunjungan, nama_atraksi, jumlah_tiket
                FROM reservasi
                WHERE username_p = %s AND tanggal_kunjungan < %s
            """, [username, today])
            riwayat_rows = cursor.fetchall()
            if riwayat_rows:
                role_data['riwayat_kunjungan'] = [
                    f"{r[0].strftime('%Y-%m-%d')} - {r[1]} - {r[2]} tiket" for r in riwayat_rows
                ]
            else:
                role_data['riwayat_kunjungan'] = ["Tidak ada"]

        elif role == 'staf_admin':
            cursor.execute("SELECT id_staf FROM staf_admin WHERE username_sa = %s", [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'

            today = date.today()

            cursor.execute("""
                SELECT COUNT(DISTINCT username_p)
                FROM reservasi
                WHERE tanggal_kunjungan = %s AND status = 'Terjadwal'
            """, [today])
            pengunjung_hari_ini = cursor.fetchone()[0]
            role_data['jumlah_pengunjung_hari_ini'] = pengunjung_hari_ini or "Tidak ada pengunjung"

            cursor.execute("""
                SELECT nama_atraksi, SUM(jumlah_tiket)
                FROM reservasi
                WHERE tanggal_kunjungan = %s AND status = 'Terjadwal'
                GROUP BY nama_atraksi
            """, [today])
            tiket_data = cursor.fetchall()

            if tiket_data:
                role_data['ringkasan_penjualan_tiket'] = {
                    row[0]: row[1] for row in tiket_data
                }
            else:
                role_data['ringkasan_penjualan_tiket'] = None


            minggu_terakhir = [today - timedelta(days=i) for i in range(7)]
            laporan_mingguan = {}

            for tanggal in minggu_terakhir[::-1]:
                cursor.execute("""
                    SELECT COALESCE(SUM(kontribusi_finansial), 0)
                    FROM adopsi
                    WHERE status_pembayaran = 'Lunas'
                    AND tgl_mulai_adopsi <= %s AND tgl_berhenti_adopsi >= %s
                """, [tanggal, tanggal])
                total = cursor.fetchone()[0]
                laporan_mingguan[tanggal.strftime('%A')] = total

            role_data['laporan_pendapatan_mingguan'] = laporan_mingguan

        elif role == 'dokter_hewan':
            cursor.execute("SELECT no_str FROM dokter_hewan WHERE username_dh = %s", [username])
            no_str = cursor.fetchone()
            role_data['no_STR'] = no_str[0] if no_str else '-'

            # Ambil daftar spesialisasi dari tabel spesialisasi
            cursor.execute("""
                SELECT nama_spesialisasi
                FROM spesialisasi
                WHERE username_sh = %s
            """, [username])
            spesialisasi_rows = cursor.fetchall()
            role_data['nama_spesialisasi'] = [row[0] for row in spesialisasi_rows] if spesialisasi_rows else []

            # Hitung jumlah hewan unik yang pernah ditangani di catatan medis
            cursor.execute("""
                SELECT COUNT(DISTINCT id_hewan)
                FROM catatan_medis
                WHERE username_dh = %s
            """, [username])
            jumlah = cursor.fetchone()
            role_data['jumlah_hewan_ditangani'] = jumlah[0] if jumlah else 0

        elif role == 'penjaga_hewan':
            # Ambil ID staf
            cursor.execute("SELECT id_staf FROM penjaga_hewan WHERE username_jh = %s", [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'

            # Hitung jumlah unik hewan yang diberi pakan oleh penjaga ini
            cursor.execute("""
                SELECT COUNT(DISTINCT id_hewan)
                FROM memberi
                WHERE username_jh = %s
            """, [username])
            jumlah = cursor.fetchone()
            role_data['jumlah_hewan_diberi_pakan'] = jumlah[0] if jumlah else 0

        elif role == 'pelatih_hewan':
            # ID staf
            cursor.execute("SELECT id_staf FROM pelatih_hewan WHERE username_lh = %s", [username])
            id_staf = cursor.fetchone()
            role_data['id_staf'] = id_staf[0] if id_staf else '-'

            today = date.today()

            # Jadwal pertunjukan hari ini
            cursor.execute("""
                SELECT nama_atraksi
                FROM jadwal_penugasan
                WHERE username_lh = %s AND tgl_penugasan = %s
            """, [username, today])
            jadwal_rows = cursor.fetchall()
            role_data['jadwal_pertunjukan_hari_ini'] = [row[0] for row in jadwal_rows] if jadwal_rows else ["Tidak ada jadwal"]

            # Daftar hewan yang dilatih (nama dan spesies hewan)
            cursor.execute("""
                SELECT DISTINCT h.name, h.species
                FROM berpartisipasi b
                JOIN hewan h ON b.id_hewan = h.id
                WHERE b.nama_fasilitas IN (
                    SELECT DISTINCT nama_atraksi
                    FROM jadwal_penugasan
                    WHERE username_lh = %s
                )
            """, [username])
            hewan_rows = cursor.fetchall()

            role_data['daftar_hewan_dilatih'] = (
                [f"{row[0]} ({row[1]})" for row in hewan_rows]
                if hewan_rows else ["Tidak ada hewan"]
            )

            cursor.execute("""
                SELECT MAX(tgl_penugasan)
                FROM jadwal_penugasan
                WHERE username_lh = %s
            """, [username])
            last_training_date = cursor.fetchone()[0]

            if last_training_date:
                last_training_date = last_training_date.date()  

            if not last_training_date:
                role_data['status_latihan_terakhir'] = "Tidak ada penugasan"
            elif last_training_date == today:
                role_data['status_latihan_terakhir'] = "Berlangsung"
            elif last_training_date < today:
                role_data['status_latihan_terakhir'] = "Selesai"
            else:
                role_data['status_latihan_terakhir'] = "Dijadwalkan"

    data_umum = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3] or '',
        'nama_belakang': row[4],
        'phone_number': row[5],
        'role': formatted_role
    }

    context = {
        'data_umum': data_umum,
        'role_data': role_data
    }

    return render(request, 'dashboard.html', context)

def data_atraksi(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
              a.nama_atraksi,
              a.lokasi,
              TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
              f.kapasitas_max,
              h.name AS nama_hewan,
              p.nama_depan,
              p.nama_tengah,
              p.nama_belakang
            FROM atraksi a
            JOIN fasilitas f ON a.nama_atraksi = f.nama
            LEFT JOIN berpartisipasi b ON a.nama_atraksi = b.nama_fasilitas
            LEFT JOIN hewan h ON b.id_hewan = h.id
            LEFT JOIN jadwal_penugasan j ON a.nama_atraksi = j.nama_atraksi
            LEFT JOIN pengguna p ON j.username_lh = p.username
            ORDER BY a.nama_atraksi
        """)
        rows = cursor.fetchall()

    data_dict = defaultdict(lambda: {
        'nama_atraksi': '',
        'lokasi': '',
        'jadwal': '',
        'kapasitas_max': 0,
        'nama_hewan': set(),
        'nama_pelatih': set()
    })

    for nama_atraksi, lokasi, jam, kapasitas, nama_hewan, nama_depan, nama_tengah, nama_belakang in rows:
        entry = data_dict[nama_atraksi]
        entry['nama_atraksi'] = nama_atraksi
        entry['lokasi'] = lokasi
        entry['jadwal'] = jam
        entry['kapasitas_max'] = kapasitas

        if nama_hewan:
            entry['nama_hewan'].add(nama_hewan)

        if nama_depan or nama_belakang:
            nama_lengkap = " ".join(filter(None, [nama_depan, nama_tengah, nama_belakang]))
            entry['nama_pelatih'].add(nama_lengkap)

    data_atraksi = []
    for item in data_dict.values():
        data_atraksi.append({
            'nama_atraksi': item['nama_atraksi'],
            'lokasi': item['lokasi'],
            'jadwal': item['jadwal'],
            'kapasitas_max': item['kapasitas_max'],
            'nama_hewan': list(item['nama_hewan']) if item['nama_hewan'] else [],
            'nama_pelatih': list(item['nama_pelatih']) if item['nama_pelatih'] else ["Belum ditugaskan"]
        })

    context = {'data_atraksi': data_atraksi}
    return render(request, 'data_atraksi.html', context)

def tambah_atraksi(request):
    if request.method == 'POST':
        data = request.POST
        nama_atraksi = data.get('nama_atraksi')
        lokasi = data.get('lokasi')
        jam_input = data.get('jadwal')  
        kapasitas = data.get('kapasitas_max')
        pelatih_fullname = data.get('pelatih')
        hewan_terpilih = data.getlist('hewan')

        # Validasi input
        if not all([nama_atraksi, lokasi, jam_input, kapasitas, pelatih_fullname]):
            return HttpResponse("Data tidak lengkap", status=400)

        try:
            kapasitas = int(kapasitas)
            waktu = datetime.strptime(jam_input, "%H:%M").time()
        except ValueError:
            return HttpResponse("Format jam harus HH:MM dan kapasitas harus angka", status=400)

        # Gabungkan tanggal sekarang dengan waktu input user
        jadwal_timestamp = datetime.combine(timezone.now().date(), waktu)

        with connection.cursor() as cursor:
            # Ambil username pelatih dari fullname
            cursor.execute("""
                SELECT p.username_lh
                FROM pelatih_hewan p
                JOIN pengguna u ON p.username_lh = u.username
                WHERE CONCAT_WS(' ', u.nama_depan, u.nama_tengah, u.nama_belakang) = %s
            """, [pelatih_fullname])
            result = cursor.fetchone()
            if not result:
                return HttpResponse("Pelatih tidak ditemukan", status=400)
            username_pelatih = result[0]

            # Insert ke tabel fasilitas
            cursor.execute("""
                INSERT INTO fasilitas (nama, jadwal, kapasitas_max)
                VALUES (%s, %s, %s)
            """, [nama_atraksi, jadwal_timestamp, kapasitas])

            # Insert ke tabel atraksi
            cursor.execute("""
                INSERT INTO atraksi (nama_atraksi, lokasi)
                VALUES (%s, %s)
            """, [nama_atraksi, lokasi])

            # Insert jadwal penugasan pakai jadwal_timestamp juga
            cursor.execute("""
                INSERT INTO jadwal_penugasan (nama_atraksi, username_lh, tgl_penugasan)
                VALUES (%s, %s, %s)
            """, [nama_atraksi, username_pelatih, jadwal_timestamp])

            # Insert relasi hewan yang berpartisipasi
            for hewan in hewan_terpilih:
                nama_hewan = hewan.split(' (')[0]
                cursor.execute("SELECT id FROM hewan WHERE name = %s", [nama_hewan])
                hasil = cursor.fetchone()
                if hasil:
                    cursor.execute("""
                        INSERT INTO berpartisipasi (nama_fasilitas, id_hewan)
                        VALUES (%s, %s)
                    """, [nama_atraksi, hasil[0]])

        return redirect('data_atraksi')

    # GET: Ambil data pelatih & hewan untuk form
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT CONCAT_WS(' ', u.nama_depan, u.nama_tengah, u.nama_belakang)
            FROM pelatih_hewan p
            JOIN pengguna u ON p.username_lh = u.username
        """)
        pelatih_list = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT name, species FROM hewan")
        hewan_list = [f"{name} ({species})" for name, species in cursor.fetchall()]

    return render(request, 'form_tambah_atraksi.html', {
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list
    })

def edit_atraksi(request, nama_atraksi):
    if request.method == 'POST':
        # Ambil data dari form
        kapasitas = request.POST.get('kapasitas')
        jadwal_waktu = request.POST.get('jadwal_waktu')

        jadwal = datetime.today().strftime('%Y-%m-%d') + ' ' + jadwal_waktu

        # Simpan perubahan ke DB
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE fasilitas
                SET kapasitas_max = %s,
                    jadwal = %s::timestamp
                WHERE nama = %s
            """, [kapasitas, jadwal, nama_atraksi])

        return redirect('data_atraksi')

    # GET: ambil data untuk form
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
              a.nama_atraksi,
              a.lokasi,
              TO_CHAR(f.jadwal, 'HH24:MI') AS jam,
              f.kapasitas_max,
              p.nama_depan,
              p.nama_tengah,
              p.nama_belakang
            FROM atraksi a
            JOIN fasilitas f ON a.nama_atraksi = f.nama
            LEFT JOIN jadwal_penugasan j ON a.nama_atraksi = j.nama_atraksi
            LEFT JOIN pengguna p ON j.username_lh = p.username
            WHERE a.nama_atraksi = %s
            LIMIT 1
        """, [nama_atraksi])
        row = cursor.fetchone()

        if not row:
            return redirect('data_atraksi')

        atraksi = {
            'nama_atraksi': row[0],
            'lokasi': row[1],
            'jadwal': row[2],
            'kapasitas_max': row[3],
            'nama_depan': row[4] or '',
            'nama_tengah': row[5] or '',
            'nama_belakang': row[6] or '',
        }
        atraksi['pelatih'] = f"{atraksi['nama_depan']} {atraksi['nama_tengah']} {atraksi['nama_belakang']}".strip()

        # Daftar pelatih
        cursor.execute("""
            SELECT DISTINCT p.nama_depan, p.nama_tengah, p.nama_belakang
            FROM pengguna p
            JOIN jadwal_penugasan j ON p.username = j.username_lh
        """)
        pelatih_rows = cursor.fetchall()
        pelatih_list = [
            f"{r[0]} {r[1]} {r[2]}".strip() if r[1] else f"{r[0]} {r[2]}".strip()
            for r in pelatih_rows
        ]

        # Hewan atraksi ini
        cursor.execute("""
            SELECT h.name
            FROM berpartisipasi b
            JOIN hewan h ON b.id_hewan = h.id
            WHERE b.nama_fasilitas = %s
        """, [nama_atraksi])
        atraksi_hewan_rows = cursor.fetchall()
        atraksi['hewan'] = [r[0] for r in atraksi_hewan_rows]

        # Semua hewan
        cursor.execute("SELECT name FROM hewan")
        hewan_all_rows = cursor.fetchall()
        hewan_list = [r[0] for r in hewan_all_rows]

    return render(request, 'form_edit_atraksi.html', {
        'atraksi': atraksi,
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list,
    })

def hapus_atraksi(request, nama_atraksi):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas = %s", [nama_atraksi])
        cursor.execute("DELETE FROM jadwal_penugasan WHERE nama_atraksi = %s", [nama_atraksi])
        cursor.execute("DELETE FROM atraksi WHERE nama_atraksi = %s", [nama_atraksi])
        cursor.execute("DELETE FROM fasilitas WHERE nama = %s", [nama_atraksi])

    return redirect('data_atraksi')

def data_wahana(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT w.nama_wahana, w.peraturan, TO_CHAR(f.jadwal, 'HH24:MI') AS jadwal, f.kapasitas_max
            FROM wahana w
            JOIN fasilitas f ON w.nama_wahana = f.nama
        """)
        rows = cursor.fetchall()

    data_wahana = []
    for nama_wahana, peraturan_str, jadwal, kapasitas_max in rows:
        if peraturan_str:
            # Asumsi peraturan disimpan newline separated
            peraturan_list = peraturan_str.strip().split("\n")
        else:
            peraturan_list = []

        data_wahana.append({
            'nama_wahana': nama_wahana,
            'peraturan': peraturan_list,
            'jadwal': jadwal,
            'kapasitas_max': kapasitas_max,
        })

    context = {
        'data_wahana': data_wahana
    }
    return render(request, 'data_wahana.html', context)

def tambah_wahana(request):
    if request.method == 'POST':
        data = request.POST
        nama_wahana = data.get('nama_wahana')
        kapasitas_max = data.get('kapasitas_max')
        jadwal_input = data.get('jadwal') 
        peraturan_list = []
        for key, value in request.POST.items():
            print(f"{key}: {value}")

        for key in data.keys():
            if key.startswith('peraturan_'):
                peraturan_list.append(data.get(key))

        if not all([nama_wahana, kapasitas_max, jadwal_input]):
            return HttpResponse("Data tidak lengkap", status=400)

        try:
            kapasitas_max = int(kapasitas_max)
            waktu = datetime.strptime(jadwal_input, "%H:%M").time()
        except ValueError:
            return HttpResponse("Format waktu harus HH:MM dan kapasitas harus angka", status=400)

        jadwal_timestamp = datetime.combine(timezone.now().date(), waktu)

        peraturan_text = "\n".join(peraturan_list) if peraturan_list else ""

        with connection.cursor() as cursor:
            # Insert ke fasilitas
            cursor.execute("""
                INSERT INTO fasilitas (nama, jadwal, kapasitas_max)
                VALUES (%s, %s, %s)
            """, [nama_wahana, jadwal_timestamp, kapasitas_max])

            # Insert ke wahana (nama_wahana dan peraturan)
            cursor.execute("""
                INSERT INTO wahana (nama_wahana, peraturan)
                VALUES (%s, %s)
            """, [nama_wahana, peraturan_text])

        return redirect('data_wahana')

    return render(request, 'form_tambah_wahana.html')

def edit_wahana(request, nama_wahana):
    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal_waktu = request.POST.get('jadwal_waktu')

        jadwal = datetime.today().strftime('%Y-%m-%d') + ' ' + jadwal_waktu

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE fasilitas SET kapasitas_max = %s, jadwal = %s::timestamp
                WHERE nama = %s
            """, [kapasitas, jadwal, nama_wahana])

        return redirect('data_wahana')

    # GET request
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT w.nama_wahana, TO_CHAR(f.jadwal, 'HH24:MI') AS jadwal, f.kapasitas_max
            FROM wahana w
            JOIN fasilitas f ON w.nama_wahana = f.nama
            WHERE w.nama_wahana = %s
        """, [nama_wahana])
        row = cursor.fetchone()

    if row:
        nama_wahana, jadwal, kapasitas_max = row
        wahana = {
            'nama_wahana': nama_wahana,
            'jadwal': jadwal,
            'kapasitas_max': kapasitas_max,
        }
    else:
        return redirect('data_wahana')

    return render(request, 'form_edit_wahana.html', {
        'wahana': wahana,
    })

def hapus_wahana(request, nama_wahana):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas = %s", [nama_wahana])
        
        try:
            cursor.execute("DELETE FROM jadwal_penugasan WHERE nama_wahana = %s", [nama_wahana])
        except Exception as e:
            if 'column "nama_wahana" does not exist' in str(e):
                pass
            else:
                raise 
            
        cursor.execute("DELETE FROM wahana WHERE nama_wahana = %s", [nama_wahana])
        cursor.execute("DELETE FROM fasilitas WHERE nama = %s", [nama_wahana])

    return redirect('data_wahana')