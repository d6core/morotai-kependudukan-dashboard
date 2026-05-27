"""
01_pembersihan.py — Tahap 1: Pembersihan Data Agregat (Data Cleansing)
======================================================================
Membersihkan 123 file XLSX mentah dari SIAK/Dukcapil dan menyimpan
versi bersih ke folder data/BERSIH_{PERIODE}/

13 Aturan Pembersihan:
  R01 - Baris kosong (semua sel None)           -> Hapus
  R02 - Baris duplikat identik                  -> Hapus
  R03 - Whitespace berlebih pada string         -> Trim & collapse
  R04 - Angka tersimpan sebagai string          -> Konversi ke numerik
  R05 - Nilai negatif pada kolom populasi       -> Flagging (biarkan, LPP boleh negatif)
  R06 - KODE tidak konsisten (ada titik, spasi) -> Normalisasi
  R07 - Header tidak standar (spasi ganda)      -> Normalisasi
  R08 - Nama wilayah tidak konsisten            -> Standardisasi UPPER + trim
  R09 - L + P != JML                            -> Flagging & auto-fix opsional
  R10 - IDEM hilang padahal ada KODE            -> Inferensi dari panjang KODE
  R11 - Sel None pada kolom numerik             -> Isi 0
  R12 - Encoding/karakter aneh                  -> Bersihkan
  R13 - Kode wilayah -> nama wilayah            -> Tambah kolom KABUPATEN/KECAMATAN/DESA

Output:
  - data/BERSIH_{PERIODE}/  (123 file XLSX bersih)
  - output/{PERIODE}/01_pembersihan_{PERIODE}.xlsx (laporan)
"""
import sys, os, re, copy
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path
from datetime import datetime
from config import OUTPUT_DIR, PERIODE, NAMA_KAB, BASE_DIR
from utils import setup_logger, norm_kode

log = setup_logger("01_pembersihan")

# Selalu baca dari AGREGAT (mentah), bukan BERSIH
DATA_DIR = BASE_DIR / "data" / f"AGREGAT_{PERIODE}"
CLEAN_DIR = BASE_DIR / "data" / f"BERSIH_{PERIODE}"
REPORT_XLSX = OUTPUT_DIR / f"01_pembersihan_{PERIODE}.xlsx"

# ── Style helpers ─────────────────────────────────────────────────────────────
NAVY="1B3A6B"; BLUE="2563A8"; ACCENT="C8860A"; WHITE="FFFFFF"
LIGHT="EBF2FA"; ALT="F4F8FD"; MUTED="555577"
GREEN="166534"; GREEN2="DCFCE7"; RED="991B1B"; RED2="FEE2E2"
AMBER="92400E"; AMBER2="FEF3C7"

def ft(b=False,s=11,c="1A1A2E",n="Calibri",i=False): return Font(bold=b,size=s,color=c,name=n,italic=i)
def fl(c): return PatternFill("solid",fgColor=c)
def al(h="left",v="center",w=False): return Alignment(horizontal=h,vertical=v,wrap_text=w)
def bd():
    s=Side(style="thin",color="C5D5E8"); return Border(top=s,bottom=s,left=s,right=s)

# ══════════════════════════════════════════════════════════════════════════════
# R14: KAMUS SINGKATAN → LENGKAP
# ══════════════════════════════════════════════════════════════════════════════

# Mapping untuk HEADER kolom (exact match, case-insensitive)
HEADER_MAP = {
    # Kolom standar
    "IDEM"       : "LEVEL",
    "JML"        : "JUMLAH",
    "L"          : "LAKI_LAKI",
    "P"          : "PEREMPUAN",
    "PR"         : "PEREMPUAN",
    "LK"         : "LAKI_LAKI",
    "NO_PROP"    : "NO_PROVINSI",
    "NO_KAB"     : "NO_KABUPATEN",
    "NO_KEC"     : "NO_KECAMATAN",
    "NO_KEL"     : "NO_KELURAHAN",
    "KEL_UMUR"   : "KELOMPOK_UMUR",
    "AGAMA_KET"  : "AGAMA",
    # Dokumen
    "WKTP"       : "WAJIB_KTP",
    "MMLK"       : "MEMILIKI",
    "BLM_MMLK"   : "BELUM_MEMILIKI",
    "PERSEN"     : "PERSENTASE",
    "CETAK_KK"   : "CETAK_KARTU_KELUARGA",
    "JML_KK"     : "JUMLAH_KK",
    "JML_CETAK_KK"   : "JUMLAH_CETAK_KK",
    "BLM_CETAK_KK_JML": "BELUM_CETAK_KK",
    "REKAM"      : "SUDAH_REKAM",
    "BLM_REKAM"  : "BELUM_REKAM",
}

# Mapping untuk BAGIAN header (substring replacement, applied in order)
HEADER_PART_MAP = {
    "_VERT"  : "",
    "_JML"   : "_JUMLAH",
    "_L"     : "_LAKI_LAKI",
    "_P"     : "_PEREMPUAN",
    "_PR"    : "_PEREMPUAN",
    " L"     : " LAKI_LAKI",
    " P"     : " PEREMPUAN",
    " PR"    : " PEREMPUAN",
    " JML"   : " JUMLAH",
    " LK"    : " LAKI_LAKI",
    "MMLK L" : "MEMILIKI LAKI_LAKI",
    "MMLK P" : "MEMILIKI PEREMPUAN",
    "MMLK JML": "MEMILIKI JUMLAH",
    "BLM_MMLK L" : "BELUM_MEMILIKI LAKI_LAKI",
    "BLM_MMLK P" : "BELUM_MEMILIKI PEREMPUAN",
    "BLM_MMLK JML": "BELUM_MEMILIKI JUMLAH",
}

