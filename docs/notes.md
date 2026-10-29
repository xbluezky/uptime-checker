# Catatan Belajar uptime-checker

## 1. Python: kenapa kode ditulis begini

### except httpx.HTTPError di checker
Menangkap semua jenis error terkait kegagalan jaringan HTTP (seperti *timeout*, koneksi ditolak, atau salah DNS) secara spesifik tanpa menangkap error pemrograman lainnya (seperti `KeyError` atau `NameError`), sehingga aplikasi bisa langsung mencatat status situs sedang *down* secara aman.

### MockTransport di test
Memungkinkan pengujian unit (*unit testing*) menyimulasi respons HTTP dari server luar tanpa melakukan panggilan jaringan internet asli, sehingga tes berjalan sangat cepat, bisa diisolasi, dan tidak bergantung pada status server pihak ketiga.

### asyncio.to_thread (nomor 4, dirapikan)
Python *event loop* bersifat *single-threaded* (satu jalur). Membungkus panggilan database sinkron dengan `asyncio.to_thread` memindahkan proses tunggu jaringan yang lambat ke *thread* terpisah, sehingga jalur utama tidak membeku, `/health` tetap responsif, dan kontainer tidak ditandai *unhealthy* oleh Docker (yang di level orkestrator bisa memicu *restart* otomatis).

### DISTINCT ON (nomor 5)
Mengambil tepat satu data status paling terbaru dari setiap URL. PostgreSQL mewajibkan kolom di `DISTINCT ON (url)` ditulis paling depan di `ORDER BY url` agar data dikelompokkan dulu (jika tidak, Postgres langsung melempar *syntax error*), lalu disusul `checked_at DESC` agar baris pertama yang diambil oleh `DISTINCT ON` dijamin merupakan pengecekan paling mutakhir (bukan data terlama).

### try/except di dalam while True
Menjamin loop pencarian/pengecekan (*scraping/monitoring*) tetap berjalan terus-menerus secara periodik meskipun terjadi kegagalan fatal pada salah satu proses pengecekan URL, sehingga aplikasi tidak mati total di tengah jalan.

### Test lolos belum tentu benar (Celah batas < 400)
Saat batas diubah dari < 400 ke < 300, tidak ada test yang gagal, artinya test awal tidak menguji wilayah status 3xx. Test yang lolos hanya membuktikan yang diuji masih benar, bukan kodenya benar. Test 304 ditambahkan sebagai nilai batas: ia gagal ketika batas diubah dan hijau ketika dikembalikan. Pelajarannya: uji nilai di sekitar batas, bukan hanya contoh sukses dan gagal yang jelas.


## 2. Docker

### Layer caching (COPY requirements dulu)
Memanfaatkan sistem *cache* Docker dengan menaruh file yang jarang berubah (`requirements.txt`) di atas kode aplikasi (`app`). Docker hanya akan mengulang proses `pip install` jika file `requirements.txt` berubah, sehingga jika hanya kode aplikasi yang diedit, proses *build* selanjutnya selesai dalam hitungan detik.

### Non-root (kenapa dan risikonya)
Menerapkan *Principle of Least Privilege* dengan menjalankan kontainer sebagai user biasa (UID 10001). Jika terjadi eksploitasi celah keamanan (*Remote Code Execution*), penyerang tidak mendapatkan hak akses administrator (`root`) sehingga dampaknya terbatas: tidak bisa mengubah sistem file atau memasang paket, dan jalur untuk keluar ke host menjadi lebih sempit.

### HEALTHCHECK pakai Python, bukan curl
Base image versi `slim` sengaja dibuat minimalis dan tidak menyediakan `curl` secara bawaan. Memanfaatkan modul internal Python `urllib.request` jauh lebih efisien untuk menjaga ukuran *image* tetap ramping dan aman, daripada harus menginstal *tools* pihak ketiga yang menambah potensi celah keamanan baru.

### Multi-stage: hasil ukur

| Image | Disk | Content |
|---|---|---|
| multi-stage | 254MB | 61.1MB |
| single-stage | 267MB | 64.5MB |

**Kesimpulan jujur:** Multi-stage menghemat ~13MB disk (254MB vs 267MB, ~5%) dan 3,4MB content size. Penyebab selisihnya belum diselidiki. Di project ini hemat kecil karena semua dependensi punya wheel jadi dan tidak ada compiler untuk dibuang. Manfaat besar baru muncul bila tahap build butuh compiler atau header.

