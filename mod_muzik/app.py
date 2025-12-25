from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import random
import json
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
FAV_DOSYASI = os.path.join(basedir, "favoriler.json")

def favorileri_oku():
    if not os.path.exists(FAV_DOSYASI):
        return []
    try:
        with open(FAV_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def favori_ekle(sarki_verisi):
    mevcut_favoriler = favorileri_oku()
    for fav in mevcut_favoriler:
        if fav["isim"] == sarki_verisi["isim"] and fav["sanatci"] == sarki_verisi["sanatci"]:
            return
    
    mevcut_favoriler.append(sarki_verisi)
    with open(FAV_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(mevcut_favoriler, f, ensure_ascii=False, indent=4)

def favori_sil(isim):
    mevcut = favorileri_oku()
    yeni_liste = [sarki for sarki in mevcut if sarki["isim"] != isim]
    with open(FAV_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(yeni_liste, f, ensure_ascii=False, indent=4)

def detay_getir(sanatci, sarki):
    varsayilan_resim = "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=500&h=500&fit=crop"
    
    try:
        aranan = f"{sanatci} {sarki}"
        aranan_kodlu = urllib.parse.quote(aranan)
        
        url = f"https://itunes.apple.com/search?term={aranan_kodlu}&limit=1&media=music"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            veri = response.json()
            if veri["resultCount"] > 0:
                sonuc = veri["results"][0]
                
                kucuk_resim = sonuc.get("artworkUrl100", "")
                buyuk_resim = kucuk_resim.replace("100x100bb", "600x600bb") if kucuk_resim else varsayilan_resim
                
                ses_linki = sonuc.get("previewUrl", "")
                
                return {"resim": buyuk_resim, "onizleme": ses_linki}
                
    except:
        pass
    
    return {"resim": varsayilan_resim, "onizleme": ""}

def sarki_getir(mod):
    url = f"https://www.last.fm/tag/{mod}/tracks"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    sarki_listesi = []
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.content, "html.parser")
        tüm_satirlar = soup.find_all("tr", class_="chartlist-row")

        if len(tüm_satirlar) > 8:
            secilen_satirlar = random.sample(tüm_satirlar, 8)
        else:
            secilen_satirlar = tüm_satirlar

        for satir in secilen_satirlar: 
            try:
                isim = satir.find("td", class_="chartlist-name").find("a").text.strip()
                sanatci = satir.find("td", class_="chartlist-artist").find("a").text.strip()
                
                detaylar = detay_getir(sanatci, isim)

                sarki_listesi.append({
                    "isim": isim,
                    "sanatci": sanatci,
                    "resim": detaylar["resim"],
                    "onizleme": detaylar["onizleme"]
                })
            except:
                continue
                
    except Exception as e:
        print(f"Hata: {e}")
        
    return sarki_listesi

@app.route('/', methods=['GET', 'POST'])
def anasayfa():
    secilen_mod = None
    sarkilar = []