# Mapping untuk NILAI DATA (exact match per cell)
VALUE_MAP = {
    # Pendidikan
    "TIDAK/BLM SEKOLAH"       : "TIDAK/BELUM SEKOLAH",
    "BELUM TAMAT SD/SEDERAJAT": "BELUM TAMAT SD SEDERAJAT",
    "TAMAT SD/SEDERAJAT"      : "TAMAT SD SEDERAJAT",
    "SLTP/SEDERAJAT"          : "SLTP SEDERAJAT",
    "SLTA/SEDERAJAT"          : "SLTA SEDERAJAT",
    "DIPLOMA I/II"            : "DIPLOMA I / II",
    "DIPLOMA III"             : "DIPLOMA III",
    "STRATA I"                : "SARJANA (S1)",
    "STRATA II"               : "MAGISTER (S2)",
    "STRATA III"              : "DOKTOR (S3)",
    "AKADEMI/DIPLOMA III/S.MUDA": "DIPLOMA III / SARJANA MUDA",
    # Pendidikan dengan kode prefix
    "01 TIDAK/BLM SEKOLAH"         : "TIDAK/BELUM SEKOLAH",
    "02 BELUM TAMAT SD/SEDERAJAT"  : "BELUM TAMAT SD SEDERAJAT",
    "03 TAMAT SD/SEDERAJAT"        : "TAMAT SD SEDERAJAT",
    "04 SLTP/SEDERAJAT"            : "SLTP SEDERAJAT",
    "05 SLTA/SEDERAJAT"            : "SLTA SEDERAJAT",
    "06 DIPLOMA I/II"              : "DIPLOMA I / II",
    "07 AKADEMI/DIPLOMA III/S.MUDA": "DIPLOMA III / SARJANA MUDA",
    "08 DIPLOMA IV/STRATA I"       : "DIPLOMA IV / SARJANA (S1)",
    "09 STRATA II"                 : "MAGISTER (S2)",
    "10 STRATA III"                : "DOKTOR (S3)",
    # Pekerjaan dengan kode prefix
    "01 BELUM/TIDAK BEKERJA"       : "BELUM/TIDAK BEKERJA",
    "02 MENGURUS RUMAH TANGGA"     : "MENGURUS RUMAH TANGGA",
    "03 PELAJAR/MAHASISWA"         : "PELAJAR/MAHASISWA",
    "04 PENSIUNAN"                 : "PENSIUNAN",
    "05 PEGAWAI NEGERI SIPIL (PNS)": "PEGAWAI NEGERI SIPIL (PNS)",
    "06 TENTARA NASIONAL INDONESIA (TNI)": "TNI",
    "07 KEPOLISIAN RI (POLRI)"     : "POLRI",
    # Disabilitas dengan kode prefix
    "01 DISABILITAS FISIK"                : "DISABILITAS FISIK",
    "02 DISABILITAS NETRA/BUTA"           : "DISABILITAS NETRA (BUTA)",
    "03 DISABILITAS RUNGU/WICARA"         : "DISABILITAS RUNGU / WICARA",
    "04 DISABILITAS MENTAL/JIWA"          : "DISABILITAS MENTAL (JIWA)",
    "05 DISABILITAS FISIK DAN MENTAL"     : "DISABILITAS FISIK DAN MENTAL",
    "06 DISABILITAS LAINNYA"              : "DISABILITAS LAINNYA",
    # Disabilitas tanpa kode
    "DISABILITAS NETRA/BUTA"   : "DISABILITAS NETRA (BUTA)",
    "DISABILITAS RUNGU/WICARA" : "DISABILITAS RUNGU / WICARA",
    "DISABILITAS MENTAL/JIWA"  : "DISABILITAS MENTAL (JIWA)",
    # Status kawin
    "BLM KAWIN"    : "BELUM KAWIN",
    "BELUM KAWIN"  : "BELUM KAWIN",
    # Hub keluarga
    "ISTERI"       : "ISTRI",
    "FAMILI LAIN"  : "KELUARGA LAIN",
    "MERTUA"       : "MERTUA",
    "LAINNYA"      : "LAINNYA",
    # Placeholder / null
    "<>"           : "",
    "Null"         : "",
    "NULL"         : "",
    "null"         : "",
    "-"            : "",
}

def expand_header(h):
    """R14: Perluas singkatan di nama kolom header."""
    if not h or not isinstance(h, str):
        return h
    s = h.strip()
    su = s.upper()

    # Exact match dulu
    if su in HEADER_MAP:
        return HEADER_MAP[su]

    # Partial match — hanya di akhir string (suffix)
    result = s

    # Longer patterns first (exact substrings that are safe)
    for abbr, full in sorted(HEADER_PART_MAP.items(), key=lambda x: -len(x[0])):
        # Hanya replace jika abbr ada di AKHIR string (suffix match)
        if result.endswith(abbr):
            result = result[:-len(abbr)] + full
        # Atau jika diikuti spasi/underscore (bukan huruf — hindari LAINNYA dll)
        elif abbr + " " in result:
            result = result.replace(abbr + " ", full + " ")
        elif abbr + "_" in result:
            result = result.replace(abbr + "_", full + "_")

    return result

def expand_value(val):
    """R14: Perluas singkatan di nilai data."""
    if not isinstance(val, str):
        return val
    s = val.strip()
    # Exact match
    if s in VALUE_MAP:
        return VALUE_MAP[s]
    # Case-insensitive exact match
    su = s.upper()
    for k, v in VALUE_MAP.items():
        if su == k.upper():
            return v
    return s

# ══════════════════════════════════════════════════════════════════════════════
# ATURAN PEMBERSIHAN
# ══════════════════════════════════════════════════════════════════════════════

