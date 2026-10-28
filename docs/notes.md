Ukuran Image Lebih Ramping (dev vs single):

&#x09;• Versi dev (multi-stage) berhasil menghemat ukuran Content Size menjadi 61.1MB dibanding versi single yang 64.5MB.

&#x09;• Ini terjadi karena sampah-sampah proses instalasi pip (seperti build tools, cache tambahan, atau sisa kompilasi) ditinggal di image builder dan tidak ikut masuk ke image final.



4\. Karena Python event loop itu sifatnya single-threaded atau satu jalur. Kalau kita langsung panggil fungsi database yang sinkron di jalur utama, seluruh aplikasi bakal "beku" nungguin proses jaringan ke database selesai, sehingga fitur lain kayak /health check ikut macet. Dengan dibungkus to\_thread, proses lambat itu dipindahin ke thread lain agar jalur utama tetap lancar. Efeknya, Docker tidak akan menandai kontainer sebagai unhealthy, yang mana di level orkestrator (seperti Kubernetes atau Swarm) bisa memicu kontainer tersebut di-restart otomatis.

5\. Query ini tujuannya untuk mengambil satu data status paling terbaru dari setiap URL. Sesuai aturan baku PostgreSQL, kolom di DISTINCT ON (url) wajib ditaruh paling depan di ORDER BY url, jika tidak maka PostgreSQL akan langsung melempar error sintaks. Setelah itu, barulah disusul checked\_at DESC untuk menentukan baris mana yang diambil. Jika menggunakan DESC, kita mengambil data paling baru. Sebaliknya, jika DESC dihilangkan, query tidak menghasilkan data acak melainkan akan mengambil data paling lama (tergantung urutan naik).



