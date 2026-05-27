"""
run_pipeline.py — Orkestrator Pipeline Kependudukan (FULL AUTO)
================================================================
Penggunaan:
  python run_pipeline.py                    # Semua tahap, periode terbaru
  python run_pipeline.py --periode 202501   # Paksa periode tertentu
  python run_pipeline.py --from 03          # Mulai dari tahap 03
  python run_pipeline.py --only 04          # Hanya tahap 04
  python run_pipeline.py --list             # Tampilkan periode tersedia
"""
import sys, os, argparse, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

def simulasi_kirim_alert(tahap_no, tahap_nama, error_msg):
    """Simulasi pengiriman notifikasi Slack/Email Webhook jika terjadi kegagalan pipeline"""
    import json
    from datetime import datetime
    
    alert_file = os.path.join(os.path.dirname(__file__), "logs", "pipeline_alerts.json")
    
    alert_payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "CRITICAL_ALERT",
        "kabupaten": "Kabupaten Pulau Morotai",
        "tahap_nomor": tahap_no,
        "tahap_nama": tahap_nama,
        "error_message": str(error_msg),
        "channel_simulated": ["Slack (#dukcapil-alerts)", "Email (admin@morotaikab.go.id)"]
    }
    
    # Load existing alerts if file exists
    alerts = []
    if os.path.exists(alert_file):
        try:
            with open(alert_file, "r") as f:
                alerts = json.load(f)
        except Exception:
            pass
            
    alerts.append(alert_payload)
    
    # Simpan kembali
    try:
        with open(alert_file, "w") as f:
            json.dump(alerts, f, indent=4)
        print(f"\n  > [ALERT WEBHOOK SIMULATION] Notifikasi bahaya dikirim!")
        print(f"    * Slack: #dukcapil-alerts <-- \"CRITICAL: Tahap {tahap_no} ({tahap_nama}) GAGAL! Error: {error_msg}\"")
        print(f"    * Email: admin@morotaikab.go.id <-- Laporan insiden teknis dikirim.")
        print(f"    * Log tercatat di: {alert_file}\n")
    except Exception as ex:
        print(f"  Gagal mencatat log alert: {ex}")