def clean_header(header_row):
    """R07: Bersihkan header — trim, collapse spasi ganda."""
    cleaned = []
    for h in header_row:
        if h is None:
            cleaned.append(None)
        else:
            s = str(h).strip()
            s = re.sub(r'\s+', ' ', s)  # collapse multiple spaces
            cleaned.append(s)
    return cleaned

def clean_string(val):
    """R03 + R12: Trim whitespace, collapse, bersihkan karakter aneh."""
    if not isinstance(val, str):
        return val
    s = val.strip()
    s = re.sub(r'\s+', ' ', s)        # collapse multiple spaces
    s = s.replace('\xa0', ' ')         # non-breaking space
    s = s.replace('\u200b', '')        # zero-width space
    s = s.replace('\ufeff', '')        # BOM
    return s

def try_numeric(val):
    """R04: Coba konversi string ke angka jika memungkinkan."""
    if not isinstance(val, str):
        return val
    s = val.strip()
    if not s or s == '-':
        return 0
    # Cek apakah ini kode wilayah (misal "82.07.01.2001") — jangan konversi
    if re.match(r'^\d{2}(\.\d{2}){1,3}$', s):
        return s
    # Cek format angka: "1,234" atau "1.234,5" atau "-0.83"
    try:
        # Hapus koma ribuan
        clean = s.replace(',', '')
        if '.' in clean:
            return float(clean)
        return int(clean)
    except (ValueError, TypeError):
        return val

def clean_kode(val):
    """R06: Normalisasi kode — hapus titik, jadikan string konsisten."""
    if val is None:
        return ""
    s = str(val).strip().replace(".", "").replace(" ", "")
    return s

def infer_idem(kode_str):
    """R10: Inferensi IDEM dari panjang KODE."""
    k = clean_kode(kode_str)
    kl = len(k)
    if kl <= 4: return 2     # Kabupaten
    elif kl <= 7: return 3   # Kecamatan
    elif kl >= 8: return 4   # Desa/Kelurahan
    return 0

def is_numeric_col(header):
    """Cek apakah kolom ini seharusnya numerik berdasarkan nama."""
    if header is None:
        return False
    h = str(header).upper()
    # Kolom yang BUKAN numerik
    non_num = {"KODE", "WILAYAH", "NAMA_WILAYAH", "KODE_WILAYAH",
               "KEL_UMUR", "UMUR", "AGAMA_KET", "NO_PROP", "NO_KAB",
               "NO_KEC", "NO_KEL", "NO", "DUSUN", "RT", "RW",
               "KABUPATEN", "KECAMATAN", "DESA_KELURAHAN"}
    if h in non_num:
        return False
    return True


def get_table_name(filename):
    from config import F
    for k, v in F.items():
        if v == filename:
            return k
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    return name


def extract_snapshot_date(table_name: str) -> str:
    """
    Ekstrak tanggal dari nama tabel dan kembalikan format ISO YYYY-MM-DD.
    Contoh:
      agr_akta_lahir_all_02032026_8207 -> 2026-03-02
      agr_kia_202502_280226_8207 -> 2026-02-28
    """
    import re
    # Cari pola tanggal DDMMYYYY (8 digit)
    match8 = re.search(r'_(\d{2})(\d{2})(\d{4})', table_name)
    if match8:
        dd, mm, yyyy = match8.groups()
        return f"{yyyy}-{mm}-{dd}"
        
    # Cari pola tanggal DDMMYY (6 digit)
    # Untuk menghindari mencocokkan periode 202502 yang berada di depan,
    # kita cari pola 6 digit yang berada di bagian belakang nama tabel (gunakan yang terakhir)
    match6 = re.findall(r'_(\d{2})(\d{2})(\d{2})(?=_|$)', table_name)
    if match6:
        dd, mm, yy = match6[-1]
        return f"20{yy}-{mm}-{dd}"
        
    return None


def get_consolidated_table(table_name: str) -> str:
    """
    Tentukan nama tabel konsolidasi master untuk tabel snapshot dinamis.
    Menggunakan regex dinamis — TIDAK ada hard-coded tanggal periode.

    Pattern snapshot yang dikenali:
      - agr_akta_lahir_all_DDMMYYYY_8207   → snapshot_akta_lahir
      - agr_rekam_cetak_ektp_DDMMYYYY_8207 → snapshot_ektp
      - agr_kia_XXXXXX_DDMMYY_8207         → snapshot_kia
      - agr_kia_XXXXXX_DDMMYYYY_8207       → snapshot_kia
    """
    import re
    # Pola snapshot = mengandung kode periode (6 digit) DAN tanggal (6 atau 8 digit)
    _HAS_DATE_SUFFIX = re.compile(
        r'_\d{6}_\d{4,8}$|_\d{8}_\d{4}$|_\d{6}$',
        re.IGNORECASE
    )
    if "akta_lahir_all" in table_name:
        return "snapshot_akta_lahir"
    elif "rekam_cetak_ektp" in table_name:
        return "snapshot_ektp"
    elif "kia" in table_name and _HAS_DATE_SUFFIX.search(table_name):
        # Pastikan ini memang snapshot KIA (bukan tabel master kia biasa)
        # Tabel master: "kia", snapshot: "agr_kia_202502_DDMMYY_8207"
        if re.search(r'kia_\d{6}_\d{4,8}', table_name, re.IGNORECASE):
            return "snapshot_kia"
    return None


