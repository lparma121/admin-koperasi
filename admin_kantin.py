import streamlit as st
from supabase import create_client
import time
from PIL import Image
import io
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# ==============================================================================
# 1. KONFIGURASI & KONEKSI
# ==============================================================================
st.set_page_config(
    page_title="Panel Admin Kantin", 
    layout="wide", 
    page_icon="👮",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# --- CSS MODERN MENU & HIDE HEADER ---
sembunyikan_menu = """
<style>
/* --- 1. HILANGKAN HEADER & FOOTER BAWAAN --- */
header {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important;}
#manage-app-button {display: none !important;}

/* --- 2. SULAP RADIO BUTTON JADI MENU MODERN --- */
div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

div[role="radiogroup"] label {
    background-color: #f7f9fc;
    border: 1px solid #dcdede;
    padding: 10px 20px !important;
    border-radius: 50px !important;
    margin: 5px;
    transition: all 0.3s ease-in-out;
    cursor: pointer;
}

div[role="radiogroup"] label p {
    margin: 0 !important;
    font-weight: 600 !important;
    color: #555 !important;
    font-size: 14px;
}

div[role="radiogroup"] label:hover {
    background-color: #e3f2fd;
    border-color: #00AAFF;
    transform: translateY(-3px);
}

div[role="radiogroup"] label:has(input[aria-checked="true"]) {
    background-color: #00AAFF !important;
    border-color: #00AAFF !important;
    box-shadow: 0 4px 10px rgba(0, 170, 255, 0.4) !important;
}

div[role="radiogroup"] label:has(input[aria-checked="true"]) p {
    color: #ffffff !important;
}

div[role="radiogroup"] {
    justify-content: center;
    flex-wrap: wrap; 
    gap: 8px;
}
</style>
"""
st.markdown(sembunyikan_menu, unsafe_allow_html=True)

if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("⚠️ Secret Supabase belum disetting!")
    st.stop()

# ==============================================================================
# 2. SISTEM LOGIN & LOGOUT
# ==============================================================================
def logout():
    st.session_state['is_logged_in'] = False
    st.rerun()

if not st.session_state['is_logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        st.write("")
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🔐 Login Admin</h2>", unsafe_allow_html=True)
            st.write("---")
            with st.form("login_form"):
                username_input = st.text_input("Username")
                password_input = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Masuk", type="primary", use_container_width=True)
                if btn_login:
                    if username_input == "admin" and password_input == "L7pasarma#":
                        st.session_state['is_logged_in'] = True
                        st.success("Login Berhasil!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Username atau Password Salah!")
    st.stop()

# ==============================================================================
# 3. DASHBOARD ADMIN (HEADER BARU)
# ==============================================================================

# Bagian Header Khusus Admin di atas layar
c_head_kiri, c_head_kanan = st.columns([4, 1], vertical_alignment="center")
with c_head_kiri:
    st.markdown("<h2 style='margin-bottom: 0px; color: #00AAFF;'>👮 Panel Admin e-PAS Mart</h2>", unsafe_allow_html=True)
    st.caption("👤 Halo, Admin! Selamat bertugas.")
with c_head_kanan:
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        logout()

st.write("") # Jarak

# Menu Navigasi Modern (Pill Style) yang ada di tengah (Ditambahkan "📊 Rekap Transaksi")
menu_admin = st.radio(
    "Navigasi Admin:", 
    ["📋 Daftar Pesanan", "📦 Manajemen Menu", "📊 Rekap Transaksi"], 
    horizontal=True,
    label_visibility="collapsed"
)
st.divider()

# --- FUNGSI BANTUAN ---
def kompres_gambar(upload_file):
    try:
        image = Image.open(upload_file)
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        image.thumbnail((600, 600))
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=50, optimize=True)
        return output_buffer.getvalue()
    except: return None

def upload_ke_supabase(file_obj, folder, nama_unik):
    try:
        file_kecil = kompres_gambar(file_obj)
        if file_kecil:
            path = f"{folder}/{nama_unik}.jpg"
            supabase.storage.from_("KANTIN-ASSETS").upload(path, file_kecil, {"upsert": "true", "content-type": "image/jpeg"})
            return supabase.storage.from_("KANTIN-ASSETS").get_public_url(path)
        return None
    except: return None

def format_rupiah(angka):
    if angka is None: return "Rp 0"
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# --- FUNGSI CETAK NOTA (PDF A6 - UPDATE TOTAL) ---
def buat_nota_pdf(p):
    # Format A6 (105mm x 148mm)
    pdf = FPDF(format=(105, 148), unit='mm')
    pdf.set_auto_page_break(auto=True, margin=5)
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "KANTIN LAPAS", ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 10, "Lapas Kelas IIB Arga Makmur", ln=True, align='C')
    pdf.line(5, 20, 100, 20)
    pdf.ln(5)
    
    # Info
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, f"RESI: {p.get('no_resi', '-')}", ln=True, align='C')
    pdf.ln(2)
    
    pdf.set_font("Arial", size=9)
    tgl = str(p.get('created_at', '-'))[:10]
    pdf.cell(0, 5, f"Tanggal : {tgl}", ln=True)
    pdf.cell(0, 5, f"Pengirim : {str(p.get('nama_pemesan', '-'))[:20]}", ln=True)
    pdf.cell(0, 5, f"No. WA   : {str(p.get('nomor_wa', '-'))[:20]}", ln=True)
    pdf.cell(0, 5, f"Penerima : {str(p.get('untuk_siapa', '-'))[:20]}", ln=True)
    
    pdf.ln(2)
    pdf.line(5, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(2)
    
    # Items
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "DETAIL PESANAN:", ln=True)
    pdf.set_font("Arial", size=9)
    items = str(p.get('item_pesanan', '')).replace('\n', ', ')
    pdf.multi_cell(0, 5, items)
    
    # --- TOTAL BAYAR ---
    pdf.ln(3)
    total_bayar = p.get('total_harga', 0)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, f"TOTAL: {format_rupiah(total_bayar)}", 1, 1, 'R', True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "LUNAS", ln=True, align='C', border=1)
    
    pdf.set_font("Arial", 'I', 7)
    pdf.cell(0, 5, "*Simpan struk ini sebagai bukti serah terima", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# HALAMAN 1: MANAJEMEN MENU
# ==============================================================================
if menu_admin == "📦 Manajemen Menu":
    st.markdown("### 📦 Manajemen Menu Kantin")
    tab_edit, tab_tambah = st.tabs(["✏️ Edit Stok & Harga", "➕ Tambah Menu Baru"])

    with tab_edit:
        res = supabase.table("barang").select("*").order("nama_barang").execute()
        items = res.data
        if items:
            col_kiri, col_kanan = st.columns([1, 2])
            with col_kiri:
                st.subheader("Pilih Produk")
                pilihan = st.selectbox("Daftar Menu:", [b['nama_barang'] for b in items], label_visibility="collapsed")
                detail = next((item for item in items if item['nama_barang'] == pilihan), None)
                if detail:
                    st.info(f"Stok: {detail['stok']} | Harga: {format_rupiah(detail.get('harga', 0))}")
                    if detail.get('gambar_url'):
                        st.image(detail['gambar_url'], caption="Foto Saat Ini", use_container_width=True)

            with col_kanan:
                if detail:
                    st.subheader(f"Edit: {detail['nama_barang']}")
                    with st.form("edit_form"):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_stok = st.number_input("Update Stok", value=detail['stok'], min_value=0)
                            new_harga = st.number_input("Update Harga (Rp)", value=int(detail.get('harga', 0)), min_value=0, step=500)
                        with c2:
                            st.markdown("**Ganti Foto**")
                            uploaded_file = st.file_uploader("Upload File Baru", type=['png', 'jpg', 'jpeg'])
                            url_manual = st.text_input("Atau Paste Link URL", value=detail.get('gambar_url', ""))

                        btn_update = st.form_submit_button("💾 Simpan Perubahan")
                        if btn_update:
                            update_data = {"stok": new_stok, "harga": new_harga}
                            if uploaded_file:
                                f_name = f"produk_{detail['id']}_{int(time.time())}"
                                url_baru = upload_ke_supabase(uploaded_file, "produk", f_name)
                                if url_baru: update_data["gambar_url"] = url_baru
                            elif url_manual != detail.get('gambar_url'):
                                update_data["gambar_url"] = url_manual
                            
                            supabase.table("barang").update(update_data).eq("id", detail['id']).execute()
                            st.success("✅ Data berhasil diperbarui!")
                            time.sleep(1)
                            st.rerun()

                    with st.expander(f"🗑️ Hapus Menu '{detail['nama_barang']}'"):
                        if st.button("Hapus Permanen", key="hapus_btn"):
                            supabase.table("barang").delete().eq("id", detail['id']).execute()
                            st.error("Produk dihapus.")
                            time.sleep(1)
                            st.rerun()

    with tab_tambah:
        st.subheader("Tambah Menu Baru")
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1:
                nama_baru = st.text_input("Nama Produk")
                harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500, value=5000)
            with c2:
                st.number_input("Stok Awal", min_value=1, value=10, key="stok_awal_input")
                img_file = st.file_uploader("Upload Foto", type=['png', 'jpg', 'jpeg'])
                img_url_text = st.text_input("Atau Link URL")
            
            submitted = st.form_submit_button("➕ Tambahkan")
            if submitted:
                if nama_baru:
                    try:
                        final_url = ""
                        if img_file:
                            f_name = f"new_{int(time.time())}"
                            final_url = upload_ke_supabase(img_file, "produk", f_name)
                        elif img_url_text:
                            final_url = img_url_text
                        stok_fix = st.session_state.get("stok_awal_input", 10)
                        new_data = {"nama_barang": nama_baru, "stok": stok_fix, "harga": harga_baru, "gambar_url": final_url}
                        supabase.table("barang").insert(new_data).execute()
                        st.success(f"🎉 {nama_baru} berhasil ditambahkan!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Nama produk wajib diisi!")