### Temuan Hadolint (Linting Dockerfile)
Pemeriksaan dengan Hadolint memicu peringatan DL3066 karena menggunakan nama user tekstual; disarankan menggunakan instruksi `USER` numerik (UID) agar mesin orkestrator bisa memvalidasi kebijakan non-root sebelum kontainer dijalankan. Selain itu, aturan DL3025 menyarankan penulisan instruksi `HEALTHCHECK` dalam format eksekusi JSON (`["executable", "param1"]`) demi menghindari *overhead* pemanggilan shell yang tidak perlu.


## 3. Compose

### Host db vs localhost
Setiap kontainer berjalan di dalam isolasi jaringannya sendiri, sehingga kata `localhost` di dalam kontainer aplikasi akan merujuk ke dirinya sendiri (bukan ke Postgres). Menggunakan host `db` memanfaatkan fitur *embedded DNS* Docker Compose untuk mengarahkan koneksi ke IP kontainer database yang tepat.

### depends_on vs service_healthy
`depends_on` biasa hanya mengatur urutan start, bukan kesiapan. Menggunakan konfigurasi `condition: service_healthy` tanpa diiringi blok `healthcheck` yang valid di sisi servis DB akan langsung ditolak oleh Docker Compose (konfigurasi error). Tanpa menunggu DB benar-benar siap menerima koneksi, aplikasi bisa gagal saat startup karena `init_db()` dipanggil sekali dan tidak ada retry.

### Volume dan down -v
Sifat penyimpanan internal kontainer adalah *ephemeral* (sementara); data di dalamnya akan lenyap permanen begitu kontainer diperbarui atau dihapus. Menggunakan volume Docker Compose mengamankan data Postgres agar tetap persisten.
**Bukti:** Sebelum down: count 42, min 06:56:38. Setelah `down` + `up`: count 46, min sama. Setelah `down -v` + `up`: count 2, min 07:08:54 (database baru).

### Secrets dan Validasi Variabel di Compose
Mengabaikan file `.env` asli dari Git repository (*gitignored*) dan hanya menyertakan `.env.example` adalah standar keamanan agar rahasia kredensial tidak bocor. Penggunaan sintaks interpolasi `${POSTGRES_PASSWORD:?...}` di dalam `compose.yaml` sangat membantu karena akan memaksa proses Docker Compose langsung gagal memberikan error yang jelas di terminal jika variabel lingkungan tersebut kosong atau belum didefinisikan.


## 4. Lab jaringan Docker

### Bridge default vs User-defined network
Pada bridge default, container tidak punya resolusi nama otomatis (hanya lewat IP), sehingga `ping n2` menghasilkan `bad address 'n2'`. Pada user-defined network (`docker network create lab`), DNS bawaan Docker aktif sehingga nama container n2 diterjemahkan ke IP (`172.19.0.3`) dan ping berhasil.


## 5. Temuan dan keterbatasan

- **GitHub 403:** Satu pengecekan ke `github.com` mendapat 403. `curl` dari laptop, baik dengan User-Agent bawaan maupun `python-httpx/0.27.2`, mendapat 200. Penyebab belum diketahui; hipotesis (reputasi IP atau deteksi bot, atau perbedaan klien selain User-Agent) belum teruji.
- **/health tidak mencerminkan status loop:** Endpoint `/health` saat ini hanya memvalidasi apakah server HTTP FastAPI masih hidup, tetapi tidak memonitor apakah *background task* (jalur loop pengecekan `while True`) di dalam aplikasi sebenarnya sudah macet atau mati.
- **Tidak ada retry koneksi DB saat startup:** init_db() dipanggil sekali, jadi aplikasi bergantung pada healthcheck DB di Compose. Saat berjalan, kegagalan simpan ditangkap try/except di loop dan siklus berikutnya mencoba lagi, tetapi hasil siklus yang gagal hilang (tidak di-buffer), dan satu kegagalan menghentikan penyimpanan sisa hasil di siklus itu.
- **/metrics ditunda ke Fase 2:** Implementasi metrik performa (seperti Prometheus/Grafana *exporter*) sengaja ditunda agar pengembangan Fase 1 berfokus penuh pada kestabilan fitur inti pemantauan *uptime* dan integrasi database.