def save_to_sqlite(filename, headers, data_rows, conn=None):
    import sqlite3
    import re
    from config import SQLITE_DB
    
    table_name = get_table_name(filename)
    if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
        raise ValueError(f"Nama tabel tidak aman: {table_name}")
        
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(SQLITE_DB)
        close_conn = True
        
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Cek apakah ini tabel snapshot berkala yang harus dikonsolidasi
        cons_table = get_consolidated_table(table_name)
        snap_date = extract_snapshot_date(table_name)
        is_consolidated = cons_table is not None and snap_date is not None
        
        target_table = cons_table if is_consolidated else table_name
        
        # DBA Performance Optimization: Deteksi tipe data secara instan menggunakan Pandas vectorization
        import pandas as pd
        df_temp = pd.DataFrame(data_rows, columns=headers)
        col_types = []
        for col in headers:
            col_type = "TEXT"
            series = df_temp[col].dropna()
            if not series.empty:
                first_val = series.iloc[0]
                # DBA Hardening: Konversi scalar numpy ke tipe bawaan Python agar isinstance() bekerja akurat
                if hasattr(first_val, 'item'):
                    try:
                        first_val = first_val.item()
                    except Exception:
                        pass
                if isinstance(first_val, int):
                    col_type = "INTEGER"
                elif isinstance(first_val, float):
                    col_type = "REAL"
            col_types.append(col_type)
            
        # Sanitize header names for SQLite
        safe_headers = []
        seen = {}
        for h in headers:
            sh = str(h)
            sh = sh.replace('+', '_POS').replace('-', '_NEG')
            sh = re.sub(r'[^a-zA-Z0-9_]', '_', sh).strip('_')
            if not sh:
                sh = "col_empty"
            elif sh[0].isdigit():
                sh = "col_" + sh
                
            base_sh = sh
            counter = 1
            while sh.lower() in seen:
                sh = f"{base_sh}_{counter}"
                counter += 1
            seen[sh.lower()] = True
            
            if not re.match(r'^[a-zA-Z0-9_]+$', sh):
                raise ValueError(f"Nama kolom tidak aman: {sh}")
            safe_headers.append(sh)
            
        # Tambahkan kolom tanggal_snapshot jika dikonsolidasikan
        db_rows_to_insert = [list(r) for r in data_rows]
        if is_consolidated:
            safe_headers.append("tanggal_snapshot")
            col_types.append("TEXT")
            for r in db_rows_to_insert:
                r.append(snap_date)
            
        with conn:
            cursor = conn.cursor()
            
            if is_consolidated:
                # Untuk tabel konsolidasian, buat tabelnya jika belum ada (TIDAK di-drop)
                fields = ", ".join(f'"{h}" {t}' for h, t in zip(safe_headers, col_types))
                create_sql = f'CREATE TABLE IF NOT EXISTS "{target_table}" ({fields})'
                cursor.execute(create_sql)
                
                # DBA Evolution: Secara dinamis tambahkan kolom baru jika skema berubah (variasi antar periode)
                cursor.execute(f'PRAGMA table_info("{target_table}")')
                existing_cols = {row[1].lower() for row in cursor.fetchall()}
                for h, t in zip(safe_headers, col_types):
                    if h.lower() not in existing_cols:
                        cursor.execute(f'ALTER TABLE "{target_table}" ADD COLUMN "{h}" {t}')
                
                # Hapus data snapshot tanggal ini jika ada sebelumnya agar idempoten
                cursor.execute(f'DELETE FROM "{target_table}" WHERE "tanggal_snapshot" = ?', (snap_date,))
            else:
                # Untuk tabel biasa, drop dan recreate
                cursor.execute(f'DROP TABLE IF EXISTS "{target_table}"')
                fields = ", ".join(f'"{h}" {t}' for h, t in zip(safe_headers, col_types))
                create_sql = f'CREATE TABLE "{target_table}" ({fields})'
                cursor.execute(create_sql)
            
            # Eksekusi insert data
            placeholders = ", ".join("?" for _ in safe_headers)
            safe_cols_str = ", ".join(f'"{h}"' for h in safe_headers)
            insert_sql = f'INSERT INTO "{target_table}" ({safe_cols_str}) VALUES ({placeholders})'
            
            cursor.executemany(insert_sql, db_rows_to_insert)
            
            # Buat view untuk kompatibilitas ke belakang (zero-breaking changes)
            if is_consolidated:
                # DBA Hardening: Cek tipe objek di sqlite_master untuk drop yang aman tanpa operational error
                cursor.execute("SELECT type FROM sqlite_master WHERE name = ?", (table_name,))
                row_type = cursor.fetchone()
                if row_type:
                    t_type = row_type[0].upper()
                    if t_type == 'VIEW':
                        cursor.execute(f'DROP VIEW "{table_name}"')
                    else:
                        cursor.execute(f'DROP TABLE "{table_name}"')
                # Ambil semua kolom kecuali tanggal_snapshot untuk view agar identik dengan tabel lama
                view_cols = ", ".join(f'"{h}"' for h in safe_headers[:-1])
                create_view_sql = f'CREATE VIEW "{table_name}" AS SELECT {view_cols} FROM "{target_table}" WHERE "tanggal_snapshot" = \'{snap_date}\''
                cursor.execute(create_view_sql)
                
                # Buat index pada kolom tanggal_snapshot
                cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{target_table}_tanggal_snapshot" ON "{target_table}" ("tanggal_snapshot")')
            
            # Create indexes on key searchable columns
            for col in safe_headers:
                col_u = col.upper()
                if col_u in ("KODE", "KODE_WILAYAH", "KODE_DESA", "LEVEL", "IDEM", "WILAYAH", "NAMA_WILAYAH", "KECAMATAN", "DESA_KELURAHAN"):
                    cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{target_table}_{col}" ON "{target_table}" ("{col}")')
                    # [FIX #1] Computed expression index: memungkinkan JOIN dengan replace(KODE,'.','')
                    # tanpa full table scan — kritis untuk performa 03_integrasi dan API
                    if col_u in ("KODE", "KODE_WILAYAH", "KODE_DESA"):
                        cursor.execute(
                            f'CREATE INDEX IF NOT EXISTS "idx_{target_table}_{col}_no_dot" '
                            f'ON "{target_table}" (replace("{col}", \'.\', \'\'))'
                        )
    finally:
        if close_conn:
            conn.close()


