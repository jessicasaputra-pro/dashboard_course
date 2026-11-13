# Salin isi file ini ke WSGI configuration file di tab Web PythonAnywhere
# (/var/www/<username>_pythonanywhere_com_wsgi.py), lalu ganti USERNAME.
import sys

PROJECT = "/home/USERNAME/dashboard_course"      # folder hasil git clone
if f"{PROJECT}/sesi7" not in sys.path:
    sys.path.insert(0, f"{PROJECT}/sesi7")

from app_dash_callback import server as application   # noqa: E402
