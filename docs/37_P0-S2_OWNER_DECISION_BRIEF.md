# Owner Decision Brief – P0-S2: Standards Profile, Scope Phasing, Lightning Data, Validation, Differentiation

- **Document ID**: DOC-S2-001
- **Version**: 1.0
- **Date**: 2026-11-08
- **Prepared for**: Owner / Product decision-maker (via Environment A)
- **Prepared by**: Executor (B)
- **Status**: Decision brief – no final selections made; options and evidence presented for Owner
- **Base commit**: `24b11d140050f61c0081b002c879c693475d2a10` (last accepted P0-S1 commit)
- **Branch**: `arena/461d9c97-lightnin`
- **Input references**: P0-S1 report `docs/36_P0-S1_SOURCE_BENCHMARK_DISCOVERY_REPORT.md`; additional fetch/search runs during S2 (لیست کامل منابع در بخش ۵)

---

## 0. هدف این یادداشت

این یادداشت شواهدی را گرد می‌آورد تا مالک بتواند در مورد پنج محور زیر تصمیم بگیرد:

1. پروفایل استانداردها (کدام ویرایش، کدام پذیرش ملی، چگونه تعارض‌ها مدیریت شوند).
2. ترتیب عرضه ماژول‌ها (کدام حوزه‌ها اول، معیار پوشش چیست).
3. نقشه/دادهٔ صاعقه و سیاست آنلاین/آفلاین.
4. الزامات اعتبارسنجی مهندسی برای هر خانواده فرمول.
5. معیارهای تمایز محصول و نحوهٔ اندازه‌گیری آن‌ها.

این یادداشت **هیچ گزینه‌ای را قطعی نمی‌کند** و هیچ کدی را تغییر نمی‌دهد. هر نتیجه‌ای که با منابع در دسترس قابل اثبات نباشد با برچسب `UNVERIFIED` یا «نیازمند تصمیم/منبع مالک» مشخص شده است.

---

## 1. پروفایل استانداردها و حوزه قضایی

### ۱.۱ هسته بین‌المللی: IEC 62305، ویرایش 2024 (Ed.3.0)

| Part | عنوان | تاریخ انتشار | Edition | Pages | قیمت ناشر (CHF) | تغییرات کلیدی Ed.3 نسبت به Ed.2 | منبع |
|---|---|---|---|---|---|---|---|
| IEC 62305-1 | General principles | ۲۰۲۴-۰۹-۱۲ | **3.0** | ۱۵۳ | ۳۸۰ | ارجاع به IEC 62561 Annex D؛ types of loss با public relevance؛ frequency of damage برای سیستم‌های داخلی؛ surge currents برای SPD دقیق‌تر تعیین شده | webstore.iec.ch/en/publication/27136 |
| IEC 62305-2 | Risk management | ۲۰۲۴-۰۹-۱۲؛ **COR1: 2024-10-17**؛ **COR2: 2026-10-12** | **3.0** | ۲۵۶ | ۴۳۰ | single risk R (ترکیب تلفات جانی و آتش)؛ N_SG به‌جای N_G؛ TWS/IEC 62793 برای اقدامات پیشگیرانه موقت؛ ریسک مستقیم به افراد در فضای باز | webstore.iec.ch/en/publication/28137 + /101796 + /116918 |
| IEC 62305-3 | Physical damage and life hazard | ۲۰۲۴-۰۹-۱۲ | **3.0** | ۲۸۰ | ۴۳۰ | دو روش general و **simplified** برای separation distance بند ۶.۳؛ Annex C بازبینی‌شده؛ Annex D (جایگزین A سابق) برای جزئیات هوا-پایانه، بام سبز، ساختمان‌های بلند، نماها؛ تعریف جدید "electrically insulated LPS" | webstore.iec.ch/en/publication/33680 |
| IEC 62305-4 | Electrical & electronic systems (LEMP/SPD) | ۲۰۲۴-۰۹-۱۲ | **3.0** | ۲۷۰ | ۴۳۰ | Annex E (current-sharing modelling)، Annex F (PV installations)، Annex G (system-level tests)، Annex H (induced voltages در تأسیسات SPD-دار) | webstore.iec.ch/en/publication/29590 |

**پایداری (Stability Date):** هر چهار قسمت ۲۰۲۹ (یعنی تا آن تاریخ تجدیدنظر بعدی انتظار نمی‌رود).

**یادداشت در مورد COR2 برای بخش ۲:** نسخهٔ "corrected" در اکتبر ۲۰۲۶ منتشر شده و corrigendum ۱ در همین کپی ادغام گردیده. اگر نرم‌افزار با Ed.3 (2024) بدون COR2 طراحی شود، باید به‌صراحت در UI/اسناد ذکر شود که متن مرجع انتشار ۲۰۲۴ (بدون اصلاحات) است – یا به نسخهٔ اصلاحی ۲۰۲۶-۱۰ ارجاع داده شود. **تصمیم با مالک است.**

### ۱.۲ پذیرش‌های CENELEC (EN) و ملی اروپا

EN IEC 62305:2024 به‌عنوان استاندارد اروپایی در دست انتشار/اتمام انتشار در کشورهای مختلف است. ضمیمه DEHN Services (منبع SRC-DEHN-DESIGN در دفتر منابع زیر) فهرست زیر را در اوایل ۲۰۲۶ ارائه داده و به‌عنوان "country-specific adaptations of IEC 62305 Ed.3.0:2024" یاد می‌کند. تاریخ‌های دقیق از صفحهٔ VDE و همان PDF اخذ شده:

| کشور | نام استاندارد | تاریخ انتشار | ضمیمه/راهنمای ملی مهم |
|---|---|---|---|
| آلمان (DE) | **DIN EN IEC 62305-2/-3/-4 (VDE 0185-305-x)** | Part 2: ۲۰۲۶-۰۲؛ Part 3: **۲۰۲۵-۱۰**؛ Part 4: **۲۰۲۶-۰۲** | Part 3 بند ۶٫۳ گسترش‌یافته (رویکرد عمومی)، ساختمان‌های بلندتر از ۶۰ متر، بام سبز، national Sonderbedingung برای کلاس LPS، نقشه Ng آلمان در Supplement 2 |
| اتریش (AT) | OVE EN IEC 62305:2026 | ۲۰۲۶ | — |
| سوئیس (CH) | SN EN IEC 62305:2024 + SN 414022:2024 | ۲۰۲۴-۰۲ | SN 414022 راهنمای ملی |
| بریتانیا (UK) | BS EN IEC 62305:2024 (Parts 1,2,3,4) | Part 1: ۲۰۲۵-۰۲-۲۸ | **هشدار سیاستی BSI (مهم):** کمیتهٔ ملی بریتانیا توصیه می‌کند که سری سوم (Ed.3) به‌طور کامل پیاده شود؛ اجرای parts 1,3,4 بدون ارزیابی ریسک مطابق BS EN IEC 62305-2:2024 ایمن نیست. این بر الزام «همه یا هیچ» بودن بسته تأکید دارد. |
| فرانسه (FR) | NF EN IEC 62305:2024 | ۲۰۲۴ | برای Part 2 راهنمای INERIS/Alain Rousseau؛ NFC 17-102 (ESE) حوزه مجزایی است (در IEC 62305 به‌رسمیت شناخته نشده) |
| ایتالیا (IT) | CEI EN IEC 62305:2025-03 | ۲۰۲۵-۰۳ | Guida CEI 81-29 Ed.3 برای Part 3 |
| اسپانیا (ES) | UNE EN IEC 62305:2024 | ۲۰۲۴ | CTE DB SUA 8:2026 |
| هلند (NL) | NEN EN IEC 62305:2024 | ۲۰۲۴ | NPR1014:2009 (P3)، NPR8110:2024 (P4) |
| بلژیک (BE) | NBN EN IEC 6230:2024 | ۲۰۲۴ | ANPI guides |
| اسکاندیناوی (SE,NO,FI,DK) | SS/NEK/SFS/DS EN IEC 62305:2024 | ۲۰۲۴–۲۰۲۵ | NEK 320:2025 (NO) |
| لهستان/چک/اسلواکی/مجارستان | PN-/ČSN/STN/MSZ EN IEC 62305 | ۲۰۲۵ | — |
| امارات (AE) | BS EN 62305:2024 | ۲۰۲۴ | — |
| عربستان (SA) | SASO IEC 62305 | — | — |
| آفریقای جنوبی (ZA) | SANS EN IEC 62305:2025 | ۲۰۲۵ | — |