def clean_file(src_path, dst_path, conn=None):
    """Bersihkan satu file XLSX -> simpan versi bersih."""
    stats = {
        "empty_rows": 0, "dup_rows": 0, "ws_fixed": 0,
        "str_to_num": 0, "neg_vals": 0, "kode_fixed": 0,
        "hdr_fixed": 0, "none_filled": 0, "idem_inferred": 0,
        "name_fixed": 0, "lp_jml_issues": 0, "wilayah_enriched": 0,
        "abbr_expanded": 0,
    }

    wb = None
    wb_out = None
    try:
        import pandas as pd
        # DBA & Data Engineer Optimization: Membaca excel menggunakan Pandas parser engine
        # Membiarkan Pandas mendeteksi tipe data biner asli Excel (numerik murni tetap int/float) agar presisi
        df = pd.read_excel(src_path, header=None)
        df = df.where(df.notna(), None)
        raw_rows = df.values.tolist()
        if not raw_rows:
            return stats

        # R07: Clean headers
        orig_headers = raw_rows[0]
        headers = clean_header(orig_headers)
        for i, (o, c) in enumerate(zip(orig_headers, headers)):
            if o != c:
                stats["hdr_fixed"] += 1

        # R14: Expand header abbreviations
        expanded_headers = []
        for h in headers:
            exp = expand_header(h)
            if exp != h:
                stats["abbr_expanded"] += 1
            expanded_headers.append(exp)
        headers = expanded_headers

        data_rows = raw_rows[1:]

        # R01: Remove empty rows
        non_empty = []
        for r in data_rows:
            if all(v is None for v in r):
                stats["empty_rows"] += 1
            else:
                non_empty.append(list(r))
        data_rows = non_empty

        # R02: Remove exact duplicate rows
        seen = set()
        unique_rows = []
        for r in data_rows:
            key = tuple(r)
            if key in seen:
                stats["dup_rows"] += 1
            else:
                seen.add(key)
                unique_rows.append(r)
        data_rows = unique_rows

        # Find column indices
        hdr_upper = [str(h).upper() if h else "" for h in headers]
        kode_idx = None
        idem_idx = None
        wilayah_idx = None
        for i, h in enumerate(hdr_upper):
            if h in ("KODE", "KODE_WILAYAH"):
                kode_idx = i
            if h in ("IDEM", "LEVEL"):
                idem_idx = i
            if h in ("WILAYAH", "NAMA_WILAYAH"):
                wilayah_idx = i

        # R10: Add LEVEL if completely missing but KODE is present
        if idem_idx is None and kode_idx is not None:
            headers.append("LEVEL")
            hdr_upper.append("LEVEL")
            idem_idx = len(headers) - 1
            for row in data_rows:
                kode_val = row[kode_idx] if kode_idx < len(row) else None
                inferred = infer_idem(kode_val) if kode_val else 0
                row.append(inferred)

        # Identify L/P/JML column groups for R09
        lp_groups = []
        for i, h in enumerate(headers):
            if h and str(h).upper().endswith("_L"):
                base = str(h)[:-2]
                p_col = None; jml_col = None
                for j, h2 in enumerate(headers):
                    if h2 and str(h2).upper() == f"{base.upper()}_P":
                        p_col = j
                    if h2 and str(h2).upper() == f"{base.upper()}_JML":
                        jml_col = j
                if p_col is not None and jml_col is not None:
                    lp_groups.append((i, p_col, jml_col, base))
        # Also check simple L, P, JML
        simple_l = simple_p = simple_jml = None
        for i, h in enumerate(hdr_upper):
            if h == "L": simple_l = i
            if h == "P": simple_p = i
            if h == "JML": simple_jml = i
        if simple_l is not None and simple_p is not None and simple_jml is not None:
            lp_groups.append((simple_l, simple_p, simple_jml, ""))

        # Process each row
        for row in data_rows:
            for i in range(len(row)):
                v = row[i]
                h = headers[i] if i < len(headers) else None
                hu = hdr_upper[i] if i < len(hdr_upper) else ""

                # R03 + R12: Clean strings
                if isinstance(v, str):
                    cleaned = clean_string(v)
                    if cleaned != v:
                        stats["ws_fixed"] += 1
                        row[i] = cleaned
                    v = row[i]

                # R06: Normalize KODE
                if i == kode_idx and v is not None:
                    orig = str(v)
                    normed = norm_kode(v)
                    # Preserve dotted format for clean output but record fix
                    if orig != str(v):
                        stats["kode_fixed"] += 1

                # R08: Standardize wilayah names
                if i == wilayah_idx and isinstance(v, str):
                    upper = v.upper().strip()
                    if upper != v:
                        row[i] = upper
                        stats["name_fixed"] += 1

                # R14: Expand abbreviations in string values
                if isinstance(row[i], str) and i != kode_idx and i != wilayah_idx:
                    expanded = expand_value(row[i])
                    if expanded != row[i]:
                        row[i] = expanded
                        stats["abbr_expanded"] += 1

                # R04: Convert string numbers to actual numbers
                if is_numeric_col(h) and isinstance(v, str):
                    converted = try_numeric(v)
                    if converted != v:
                        row[i] = converted
                        stats["str_to_num"] += 1

                # R11: Fill None in numeric columns with 0
                if is_numeric_col(h) and v is None:
                    row[i] = 0
                    stats["none_filled"] += 1

                # R05: Flag negatives (don't auto-fix — LPP can be negative)
                if isinstance(row[i], (int, float)) and row[i] < 0:
                    stats["neg_vals"] += 1

            # R10: Infer IDEM if missing
            if idem_idx is not None and kode_idx is not None:
                if row[idem_idx] is None or row[idem_idx] == "":
                    kode_val = row[kode_idx] if kode_idx < len(row) else None
                    if kode_val:
                        row[idem_idx] = infer_idem(kode_val)
                        stats["idem_inferred"] += 1

            # R09: Check L + P = JML consistency
            for l_idx, p_idx, jml_idx, base in lp_groups:
                if l_idx < len(row) and p_idx < len(row) and jml_idx < len(row):
                    lv = row[l_idx]; pv = row[p_idx]; jv = row[jml_idx]
                    if isinstance(lv, (int, float)) and isinstance(pv, (int, float)) and isinstance(jv, (int, float)):
                        expected = lv + pv
                        if abs(expected - jv) > 0.5:  # tolerance for rounding
                            stats["lp_jml_issues"] += 1
                            # [FIX #4] Log detail sebelum auto-fix agar bisa diaudit
                            kode_val = row[kode_idx] if kode_idx is not None and kode_idx < len(row) else "?"
                            log.warning(
                                f"R09 auto-fix: file={src_path.name}, "
                                f"KODE={kode_val}, kolom={base or 'L/P/JML'}, "
                                f"L={lv}, P={pv}, JML={jv} → {expected}"
                            )
                            # Auto-fix: set JML = L + P
                            row[jml_idx] = expected

        # ══ R13: Enrichment — tambah kolom KABUPATEN, KECAMATAN, DESA_KELURAHAN ══
        if kode_idx is not None and wilayah_idx is not None:
            # Pass 1: bangun lookup KODE -> NAMA dari data ini
            kode_nama = {}
            for row in data_rows:
                if kode_idx < len(row) and wilayah_idx < len(row):
                    kv = row[kode_idx]
                    nv = row[wilayah_idx]
                    if kv is not None and nv is not None:
                        k = norm_kode(str(kv))
                        kode_nama[k] = str(nv).strip().upper()

            # Tentukan nama kab/kec/desa untuk setiap kode
            # Kab: kode 4 digit, Kec: 6-7 digit, Desa: 10 digit
            nama_kab_map = {k: v for k, v in kode_nama.items() if len(k) <= 4}
            nama_kec_map = {k: v for k, v in kode_nama.items() if 5 <= len(k) <= 7}
            nama_des_map = {k: v for k, v in kode_nama.items() if len(k) >= 8}

            # Default nama kabupaten (biasanya hanya 1)
            default_kab = list(nama_kab_map.values())[0] if nama_kab_map else ""

            # Tambah 3 kolom baru di header
            # Cari posisi setelah WILAYAH
            insert_pos = wilayah_idx + 1
            headers.insert(insert_pos, "KABUPATEN")
            headers.insert(insert_pos + 1, "KECAMATAN")
            headers.insert(insert_pos + 2, "DESA_KELURAHAN")
            hdr_upper = [str(h).upper() if h else "" for h in headers]

            # Pass 2: isi kolom baru untuk setiap baris
            for row in data_rows:
                kv = row[kode_idx] if kode_idx < len(row) else None
                k = norm_kode(str(kv)) if kv else ""
                kl = len(k)

                nama_kab = default_kab
                nama_kec = ""
                nama_des = ""

                if kl >= 8:  # Desa
                    nama_des = kode_nama.get(k, "")
                    kode_kec = k[:6] if len(k) == 10 else k[:7]
                    nama_kec = nama_kec_map.get(kode_kec, nama_kec_map.get(k[:6], ""))
                elif 5 <= kl <= 7:  # Kecamatan
                    nama_kec = kode_nama.get(k, "")
                elif kl <= 4:  # Kabupaten
                    nama_kab = kode_nama.get(k, default_kab)

                row.insert(insert_pos, nama_kab)
                row.insert(insert_pos + 1, nama_kec)
                row.insert(insert_pos + 2, nama_des)
                stats["wilayah_enriched"] += 1

        # Write cleaned file using Pandas - DBA/Data Engineer Performance Tuning
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        padded_rows = []
        for row in data_rows:
            # Pad row if shorter than headers
            r = list(row)
            while len(r) < len(headers):
                r.append(0)
            padded_rows.append(r[:len(headers)])
            
        df_out = pd.DataFrame(padded_rows, columns=headers)
        df_out.to_excel(dst_path, index=False)

        # Save to SQLite database
        try:
            save_to_sqlite(src_path.name, headers, padded_rows, conn=conn)
        except Exception as e:
            log.warning(f"    ! Failed to save {src_path.name} to SQLite: {e}")

    finally:
        if wb is not None:
            wb.close()
        if wb_out is not None:
            wb_out.close()

    return stats


