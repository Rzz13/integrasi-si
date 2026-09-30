# Tugas Analisis Minggu 3

## 1. Analisis Pola Arsitektur

Rancangan ini dikategorikan sebagai **Adapter Pattern** dalam arsitektur EAI karena program berbasis C hanya mampu membaca dan menulis file teks lokal tanpa memiliki antarmuka jaringan. Server `adapter_service.py` bertindak sebagai penerjemah (adapter) yang mengubah permintaan HTTP/XML dari klien modern menjadi format teks flat (CSV) pada file basis data, dan sebaliknya, tanpa perlu mengubah kode sumber C sama sekali.

Keuntungan utama bagi klien web luar meliputi:
- **Loose Coupling:** Klien hanya perlu mengetahui endpoint HTTP dan struktur XML tanpa perlu memahami cara sistem legacy menyimpan data.
- **Fleksibilitas Sistem:** Sistem legacy dapat diperbarui atau diganti di masa mendatang tanpa memengaruhi klien, selama kontrak XML tidak berubah.
- **Efisiensi Risiko:** Sistem lama yang sudah berjalan tidak perlu dimodifikasi, sehingga meminimalkan risiko kerusakan sistem.
- **Interoperabilitas:** Protokol HTTP dan XML bersifat independen terhadap platform maupun bahasa pemrograman.

---

## 2. Analisis Overhead Serialisasi Data

Respons XML aktual dari endpoint `GET /students/2415354001`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<StudentResponse><NIM>2415354001</NIM><Nama>I Made Sujana</Nama><Jurusan>Teknologi Informasi</Jurusan><Status>ACTIVE</Status></StudentResponse>
```

### Kalkulasi Data Aktual (Murni):
- `"2415354001"` = 10 byte
- `"I Made Sujana"` = 13 byte
- `"Teknologi Informasi"` = 19 byte
- `"ACTIVE"` = 6 byte
- **Total Data Asli:** $10 + 13 + 19 + 6 = \mathbf{48\text{ byte}}$

### Kalkulasi Ukuran Respons XML:
- Total ukuran seluruh karakter dokumen XML di atas (termasuk deklarasi `<?xml ...?>` dan tag pembungkus) adalah **184 byte**.

### Kalkulasi Rasio Overhead:
- **Ukuran Overhead:** \(184 − 48 = 136 byte\)
- **Rasio Overhead (vs. Data Murni):** \(136 ÷ 48) × 100% = 283,33%
- **Proporsi Overhead (vs. Total Payload):** \(136 ÷ 184) × 100% = 73,91%

**Kesimpulan:** Sekitar **73,91%** isi dari seluruh payload yang ditransmisikan hanya berupa tag XML pembungkus, bukan data aktual. Hal ini menunjukkan bahwa serialisasi XML menimbulkan pembengkakan ukuran (*overhead*) sebesar **283,33%** dibandingkan data aslinya.

---

## 3. Prediksi Keterbatasan Integrasi

Server bawaan Python (`http.server`) bekerja secara *synchronous single-threaded*. Jika terdapat 500 permintaan `POST` simultan pada detik yang sama, server tidak sanggup membuka banyak koneksi bersamaan, menyebabkan keterbatasan antrean socket (*socket backlog limit*) dan kegagalan masif pada jaringan.

Selain itu, penulisan langsung ke file `students_db.txt` berisiko memicu:
- **Race Condition & Data Corruption:** Penulisan bersamaan dapat menyebabkan data saling tertimpa atau terpotong karena tidak ada mekanisme *file locking*.
- **Absensi Transaksi:** Tidak adanya fitur *concurrency control* atau pengecekan *primary key* (NIM ganda) seperti pada RDBMS modern.

### Solusi Message Broker (RabbitMQ / Apache Kafka):
Message Broker dibutuhkan untuk mengubah pola komunikasi dari *synchronous* menjadi *asynchronous event-driven*:
- Message Broker dapat menampung 500 request berkecepatan tinggi ke dalam memori (*buffer*) dalam hitungan milidetik.
- Server adapter bisa langsung memberikan balasan cepat (`202 Accepted`) ke klien tanpa menunggu proses penulisan file selesai.
- *Worker service* akan mengambil pesan dari antrean dan menuliskannya ke file legacy satu per satu secara sekuensial, sehingga mencegah korupsi data dan penolakan koneksi