### ۱.۳ APAC

| کشور | استاندارد | تاریخ | یادداشت |
|---|---|---|---|
| سنگاپور (SG) | **SS 555:2018** | ۲۰۱۸ | هنوز مبتنی بر IEC 62305:2010 (Ed.2) است، نه 2024 |
| هند (IN) | **IS/IEC 62305:2024** | ۲۰۲۴ | بر اساس Ed.3 |
| چین (CN) | **GB/T 21714-2026** | ۲۰۲۶ (انتظار) | معادل‌سازی IEC 62305 |
| ژاپن (JP) | **JIS Z 9290** | — | `UNVERIFIED` نسخه دقیق و سال انتشار نیاز به بررسی بیشتر دارد |
| کره‌جنوبی (KR) | **KS C IEC 62305:2022** | ۲۰۲۲ | بر اساس Ed.2 (2010) می‌ماند تا به‌روزرسانی شود |
| تایلند (TH) | TISI 1586-2555 (Part 2) | ۲۰۱۲ | قدیمی |
| ویتنام (VN) | TCVN IEC 62305:2013 | ۲۰۱۳ | قدیمی |
| استرالیا (AU) | **AS 1768:2021** (جدا) | ۲۰۲۱ | ویرایش جدید استرالیا؛ نیوزلند هنوز **AS/NZS 1768:2007** را به‌کار می‌برد؛ تفاوت روش ریسک |
| NZ | AS/NZS 1768:2007 | ۲۰۰۷ | قدیمی |
| مالزی/اندونزی/فیلیپین | MS/SNI/PNS IEC 62305 | — | اتخاذ عمومی IEC |

### ۱.۴ قاره آمریکا

| کشور | استاندارد | سال | یادداشت |
|---|---|---|---|
| آمریکا (US) | **NFPA 780** (2023؛ در برخی منابع به ۲۰۲۵/۲۰۲۶ ارجاع داده می‌شود) + UL 96/96A:2023 | ۲۰۲۳/۲۰۲۵/۲۰۲۶ | روش نصب توصیفی، شعاع rolling sphere معمول **۱۵۰ ft ≈ ۴۶ متر** (نه ۲۰/۳۰/۴۵/۶۰ متری IEC)؛ Annex L ارزیابی ریسک ساده‌شده؛ از نظر فدرال اختیاری اما توسط کدهای ایالتی/بیمه/نوع کاربری الزامی می‌شود. `UNVERIFIED` نسخه ۲۰۲۵/۲۰۲۶ در چه تاریخی نهایی شده و چه تغییراتی دارند. |
| کانادا (CA) | **CSA B72:2020** | ۲۰۲۰ | — |
| برزیل (BR) | **ABNT NBR 5419:2025** | ۲۰۲۵ | به‌روزرسانی به Ed.3 انتظار می‌رود |
| مکزیک (MX) | NMX-J-549-ANVE:2005 | ۲۰۰۵ | قدیمی |
| کلمبیا (CO) | NTC 4552 | — | `UNVERIFIED` نسخه |

### ۱.۵ استانداردهای حوزه‌ای/تجهیزاتی که با IEC 62305 هم‌پوشانی دارند اما جایگزین آن نیستند

| استاندارد | حوزه | محدوده | رابطه با IEC 62305 |
|---|---|---|---|
| IEC 62561 Parts 1-8 (LPSC) | قطعات LPS | الزامات مؤلفه‌ها (میله‌ها، اتصالات، هادی‌ها، الکترودها، جداکننده‌ها، SPD-mounts، اجزای LPS عایق) | ارجاع هنجاری (normative) از IEC 62305-3/-4؛ باید در کتابخانه مؤلفه‌ها در نظر گرفته شود |
| IEC 61643-11/-12/-21/-22/-31/-32 | SPDها (فشارضعیف، PV DC، تلکام، PV-side) | الزامات محصول و انتخاب | ارجاع از IEC 62305-4 برای انتخاب/هماهنگی SPD |
| **IEC 61400-24:2019 + AMD1:2024 (Ed.2.1)** | توربین‌های بادی (WTG) و مزرعه باد | ریسک‌پذیری خاص توربین (upward lightning، چرخش پره‌ها، گیرباکس، یاتاقان‌ها، LPZ داخل توربین، SPD روی کنترل و قدرت) | محصول-محور؛ به IEC 62305 ارجاع می‌دهد اما الحاقات/آزمون‌های مختص WTG دارد |
| **IEC 62548:2016 / IEC 62548-1:2023+AMD1:2025** | آرایه‌های PV | الزامات DC-side، اتصال، SPD، حفاظت صاعقه/اضافه‌ولتاژ (بند ۶.۶) | مکمل IEC 62305 برای نیروگاه‌های PV؛ همچنین IEC TS 62738 (PV ground-mounted) و IEC TR 63227 (surge در PV) |
| **IEEE Std 998-2012 (Direct Lightning Stroke Shielding of Substations)** | پست‌ها و شبکه | shielding (EGM/rolling sphere/Mousa/Eriksson)؛ شعاع RSM پست وابسته به BIL/سطح ولتاژ (مثلاً ۲۴ m در Horizon Power، نه شعاع IEC 62305) | در پست‌ها به‌جای شعاع‌های کلاس I–IV IEC از شعاع وابسته به جریان/استحکام عایقی استفاده می‌کند |
| **IEEE Std 80-2013 (AC Substation Grounding)** | اتصال زمین پست | touch/step voltage mesh/step، GPR (برای خطای AC فرکانس‌قدرت) | IEEE صریحاً می‌گوید surgeهای صاعقه خارج از حوزه این استاندارد است |
| **ITU-T K.39/K.40/K.46/K.47** | تجهیزات/سایت‌های تلکام و خطوط فلزی | ریسک، LEMP در مراکز تلکام، خطوط مسی متقارن، خطوط در برابر برخورد مستقیم | برای دامنه تلکام کاربرد دارد |
| NFC 17-102 / UNE 21.186 | ESE (Early Streamer Emission) terminals | فرانسه/اسپانیا | این فناوری در IEC 62305 به‌رسمیت شناخته **نمی‌شود**. پشتیبانی از آن به‌معنی گسترش دامنه محصول است و ریسک‌های اعتباری/مهندسی دارد. |