# ══════════════════════════════════════════════════════════════════════════════
# LAPORAN
# ══════════════════════════════════════════════════════════════════════════════

def write_report(all_stats, total_files, duration):
    """Tulis laporan pembersihan ke XLSX."""
    wb = Workbook()
    wb.remove(wb.active)

    # ── Sheet 1: Ringkasan ────────────────────────────────────────────────
    ws = wb.create_sheet("Ringkasan", 0)
    ws.sheet_view.showGridLines = False
    for c, w in {"A":4,"B":30,"C":16,"D":16,"E":16,"F":4}.items():
        ws.column_dimensions[c].width = w

    # Banner
    for r in (1,2):
        for c in range(1,7): ws.cell(r,c).fill = fl(NAVY)
    ws.row_dimensions[1].height = 8
    ws.row_dimensions[2].height = 42
    ws.row_dimensions[3].height = 4
    for c in range(1,7): ws.cell(3,c).fill = fl(ACCENT)
    ws.merge_cells("B2:E2"); c = ws.cell(2,2)
    c.value = f"LAPORAN PEMBERSIHAN DATA -- {NAMA_KAB}"
    c.font = ft(True,16,WHITE,"Georgia"); c.alignment = al("center","center")
    ws.merge_cells("B4:E4"); c = ws.cell(4,2)
    c.value = f"Periode: {PERIODE} | {datetime.now():%d %B %Y %H:%M} | Durasi: {duration:.0f}s"
    c.font = ft(i=True,s=10,c=MUTED); c.alignment = al("center","center")

    # Statistik total
    totals = {}
    for key in ["empty_rows","dup_rows","ws_fixed","str_to_num","neg_vals",
                "kode_fixed","hdr_fixed","none_filled","idem_inferred",
                "name_fixed","lp_jml_issues","wilayah_enriched","abbr_expanded"]:
        totals[key] = sum(s.get(key, 0) for s in all_stats.values())

    total_fixes = sum(v for k, v in totals.items() if k not in ("neg_vals","wilayah_enriched"))
    r = 6
    ws.merge_cells(f"B{r}:E{r}"); c = ws.cell(r,2)
    c.value = f"TOTAL: {total_fixes:,} perbaikan + {totals['wilayah_enriched']:,} baris diperkaya pada {total_files} file"
    c.font = ft(True,12,NAVY,"Georgia"); c.fill = fl(LIGHT)
    c.alignment = al("center","center"); c.border = bd()

    r = 8
    metrics = [
        ("R01 -- Baris Kosong Dihapus", totals["empty_rows"], "baris"),
        ("R02 -- Baris Duplikat Dihapus", totals["dup_rows"], "baris"),
        ("R03 -- Whitespace Dibersihkan", totals["ws_fixed"], "sel"),
        ("R04 -- String -> Numerik", totals["str_to_num"], "sel"),
        ("R05 -- Nilai Negatif (flag)", totals["neg_vals"], "sel"),
        ("R07 -- Header Dinormalisasi", totals["hdr_fixed"], "kolom"),
        ("R08 -- Nama Wilayah Distandardisasi", totals["name_fixed"], "sel"),
        ("R09 -- L+P!=JML Diperbaiki", totals["lp_jml_issues"], "sel"),
        ("R10 -- IDEM Diinferensi", totals["idem_inferred"], "baris"),
        ("R11 -- None -> 0 (numerik)", totals["none_filled"], "sel"),
        ("R13 -- Kolom Nama Wilayah Ditambahkan", totals["wilayah_enriched"], "baris"),
        ("R14 -- Singkatan Diperluas", totals["abbr_expanded"], "sel"),
    ]
    for i, h in enumerate(["Aturan", "Jumlah", "Satuan"]):
        c = ws.cell(r, i+2); c.value = h; c.font = ft(True,10,WHITE)
        c.fill = fl(BLUE); c.alignment = al("center","center"); c.border = bd()
    r += 1
    for i, (label, count, unit) in enumerate(metrics):
        bg = LIGHT if i % 2 == 0 else WHITE
        clr = RED if count > 0 and "flag" not in label else "1A1A2E"
        for j, v in enumerate([label, f"{count:,}", unit]):
            c = ws.cell(r, j+2); c.value = v
            c.fill = fl(bg); c.border = bd()
            c.font = ft(s=10, b=(j==1), c=clr if j==1 else "1A1A2E")
            c.alignment = al("center" if j > 0 else "left", "center")
        r += 1

    # ── Sheet 2: Detail per File ──────────────────────────────────────────
    ws2 = wb.create_sheet("Detail per File")
    ws2.sheet_view.showGridLines = False
    cols = ["File", "Empty", "Dup", "WS", "Str>Num", "Neg", "Hdr",
            "Name", "L+P", "IDEM", "None>0", "Total Fix"]
    widths = [50, 8, 8, 8, 10, 8, 8, 8, 8, 8, 10, 12]
    for i, w in enumerate(widths):
        ws2.column_dimensions[get_column_letter(i+1)].width = w

    # Banner
    for rr in (1,2):
        for cc in range(1, len(cols)+1): ws2.cell(rr, cc).fill = fl(NAVY)
    ws2.row_dimensions[1].height = 8; ws2.row_dimensions[2].height = 36
    ws2.row_dimensions[3].height = 4
    for cc in range(1, len(cols)+1): ws2.cell(3, cc).fill = fl(ACCENT)
    ws2.merge_cells(f"A2:{get_column_letter(len(cols))}2")
    c = ws2.cell(2,1); c.value = "DETAIL PEMBERSIHAN PER FILE"
    c.font = ft(True,14,WHITE,"Georgia"); c.alignment = al("center","center")

    r = 5
    for i, h in enumerate(cols):
        c = ws2.cell(r, i+1); c.value = h; c.font = ft(True,9,WHITE)
        c.fill = fl(BLUE); c.alignment = al("center","center",True); c.border = bd()
    r += 1

    # Sort by total fixes descending
    sorted_files = sorted(all_stats.items(),
                         key=lambda x: sum(v for k,v in x[1].items() if k != "neg_vals"),
                         reverse=True)
    for idx, (fname, st) in enumerate(sorted_files):
        total_fix = sum(v for k, v in st.items() if k != "neg_vals")
        vals = [
            fname[:48],
            st["empty_rows"], st["dup_rows"], st["ws_fixed"], st["str_to_num"],
            st["neg_vals"], st["hdr_fixed"], st["name_fixed"],
            st["lp_jml_issues"], st["idem_inferred"], st["none_filled"],
            total_fix
        ]
        bg = LIGHT if idx % 2 == 0 else WHITE
        if total_fix > 100:
            bg = AMBER2
        ws2.row_dimensions[r].height = 16
        for j, v in enumerate(vals):
            c = ws2.cell(r, j+1); c.value = v
            c.fill = fl(bg); c.border = bd()
            c.font = ft(s=9, b=(j==len(vals)-1))
            c.alignment = al("left" if j==0 else "center", "center")
        r += 1

    # ── Sheet 3: File Bersih ──────────────────────────────────────────────
    ws3 = wb.create_sheet("Lokasi Output")
    ws3.sheet_view.showGridLines = False
    ws3.column_dimensions["A"].width = 4
    ws3.column_dimensions["B"].width = 60
    ws3.column_dimensions["C"].width = 4
    for rr in (1,2):
        for cc in range(1,4): ws3.cell(rr,cc).fill = fl(NAVY)
    ws3.row_dimensions[1].height = 8; ws3.row_dimensions[2].height = 36
    ws3.merge_cells("A2:C2"); c = ws3.cell(2,1)
    c.value = "INFORMASI OUTPUT"; c.font = ft(True,14,WHITE,"Georgia")
    c.alignment = al("center","center")
    r = 4
    info = [
        ("Data mentah:", str(DATA_DIR)),
        ("Data bersih:", str(CLEAN_DIR)),
        ("Laporan:", str(REPORT_XLSX)),
        ("File diproses:", f"{total_files} file XLSX"),
        ("Total perbaikan:", f"{total_fixes:,} sel/baris"),
        ("", ""),
        ("CATATAN:", ""),
        ("", "Tahap 02-06 otomatis menggunakan data BERSIH jika tersedia."),
        ("", "Data mentah (AGREGAT) TIDAK dimodifikasi."),
    ]
    for label, val in info:
        c = ws3.cell(r, 2)
        if label and label == "CATATAN:":
            c.value = label; c.font = ft(True, 11, NAVY, "Georgia")
        elif label:
            c.value = f"{label} {val}"; c.font = ft(s=10, b=True)
        else:
            c.value = val; c.font = ft(s=10, i=True, c=MUTED)
        r += 1

    wb.save(REPORT_XLSX)
    log.info(f"  Laporan: {REPORT_XLSX}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def write_pipeline_metadata(conn, total_files, total_fixes, duration):
    """DBA: Mencatat log eksekusi pipeline secara dinamis ke tabel pipeline_metadata."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                periode TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                total_fixes INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.execute("""
            INSERT INTO pipeline_metadata (timestamp, periode, total_files, total_fixes, duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            PERIODE,
            total_files,
            total_fixes,
            duration,
            "SUCCESS"
        ))
    log.info("  [DBA] Metadata eksekusi berhasil dicatat ke tabel `pipeline_metadata`.")