# ==============================================================================
# HALAMAN 2: DAFTAR PESANAN
# ==============================================================================
elif menu_admin == "📋 Daftar Pesanan":
    st.markdown("### 📋 Verifikasi & Proses Pesanan")
    
    c_search, c_btn = st.columns([3, 1])
    with c_search:
        cari_resi = st.text_input("🔍 Cari Nomor Resi", placeholder="Ketik Resi Lengkap atau 4 Digit Terakhir...")
    with c_btn:
        st.write(""); st.write("") 
        if st.button("🔄 Refresh Data", use_container_width=True): st.rerun()

    filter_data = None
    if cari_resi:
        res = supabase.table("pesanan").select("*").ilike("no_resi", f"%{cari_resi.strip()}").execute()
        filter_data = res.data
        if not filter_data: st.error("Resi tidak ditemukan.")
        else: st.success(f"Ditemukan {len(filter_data)} pesanan.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Pesanan Masuk", "📦 Sedang Diproses", "✅ Riwayat Selesai", "❌ Dibatalkan User", "🚫 Ditolak Admin"])

    def render_pesanan(p_list, status_tab):
        if not p_list:
            st.info("Tidak ada data.")
            return

        for p in p_list:
            total_duit = p.get('total_harga', 0)
            if total_duit is None: total_duit = 0

            with st.container(border=True):
                cols = st.columns([1, 2, 2])
                with cols[0]:
                    st.subheader(f"#{p['id']}")
                    st.caption(f"Resi: {p.get('no_resi', '-')}")
                    if p.get('bukti_transfer'):
                        st.image(p['bukti_transfer'], caption="Bukti TF", width=150)
                    else:
                        st.error("Belum ada bukti TF")
                    
                    if p.get('nota_url'): st.link_button("🧾 Nota Lama", p['nota_url'])

                with cols[1]:
                    st.write(f"**Pengirim:** {p['nama_pemesan']}")
                    st.write(f"**No. WA:** {p.get('nomor_wa', '-')}")
                    st.write(f"**Penerima:** {p['untuk_siapa']}")
                    st.write(f"**Metode:** {p.get('cara_bayar', '-')}")
                    
                    st.code(f"Isi: {p['item_pesanan']}")
                    
                    st.markdown(f"💰 **TOTAL TRANSFER:**")
                    st.markdown(f"### `{format_rupiah(total_duit)}`")
                    st.caption("*(Cocokkan angka ini dengan mutasi rekening)*")

                    if "Ditolak" in p.get('status', ''): st.error(f"Status: {p['status']}")

                with cols[2]:
                    if p['status'] in ["Pembayaran Valid (Diproses)", "Selesai"] or status_tab == "Proses":
                        pdf_data = buat_nota_pdf(p)
                        st.download_button("🖨️ CETAK NOTA (PDF)", pdf_data, f"Nota_{p['no_resi']}.pdf", "application/pdf", key=f"print_{p['id']}", type="secondary")
                        st.write("---")

                    if "Ditolak" in p.get('status', ''):
                        st.info("ℹ️ Data ini telah diarsipkan.")
                    else:
                        with st.form(key=f"form_{p['id']}"):
                            st.write("**Tindakan:**")
                            opsi = ["Menunggu Verifikasi", "Pembayaran Valid (Diproses)", "Selesai"]
                            try: idx = opsi.index(p['status'])
                            except: idx = 0 
                            st_baru = st.selectbox("Update Status", opsi, index=idx, key=f"s_{p['id']}")
                            
                            foto = None
                            if st_baru == "Selesai":
                                st.caption("📷 Upload Foto Penyerahan Barang (Max 5MB):")
                                foto = st.file_uploader("Pilih file foto", type=['jpg', 'jpeg', 'png'], key=f"c_{p['id']}")
                            
                            btn_proses = st.form_submit_button("Simpan & Proses")
                            if btn_proses:
                                u_data = {"status": st_baru}
                                if st_baru == "Selesai":
                                    if foto:
                                        if foto.size > 5 * 1024 * 1024:
                                            st.error("⚠️ Ukuran file foto melebihi 5 MB! Harap upload file yang lebih kecil.")
                                        else:
                                            f_name = f"serah_{p['no_resi'] if p.get('no_resi') else p['id']}"
                                            url_foto = upload_ke_supabase(foto, "bukti_serah", f_name)
                                            if url_foto:
                                                u_data["foto_penerima"] = url_foto
                                                supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                                
                                                no_hp = p.get('nomor_wa', '')
                                                if no_hp and no_hp.startswith('0'): no_hp = '62' + no_hp[1:]
                                                msg = f"Halo, Pesanan Resi {p.get('no_resi')} SUDAH DITERIMA oleh {p['untuk_siapa']}. Terima kasih."
                                                link_wa = f"https://wa.me/{no_hp}?text={msg.replace(' ', '%20')}"
                                                st.success("✅ Pesanan Selesai!")
                                                st.link_button("📲 Kabari via WA", link_wa)
                                            else: st.error("Gagal upload foto.")
                                    else: st.error("⚠️ Foto penyerahan wajib di-upload!")
                                else:
                                    supabase.table("pesanan").update(u_data).eq("id", p['id']).execute()
                                    st.success(f"Status diubah: {st_baru}"); time.sleep(1); st.rerun()

    if filter_data:
        st.warning("Menampilkan hasil pencarian:")
        render_pesanan(filter_data, "Search")
    else:
        with tab1: # Pesanan Masuk
            st.header("📥 Pesanan Baru Masuk")
            res = supabase.table("pesanan").select("*").eq("status", "Menunggu Verifikasi").order("id", desc=True).execute()
            if not res.data: st.info("✅ Tidak ada antrian pesanan baru.")
            else:
                for p in res.data:
                    total_duit = p.get('total_harga', 0)
                    if total_duit is None: total_duit = 0

                    with st.container(border=True):
                        cols = st.columns([1, 2, 2])
                        with cols[0]:
                            st.subheader(f"#{p['id']}")
                            st.caption(f"Resi: {p.get('no_resi', '-')}")
                            if p.get('bukti_transfer'):
                                st.image(p['bukti_transfer'], caption="Cek Bukti TF", width=150)
                                st.link_button("🔍 Zoom Gambar", p['bukti_transfer'])
                            else: st.error("❌ TIDAK ADA BUKTI")
                        with cols[1]:
                            st.write(f"**Pengirim:** {p['nama_pemesan']}")
                            st.write(f"**No. WA:** {p.get('nomor_wa', '-')}")
                            st.write(f"**Penerima:** {p['untuk_siapa']}")
                            st.info(f"Metode: {p.get('cara_bayar', '-')}")
                            st.code(f"Isi: {p['item_pesanan']}")

                            st.markdown(f"💰 **TOTAL TRANSFER:**")
                            st.markdown(f"### `{format_rupiah(total_duit)}`")
                            st.caption("*(Termasuk Kode Unik)*")

                        with cols[2]:
                            st.write("---")
                            st.write("**Keputusan:**")
                            if st.button("✅ TERIMA PESANAN", key=f"acc_{p['id']}", type="primary", use_container_width=True):
                                supabase.table("pesanan").update({"status": "Pembayaran Valid (Diproses)"}).eq("id", p['id']).execute()
                                st.success("Pesanan diterima!"); time.sleep(1); st.rerun()
                            st.write("") 
                            with st.expander("🚫 Tolak Pesanan"):
                                st.warning("Pesanan akan ditandai 'Ditolak'")
                                alasan_list = ["Bukti Transfer Palsu / Buram", "Nominal Transfer Kurang", "Stok Barang Habis", "Data WBP Tidak Ditemukan", "Indikasi Spam"]
                                alasan_pilih = st.selectbox("Alasan:", alasan_list, key=f"rsn_{p['id']}")
                                if st.button("🚫 TOLAK", key=f"deny_{p['id']}", type="secondary", use_container_width=True):
                                    supabase.table("pesanan").update({"status": f"Ditolak Admin: {alasan_pilih}"}).eq("id", p['id']).execute()
                                    st.error("Ditolak."); time.sleep(1); st.rerun()

        with tab2: # Sedang Diproses
            st.header("📦 Sedang Disiapkan")
            res = supabase.table("pesanan").select("*").eq("status", "Pembayaran Valid (Diproses)").order("id", desc=True).execute()
            render_pesanan(res.data, "Proses")

        with tab3: # Selesai
            st.header("✅ Riwayat Selesai")
            res = supabase.table("pesanan").select("*").eq("status", "Selesai").order("id", desc=True).limit(20).execute()
            if res.data:
                for p in res.data:
                    with st.expander(f"✅ {p['no_resi']} - {p['untuk_siapa']}"):
                        st.write(f"Item: {p['item_pesanan']}")
                        pdf_data = buat_nota_pdf(p)
                        st.download_button("🖨️ Reprint Nota", pdf_data, f"Nota_{p['no_resi']}.pdf", "application/pdf", key=f"reprint_{p['id']}")
                        if p.get('foto_penerima'): st.image(p['foto_penerima'], caption="Bukti Serah", width=200)
            else: st.info("Belum ada riwayat.")

        with tab4: # Batal User
            st.header("🎫 Audit Voucher")
            c_cek, c_info = st.columns([3, 1])
            with c_cek: cek_kode = st.text_input("🔍 Scan Kode Resi / Voucher")
            
            query = supabase.table("pesanan").select("*").in_("status", ["Dibatalkan", "Voucher Sudah Dipakai"]).order("id", desc=True)
            if cek_kode: query = query.eq("no_resi", cek_kode.replace("REF-", "").strip())
            
            items = query.execute().data
            if not items: st.info("Data tidak ditemukan.")
            else:
                for d in items:
                    status_text = "VOUCHER BELUM DIPAKAI" if d['status'] == "Dibatalkan" else "SUDAH TERPAKAI"
                    bg_color = "#07213d" if d['status'] == "Dibatalkan" else "#fff5f5"
                    border_color = "green" if d['status'] == "Dibatalkan" else "red"
                    
                    with st.container():
                        st.markdown(f"""<div style="border: 2px solid {border_color}; padding: 10px; border-radius: 10px; background-color: {bg_color}; margin-bottom: 10px;"><h3 style="margin:0;">{d['no_resi']}</h3><b>STATUS: {status_text}</b></div>""", unsafe_allow_html=True)
                        c1, c2 = st.columns([1.5, 1])
                        with c1:
                            st.write(f"👤 **Pemilik:** {d['nama_pemesan']}")
                            
                            total_vou = d.get('total_harga', 0)
                            if total_vou is None: total_vou = 0
                            st.markdown(f"💰 **Nilai Voucher:** `{format_rupiah(total_vou)}`")
                            
                            if d['status'] == "Dibatalkan":
                                st.write("---"); c_sah, c_tolak = st.columns(2)
                                with c_sah:
                                    if st.button("✅ SAHKAN", key=f"clm_{d['id']}", type="primary", use_container_width=True):
                                        supabase.table("pesanan").update({"status": "Voucher Sudah Dipakai"}).eq("id", d['id']).execute()
                                        st.rerun()
                                with c_tolak:
                                    if st.button("🚫 HANGUSKAN", key=f"dny_{d['id']}", use_keyword=True, use_container_width=True):
                                        supabase.table("pesanan").update({"status": "Voucher Ditolak / Hangus"}).eq("id", d['id']).execute()
                                        st.rerun()
                        with c2:
                            if d.get('bukti_transfer'): st.image(d['bukti_transfer'])
                            else: st.error("No Bukti")

        with tab5: # Ditolak Admin
            st.header("🚫 Arsip Penolakan")
            res_tolak = supabase.table("pesanan").select("*").ilike("status", "%Ditolak Admin%").order("id", desc=True).limit(50).execute()
            render_pesanan(res_tolak.data, "Arsip")

