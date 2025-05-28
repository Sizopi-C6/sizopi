from django import forms
from django.db import connection

class SatwaForm(forms.Form):
    name = forms.CharField(
        label="Nama Individu (Opsional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    species = forms.CharField(
        label="Spesies",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    asal_hewan = forms.CharField(
        label="Asal Hewan",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    tanggal_lahir = forms.DateField(
        label="Tanggal Lahir (Opsional)",
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500', 'type': 'date'})
    )
    status_kesehatan = forms.ChoiceField(
        label="Status Kesehatan",
        required=True,
        choices=[
            ('', '-- Pilih Status --'),
            ('Sehat', 'Sehat'),
            ('Sakit', 'Sakit'),
            ('Dalam Pemantauan', 'Dalam Pemantauan'),
            ('lainnya', 'Lainnya')
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    nama_habitat = forms.ChoiceField(
        label="Nama Habitat",
        required=True,
        choices=[
            ('', '-- Pilih Habitat --'),
            ('Gurun Panas', 'Gurun Panas'),
            ('Lembah Hijau', 'Lembah Hijau'),
            ('Rawa-rawa', 'Rawa-rawa'),
            ('Gunung Salju', 'Gunung Salju'),
            ('Pesisir Pantai', 'Pesisir Pantai'),
            ('Hutan Tropis', 'Hutan Tropis'),
            ('Tepi Sungai', 'Tepi Sungai'),
            ('Savannah Besar', 'Savannah Besar'),
            ('Hutan Mangrove', 'Hutan Mangrove'),
            ('Bukit Berbatu', 'Bukit Berbatu'),
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    url_foto = forms.URLField(
        label="URL Foto Satwa",
        required=True,
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT nama FROM habitat ORDER BY nama ASC")
            rows = cursor.fetchall()

        habitat_choices = [(row[0], row[0]) for row in rows]
        self.fields['nama_habitat'].choices = habitat_choices

        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT status_kesehatan FROM hewan")
            rows = cursor.fetchall()

        status_kesehatan_choices = [(row[0], row[0]) for row in rows]
        self.fields['status_kesehatan'].choices = status_kesehatan_choices


class SatwaUpdateForm(forms.Form):
    name = forms.CharField(
        label="Nama Individu (Opsional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    species = forms.CharField(
        label="Spesies",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    asal_hewan = forms.CharField(
        label="Asal Hewan",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    tanggal_lahir = forms.DateField(
        label="Tanggal Lahir (Opsional)",
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500', 'type': 'date'})
    )
    status_kesehatan = forms.ChoiceField(
        label="Status Kesehatan",
        required=False,
        choices=[
            ('', '-- Pilih Status --'),
            ('Sehat', 'Sehat'),
            ('Sakit', 'Sakit'),
            ('Dalam Pemantauan', 'Dalam Pemantauan'),
            ('lainnya', 'Lainnya')
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    nama_habitat = forms.ChoiceField(
        label="Nama Habitat",
        required=False,
        choices=[
            ('', '-- Pilih Habitat --'),
            ('Gurun Panas', 'Gurun Panas'),
            ('Lembah Hijau', 'Lembah Hijau'),
            ('Rawa-rawa', 'Rawa-rawa'),
            ('Gunung Salju', 'Gunung Salju'),
            ('Pesisir Pantai', 'Pesisir Pantai'),
            ('Hutan Tropis', 'Hutan Tropis'),
            ('Tepi Sungai', 'Tepi Sungai'),
            ('Savannah Besar', 'Savannah Besar'),
            ('Hutan Mangrove', 'Hutan Mangrove'),
            ('Bukit Berbatu', 'Bukit Berbatu'),
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    url_foto = forms.URLField(
        label="URL Foto Satwa",
        required=False,
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT nama FROM habitat ORDER BY nama ASC")
            rows = cursor.fetchall()

        habitat_choices = [(row[0], row[0]) for row in rows]
        self.fields['nama_habitat'].choices = habitat_choices

        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT status_kesehatan FROM hewan")
            rows = cursor.fetchall()

        status_kesehatan_choices = [(row[0], row[0]) for row in rows]
        self.fields['status_kesehatan'].choices = status_kesehatan_choices

    def clean(self):
        cleaned_data = super().clean()

        if self.initial:
            asal_baru = cleaned_data.get('asal_hewan')
            asal_lama = self.initial.get('asal_hewan')
            status_baru = cleaned_data.get('status_kesehatan')
            status_lama = self.initial.get('status_kesehatan')

            if asal_baru == asal_lama and status_baru == status_lama:
                raise forms.ValidationError(
                    "Tidak ada perubahan pada asal hewan atau status kesehatan. Harap ubah salah satu untuk memperbarui data."
                )

        return cleaned_data

class HabitatForm(forms.Form):
    nama = forms.CharField(
        label="Nama Habitat",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50'
        })
    )
    luas_area = forms.FloatField(
        label="Luas Area (dalam m²)",
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50'
        })
    )
    kapasitas = forms.IntegerField(
        label="Kapasitas Maksimal (jumlah hewan)",
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50'
        })
    )
    status = forms.CharField(
        label="Status Lingkungan",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'style': 'resize: none;',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50',
            'placeholder': 'Contoh: Suhu: 28°C, Kelembapan: 70%, Vegetasi lebat'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HabitatUpdatedForm(forms.Form):
    nama = forms.CharField(
        label="Nama Habitat",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-yellow-500 focus:ring focus:ring-yellow-500 focus:ring-opacity-50'
        })
    )
    luas_area = forms.FloatField(
        label="Luas Area (dalam m²)",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-yellow-500 focus:ring focus:ring-yellow-500 focus:ring-opacity-50'
        })
    )
    kapasitas = forms.IntegerField(
        label="Kapasitas Maksimal (jumlah hewan)",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-yellow-500 focus:ring focus:ring-yellow-500 focus:ring-opacity-50'
        })
    )
    status = forms.CharField(
        label="Status Lingkungan",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'style': 'resize: none;',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-yellow-500 focus:ring focus:ring-yellow-500 focus:ring-opacity-50',
            'placeholder': 'Contoh: Suhu: 28°C, Kelembapan: 70%, Vegetasi lebat'
        })
    )

    def clean_kapasitas(self):
        kapasitas = self.cleaned_data.get('kapasitas')
        if kapasitas is not None and kapasitas < 0:
            raise forms.ValidationError("Kapasitas harus bernilai positif.")
        return kapasitas  # harus mengembalikan nilai kapasitas saja

    def clean(self):
        cleaned_data = super().clean()
        kapasitas_baru = cleaned_data.get('kapasitas')
        print("Kapasitas baru:", kapasitas_baru)
        status_baru = cleaned_data.get('status')
        print("Status baru:", status_baru)
        kapasitas_lama = self.initial.get('kapasitas')
        print("Kapasitas lama:", kapasitas_lama)
        status_lama = self.initial.get('status')
        print("Status lama:", status_lama)

        if kapasitas_baru == kapasitas_lama and status_baru == status_lama:
            raise forms.ValidationError(
                "Tidak ada perubahan pada kapasitas atau status. Harap ubah salah satu untuk memperbarui data."
            )
        return cleaned_data