from django import forms

class SatwaForm(forms.Form):
    nama_individu = forms.CharField(
        label="Nama Individu (Opsional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    spesies = forms.CharField(
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
            ('sehat', 'Sehat'),
            ('sakit', 'Sakit'),
            ('dalam_pemantauan', 'Dalam Pemantauan'),
            ('lainnya', 'Lainnya')
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    nama_habitat = forms.ChoiceField(
        label="Nama Habitat",
        required=True,
        choices=[
            ('', '-- Pilih Habitat --'),
            ('gurun_panas', 'Gurun Panas'),
            ('lembah_hijau', 'Lembah Hijau'),
            ('rawa_rawa', 'Rawa-rawa'),
            ('gunung_salju', 'Gunung Salju'),
            ('pesisir_pantai', 'Pesisir Pantai'),
            ('hujan_tropis', 'Hutan Tropis'),
            ('tepi_sungai', 'Tepi Sungai'),
            ('savannah_besar', 'Savannah Besar'),
            ('hujan_mangrove', 'Hutan Mangrove'),
            ('bukit_berbatu', 'Bukit Berbatu'),
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    url_foto = forms.URLField(
        label="URL Foto Satwa",
        required=True,
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'})
    )
    def __init__(self, *args, edit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        if edit_mode:
            self.fields['nama_individu'].widget.attrs['readonly'] = True
            self.fields['spesies'].widget.attrs['readonly'] = True
            self.fields['tanggal_lahir'].widget.attrs['readonly'] = True
            self.fields['nama_habitat'].widget.attrs['readonly'] = True
            self.fields['url_foto'].widget.attrs['readonly'] = True


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

    def __init__(self, *args, edit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        if edit_mode:
            self.fields['nama'].widget.attrs['readonly'] = True
            self.fields['luas_area'].widget.attrs['readonly'] = True