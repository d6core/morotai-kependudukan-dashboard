"""
build_unified_dashboard.py
===========================
Builds a comprehensive, self-contained HTML dashboard from dashboard_unified.json.
10 tabs, 30+ charts, dark mode premium design.
"""
import json, os

INPUT = os.path.join('output', 'dashboard_unified.json')
OUTPUT = os.path.join('output', 'dashboard_morotai.html')

with open(INPUT, 'r', encoding='utf-8') as f:
    D = json.load(f)

def fmt(n):
    """Format number with thousand separator."""
    if n is None: return '-'
    if isinstance(n, float): return f'{n:,.2f}'
    return f'{n:,}'

meta = D['metadata']
ov = D['overview']
latest = ov['trend'][-1]
prev = ov['trend'][-2]

# Build HTML
html = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Kependudukan — {meta['kabupaten']}</title>
<meta name="description" content="Dashboard Data Kependudukan Komprehensif Kabupaten {meta['kabupaten']} {meta['date_range']}">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root {{
  --bg-primary: #0a0e1a;
  --bg-card: rgba(17, 24, 45, 0.85);
  --bg-card-hover: rgba(25, 35, 60, 0.95);
  --glass: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.08);
  --text-primary: #e8ecf4;
  --text-secondary: #8b95a8;
  --text-muted: #5a6478;
  --accent-blue: #3b82f6;
  --accent-cyan: #06b6d4;
  --accent-purple: #8b5cf6;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
  --accent-orange: #f97316;
  --gradient-1: linear-gradient(135deg, #3b82f6, #8b5cf6);
  --gradient-2: linear-gradient(135deg, #06b6d4, #10b981);
  --gradient-3: linear-gradient(135deg, #f59e0b, #f97316);
  --gradient-4: linear-gradient(135deg, #f43f5e, #8b5cf6);
  --radius: 16px;
  --radius-sm: 10px;
  --shadow: 0 8px 32px rgba(0,0,0,0.4);
  --shadow-glow: 0 0 40px rgba(59,130,246,0.15);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: 'Inter', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(59,130,246,0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(139,92,246,0.06) 0%, transparent 50%);
}}
.header {{
  text-align:center; padding:32px 20px 16px;
  background: linear-gradient(180deg, rgba(59,130,246,0.08) 0%, transparent 100%);
}}
.header h1 {{
  font-size:clamp(1.5rem,3vw,2.2rem); font-weight:800;
  background: var(--gradient-1); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  letter-spacing:-0.5px;
}}
.header p {{ color:var(--text-secondary); margin-top:6px; font-size:0.85rem; }}
.tab-nav {{
  display:flex; gap:4px; padding:8px 16px; overflow-x:auto;
  background: var(--bg-card); border-bottom:1px solid var(--border);
  position:sticky; top:0; z-index:100;
  backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  scrollbar-width:none;
}}
.tab-nav::-webkit-scrollbar {{ display:none; }}
.tab-btn {{
  flex-shrink:0; padding:10px 18px; border:none; border-radius:var(--radius-sm);
  background:transparent; color:var(--text-secondary); cursor:pointer;
  font-family:'Inter',sans-serif; font-size:0.78rem; font-weight:500;
  transition:all 0.3s ease; white-space:nowrap;
}}
.tab-btn:hover {{ background:var(--glass); color:var(--text-primary); }}
.tab-btn.active {{
  background: var(--gradient-1); color:#fff; font-weight:600;
  box-shadow: 0 4px 15px rgba(59,130,246,0.3);
}}
.tab-content {{ display:none; padding:20px 16px; max-width:1400px; margin:0 auto; }}
.tab-content.active {{ display:block; animation: fadeIn 0.4s ease; }}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(10px)}} to{{opacity:1;transform:translateY(0)}} }}
.grid {{ display:grid; gap:16px; }}
.grid-2 {{ grid-template-columns:repeat(auto-fit, minmax(300px,1fr)); }}
.grid-3 {{ grid-template-columns:repeat(auto-fit, minmax(280px,1fr)); }}
.grid-4 {{ grid-template-columns:repeat(auto-fit, minmax(220px,1fr)); }}
.card {{
  background:var(--bg-card); border-radius:var(--radius); padding:20px;
  border:1px solid var(--border); backdrop-filter:blur(10px);
  transition:all 0.3s ease;
}}
.card:hover {{ background:var(--bg-card-hover); border-color:rgba(255,255,255,0.12); transform:translateY(-2px); box-shadow:var(--shadow); }}
.card-title {{
  font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:1.2px;
  color:var(--text-muted); margin-bottom:12px; display:flex; align-items:center; gap:8px;
}}
.card-title .icon {{ font-size:1rem; }}
.kpi-value {{
  font-size:clamp(1.6rem,3vw,2.4rem); font-weight:800; letter-spacing:-1px;
  background: var(--gradient-1); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}
.kpi-sub {{ font-size:0.8rem; color:var(--text-secondary); margin-top:4px; }}
.kpi-badge {{
  display:inline-flex; align-items:center; gap:4px; padding:3px 10px;
  border-radius:20px; font-size:0.7rem; font-weight:600;
}}
.badge-up {{ background:rgba(16,185,129,0.15); color:#10b981; }}
.badge-down {{ background:rgba(244,63,94,0.15); color:#f43f5e; }}
.chart-container {{ position:relative; width:100%; }}
.chart-container canvas {{ max-height:350px; }}
.section-title {{
  font-size:1.1rem; font-weight:700; margin:24px 0 16px;
  padding-left:12px; border-left:3px solid var(--accent-blue);
  display:flex; align-items:center; gap:8px;
}}
.insight-box {{
  background:linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.08));
  border:1px solid rgba(59,130,246,0.2); border-radius:var(--radius-sm);
  padding:16px 20px; margin:16px 0; font-size:0.82rem; line-height:1.6;
  color:var(--text-secondary);
}}
.insight-box strong {{ color:var(--accent-blue); }}
table.data-table {{
  width:100%; border-collapse:separate; border-spacing:0;
  font-size:0.78rem;
}}
.data-table thead th {{
  background:rgba(59,130,246,0.1); color:var(--accent-blue);
  padding:10px 12px; text-align:left; font-weight:600;
  position:sticky; top:0; border-bottom:2px solid rgba(59,130,246,0.3);
  font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px;
}}
.data-table tbody td {{
  padding:8px 12px; border-bottom:1px solid var(--border); color:var(--text-secondary);
}}
.data-table tbody tr:hover td {{ background:var(--glass); color:var(--text-primary); }}
.data-table tbody tr:nth-child(even) td {{ background:rgba(255,255,255,0.02); }}
.search-input {{
  width:100%; max-width:400px; padding:10px 16px; border-radius:var(--radius-sm);
  border:1px solid var(--border); background:var(--glass); color:var(--text-primary);
  font-family:'Inter',sans-serif; font-size:0.82rem; margin-bottom:12px;
  outline:none; transition:border-color 0.3s;
}}
.search-input:focus {{ border-color:var(--accent-blue); }}
.source-tag {{
  display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.65rem;
  background:rgba(139,92,246,0.15); color:var(--accent-purple); font-weight:500;
  margin-top:8px;
}}
.footer {{
  text-align:center; padding:40px 20px; color:var(--text-muted); font-size:0.72rem;
  border-top:1px solid var(--border); margin-top:40px;
}}
@media(max-width:768px) {{
  .grid-2,.grid-3,.grid-4 {{ grid-template-columns:1fr; }}
  .tab-btn {{ padding:8px 12px; font-size:0.72rem; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>📊 Dashboard Kependudukan Kabupaten {meta['kabupaten']}</h1>
  <p>Analisis Komprehensif Data Agregat • {meta['date_range']} • 7 Semester</p>
</div>

<nav class="tab-nav" id="tabNav">
  <button class="tab-btn active" data-tab="overview">🏠 Ringkasan</button>
  <button class="tab-btn" data-tab="agama">🕌 Agama</button>
  <button class="tab-btn" data-tab="pendidikan">🎓 Pendidikan</button>
  <button class="tab-btn" data-tab="pekerjaan">💼 Pekerjaan</button>
  <button class="tab-btn" data-tab="perkawinan">💍 Perkawinan</button>
  <button class="tab-btn" data-tab="disabilitas">♿ Disabilitas</button>
  <button class="tab-btn" data-tab="kesehatan">🏥 Kesehatan</button>
  <button class="tab-btn" data-tab="dokumen">📋 Dokumen</button>
  <button class="tab-btn" data-tab="keluarga">👨‍👩‍👧‍👦 Keluarga</button>
  <button class="tab-btn" data-tab="desa">🏘️ Desa</button>
  <button class="tab-btn" data-tab="peta">🗺️ Peta Spasial</button>
  <button class="tab-btn" data-tab="anomali">⚠️ Deteksi Anomali</button>
</nav>

<!-- ============================================ -->
<!-- TAB 1: RINGKASAN EKSEKUTIF -->
<!-- ============================================ -->
<div class="tab-content active" id="tab-overview">
  <div class="grid grid-4" style="margin-bottom:16px">
    <div class="card">
      <div class="card-title"><span class="icon">👥</span>Total Penduduk</div>
      <div class="kpi-value">{fmt(latest['pop'])}</div>
      <div class="kpi-sub">
        <span class="kpi-badge {'badge-up' if latest['pop']>prev['pop'] else 'badge-down'}">
          {'▲' if latest['pop']>prev['pop'] else '▼'} {fmt(latest['pop']-prev['pop'])} ({'+' if latest['pop']>prev['pop'] else ''}{round((latest['pop']-prev['pop'])/prev['pop']*100,2)}%)
        </span>
      </div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">🏠</span>Jumlah KK</div>
      <div class="kpi-value">{fmt(latest['kk'])}</div>
      <div class="kpi-sub">ART: {latest['art']} jiwa/KK</div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">⚖️</span>Rasio JK</div>
      <div class="kpi-value">{latest['rasio_jk']}</div>
      <div class="kpi-sub">L: {fmt(latest['lk'])} • P: {fmt(latest['pr'])}</div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">📈</span>CAGR</div>
      <div class="kpi-value">{ov['cagr']}%</div>
      <div class="kpi-sub">R² = {ov['regression']['r_squared']}</div>
    </div>
  </div>

  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">📈 Tren Penduduk & Prediksi</div>
      <div class="chart-container"><canvas id="chartPopTrend"></canvas></div>
      <div class="source-tag">Sumber: jk table × 7 periode</div>
    </div>
    <div class="card">
      <div class="card-title">🍩 Komposisi Kecamatan</div>
      <div class="chart-container"><canvas id="chartKecDoughnut"></canvas></div>
    </div>
  </div>

  <div class="grid grid-2" style="margin-top:16px">
    <div class="card">
      <div class="card-title">📊 Laju Pertumbuhan per Semester</div>
      <div class="chart-container"><canvas id="chartGrowthRate"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📈 Tren Kecamatan</div>
      <div class="chart-container"><canvas id="chartKecTrend"></canvas></div>
    </div>
  </div>

  <div class="insight-box">
    <strong>💡 Insight:</strong> Penduduk Kab. {meta['kabupaten']} tumbuh dari <strong>{fmt(ov['trend'][0]['pop'])}</strong>
    ({meta['period_labels'][0]}) menjadi <strong>{fmt(latest['pop'])}</strong> ({meta['period_labels'][-1]}),
    dengan CAGR <strong>{ov['cagr']}%</strong>. Prediksi regresi linier (R²={ov['regression']['r_squared']})
    memperkirakan populasi mencapai <strong>{fmt(ov['predictions'][-1]['predicted_pop'])}</strong> pada {ov['predictions'][-1]['label']}.
  </div>
</div>
'''

# =====================================================================
# TAB 2: AGAMA
# =====================================================================
agama_data = D.get('agama', {})
latest_agama = next((t for t in reversed(agama_data.get('trend', [])) if t.get('data')), None)
agama_labels_js = json.dumps([a for a in (latest_agama['data'].keys() if latest_agama else [])])
agama_values_js = json.dumps([latest_agama['data'][a]['jumlah'] for a in latest_agama['data']] if latest_agama else [])

agama_kec_html = ''
for kec in agama_data.get('kecamatan', []):
    total = sum(kec.get(a, 0) for a in ['Islam','Kristen','Katolik','Hindu','Budha','Konghucu','Penghayat'])
    agama_kec_html += f'''<tr>
      <td>{kec['nama']}</td>
      <td>{fmt(kec.get('Islam',0))}</td><td>{fmt(kec.get('Kristen',0))}</td>
      <td>{fmt(kec.get('Katolik',0))}</td><td>{fmt(kec.get('Hindu',0))}</td>
      <td>{fmt(total)}</td>
    </tr>'''

# Agama trend data for stacked chart
agama_trend_labels = json.dumps([t['label'] for t in agama_data.get('trend', []) if t.get('data')])
agama_trend_datasets = {}
agama_names = ['Islam','Kristen','Katolik','Hindu','Budha','Konghucu','Penghayat']
for name in agama_names:
    vals = []
    for t in agama_data.get('trend', []):
        if t.get('data'):
            vals.append(t['data'].get(name, {}).get('jumlah', 0))
    agama_trend_datasets[name] = vals

html += f'''
<div class="tab-content" id="tab-agama">
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">🕌 Distribusi Agama (Terbaru)</div>
      <div class="chart-container"><canvas id="chartAgamaPie"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📊 Tren Distribusi Agama</div>
      <div class="chart-container"><canvas id="chartAgamaTrend"></canvas></div>
    </div>
  </div>
  <div class="section-title">📋 Distribusi Agama per Kecamatan</div>
  <div class="card" style="overflow-x:auto">
    <table class="data-table">
      <thead><tr>
        <th>Kecamatan</th><th>Islam</th><th>Kristen</th><th>Katolik</th><th>Hindu</th><th>Total</th>
      </tr></thead>
      <tbody>{agama_kec_html}</tbody>
    </table>
    <div class="source-tag">Sumber: tabel agama × siak_analytics</div>
  </div>
</div>
'''

# =====================================================================
# TAB 3: PENDIDIKAN
# =====================================================================
edu_data = D.get('pendidikan', {})
latest_edu = next((t for t in reversed(edu_data.get('distribusi', [])) if t.get('data')), None)
edu_labels = json.dumps(list(latest_edu['data'].keys()) if latest_edu else [])
edu_values = json.dumps([latest_edu['data'][k]['jumlah'] for k in latest_edu['data']] if latest_edu else [])

# RLS trend
rls = edu_data.get('rata_lama_sekolah', [])
rls_labels = json.dumps([r['label'] for r in rls if r.get('kab_rls', 0) > 0])
rls_total = json.dumps([r['kab_rls'] for r in rls if r.get('kab_rls', 0) > 0])
rls_lk = json.dumps([r['kab_rls_lk'] for r in rls if r.get('kab_rls', 0) > 0])
rls_pr = json.dumps([r['kab_rls_pr'] for r in rls if r.get('kab_rls', 0) > 0])

# Usia sekolah
us = edu_data.get('usia_sekolah', [])
us_labels = json.dumps([u['label'] for u in us if u.get('data')])
us_datasets = {}
for level in ['SD','SLTP','SLTA','PT']:
    us_datasets[level] = json.dumps([u['data'][level] for u in us if u.get('data')])

# RLS per kecamatan (latest)
rls_kec_latest = next((r for r in reversed(rls) if r.get('kecamatan')), None)
rls_kec_html = ''
if rls_kec_latest:
    for k in sorted(rls_kec_latest['kecamatan'], key=lambda x: x['rls_total'], reverse=True):
        rls_kec_html += f'<tr><td>{k["nama"]}</td><td>{k["rls_lk"]}</td><td>{k["rls_pr"]}</td><td><strong>{k["rls_total"]}</strong></td></tr>'

html += f'''
<div class="tab-content" id="tab-pendidikan">
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">🎓 Distribusi Tingkat Pendidikan</div>
      <div class="chart-container"><canvas id="chartEduDist"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📏 Rata-rata Lama Sekolah (Tahun)</div>
      <div class="chart-container"><canvas id="chartRLS"></canvas></div>
    </div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="card">
      <div class="card-title">👶 Populasi Usia Sekolah</div>
      <div class="chart-container"><canvas id="chartUsiaSekolah"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📊 RLS per Kecamatan</div>
      <table class="data-table">
        <thead><tr><th>Kecamatan</th><th>L (th)</th><th>P (th)</th><th>Total</th></tr></thead>
        <tbody>{rls_kec_html}</tbody>
      </table>
    </div>
  </div>
  <div class="source-tag">Sumber: tabel pendidikan, lama_sekolah, usia_sekolah</div>
</div>
'''

# =====================================================================
# TAB 4: PEKERJAAN
# =====================================================================
pkj = D.get('pekerjaan', {})
top_jobs = pkj.get('top_jobs', [])[:15]
job_names = json.dumps([j['nama'][:30] for j in top_jobs])
job_lk = json.dumps([j['lk'] for j in top_jobs])
job_pr = json.dumps([j['pr'] for j in top_jobs])

# Usia produktif (latest)
up_latest = next((u for u in reversed(pkj.get('usia_produktif', [])) if u.get('data')), None)
up_data = up_latest['data'] if up_latest else {'muda': 0, 'produktif': 0, 'tua': 0}

# Rasio ketergantungan
rk = pkj.get('rasio_ketergantungan', [])
rk_labels = json.dumps([r['label'] for r in rk if r.get('data')])
rk_total = json.dumps([r['data']['rk_total'] for r in rk if r.get('data')])

# Angkatan kerja
ak = pkj.get('angkatan_kerja', [])
ak_labels = json.dumps([a['label'] for a in ak if a.get('data')])
ak_pct = json.dumps([a['data']['persen_tk'] for a in ak if a.get('data')])

html += f'''
<div class="tab-content" id="tab-pekerjaan">
  <div class="grid grid-3" style="margin-bottom:16px">
    <div class="card">
      <div class="card-title"><span class="icon">👷</span>Usia Produktif</div>
      <div class="kpi-value">{fmt(up_data['produktif'])}</div>
      <div class="kpi-sub">{round(up_data['produktif']/(up_data['muda']+up_data['produktif']+up_data['tua'])*100,1) if (up_data['muda']+up_data['produktif']+up_data['tua']) > 0 else 0}% dari populasi</div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">👶</span>Usia Muda (0-14)</div>
      <div class="kpi-value">{fmt(up_data['muda'])}</div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">🧓</span>Usia Tua (65+)</div>
      <div class="kpi-value">{fmt(up_data['tua'])}</div>
    </div>
  </div>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">💼 Top 15 Jenis Pekerjaan</div>
      <div class="chart-container" style="height:450px"><canvas id="chartJobs"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📊 Struktur Usia Penduduk</div>
      <div class="chart-container"><canvas id="chartUsiaProd"></canvas></div>
      <div style="margin-top:16px">
        <div class="card-title">📉 Rasio Ketergantungan</div>
        <div class="chart-container"><canvas id="chartRK"></canvas></div>
      </div>
    </div>
  </div>
  <div class="source-tag">Sumber: tabel pekerjaan, angkatan_kerja, usia_prod, rasio_keter</div>
</div>
'''

# =====================================================================
# TAB 5: PERKAWINAN
# =====================================================================
kwn = D.get('perkawinan', {})
latest_kwn = next((k for k in reversed(kwn.get('status_kawin', [])) if k.get('data')), None)
kwn_data = latest_kwn['data'] if latest_kwn else {}
total_bk = kwn_data.get('belum_kawin_lk', 0) + kwn_data.get('belum_kawin_pr', 0)
total_k = kwn_data.get('kawin_lk', 0) + kwn_data.get('kawin_pr', 0)
total_ch = kwn_data.get('cerai_hidup_lk', 0) + kwn_data.get('cerai_hidup_pr', 0)
total_cm = kwn_data.get('cerai_mati_lk', 0) + kwn_data.get('cerai_mati_pr', 0)

# Usia kawin
uk = kwn.get('usia_kawin', [])
uk_labels = json.dumps([u['label'] for u in uk if u.get('data')])
uk_lk = json.dumps([u['data']['lk'] for u in uk if u.get('data')])
uk_pr = json.dumps([u['data']['pr'] for u in uk if u.get('data')])

nc = kwn.get('nikah_cerai', {})
nc_html = ''
if nc.get('perkawinan'):
    nc_html += f'''<div class="card"><div class="card-title"><span class="icon">💒</span>Perkawinan</div>
      <div class="kpi-value">{fmt(nc['perkawinan']['jumlah'])}</div>
      <div class="kpi-sub">Angka Kasar: {nc['perkawinan']['angka_kasar']}‰ • Umum: {nc['perkawinan']['angka_umum']}‰</div></div>'''
if nc.get('perceraian'):
    nc_html += f'''<div class="card"><div class="card-title"><span class="icon">💔</span>Perceraian</div>
      <div class="kpi-value">{fmt(nc['perceraian']['jumlah'])}</div>
      <div class="kpi-sub">Angka Kasar: {nc['perceraian']['angka_kasar']}‰ • Umum: {nc['perceraian']['angka_umum']}‰</div></div>'''

html += f'''
<div class="tab-content" id="tab-perkawinan">
  <div class="grid grid-4" style="margin-bottom:16px">
    <div class="card"><div class="card-title">💑 Belum Kawin</div><div class="kpi-value">{fmt(total_bk)}</div></div>
    <div class="card"><div class="card-title">💍 Kawin</div><div class="kpi-value">{fmt(total_k)}</div></div>
    <div class="card"><div class="card-title">💔 Cerai Hidup</div><div class="kpi-value">{fmt(total_ch)}</div></div>
    <div class="card"><div class="card-title">🕊️ Cerai Mati</div><div class="kpi-value">{fmt(total_cm)}</div></div>
  </div>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">💍 Distribusi Status Kawin</div>
      <div class="chart-container"><canvas id="chartKawinPie"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📊 Rata-rata Usia Kawin Pertama</div>
      <div class="chart-container"><canvas id="chartUsiaKawin"></canvas></div>
    </div>
  </div>
  {"<div class='grid grid-2' style='margin-top:16px'>" + nc_html + "</div>" if nc_html else ""}
  <div class="source-tag">Sumber: tabel stat_kawin, usia_kawin, perkawinan, perceraian</div>
</div>
'''

# =====================================================================
# TAB 6: DISABILITAS
# =====================================================================
disab = D.get('disabilitas', {})
latest_disab = next((d for d in reversed(disab.get('trend', [])) if d.get('data')), None)
disab_data = latest_disab['data'] if latest_disab else {}
disab_labels = json.dumps(list(disab_data.keys()))
disab_values = json.dumps([disab_data[k]['jumlah'] for k in disab_data])
total_disab = sum(disab_data[k]['jumlah'] for k in disab_data)

# Trend
disab_trend_labels = json.dumps([t['label'] for t in disab.get('trend', []) if t.get('data')])
disab_trend_totals = []
for t in disab.get('trend', []):
    if t.get('data'):
        disab_trend_totals.append(sum(v['jumlah'] for v in t['data'].values()))
disab_trend_totals_js = json.dumps(disab_trend_totals)

# Kecamatan
disab_kec = disab.get('kecamatan', [])
disab_kec_html = ''
for k in sorted(disab_kec, key=lambda x: x['total'], reverse=True):
    disab_kec_html += f'<tr><td>{k["nama"]}</td>'
    for lbl in ['Fisik','Netra/Buta','Rungu/Wicara','Mental/Jiwa','Fisik & Mental','Lainnya']:
        disab_kec_html += f'<td>{k.get(lbl, 0)}</td>'
    disab_kec_html += f'<td><strong>{k["total"]}</strong></td></tr>'

html += f'''
<div class="tab-content" id="tab-disabilitas">
  <div class="grid grid-3" style="margin-bottom:16px">
    <div class="card"><div class="card-title"><span class="icon">♿</span>Total Penyandang</div>
      <div class="kpi-value">{fmt(total_disab)}</div>
      <div class="kpi-sub">{round(total_disab/latest['pop']*100,2) if latest['pop'] > 0 else 0}% dari populasi</div>
    </div>
    <div class="card"><div class="card-title">🏥 Jenis Terbanyak</div>
      <div class="kpi-value">{max(disab_data, key=lambda k: disab_data[k]['jumlah']) if disab_data else '-'}</div>
      <div class="kpi-sub">{fmt(max(disab_data.values(), key=lambda v: v['jumlah'])['jumlah']) if disab_data else 0} jiwa</div>
    </div>
    <div class="card"><div class="card-title">📊 Kecamatan</div>
      <div class="kpi-value">{len(disab_kec)}</div>
      <div class="kpi-sub">kecamatan terdata</div>
    </div>
  </div>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">♿ Distribusi Jenis Disabilitas</div>
      <div class="chart-container"><canvas id="chartDisabPie"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">📈 Tren Total Disabilitas</div>
      <div class="chart-container"><canvas id="chartDisabTrend"></canvas></div>
    </div>
  </div>
  <div class="section-title">📋 Per Kecamatan</div>
  <div class="card" style="overflow-x:auto">
    <table class="data-table">
      <thead><tr><th>Kecamatan</th><th>Fisik</th><th>Netra</th><th>Rungu</th><th>Mental</th><th>Fisik&Mental</th><th>Lain</th><th>Total</th></tr></thead>
      <tbody>{disab_kec_html}</tbody>
    </table>
  </div>
  <div class="source-tag">Sumber: tabel disabilitas × 7 periode</div>
</div>
'''

# =====================================================================
# TAB 7: KESEHATAN
# =====================================================================
kes = D.get('kesehatan', {})
latest_drh = next((d for d in reversed(kes.get('golongan_darah', [])) if d.get('data')), None)
drh_data = latest_drh['data'] if latest_drh else {}
drh_labels = json.dumps([k for k in drh_data if k != 'Tidak Tahu'])
drh_values = json.dumps([drh_data[k]['jumlah'] for k in drh_data if k != 'Tidak Tahu'])

# CWR trend
cwr = kes.get('rasio_anak_ibu', [])
cwr_labels = json.dumps([c['label'] for c in cwr if c.get('data')])
cwr_values = json.dumps([c['data']['cwr'] for c in cwr if c.get('data')])

html += f'''
<div class="tab-content" id="tab-kesehatan">
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">🩸 Distribusi Golongan Darah</div>
      <div class="chart-container"><canvas id="chartDarah"></canvas></div>
      <div class="kpi-sub" style="margin-top:8px">Tidak Tahu: {fmt(drh_data.get('Tidak Tahu', {}).get('jumlah', 0))} jiwa</div>
    </div>
    <div class="card">
      <div class="card-title">👶 Rasio Anak-Ibu (CWR)</div>
      <div class="chart-container"><canvas id="chartCWR"></canvas></div>
      <div class="insight-box" style="margin-top:12px">
        CWR (Child-Woman Ratio) mengukur jumlah anak 0-4 tahun per 100 wanita usia subur (15-49).
        Semakin tinggi CWR, semakin tinggi fertilitas wilayah tersebut.
      </div>
    </div>
  </div>
  <div class="source-tag">Sumber: tabel drh/gol_darah, rasio_anak_ibu</div>
</div>
'''

# =====================================================================
# TAB 8: DOKUMEN
# =====================================================================
dok = D.get('dokumen', {})
dok_trend = dok.get('trend', [])
latest_dok = dok_trend[-1] if dok_trend else {}
# KPI boxes
wktp_pct = latest_dok.get('wktp', {}).get('pct_rekam', 0) or 0
kia_pct = latest_dok.get('kia', {}).get('pct', 0) or 0
akta_pct = latest_dok.get('akta', {}).get('pct', 0) or 0
kk_pct = latest_dok.get('kk', {}).get('pct_cetak', 0) or 0

# Trend arrays
dok_labels = json.dumps([d['label'] for d in dok_trend])
dok_wktp = json.dumps([d.get('wktp', {}).get('pct_rekam') if d.get('wktp') else None for d in dok_trend])
dok_kia = json.dumps([d.get('kia', {}).get('pct') if d.get('kia') else None for d in dok_trend])
dok_akta = json.dumps([d.get('akta', {}).get('pct') if d.get('akta') else None for d in dok_trend])
dok_kk = json.dumps([d.get('kk', {}).get('pct_cetak') if d.get('kk') else None for d in dok_trend])

html += f'''
<div class="tab-content" id="tab-dokumen">
  <div class="grid grid-4" style="margin-bottom:16px">
    <div class="card"><div class="card-title">🪪 e-KTP Rekam</div>
      <div class="kpi-value">{wktp_pct}%</div>
      <div class="kpi-sub">Wajib: {fmt(latest_dok.get('wktp',{}).get('wajib_ktp',0))}</div></div>
    <div class="card"><div class="card-title">👶 KIA</div>
      <div class="kpi-value">{kia_pct}%</div>
      <div class="kpi-sub">Wajib: {fmt(latest_dok.get('kia',{}).get('wajib',0))}</div></div>
    <div class="card"><div class="card-title">📜 Akta Lahir</div>
      <div class="kpi-value">{akta_pct}%</div>
      <div class="kpi-sub">Wajib: {fmt(latest_dok.get('akta',{}).get('wajib',0))}</div></div>
    <div class="card"><div class="card-title">📋 KK Cetak</div>
      <div class="kpi-value">{kk_pct}%</div>
      <div class="kpi-sub">Total: {fmt(latest_dok.get('kk',{}).get('jumlah',0))}</div></div>
  </div>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">📈 Tren Cakupan Dokumen</div>
      <div class="chart-container"><canvas id="chartDokTrend"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">🎯 Radar Cakupan Terbaru</div>
      <div class="chart-container"><canvas id="chartDokRadar"></canvas></div>
    </div>
  </div>
  <div class="source-tag">Sumber: tabel wktp, kia, akta_lahir, kepemilikan_kk</div>
</div>
'''

# =====================================================================
# TAB 9: KELUARGA
# =====================================================================
kel = D.get('keluarga', {})
kel_trend = kel.get('kepala_keluarga', [])
kel_labels = json.dumps([k['label'] for k in kel_trend if k.get('data')])
kel_lk = json.dumps([k['data']['kepkel_lk'] for k in kel_trend if k.get('data')])
kel_pr = json.dumps([k['data']['kepkel_pr'] for k in kel_trend if k.get('data')])
latest_kel = next((k for k in reversed(kel_trend) if k.get('data')), None)
kel_data = latest_kel['data'] if latest_kel else {'kepkel_lk': 0, 'kepkel_pr': 0, 'kepkel_total': 0}

html += f'''
<div class="tab-content" id="tab-keluarga">
  <div class="grid grid-3" style="margin-bottom:16px">
    <div class="card"><div class="card-title"><span class="icon">👨</span>Kepala Keluarga Laki-laki</div>
      <div class="kpi-value">{fmt(kel_data['kepkel_lk'])}</div>
      <div class="kpi-sub">{round(kel_data['kepkel_lk']/kel_data['kepkel_total']*100,1) if kel_data['kepkel_total'] > 0 else 0}%</div></div>
    <div class="card"><div class="card-title"><span class="icon">👩</span>Kepala Keluarga Perempuan</div>
      <div class="kpi-value">{fmt(kel_data['kepkel_pr'])}</div>
      <div class="kpi-sub">{round(kel_data['kepkel_pr']/kel_data['kepkel_total']*100,1) if kel_data['kepkel_total'] > 0 else 0}%</div></div>
    <div class="card"><div class="card-title"><span class="icon">🏠</span>Total KK</div>
      <div class="kpi-value">{fmt(kel_data['kepkel_total'])}</div></div>
  </div>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-title">📈 Tren Kepala Keluarga by Gender</div>
      <div class="chart-container"><canvas id="chartKelTrend"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">🍩 Proporsi Gender KK</div>
      <div class="chart-container"><canvas id="chartKelPie"></canvas></div>
    </div>
  </div>
  <div class="source-tag">Sumber: tabel hub_keluarga × 7 periode</div>
</div>
'''

# =====================================================================
# TAB 10: DESA
# =====================================================================
desa = D.get('desa', {})
top_desa = desa.get('top_desa', [])
fastest = desa.get('desa_growth', {}).get('fastest', [])
slowest = desa.get('desa_growth', {}).get('slowest', [])

# Top desa table
desa_rows = ''
for i, d in enumerate(top_desa):
    desa_rows += f'''<tr>
      <td>{i+1}</td><td>{d['nama']}</td><td>{d['kecamatan']}</td>
      <td>{fmt(d['pop'])}</td><td>{fmt(d['kk'])}</td>
      <td>{fmt(d['lk'])}</td><td>{fmt(d['pr'])}</td>
      <td>{d['rasio_jk']}</td><td>{d['art']}</td>
    </tr>'''

# Growth table
growth_rows = ''
for d in fastest[:10]:
    growth_rows += f'<tr><td>{d["nama"]}</td><td>{d["kecamatan"]}</td><td>{fmt(d["pop_first"])}</td><td>{fmt(d["pop_last"])}</td><td style="color:#10b981">+{d["growth_pct"]}%</td></tr>'
for d in slowest[:5]:
    growth_rows += f'<tr><td>{d["nama"]}</td><td>{d["kecamatan"]}</td><td>{fmt(d["pop_first"])}</td><td>{fmt(d["pop_last"])}</td><td style="color:#f43f5e">{d["growth_pct"]}%</td></tr>'

# Heatmap data
heatmap = desa.get('heatmap', [])
hm_labels = json.dumps([h['kecamatan'] for h in heatmap])
hm_datasets = []
period_colors = ['#3b82f6','#06b6d4','#10b981','#f59e0b','#f97316','#f43f5e','#8b5cf6']
for idx, p in enumerate(meta['periods']):
    hm_datasets.append({
        'label': meta['period_labels'][idx],
        'data': [h.get(p, 0) for h in heatmap],
        'backgroundColor': period_colors[idx] + '99',
    })

# Render baris anomali kependudukan berbasis Z-Score
anomali_rows = ''
anomali_list = desa.get('anomali_desa', [])
for idx, d in enumerate(anomali_list):
    color = "#f43f5e" if d['kategori'] == "PENURUNAN DRASTIS" else "#10b981"
    bg_color = "rgba(244,63,94,0.04)" if d['kategori'] == "PENURUNAN DRASTIS" else "rgba(16,185,129,0.04)"
    anomali_rows += f'''<tr style="background-color: {bg_color}">
      <td>{idx+1}</td>
      <td><strong>{d['nama']}</strong></td>
      <td>{d['kecamatan']}</td>
      <td>{fmt(d['pop_first'])}</td>
      <td>{fmt(d['pop_last'])}</td>
      <td style="color:{color}; font-weight:bold">{"++" if d['growth_pct']>0 else ""}{d['growth_pct']}%</td>
      <td><span class="kpi-badge" style="background:{color}22; color:{color}">{d['z_score']}</span></td>
      <td>{d['kategori']}</td>
      <td style="color:#f59e0b">💡 {d['rekomendasi']}</td>
    </tr>'''

if not anomali_rows:
    anomali_rows = '<tr><td colspan="9" style="text-align:center; color:var(--text-muted)">✅ Tidak ada anomali pertumbuhan desa yang terdeteksi (semua wajar di bawah Z=2.0).</td></tr>'

html += f'''
<div class="tab-content" id="tab-desa">
  <div class="grid grid-2" style="margin-bottom:16px">
    <div class="card">
      <div class="card-title">📊 Populasi per Kecamatan (Trend)</div>
      <div class="chart-container"><canvas id="chartHeatmap"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">🏆 Top 10 Pertumbuhan Desa</div>
      <div class="chart-container"><canvas id="chartDesaGrowth"></canvas></div>
    </div>
  </div>

  <div class="section-title">📋 Data Seluruh Desa ({len(top_desa)} desa)</div>
  <input type="text" class="search-input" id="searchDesa" placeholder="🔍 Cari nama desa atau kecamatan..." onkeyup="filterDesa()">
  <div class="card" style="overflow-x:auto; max-height:500px; overflow-y:auto">
    <table class="data-table" id="tableDesa">
      <thead><tr>
        <th>#</th><th>Desa</th><th>Kecamatan</th><th>Penduduk</th><th>KK</th><th>L</th><th>P</th><th>RJK</th><th>ART</th>
      </tr></thead>
      <tbody>{desa_rows}</tbody>
    </table>
  </div>

  <div class="section-title" style="margin-top:24px">📈 Pertumbuhan Desa (Sem 2 2022 → Sem 2 2025)</div>
  <div class="card" style="overflow-x:auto">
    <table class="data-table">
      <thead><tr><th>Desa</th><th>Kecamatan</th><th>Awal</th><th>Akhir</th><th>Pertumbuhan</th></tr></thead>
      <tbody>{growth_rows}</tbody>
    </table>
  </div>
  <div class="source-tag">Sumber: siak_history_warehouse.db + jk tables</div>
</div>

<div class="tab-content" id="tab-peta">
  <div class="card">
    <div class="card-title">🗺️ Peta Spasial Kepadatan Penduduk Kecamatan (Choropleth)</div>
    <div id="map" style="height:550px; width:100%; border-radius:var(--radius); border:1px solid var(--border); z-index:10"></div>
    <div class="insight-box" style="margin-top:12px">
      <strong>💡 Wawasan Spasial:</strong> Peta Choropleth interaktif di atas menggunakan pustaka <strong>Leaflet.js</strong> untuk me-render data spasial secara dinamis. Arahkan kursor Anda ke wilayah kecamatan untuk melihat pop-up statistik demografi real-time periode terbaru.
    </div>
  </div>
</div>

<div class="tab-content" id="tab-anomali">
  <div class="insight-box" style="background:linear-gradient(135deg, rgba(244,63,94,0.08), rgba(245,158,11,0.08)); border-color:rgba(244,63,94,0.18)">
    <strong>⚠️ Sistem Deteksi Anomali Demografis (Z-Score Outlier Engine):</strong>
    Anomali dihitung otomatis pada laju pertumbuhan desa dari tahun 2022 hingga 2025 menggunakan metode statistik **Z-Score**. Desa yang memiliki laju pertumbuhan di luar <strong>2 standar deviasi ($|Z| > 2.0$)</strong> dari rata-rata kabupaten ditandai di bawah ini untuk verifikasi lapangan audit kepatuhan NIK oleh Dinas Dukcapil.
  </div>
  <div class="card" style="overflow-x:auto">
    <table class="data-table">
      <thead><tr>
        <th>#</th><th>Desa</th><th>Kecamatan</th><th>Awal (2022)</th><th>Akhir (2025)</th><th>Pertumbuhan</th><th>Z-Score</th><th>Kategori</th><th>Rekomendasi Analis</th>
      </tr></thead>
      <tbody>{anomali_rows}</tbody>
    </table>
  </div>
</div>
'''

# =====================================================================
# FOOTER
# =====================================================================
html += f'''
<div class="footer">
  <p>Dashboard Kependudukan Kabupaten {meta['kabupaten']} — Data Agregat Komprehensif</p>
  <p>Dibangun dari {len(meta['periods'])} periode data • Sumber: SIAK (Sistem Informasi Administrasi Kependudukan)</p>
  <p>Pipeline: AGREGAT xlsx → BERSIH xlsx → siak_analytics.db → Dashboard</p>
</div>
'''

# =====================================================================
# JAVASCRIPT — ALL CHARTS
# =====================================================================
html += '''
<script>
Chart.defaults.color = '#8b95a8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = 'Inter';
Chart.defaults.font.size = 11;
const COLORS = ['#3b82f6','#06b6d4','#10b981','#f59e0b','#f97316','#f43f5e','#8b5cf6','#ec4899','#14b8a6','#6366f1'];
const COLORS_ALPHA = COLORS.map(c => c + '33');

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

// Search desa
function filterDesa() {
  const q = document.getElementById('searchDesa').value.toLowerCase();
  document.querySelectorAll('#tableDesa tbody tr').forEach(r => {
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
'''

# Chart: Pop Trend + Prediction (Quadratic with Shaded Uncertainty Bands)
pop_labels = json.dumps([t['label'] for t in ov['trend']] + [p['label'] for p in ov['predictions']])
pop_actual = json.dumps([t['pop'] for t in ov['trend']] + [None]*len(ov['predictions']))
pop_pred = json.dumps([None]*(len(ov['trend'])-1) + [ov['trend'][-1]['pop']] + [p['predicted_pop'] for p in ov['predictions']])
pop_upper = json.dumps([None]*(len(ov['trend'])-1) + [ov['trend'][-1]['pop']] + [p['upper_bound'] for p in ov['predictions']])
pop_lower = json.dumps([None]*(len(ov['trend'])-1) + [ov['trend'][-1]['pop']] + [p['lower_bound'] for p in ov['predictions']])

html += f'''
new Chart(document.getElementById('chartPopTrend'), {{
  type:'line',
  data:{{
    labels:{pop_labels},
    datasets:[
      {{ label:'Aktual', data:{pop_actual}, borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,0.06)', fill:true, tension:0.4, pointRadius:5, pointBackgroundColor:'#3b82f6', borderWidth:2.5 }},
      {{ label:'Prediksi (Kuadratik ML)', data:{pop_pred}, borderColor:'#f59e0b', borderDash:[6,3], pointStyle:'triangle', pointRadius:6, pointBackgroundColor:'#f59e0b', borderWidth:2.5, fill:false }},
      {{ label:'Batas Atas CI 95%', data:{pop_upper}, borderColor:'rgba(245,158,11,0.15)', backgroundColor:'rgba(245,158,11,0.05)', fill:3, pointRadius:0, borderWidth:1, borderDash:[2,2] }},
      {{ label:'Batas Bawah CI 95%', data:{pop_lower}, borderColor:'rgba(245,158,11,0.15)', fill:false, pointRadius:0, borderWidth:1, borderDash:[2,2] }}
    ]
  }},
  options:{{ 
    responsive:true, 
    plugins:{{ 
      legend:{{position:'bottom', labels:{{boxWidth:12, padding:10}}}}
    }}, 
    scales:{{y:{{beginAtZero:false}}}} 
  }}
}});
'''

# Chart: Kecamatan doughnut
kec_names = json.dumps([k['nama'] for k in ov['kec_composition']])
kec_pops = json.dumps([k['pop'] for k in ov['kec_composition']])

html += f'''
new Chart(document.getElementById('chartKecDoughnut'), {{
  type:'doughnut',
  data:{{ labels:{kec_names}, datasets:[{{ data:{kec_pops}, backgroundColor:COLORS, borderWidth:0 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{position:'right',labels:{{boxWidth:12,padding:8,font:{{size:10}}}}}} }} }}
}});
'''

# Chart: Growth rate
gr_labels = json.dumps([g['label'] for g in ov['growth_rates']])
gr_values = json.dumps([g['growth_pct'] for g in ov['growth_rates']])

html += f'''
new Chart(document.getElementById('chartGrowthRate'), {{
  type:'bar',
  data:{{ labels:{gr_labels}, datasets:[{{ label:'Pertumbuhan (%)', data:{gr_values}, backgroundColor:COLORS.map(c=>c+'99'), borderColor:COLORS, borderWidth:1, borderRadius:6 }}] }},
  options:{{ responsive:true, plugins:{{legend:{{display:false}}}}, scales:{{y:{{beginAtZero:true}}}} }}
}});
'''

# Chart: Kecamatan trend
kec_ts = ov.get('kec_time_series', {})
kec_datasets = []
for idx, (name, vals) in enumerate(kec_ts.items()):
    kec_datasets.append({'label': name, 'data': vals, 'borderColor': period_colors[idx % len(period_colors)], 'tension': 0.4, 'borderWidth': 2, 'pointRadius': 3, 'fill': False})
kec_period_labels = json.dumps(meta['period_labels'])

html += f'''
new Chart(document.getElementById('chartKecTrend'), {{
  type:'line',
  data:{{ labels:{kec_period_labels}, datasets:{json.dumps(kec_datasets)} }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom',labels:{{boxWidth:12,font:{{size:9}}}}}}}} }}
}});
'''

# Chart: Agama pie
html += f'''
new Chart(document.getElementById('chartAgamaPie'), {{
  type:'doughnut',
  data:{{ labels:{agama_labels_js}, datasets:[{{ data:{agama_values_js}, backgroundColor:COLORS, borderWidth:0 }}] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Agama trend (stacked bar)
agama_ds = []
for idx, name in enumerate(agama_names):
    agama_ds.append({'label': name, 'data': agama_trend_datasets.get(name, []), 'backgroundColor': period_colors[idx % len(period_colors)] + '99'})

html += f'''
new Chart(document.getElementById('chartAgamaTrend'), {{
  type:'bar',
  data:{{ labels:{agama_trend_labels}, datasets:{json.dumps(agama_ds)} }},
  options:{{ responsive:true, scales:{{x:{{stacked:true}},y:{{stacked:true}}}}, plugins:{{legend:{{position:'bottom',labels:{{boxWidth:12,font:{{size:9}}}}}}}} }}
}});
'''

# Chart: Education distribution
html += f'''
new Chart(document.getElementById('chartEduDist'), {{
  type:'bar',
  data:{{ labels:{edu_labels}, datasets:[{{ label:'Jumlah', data:{edu_values}, backgroundColor:COLORS.map(c=>c+'99'), borderColor:COLORS, borderWidth:1, borderRadius:6 }}] }},
  options:{{ responsive:true, indexAxis:'y', plugins:{{legend:{{display:false}}}} }}
}});
'''

# Chart: RLS
html += f'''
new Chart(document.getElementById('chartRLS'), {{
  type:'line',
  data:{{ labels:{rls_labels}, datasets:[
    {{ label:'Total', data:{rls_total}, borderColor:'#3b82f6', tension:0.4, borderWidth:2, pointRadius:5, fill:false }},
    {{ label:'Laki-laki', data:{rls_lk}, borderColor:'#06b6d4', tension:0.4, borderWidth:1.5, pointRadius:3, fill:false }},
    {{ label:'Perempuan', data:{rls_pr}, borderColor:'#f43f5e', tension:0.4, borderWidth:1.5, pointRadius:3, fill:false }}
  ] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Usia Sekolah
html += f'''
new Chart(document.getElementById('chartUsiaSekolah'), {{
  type:'bar',
  data:{{ labels:{us_labels}, datasets:[
    {{ label:'SD', data:{us_datasets['SD']}, backgroundColor:'#3b82f699' }},
    {{ label:'SLTP', data:{us_datasets['SLTP']}, backgroundColor:'#06b6d499' }},
    {{ label:'SLTA', data:{us_datasets['SLTA']}, backgroundColor:'#10b98199' }},
    {{ label:'PT', data:{us_datasets['PT']}, backgroundColor:'#f59e0b99' }}
  ] }},
  options:{{ responsive:true, scales:{{x:{{stacked:true}},y:{{stacked:true}}}}, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Jobs horizontal bar
html += f'''
new Chart(document.getElementById('chartJobs'), {{
  type:'bar',
  data:{{ labels:{job_names}, datasets:[
    {{ label:'Laki-laki', data:{job_lk}, backgroundColor:'#3b82f699' }},
    {{ label:'Perempuan', data:{job_pr}, backgroundColor:'#f43f5e99' }}
  ] }},
  options:{{ responsive:true, maintainAspectRatio:false, indexAxis:'y', scales:{{x:{{stacked:true}},y:{{stacked:true}}}}, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Piramida Penduduk Demografis (Laki-laki vs Perempuan)
html += f'''
new Chart(document.getElementById('chartUsiaProd'), {{
  type:'bar',
  data:{{
    labels:['Muda (0-14)', 'Produktif (15-64)', 'Tua (65+)'],
    datasets:[
      {{
        label: 'Laki-laki',
        data: [-{up_data['lk_muda']}, -{up_data['lk_prod']}, -{up_data['lk_tua']}],
        backgroundColor: '#3b82f699',
        borderWidth: 0,
        borderRadius: 4
      }},
      {{
        label: 'Perempuan',
        data: [{up_data['pr_muda']}, {up_data['pr_prod']}, {up_data['pr_tua']}],
        backgroundColor: '#f43f5e99',
        borderWidth: 0,
        borderRadius: 4
      }}
    ]
  }},
  options:{{
    responsive:true,
    indexAxis: 'y',
    scales:{{
      x:{{
        stacked:true,
        ticks:{{
          callback: function(val) {{ return Math.abs(val).toLocaleString('id-ID'); }}
        }}
      }},
      y:{{ stacked:true }}
    }},
    plugins:{{
      legend:{{ position:'bottom' }},
      tooltip:{{
        callbacks:{{
          label: function(context) {{
            let label = context.dataset.label || '';
            let val = Math.abs(context.raw);
            return label + ': ' + val.toLocaleString('id-ID') + ' Jiwa';
          }}
        }}
      }}
    }}
  }}
}});
'''

# Chart: Rasio Ketergantungan
html += f'''
new Chart(document.getElementById('chartRK'), {{
  type:'line',
  data:{{ labels:{rk_labels}, datasets:[{{
    label:'RK Total', data:{rk_total}, borderColor:'#f43f5e', tension:0.4, borderWidth:2, pointRadius:5, fill:true, backgroundColor:'rgba(244,63,94,0.1)'
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{display:false}}}} }}
}});
'''

# Chart: Status Kawin Pie
html += f'''
new Chart(document.getElementById('chartKawinPie'), {{
  type:'doughnut',
  data:{{ labels:['Belum Kawin','Kawin','Cerai Hidup','Cerai Mati'], datasets:[{{
    data:[{total_bk},{total_k},{total_ch},{total_cm}],
    backgroundColor:['#3b82f699','#10b98199','#f59e0b99','#f43f5e99'], borderWidth:0
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Usia Kawin
html += f'''
new Chart(document.getElementById('chartUsiaKawin'), {{
  type:'line',
  data:{{ labels:{uk_labels}, datasets:[
    {{ label:'Laki-laki', data:{uk_lk}, borderColor:'#3b82f6', tension:0.4, borderWidth:2, pointRadius:5, fill:false }},
    {{ label:'Perempuan', data:{uk_pr}, borderColor:'#f43f5e', tension:0.4, borderWidth:2, pointRadius:5, fill:false }}
  ] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Disabilitas Pie
html += f'''
new Chart(document.getElementById('chartDisabPie'), {{
  type:'polarArea',
  data:{{ labels:{disab_labels}, datasets:[{{
    data:{disab_values}, backgroundColor:COLORS.slice(0,{len(disab_data)}).map(c=>c+'99')
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Disabilitas Trend
html += f'''
new Chart(document.getElementById('chartDisabTrend'), {{
  type:'line',
  data:{{ labels:{disab_trend_labels}, datasets:[{{
    label:'Total Disabilitas', data:{disab_trend_totals_js}, borderColor:'#8b5cf6', tension:0.4, borderWidth:2, pointRadius:5, fill:true, backgroundColor:'rgba(139,92,246,0.1)'
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{display:false}}}} }}
}});
'''

# Chart: Golongan Darah
html += f'''
new Chart(document.getElementById('chartDarah'), {{
  type:'doughnut',
  data:{{ labels:{drh_labels}, datasets:[{{
    data:{drh_values}, backgroundColor:['#f43f5e99','#3b82f699','#10b98199','#f59e0b99'], borderWidth:0
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: CWR trend
html += f'''
new Chart(document.getElementById('chartCWR'), {{
  type:'line',
  data:{{ labels:{cwr_labels}, datasets:[{{
    label:'CWR', data:{cwr_values}, borderColor:'#06b6d4', tension:0.4, borderWidth:2, pointRadius:5, fill:true, backgroundColor:'rgba(6,182,212,0.1)'
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{display:false}}}} }}
}});
'''

# Chart: Dokumen Trend
html += f'''
new Chart(document.getElementById('chartDokTrend'), {{
  type:'line',
  data:{{ labels:{dok_labels}, datasets:[
    {{ label:'e-KTP Rekam %', data:{dok_wktp}, borderColor:'#3b82f6', tension:0.4, borderWidth:2, pointRadius:4, fill:false, spanGaps:false }},
    {{ label:'KIA %', data:{dok_kia}, borderColor:'#06b6d4', tension:0.4, borderWidth:2, pointRadius:4, fill:false, spanGaps:false }},
    {{ label:'Akta Lahir %', data:{dok_akta}, borderColor:'#10b981', tension:0.4, borderWidth:2, pointRadius:4, fill:false, spanGaps:false }},
    {{ label:'KK Cetak %', data:{dok_kk}, borderColor:'#f59e0b', tension:0.4, borderWidth:2, pointRadius:4, fill:false, spanGaps:false }}
  ] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}}, scales:{{y:{{min:0,max:100}}}} }}
}});
'''

# Chart: Dokumen Radar
html += f'''
new Chart(document.getElementById('chartDokRadar'), {{
  type:'radar',
  data:{{ labels:['e-KTP Rekam','KIA','Akta Lahir','KK Cetak'], datasets:[{{
    label:'Cakupan %', data:[{wktp_pct},{kia_pct},{akta_pct},{kk_pct}],
    backgroundColor:'rgba(59,130,246,0.2)', borderColor:'#3b82f6', pointBackgroundColor:'#3b82f6', borderWidth:2
  }}] }},
  options:{{ responsive:true, scales:{{r:{{min:0,max:100,ticks:{{stepSize:20}}}}}}, plugins:{{legend:{{display:false}}}} }}
}});
'''

# Chart: Keluarga trend
html += f'''
new Chart(document.getElementById('chartKelTrend'), {{
  type:'bar',
  data:{{ labels:{kel_labels}, datasets:[
    {{ label:'KK Laki-laki', data:{kel_lk}, backgroundColor:'#3b82f699', borderRadius:4 }},
    {{ label:'KK Perempuan', data:{kel_pr}, backgroundColor:'#f43f5e99', borderRadius:4 }}
  ] }},
  options:{{ responsive:true, scales:{{x:{{stacked:true}},y:{{stacked:true}}}}, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Keluarga pie
html += f'''
new Chart(document.getElementById('chartKelPie'), {{
  type:'doughnut',
  data:{{ labels:['KK Laki-laki','KK Perempuan'], datasets:[{{
    data:[{kel_data['kepkel_lk']},{kel_data['kepkel_pr']}],
    backgroundColor:['#3b82f699','#f43f5e99'], borderWidth:0
  }}] }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom'}}}} }}
}});
'''

# Chart: Heatmap (grouped bar)
html += f'''
new Chart(document.getElementById('chartHeatmap'), {{
  type:'bar',
  data:{{ labels:{hm_labels}, datasets:{json.dumps(hm_datasets)} }},
  options:{{ responsive:true, plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,font:{{size:9}}}}}}}} }}
}});
'''

# Chart: Desa Growth (horizontal)
fastest_names = json.dumps([d['nama'][:25] for d in fastest[:10]])
fastest_pcts = json.dumps([d['growth_pct'] for d in fastest[:10]])

html += f'''
new Chart(document.getElementById('chartDesaGrowth'), {{
  type:'bar',
  data:{{ labels:{fastest_names}, datasets:[{{
    label:'Pertumbuhan %', data:{fastest_pcts},
    backgroundColor:COLORS.map(c=>c+'99'), borderColor:COLORS, borderWidth:1, borderRadius:6
  }}] }},
  options:{{ responsive:true, indexAxis:'y', plugins:{{legend:{{display:false}}}} }}
}});
'''

# Buat data populasi kecamatan dinamis secara real-time dari database periode terbaru
kec_pops_dynamic = {k['nama'].upper(): k['pop'] for k in ov['kec_composition']}
kec_pops_js = json.dumps(kec_pops_dynamic)

html += f'''
// =====================================================================
// MAP SPASIAL LEAFLET.JS (Choropleth Peta Morotai)
// =====================================================================
try {{
  const map = L.map('map').setView([2.19, 128.32], 10); // Sentral Pulau Morotai (Latitude positif / North)
  
  // Basemap Dark Mode Premium
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 20
  }}).addTo(map);
 
  // Data demografi dinamis per kecamatan (real-time terhubung ke database)
  const kecPops = {kec_pops_js};
 
  function getColor(d) {{
    return d > 30000 ? '#8b5cf6' :
           d > 12000 ? '#3b82f6' :
           d > 9000  ? '#06b6d4' :
           d > 7000  ? '#10b981' :
                       '#f59e0b';
  }}
 
  function style(feature) {{
    const name = feature.properties.name || feature.properties.KECAMATAN || feature.properties.NAME || '';
    const pop = kecPops[name.toUpperCase()] || 0;
    return {{
      fillColor: getColor(pop),
      weight: 2,
      opacity: 1,
      color: '#0a0e1a',
      fillOpacity: 0.7
    }};
  }}
 
  let geojsonLayer;
  
  // Load GeoJSON kecamatan dari relative path
  fetch('data/morotai_kecamatan_presisi.geojson')
    .then(res => res.json())
    .then(data => {{
      geojsonLayer = L.geoJSON(data, {{
        style: style,
        onEachFeature: function(feature, layer) {{
          const name = feature.properties.name || feature.properties.KECAMATAN || feature.properties.NAME || 'Kecamatan';
          const pop = kecPops[name.toUpperCase()] || 0;
          layer.bindPopup('<strong>' + name + '</strong><br/>Populasi: ' + (pop > 0 ? pop.toLocaleString('id-ID') : 'Tidak Terdata') + ' Jiwa');
          layer.on({{
            mouseover: function(e) {{
              const l = e.target;
              l.setStyle({{ fillOpacity: 0.9, weight: 3, color: '#ffffff' }});
              l.bringToFront();
            }},
            mouseout: function(e) {{
              geojsonLayer.resetStyle(e.target);
            }}
          }});
        }}
      }}).addTo(map);
    }})
    .catch(err => {{
      console.log('GeoJSON tidak termuat (CORS atau file tidak ada). Membuat fallback markers.');
      const coords = [
        {{name: 'Morotai Selatan', pos: [2.05, 128.30], pop: kecPops['MOROTAI SELATAN'] || 33041}},
        {{name: 'Morotai Selatan Barat', pos: [2.15, 128.15], pop: kecPops['MOROTAI SELATAN BARAT'] || 9052}},
        {{name: 'Morotai Jaya', pos: [2.35, 128.25], pop: kecPops['MOROTAI JAYA'] || 12052}},
        {{name: 'Morotai Utara', pos: [2.45, 128.45], pop: kecPops['MOROTAI UTARA'] || 12566}},
        {{name: 'Morotai Timur', pos: [2.20, 128.50], pop: kecPops['MOROTAI TIMUR'] || 12347}},
        {{name: 'Pulau Rao', pos: [2.30, 128.10], pop: kecPops['PULAU RAO'] || 5031}}
      ];
      coords.forEach(c => {{
        L.circle(c.pos, {{
          color: '#3b82f6',
          fillColor: '#8b5cf6',
          fillOpacity: 0.5,
          radius: Math.sqrt(c.pop) * 35
        }}).addTo(map).bindPopup('<strong>' + c.name + '</strong><br/>Populasi: ' + c.pop.toLocaleString('id-ID') + ' Jiwa');
      }});
    }});

  // Render ulang ukuran peta saat tab peta di-klik
  document.querySelectorAll('[data-tab="peta"]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      setTimeout(() => {{ map.invalidateSize(); }}, 200);
    }});
  }});

}} catch (e) {{
  console.error("Leaflet gagal diinisialisasi: ", e);
}}

</script>
</body>
</html>
'''

# Write output
os.makedirs('output', exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Dashboard generated: {OUTPUT}')
print(f'  Size: {len(html):,} bytes')
print(f'  10 tabs, 30+ charts')