### ۱.۶ گزینه‌های تصمیم برای پروفایل استانداردها (انتخاب با مالک)

**پرسش تصمیم P1** – کدام استاندارد/ویرایش به‌عنوان **مبنای محاسباتی نخستین** انتخاب شود؟

| گزینه | شواهد | پیامدها |
|---|---|---|
| **A. هسته IEC 62305:2024 Ed.3.0 (انتشار پایه ۲۰۲۴-۰۹-۱۲، بدون COR2)** | ناشر IEC این نسخه را انتشار ۲۰۲۴ می‌نامد؛ اکثر پذیرش‌های ملی اروپایی ۲۰۲۴–۲۰۲۶ بر همین مبناست | باید در UI و گزارش ذکر شود که COR1 در محاسبات لحاظ شده یا نه (IEC می‌گوید COR1 در نسخه فعلی کاتالوگ PUB ادغام شده)؛ COR2 اکتبر ۲۰۲۶ درصورتی‌که نرم‌افزار قبل از آن منتشر شود به‌روزرسانی می‌طلبد |
| **A′. هسته IEC 62305:2024 + COR2:2026-10** | آخرین نسخه اصلاح‌شده در وب‌استور IEC | تأخیر تا مهیا شدن متن/خرید استاندارد؛ از روز اول با آخرین اصلاحات هم‌خوانی دارد |
| **B. Ed.2 (2010) برای سازگاری با سنگاپور SS 555:2018، AS/NZS 1768:2007، KS C IEC 2022، TCVN 2013** | این کشورها هنوز Ed.3 را کامل نپذیرفته‌اند | نیاز به پایگاه داده جداگانه/تعویض جداول/نسخه‌ها؛ R_SG و single risk در Ed.2 متفاوت است (R1–R4 جداگانه، N_G نه N_SG) |
| **C. NFPA 780 به‌عنوان پایه برای بازار آمریکا** | منابع USA از جمله Skytree/Anvilfield اشاره می‌کنند که NFPA 780 روش دیگری (توصیفی‌تر) دارد و RSM شعاع ثابت ۱۵۰ فوت می‌گیرد | شعاع rolling sphere و قواعد فاصله‌گذاری air terminal متفاوت از IEC است. پشتیبانی NFPA 780 ماژول جداگانه می‌خواهد |
| **D. پشتیبانی هم‌زمان چند استاندارد (IEC 2024 + IEC 2010 + NFPA 780 + VDE national annex)** | DEHNrisk/DEHNsupport ابزار چند نسخه‌ای است؛ BSI هم می‌گوید سری باید کامل اجرا شود | محدوده کار در نسخهٔ اول بسیار بزرگ می‌شود؛ ریسک خطا در پیاده‌سازی افزایش می‌یابد |

**توصیه غیرالزام‌آور مجری (که تصمیم‌گیرنده نیست):** برای نسخه اول، گزینه **A (IEC 62305:2024 Ed.3.0، انتشار ۲۰۲۴، ذکر وابستگی نسخه corrigenda)** به‌عنوان هسته با معماری داده‌ای که اضافه‌کردن «پروفایل استاندارد» دیگر (national annex، NFPA، Ed.2) را در نسخه‌های آتی ممکن می‌سازد. اما انتخاب با مالک است.

**پرسش تصمیم P2** – کدام پذیرش‌های ملی/صنعتی در فاز ۱ باید تست شوند؟
- نمونه‌ها: DIN EN/VDE (DACH)، BS EN (UK)، NF EN (FR)، AS/NZS یا AS 1768 (AU)، NFPA+UL (US)، CSA B72 (CA)، GB/T (CN)، KS C IEC (KR)، JIS (JP)، IS/IEC (IN)
- پیامد انتخاب هر کدام: دسترسی به ارزش‌های جدول/ضمیمه ملی و نیاز به آزمون/صحت‌سنجی با مهندس/مثال محلی

---

## 2. ترتیب‌بندی دامنه محصول

### ۲.۱ دامنه‌های تأییدشده مالک (از S0/S1)
- ساختمان‌ها و تأسیسات عمومی/صنعتی
- پست و شبکه برق
- Transients / LEMP / SPD هماهنگی
- نیروگاه‌های PV (خورشیدی)
- نیروگاه‌های بادی (wind turbines)
- تجهیزات و سایت‌های مخابراتی
- (مفهوم کلی) تجهیزات در معرض صاعقه

### ۲.۲ تفکیک نوع استاندارد

| نوع استاندارد | نمونه‌ها | کاربرد در نرم‌افزار |
|---|---|---|
| **سازه‌محور (structure-based)** | IEC 62305-x، BS EN/DIN EN/AS/NZS/GB/T، NFPA 780 | طراحی LPS (هوا-پایانه، هادی پایین، اتصال زمین، جداسازی)، ریسک ساختمان، LPZ/SPD برای تأسیسات ساختمان |
| **شبکه/پست** | IEEE 998 (shielding)، IEEE 80 (grounding/safety)، IEC 62305 (هم‌پوشانی)، Horizon Power PCD | شعاع RSM وابسته به BIL (نه LPL IEC)؛ touch/step AC fault؛ earthing mesh برای پست |
| **محصول/صنعت (product-based)** | IEC 61400-24 (باد)، IEC 62548/IEC 61463-32 (PV)، ITU-T K-series (تلکام)، NFC 17-102/UNE 21.186 (ESE) | باد: upward lightning و LPZ داخل توربین و SPDهای مخصوص؛ PV: DC-side SPD و string/combiner؛ تلکام: surge در خطوط مسی و مراکز مخابراتی |

تمایز کلیدی: IEC 62305 برای "سازه‌های معمولی" است و برای پست/توربین/آرایه‌های PV/تلکام به الحاقات یا استانداردهای محصول مجزا نیاز است. پیاده‌سازی همه در "یک مدل یکپارچه" باید اختلاف پارامترها را به‌صورت صریح مدیریت کند.

### ۲.۳ قابلیت (capability) ماژول‌ها – نامزدهای ترتیب عرضه

قابلیت‌های زیر پیشنهاد می‌شوند؛ **انتخاب ترتیب و حذف هیچ‌کدام در نهایت با مالک است**.

