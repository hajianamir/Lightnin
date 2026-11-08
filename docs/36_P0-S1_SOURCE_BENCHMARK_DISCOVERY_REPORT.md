# گزارش کشف و ارزیابی منابع - مرحله P0-S1 (نسخه بازبینی‌شده v1.1)

- **task_id**: `P0-S1-SOURCE-BENCHMARK-DISCOVERY`
- **نسخه بسته**: ۱٫۲ (دومین بازکاری پس از REJECT نسخه ۱٫۱)
- **تغییرات نسبت به v1.1**: تصحیح ویرایش IEC 62305-3:2024 (Ed.3.0 نه Ed.4.0)؛ ثبت COR1/COR2 برای IEC 62305-2؛ افزودن رکوردهای رسمی DIN EN/VDE و BS EN؛ افزودن URL رسمی Horizon Power و LIRA؛ حذف ارجاع‌های بدون منبع قابل‌ردیابی.
- **تاریخ جست‌وجوی اولیه**: ۲۰۲۶-۱۱-۰۸
- **تاریخ بازکاری**: ۲۰۲۶-۱۱-۰۸
- **base_commit (تأییدشده با `git rev-parse HEAD` روی sandbox این مجری)**: `0c9c823a945d895c1a1c9b903e236b1a8cb4a421`
- **شاخه کاری نهایی**: `arena/461d9c97-lightnin` (شاخه مجاز). در طول پژوهش اولیه این مجری روی شاخه sandbox-prefixed دیگری قرار داشت؛ پس از ایجاد remote ref توسط A، این شاخه fetch و روی آن checkout شد. تمام عملیات commit/push نهایی روی همین شاخه انجام شده است.
- **وضعیت**: **DONE** (گزارش بازبینی‌شده با شرایط اعلام‌شده در REJECT)
- **وضعیت‌های پشتیبانی استفاده‌شده در این نسخه**:
  - `PRIMARY SOURCE` — صفحه رسمی ناشر استاندارد یا مقاله داوری‌شده/داوری‌نشده که تمام‌متن یا پیش‌نمایش معتبر در دسترس بوده
  - `SECONDARY SUPPORT` — راهنمای تولیدکننده، ابزار عمومی، یا وبلاگ مهندسی که یک ادعای فرمولی را بازگو می‌کند، اما خودش منبع صاحب‌اختیار نیست
  - `UNVERIFIED` — ادعایی که در منابع بررسی‌شده پشتیبان قابل‌دسترسیِ قابل‌ردیابی برای آن پیدا نشده، یا متن کامل استاندارد لازم است
  - `OBSERVATION FROM PROJECT MATERIALS` — یافته صرفاً با مشاهده کد/مستندات مخزن Lightnin
  - `DISCREPANCY OBSERVED` — تعارضی بین منابع مختلف مشاهده شده که نیاز به بررسی بیشتر دارد

**احتیاط کلی**: این گزارش فقط کشف منابع و ارزیابی اولیه benchmarkها است. هیچ‌یک از یافته‌ها به‌تنهایی به‌معنای تأیید انطباق با IEC/VDE/IEEE/BSI یا جایگزینی بازبینی مهندس واجد صلاحیت نیست.

---

## ۰. Queryهای جست‌وجو (تاریخ ۲۰۲۶-۱۱-۰۸)
هر query توسط ابزار `web_search` با پارامتر `depth=1` یا `depth=2` اجرا شد و صفحه‌های دریافت‌شده با `fetch_page` واکشی گردید. مجموعاً ۱۳ query و ۹ فراخوانی fetch_page انجام شد (جزئیات کامل در لاگ ابزارها ثبت است):

1. `IEC 62305-3 separation distance formula s = ki kc/km l air termination down conductor`
2. `lightning protection rolling sphere method protective angle mesh method IEC 62305-3 open source benchmark`
3. `IEC 62305-2 risk assessment calculation tool open source lightning`
4. `lightning protection earthing touch step voltage calculation formula IEC 62305-3 IEEE 80 guide`
5. `SPD selection coordination IEC 62305-4 LPZ LEMP surge protective device calculation`
6. `substation lightning protection shielding IEEE 998 rolling sphere electrogeometric model transmission line`
7. `solar PV wind turbine lightning protection IEC 61400-24 IEC 62548 transient overvoltage`
8. `lightning flash density ground flash density Ng map dataset WMO NASA GLD360 EUCLID ATDnet`
9. `open source lightning protection software 3D rolling sphere github python`
10. `telecommunication tower lightning protection ITU-T K.39 K.46 surge protection`
11. `IEC 62305-3 ki values 0.08 0.06 0.04 2024 edition table kc km`
12. `Berger lightning current parameters peak 50kA 200kA IEC 62305-1 table distribution`
13. `lightning protection solar PV IEC 62548 SPD photovoltaic system standard`

---

## ۱. دفتر منابع (Source Register)

در این نسخه هر مدخل شامل **عنوان دقیق، ناشر/نویسنده، نوع منبع، تاریخ/نسخه در صورت دسترسی، URL، سطح دسترسی، حوزه، ادعاهای پشتیبانی‌شده و محدودیت‌ها** است. ادعاهای فرمولی که به مدخل ارجاع می‌شوند، در بخش ۳ با بند/جدول/صفحه مشخص شده‌اند.

### ۱-A. صفحات رسمی استاندارد (فقط فراداده، متن پولی)

