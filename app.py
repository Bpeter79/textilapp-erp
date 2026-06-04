import os
import re
import streamlit as st
from sqlalchemy import create_engine, text
from PIL import Image
import io

# --- Konfiguráció ---
# A felhőben a Streamlit Secrets-ből veszi a kapcsolatot, ha az nincs, akkor helyi SQLite
DB_CONNECTION_STRING = st.secrets.get("DATABASE_URL", "sqlite:///textilapp.db")

# Fájlrendszer előkészítés
UPLOAD_DIR_FILES = "stored_optitex"
UPLOAD_DIR_IMAGES = "stored_images"
os.makedirs(UPLOAD_DIR_FILES, exist_ok=True)
os.makedirs(UPLOAD_DIR_IMAGES, exist_ok=True)

# --- Adatbázis Kapcsolat ---
@st.cache_resource
def get_engine():
    engine = create_engine(DB_CONNECTION_STRING, echo=False)
    return engine

def db_exec(sql, params=None):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error(f"Adatbázis hiba: {e}")
        return False

# --- Képoptimalizálás ---
def optimize_and_compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if img.width > 1280:
        ratio = 1280 / float(img.width)
        new_height = int(float(img.height) * ratio)
        img = img.resize((1280, new_height), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75, optimize=True)
    return buffer.getvalue()

# --- Felület ---
st.title("🧵 TextilApp ERP — Éles")

menu = st.sidebar.radio("Navigáció", ["Ügyfelek", "Projektek"])

if menu == "Ügyfelek":
    st.header("Új ügyfél")
    cegnev = st.text_input("Cégnév")
    if st.button("Mentés") and cegnev:
        db_exec("INSERT INTO ugyfelek (cegnev) VALUES (:c)", {"c": cegnev})
        st.success("Mentve!")

elif menu == "Projektek":
    st.header("Projektek és Média")
    p_szam = st.text_input("Projekt szám")
    p_nev = st.text_input("Projekt név")
    
    uploaded_photo = st.file_uploader("Fénykép feltöltése (mobilról)", type=["jpg", "png"])
    
    if st.button("Mentés"):
        photo_path = None
        if uploaded_photo:
            filename = f"{p_szam}_photo.jpg"
            photo_path = os.path.join(UPLOAD_DIR_IMAGES, filename)
            with open(photo_path, "wb") as f:
                f.write(optimize_and_compress_image(uploaded_photo))
        
        # SQL beszúrás ide jön...
        st.success("Projekt és kép feldolgozva!")