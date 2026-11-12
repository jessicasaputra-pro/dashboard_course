# Paket Praktikum — Interactive Dashboard Development with Streamlit & Dash

Pendamping buku praktikum (2nd OJT Technical Data Analytics, ITSB Corporation).
Semua perintah dijalankan dari folder ini.

## Setup
    python -m venv .venv
    .venv\Scripts\activate          # Windows
    source .venv/bin/activate       # macOS/Linux
    pip install -r requirements.txt

## Menjalankan
| Sesi | Perintah |
|---|---|
| 1 | streamlit run sesi1/app_hello.py  ·  sesi1/app_komponen.py  ·  sesi1/app_kalkulator_tagihan.py |
| 2 | python sesi2/eda_churn.py (16 grafik)  ·  streamlit run sesi2/app_eda.py |
| 3 | streamlit run sesi3/app_layout_dashboard.py |
| 4 | python sesi4/cek_inference.py  ·  streamlit run sesi4/app_prediksi.py |
| 5 | python sesi5/app_halo.py  ·  python sesi5/app_dash_dasar.py  (http://127.0.0.1:8050) |
| 6 | python sesi6/plotly_galeri.py  ·  python sesi6/app_dash_plotly.py  (:8051) |
| 7 | python sesi7/app_dash_callback.py  (:8052) |
| 8 | python sesi8/app_final_dashboard.py  (:8053) |

Model final: models/churn_model.joblib (scikit-learn 1.9.1). Data latihan bersifat sintetis.
models/prepare_final_model.py hanya dokumentasi fasilitator — tidak dijalankan peserta.

## Untuk keluar

Untuk keluar dari tampilan tersebut di VS Code, kemungkinan Anda sedang menjalankan aplikasi Streamlit di Terminal.

Tekan:  Control (⌃) + C


## Buka Terminal di VS Code

Pilih menu:

Terminal → New Terminal

Jalankan:
git init
git add .
git commit -m "Initial commit"


## Hubungkan dengan GitHub

1. Buka GitHub.
2. Buat repository bernama dashboard-course.
3. Kembali ke Terminal VS Code.
4. Jalankan perintah berikut (ganti USERNAME dengan username GitHub Anda).
git branch -M main
git remote add origin https://github.com/USERNAME/dashboard-course.git
git push -u origin main


## Deploy ke Streamlit Cloud
Buka Streamlit Community Cloud ---> https://share.streamlit.io.

Pilih:
- Repository: dashboard-course
- Branch: main
- Main file path: sesi1/app_hello.py
Klik Deploy.