# ==============================================================================
# HALAMAN 3: REKAP TRANSAKSI (FITUR BARU)
# ==============================================================================
# ==============================================================================
# HALAMAN 3: REKAP TRANSAKSI (DENGAN FITUR CETAK PDF)
# ==============================================================================
elif menu_admin == "📊 Rekap Transaksi":
    st.markdown("### 📊 Rekap Transaksi Sukses e-PAS Mart")
    st.caption("Menampilkan seluruh daftar transaksi yang telah berstatus **Selesai** lengkap dengan informasi detail, bukti transfer, dan bukti serah terima.")

    # Ambil data transaksi yang statusnya 'Selesai' dari Supabase
    res_rekap = supabase.table("pesanan").select("*").eq("status", "Selesai").order("id", desc=True).execute()
    data_selesai = res_rekap.data

    if not data_selesai:
        st.info("Belum ada data transaksi yang berstatus 'Selesai'.")
    else:
        # Fungsi untuk membuat PDF Rekap Transaksi Keseluruhan
        def buat_rekap_pdf(data_list):
            pdf = FPDF(unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            
            # Header Laporan
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 8, "LAPORAN REKAP TRANSAKSI SUKSES", ln=True, align='C')
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, "e-PAS Mart - Lapas Kelas IIB Arga Makmur", ln=True, align='C')
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 5, f"Dicetak pada: {datetime.now().strftime('%d-%m-%Y %H:%M')} WIB", ln=True, align='C')
            pdf.ln(5)
            
            # Tabel Header
            pdf.set_font("Arial", 'B', 8)
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(10, 7, "No", 1, 0, 'C', True)
            pdf.cell(30, 7, "No. Resi", 1, 0, 'C', True)
            pdf.cell(35, 7, "Pemesan", 1, 0, 'C', True)
            pdf.cell(35, 7, "Penerima (WBP)", 1, 0, 'C', True)
            pdf.cell(50, 7, "Item Pesanan", 1, 0, 'C', True)
            pdf.cell(30, 7, "Total (Rp)", 1, 1, 'C', True)
            
            # Isi Tabel
            pdf.set_font("Arial", '', 8)
            for idx, item in enumerate(data_list, 1):
                resi = str(item.get('no_resi', '-'))
                pemesan = str(item.get('nama_pemesan', '-'))[:18]
                penerima = str(item.get('untuk_siapa', '-'))[:18]
                item_pesan = str(item.get('item_pesanan', '-'))[:28]
                total = format_rupiah(item.get('total_harga', 0))
                
                pdf.cell(10, 6, str(idx), 1, 0, 'C')
                pdf.cell(30, 6, resi, 1, 0, 'C')
                pdf.cell(35, 6, pemesan, 1, 0, 'L')
                pdf.cell(35, 6, penerima, 1, 0, 'L')
                pdf.cell(50, 6, item_pesan, 1, 0, 'L')
                pdf.cell(30, 6, total, 1, 1, 'R')
                
            return pdf.output(dest='S').encode('latin-1')

        # Tombol Cetak/Download Rekap (CSV & PDF)
        st.write("---")
        c_info, c_csv, c_pdf = st.columns([1.5, 1, 1])
        with c_info:
            st.write(f"Total Transaksi Sukses Tercatat: **{len(data_selesai)} pesanan**")
        with c_csv:
            df_rekap = pd.DataFrame(data_selesai)
            kolom_laporan = {
                'id': 'ID', 'no_resi': 'No Resi', 'created_at': 'Tanggal Pesan',
                'nama_pemesan': 'Nama Pemesan', 'nomor_wa': 'No HP Pemesan',
                'untuk_siapa': 'Nama Penerima (WBP)', 'item_pesanan': 'Barang Pesanan',
                'total_harga': 'Total Harga (Rp)', 'cara_bayar': 'Metode Bayar',
                'bukti_transfer': 'Link Bukti Transfer', 'foto_penerima': 'Link Bukti Serah Terima'
            }
            df_export = df_rekap[[k for k in kolom_laporan.keys() if k in df_rekap.columns]].rename(columns=kolom_laporan)
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"Rekap_Transaksi_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c_pdf:
            pdf_rekap_data = buat_rekap_pdf(data_selesai)
            st.download_button(
                label="🖨️ Cetak PDF",
                data=pdf_rekap_data,
                file_name=f"Rekap_Transaksi_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        st.write("---")

        # Tampilkan Detail Per Transaksi di Panel Admin
        for idx, item in enumerate(data_selesai, 1):
            with st.container(border=True):
                st.markdown(f"#### 🏷️ Transaksi #{item.get('id')} — Resi: `{item.get('no_resi', '-')}`")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.markdown(f"**👤 Nama Pemesan:** {item.get('nama_pemesan', '-')}")
                    st.markdown(f"**📞 No. HP / WA:** {item.get('nomor_wa', '-')}")
                    st.markdown(f"**📅 Tanggal:** {str(item.get('created_at', '-'))[:16]}")
                with col_info2:
                    st.markdown(f"**🎯 Nama Penerima (WBP):** {item.get('untuk_siapa', '-')}")
                    st.markdown(f"**💳 Metode Bayar:** {item.get('cara_bayar', '-')}")
                    st.markdown(f"**💰 Total Transaksi:** `{format_rupiah(item.get('total_harga', 0))}`")
                with col_info3:
                    st.markdown(f"**📦 Barang Pesanan:**")
                    st.code(item.get('item_pesanan', '-'))

                st.write("")
                
                col_img1, col_img2 = st.columns(2)
                with col_img1:
                    st.markdown("**🧾 Bukti Transfer:**")
                    if item.get('bukti_transfer'):
                        st.image(item.get('bukti_transfer'), caption="Bukti Transfer Pengirim", width=250)
                        st.link_button("🔍 Buka Gambar TF Full", item.get('bukti_transfer'))
                    else:
                        st.warning("Tidak ada bukti transfer yang diunggah.")
                        
                with col_img2:
                    st.markdown("**🤝 Bukti Serah Terima:**")
                    if item.get('foto_penerima'):
                        st.image(item.get('foto_penerima'), caption="Foto Penyerahan ke WBP", width=250)
                        st.link_button("🔍 Buka Foto Serah Terima Full", item.get('foto_penerima'))
                    else:
                        st.warning("Foto bukti serah terima belum tersedia.")
