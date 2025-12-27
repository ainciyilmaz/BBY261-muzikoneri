from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import urllib.parse
import json
import os
import random

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
FAV_DOSYASI = os.path.join(basedir, "favoriler.json")

def favorileri_oku():
    if not os.path.exists(FAV_DOSYASI): return []
    try:
        with open(FAV_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

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

def sarki_getir(mod):
    # Mood'a göre iTunes'da aranacak kelimeler (İngilizce + Türkçe karışık en iyi sonuç için)
    arama_terimleri = {
        "happy": "happy hits music",
        "sad": "sad songs emotional",
        "energetic": "workout energy rock",
        "chill": "chillout lounge relax"
    }

    aranacak_kelime = arama_terimleri.get(mod, "pop hits")

    # iTunes API'si PythonAnywhere'de ENGELLİ DEĞİLDİR!
    # Direkt arama yapıyoruz.
    try:
        parametreler = {
            "term": aranacak_kelime,
            "media": "music",
            "entity": "song",
            "limit": 50,  # 50 tane çekelim ki içinden rastgele seçelim
            "country": "TR" # Türkiye mağazasından çeksin
        }

        url = "https://itunes.apple.com/search"
        response = requests.get(url, params=parametreler, timeout=10)

        sarki_listesi = []

        if response.status_code == 200:
            sonuclar = response.json().get("results", [])

            # Gelen sonuçları karıştıralım ki her seferinde aynısı gelmesin
            if len(sonuclar) > 0:
                random.shuffle(sonuclar)
                secilenler = sonuclar[:8] # İlk 8 tanesini al

                for sarki in secilenler:
                    # Resim kalitesini artır
                    resim = sarki.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                    if not resim:
                        resim = "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=500&h=500&fit=crop"

                    sarki_listesi.append({
                        "isim": sarki.get("trackName"),
                        "sanatci": sarki.get("artistName"),
                        "resim": resim,
                        "onizleme": sarki.get("previewUrl")
                    })

        return sarki_listesi

    except Exception as e:
        print(f"Hata: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def anasayfa():
    secilen_mod = None
    sarkilar = []

    if request.method == 'POST':
        secilen_mod = request.form.get('mod')
        sarkilar = sarki_getir(secilen_mod)

    return render_template('index.html', sarkilar=sarkilar, mod=secilen_mod)

@app.route('/begen', methods=['POST'])
def begen():
    data = request.get_json()
    sarki = {
        "isim": data.get('isim'),
        "sanatci": data.get('sanatci'),
        "resim": data.get('resim'),
        "onizleme": data.get('onizleme')
    }
    favori_ekle(sarki)
    return jsonify({"success": True})

@app.route('/sil', methods=['POST'])
def sil():
    isim = request.form.get('isim')
    favori_sil(isim)
    return redirect(url_for('favorilerim'))

@app.route('/favorilerim')
def favorilerim():
    kayitli_sarkilar = favorileri_oku()
    return render_template('favoriler.html', sarkilar=kayitli_sarkilar)

if __name__ == '__main__':
    app.run(debug=True)