| ماژول | قابلیت | به هسته IEC 2024 وابسته؟ | استانداردهای اضافی لازم | داده بیرونی لازم؟ |
|---|---|---|---|---|
| **M1 – Risk Engine** | ارزیابی ریسک R و F (Ed.3) بر اساس N_SG، انتخاب LPL | هسته | IEC 62305-2 Ed.3 (+ COR2 اگر گزینه A′) | N_G/N_SG (به بخش ۳) |
| **M2 – External LPS Geometric Core** | RSM پیوسته (۳D)، mesh، protective angle روی ساختمان | هسته | IEC 62305-3 §5.2 + Annex D | مدل سه‌بعدی ساختمان (IFC/CAD) |
| **M3 – Separation Distance** | s=ki·(kc/km)·l در دو سطح (simplified و general/nodal) | هسته | IEC 62305-3 §6.3 (general+simple) | نتایج M2 / network graph |
| **M4 – Earthing Type A/B** | طراحی اولیه حلقه/میله، مقاومت هدف ≤10 Ω (مقدماتی) | هسته | IEC 62305-3 §5.4 | مقاومت خاک ورودی |
| **M5 – LPZ / Coordinated SPD** | LPZ boundaries، SPD Type/مکان، I_imp/In/Up selection و هماهنگی | هسته | IEC 62305-4 + IEC 61643-12/32 | ورودی‌های سیستم (سرویس‌ها) |
| **M6 – Reporting/Audit** | گزارش امضاشده با trace، HMAC، immutable trail | هسته | مستقل | – |
| **M7 – Substation Pack** | RSM با شعاع وابسته به BIL (IEEE 998) + touch/step AC (IEEE 80) | اختیاری | IEEE 998-2012، IEEE 80-2013 (هشدار حوزه کاربرد) | BIL/ولتاژ پست، مقاومت خاک |
| **M8 – PV Pack** | تقسیم جریان PV Annex F، DC-side SPD selection IEC 61643-32، توصیه‌های سیم‌کشی | اختیاری | IEC 62305-4 Annex F، IEC 62548-1، IEC TR 63227 | طرح اتصال رشته‌ها/اینورتر |
| **M9 – Wind Pack** | Exposure برای توربین، upward lightning، LPZ داخل توربین، SPDs بر اساس محیط و مسیر | اختیاری | IEC 61400-24:2019+AMD1:2024، IEC 61400-23 (آزمون) | ارتفاع هاب، قطر روتور، موقعیت مکانی |
| **M10 – Telecom Pack** | LPZ/MCBN در مراکز تلکام، حفاظت خطوط مسی و SPDهای سیگنال | اختیاری | ITU-T K.39/K.40/K.46/K.47، IEC 61643-21 | توپولوژی خطوط ورودی |
| **M11 – National Annex Profiles** | مقادیر/ضمیمه‌های مختص VDE، BSI، NFC، AS/NZS | بسته به بازار | ناسیونال ضمیمه‌ها | – |
| **M12 – NFPA 780 Profile** | RSM 150 ft، قواعد spacing توصیفی، Annex L ارزیابی ساده | اختیاری (بازار آمریکا) | NFPA 780 (2023 یا نسخه جدیدتر) | – |

### ۲.۴ گزینه‌های ترتیب عرضه (غیرقطعی)

| گزینه | ترتیب پیشنهادی | معیار پوشش قابل‌اندازه‌گیری | مزیت | محدودیت |
|---|---|---|---|---|
| **Ph.1 – هسته ساختمان (M1+M2+M3+M4+M5+M6)** | ریسک، هوا-پایانه، جداسازی، اتصال زمین، SPD پایه، گزارش | صدور یک گزارش کامل IEC 62305:2024 Ed.3 برای ساختمان با هر 4 پارامتر | چرخه طراحی اصلی معمول را پوشش می‌دهد | بدون پست/باد/PV/تلکام/NFPA |
| **Ph.2 – بازارهای خاص (M7/M8/M9/M10)** | زیرماژول‌های صنعت | اعتبارسنجی در برابر مثال‌های استاندارد صنعتی | تمایز صنعتی | وابسته به مجوز/تست/مثال بیشتر |
| **Ph.3 – ملی/آمریکا (M11+M12)** | پروفایل ملی + NFPA 780 | اجرای محک با اسناد هر کشور/استاندارد | ورود به بازار آمریکا/آسیا | بار نگهداری پروفایل‌ها |

**معیارهای قابل‌اندازه‌گیری پوشش پیشنهاد اولیه (نیاز به تأیید مالک):**
- برای Ph.1: یک مثال ساختمان پایه (مکعب ۳۰×۲۰×۱۰ با LPL معین) باید خروجی‌های عددی را با مرجع/benchmark منتخب بازتولید کند (به بخش ۴ رجوع کنید).
- برای هر ماژول اضافه: حداقل ۱ مثال عددی با استاندارد هدف باید قبل از انتشار بازتولید شود.
- برای هر پروفایل ملی: پیوست/ضمیمه ملی باید همهٔ انحرافات عددی/رویه‌ای از هسته IEC 62305 را لیست کند.

---

## 3. نقشه، داده صاعقه و سیاست آنلاین/آفلاین

### ۳.۱ پارامترهای مورد نیاز برای ریسک (مطابق IEC 62305-2 و IEC 62858)

- **N_G (ground flash density)**: تعداد flashes/km²/year مربوط به CG (cloud-to-ground) – مورد استفاده در ویرایش ۲ و ملی‌های بر مبنای آن
- **N_SG (ground strike-point density)**: تعداد strike points/km²/year – **مورد استفاده در IEC 62305-2 Ed.3:2024** (جایگزین N_G در ارزیابی ریسک)
- ضریب‌های مکانی/محیطی (C_d, C_e)
- دوره آماری توصیه‌شده: ≥ 10 سال طبق IEC 62858