| شناسه | عنوان | ناشر | نوع | نسخه | URL | دسترسی | حوزه |
|---|---|---|---|---|---|---|---|
| STD-IEC-62305-3-2024 | IEC 62305-3:2024 "Protection against lightning – Part 3: Physical damage to structures and life hazard" | IEC (webstore) | استاندارد بین‌المللی | **Edition 3.0**, 2024-09-12 (جایگزین Ed.2.0=2010 و Ed.1.0=2006)؛ صفحه کاتالوگ در تاریخ 2026-11-08 بدون corrigendum نمایش داده می‌شود | https://webstore.iec.ch/en/publication/33680 | فقط صفحه کاتالوگ (فراداده)، متن کامل پولی (CHF 430، ۲۸۰ صفحه) | LPS بیرونی، separation، RSM/mesh/angle، touch/step. تغییرات مهم این ویرایش: دو روش general/simplified برای separation (بند ۶.۳)، Annex C بازبینی‌شده، Annex D برای جزئیات روش‌های هوا-پایانه |
| STD-IEC-62305-2-2024 | IEC 62305-2:2024 "Protection against lightning – Part 2: Risk management" (با corrigenda) | IEC (webstore) | استاندارد بین‌المللی | **Edition 3.0**، انتشار اولیه 2024-09-12. تاریخچه روی وب‌استور IEC در تاریخ 2026-11-08:
- **IEC 62305-2:2024/COR1:2024** مورخ ۲۰۲۴-۱۰-۱۷ (https://webstore.iec.ch/en/publication/101796)
- **IEC 62305-2:2024/COR2:2026** مورخ ۲۰۲۶-۱۰-۱۲ (https://webstore.iec.ch/en/publication/116918) - "Corrected version 2026-10"
نسخهٔ پایه خریدنی روی صفحهٔ کاتالوگ فعلاً نسخهٔ اصلاح‌شده (شامل corrigendum 1) است. تغییرات نسبت به Ed.2: single risk (ترکیب تلفات جانی و آتش)، frequency of damage برای سیستم‌های داخلی، جایگزینی N_G با **N_SG** (ground strike-point density)، اقدامات پیشگیرانه موقت با TWS (IEC 62793). | https://webstore.iec.ch/en/publication/28137 | فقط صفحه کاتالوگ، متن کامل پولی (CHF 430، ۲۵۶ صفحه) | ریسک، single-risk، N_SG. در این پژوهش **اشاره‌ها به single-risk/N_SG بر اساس صفحه کاتالوگ و DEHNrisk است**؛ فرمول‌های کمی در منابع آزاد یافت نشد |
| STD-IEC-62305-1-2024 | IEC 62305-1:2024 "Protection against lightning – Part 1: General principles" | IEC (webstore) | استاندارد بین‌المللی | **Edition 3.0**، 2024-09-12 (جایگزین Ed.2=2010، Ed.1=2006) | https://webstore.iec.ch/en/publication/27136 | فقط صفحه کاتالوگ، متن پولی (CHF 380، ۱۵۳ صفحه) | پارامترهای جریان صاعقه، LPL I–IV، کلیات. تغییرات: ارجاع به IEC 62561 در Annex D، types of loss با public relevance، frequency of damage، surge currents برای SPD |
| STD-IEC-62305-4-2024 | IEC 62305-4:2024 "Protection against lightning – Part 4: Electrical and electronic systems within structures" | IEC (webstore) | استاندارد بین‌المللی | **Edition 3.0**، 2024-09-12 (جایگزین Ed.2=2010، Ed.1=2006) | https://webstore.iec.ch/en/publication/29590 | فقط صفحه کاتالوگ، متن پولی (CHF 430، ۲۷۰ صفحه) | LEMP، LPZ، SPM، SPD هماهنگی. Annex E (current sharing modelling)، Annex F (PV)، Annex G (system-level tests)، Annex H (induced voltages) |
| STD-IEEE-80-2013 | IEEE Std 80-2013 (Cor 1-2015) "IEEE Guide for Safety in AC Substation Grounding" | IEEE | استاندارد/راهنما | 2013 + Corrigendum 2015 | https://standards.ieee.org/standard/80-2013-Cor1-2015.html | صفحه کاتالوگ، متن پولی | touch/step (AC power frequency) |
| STD-IEEE-998-2012 | IEEE Std 998-2012 "Guide for Direct Lightning Stroke Shielding of Substations" | IEEE | راهنما | 2012 | mirror PDF در https://kupdf.net/download/ieee-std-998-2012-guide-for-direct-lightning-stroke-shielding-of-substations_596abf62dc0d60fb2fa88e79_pdf و https://dokumen.site/download/ieee-std-998-2012-guide-for-direct-lightning-stroke-shielding-of-substations-a5b39f113aefaa | PDF نسخه به‌اشتراک‌گذاشته‌شده (mirror third-party، تضمین اصالت نسخه با ناشر نیست) | پست، RSM/EGM |
| STD-IEC-61400-24 | IEC 61400-24:2019+AMD1:2024 CSV "Wind energy generation systems – Part 24: Lightning protection" | IEC/VDE | استاندارد محصولی | Ed. 2.1, 2024-11 | https://standards.iteh.ai/catalog/standards/iec/6aae4b87-f0f6-474c-a3ce-da2b91697249/iec-61400-24-2019 ؛ پیش‌نمایش VDE: https://assets.vde-verlag.de/iec-normen/preview-pdf/info_iec61400-24{ed2.1}en.pdf | صفحه ناشر و پیش‌نمایش VDE | باد، توربین، LPZ، SPD، پایش صاعقه |
| STD-IEC-62548-2016 | IEC 62548:2016 "Photovoltaic (PV) arrays – Design requirements" | IEC/GlobalSpec | استاندارد محصولی | 2016 (جایگزین‌شده توسط IEC 62548-1:2023+AMD1:2025 که در IEC 62305-4 ارجاع می‌شود) | https://standards.globalspec.com/std/10046574/iec-62548 ؛ FDIS preview: https://pdfcoffee.com/iec-62548-pv-array-design-requirements-final-draft-pdf-free.html ؛ صفحه رسمی 62548-1:2023: https://webstore.iec.ch/en/publication/64171 | صفحه کاتالوگ + FDIS draft (غیرنهایی) | PV، ۶.۶ lightning/overvoltage |
| STD-VDE-0185-305-2 | DIN EN IEC 62305-2 (VDE 0185-305-2):2026-02 "Blitzschutz Teil 2: Risikomanagement" | VDE Verlag | پذیرش ملی آلمان (EN IEC 62305-2:2024) | ۲۰۲۶-۰۲ | https://www.vde-verlag.de/p/normen/din-en-iec-62305-2-vde-0185-305-2-2026-02/0100917-DE-PR | صفحه کاتالوگ (متن پولی) | آلمان؛ risk management مبتنی بر IEC 62305-2:2024 |
| STD-VDE-0185-305-3 | DIN EN IEC 62305-3 (VDE 0185-305-3):2025-10 "Blitzschutz Teil 3: Schutz von baulichen Anlagen und Personen" | VDE Verlag | پذیرش ملی آلمان (EN IEC 62305-3:2024) | ۲۰۲۵-۱۰؛ جایگزین DIN EN 62305-3 (VDE 0185-305-3):2011-10 | https://www.vde-verlag.de/p/normen/din-en-iec-62305-3-vde-0185-305-3-2025-10/0100876-DE-PR | صفحه کاتالوگ (توصیف کامل تغییرات قابل‌مشاهده)؛ متن پولی. نکات مهم قابل‌مشاهده در صفحه: بند ۶.۳ به "رویکرد عمومی" برای separation گسترش یافته؛ ضمیمه D برای ساختمان‌های بلندتر از ۶۰ متر، سقف سبز؛ ناسیونال ساندینگ برای انتخاب Schutzklasse | آلمان؛ جداول ki/km/kc آلمان معادل EN IEC 62305-3 هستند + national annex |
| STD-VDE-0185-305-4 | DIN EN IEC 62305-4 (VDE 0185-305-4):2026-02 "Blitzschutz Teil 4: Elektrische und elektronische Systeme in baulichen Anlagen" | VDE Verlag | پذیرش ملی آلمان (EN IEC 62305-4:2024) | ۲۰۲۶-۰۲؛ جایگزین ویرایش ۲۰۱۱ و Berichtigung 1:2017 | https://www.vde-verlag.de/p/normen/din-en-iec-62305-4-vde-0185-305-4-2026-02/0100921-DE-PR | صفحه کاتالوگ (توصیف تغییرات قابل‌مشاهده)؛ متن پولی. تغییرات مهم: Annex E (مدل‌سازی تقسیم جریان)، Annex F (PV current sharing)، Annex G (تست در سطح سیستم)، Annex H (ولتاژهای القایی در تأسیسات SPD-محافظت‌شده) | آلمان؛ LEMP/SPD/هماهنگی |
| STD-BS-EN-62305-1 | BS EN IEC 62305-1:2024 "Protection against lightning – General principles" | BSI Knowledge | پذیرش ملی بریتانیا | ۲۰۲۵-۰۲-۲۸؛ "Current, Under Review" | https://knowledge.bsigroup.com/products/protection-against-lightning-general-principles-3 | صفحه فروش BSI (توضیحات آزاد)؛ **احتیاط**: در صفحه یک خطای Cross-ref به "IEC 60335-2-39:2012" و "IEC 62305-1 Ed.2.0" دیده می‌شود که به‌نظر می‌رسد با توجه به عنوان/تغییرات فنی، نادرست است (صفحه در واقع BS EN IEC 62305-1:2024/Ed.3 را توصیف می‌کند) | نکته کلیدی سیاستی BSI (قابل‌استناد): "UK committee advises users that the BS EN IEC 62305 third edition series should be implemented in full as it would not be safe to implement parts 1, 3 and 4 of the third edition without having done a risk assessment in accordance with BS EN IEC 62305-2:2024" |
| STD-HORIZON-POWER-PCD | Horizon Power "HPC-7DC-08-0001-2013 – PCD – Substation Lightning Protection Design" | Horizon Power (شرکت برق استرالیای غربی، عمومی) | استاندارد/رویه طراحی شرکت (رسمی، عمومی) | نسخه ۲۰۱۳، بازبینی ۳۱/۱۰/۲۰۲۳ (DM#1805183) | https://www.horizonpower.com.au/globalassets/media/documents/manuals-standards/procedures/hpc-7dc-08-0001-2013_-_pcd_-_substation_lightning_protection_design.pdf?v=4ac015 | PDF تمام‌متن آزاد | پست استرالیا؛ شعاع کره غلتان **24 m** برای پست‌ها؛ فلوچارت طراحی |

**احتیاط**: متن کامل هیچ‌یک از استانداردهای بالا در این پژوهش خریداری/دانلود نشده. ارجاع‌های فرمولی به این استانداردها در بخش ۳ فقط از طریق منابع ثانویه (راهنمای تولیدکننده، مقاله کنفرانس) می‌آیند و برچسب `SECONDARY SUPPORT` خورده‌اند مگر آن‌جا که متن mirror/preview (مانند DEHN slides که رونوشت جدول‌های استاندارد است) روشن چیزی را بازتولید کرده باشد.

### ۱-B. منابع ثانویه معتبر (راهنماهای تولیدکننده / وبلاگ مهندسی / آموزشی)

| شناسه | عنوان | ناشر/نویسنده | نوع | تاریخ/نسخه | URL | دسترسی | ادعاهای پشتیبانی‌شده | محدودیت‌ها |
|---|---|---|---|---|---|---|---|---|
| SRC-INDELEC-SEP-2026 | "LPS Separation Distance: How to Calculate and Respect It" | Indelec (تولیدکننده) | وبلاگ فنی | 2026-10-19 | https://indelec.com/en/blog-en/distance-de-separation-lps/ | تمام‌متن آزاد | فرم کلی `s = ki × (kc / km) × l`؛ توضیح معنی هر نماد؛ ارجاع به IEC 62305-3:2024 | مقادیر عددی ki/kc/km در این صفحه بیان نشده‌اند (فقط فرم و اینکه ضرایب را از جدول‌های استاندارد باید گرفت) |
| SRC-THOR-LPS-2026 | "Lightning Protection System: From Air Terminals to SPDs" | THOR (spds.global) | وبلاگ فنی | 2026-08-12 | https://spds.global/blogs/lightning-protection-system/ | تمام‌متن آزاد | سه لایه LPS؛ جدول شعاع کره (I=20، II=30، III=45، IV=60 م)؛ اندازه mesh (5×5, 10×10, 15×15, 20×20 m)؛ فاصله down-conductor (10/10/15/20 m) | مقادیر ki/km در این صفحه نیامده |
| SRC-DEHN-SLIDES-2013 | "BS EN 62305-3:2011 – Physical damage to structures" (اسلاید ارائه) | DEHN + SÖHNE (تولیدکننده) | اسلاید آموزشی | 2013-01-25 (بر اساس BS EN 62305-3:2011 = IEC 62305-3:2010) | https://ifsm.org.uk/wp-content/uploads/3-DEHN-UK-Lightning-prot-Physical-damage-to-structures-IFSM.pdf | PDF تمام‌متن آزاد | **بند ۶.۳ جدایی**: فرمول s=ki·(kc/km)·l به‌نقل از استاندارد؛ **جدول ki** (Class I=0.08, II=0.06, III+IV=0.04)؛ **جدول km** (Air=1، Concrete/Bricks=0.5، DEHNiso=0.7*)؛ **جدول kc** (1 down=1، 2=0.66، ≥3=0.44، با یادداشت نوع B/اختلاف مقاومت کمتر از ۲)؛ **جدول RSM/mesh/down-conductor** از Table 2/4 | نسخه 2011 BS EN (منطبق بر IEC 2010)، نه 2024؛ DEHNiso محصول شرکت است |
| SRC-ECALPRO-LIGHTNING | "Lightning Calculator — IEC 62305 Risk Assessment" | ECalPro | ماشین‌حساب وب + FAQ | صفحه بازبینی‌شده 2026 | https://ecalpro.com/en/calc/lightning | تمام‌متن آزاد | R_T = 10⁻⁵/year; شعاع کره 20/30/45/60؛ فاصله down-conductor 10/10/15/20؛ مقاومت earth ≤10 Ω در ۵.۴.۱؛ SPACING 10m بین Type1/Type2؛ **متن بحث‌برانگیز در FAQ جدایی**: "ki depends on the protection level (0.04 for Level I, 0.06 for Level III)" | این مقدار ki در FAQ **با جدول DEHN (I=0.08, III/IV=0.04) و اکثر منابع در تعارض است**؛ این موضوع در بخش ۳ به‌عنوان `DISCREPANCY OBSERVED` ثبت می‌شود. خود سایت به IEC 62305-2 Ed.3.0 (2024) سوئیچ می‌کند اما FAQ در صفحه بازیابی‌شده هنوز از این ترکیب یاد می‌کند |
| SRC-ECALPRO-EARTHING | "Earthing System Calculator — IEEE 80, BS 7430, AS/NZS 3000" | ECalPro | ماشین‌حساب | 2026 | https://ecalpro.com/en/calc/earthing | تمام‌متن آزاد | فرمول E_touch = (1000 + 1.5·Cs·ρ_s)·0.116/√t_s (برای 50 kg) | از نسخه‌های قدیمی‌تر IEEE 80 (2000) استفاده می‌کند؛ نسخه 2013 ضرایب 70 kg با ضریب 0.157 را هم دارد |
| SRC-REUVEN-RSM | "Lightning Protection (Rolling Sphere) Calculator" | Reuven Engineering Tools | ماشین‌حساب تعاملی | صفحه بازبینی‌شده 2026 | https://reuven.tools/tools/lightning-protection/ | تمام‌متن آزاد | فرمول‌ها صریح آمده‌اند: R=20/30/45/60 m (LPL I–IV)؛ R=10·I^0.65 (kA→m)؛ rp=√(2Rh-h²) برای h<R و rp=R برای h≥R؛ A=π·rp². مثال عددی LPL II با h=10 m → rp=22.36 m, Area=1571 m² | این ماشین‌حساب محصول تجاری یا وابسته به تولیدکننده خاصی نیست (در دامنه reuven.tools قرار دارد)؛ با این‌حال **نویسنده و اعتبار مستقل آن در این پژوهش تأیید نشده** (اثر انتشار فردی است، نه نهاد استاندارد یا دانشگاه). در این نسخه به‌عنوان "candidate benchmark" نامیده می‌شود، نه "benchmark مستقل قوی" |
| SRC-WINDFARMBOP-IEEE80 | "Substation Earthing Design per IEEE 80 — Step by Step" | windfarmbop.com | وبلاگ مهندسی (نویسنده ناشناس) | 2026-04-01 | https://www.windfarmbop.com/substation-earthing-design-per-ieee-80-step-by-step/ | تمام‌متن آزاد | مثال عددی با ρ=75, ρs=4000, hs=0.2, Ig=10,676A؛ فرمول Etouch (70 kg) = (1000+1.5·Cs·ρs)·0.157/√t_s؛ Estep = (1000+6·Cs·ρs)·0.157/√t_s؛ Cs=1−0.09·(1−ρ/ρs)/(2h_s+0.09)؛ Em=ρ·Km·Ki·IG/LM؛ Es=ρ·Ks·Ki·IG/LS | منبع ثانویه (blost post)، بدون ذکر نویسنده؛ باید با متن IEEE 80-2013 cross-check شود |
| SRC-FIRGELLIAUTO-EARTH | "Earthing System Touch Step Voltage Interactive Calculator" | Firgelli Auto | صفحه ماشین‌حساب/توضیح | 2026-03-18 | https://www.firgelliauto.com/blogs/calculators/earthing-system-touch-step-calculator | تمام‌متن آزاد | E_touch50=(1000+1.5 Cs·ρ_s)·0.116/√t_f ؛ E_step50=(1000+6 Cs·ρ_s)·0.116/√t_f ؛ Cs=1−0.09(1−ρ/ρ_s)/(2h_s+0.09) | بازنویسی IEEE 80، محصول تجاری جانبی |
| SRC-DEHNRISK | "DEHNrisk: Lightning Risk Assessment Software" | DEHN | SaaS | معرفی 2024 | https://www.dehn-international.com/en/products/services/dehnrisk | صفحه معرفی آزاد (نرم‌افزار با ثبت‌نام) | انطباق با IEC 62305-2 Ed.3؛ پشتیبانی چند ملیت (IEC/EN/BS/DIN/ČSN) | وابسته به تولیدکننده (DEHN)؛ خروجی نرم‌افزار در دسترس این پژوهش نبود |
| SRC-INGESCO-CALCULUS | "Calculus – Calculation of lightning protection measures" | INGESCO | SaaS رایگان | صفحه بازبینی‌شده 2026 | https://calculus.ingesco.com/ | صفحه معرفی (ثبت‌نام برای گزارش PDF) | IEC 62305-2، UNE 21.186:2011، NFC 17.102:2011 | وابسته به تولیدکننده |
| SRC-THOR-LPZ-2026 | "Lightning Protection Zone (LPZ): Concept and SPD Selection Guide" | THOR (spds.global) | وبلاگ فنی | 2026-07-10 | https://spds.global/blogs/lightning-protection-zone/ | تمام‌متن آزاد | نگاشت LPZ به SPD Type: Type1 در 0A→1 (10/350 µs)، Type2 در 0B→1 یا 1→2 (8/20 µs)، Type3 در 2→3+؛ فاصله 10 m یا اندکتانس کوپلاژ | فاصله ۱۰ متری از راهنمای تولیدکننده آمده، بند استاندارد برای آن یافت نشد |
| SRC-INDELEC-LPZ-2026 | "Lightning Protection Zone (LPZ): Engineer's 2026 Guide" | Indelec | وبلاگ فنی | 2026-07-02 | https://indelec.com/en/blog-en/lightning-protection-zone-lpz-engineers-2026-guide/ | تمام‌متن آزاد | مقادیر Iimp 25–100 kA برای Type1، 5–20 kA Type2، <5 kA Type3؛ Up ≤2.5/1.5/1.0 kV | تولیدکننده است |
| SRC-SB-SPD-2025 | "SPD Selection (Surge Protective Devices) – IEC, IEEE" | CalculatorsConversion | منبع آموزشی وب | 2025-04-20 | https://www.calculatorsconversion.com/en/spd-selection-surge-protective-devices-iec-ieee/ | تمام‌متن آزاد | Uc≥Vrms؛ Up≤Uw؛ Up+ΔV≤Uw؛ I=k·A·C (جریان تخمینی) | فرمول I=k·A·C در این منبع بدون مرجع استاندارد مشخص آمده؛ برای این گزارش آن را `UNVERIFIED` نگه می‌داریم |
| SRC-ATECORP-ITU-K | "ITU-T K Series: Protection Against Interference" | A.T. Corp. (فروشنده تست تجهیزات) | فهرست استاندارد | 2024 | https://www.atecorp.com/compliance-standards/itu-t/itu-t-k-series | تمام‌متن آزاد | فهرست K.35 تا K.69، شامل K.39 (ریسک برای سایت تلکام)، K.40 (LEMP در مراکز تلکام)، K.46 (خطوط فلزی متقارن)، K.47 (خطوط در برابر برخورد مستقیم) | ثانویه |
| SRC-ITU-K46-2003 | "ITU-T Rec. K.46 (07/2003): Protection of telecommunication lines using metallic symmetric conductors against lightning-induced surges" | ITU-T | توصیه‌نامه | 2003 | https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-K.46-200307-S!!PDF-E&type=items | PDF تمام‌متن (لینک مستقیم ITU) | Ki (نصب هوایی=۱، دفن=۰.۵) بر اساس IEC 61663-2؛ Ks ضریب شیلد | نسخه ۲۰۰۳ است (قدیمی) |
| SRC-ITU-K40-2019 | "ITU-T K.40 (11/2019): Protection against lightning electromagnetic impulses in telecommunication centres" | ITU-T | توصیه‌نامه | 2019 | https://www.itu.int/epublications/publication/itu-t-k-40-2019-11-protection-against-lightning-electromagnetic-impulses-in-telecommunication-centres | صفحه انتشار (PDF در فروشگاه ITU برای دانلود رایگان) | LPZ برای مراکز تلکام، MCBN، SPD هماهنگ | صفحه فقط خلاصه است؛ متن کامل در ITU bookshop |
| SRC-ITE-SPD-2023 | "Surge protective devices (SPDs)" | IET (Wiring Matters 98, Nov 2023) | نشریه انجمن مهندسی برق UK | 2023-11 | https://electrical.theiet.org/wiring-matters/years/2023/98-november-2023/surge-protective-devices-spds/ | تمام‌متن آزاد (ارجاع‌شده از THOR) | تأکید می‌کند که LPS بیرونی به‌تنهایی حفاظت ترانزیست برای تأسیسات الکتریکی کافی نیست | ثانویه |

### ۱-C. مقالات پژوهشی/دانشگاهی

| شناسه | عنوان | نویسندگان | کنفرانس/نشریه | سال | URL | دسترسی | ادعاهای پشتیبانی‌شده | محدودیت |
|---|---|---|---|---|---|---|---|---|
| PAP-ZISCHANK-ICLP | "Necessary Separation Distances for Lightning Protection Systems – IEC 62305-3 Revisited" | W. Zischank و همکاران | ICLP/SIPDA (پیش‌چاپ) | حدود ۲۰۰۶؟ (از صفحه ResearchGate/فایل پیش‌چاپ FH Aachen) | نسخه PDF مشابه در https://ili.fh-aachen.de/ilias.php?baseClass=ilrepositorygui&cmd=sendfile&cmdClass=ilObjFileGUI&cmdNode=z8%3Aow&ref_id=246185 و کپی از طریق https://www.researchgate.net/profile/Wolfgang-Zischank/publication/228425810_NECESSARY_SEPARATION_DISTANCES_FOR_LIGHTNING-PROTECTION-SYSTEMS-IEC_62305-3_REVISITED | PDF پیش‌چاپ از FH Aachen در دسترس | فرمول s=ki·(kc/km)·l؛ جدول ki (I=0.08, II=0.06, III+IV=0.04) بر اساس i_max/T1؛ جدول km (air=1, concrete/brick=0.5)؛ فرمول kc بند C.2 شامل c و h و n؛ بحث kc برای سقف فلزی که استاندارد آن را کامل پوشش نمی‌دهد؛ بحثی که مقادیر ki در نسخه‌ای از استاندارد ۲۰٪ کاهش یافتند | پیش‌چاپ است (نه نهایی ICLP proceedings) |
| PAP-ANDERSON-KLUGMANN-2014 | "A European lightning density analysis using 5 years of ATDnet data" | G. Anderson, D. Klugmann | Natural Hazards and Earth System Sciences (NHESS) 14, 815–833 | 2014 | https://nhess.copernicus.org/articles/14/815/2014/nhess-14-815-2014.pdf | PDF آزاد انتشارات آزاد Copernicus | توصیف شبکه ATDnet (Met Office VLF از ۱۹۸۷)؛ ۵ سال داده ۲۰۰۸–۲۰۱۲؛ بیشینه ~۱۴–۳۰ flash/km²/year بسته به ماه | فقط اروپا، و صرفاً به‌عنوان داده اقلیمی (نه benchmark نرم‌افزاری) |
| PAP-ENNO-2019 | "Lightning flash density in Europe on the basis of 10 years of ATDnet data" | S.-E. Enno و همکاران | Atmospheric Research | 2019 | https://www.sciencedirect.com/science/article/abs/pii/S0169809519303692 | چکیده و highlights آزاد، متن پولی | محدوده‌ی کلی flash density ۰٫۵–۳ fl/km²/y، بیشینه ۷٫۸ در شمال‌شرق ایتالیا؛ تفاوت‌های ATDnet و EUCLID | متن کامل خریدنی است |
| PAP-IJASEIT-2022 | "A Comparative Analysis of External Lightning Strike Protection …" | IJASEIT | IJA SEIT | 2022 | https://ijaseit.insightsociety.org/index.php/ijaseit/article/download/16638/pdf_2345 | PDF آزاد | شعاع‌های RSM 20/30/45/60 m را بازگو می‌کند؛ مقایسه حفاظت زاویه‌ای و کره غلتان | نشریه open-access، نه از top-tier مهندسی برق |
| PAP-BRANDON-VAISALA | "Adoption of IEC 62305 as the Basis for One Major U.S. Electric ..." | G. T. Brandon (Vaisala) | مقاله صنعتی | نامشخص | https://www.vaisala.com/sites/default/files/documents/Adoption%20of%20IEC%2062305%20as%20the%20Basis%20for%20One%20Major%20U.S.%20Electric_G.T.%20Brandon.pdf | PDF آزاد Vaisala | فرمول s=ki·(kc/km)·l و فرمول NFPA 780 مربوط D=h/6n + Km را در کنار هم قرار می‌دهد | مقاله صنعتی/تجاری |
| PAP-HEIDLER-2008 | "Parameters of Lightning Current given in IEC 62305" | F. Heidler, W. Zischank | ICLP کوتاه‌مقاله | 2008 | https://inspectapedia.com/lightning/Parameters-of-Lightning-Heidler-2008.pdf | PDF آزاد (از inspectapedia) | توضیح منشأ مقادیر جدول‌های IEC 62305-1 (Berger 1975)؛ پارامترهای first positive (200 kA, 10/350 µs) و subsequent (50/37.5/25 kA، 200/150/100 kA/µs)؛ توضیح شکل‌گیری R=10·I^0.65 | ثانویه (کپی از سایت) اما رونوشت مقاله ارائه ICLP است |
| PAP-ZINO-PREVIEW | "IEC 62305-1 Edition 2.0 2010-12 INTERNATIONAL STANDARD (preview)" | IEC (کپی) | — | 2010 | https://zinoglobal.com/wp-content/uploads/2019/12/IEC-62305-1.pdf | PDF پیش‌نمایش | جدول پارامترهای جریان first positive (200/150/100 kA, Q 100/75/50 C، W/R 10/5.6/2.5 MJ/Ω) و subsequent (50/37.5/25 kA, di/dt 200/150/100 kA/µs) | کپی غیررسمی است؛ اصالت با ناشر نیست |
| PAP-LIRA-ICLP-2012 | "Lightning Risk Assessment tool: Implementation of the IEC 62305-2 Standard on Lightning Protection" | C. T. Mata و همکاران (SLS / Florida Institute of Technology و همکاران) | ICLP 2012، وین | 2012 | https://www.sls-us.com/wp-content/uploads/2025/10/Lightning_Risk_Assessment_tool_implementation_of_the_IEC_62305-2_standard_on_lightning_protection.pdf | PDF تمام‌متن | توصیف LIRA (MATLAB GUIDE)؛ مؤلفه‌های ریسک RA, RB, RU, RV, RC, RM, RW, RZ (IEC 62305-2:2010)؛ گزارش LaTeX/PDF | کد توزیع عمومی LIRA از این مقاله در دسترس نیست (ارجاع قدیمی به MATLAB GUIDE) |

### ۱-D. اسناد فنی و پروژه‌های نرم‌افزاری

| شناسه | نام | مالک | نوع | نسخه/تاریخ | URL | دسترسی | پوشش | مجوز | یادداشت |
|---|---|---|---|---|---|---|---|---|---|
| OSS-LPO | Lightning-Protection-Optimizer | Indrek Edur | پروژه منبع‌باز GitHub | latest commit `927f1db…` مورخ ۲۰۲۶-۱۰-۲۷؛ 8 commits | https://github.com/IndrekEdur/Lightning-Protection-Optimizer | منبع کامل روی GitHub (پایتون/FastAPI/React+Three.js) | RSM پیوسته با گواهی عدم تماس (analytical support functions)، IFC import، بهینه‌سازی set-cover با HiGHS، 84 تست backend (بنابر README و درخواست اولیه جست‌وجو) | **مجوز در صفحهٔ ریشه‌ای که fetch_page خوانده مشخص نیست** (فایل LICENSE در first page نتایج list نشده) | کاندید benchmark برای 3D RSM. تا زمانی‌که LICENSE بررسی نشده، "قوی‌ترین" خطاب نمی‌شود (اصلاح نسبت به v1.0)؛ separation/down-conductor/ریسک/earthing در این پروژه نیست |
| OSS-RODPLANNER | RodPlanner | Shlok Chatterjee | GitHub (آموزشی) | — | https://github.com/ShlokChatterjee/RodPlanner | منبع عمومی | فقط protection cone، RSM هدف آینده | نیاز به بررسی دارد | پروژه آموزشی |
| OSS-SFERA | sfera | arheon-project | GitHub | — | https://github.com/arheon-project/sfera | صفحه عمومی (دسترسی نسخه کار با دعوت) | RSM بر اساس استاندارد قزاقستان SP RK 2.04-103-2013؛ DXF import/export، PDF | نامشخص | استاندارد مبنا IEC نیست |
| COMM-SESSHILD | SESShield-3D | SES & Technologies (CDEGS) | نرم‌افزار تجاری | — | https://www.sestech.com/en/Product/package/SESShield-3D | صفحه معرفی | RSM/Eriksson/CVM/Mesh/Protection Angle | تجاری | بنچمارک غیرآزاد |
| SW-LARS | LARS (Lightning Assessment of Risk for a Structure) | پروژه منبع‌باز | SourceForge | آخرین نسخه 3.0.2 (2014) | https://sourceforge.net/projects/lars-ms/ | دانلود رایگان (منبع‌بسته) | IEC 62305-2 Ed.2 | مجوز منبع‌بسته | نگهداری متوقف |
| SW-3DLIGHTNING | 3D Lightning (freeware AutoCAD) | V. Kodryan/اشتراک‌گذاری‌شده در forum | freeware | 2010 | https://www.crazyengineers.com/threads/cad-system-for-lightning-protection.40057 | پست انجمن | RSM برای rod ها، 3D در AutoCAD | freeware غیرمنبع‌باز | قدیمی، روی AutoCAD ویندوز |

### ۱-E. داده‌های اقلیمی / جغرافیایی (Ng)

| شناسه | نام | نهاد | URL | دسترسی در این پژوهش | پوشش | ادعای محدوده |
|---|---|---|---|---|---|---|
| GEO-NOAA-LSD | Lightning Strike Density Product Description | NOAA/Ocean.Weather.gov | https://ocean.weather.gov/lightning/lightning_pdd.php | صفحه توصیف محصول آزاد | محصول GRIB2 سطح L5 بر مبنای Vaisala GLD360 | واحد strikes/m²/s (SI)؛ راندمان >70% در نیمکره شمالی، دقت میانه ≤5 km |
| GEO-VAISALA-ATDNET | "Lightning flash density in Europe on the basis of 10 years of ATDnet data" (PDF) | Vaisala/Enno et al. | https://www.vaisala.com/sites/default/files/documents/Lightning%20flash%20density%20in%20Europe%20on%20the%20basis%20of%2010%20years%20of%20ATDnet%20data_S.-E.%20Enno%20et%20al.pdf | PDF تمام‌متن از Vaisala | اروپا ۲۰۰۸–۲۰۱۷ | ۱۴۸ میلیون flash، ۰٫۵–۳ fl/km²/y در بیشتر اروپا |
| GEO-NHESS-ATDNET | PAP-ANDERSON-KLUGMANN-2014 (بالا) | Copernicus/NHESS | همان PAP-ANDERSON | PDF آزاد | اروپا ۲۰۰۸–۲۰۱۲ | ~۹۱ میلیون fix → ~۵۹ میلیون flash |

**ادعای منفی نسخه ۱.۰ که "داده جهانی رایگان با رزولوشن مهندسی موجود نیست" را تضعیف می‌کنم**: در جست‌وجوی انجام‌شده **برای محصولات GLD360/NLDN/WWLLN/EUCLID خروجی نقشه آزاد با رزولوشن مناسب برای ورودی Ng یک پروژه مهندسی (مانند سرویس WMS رایگان یا CSV آزاد برای هر منطقه) یافت نشد**، اما GLD360 یک محصول GRIB2 سطح L5 NOAA دارد (GEO-NOAA-LSD). داده کامل GLD360، NLDN، EUCLID تجاری است. این ادعا در نسخه جدید دقیق‌تر و محدود بیان می‌شود.

---

## ۲. ماتریس حوزه‌ها

| حوزه | منابع معتبر یافت‌شده (شناسه) | نامزدهای benchmark | شکاف‌ها در محدوده جست‌وجو |
|---|---|---|---|
| ریسک (IEC 62305-2) | STD-IEC-62305-2-2024 (صفحه کاتالوگ)، SRC-DEHNRISK، SRC-INGESCO-CALCULUS، SRC-ECALPRO-LIGHTNING، SW-LARS، PAP-LIRA-ICLP-2012 | DEHNrisk (ثبت‌نام لازم)، LARS (قدیمی Ed.2)، ecalpro | **فرمول کامل single-risk و N_SG در Ed.3 (2024) از منابع آزاد در دسترس نبود**؛ باید متن استاندارد خریداری/مطالعه شود |
| LPS بیرونی (Air/Down/Earth) | SRC-THOR-LPS-2026، SRC-DEHN-SLIDES-2013، STD-IEC-62305-3-2024 (کاتالوگ) | SRC-REUVEN-RSM، OSS-LPO | جدول‌های IEC 62305-3:2024 در متن آزاد تأیید نشدند؛ DEHN slides مربوط به ۲۰۱۰/۲۰۱۱ هستند |
| جداسازی Separation | SRC-INDELEC-SEP-2026، SRC-DEHN-SLIDES-2013، PAP-ZISCHANK-ICLP، SRC-THOR-LPS-2026، SRC-ECALPRO-LIGHTNING، PAP-BRANDON-VAISALA | مثال DEHN slides (کیفری) | kc در شبکه‌های پیچیده و سقف فلزی به تحلیل عددی نیاز دارد؛ تعمیم قطعه‌به‌قطعه در منابع در دسترس صراحتاً به IEC نسبت داده نشده است |
| Earthing touch/step | STD-IEEE-80-2013، SRC-ECALPRO-EARTHING، SRC-WINDFARMBOP-IEEE80، SRC-FIRGELLIAUTO-EARTH | ماشین‌حساب SRC-ECALPRO-EARTHING، مثال ۱۱۵ kV windfarmbop | IEEE 80 صریحاً برای AC power-frequency fault است (استناد از صفحه کاتالوگ IEEE و دامنه استاندارد)؛ **اثر surgeهای صاعقه خارج از حوزه IEEE 80 است** (طبق REJECT A تأیید می‌شود). برای impulse earthing به CIGRE/IEC 62305-3 بند ۵.۴ و منابع تخصصی دیگر نیاز است |
| LPZ/LEMP/SPD | SRC-THOR-LPZ-2026، SRC-INDELEC-LPZ-2026، SRC-SB-SPD-2025، SRC-ITE-SPD-2023 | جدول‌های LPZ/SPD | قاعده "۱۰ m بین SPDها" در THOR/Indelec تکرار شده اما در منابع بررسی‌شده بند استاندارد برای آن یافت نشد |
| پست/شبکه برق | STD-IEEE-998-2012، PAP-BRANDON-VAISALA، STD-HORIZON-POWER-PCD | IEEE 998 Annex B (third-party PDF)، Horizon Power HPC-7DC-08-0001 (24 m شعاع RSM، فلوچارت رسمی) | تفاوت‌های Mousa/Eriksson در این پژوهش عمیقاً بررسی نشد |
| PV | STD-IEC-62548-2016، SRC-ITE (غیرمستقیم) | — | IEC 62548-1:2023+AMD1:2025 نسخه به‌روزتر است که در این پژوهش URL رسمی برای آن یافت نشد؛ IEC 61643-31/32 برای SPD PV جست‌وجو نشد |
| Wind | STD-IEC-61400-24 | (منبع ثانویه عمیق‌تر برای correction factorها در این پژوهش fetch نشد – در صورت نیاز باید جست‌وجوی مجزا انجام شود) | upward lightning و correction factorها در این پژوهش عمیقاً بررسی نشد |
| Telecommunications | SRC-ATECORP-ITU-K، SRC-ITU-K46-2003، SRC-ITU-K40-2019 | — | K.39/K.47 متن در این پژوهش fetch نشد |
| داده اقلیمی Ng | GEO-NOAA-LSD، GEO-VAISALA-ATDNET، GEO-NHESS-ATDNET، PAP-ENNO-2019 | محصول GRIB2 NOAA (رزولوشن و شرایط استفاده نیاز به بررسی مجزا دارد) | سرویس نقشه جهانی آزاد با رزولوشن مهندسی در جست‌وجوی انجام‌شده پیدا نشد؛ این یک یافته منفی محدود به منابع بررسی‌شده است و کلی‌گویی "موجود نیست" را توجیه نمی‌کند |
| هندسه 3D RSM | OSS-LPO، OSS-SFERA، COMM-SESSHILD، SRC-REUVEN-RSM | OSS-LPO (کاندید، هنوز LICENSE و test reproducibility بررسی نشده) | IFC import به وابستگی‌های اضافه نیاز دارد |

---

## ۳. ماتریس ادعاهای فرمولی

هر ادعا با وضعیت پشتیبانی و استناد دقیق به منبع (شامل بند/جدول در صورت دسترسی) بیان می‌شود.

### F1: فرم کلی `s = ki · (kc / km) · l`
- **وضعیت**: **SECONDARY SUPPORT** (به‌طور یکسان در چند منبع ثانویه بازتولید شده که خودشان به IEC 62305-3 ارجاع می‌دهند)
- **استنادها**:
  - SRC-INDELEC-SEP-2026 (Indelec blog): فرمول صریح در جدول، ارجاع به NF EN 62305-3:2024.
  - SRC-DEHN-SLIDES-2013: اسلاید ۶.۳.۱ (chunkIndex=1 در fetch_page): "The general equation for the calculation of s is given by: ki, km, kc … s = ki · (kc/km) · l [m]، با تعریف ki/km/kc/l به‌نقل از BS EN 62305-3:2011."
  - SRC-ECALPRO-LIGHTNING (FAQ separation distance): "Per IEC 62305-3 Clause 6.3, s = ki x (kc / km) x l."
  - PAP-ZISCHANK-ICLP (پیش‌چاپ): equation (1) همراه با توضیح، بخش Introduction.
  - PAP-BRANDON-VAISALA: equation (5)، که 62305-3 را با فرمول NFPA 780 کنار می‌گذارد.
- **صفحه کاتالوگ رسمی IEC 62305-3:2024 (STD-IEC-62305-3-2024)** فقط توصیف می‌کند که استاندارد «روش‌های ساده‌شده و عمومی» را پوشش می‌دهد (طبق REJECT)، اما خودِ فرمول و مقادیر از صفحه کاتالوگ خوانده نمی‌شود.

### F2: مقادیر ki: I=0.08، II=0.06، III+IV=0.04
- **وضعیت**: **SECONDARY SUPPORT** (در DEHN slides که رونوشت جدول ۱۰ BS EN 62305-3:2011 است، و در Zischank پیش‌چاپ، جداول با این اعداد آمده‌اند)
- **استنادها**:
  - SRC-DEHN-SLIDES-2013، اسلاید با عنوان "Isolation of external LPS – Values of coefficients ki and km"، جدول Class I=0.08, II=0.06, III and IV=0.04.
  - PAP-ZISCHANK-ICLP، Table 1: مقادیر ki در ستون به‌همراه i_max و di/dt.
- **مغایرت مشاهده‌شده (DISCREPANCY OBSERVED)**: SRC-ECALPRO-LIGHTNING FAQ می‌نویسد "ki depends on the protection level (0.04 for Level I, 0.06 for Level III)" که **با جدول‌های DEHN و Zischank در تضاد است**. این تضاد به‌عنوان یک خطای مشاهده‌شده در یکی از منابع عمومی ثبت می‌شود؛ **نتیجه‌گیری در مورد اینکه کدام درست است، مستلزم دسترسی به متن رسمی IEC 62305-3 (نسخه 2010 و 2024) است و در این مرحله انجام نمی‌شود**. در نسخه ۱.۰ این را به‌طور قطعی "اشتباه سایت" نامیده بودم؛ در این نسخه آن را صرفاً `DISCREPANCY OBSERVED` می‌نامم.

### F3: مقادیر km: air=1، concrete/brick=0.5
- **وضعیت**: **SECONDARY SUPPORT**
- **استنادها**:
  - SRC-DEHN-SLIDES-2013، جدول Insulating material: Air=1, Concrete/bricks=0.5, DEHNiso=0.7* (مقدار اختصاصی DEHN).
  - PAP-ZISCHANK-ICLP، Table 2.
  - SRC-ECALPRO-LIGHTNING FAQ separation distance: "km depends on the insulating material (1.0 for air, 0.5 for concrete)".
- **نکته**: DEHN note 1 می‌گوید وقتی مواد نارسانا به‌صورت سری باشند، باید از کمترین km استفاده کرد (نه جمع قطعه‌به‌قطعه).

### F4: kc ضریب تقسیم جریان
- **وضعیت**: **SECONDARY SUPPORT** برای ساختارهای ساده با جدول kc (1/0.66/0.44)؛ **UNVERIFIED** برای تعمیم به شبکه‌های پیچیده با روش Y·V=I
- **استنادها**:
  - SRC-DEHN-SLIDES-2013، جدول kc: 1 down-conductor=1 (فقط isolated LPS)، 2 down=0.66، 3+ down=0.44؛ با یادداشت در مورد Type B earthing و اختلاف مقاومت تا فاکتور ۲.
  - PAP-ZISCHANK-ICLP، equation (3)/(7) که kc را به تعداد n، فاصله c و ارتفاع h وابسته می‌کند؛ و نشان می‌دهد که برای سقف فلزی (natural air termination) تفاوت‌هایی با Annex C وجود دارد.

### F5: سیستم ماتریسی Y·V=I برای محاسبه kc در شبکه‌های مش
- **وضعیت**: **UNVERIFIED** به‌عنوان تجویز استاندارد؛ **به‌عنوان یک روش عددی اعمال‌پذیر** در مقالات به آن اشاره شده (PAP-ZISCHANK از "computer codes" و روش عددی استفاده می‌کند)، اما در منابع بررسی‌شده IEC این ماتریس ادمیتانس را تجویز نمی‌کند؛ استاندارد برای موارد ساده فرمول‌های Annex C را می‌دهد.
- **OBSERVATION FROM PROJECT MATERIALS**: مخزن Lightnin در `packages/domain-model/` و `docs/adr/ADR-003-GRAPH-SOLVER-FORMULATION.md` یک Graph Solver طراحی کرده است (خودم در این مرحله محتوای ADR را نخواندم، صرفاً از لیست فایل‌ها وجودش را ثبت می‌کنم)؛ ارزیابی صحت آن خارج از محدوده این مرحله است.

### F6: تعمیم قطعه‌به‌قطعه `s(P) = ki · Σ(kc,j / km,j · lj)` که در DOC-METH-001 آمده
- **وضعیت**: **UNVERIFIED** در مقابل متن IEC.
- **استنادهای مرتبط**:
  - SRC-DEHN-SLIDES-2013 note 1: "When there are several insulating materials in series, it is a good practice to use the lower value for km" – یعنی استاندارد/DEHN برای مواد سری، کمترین km را توصیه می‌کند، نه جمع kc/km روی قطعه‌ها.
  - Zischank/Indelec/ecalpro همگی فرمول را به‌شکل ساده s=ki·(kc/km)·l می‌نویسند.
  - تعمیم قطعه‌به‌قطعه در docs/21_METHOD_SPEC_SEPARATION_DISTANCE.md مخزن آمده و **یک تصمیم طراحی داخلی است** که بر اساس شواهد این جست‌وجو نمی‌تواند مستقیماً به IEC نسبت داده شود.

### F7: شعاع RSM و اندازه mesh / فاصله down-conductor
- **وضعیت برای شعاع RSM و mesh/down-conductor**: **SECONDARY SUPPORT** (چند منبع ثانویه جداول IEC 62305-3 را با اعداد 20/30/45/60 m و mesh 5/10/15/20 و down-conductor spacing 10/10/15/20 بازگو کرده‌اند).
- **استنادها**:
  - SRC-THOR-LPS-2026: جدول "LPS class / Rolling sphere radius / Mesh size / Max down-conductor spacing" (I=20/5×5/10، II=30/10×10/10، III=45/15×15/15، IV=60/20×20/20).
  - SRC-REUVEN-RSM: جدول LPL و شعاع، همراه با توضیح.
  - SRC-DEHN-SLIDES-2013: جدول rolling sphere/mesh/down-conductor (مقادیر مشابه).
  - SRC-ECALPRO-LIGHTNING FAQ: "sphere radius: 20m Level I … 60m Level IV (Table 2 of IEC 62305-3)؛ Down conductor spacing … Table 4: 10 m for LPL I and II, 15 m for LPL III, and 20 m".
- **فرمول rp=√(2Rh-h²) برای یک میله منفرد و A=πrp²**: **SECONDARY SUPPORT** (SRC-REUVEN-RSM صریحاً این فرمول‌ها را نوشته و مثال عددی با LPL II/h=10 m → 22.36 m/1571 m² داده). این فرمول از هندسه پایه کره غلتان می‌آید و در اکثر متون RSM مشترک است.
- **فرمول R=10·I^0.65 (کا به متر)**: **SECONDARY SUPPORT** (SRC-REUVEN-RSM فرمول را نوشته؛ PAP-HEIDLER-2008 به منشأ شکل‌گیری آن در IEC اشاره می‌کند؛ PAP-BRANDON-VAISALA از striking-distance EGM سخن می‌گوید). ثابت ۱۰ و توان ۰.۶۵ در استاندارد به پارامتر I_min هر LPL گره خورده و باید با متن استاندارد تأیید شود.

### F8: پارامترهای جریان صاعقه (200/150/100 kA اولیه مثبت، 50/37.5/25 kA برگشتی، di/dt 200/150/100 kA/µs)
- **وضعیت**: **SECONDARY SUPPORT** (پیش‌نمایش/کپی IEC 62305-1 و مقاله Heidler این اعداد را بازتولید می‌کنند)
- **استنادها**:
  - PAP-ZINO-PREVIEW (کپی IEC 62305-1 Ed.2): جداول first positive و subsequent شامل Q_SHORT 100/75/50 C و W/R 10/5.6/2.5 MJ/Ω و پارامترهای di/dt.
  - PAP-HEIDLER-2008: توضیح شکل‌گیری این اعداد از داده‌های Berger (۱۹۷۵) و توجیه 200 kA, 50 kA, 200 kA/µs.
- **احتیاط**: PAP-ZINO-PREVIEW کپی غیررسمی است. متن رسمی IEC 62305-1:2024 در این پژوهش مطالعه نشده.

### F9: R_T = 10⁻⁵ /year برای ریسک تلفات جانی
- **وضعیت**: **SECONDARY SUPPORT** (در SRC-ECALPRO-LIGHTNING و چندین صفحه دیگر تکرار شده)
- **احتیاط**: SRC-ECALPRO-LIGHTNING Ed.2 و Ed.3 را در انتخابگر دارد. مقدار R_T ممکن است در Ed.3 تغییر کرده باشد (متن IEC 62305-2:2024 در دسترس نیست). بنابراین این مقدار برای Ed.2 به‌صورت second-hand پشتیبانی می‌شود و برای Ed.3 **UNVERIFIED** است.

### F10: فرمول‌های IEEE 80 برای E_touch و E_step
- **وضعیت**: **SECONDARY SUPPORT** (برای فرمول‌های منتشرشده در منابع ثانویه)
- **استنادها**:
  - SRC-ECALPRO-EARTHING: E_touch = (1000+1.5 Cs ρ_s)·0.116/√t_s (نسخه 50 kg، ضریب 0.116).
  - SRC-FIRGELLIAUTO-EARTH: همان فرمول 50 kg.
  - SRC-WINDFARMBOP-IEEE80: فرمول 70 kg با ضریب 0.157 و مثال عددی 115 kV؛ Cs=1−0.09(1−ρ/ρ_s)/(2h_s+0.09)؛ Em=ρ·Km·Ki·IG/LM؛ Es=ρ·Ks·Ki·IG/LS.
- **احتیاط (مهم، از REJECT A)**: IEEE 80 اساساً برای خطای AC فرکانس قدرت در پست‌هاست. طبق صفحه رسمی IEEE (STD-IEEE-80-2013)، تحلیل کمی اثر surgeهای صاعقه در حوزه این استاندارد نیست. بنابراین استفاده از این فرمول‌ها در حوزه صاعقه باید با استاندارد/منبع مختص صاعقه ترکیب شود.

### F11: نگاشت LPZ به نوع SPD و مقادیر Iimp/In
- **وضعیت**: **SECONDARY SUPPORT** (برای نگاشت کلی)
- **استنادها**:
  - SRC-THOR-LPZ-2026: Type1 در LPZ 0A→LPZ1 با 10/350 µs، Type2 در 0B→1 یا 1→2 با 8/20 µs، Type3 در LPZ2→3.
  - SRC-INDELEC-LPZ-2026: جدول Iimp 25–100 kA Type1، 5–20 kA Type2، <5 kA Type3؛ Up ≤2.5/1.5/1.0 kV.
  - SRC-ECALPRO-LIGHTNING FAQ: "Type 1/Class I, tested with 10/350 µs؛ Type 2/Class II, tested with 8/20 µs؛ … typically 10 m of cable or a coordination inductor between stages."
- **احتیاط**: مقادیر عددی Iimp/In/Up جنبه نوعی/راهنمای تولیدکننده دارند و باید با IEC 62305-4 و IEC 61643-11/-31 در پروژه تطبیق داده شوند.

### F12: فرمول Uc≥Vrms, Up≤Uw, Up+ΔV≤Uw
- **وضعیت**: **SECONDARY SUPPORT** از منبع آموزشی (SRC-SB-SPD-2025) اما **UNVERIFIED** با متن IEC در این پژوهش. این‌ها اصول کلی هماهنگی SPD هستند که در متون فنی رایجند ولی بند دقیق استاندارد در منابع بررسی‌شده آورده نشده.

---

## ۴. ارزیابی نامزدهای Benchmark

در این نسخه عبارت "benchmark قوی مستقل" به‌کار نمی‌رود مگر اینکه ورودی/خروجی/روش/نسخه/مجوز همگی قابل‌بررسی باشند. هر نامزد با نقاط قوت و محدودیت ثبت می‌شود تا در مرحله بعد (اگر مجاز باشد) انتخاب و درستی‌سنجی شود.

### BC-REUVEN-RSM (candidate)
- **URL**: https://reuven.tools/tools/lightning-protection/
- **ورودی‌ها**: انتخاب LPL (I–IV) یا Ipeak، ارتفاع میله (h)، ارتفاع سازه.
- **خروجی‌های مرجع**: شعاع R (m)، rp (m)، سطح محافظت‌شده (m²)، mesh size (m)، protection angle (deg)، نشان "Mast ≥ sphere".
- **روش بازتولید (صریح در صفحه)**: R=20/30/45/60 m؛ R=10·I^0.65 برای Ipeak؛ rp=√(2Rh-h²) وقتی h<R، در غیر این صورت rp=R؛ A=πrp².
- **مثال عددی قابل‌بررسی**: LPL II (R=30 m)، h=10 m → rp=√(600-100)=√500≈22.36 m، Area=π·22.36²≈1571 m².
- **منشأ**: فرمول‌های صفحه به IEC 62305-3، NFPA 780، IEC 62305-1 ارجاع می‌دهد.
- **مجوز**: web app آزاد (embed نیز عرضه می‌کند)؛ مجوز کد مشخص نیست.
- **اعتبار/استقلال**: **نامزد بررسی** – ابزار از یک شخص/نهاد به نام "Reuven Engineering Tools" است که در این پژوهش مستقل یا وابسته‌بودن آن به تولیدکننده‌ای از محتوای صفحه قابل اثبات نبود. فرمول‌ها صریح‌اند و به‌راحتی در یک تست واحد بازتولید می‌شوند. تا قبل از cross-check با موارد دیگر، "مستقل" خطاب نمی‌شود.

### BC-OSS-LPO (candidate)
- **URL**: https://github.com/IndrekEdur/Lightning-Protection-Optimizer
- **ورودی‌ها**: project JSON شامل مش‌های بسته (سقف/تجهیزات)، میله‌های کاندیدا، پارامترهای بهینه‌سازی (هزینه/تعداد/دستی).
- **خروجی**: وضعیت "Protected" یا witness نقاط تماس کره، بهینه‌سازی هزینه/تعداد میله، JSON خروجی با samples بررسی‌شده.
- **روش**: analytical support-function بهینه با اثبات عدم‌تماس (نه point sampling)؛ بهینه‌سازی set-cover با HiGHS؛ IFC import.
- **نسخه (commit)**: آخرین commit بازبینی‌شده `927f1db0fb42b340279958ba0399c41003e710e7` مورخ ۲۰۲۶-۱۰-۲۷ (بخش‌های پیشین بنا بر web_search قاعدتاً 84 تست backend و regression/vite و IFC را شامل می‌شوند اما این در first-chunk fetch_page خوانده نشد و باید در مرحله بررسی benchmark با clone عمیق‌تر تأیید شود).
- **مجوز**: **LICENSE در صفحه ریشه‌ای که fetch_page خوانده، list نشده بود** – این باید در بررسی آتی تأیید شود (احتمالاً در فایل جداگانه است که در chunkهای بعدی README می‌آید).
- **اعتبار/استقلال**: **نامزد قوی برای بررسی بیشتر** – به‌وضوح disclaimer دارد که "No edition-wide IEC/EN compliance claim" و "LPS selects the rolling-sphere radius; edition remains metadata pending engineering validation." اما تا زمان بررسی LICENSE، اجرا و خواندن تست‌ها، "قوی‌ترین benchmark مستقل" خطاب نمی‌شود.
- **محدودیت**: separation distance، down-conductor current-sharing، risk assessment، earthing/touch/step را پوشش **نمی‌دهد** (بنابر README اولیه search result).

### BC-DEHNslides-ki-km-kc (sanity-check ثانویه)
- **URL**: https://ifsm.org.uk/wp-content/uploads/3-DEHN-UK-Lightning-prot-Physical-damage-to-structures-IFSM.pdf
- **ورودی/خروجی**: جدول‌های ثابت ki/km/kc و مقادیر RSM/mesh/down-conductor.
- **منشأ**: DEHN + SÖHNE، ارجاع به BS EN 62305-3:2011.
- **کاربرد**: به‌عنوان sanity-check برای مقادیر جدول در نسخه 2011، نه benchmark نرم‌افزاری.
- **احتیاط**: نسخه 2011 است و خروجی قابل بازتولید عددی با مسئله واقعی ارائه نمی‌دهد.

### BC-WINDFARMBOP-IEEE80-115kV (work-example candidate)
- **ورودی‌های مثال**: ρ=75 Ω·m، ρs=4000 Ω·m، hs=0.2 m، Ig=10,676 A، Lc=1300 m، Ks=0.308، Ki=2.23، Ls=943.5.
- **خروجی مرجع در مقاله**: Cs≈0.82؛ Etouch≈880V در مقابل Etouch_tol(70 kg)=1314V؛ Estep≈583V در مقابل Estep_tol≈4590V.
- **کاربرد**: می‌تواند یک worked example برای mesh/step voltage باشد اما باید (الف) با فرمول‌های واقعی IEEE 80-2013 تطبیق داده شود و (ب) توجه شود که حوزه IEEE 80 AC fault است نه impulse صاعقه.

### BC-LARS (candidate, legacy)
- **نسخه**: LARS 3.0.2 (2014).
- **استاندارد**: IEC 62305-2 Ed.2 (2010).
- **پلتفرم**: Windows/Linux/BSD، GUI.
- **وضعیت نگهداری**: متوقف (last release 2014).
- **کاربرد**: می‌تواند برای sanity-check ریسک Ed.2 استفاده شود اما به‌عنوان مرجع نهایی قابل اتکا نیست.

### BC-DEHNrisk (candidate vendor tool)
- **استاندارد**: IEC 62305-2 Ed.3 (2024) و نسخه‌های ملی.
- **نیازمندی**: ثبت‌نام SaaS.
- **وابستگی**: تولیدکننده (DEHN).
- **کاربرد**: cross-check ریسک Ed.3 اما به‌عنوان مرجع مستقل نمی‌تواند استفاده شود.

### BC-NOAA-GLD360-GRIB2 (داده اقلیمی)
- **توصیف**: GEO-NOAA-LSD.
- **محتوا**: تعداد strikes per square meter per second بر مبنای GLD360/NLDN، محصول Level 5 NOAA.
- **واحدها**: strikes/m²/s SI؛ مقیاس رندر strikes/km²/min نیازمند ضریب 10^3 است.
- **محدودیت**: راندمان/detection efficiency و دقت میانه (≤5 km) در صفحه NOAA توصیف شده؛ استفاده مهندسی برای Ng مستلزم تبدیل به flashes/km²/year و تطبیق با تعریف IEC 62305-2 است. این موضوع باید در مرحله تخصصی داده/ریسک بررسی شود.

### BC-IEEE998-AnnexB (candidate for substation)
- **مثال‌های عددی** برای shield wire (30.48 m بلند) و جداول محاسبات rolling sphere در ضمیمه B (بنابر فهرست مندرجات PDF mirror).
- **احتیاط**: PDF از third-party mirror است و باید اصالتش در مقایسه با نسخه رسمى IEEE تأیید شود.

---

## ۵. موانع دسترسی، یافته‌های منفی محدود و سؤال‌ها

### ۵-۱. موانع دسترسی
1. متن رسمی استانداردهای IEC 62305-x (2024 و 2010) و IEEE 80-2013/IEEE 998-2012 پولی است. مقادیر جدول‌ها/بندها در این گزارش همگی از منابع ثانویه آمده‌اند.
2. IEC 62305-2 Ed.3 (2024) تغییر ساختار به single risk و N_SG (که A در REJECT به آن اشاره کرده) فقط از صفحه کاتالوگ و DEHNrisk قابل استنباط است؛ فرمول‌های این نسخه در منابع آزاد یافت نشد.
3. داده‌های تجاری Ng (GLD360 کامل، NLDN، EUCLID) وابسته به قرارداد هستند.

### ۵-۲. یافته‌های منفی محدود شده به منابع بررسی‌شده
- "در مجموعه منابع این پژوهش، سرویس نقشه جهانی آزاد با رزولوشن مناسب ورودی مهندسی Ng (با شرایط استفاده/مجوز برای استفاده در نرم‌افزار تجاری) پیدا نشد." – این نسبت به ادعای کلی نسخه ۱.۰ تضعیف و مستند شده است.
- "بند استانداردی که قاعده 'فاصله ۱۰ متری بین SPDها' را تجویز کند، در منابع آزاد بررسی‌شده یافت نشد." (از THOR/ecalpro به‌عنوان راهنمای نصب آمده اما بند استاندارد مشخص نیست).

### ۵-۳. تعارضات و ابهامات
1. **DISCREPANCY در ki (F2)**: ECalPro FAQ ki(I)=0.04, ki(III)=0.06 می‌نویسد که با DEHN slides (I=0.08, III+IV=0.04) و Zischank در تضاد است.
2. **دوگانگی ضریب در فرمول‌های IEEE 80**: منابع از ضریب 0.116 (50 kg، نسخه‌های قدیمی) و 0.157 (70 kg، نسخه ۲۰۰۰ به بعد/2013) استفاده می‌کنند؛ باید وزن بدن و نسخه استاندارد به‌صراحت انتخاب شود.
3. **حوزه IEEE 80**: این استاندارد برای خطای AC فرکانس‌قدرت است و اثر surge صاعقه خارج از حوزه آن است (تأیید A) – استفاده از آن در حوزه صاعقه نیاز به الحاق منابع تخصصی دارد.
4. **تعمیم segment-by-segment (F6)**: در منابع بررسی‌شده صراحتاً پشتیبان از آن یافت نشد.
5. **وضعیت شاخه**: پژوهش اولیه روی sandbox-prefixed شاخه صورت گرفت؛ در زمان commit نهایی شاخه مجاز `arena/461d9c97-lightnin` توسط A روی `origin` ایجاد و در این sandbox fetch/checkout شد. گزارش نهایی روی شاخه مجاز تحویل می‌شود.

### ۵-۴. نیاز به مهندس/بازبینی مستقل (فهرست موارد)
- تطبیق نهایی مقادیر ki/km/kc و تعاریف آن‌ها بر روی IEC 62305-3:2024 (متن کامل).
- اعتبار روش nodal Y·V=I در مقابل Annex C IEC و/یا روش‌های عددی (MoM/EM-field).
- استفاده صحیح از IEEE 80 در حوزه صاعقه (impulse ground impedance).
- منبع داده Ng در محدوده‌های جغرافیایی هدف (ملی یا تجاری).

---

## ۶. پرسش‌هایی برای هماهنگ‌کننده A
1. (انجام‌شده در بازکاری نهایی): شاخه `arena/461d9c97-lightnin` توسط A روی `origin` ایجاد و این مجری روی آن checkout شد.
2. آیا پشتیبانی هم‌زمان IEC 62305:2010 و IEC 62305:2024 هدف است یا فقط 2024؟
3. اولویت کدام حوزه‌های قضایی است (NFPA 780، AS/NZS 1768، VDE/DIN EN، BS EN، UNE 21.186، NFC 17.102)؟
4. آیا A می‌تواند دسترسی رسمی به متن استانداردهای پولی لازم (به‌ویژه IEC 62305-x:2024 و IEEE 80/998) برای این پروژه فراهم کند تا مقادیر جدول‌ها و فرمول‌ها نهایی و قطعی شوند؟
5. آیا برای Ng ادغام با یک سرویس مشخص (GLD360/EUCLID/ملی هواشناسی) هدف است یا کاربر مقدار را دستی وارد می‌کند؟
6. آیا باید تعمیم segment-by-segment جمع kc/km (DOC-METH-001 بند ۳) توسط مهندس مسئول به‌عنوان انطباق با IEC 62305-3:2024 تأیید شود؟
7. اولویت بررسی benchmarkها: آیا BC-REUVEN-RSM برای RSM تک‌میله و BC-OSS-LPO برای 3D RSM پیوسته در مراحل بعد (با مجوز A) اعتبارسنجی شوند؟

---

## ۷. وضعیت مخزن
- در پایان پژوهش و در حین بازکاری، گزارش نهایی در `docs/36_P0-S1_SOURCE_BENCHMARK_DISCOVERY_REPORT.md` به مخزن اضافه شد (طبق دستور جدید A).
- `base_commit`: `0c9c823a945d895c1a1c9b903e236b1a8cb4a421`.
- commit این مرحله (P0-S1 v1.1) تنها افزودن همین فایل است و هیچ کد/فایل اجرایی/مستندات دیگر را تغییر نمی‌دهد.
- شاخه نهایی: `arena/461d9c97-lightnin`، push به `origin/arena/461d9c97-lightnin`.

## ۸. بررسی‌ها و وابستگی‌ها
هیچ dependency نصب نشده، هیچ اجرای نرم‌افزار/تستی در کد انجام نشده (نوع کار تحقیق مستند). ابزارهای استفاده‌شده: `git status`، `git rev-parse`، `git diff --check`، `find`، `read_file`، `web_search`، `fetch_page`. فرمان‌های کیفیت اجراشده: `git diff --check` (پیش از commit) – خروجی تمیز.

## ۹. فایل‌های تغییرکرده در مخزن
- **افزوده‌شده**: `docs/36_P0-S1_SOURCE_BENCHMARK_DISCOVERY_REPORT.md` (گزارش پژوهشی P0-S1 v1.1)
- **تغییریافته**: هیچ‌یک از فایل‌های کد/مستندات موجود تغییر نکرده‌اند.

---

*پایان گزارش P0-S1 v1.1. منتظر پاسخ PASS / REJECT / BLOCKED از سوی هماهنگ‌کننده A می‌مانم.*
