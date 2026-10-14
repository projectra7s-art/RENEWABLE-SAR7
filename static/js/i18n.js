// Arabic / English text for the whole page.
//
//  - Static HTML uses  data-i18n="key"  (text),  data-i18n-placeholder="key",
//    data-i18n-title="key".
//  - JavaScript uses  t("key", { name: value }).
//
// To translate a new sentence: add the key to BOTH languages below.

const DICT = {
  ar: {
    "title": "RE-SIZER | تصميم نظام الطاقة المتجددة",
    "lang.switch": "English",

    // ---- hero
    "hero.text": "اختر موقعك على الخريطة وأدخل استهلاكك الشهري. نحسب لك أرخص نظام يحقق نسبة الطاقة المتجددة التي تريدها، من بيانات الشمس والرياح الساعية لموقعك.",
    // ---- step 1: location
    "loc.lat": "خط العرض (Latitude)",
    "loc.lon": "خط الطول (Longitude)",
    "loc.elev": "الارتفاع عن سطح البحر",
    "loc.elev.loading": "جاري الحساب...",
    "loc.elev.na": "غير متاح",

    // ---- step 2: consumption
    "tab.monthly": "استهلاك شهري (12 شهرًا)",
    "tab.file": "ملف ساعي",
    "fill.label": "تعبئة كل الأشهر بنفس القيمة",
    "fill.button": "تعبئة",
    "month.1": "يناير", "month.2": "فبراير", "month.3": "مارس",
    "month.4": "أبريل", "month.5": "مايو", "month.6": "يونيو",
    "month.7": "يوليو", "month.8": "أغسطس", "month.9": "سبتمبر",
    "month.10": "أكتوبر", "month.11": "نوفمبر", "month.12": "ديسمبر",

    "file.label": "ملف الحمل الساعي (CSV أو TXT)",
    "file.hint":
      "قيمة واحدة لكل ساعة بوحدة kWh: 8760 سطرًا (8784 في السنة الكبيسة) " +
      "تبدأ من 1 يناير الساعة 00:00. إذا كان في الملف أعمدة أخرى يؤخذ العمود الذي " +
      "عنوانه load أو demand أو consumption أو حمل، وإلا آخر عمود رقمي؛ ويتم تجاهل سطر العناوين. من Excel احفظه بصيغة CSV.",
    "file.none": "لم يتم اختيار ملف.",
    "file.ok": "تمت قراءة {count} قيمة • المجموع {total} kWh في السنة • المتوسط {avg} kW",
    "file.bad_count":
      "عدد القيم في الملف ({count}) غير صحيح. المطلوب 8760 (أو 8784).",
    "file.read_error": "تعذّرت قراءة الملف.",

    "target.label": "نسبة الطاقة المتجددة المطلوبة",
    "target.hint":
      "سيبحث النظام عن أقل تكلفة تغطي هذه النسبة من استهلاك المنزل بالطاقة " +
      "المتجددة، والباقي يُشترى من الشبكة.",

    "adv.title": "إعدادات متقدمة",
    "adv.elev.label": "تعديل الارتفاع يدويًا (م) — اختياري",
    "adv.elev.hint": "الارتفاع يُؤخذ تلقائيًا من الخريطة عند اختيار الموقع. اكتب قيمة هنا فقط إذا كنت تعرف ارتفاع موقعك بدقة أكبر. الارتفاع يقلل كثافة الهواء وبالتالي طاقة الرياح، ويُصحَّح به درجة الحرارة.",
    "adv.year.label": "سنة بيانات NASA POWER",

    "run": "تشغيل التحليل والتحسين",
    "running": "جاري التحليل...",

    "loading.title": "جاري الحساب...",
    "loading.text":
      "جاري جلب بيانات NASA POWER وتشغيل PSO للسيناريوهات الثلاثة على " +
      "البيانات الساعية. قد يستغرق ذلك حوالي نصف دقيقة.",

    // ---- results: scenarios
    "res.title": "النتائج والمقارنة",
    "res.hint": "الموصى به هو الأرخص في التكلفة السنوية (تكلفة المعدات موزّعة على أعمارها + فاتورة الشبكة) من بين السيناريوهات التي تحقق الهدف. اضغط على أي سيناريو لعرض تفاصيله.",
    "scn.solar_battery": "شمسي + بطارية",
    "scn.wind_battery": "رياح + بطارية",
    "scn.hybrid": "هجين (شمسي + رياح + بطارية)",
    "scn.solar_battery.desc": "ألواح شمسية، مع بطارية إذا خفّضت التكلفة أو لتحقيق الهدف.",
    "scn.wind_battery.desc": "توربينات رياح، مع بطارية إذا خفّضت التكلفة أو لتحقيق الهدف.",
    "scn.hybrid.desc": "لوح واحد وتوربين واحد على الأقل، مع بطارية عند الحاجة.",
    "scn.badge.cheapest": "موصى به",
    "scn.badge.unmet": "لا يحقق الهدف",
    "scn.pv": "ألواح PV",
    "scn.wind": "توربينات الرياح",
    "scn.battery": "البطاريات",
    "scn.capex": "التكلفة الإجمالية",
    "scn.rf": "نسبة الطاقة المتجددة",
    "scn.choose": "عرض التفاصيل",
    "scn.details": "تفاصيل السيناريو: {label}",

    // ---- results: cards
    "kpi.pv": "ألواح PV",
    "kpi.wind": "توربينات الرياح",
    "kpi.battery": "وحدات البطارية",
    "kpi.coverage": "التغطية بالطاقة المتجددة",
    "kpi.of_demand": "من إجمالي الطلب",
    "kpi.type": "النوع",
    "kpi.panel_w": "قدرة اللوح",
    "kpi.price_panel": "السعر/لوح",
    "kpi.turbine_kw": "قدرة التوربين",
    "kpi.hub": "ارتفاع المحور",
    "kpi.price_turbine": "السعر/توربين",
    "kpi.unit_kwh": "سعة الوحدة (القابلة للاستخدام)",
    "kpi.price_unit": "السعر/وحدة",
    "kpi.target": "الهدف المطلوب",
    "kpi.status": "الحالة",
    "kpi.met": "تحقق الهدف",
    "kpi.unmet": "أقل من الهدف",
    "kpi.unused": "غير مستخدم في هذا السيناريو",

    // ---- results: cost & performance
    "cost.title": "التكلفة والأداء",
    "cost.annualized": "القسط السنوي لرأس المال",
    "cost.total_year": "التكلفة السنوية الإجمالية (قسط + شبكة)",
    "cost.grid_kwh": "الطاقة من الشبكة سنويًا",
    "cost.grid_sar": "تكلفة الشبكة السنوية التقديرية",
    "cost.generated": "الطاقة المتجددة المولّدة",
    "cost.served": "الطاقة المتجددة المستخدمة",
    "cost.curtailed": "الطاقة الفائضة غير المستخدمة (Curtailed)",
    "cost.export": "إيراد تصدير الفائض للشبكة",
    "cost.unserved": "الطاقة غير الملباة (Unserved)",

    // ---- results: site
    "site.title": "ملخص الموقع والطقس",
    "site.hours": "ساعات NASA الصالحة",
    "site.year": "سنة البيانات",
    "site.elev": "ارتفاع الموقع",
    "site.solar": "متوسط الإشعاع الشمسي",
    "site.temp": "متوسط درجة الحرارة",
    "site.wind10": "متوسط سرعة الرياح على 10 م",
    "site.wind_hub": "متوسط سرعة الرياح عند ارتفاع المحور",
    "site.shear": "معامل تدرّج الرياح (shear)",
    "site.rho": "كثافة الهواء المتوسطة",
    "site.load_avg": "متوسط الحمل",
    "site.load_month": "الاستهلاك الشهري (متوسط)",
    "site.load_year": "الاستهلاك السنوي",
    "site.method": "طريقة إدخال الاستهلاك",
    "src.user": "أدخلته أنت",
    "src.DEM": "نموذج ارتفاع DEM",
    "src.NASA": "من NASA",
    "src.default": "افتراضي (مستوى البحر)",
    "src.shear.nasa": "محسوب من NASA",
    "src.shear.default": "افتراضي",
    "method.monthly_kwh": "12 قيمة شهرية (kWh)",
    "method.hourly_file": "ملف ساعي",

    // ---- results: cost of one generated kWh
    "cmp.title": "تكلفة الطاقة المولّدة في هذا الموقع",
    "cmp.pv": "لوح PV",
    "cmp.wind": "توربين رياح",
    "cmp.wind_worse": "في هذا الموقع كل kWh من الرياح أغلى {ratio} مرة من الألواح.",
    "cmp.wind_better": "في هذا الموقع كل kWh من الرياح أرخص من الألواح (بنسبة {ratio} من تكلفتها).",
    "cmp.similar": "تكلفة الطاقة من الرياح والألواح متقاربة في هذا الموقع.",
    "cmp.note":
      " المقارنة للمولّد فقط؛ الرياح قد تخفّض حجم البطارية لأنها تعمل ليلًا، " +
      "لذلك قارن السيناريوهات في الأعلى.",

    // ---- results: charts
    "chart.day.title": "منحنى يومي (متوسط كل ساعة)",
    "chart.day.desc":
      "متوسط كل ساعة من ساعات اليوم على مدى {period} (وليس أول 24 ساعة " +
      "فقط)، بالتوقيت الشمسي المحلي لبيانات NASA.",
    "chart.period": "الفترة",
    "chart.whole_year": "السنة كاملة",
    "chart.load": "الحمل (kW)",
    "chart.renewable": "الطاقة المتجددة (kW)",
    "chart.grid": "الشبكة (kW)",
    // ---- notices / footer
    "notice.grid.title": "الربط بالشبكة:",
    "notice.grid.text":
      "النظام يُحسب كنظام مربوط بالشبكة، والشبكة تغطي أي عجز. الطاقة الفائضة " +
      "لا تُباع افتراضيًا (سعر التغذية العكسية = 0 في config.py). للتنفيذ " +
      "الفعلي يلزم طلب الربط وموافقة شركة الكهرباء وشروط العداد ثنائي الاتجاه " +
      "(Net Metering).",
    "notice.eng.title": "تنبيه هندسي:",
    "notice.eng.text":
      "النتائج تقديرية لغرض الدراسة والتصميم الأولي. يجب استبدال مواصفات " +
      "المكونات العامة ببيانات الشركات والمكونات المختارة، ومراجعة الكابلات " +
      "والعاكسات والحماية والاشتراطات المحلية قبل أي تنفيذ فعلي.",
    "footer.left": "RE-SIZER • PSO + NASA POWER",
    "footer.credits":
      "بيانات الطقس: NASA POWER • الارتفاع: Copernicus DEM عبر Open-Meteo • الخريطة: OpenStreetMap",

    // ---- errors (client side)
    "err.no_location": "حدد موقع المنزل من الخريطة أولًا.",
    "err.target": "أدخل نسبة تغطية بالطاقة المتجددة بين 1% و100%.",
    "err.months": "أدخل قيمًا صحيحة للأشهر (واحدة منها على الأقل أكبر من صفر).",
    "err.file_missing": "اختر ملف الحمل الساعي أولًا.",
    "err.elevation": "أدخل ارتفاعًا صحيحًا بالمتر أو اتركه فارغًا.",
    "err.server": "تعذّر إكمال التحليل (رمز الخطأ {status}). حاول مرة أخرى.",
    "nav.home": "الرئيسية",
    "nav.analysis": "التحليل",
    "nav.results": "النتائج",
    "nav.about": "عن المشروع",
    "nav.help": "مساعدة",
    "hero.title1": "كم لوحًا وتوربينًا وبطارية يحتاج بيتك؟",
    "hero.title2": "أنظف",
    "chip.data.t": "بيانات ساعية",
    "chip.data.s": "من NASA POWER لموقعك",
    "chip.pso.t": "أقل تكلفة",
    "chip.pso.s": "بخوارزمية سرب الجسيمات (PSO)",
    "chip.scen.t": "ثلاثة أنظمة",
    "chip.scen.s": "شمسي، رياح، هجين",
    "chip.global.t": "تغطية عالمية",
    "chip.global.s": "أي مكان في العالم",
    "step.location": "اختر الموقع",
    "step.consumption": "استهلاك الطاقة",
    "step.prefs": "تفضيلات النظام",
    "loc.search": "ابحث عن موقع...",
    "loc.search.none": "لم يتم العثور على المكان.",
    "pv.factor.label": "معامل أداء الألواح (PV Performance Factor)",
    "pv.factor.hint": "الخسائر غير الحرارية: غبار وكابلات وعاكس. الحرارة تُحسب بشكل منفصل من بيانات NASA.",
    "batt.eff.label": "كفاءة البطارية (Round-trip)",
    "batt.eff.hint": "نسبة الطاقة العائدة من البطارية بعد الشحن والتفريغ.",
    "tab.overview": "نظرة عامة",
    "tab.solar_battery": "شمسي + بطارية",
    "tab.wind_battery": "رياح + بطارية",
    "tab.hybrid": "هجين + بطارية",
    "chart.monthly.title": "الإنتاج الشهري مقابل الحمل",
    "chart.monthly.solar": "شمسي",
    "chart.monthly.wind": "رياح",
    "chart.monthly.load": "الحمل",
    "chart.mix.title": "مصدر الطاقة السنوي",
    "chart.mix.solar": "شمسي",
    "chart.mix.wind": "رياح",
    "chart.mix.grid": "الشبكة",
    "chart.mix.desc": "نسبة الطلب السنوي التي غطّاها كل مصدر (طاقة البطارية تُنسب للشمس والرياح بنسبة إنتاجهما).",
    "about.title": "عن المشروع",
    "about.text": "RE-SIZER أداة لتحديد حجم نظام الطاقة المتجددة للمنزل. تُجلب بيانات الإشعاع الشمسي والرياح ودرجة الحرارة الساعية من NASA POWER لموقعك، ثم تبحث خوارزمية سرب الجسيمات (PSO) عن أقل تكلفة سنوية تحقق نسبة الطاقة المتجددة المطلوبة، وذلك لكل سيناريو: شمسي + بطارية، رياح + بطارية، هجين.",
    "help.title": "مساعدة",
    "help.q1": "كيف أدخل استهلاكي؟",
    "help.a1": "أدخل kWh لكل شهر من فواتيرك، للأدق ارفع ملف الحمل الساعي.",
    "help.q2": "ماذا تعني نسبة الطاقة المتجددة المطلوبة؟",
    "help.a2": "هي الحصة من استهلاك المنزل التي يجب أن تغطيها الشمس والرياح (مباشرة أو عبر البطارية). الباقي تشتريه من الشبكة.",
    "help.q3": "لماذا يظهر عدد توربينات الرياح صفر؟",
    "help.a3": "لأن تكلفة الطاقة من الرياح في موقعك أعلى من الألواح. قارن التكلفتين في لوحة «تكلفة الطاقة المولّدة» داخل تفاصيل أي سيناريو.",
    "help.q4": "كم يستغرق التحليل؟",
    "help.a4": "من 10 ثوانٍ إلى نصف دقيقة تقريبًا لأنه يحسب 8760 ساعة لكل سيناريو.",
    "band.1.t": "تغطية عالمية",
    "band.1.s": "في أي مكان بالعالم",
    "band.2.t": "بيانات NASA حقيقية",
    "band.2.s": "الشمس والرياح",
    "band.3.t": "تحسين ذكي",
    "band.3.s": "خوارزمية سرب الجسيمات",
    "band.4.t": "مستقبل مستدام",
    "band.4.s": "أنظف. أذكى. أخضر.",
    "err.pv_factor": "أدخل معامل أداء بين 0.30 و1.00.",
    "err.batt_eff": "أدخل كفاءة بطارية بين 0.50 و1.00.",
    "theme.dark": "الوضع الليلي",
    "theme.light": "الوضع النهاري",
    "climate.title": "مناخ الموقع",
    "climate.solar": "متوسط الإشعاع الشمسي",
    "climate.wind": "متوسط سرعة الرياح (10 م)",
    "climate.temp": "متوسط الحرارة في الموقع",
    "climate.elev": "الارتفاع عن سطح البحر",
    "scn.badge.limit": "لا يحقق الهدف حتى بالحد الأقصى",
    "cost.capex": "التكلفة الإجمالية (تُدفع مرة واحدة)",
    "cost.explain.title": "كيف حُسبت التكلفة؟",
    "cost.col.item": "البند",
    "cost.col.unit": "سعر القطعة الواحدة",
    "cost.col.qty": "العدد",
    "cost.col.total": "الإجمالي",
    "cost.item.pv": "لوح شمسي",
    "cost.item.wind": "توربين رياح",
    "cost.item.battery": "بطارية",
    "cost.item.inverter": "العاكس",
    "cost.item.bos": "التركيب والكابلات والحماية (BOS)",
    "cost.row.total": "المجموع",
    "cost.explain.1": "التكلفة الإجمالية تُدفع مرة واحدة = سعر القطعة الواحدة × العدد، لكل بند.",
    "site.temp_corr": "تصحيح الحرارة لارتفاع الموقع",
    "elev.auto": "يُحدَّد تلقائيًا من الخريطة",
    "cons.file_or_months": "أدخل استهلاك كل شهر بوحدة kWh، أو ارفع ملف الحمل الساعي.",
    "cost.note": "أسعار اللوح والتوربين والبطارية هي للمعدة فقط، بدون التركيب. التركيب والكابلات والحماية في بند BOS (مبلغ واحد للنظام يُعدَّل من config.py)، والعاكس بند مستقل.",
    "limit.pv": "الألواح ({n})",
    "limit.wind": "التوربينات ({n})",
    "limit.battery": "البطاريات ({n})",
    "notice.limit": "وصل هذا السيناريو إلى الحد الأقصى المسموح: {items}، ومع ذلك لا يحقق الهدف (نسبة {rf}% من {target}%). لذلك لا يُوصى به، وهو معروض للمقارنة فقط. يمكن رفع الحدود من config.py (max_pv_panels وmax_wind_turbines وmax_batteries) لكن التكلفة ترتفع بشكل كبير.",
  },

  en: {
    "title": "RE-SIZER | Renewable Energy System Sizing",
    "lang.switch": "العربية",

    "hero.text": "Pick your location on the map and enter your monthly use. RE-SIZER finds the cheapest system that reaches your renewable target, using hourly sun and wind data for that spot.",
    "loc.lat": "Latitude",
    "loc.lon": "Longitude",
    "loc.elev": "Elevation above sea level",
    "loc.elev.loading": "Looking up...",
    "loc.elev.na": "Not available",

    "tab.monthly": "Monthly (12 months)",
    "tab.file": "Hourly file",
    "fill.label": "Fill all months with the same value",
    "fill.button": "Fill",
    "month.1": "January", "month.2": "February", "month.3": "March",
    "month.4": "April", "month.5": "May", "month.6": "June",
    "month.7": "July", "month.8": "August", "month.9": "September",
    "month.10": "October", "month.11": "November", "month.12": "December",

    "file.label": "Hourly load file (CSV or TXT)",
    "file.hint":
      "One value per hour in kWh: 8760 lines (8784 in a leap year) starting " +
      "on 1 January at 00:00. If the file has other columns, the one whose header says load, demand or " +
      "consumption is used, otherwise the last numeric column; a header line is ignored. From Excel, save as CSV.",
    "file.none": "No file selected.",
    "file.ok": "Read {count} values • total {total} kWh per year • average {avg} kW",
    "file.bad_count":
      "The number of values in the file ({count}) is not valid. 8760 (or 8784) are required.",
    "file.read_error": "The file could not be read.",

    "target.label": "Target Renewable Fraction",
    "target.hint":
      "The system looks for the cheapest design that covers this share of " +
      "the home's consumption with renewable energy; the rest is bought from " +
      "the grid.",

    "adv.title": "Advanced settings",
    "adv.elev.label": "Override the elevation (m) — optional",
    "adv.elev.hint": "The elevation is taken automatically from the map when you choose the location. Type a value here only if you know your site's elevation more accurately. Elevation lowers air density (less wind power) and corrects the temperature.",
    "adv.year.label": "NASA POWER data year",

    "run": "Run Optimization",
    "running": "Analyzing...",

    "loading.title": "Calculating...",
    "loading.text":
      "Fetching NASA POWER data and running PSO for the three scenarios on " +
      "hourly data. This can take about half a minute.",

    "res.title": "Results & Comparison",
    "res.hint": "The recommended one is the cheapest in yearly cost (equipment cost spread over its life + the grid bill) among the scenarios that reach the target. Click a scenario to see its details.",
    "scn.solar_battery": "Solar + Battery",
    "scn.wind_battery": "Wind + Battery",
    "scn.hybrid": "Hybrid (PV + Wind + Battery)",
    "scn.solar_battery.desc": "Solar panels, with a battery if it lowers the cost or is needed for the target.",
    "scn.wind_battery.desc": "Wind turbines, with a battery if it lowers the cost or is needed for the target.",
    "scn.hybrid.desc": "At least one panel and one turbine, with a battery when needed.",
    "scn.badge.cheapest": "Recommended",
    "scn.badge.unmet": "Target not met",
    "scn.pv": "PV Panels",
    "scn.wind": "Wind Turbines",
    "scn.battery": "Batteries",
    "scn.capex": "Total Cost",
    "scn.rf": "Renewable Fraction",
    "scn.choose": "View details",
    "scn.details": "Scenario details: {label}",

    "kpi.pv": "PV panels",
    "kpi.wind": "Wind turbines",
    "kpi.battery": "Battery units",
    "kpi.coverage": "Renewable coverage",
    "kpi.of_demand": "of total demand",
    "kpi.type": "Model",
    "kpi.panel_w": "Panel rating",
    "kpi.price_panel": "Price / panel",
    "kpi.turbine_kw": "Turbine rating",
    "kpi.hub": "Hub height",
    "kpi.price_turbine": "Price / turbine",
    "kpi.unit_kwh": "Unit capacity (usable)",
    "kpi.price_unit": "Price / unit",
    "kpi.target": "Required target",
    "kpi.status": "Status",
    "kpi.met": "Target met",
    "kpi.unmet": "Below target",
    "kpi.unused": "Not used in this scenario",

    "cost.title": "Cost & performance",
    "cost.annualized": "Yearly capital charge",
    "cost.total_year": "Total yearly cost (capital + grid)",
    "cost.grid_kwh": "Energy from the grid per year",
    "cost.grid_sar": "Estimated yearly grid cost",
    "cost.generated": "Renewable energy generated",
    "cost.served": "Renewable energy used",
    "cost.curtailed": "Unused surplus energy (curtailed)",
    "cost.export": "Revenue from exporting the surplus",
    "cost.unserved": "Unserved energy",

    "site.title": "Site & weather summary",
    "site.hours": "Valid NASA hours",
    "site.year": "Data year",
    "site.elev": "Site elevation",
    "site.solar": "Average solar irradiance",
    "site.temp": "Average temperature",
    "site.wind10": "Average wind speed at 10 m",
    "site.wind_hub": "Average wind speed at hub height",
    "site.shear": "Wind shear exponent",
    "site.rho": "Average air density",
    "site.load_avg": "Average load",
    "site.load_month": "Monthly consumption (average)",
    "site.load_year": "Yearly consumption",
    "site.method": "Consumption input",
    "src.user": "entered by you",
    "src.DEM": "DEM elevation model",
    "src.NASA": "from NASA",
    "src.default": "default (sea level)",
    "src.shear.nasa": "computed from NASA",
    "src.shear.default": "default",
    "method.monthly_kwh": "12 monthly values (kWh)",
    "method.hourly_file": "Hourly file",

    "cmp.title": "Cost of generated energy at this site",
    "cmp.pv": "PV panel",
    "cmp.wind": "Wind turbine",
    "cmp.wind_worse": "At this site each kWh from wind costs {ratio}× more than from panels.",
    "cmp.wind_better": "At this site each kWh from wind is cheaper than from panels ({ratio} of their cost).",
    "cmp.similar": "Wind and PV energy cost about the same at this site.",
    "cmp.note":
      " This compares the generators only; wind may shrink the battery because " +
      "it also blows at night, so compare the scenarios above.",

    "chart.day.title": "Daily curve (average of each hour)",
    "chart.day.desc":
      "Average of every hour of the day over {period} (not just the first " +
      "24 hours), in NASA's local solar time.",
    "chart.period": "Period",
    "chart.whole_year": "Whole year",
    "chart.load": "Load (kW)",
    "chart.renewable": "Renewable (kW)",
    "chart.grid": "Grid (kW)",
    "notice.grid.title": "Grid connection:",
    "notice.grid.text":
      "The system is modelled as grid-tied and the grid covers any shortfall. " +
      "Surplus energy is not sold by default (feed-in tariff = 0 in " +
      "config.py). A real installation needs an interconnection request, the " +
      "utility's approval and a bidirectional meter (net metering).",
    "notice.eng.title": "Engineering notice:",
    "notice.eng.text":
      "Results are estimates for study and preliminary design. Replace the " +
      "generic component data with the chosen manufacturers' data and review " +
      "cables, inverters, protection and local requirements before any real " +
      "installation.",
    "footer.left": "RE-SIZER • PSO + NASA POWER",
    "footer.credits":
      "Weather: NASA POWER • Elevation: Copernicus DEM via Open-Meteo • Map: OpenStreetMap",

    "err.no_location": "Select the house location on the map first.",
    "err.target": "Enter a renewable coverage between 1% and 100%.",
    "err.months": "Enter valid monthly values (at least one greater than zero).",
    "err.file_missing": "Choose the hourly load file first.",
    "err.elevation": "Enter a valid elevation in metres or leave it empty.",
    "err.server": "The analysis could not be completed (error code {status}). Please try again.",
    "nav.home": "Home",
    "nav.analysis": "Analysis",
    "nav.results": "Results",
    "nav.about": "About",
    "nav.help": "Help",
    "hero.title1": "How many panels, turbines and batteries does your home need?",
    "hero.title2": "Future",
    "chip.data.t": "Hourly data",
    "chip.data.s": "From NASA POWER for your site",
    "chip.pso.t": "Lowest cost",
    "chip.pso.s": "Particle Swarm Optimization (PSO)",
    "chip.scen.t": "Three systems",
    "chip.scen.s": "Solar, wind, hybrid",
    "chip.global.t": "Global Coverage",
    "chip.global.s": "Anywhere in the world",
    "step.location": "Select Location",
    "step.consumption": "Energy Consumption",
    "step.prefs": "System Preferences",
    "loc.search": "Search for a location...",
    "loc.search.none": "Place not found.",
    "pv.factor.label": "PV Performance Factor",
    "pv.factor.hint": "Non-thermal losses: dust, cables, inverter. Temperature losses are computed separately from NASA data.",
    "batt.eff.label": "Battery Efficiency (round-trip)",
    "batt.eff.hint": "Share of the energy that comes back from the battery after charging and discharging.",
    "tab.overview": "Overview",
    "tab.solar_battery": "PV + Battery",
    "tab.wind_battery": "Wind + Battery",
    "tab.hybrid": "Hybrid + Battery",
    "chart.monthly.title": "Monthly Production vs Load",
    "chart.monthly.solar": "Solar",
    "chart.monthly.wind": "Wind",
    "chart.monthly.load": "Load",
    "chart.mix.title": "Annual Energy Source",
    "chart.mix.solar": "Solar",
    "chart.mix.wind": "Wind",
    "chart.mix.grid": "Grid",
    "chart.mix.desc": "Share of the yearly demand served by each source (battery energy is attributed to solar and wind in proportion to what they produce).",
    "about.title": "About the project",
    "about.text": "RE-SIZER sizes a home renewable energy system. Hourly solar irradiance, wind speed and temperature are fetched from NASA POWER for your location, then Particle Swarm Optimization (PSO) looks for the lowest yearly cost that reaches the requested renewable share, for each scenario: PV + Battery, Wind + Battery and Hybrid.",
    "help.title": "Help",
    "help.q1": "How do I enter my consumption?",
    "help.a1": "Enter the kWh of each month from your bills. For the best accuracy upload an hourly load file.",
    "help.q2": "What does the target renewable fraction mean?",
    "help.a2": "The share of the home's consumption that must be covered by solar and wind (directly or through the battery). The rest is bought from the grid.",
    "help.q3": "Why is the number of wind turbines zero?",
    "help.a3": "Because wind energy costs more than solar at your location. Compare the two costs in the \"Cost of generated energy\" panel inside any scenario's details.",
    "help.q4": "How long does the analysis take?",
    "help.a4": "About 10 seconds to half a minute, because 8760 hours are simulated for each scenario.",
    "band.1.t": "Global Coverage",
    "band.1.s": "Anywhere in the world",
    "band.2.t": "Real NASA Data",
    "band.2.s": "Solar & Wind",
    "band.3.t": "Intelligent Optimization",
    "band.3.s": "Particle Swarm Optimization",
    "band.4.t": "Sustainable Future",
    "band.4.s": "Cleaner. Smarter. Greener.",
    "err.pv_factor": "Enter a performance factor between 0.30 and 1.00.",
    "err.batt_eff": "Enter a battery efficiency between 0.50 and 1.00.",
    "theme.dark": "Dark mode",
    "theme.light": "Light mode",
    "climate.title": "Site climate",
    "climate.solar": "Average solar irradiance",
    "climate.wind": "Average wind speed (10 m)",
    "climate.temp": "Average temperature at the site",
    "climate.elev": "Elevation above sea level",
    "scn.badge.limit": "Target not reached even at the maximum",
    "cost.capex": "Total cost (paid once)",
    "cost.explain.title": "How is the cost calculated?",
    "cost.col.item": "Item",
    "cost.col.unit": "Price of ONE unit",
    "cost.col.qty": "Quantity",
    "cost.col.total": "Total",
    "cost.item.pv": "Solar panel",
    "cost.item.wind": "Wind turbine",
    "cost.item.battery": "Battery",
    "cost.item.inverter": "Inverter",
    "cost.item.bos": "Installation, cables and protection (BOS)",
    "cost.row.total": "Total",
    "cost.explain.1": "The total cost is paid once = price of ONE unit × quantity, for each item.",
    "site.temp_corr": "Temperature correction for site elevation",
    "elev.auto": "Set automatically from the map",
    "cons.file_or_months": "Enter each month's consumption in kWh, or upload an hourly load file.",
    "cost.note": "The panel, turbine and battery prices are for the equipment only, without installation. Installation, cables and protection are in the BOS line (one amount for the system, edited in config.py); the inverter is a separate item.",
    "limit.pv": "panels ({n})",
    "limit.wind": "turbines ({n})",
    "limit.battery": "batteries ({n})",
    "notice.limit": "This scenario reached the maximum allowed quantity: {items}, and still does not reach the target ({rf}% of {target}%). It is therefore not recommended and is shown for comparison only. The limits can be raised in config.py (max_pv_panels, max_wind_turbines, max_batteries), but the cost grows very fast.",
  },
};

const STORAGE_KEY = "resizer.lang";
let current = "ar";

export function getLang() {
  return current;
}

export function t(key, vars = {}) {
  const text = DICT[current][key] ?? DICT.ar[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) =>
    vars[name] === undefined ? `{${name}}` : String(vars[name])
  );
}

export function applyTranslations() {
  document.documentElement.lang = current;
  document.documentElement.dir = current === "ar" ? "rtl" : "ltr";
  document.title = t("title");

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
}

export function setLang(lang) {
  current = lang === "en" ? "en" : "ar";

  try {
    localStorage.setItem(STORAGE_KEY, current);
  } catch {
    // storage may be blocked; the choice then lasts for this visit only
  }

  applyTranslations();
  document.dispatchEvent(new CustomEvent("languagechange"));
}

export function initI18n() {
  let saved = null;
  try {
    saved = localStorage.getItem(STORAGE_KEY);
  } catch {
    // ignore
  }

  const fromUrl = new URLSearchParams(location.search).get("lang");
  current = [fromUrl, saved].find((l) => l === "ar" || l === "en") || "ar";
  applyTranslations();
}

// exposed for the automatic tests
export const DICTIONARY = DICT;