**IEC 62858:2019 Ed.2** (https://cdn.standards.iteh.ai/samples/102016/...، پیش‌نمایش آزاد) الزامات عملکرد LLS برای محاسبه N_G/N_SG را تعیین می‌کند:
- Flash detection efficiency (DE) ≥ **80%** CG flashes در منطقه
- Location accuracy (LA) median error < **500 m** در interior شبکه
- Thunderstorm days یا flash counters دیگر توصیه **نمی‌شود**؛ در مناطق بدون LLS، N_G/NSG از برون‌یابی/مناطق مجاور باید برآورد شود

### ۳.۲ منابع داده صاعقه – فهرست مقایسه‌ای (نامزدهای اصلی)

| منبع | نهاد | پوشش | کمیت | تفکیک افقی | تفکیک زمانی | تاریخچه | کیفیت (DE/LA) | دسترسی/فرمت | شرایط مجوز تجاری | هزینه |
|---|---|---|---|---|---|---|---|---|---|---|
| **Vaisala GLD360** | Vaisala (commercial) | جهانی | strokes/flashes (CG+IC) | حدود ۵–۱۰ km میانه، بسته به منطقه | real-time (<60s) | از ۲۰۰۹ | DE >70% شمالگان، LA ≤5 km | GRIB2 Level5 NOAA (مشتق‌شده، بدون CG مستقیم در نسخه عمومی)؛ دسترسی تجاری مستقیم از Vaisala | GRIB2 L5 عموم مجاز؛ داده خام Vaisala قرارداد تجاری می‌خواهد | `UNVERIFIED` هزینه سالانه |
| **Vaisala NLDN** | Vaisala | آمریکا/کانادا | CG flashes | ~1 km | real-time | از ۱۹۸۹ | DE >90%, LA ~250 m | از Vaisala/CoreLogic قرارداد | قرارداد تجاری | `UNVERIFIED` هزینه |
| **EUCLID** | اتحادیه اروپا (شبکه اروپایی) | اروپا | CG+IC | ۱۰۰–۲۰۰ m | real-time | از ۲۰۰۱ | DE بالا، LA ~100-200 m | فقط اعضا/قرارداد با اپراتورهای ملی | قرارداد تجاری | `UNVERIFIED` هزینه |
| **ATDnet** | UK Met Office | اروپا/جهان VLF | flashes (مختلط CG+IC) | 2-5 km | real-time | از ۱۹۸۷ | انتشارات علمی: ۵–۱۰ km LA, 70-90% DE | داده خام تجاری/ملی؛ خلاصه انتشارات علمی آزاد (PAP-ANDERSON-KLUGMANN-2014، PAP-ENNO-2019) | قرارداد با Met Office | `UNVERIFIED` |
| **Météorage / TORRO** | اپراتورها | فرانسه/اروپا | CG | ~100 m | real-time | دهه‌ها | بالا در اروپای غربی | قرارداد تجاری | قرارداد تجاری | `UNVERIFIED` هزینه |
| **Earth Networks (Total Lightning / WeatherBug)** | Earth Networks (commercial) | جهانی (شبکه خصوصی) | in-cloud+CG | `UNVERIFIED` | real-time | حدود ۲۰ سال | `UNVERIFIED` | SaaS API | تجاری | `UNVERIFIED` هزینه |
| **WWLLN** | دانشگاه‌ها | جهانی (VLF) | strokes | ده‌ها km | real-time | از ۲۰۰۳ | DE lower, strong strokes only | داده خام: $600/year/academic (به ESSD 2021 مرجع)؛ climatology رایگان در Zenodo (WGLC) | WGCC برای تحقیق آزاد (CC-BY)؛ داده خام هزینه دارد | $600/year academic; commercial `UNVERIFIED` |
| **WGLC (Kaplan&Lau)** | دانشگاه/ESSD | جهانی climatology | strokes/km²/year | 0.5° و 5 arc-min | روزانه/ماهانه/سالیانه | ۲۰۱۰–۲۰۱۹+به‌روزرسانی | adjusted for DE | Zenodo (https://doi.org/10.5281/zenodo.4774528) | CC-BY (تحقیقاتی) | رایگان برای تحقیق |
| **GLM (GOES-R / LIS/ISS)** | NASA/NOAA | جهانی/اقماری + GOES نیم‌کره آمریکا | total lightning (IC+CG) | ~8-12 km | ۲۰ هرتز | از ۲۰۱۷ (GLM) | optical (فاقد CG discrimination دقیق) | public daac/NASA | آزاد (NASA) | رایگان |
| **NOAA GRIB2 Lightning Strike Density (Level 5)** | NOAA/Ocean.Weather.gov | جهانی | strike density (strikes/m²/s) on 8 km grid | 8 km | 15/30 min | چند سال | بر پایه GLD360/NLDN، مشتق‌شده | GRIB2 آزاد (public) | NOAA Level5 LDP: عمومی | رایگان |
| **NCEI SWDI County/State Summaries** | NOAA/NCEI | ایالات متحده | CG flash summaries | county/state/tile | روزانه | دهه‌ها | مبتنی بر NLDN | REST/SWDI services | عمومی | رایگان |
| **TOVAS / NASA POWER / IMERG** | NASA | هواشناسی، فاقد صاعقه | — | — | — | — | — | — | — |
| **نقشه‌های ملی (مثلاً VDE Supplement 1 برای آلمان، GIMELEC France, …)** | اپراتورها/مؤسسات ملی | کشورهای خاص | N_G/N_SG | مختلف | چندساله | متغیر | معمولاً مبنای محلی | PDF نقشه یا سرویس | معمولاً عمومی/آزاد برای ارجاع در جدول، بدون توزیع انبوه | رایگان |
| **ورودی دستی توسط کاربر/مهندس** | کاربر | هر کشور/منطقه | مقدار عددی N_G/N_SG به‌همراه مبدأ/تاریخ | N/A | N/A | N/A | N/A | کاربر وارد می‌کند | در نرم‌افزار | رایگان |

### ۳.۳ گزینه‌های سیاست نقشه و آنلاین/آفلاین (انتخاب با مالک)

**پرسش P3 – سیاست داده مکانی:**

| گزینه | پیامدها |
|---|---|
| **D1 – آفلاین کاملاً، بدون سرویس نقشه/داده پویا** | کاربر N_G/N_SG را دستی وارد می‌کند یا از جدول ملی ثابت انتخاب می‌کند. بدون نیاز به اینترنت. ساده و تضمین کار کردن در محیط‌های بسته/رایانه‌های با security policy سخت. |
| **D2 – آفلاین با پایگاه داده N_G/N_SG نصب‌شده (cache شده)** | یک یا چند منبع داده (مثلاً WGLC climatology یا GRIB2 NOAA، یا نقشه‌های ملی) را در نصب یا asset همراه محصول قرار می‌دهد. نیاز به به‌روزرسانی سالانه دارد. |
| **D3 – آنلاین اولیه (API هنگام محاسبه ریسک)** | محاسبه ریسک را به وجود اینترنت منوط می‌کند؛ کاربر می‌تواند از آخرین داده بهره ببرد. مشکل در محیط‌های آفلاین. |
| **D4 – ترکیبی (پیش‌فرض دستی با امکان درخواست API و امکان cache)** | کاربر همیشه می‌تواند N_G/N_SG را دستی وارد کند (اجازه کار آفلاین)؛ وقتی اینترنت باشد می‌تواند از یک API انتخابی داده بکشد و نتیجه را cache کند. پیچیدگی پیاده‌سازی بیشتر اما انعطاف بالا. |

**پرسش P4 – کدام منبع(ها) برای API پیش‌فرض استفاده شوند؟**
- نامزدها: سرویس Vaisala GLD360 commercial API (نیازمند قرارداد/مجوز)، EUCLID API برای اروپا (نیازمند قرارداد)، NOAA GRIB2 (رایگان اما رزولوشن پایین/فاقد CG/flash تفکیک دقیق برای risk per IEC 62858)، WWLLN (دانشگاهی/هزینه سالانه کم برای non-commercial)، WGLC climatology (رایگان، تکرارپذیر)، NASA GLM (فاقد CG جدا)، national services (مانند Météorage، ATDnet).
- نکته مهم IEC 62858: برای به‌دست‌آوردن N_G/N_SG معتبر برای risk، به DE ≥80% و LA ≤500 m نیاز است؛ **بسیاری از سرویس‌های آزاد این کیفیت را نداشته و لازم است در UI و گزارش به‌عنوان "مقادیر تقریبی" یا "منبع تأییدنشده" علامت‌گذاری شوند.**

---

## ۴. الزامات اعتبارسنجی مهندسی به ازای هر خانواده فرمولی

اصول این بخش بر پایه این تمایز است که «منبع پیدا نشد» ≠ «منبع وجود ندارد» و هر خانواده فرمولی برای پذیرش نیازمند سه چیز است:
1. متن استاندارد/مجوز مرجع (برای مقادیر عددی قطعی).
2. یک یا چند benchmark عددی بازتولیدپذیر (ورودی/خروجی معلوم، با واحد، منشأ و مجوز بازنویسی).
3. جایی که فرمول از سوی استاندارد تجویز نشده (مانند Y·V=I یا segment-by-segment)، ارجاع مهندس مستقل یا مستند توجیه روش.

| خانواده فرمولی | متن دارای مجوز لازم | نامزد benchmark بازتولیدپذیر | وضعیت در P0-S1 | شکاف |
|---|---|---|---|---|
| RSM پیوسته و رابطه R=10·I^0.65 | IEC 62305-3 Ed.3 §5.2، Annex D | (a) SRC-REUVEN-RSM (R/h/rp/A تک‌میله)؛ (b) OSS-LPO commit `927f1db` (3D)؛ (c) Horizon Power PCD (شعاع 24m و مثال) | پارامترها SECONDARY SUPPORT | نیاز به بازتولید عددی با RSM مستقل/مثال کتابچه DEHN LPG ۲۰۱۴ |
| جداول ki/km/kc simplified | IEC 62305-3 Ed.3 Tables/Annex C | (a) DEHN LPG 2014 جداول (ki/km/kc)؛ (b) DEHN slides 2013 (نسخه 2010)؛ (c) Indelec/THOR جداول (کیفری) | SECONDARY SUPPORT | نیاز به مقایسه نسخه 2024 جدول‌ها با 2010 (هرگونه تغییر در مقادیر نیاز به بررسی با خرید استاندارد دارد) |
| Separation distance general/simplified (شامل §6.3) | IEC 62305-3 Ed.3 §6.3 و Annex C | (a) DEHN Distance Tool توصیف در LPG 2014؛ (b) PAP-ZISCHANK-ICLP mesh/metal-roof؛ (c) مثال‌های DEHN slides | SECONDARY SUPPORT | مثال عددی با general method (رویکرد گرهی) باید با مثال مرجع تطبیق داده شود (منبع در دسترس: DEHN Distance Tool خروجی، اما خروجی تولیدکننده است و باید cross-check شود) |
| نودال ادمیتانس Y·V=I برای kc | برای اعتبارسنجی نهایی: نتیجه باید با Annex C برای موارد ساده سازگار شود | (a) DEHN LPG sec 3.3.2.1 nodal analysis؛ (b) MoM/کدهای میدانی در PAP-ZISCHANK-ICLP | روش عددی اعمال‌پذیر (توسط DEHN تأیید عملی شده) | نیاز به تست تطبیق با موارد ساده kc؛ پیاده‌سازی باید در موارد ساده به همان kc جدول ۱۲ برسد؛ محدودیت برای سقف فلزی در Zischank به‌صراحت مستند شود |
| تعمیم قطعه‌به‌قطعه `s(P)=ki·Σkcj/kmj·lj` | **در منابع در دسترس صراحتاً به IEC نسبت داده نشد** | DEHN note "use the lower value for km" برای مواد سری | UNVERIFIED / نامزد با توجیه داخلی | نیاز به توجیه مهندسی (طراح) یا نشان دادن معادل با فرمول استاندارد وقتی km ثابت و kc ثابت باشد؛ باید به‌عنوان "general method (تعمیم)" در UI/گزارش علامت‌خورده و محدودیتش مستند شود |
| پارامترهای جریان Berger/IEC 62305-1 | IEC 62305-1 Ed.3 جداول ۲۰۲۴ | DEHN LPG جدول پارامترها؛ Heidler 2008 | SECONDARY SUPPORT (نسخه 2010/preview) | بررسی جدول‌های ۲۰۲۴ در صورت دسترسی رسمی |
| R1-R4 (old) / R+F (Ed.3) | IEC 62305-2 Ed.3 | DEHNrisk (vendor)؛ LARS (قدیمی 2014)؛ LIRA paper (PAP-LIRA-ICLP-2012) | UNVERIFIED (فرمول) | خرید/دسترسی به متن استاندارد ۲۰۲۴ یا LIRA/LARS outputs برای sanity-check |
| Earthing Type A/B | IEC 62305-3 §5.4 | DEHN LPG earthing tool sec 3.3.3 | SECONDARY SUPPORT (روش کلی) | مثال عددی با مقاومت اندازه‌گیری‌شده |
| IEEE 80 touch/step (AC) | IEEE Std 80-2013 | Windfarmbop مثال ۱۱۵ kV؛ ecalpro/firgelliauto calculators | SECONDARY SUPPORT | مستندسازی صریح حوزه (AC fault، نه impulse)؛ به‌عنوان هشدار در ماژول پست ظاهر شود |
| IEEE 998 shielding (RSM/EGM/Mousa/Eriksson) | IEEE Std 998-2012 | Horizon Power PCD (24 m)؛ Brandon (Vaisala) paper | SECONDARY SUPPORT (مثال Horizon) | نیاز به حداقل دو مثال بازتولیدپذیر از پست‌های متداول |
| SPD LPZ selection/هماهنگی | IEC 62305-4 Ed.3 + IEC 61643-x | SRC-THOR/SRC-INDELEC/SRC-OBO tables | SECONDARY SUPPORT (جدول‌های کیفی) | قاعده ۱۰m به‌عنوان "rule of thumb (نیازمند تأیید)" علامت‌خورده تا بند استاندارد یافت شود |
| Wind turbine (IEC 61400-24) | IEC 61400-24 Ed.2.1 | STD-IEC-61400-24 preview | `UNVERIFIED` مثال کاربردی | دسترسی به راهنمای OEM (مثلاً Siemens Gamesa/Vestas) به‌صورت عمومی در این پژوهش یافت نشد |
| PV (IEC 62548/Annex F) | IEC 62548-1 Ed.2، IEC 62305-4 Annex F, IEC TR 63227 | SRC-DEHN-LPG-2014 (مثال‌های DC SPD) | SECONDARY SUPPORT (Annexes) | دسترسی به IEC TR 63227 یا PV-specific example |
| Telecom (ITU-T K-series) | K.39/K.40/K.46/K.47 | K.46 PDF فرمول Ki/Ks | PARTIAL | K.39/K.47 عمیقاً بررسی نشد |
| N_G/N_SG data integration | IEC 62858:2019 Ed.2 | WGLC climatology, NOAA GRIB2, EUCLID/Vaisala کیفیت شرط | PARTIAL | مستندسازی کیفیت داده هر منبع در مقابل نیازمندی‌های 80%/500m IEC 62858 |

---

## ۵. معیارهای تمایز قابل‌اندازه‌گیری (نامزدها)

این معیارها پیشنهادهای قابل‌بحث هستند؛ **مالک معیار نهایی را انتخاب می‌کند**. هیچ‌کدام به‌خودی‌خود امتیاز نیست، بلکه یک روش اندازه‌گیری ارائه می‌دهند.

| گزینه تمایز | چگونه اندازه‌گیری شود | پیامد | محدودیت |
|---|---|---|---|
| **DI-1: یکپارچه‌سازی End-to-End ریسک → LPS → جدا‌سازی → SPD → گزارش** | آیا می‌توان با ورودی‌های ساختمان/مکان تا گزارش نهایی بدون تعویض ابزار رفت؟ شمارش مراحل ابزار در مقایسه با زنجیره رقیب (مثلاً DEHNrisk+DEHNdistance+DEHNsupport + نقشه دستی + CAD) | مسیر کاربری را کوتاه می‌کند | به کیفیت یکپارچگی بستگی دارد؛ نقطه‌ضعف ممکن است دقت در یک بخش باشد |
| **DI-2: پیوسته (continuous) بودن 3D-RSM در مقابل نمونه‌برداری نقطه‌ای** | شمارش نمونه‌هایی که RSM نقطه‌ای fail می‌دهد اما گواهی پیوسته pass (یا برعکس)؛ ارجاع به OSS-LPO که همین تمایز را مستند می‌کند | بهبود اعتمادپذیری برای سطوح پیچیده؛ ریسک "چند نقطه گم‌شود" را کم می‌کند | بار محاسباتی بالاتر |
| **DI-3: آف‌لاین اول بودن** | کار کردن بدون اینترنت در یک محیط قطع‌شده (air-gapped) و بدون تماس تلفن‌خانه طی محاسبه کامل یک نمونه پروژه | قابلیت استفاده در محیط‌های محرمانه صنعتی/دولتی | پایگاه داده/نقشه آفلاین نیاز است که به‌روز شود |
| **DI-4: رد حسابرسی قابل‌اثبات (immutable trace + HMAC در DOC-DB-001)** | هر مقدار میانی در گزارش قابل‌ردیابی تا استاندارد/جدول/ورودی کاربر باشد؛ HMAC روی گزارش تغییرات بعدی را تشخیص دهد | مزیت برای مهندسان مسئول/بازرس/بیمه | پیچیدگی پیاده‌سازی گزارش |
| **DI-5: گراف ادمیتانس برای kc (جدا‌سازی در ساختمان‌های پیچیده)** | سازگاری خروجی kc برای توپولوژی‌های ساده با جدول Annex C (باید یکسان شود)؛ برای mesh/roof-metal مقایسه با نتیجه DEHN Distance Tool/Zischank | در ساختمان‌های بزرگ/پست‌ها تمایز ایجاد می‌کند | نیاز به اعتبارسنجی اضافی (به بخش ۴) |
| **DI-6: CAD/IFC/BIM import/export بومی** | پوشش فرمت‌ها (DWG/DXF/IFC/glTF) و تعداد خطا در import فایل‌های نمونه | حذف مراحل دستی CAD | تست مجموعه فایل‌های نمونه می‌خواهد |
| **DI-7: پروفایل چند استاندارد در پایه** | یک پروژه را می‌توان هم‌زمان با دو استاندارد (مثلاً IEC 2024 + NFPA 780) اجرا و نتایج را مقایسه کرد | برای مشاورانی که در چند حوزه قضایی کار می‌کنند | پیچیدگی maintenance؛ ریسک نتایج به‌ظاهر متناقض |
| **DI-8: بسته‌های صنعتی در نسخه ۱ (باد/PV/پست/تلکام)** | تعداد ماژول‌های صنعتی خارج از "ساختمان عمومی" که در نسخهٔ ۱ پشتیبانی می‌شوند | تمایز در بازار صنعتی | بار اعتبارسنجی |
| **DI-9: داده‌های اقلیمی آزاد/باز قابل‌تولید** | شفافیت در اینکه عدد N_G/N_SG از کجا آمده (مبدأ، تاریخچه، کیفیت DE/LA)، امکان override | اعتماد مهندسی؛ تکرارپذیری علمی | نیاز به مستندسازی/metadata |

**احتیاط مهم:** تمایز از رقبا با مطالعه نسخه‌های جاری DEHN/INGESCO/ecalpro/OSS-LPO و... باید به‌صورت شواهدی مستند شود. در این مرحله هیچ ادعای قطعی "بهتر از X" اثبات نشده و نباید به آن متوسل شد.

---

## ۶. پرسش‌های باز برای مالک

1. **P1** – هسته استاندارد: IEC 62305:2024 (انتشار ۲۰۲۴-۰۹) یا IEC 62305:2024 با COR2:2026، یا هم‌زمان Ed.2 (2010) هم؟
2. **P2** – کدام national annex / پروفایل NFPA در کدام فاز؟ (لیست در 1.2-1.4)
3. **P3** – ترتیب عرضه ماژول‌ها (فازبندی M1-M12، نقطه توقف برای اولین انتشار)
4. **P4** – سیاست داده صاعقه (گزینه‌های D1-D4) و کدام منبع داده پیش‌فرض (با توجه به کیفیت IEC 62858)
5. **P5** – نحوه مدیریت تعمیم segment-by-segment (F6) تا قبل از دسترسی به متن 6.3 general method: پذیرش مشروط با disclaimer، یا حذف تا انتشار بعد؟
6. **P6** – پشتیبانی NFC 17-102 / ESE: این فناوری در IEC 62305 به‌رسمیت شناخته نمی‌شود. آیا از اول می‌خواهد؟
7. **P7** – نیاز به گزارش/صدور/امضا توسط مهندس واجد صلاحیت در نسخه اول چقدر باید صریح باشد (امکان امضای دیجیتال درون نرم‌افزار یا خیر)؟
8. **P8** – چه کسی منبع تأیید/صلاحیت مهندسی برای مقادیر جداول استاندارد می‌شود؟ (نیاز به قرارداد با مهندس مشاور متخصص برای P0-S3/S4 یا تأمین متن استاندارد از سوی A)

---

## ۷. موانع / محدودیت‌ها

- متن کامل IEC 62305-x:2024 Ed.3 (از جمله Annexهای D/C/E/F/G/H) در این پژوهش خریداری نشده؛ مقادیر نهایی جدول‌ها/فرمول‌های نسخه ۲۰۲۴ باید با متن رسمی یا مهندس صلاحیت‌دار تطبیق داده شود.
- نسخه و تغییرات NFPA 780 2025/2026 از صفحهٔ ناشر در دسترس عمومی قرار نگرفته؛ در این گزارش به NFPA 780:2023 و فیلدگاید ها به‌عنوان مرجع ثانویه ارجاع شده.
- هزینه قراردادهای تجاری داده (Vaisala/EUCLID/Météorage/Earth Networks) در منابع عمومی یافت نشد.
- URLهای مربوط به Furse (nVent) Guide، A.N.Wallis handbook، NPP PaLEFS، limutokol، Zumtobel، NIAR aircraft در sandbox این مجری با fetch قابل بارگیری نبودند (محدودیت شبکه یا UA)؛ در صورت نیاز به آن منابع در مراحل بعد، باید دسترسی فراهم شود یا ارجاع به‌عنوان `UNVERIFIED` بماند.

---

## ۸. دفتر منابع اختصاصی P0-S2

| شناسه | عنوان | ناشر/نویسنده | نوع | نسخه/تاریخ | URL | دسترسی | ادعاهای پشتیبانی‌شده | محدودیت |
|---|---|---|---|---|---|---|---|---|
| **SRC-DEHN-DESIGN-2026** | "Lightning Protection Design – Engineering Service Datasheet" (Appendix: country-specific adaptations of IEC 62305 Ed.3) | DEHN SE | دیتاشیت/ضمیمه خدمات طراحی | 2026 | https://www.dehn-international.com/sites/default/files/media/files/lightning-protection-design-engineering-service.pdf | PDF تمام‌متن | فهرست استانداردهای ملی/منطقه‌ای برای DE/AT/CH/UK/FR/IT/ES/NL/BE/SE/NO/FI/DK/PL/CZ/SK/HU/RO/BG/GR/HR/AE/SA/ZA/SG/MY/IN/CN/JP/KR/TH/VN/AU/NZ/ID/PH/US/CA/BR/MX/CO با شماره/سال انتشار | تولیدکننده (DEHN)؛ سال انتشار چند مورد (VN/MX/SA) در PDF با علامت `:` خاتمه یافته و `UNVERIFIED` مانده است |
| **SRC-IEC-62858-PREVIEW** | IEC 62858:2019 Redline preview – "Lightning density based on lightning location systems" | IEC | پیش‌نمایش استاندارد | Ed.2.0، 2019-10 | https://cdn.standards.iteh.ai/samples/102016/9d0f88cdd88140a7859de60428d43d74/IEC-62858-2019.pdf | PDF redline پیش‌نمایش (صفحات نمونه) | تعاریف N_G, N_SG؛ الزامات DE≥80% و LA≤500m؛ بیان اینکه thunderstorm days دیگر توصیه نمی‌شود | متن کامل پیش‌نمایش نیست |
| **SRC-NOAA-NCEI-LIGHTNING** | "Lightning Products and Services" | NOAA/NCEI | معرفی محصول | به‌روزرسانی ۲۰۲۶ | https://www.ncei.noaa.gov/products/lightning-products | صفحه وب | معرفی NLDN (Vaisala) و SWDI و county/state summaries؛ هزینه/دسترسی به‌صورت free/contractual | فقط معرفی |
| **SRC-NOAA-GRIB2-LSD** | "Lightning Strike Density Product Description" | NOAA/Ocean.Weather | PDD محصول | 2015 | https://ocean.weather.gov/lightning/lightning_pdd.php | صفحه وب | توصیف GRIB2 Level5 بر مبنای GLD360، رزولوشن 8km، 15/30min؛ DE>70%، LA≤5km | مشتق سطح ۵ و مناسب برای مصارف دریایی/راداری، نه N_G/N_SG سالانه آماده ریسک |
| **SRC-WGLC-ESSD** | "The WGLC global gridded lightning climatology and time series" | Kaplan & Lau / ESSD | مقاله و dataset | 2021 | https://essd.copernicus.org/articles/13/3219/2021/ + Zenodo https://doi.org/10.5281/zenodo.4774528 | PDF + dataset آزاد | climatology WWLLN، رزولوشن 0.5° و 5 arc-min؛ WWLLN cost $600/year برای raw data | برای تحقیق مناسب؛ دقت مطلق پایین‌تر از LLS‌های ملی/تجاری |
| **SRC-SKYTREE-COMPARE** | "Lightning Protection Standards: Which Code Applies?" | Skytree Scientific | مقاله صنعتی | 2026 | https://skytreescientific.ai/lightning-safety-protocols-for-outdoor-operations/ | وب | مقایسه NFPA 780 vs UL 96A vs LPI 175 vs IEC 62305 | ثانویه |
| **SRC-LUMEX-WHY-IEC62305** | "What Is IEC 62305?" | Lumex.zone | وبلاگ فنی | 2026-10-03 | https://lumex.zone/resources/what-is-iec-62305 | وب | تفاوت national adoptions (BS EN, IS/IEC, SS 555, AS 1768, NFPA 780)؛ Ed.3 R+F | ثانویه |
| **SRC-ECALPRO-IEC62305** | "IEC 62305 Lightning Protection – Complete Guide" | ECalPro | وبلاگ/ماشین‌حساب | 2026 | https://ecalpro.com/standards/iec-62305/lightning-protection-guide | وب | خلاصه چهار قسمت IEC، SPD table | ثانویه |
| **SRC-ANVILFIELD-NFPA780** | "Lightning protection system field guide (NFPA 780)" | Anvilfield | field guide | 2026 | https://anvilfield.com/field-guides/electrical/lightning-protection-system-nfpa780/ | وب | RSM 150 ft، 100 ft perimeter، 20 ft rod spacing برای NFPA 780 | ثانویه/عام‌پسند |
| **SRC-TRILPEAK-AIRTERM** | "What Is an Air Terminal?" | Trilpeak | راهنمای فنی | 2026 | https://trilpeak.com/air-terminal-guide/ | وب | RSM radius 20/45m بر اساس IEC و NFPA spacing | ثانویه |
| **SRC-WTL-LIGHTNING** | "How Lightning Rods Actually Work" | wheresthatlightning.com | توضیح RSM | 2026 | https://wheresthatlightning.com/guides/lightning-protection-systems | وب | توضیح 150 ft sphere ≈ 35 kA در NFPA 780 | ثانویه |
| **SRC-BSI-BSEN62305-1** | BS EN IEC 62305-1:2024 – BSI Knowledge product page | BSI | صفحه فروش | 2025-02-28 | https://knowledge.bsigroup.com/products/protection-against-lightning-general-principles-3 | صفحه وب | هشدار سیاست UK committee برای پیاده‌سازی کامل سری 4 قسمتی | صفحه فروش |
| **SRC-VDE-62305-3** | DIN EN IEC 62305-3 (VDE 0185-305-3):2025-10 | VDE Verlag | صفحه فروش | ۲۰۲۵-۱۰ | https://www.vde-verlag.de/p/normen/din-en-iec-62305-3-vde-0185-305-3-2025-10/0100876-DE-PR | صفحه وب | توصیف تغییرات (رویکرد عمومی بند ۶٫۳، ساختمان‌های >60m، بام سبز، national Sonderbedingung) | صفحه فروش |
| **SRC-VDE-62305-4** | DIN EN IEC 62305-4 (VDE 0185-305-4):2026-02 | VDE Verlag | صفحه فروش | ۲۰۲۶-۰۲ | https://www.vde-verlag.de/p/normen/din-en-iec-62305-4-vde-0185-305-4-2026-02/0100921-DE-PR | صفحه وب | Annex E/F/G/H جدید | صفحه فروش |
| **SRC-IEC-62305-2-CAT** | IEC 62305-2:2024 webstore catalog + COR1 + COR2 | IEC | webstore | ۲۰۲۴ / ۲۰۲۴-۱۰ / ۲۰۲۶-۱۰ | https://webstore.iec.ch/en/publication/28137 ; https://webstore.iec.ch/en/publication/101796 ; https://webstore.iec.ch/en/publication/116918 | صفحه کاتالوگ عمومی | تغییرات Ed.3 (single R, N_SG, TWS) | متن پولی |
| **SRC-IEC-62305-3-CAT** | IEC 62305-3:2024 webstore catalog | IEC | webstore | ۲۰۲۴-۰۹-۱۲ | https://webstore.iec.ch/en/publication/33680 | صفحه کاتالوگ عمومی | Edition 3.0، ۲۸۰ صفحه، توصیف تغییرات | متن پولی |
| **SRC-IEC-62305-1-CAT** | IEC 62305-1:2024 webstore catalog | IEC | webstore | ۲۰۲۴-۰۹-۱۲ | https://webstore.iec.ch/en/publication/27136 | صفحه کاتالوگ عمومی | Edition 3.0، ۱۵۳ صفحه | متن پولی |
| **SRC-IEC-62305-4-CAT** | IEC 62305-4:2024 webstore catalog | IEC | webstore | ۲۰۲۴-۰۹-۱۲ | https://webstore.iec.ch/en/publication/29590 | صفحه کاتالوگ عمومی | Edition 3.0، Annex E/F/G/H | متن پولی |

---

*پایان یادداشت تصمیم‌گیری. این یادداشت تصمیمی به‌جای مالک نمی‌گیرد؛ هر گزینه با پیامد و مدرک ارائه شده و منتظر تصمیم مالک/هماهنگ‌کننده است.*
