# rPPG Stress Monitor Frontend

Frontend React + Vite untuk estimasi stres fisiologis dari video wajah menggunakan remote photoplethysmography (rPPG).

Visual interface menggunakan pendekatan Glassmorphism Pro-inspired: background gelap `#060A12`, font Outfit, glow mint/sky/indigo, noise overlay, dan kartu glass panel premium.

Sistem ini menampilkan alur pengguna:

1. Landing page
2. Instruksi dan izin kamera
3. Live measurement selama 60 detik
4. Ringkasan hasil estimasi
5. Detail sinyal untuk kebutuhan akademik/admin

## Cara Menjalankan

```bash
npm install
npm run dev
```

Buka URL lokal yang ditampilkan Vite, biasanya:

```text
http://127.0.0.1:5173/
```

Untuk build production:

```bash
npm run build
```

Untuk lint:

```bash
npm run lint
```

## Izin Kamera

Browser akan meminta izin kamera saat pengguna menekan tombol **Aktifkan Kamera** pada halaman instruksi.

Jika izin ditolak atau kamera tidak ditemukan, aplikasi menampilkan pesan error yang ramah dan tidak akan crash.

## Flow Pengukuran

- Pengguna membuka landing page dan menekan **Mulai Pengukuran**.
- Pengguna membaca instruksi posisi, pencahayaan, gerakan, dan durasi.
- Kamera dibuka setelah izin diberikan.
- Pengukuran berjalan selama 60 detik.
- UI menampilkan preview kamera, placeholder overlay wajah/ROI, status kualitas sinyal, heart rate, stress level, confidence, dan progress timer.
- Setelah timer selesai, aplikasi menampilkan halaman hasil.
- Halaman detail sinyal menampilkan chart dan tabel fitur HRV/rPPG.

## Backend Integration

Untuk saat ini data pengukuran berasal dari mock service di:

```text
src/services/measurementService.ts
```

Service layer sudah menyediakan fungsi:

- `startMeasurement()`
- `stopMeasurement()`
- `getMeasurementResult()`
- `getSignalDetails()`

TODO di file tersebut menunjukkan lokasi integrasi endpoint backend sebenarnya.

## Disclaimer

Hasil sistem ini adalah estimasi awal indikator fisiologis, bukan diagnosis medis.

Hasil dapat dipengaruhi oleh pencahayaan, gerakan, kafein, olahraga, kurang tidur, suhu ruangan, kualitas kamera, dan kondisi tubuh lainnya.