def main():
    # Pre-parse --periode dan --list sebelum import config
    # (karena config.py butuh sys.argv untuk --periode)
    p=argparse.ArgumentParser(description="Pipeline Kependudukan Kabupaten Pulau Morotai")
    p.add_argument("--periode",default=None,help="Kode periode (misal: 202601). Kosong = auto-detect terbaru")
    p.add_argument("--list",action="store_true",help="Tampilkan semua periode yang tersedia")
    p.add_argument("--from",dest="start",default="01",choices=["01","02","03","04","05","06","07"])
    p.add_argument("--only",default=None,choices=["01","02","03","04","05","06","07"])
    p.add_argument("--skip-on-error",action="store_true")
    p.add_argument("--all-periods", "--all", action="store_true", help="Jalankan rekonstruksi historis penuh untuk semua periode")
    args=p.parse_args()

    # Jika --all-periods diaktifkan, jalankan orkestrator multi-periode penuh
    if args.all_periods:
        import subprocess, shutil
        from pathlib import Path
        print("\n" + "="*80)
        print("  REKONSTRUKSI HISTORIS MULTI-PERIODE PENUH (SCD TYPE 2 & STAR SCHEMA)")
        print("="*80)
        
        # Import config setelah parsing argument
        from config import SEMUA_PERIODE, BASE_DIR
        
        print(f"Terdeteksi {len(SEMUA_PERIODE)} periode data agregat secara kronologis:")
        for idx, pr in enumerate(SEMUA_PERIODE):
            sem = "Semester 1" if pr.endswith("01") else "Semester 2"
            print(f"  {idx + 1}. {pr} ({pr[:4]} {sem})")
            
        # Reset / Backup Database Historis Warehouse
        warehouse_db = BASE_DIR / "data" / "siak_history_warehouse.db"
        warehouse_backup = BASE_DIR / "data" / "siak_history_warehouse.db.bak"
        if warehouse_db.exists():
            print(f"\n[INFO] Menemukan database warehouse lama di: {warehouse_db}")
            try:
                print(f"       -> Membuat salinan cadangan ke: {warehouse_backup}")
                shutil.copy2(warehouse_db, warehouse_backup)
                print(f"       -> Menghapus database lama agar dibangun kembali secara bersih...")
                os.remove(warehouse_db)
                for suffix in ["-wal", "-journal", "-shm"]:
                    wal_file = Path(str(warehouse_db) + suffix)
                    if wal_file.exists():
                        os.remove(wal_file)
                print("       -> Berhasil di-reset.")
            except Exception as e:
                print(f"[WARNING] Gagal mereset database warehouse historis: {e}")
                
        # Reset / Backup Database Star Schema
        star_db = BASE_DIR / "data" / "siak_star_warehouse.db"
        star_backup = BASE_DIR / "data" / "siak_star_warehouse.db.bak"
        if star_db.exists():
            print(f"\n[INFO] Menemukan database Star Schema lama di: {star_db}")
            try:
                print(f"       -> Membuat salinan cadangan ke: {star_backup}")
                shutil.copy2(star_db, star_backup)
                print(f"       -> Menghapus database lama agar dibangun kembali secara bersih...")
                os.remove(star_db)
                for suffix in ["-wal", "-journal", "-shm"]:
                    wal_file = Path(str(star_db) + suffix)
                    if wal_file.exists():
                        os.remove(wal_file)
                print("       -> Berhasil di-reset.")
            except Exception as e:
                print(f"[WARNING] Gagal mereset database Star Schema: {e}")
                
        # Loop Sekuensial Periode
        start_all = time.time()
        results = {}
        for idx, pr in enumerate(SEMUA_PERIODE):
            sem = "Semester 1" if pr.endswith("01") else "Semester 2"
            print(f"\n" + "=" * 80)
            print(f" MENJALANKAN PIPELINE: PERIODE {pr} ({pr[:4]} {sem}) — [{idx+1}/{len(SEMUA_PERIODE)}]".center(80))
            print("=" * 80 + "\n")
            
            t0 = time.time()
            cmd = [sys.executable, __file__, "--periode", pr, "--skip-on-error"]
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=str(BASE_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                if process.stdout:
                    for line in process.stdout:
                        print(line, end="")
                process.wait()
                elapsed = time.time() - t0
                if process.returncode == 0:
                    results[pr] = "SUCCESS"
                    print(f"\n[SUCCESS] Periode {pr} selesai dalam {elapsed:.1f} detik.")
                else:
                    results[pr] = f"FAILED (Exit Code {process.returncode})"
                    print(f"\n[FAILED] Periode {pr} gagal.")
            except Exception as e:
                results[pr] = f"ERROR ({e})"
                print(f"\n[ERROR] Gagal mengeksekusi periode {pr}: {e}")
                
        # Jalankan Penyelesaian Akhir
        print("\n" + "="*80)
        print("  LANGKAH PENYELASAIAN AKHIR KOLEKTIF (CONSOLIDATED FINALIZATION)")
        print("="*80)
        try:
            print("[INFO] Mengekstraksi data agregat untuk dashboard terpadu...")
            subprocess.run([sys.executable, "generate_unified_dashboard_data.py"], check=True)
            
            print("[INFO] Merakit dasbor HTML premium...")
            subprocess.run([sys.executable, "build_unified_dashboard.py"], check=True)
            
            print("[INFO] Menyalin dasbor terbaru ke root index.html...")
            shutil.copy2(os.path.join("output", "dashboard_morotai.html"), "index.html")
            print("  OK  index.html berhasil diperbarui.")
            
            print("[INFO] Memverifikasi integritas dasbor...")
            subprocess.run([sys.executable, os.path.join("scratch", "verify_unified.py")], check=True)
            
            print("[INFO] Memverifikasi integritas database Star Schema...")
            subprocess.run([sys.executable, "-m", "unittest", os.path.join("tests", "test_star_schema.py")], check=True)
            
            print("\n[SUCCESS] Seluruh eksekusi dan verifikasi multi-periode berhasil 100%!")
        except Exception as e:
            print(f"\n[ERROR] Kegagalan pada langkah pasca-pipeline multi-periode: {e}")
            sys.exit(1)
            
        print("\n" + "="*80)
        print("  RINGKASAN EKSEKUSI MULTI-PERIODE")
        print("="*80)
        for pr, res in results.items():
            print(f"    Periode {pr}: {res}")
        print(f"\n  Total Durasi: {time.time()-start_all:.1f}s")
        print("="*80 + "\n")
        return

    # Import config setelah argparse (config.py membaca sys.argv)
    from config import PERIODE, NAMA_KAB, DATA_DIR, OUTPUT_DIR, SEMUA_PERIODE, PREV_PERIODE, DATA_IS_CLEAN

    # Jalankan otomatisasi pembersih sampah berkas (Sprint 1)
    try:
        from scripts import cleanup
        cleanup.main()
    except Exception as e:
        print(f"  [WARNING] Gagal menjalankan pembersihan otomatis: {e}")

    # --list: tampilkan semua periode
    if args.list:
        print(f"\nPeriode tersedia di folder data/:")
        for i, pr in enumerate(SEMUA_PERIODE):
            tag = " <-- AKTIF" if pr == PERIODE else ""
            sem = "Semester 1" if pr.endswith("01") else "Semester 2"
            print(f"  {i+1}. {pr} ({pr[:4]} {sem}){tag}")
        if not SEMUA_PERIODE:
            print("  (tidak ada folder AGREGAT_* di data/)")
        print()
        return

    # Validasi folder data ada
    if not DATA_DIR.exists():
        print(f"\n  ERROR: Folder data tidak ditemukan: {DATA_DIR}")
        print(f"  Periode tersedia: {', '.join(SEMUA_PERIODE) if SEMUA_PERIODE else 'tidak ada'}")
        print(f"  Solusi: buat folder data/AGREGAT_{PERIODE}/ dan isi file XLSX\n")
        return

    # Banner
    print("\n" + "="*64)
    print(f"  PIPELINE KEPENDUDUKAN -- {NAMA_KAB}")
    print(f"  Periode: {PERIODE} (Semester {PERIODE[4:]} / {PERIODE[:4]})")
    print(f"  Prev   : {PREV_PERIODE}")
    print(f"  Data   : {DATA_DIR}")
    print(f"  Status : {'BERSIH (sudah dibersihkan)' if DATA_IS_CLEAN else 'MENTAH (belum dibersihkan)'}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  Waktu  : {datetime.now():%d %B %Y %H:%M:%S}")
    n_xlsx = len(list(DATA_DIR.glob("*.xlsx")))
    print(f"  File   : {n_xlsx} file XLSX terdeteksi")
    if len(SEMUA_PERIODE) > 1:
        print(f"  Tersedia: {', '.join(SEMUA_PERIODE)}")
    print("="*64 + "\n")

    # Tahapan
    tahap=[("01","PEMBERSIHAN DATA","01_pembersihan"),
           ("02","VALIDASI & QC","02_validasi"),("03","INTEGRASI MASTER","03_integrasi"),
           ("04","ANALISIS STATISTIK","04_analisis"),("05","LAPORAN EKSEKUTIF","05_laporan"),
           ("06","KOMPREHENSIF (123 FILE)","06_komprehensif"),
           ("07","VISUALISASI DASHBOARD","07_visualisasi")]
    if args.only: tahap=[t for t in tahap if t[0]==args.only]
    else: tahap=[t for t in tahap if t[0]>=args.start]

    # Split tahap menjadi sekuensial (<= 03) dan paralel (>= 04)
    tahap_seq = [t for t in tahap if t[0] <= "03"]
    tahap_para = [t for t in tahap if t[0] >= "04"]

    t0 = time.time()
    hasil = {}
    
    # 1. Eksekusi Tahap Sekuensial (01 - 03)
    for no, nm, mod in tahap_seq:
        print(f"\n{'-'*64}\n  >  TAHAP {no}: {nm}\n{'-'*64}")
        t = time.time()
        try:
            m = __import__(mod)
            m.main()
            print(f"  OK  Selesai dalam {time.time()-t:.1f}s")
            hasil[no] = True
            
            # Post-Stage-03 ETL Actions: Setup & Migrate Star Schema
            if no == "03":
                print(f"\n  [ETL] Menyiapkan Star Schema dan Migrasi...")
                import subprocess
                subprocess.run([sys.executable, os.path.join("scripts", "setup_star_schema.py")], check=True)
                subprocess.run([sys.executable, os.path.join("scripts", "migrate_historical_to_star.py")], check=True)
                print(f"  OK  Star Schema Setup & Migrasi selesai.")
                
        except Exception as e:
            print(f"  GAGAL  Error: {e}")
            import traceback
            traceback.print_exc()
            hasil[no] = False
            simulasi_kirim_alert(no, nm, e)
            if not args.skip_on_error:
                print(f"\n  Dihentikan di Tahap {no}. Gunakan --skip-on-error untuk lanjut.")
                break
                
    # Cek kelayakan kelanjutan paralel
    dapat_lanjut = True
    if not args.skip_on_error:
        for no, ok in hasil.items():
            if not ok:
                dapat_lanjut = False
                break
                
    # 2. Eksekusi Tahap Paralel (04 - 07 Concurrent DAG)
    if dapat_lanjut and tahap_para:
        print(f"\n{'-'*64}\n  >  EKSEKUSI PARALEL (TAHAP 04 - 07 CONCURRENT DAG)\n{'-'*64}")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def run_single_stage(t_info):
            no_p, nm_p, mod_p = t_info
            t_start = time.time()
            try:
                print(f"  [START] Tahap {no_p}: {nm_p}...")
                m_p = __import__(mod_p)
                m_p.main()
                elapsed = time.time() - t_start
                print(f"  [SUCCESS] Tahap {no_p}: {nm_p} selesai dalam {elapsed:.1f}s")
                return no_p, True, None
            except Exception as e_p:
                import traceback
                tb_p = traceback.format_exc()
                return no_p, False, (e_p, tb_p)
                
        with ThreadPoolExecutor(max_workers=len(tahap_para)) as executor:
            future_to_stage = {executor.submit(run_single_stage, t): t for t in tahap_para}
            
            for future in as_completed(future_to_stage):
                stage_info = future_to_stage[future]
                no_s, nm_s, mod_s = stage_info
                try:
                    no_res, ok_res, err_info = future.result()
                    hasil[no_res] = ok_res
                    if not ok_res:
                        e_p, tb_p = err_info
                        print(f"  [FAILED] Tahap {no_s}: {nm_s} GAGAL! Error: {e_p}")
                        print(tb_p)
                        simulasi_kirim_alert(no_s, nm_s, e_p)
                except Exception as exc:
                    print(f"  [FAILED] Tahap {no_s}: {nm_s} menghasilkan eksepsi thread: {exc}")
                    hasil[no_s] = False

        # Post-Stage-07 GIS Action: Generate Leaflet Map
        if hasil.get("07"):
            print(f"\n{'-'*64}\n  >  [GIS] MENGHASILKAN PETA LEAFLET SPASIAL\n{'-'*64}")
            try:
                import subprocess
                subprocess.run([sys.executable, os.path.join("scripts", "generate_leaflet_map.py")], check=True)
                print(f"  OK  Peta Leaflet Spasial berhasil dibuat.")
            except Exception as e:
                print(f"  [WARNING] Gagal menghasilkan peta Leaflet spasial: {e}")

    print(f"\n{'='*64}\n  RINGKASAN\n{'='*64}")
    print(f"  Periode: {PERIODE}")
    for no,ok in hasil.items(): print(f"    Tahap {no}: {'OK' if ok else 'GAGAL'}")
    print(f"\n    Total: {time.time()-t0:.1f}s | Output: {OUTPUT_DIR}\n{'='*64}\n")

    # 3. Langkah Penyelesaian Akhir Terpadu (Kompilasi Dashboard & Verifikasi)
    # Hanya dijalankan jika seluruh tahap yang diminta berhasil
    tahap_sukses = all(hasil.get(no) for no, _, _ in tahap)
    if tahap_sukses:
        print(f"\n{'='*64}\n  POST-PIPELINE INTEGRATION & VERIFICATION\n{'='*64}")
        try:
            import subprocess, shutil
            print("[INFO] Mengekstraksi data agregat untuk dashboard terpadu...")
            subprocess.run([sys.executable, "generate_unified_dashboard_data.py"], check=True)
            
            print("[INFO] Merakit dasbor HTML premium...")
            subprocess.run([sys.executable, "build_unified_dashboard.py"], check=True)
            
            print("[INFO] Menyalin dasbor terbaru ke root index.html...")
            shutil.copy2(os.path.join("output", "dashboard_morotai.html"), "index.html")
            print("  OK  index.html berhasil diperbarui.")
            
            print("[INFO] Memverifikasi integritas dasbor...")
            subprocess.run([sys.executable, os.path.join("scratch", "verify_unified.py")], check=True)
            
            print("[INFO] Memverifikasi integritas database Star Schema...")
            subprocess.run([sys.executable, "-m", "unittest", os.path.join("tests", "test_star_schema.py")], check=True)
            
            print("\n[SUCCESS] Seluruh eksekusi dan verifikasi pipeline berhasil 100%!")
        except Exception as e:
            print(f"\n[ERROR] Kegagalan pada langkah pasca-pipeline: {e}")
            sys.exit(1)

if __name__=="__main__": main()
