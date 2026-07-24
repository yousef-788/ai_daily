# AI Daily

نظام يجمع محتوى عن الذكاء الاصطناعي من مصادر مختلفة (حاليًا RSS، وقابل للتوسع لاحقًا)،
يعالجه (تنظيف نص + تلخيص اختياري بالـ AI)، ثم يجهّزه كنشرة يومية جاهزة للنشر
في قناة واتساب باسم **AI Daily**.

## حالة المشروع

✅ **MVP كامل وشغال**: الجمع → منع التكرار → التنظيف → التلخيص (اختياري) → تجهيز مسودة النشر.

## التثبيت

```bash
# 1) استنساخ المشروع والدخول لمجلده
cd ai_daily

# 2) (يُفضّل) إنشاء بيئة افتراضية
python3 -m venv .venv
source .venv/bin/activate

# 3) تثبيت المشروع مع أدوات التطوير (pytest)
pip install -e ".[dev]"
```

## الإعداد

### 1) مصادر المحتوى

المصادر الحالية في `config/sources.json`:

| المصدر | النوع | بيغطي |
|---|---|---|
| VentureBeat AI | `rss` | أخبار AI عامة |
| TechCrunch | `rss` | أخبار AI وستارت أب |
| The Rundown AI | `rss` | أخبار + أداة اليوم + تلميحات Prompt |
| Wuzzuf AI Jobs | `wuzzuf_jobs` | وظائف AI في مصر (مفلترة بالكلمات المفتاحية) |

عدّل الملف وأضف/احذف مصادر حسب احتياجك. أنواع RSS الجديدة تحتاج بس `name` و`type: rss` و`url`. لإضافة مصدر Scraping عام، استخدم `type: scraping` مع `selectors` (راجع `web_scraper_collector.py`).

**ملحوظة عن Wuzzuf AI Jobs:** الـ CSS selectors المستخدمة قابلة للتغيّر لو Wuzzuf عدّل تصميم الموقع. لو المصدر رجّع صفر وظائف رغم وجود وظائف AI فعليًا على الموقع، افتح صفحة البحث في المتصفح، افحص الـ HTML (Inspect Element)، وحدّث الـ selectors في `wuzzuf_jobs_collector.py`.

### 2) تلخيص المحتوى بالـ AI (اختياري)

لو عايز تفعّل تلخيص الأخبار تلقائيًا بالـ AI بدل نشر النص الخام:

```bash
cp .env.example .env
# افتح .env وحط مفتاح Anthropic API الحقيقي بتاعك في ANTHROPIC_API_KEY
```

من غير المفتاح ده، المشروع هيشتغل عادي وينشر المحتوى بعد التنظيف بس (بدون تلخيص).

## التشغيل

```bash
ai-daily
# أو
python src/ai_daily/main.py
```

هيتم حفظ نشرة اليوم في `data/drafts/<التاريخ>.txt`، جاهزة تفتحها وتنسخها لقناة واتساب.

## التشغيل الأوتوماتيكي اليومي (Windows)

عشان المشروع يشتغل لوحده كل يوم من غير ما تشغّله يدويًا:

### الطريقة السريعة (PowerShell كمسؤول)

```powershell
schtasks /create /tn "AI Daily" /tr "C:\Users\m\Desktop\ai_daily\run_daily.bat" /sc daily /st 08:00
```

ده هيسجّل مهمة اسمها "AI Daily" تشتغل كل يوم الساعة 8 الصبح. غيّر `08:00` للوقت اللي يناسبك.

### الطريقة بالواجهة الرسومية (Task Scheduler)

1. افتح **Task Scheduler** من قائمة Start.
2. **Create Basic Task** → اكتب اسم زي "AI Daily".
3. **Trigger**: اختر Daily وحدد الوقت.
4. **Action**: اختر "Start a program"، وحدد المسار لملف `run_daily.bat` في مجلد المشروع.
5. خلّص الـ Wizard.

### التأكد إنها شغالة

بعد ما تعدّي أول موعد مجدول، افحص `data/logs/<تاريخ>.log` و`data/drafts/<تاريخ>.txt` — لو فيهم محتوى بتاريخ اليوم، يبقى الجدولة شغالة صح.

## التشغيل الأوتوماتيكي بدون الحاجة لجهاز شغال (GitHub Actions)

الطريقة دي بتشغّل المشروع يوميًا على سيرفرات GitHub المجانية، **من غير ما تسيب أي جهاز شغال خالص**.

### الخطوات (لمرة واحدة بس)