def main():
    import time
    import sqlite3
    from config import SQLITE_DB
    t0 = time.time()
    log.info("=" * 60)
    log.info(f"TAHAP 1 -- PEMBERSIHAN DATA {PERIODE}")
    log.info(f"Kabupaten: {NAMA_KAB}")
    log.info(f"Sumber : {DATA_DIR}")
    log.info(f"Target : {CLEAN_DIR}")
    log.info("=" * 60)

    if not DATA_DIR.exists():
        log.error(f"Folder data tidak ditemukan: {DATA_DIR}")
        return

    files = sorted(DATA_DIR.glob("*.xlsx"))
    log.info(f"Total file: {len(files)}")

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    all_stats = {}

    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        # DBA Performance Optimization: Mengurangi sinkronisasi disk fisik per transaksi & mengutamakan memory caching
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA cache_size = -20000") # Cache size set ke 20MB memori RAM
        
        for i, src in enumerate(files):
            dst = CLEAN_DIR / src.name
            log.info(f"  [{i+1:3d}/{len(files)}] {src.name[:60]}...")
            try:
                stats = clean_file(src, dst, conn=conn)
                all_stats[src.name] = stats
                total_fix = sum(v for k, v in stats.items() if k != "neg_vals")
                if total_fix > 0:
                    log.debug(f"    -> {total_fix} perbaikan")
            except Exception as e:
                log.warning(f"    ! Error: {e}")
                all_stats[src.name] = {"empty_rows":0,"dup_rows":0,"ws_fixed":0,
                    "str_to_num":0,"neg_vals":0,"kode_fixed":0,"hdr_fixed":0,
                    "none_filled":0,"idem_inferred":0,"name_fixed":0,"lp_jml_issues":0,
                    "wilayah_enriched":0,"abbr_expanded":0}

        duration = time.time() - t0
        total_fixes = sum(
            sum(v for k, v in s.items() if k != "neg_vals")
            for s in all_stats.values()
        )
        log.info(f"\n>> Data bersih: {CLEAN_DIR}")
        log.info(f"   -> {len(files)} file diproses")
        log.info(f"   -> {total_fixes:,} total perbaikan")
        log.info(f"   -> Durasi: {duration:.1f}s")

        try:
            write_pipeline_metadata(conn, len(files), total_fixes, duration)
        except Exception as e:
            log.warning(f"  ! Gagal mencatat pipeline metadata: {e}")

        # [FIX #1] ANALYZE: Perbarui statistik query planner SQLite setelah semua index dibuat
        # Ini memastikan SQLite menggunakan computed index (KODE_no_dot) secara optimal
        try:
            log.info("  [DBA] Menjalankan ANALYZE untuk memperbarui statistik query planner...")
            conn.execute("ANALYZE")
            conn.commit()
            log.info("  [DBA] ANALYZE selesai — query planner statistics diperbarui.")
        except Exception as e:
            log.warning(f"  ! ANALYZE gagal (tidak kritis): {e}")

        write_report(all_stats, len(files), duration)
        log.info("=" * 60)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
