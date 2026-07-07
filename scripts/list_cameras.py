#!/usr/bin/env python
"""Script untuk mengecek indeks kamera yang tersedia di Windows."""

import cv2

def main():
    print("=" * 60)
    print("  MENGECEK INDEKS KAMERA YANG TERSEDIA DI SISTEM ANDA")
    print("=" * 60)
    print("Mengecek indeks kamera dari 0 sampai 9 menggunakan OpenCV...")
    
    # Mengetes dengan DirectShow (sangat disarankan untuk Windows & Iriun Webcam)
    print("\n[INFO] Mengetes dengan backend DirectShow (cv2.CAP_DSHOW)...")
    found_dshow = False
    for index in range(10):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  -> Indeks Kamera: {index} (DirectShow)")
                print(f"     Resolusi: {int(w)}x{int(h)} | FPS: {fps}")
                found_dshow = True
            cap.release()
            
    if not found_dshow:
        print("  ❌ Tidak ada kamera yang terdeteksi dengan DirectShow.")
        
    # Mengetes dengan backend default
    print("\n[INFO] Mengetes dengan backend Default OpenCV...")
    found_default = False
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  -> Indeks Kamera: {index} (Default)")
                print(f"     Resolusi: {int(w)}x{int(h)} | FPS: {fps}")
                found_default = True
            cap.release()
            
    if not found_default:
        print("  ❌ Tidak ada kamera yang terdeteksi dengan backend default.")
        
    print("\n" + "=" * 60)
    print("PANDUAN PENGGUNAAN:")
    print("1. Pastikan Iriun Webcam sudah terinstal di PC dan iPhone Anda.")
    print("2. Hubungkan iPhone dan PC ke jaringan Wi-Fi yang sama (atau gunakan kabel USB).")
    print("3. Buka aplikasi Iriun Webcam di iPhone dan PC Anda.")
    print("4. Jalankan kembali script ini untuk melihat indeks Iriun Webcam.")
    print("5. Setelah mengetahui indeksnya (misal: 1), jalankan realtime_demo.py dengan:")
    print("   python scripts/03_realtime_demo.py --camera 1")
    print("=" * 60)

if __name__ == "__main__":
    main()