**1) لو معندكش حساب GitHub:**
اعمل حساب مجاني من [github.com/signup](https://github.com/signup) (بس إيميل وكلمة سر).

**2) ارفع المشروع على GitHub:**
- ادخل [github.com/new](https://github.com/new)، اختار اسم للمستودع (مثلاً `ai-daily`)، خليه **Private** (عشان لو حطيت مفاتيح حساسة)، واعمل **Create repository**.
- في مجلد المشروع عندك، شغّل الأوامر دي (غيّر `YOUR_USERNAME` باسم حسابك):

```powershell
cd C:\Users\m\Desktop\ai_daily
git init
git add .
git commit -m "First commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-daily.git
git push -u origin main
```

(لو `git` مش متعرّف عليه، نزّل [Git for Windows](https://git-scm.com/download/win) الأول).

**3) (اختياري) لو عايز التلخيص بالـ AI يشتغل:**
- في صفحة المستودع على GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
- الاسم: `ANTHROPIC_API_KEY`، والقيمة: مفتاحك الحقيقي.
- من غيرها، الأتمتة هتشتغل عادي بمحتوى منظّف بس بدون تلخيص (زي المحلي بالظبط).

**4) فعّل الجدولة:**
مفيش خطوة إضافية! ملف `.github/workflows/daily.yml` موجود أصلًا في المشروع، وهيتفعّل تلقائيًا بمجرد ما ترفع المشروع على GitHub. افتراضيًا بيشتغل الساعة 8 صباحًا بتوقيت مصر تقريبًا (تقدر تغيّر الميعاد بتعديل السطر `cron` جوه الملف).

### للتجربة الفورية (بدون استنى الميعاد)

في صفحة المستودع: تبويب **Actions** → اختار "AI Daily" من القائمة الجانبية → زرار **Run workflow**.

### وين تشوف النتيجة؟

بعد كل تشغيلة، هتلاقي ملف نشرة جديد اتضاف تلقائيًا في `data/drafts/` جوه المستودع على GitHub — تقدر تفتحه من المتصفح أو تطبيق GitHub على الموبايل، تنسخ محتواه، وتلصقه في قناة واتساب.

## النشر الفعلي في قناة واتساب (اختياري، عبر WAHA)

⚠️ **تنويه:** ده استخدام غير رسمي لواتساب (WAHA بيشتغل فوق واتساب ويب، مش API رسمي من Meta). فيه احتمال (غير مؤكد) لحظر الرقم حسب حجم الاستخدام. استخدامه على مسؤوليتك.

### 1) نشر WAHA على Railway

1. اعمل حساب مجاني على [railway.com](https://railway.com) (تقدر تسجّل بحساب GitHub بتاعك مباشرة).
2. روح [railway.com/deploy/waha-api](https://railway.com/deploy/waha-api) ودوس **Deploy**.
3. وقت الإعداد، حدّد:
   - `WAHA_API_KEY`: كلمة سر قوية من عندك (احفظها، هتحتاجها بعدين).
   - `WHATSAPP_DEFAULT_ENGINE`: `NOWEB` (أخف على الموارد المجانية).
4. بعد ما ينتهي الـ Deploy، Railway هيديك رابط عام (مثال: `https://your-app.up.railway.app`).

### 2) ربط رقم واتساب بتاعك

1. افتح `https://your-app.up.railway.app/dashboard` في المتصفح.
2. سجّل دخول بمفتاح الـ API اللي حددته.
3. ابدأ جلسة (Session) جديدة، وهيظهرلك QR code.
4. من موبايلك: واتساب → **الأجهزة المرتبطة** → **ربط جهاز** → امسح الكود.

### 3) الحصول على معرّف القناة (Channel ID)

1. من نفس الـ Dashboard، دوّر على قائمة القنوات (Channels) المرتبطة برقمك.
2. انسخ الـ ID بتاع قناة "AI Daily" بتاعتك (شكله: `123456789012345678@newsletter`).

### 4) ضبط الإعدادات

**محليًا:** ضيف في ملف `.env`:
```
WAHA_BASE_URL=https://your-app.up.railway.app
WAHA_API_KEY=المفتاح-اللي-حددته
WHATSAPP_CHANNEL_ID=123456789012345678@newsletter
```

**على GitHub Actions (لو بتستخدم الأتمتة السحابية):** ضيف نفس الثلاث قيم كـ Secrets في **Settings → Secrets and variables → Actions** (بنفس الأسماء بالظبط).

من غير الإعدادات دي، المشروع هيفضل يشتغل عادي ويكتفي بحفظ نسخة محلية في `data/drafts/` بس.

## تشغيل الاختبارات

```bash
pytest
```

## الهيكل الحالي

```
ai_daily/
├── src/ai_daily/
│   ├── collectors/       # جمع المحتوى (RSS حاليًا، قابل للتوسع)
│   │   ├── base.py           # عقد BaseCollector
│   │   ├── rss_collector.py  # تطبيق RSS
│   │   └── factory.py        # بناء Collector مناسب من إعدادات المصدر
│   ├── processors/       # معالجة المحتوى
│   │   ├── base.py            # عقد BaseProcessor
│   │   ├── text_cleaner.py    # تنظيف HTML/مسافات
│   │   └── ai_summarizer.py   # تلخيص بالـ AI (اختياري)
│   ├── publishers/       # تجهيز/نشر النشرة
│   │   ├── base.py            # عقد BasePublisher
│   │   ├── formatting.py      # تنسيق نص النشرة
│   │   └── file_publisher.py  # حفظ كملف مسودة محلي
│   ├── storage/           # منع تكرار الأخبار
│   │   ├── base.py                  # عقد SeenItemsStore
│   │   └── json_seen_items_store.py # تطبيق ملف JSON
│   ├── models/             # هياكل البيانات المشتركة
│   │   ├── content_item.py    # عنصر محتوى واحد
│   │   └── source_config.py   # إعدادات مصدر واحد
│   ├── config.py           # قراءة sources.json و .env
│   └── main.py              # نقطة التشغيل: تربط كل الطبقات
├── config/
│   └── sources.json         # قائمة مصادر RSS
├── data/                     # بيانات مُولَّدة وقت التشغيل (متجاهَلة في git)
│   ├── seen_items.json          # سجل الروابط السابقة (منع التكرار)
│   └── drafts/<تاريخ>.txt       # نشرة اليوم الجاهزة للنشر
├── tests/                     # اختبارات كل طبقة + اختبارات تكاملية
├── pyproject.toml
├── requirements.txt
├── .env.example
└── .gitignore
```

## فلسفة التصميم

كل طبقة (Collectors, Processors, Publishers, Storage) مبنية خلف **عقد (Interface)**
عن طريق `ABC`، بحيث أي تطبيق جديد (مصدر Scraping بدل RSS، قاعدة بيانات حقيقية بدل
ملف JSON، واتساب API حقيقي بدل ملف مسودة...) يقدر يحل محل التطبيق الحالي من غير
ما يكسر باقي المشروع.
