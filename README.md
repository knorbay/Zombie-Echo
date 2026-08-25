# Zombie Echo: Those Left in the Dark

![Zombie Echo logo](assets/logo.png)

Sade dark temalı, hızlı tempolu bir Pygame arena-aksiyon oyunu.

## Çalıştırma

PyCharm içinden `main.py` dosyasını çalıştırabilir veya proje klasöründe:

```bash
.venv/bin/python main.py
```

macOS kullanıcıları GitHub Actions tarafından oluşturulan `Zombie-Echo-macOS`
artifact'ini indirip `Zombie Echo.app` dosyasını doğrudan açabilir.

## Kontroller

- `WASD`: Hareket
- `Sol tık`: Ateş
- `R`: Şarjör değiştir
- `1-7` veya fare tekerleği: Silah seç
- `SPACE`: Dash
- `Q` veya `sağ tık`: Yakın mesafe itme saldırısı
- `H`: Sağlık çantası kullan
- `I` veya `TAB`: Envanter / loadout
- `E`: Eşya al
- `ESC`: Duraklat

## Aksiyon güncellemesi

- 7 silah: Pistol, Revolver, SMG, Rifle, Shotgun, LMG ve Launcher
- Basit silah listesi ve cephane ekranı
- Sağlık çantası, cephane ve geçici güçlendirmeler
- Her dalga sonunda garantili ödül
- Her 5 dalgada Juggernaut, Broodmother veya Reaper boss
- Hasar veren dash, yakın saldırı ve patlayan variller
- Yakın öldürmelerde mermi iadesi ve dash yenileme; kill zincirinde artan hareket/ateş temposu
- Düşük canlı normal düşmanlara melee bitirici vuruş
- Otomatik sarf malzemesi toplama ve kesintisiz silah değiştirme
- Daha kısa bekleme süreleri ve hızlı dalga temposu
- Duvarları dolaşan, oyuncunun hareketini öngören ve birbirinden ayrılan gelişmiş düşman davranışları
- Sade daire/şekil görsel dili, kısa mermi izleri ve koyu harita dokusu
- Oyuncuda 250 px tam görüş + iki adet 50 px geçiş bandı; harita lambalarında 300 px katmanlı ışık
- Oyun boyunca döngüde çalan arka plan müziği
- Yeni pickup, seçim, hata, loot ve yakın saldırı sesleri

## Asset lisansları

- Ek ses efektleri: Kenney.nl, CC0

## macOS uygulaması oluşturma

```bash
python3 -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm ZombieEcho.spec
```

Uygulama `dist/Zombie Echo.app` olarak oluşur.
