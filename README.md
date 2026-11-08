# Sosial Instruktor — Telegram Botu

Modern, çoxfunksiyalı Telegram botu (Aiogram v3) — investisiya testi, investisiya xəbərləri və RBCron balansı.

## Xüsusiyyətlər

- 📈 İnvestisiya xəbərləri — admin əlavə edir, istifadəçilərə bildiriş gedir
- 💰 RBCron balansı — balansı göstər/artır, qəbz adminə təsdiq üçün gedir
- 🔔 Admin start bildirişi — hansı build-in işə düşdüyü görünür

Arxitektura: Aiogram Router-ları (`handlers/*`) və PostgreSQL. Balanslar, ödəniş qəbzləri, xəbərlər və istifadəçi tarixçələri verilənlər bazasında saxlanılır.

## Quraşdırma (lokal)

1) Tələblər
- Python 3.12 (runtime.txt ilə uyğun)
- Pip paketləri: `pip install -r requirements.txt`

2) Mühit dəyişənləri (`.env`)
```
BOT_TOKEN=xxxx:yyyy
ADMIN_ID=123456789
APP_VERSION=dev
REPO_NAME=Yeni_Repo
DATABASE_URL=postgresql://user:password@host:5432/database
PAYMENT_PROVIDER_TOKEN=...
PAYMENT_CURRENCY=USD
```

3) İşə salma
- VS Code task: Run Bot (venv)
- və ya terminaldan:
```
python run.py
```

## İstifadəçi axınları (qısa)

- `/start` (şəxsi mesaj): əsas menyunu açır
- “İnvestisiya xəbərləri” → başlıqlar siyahısı, oxu düyməsi
- “Balans” → paket seçib Telegram Payments ilə ödəniş etmək
- İstifadəçi və bot mesajları 5 dəqiqədən sonra avtomatik silinir; qruplarda istifadəçi mesajlarını silmək üçün bot admin icazəsinə malik olmalıdır
- `/clearall` (yalnız admin): təsdiqdən sonra botun məlumat cədvəllərini təmizləyir; miqrasiya qeydləri saxlanılır ki, köhnə məlumatlar yenidən import olunmasın

## Deploy (Railway)

- Procfile: `worker: python run.py`
- runtime.txt: `python-3.12`
- Environment: `BOT_TOKEN`, `ADMIN_ID`, `DATABASE_URL`, `PAYMENT_PROVIDER_TOKEN`, `PAYMENT_CURRENCY`, opsional `APP_VERSION`, `REPO_NAME`

Addımlar:
1. Repo GitHub-da hazır olsun
2. Railway → New Project → Deploy from GitHub → bu repozitoriyanı seç
3. Eyni Railway layihəsində PostgreSQL servisi əlavə et və onun bağlantı URL-ini bot servisində `DATABASE_URL` dəyişəni kimi qoş
4. `BOT_TOKEN`, `ADMIN_ID` və BotFather-dən alınan `PAYMENT_PROVIDER_TOKEN` daxil olmaqla mühit dəyişənlərini əlavə et; tokeni repoya yazma
5. Deploy — asılılıqlar avtomatik qurulacaq, worker prosesi işə düşəcək

Qeydlər:
- Long polling istifadə olunur (webhook tələb etmir)
- `DATABASE_URL` mütləq PostgreSQL servisindən gəlməlidir; SQLite faylı Railway deploy-ları arasında davamlı saxlanmır
- İlk startda deploy paketində tapılan köhnə SQLite/JSON/log məlumatları PostgreSQL-ə bir dəfə import edilir

## Faydalı fayllar
- `run.py` — giriş nöqtəsi; router-ları qoşur, DB cədvəllərini yaradır, start bildirişi göndərir
- `handlers/` — modul-modul xüsusiyyətlər
- `database/` — PostgreSQL bağlantısı, sxem və birdəfəlik legacy data importu
- `media/` — video və media faylları

— Bu botu öz layihənə uyğun asanlıqla fərdiləşdirə bilərsən.