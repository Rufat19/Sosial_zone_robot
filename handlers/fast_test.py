import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()


# ===================== QUIZ SUALLARI =====================
QUESTIONS = [
    {"q": "İnvestisiyanı müxtəlif aktivlər arasında bölüşdürmək əsasən nəyə kömək edir?", "options": ["Tək aktivdən asılılığı və bəzi riskləri azaltmağa", "Gəliri zəmanət altına almağa", "Bütün komissiyaları ləğv etməyə", "Bazar enişini dayandırmağa"], "answer": 0},
    {"q": "1000 AZN illik 10% mürəkkəb gəlirlə 2 il artsa, təxminən nə qədər olar?", "options": ["1100 AZN", "1200 AZN", "1210 AZN", "1220 AZN"], "answer": 2},
    {"q": "İnflyasiya pulun alıcılıq qabiliyyətinə necə təsir edə bilər?", "options": ["Artıra bilər", "Azalda bilər", "Həmişə dəyişməz saxlayır", "Yalnız səhm qiymətlərini dəyişir"], "answer": 1},
    {"q": "İstiqraz alan investor adətən nə edir?", "options": ["Şirkətin sahibi olur", "Emitentə borc verir", "Bank hesabı açır", "Səhm dividendinə zəmanət alır"], "answer": 1},
    {"q": "ETF fondunun əsas xüsusiyyətlərindən biri hansıdır?", "options": ["Bir alətlə müxtəlif aktivlərə çıxış verə bilər", "Həmişə zərərsizdir", "Gəliri əvvəlcədən məlumdur", "Yalnız bir şirkətin səhmini saxlayır"], "answer": 0},
    {"q": "İnvestisiyanın likvid olması nə deməkdir?", "options": ["Qiymətinin daim artması", "Nisbətən tez nağd pula çevrilə bilməsi", "Vergidən azad olması", "Risk daşımaması"], "answer": 1},
    {"q": "Ümumən, daha yüksək gəlir gözləntisi ilə hansı amil də arta bilər?", "options": ["Risk", "Gəlir zəmanəti", "Likvidlik zəmanəti", "İnflyasiyanın yox olması"], "answer": 0},
    {"q": "Digər şərtlər eyni qalarsa, bazar faizləri artanda sabit kuponlu mövcud istiqrazların qiyməti adətən necə dəyişir?", "options": ["Enir", "Artır", "Dəyişmir", "Sıfırlanır"], "answer": 0},
    {"q": "İnvestisiya komissiyaları uzun müddətdə nəyə səbəb ola bilər?", "options": ["Xalis gəlirin azalmasına", "Riskin tam yox olmasına", "Gəlirin zəmanətinə", "İnflyasiyanın artmasına"], "answer": 0},
    {"q": "Şirkət dividend ödəməyə borcludurmu?", "options": ["Bəli, hər ay", "Bəli, mənfəət olmasa da", "Xeyr, dividendə zəmanət yoxdur", "Yalnız istiqraz sahiblərinə"], "answer": 2},
    {"q": "Limitli alış sifarişi nəyi müəyyən edir?", "options": ["Alıcının ödəməyə razı olduğu ən yüksək qiyməti", "Səhmin gələcək qiymətini", "Şirkətin illik mənfəətini", "Dividendin məbləğini"], "answer": 0},
    {"q": "Leverage-dən istifadə investisiyada nə edə bilər?", "options": ["Həm mümkün qazancı, həm də zərəri böyüdə bilər", "Zərəri mümkünsüz edə bilər", "Gəliri sabitləşdirə bilər", "Komissiyaları ləğv edə bilər"], "answer": 0},
    {"q": "Keçmişdə yüksək gəlir göstərən aktiv haqqında hansı fikir daha düzgündür?", "options": ["Gələcəkdə də mütləq artacaq", "Keçmiş nəticə gələcək gəlirə zəmanət vermir", "Artıq risk daşımır", "Qiyməti dəyişə bilməz"], "answer": 1},
    {"q": "Portfeli yenidən balanslaşdırmaq nə deməkdir?", "options": ["Aktiv paylarını seçilmiş hədəf bölgüyə qaytarmaq", "Bütün aktivləri satmaq", "Yalnız nağd pul saxlamaq", "Gəliri zəmanətə almaq"], "answer": 0},
    {"q": "İndeks fondu adətən nə etməyə çalışır?", "options": ["Müəyyən bazar indeksinin nəticəsini izləməyə", "Hər il sabit gəlir verməyə", "Bütün riskləri aradan qaldırmağa", "Yalnız qızıl almağa"], "answer": 0},
    {"q": "Şaxələndirmə hansı riski tam aradan qaldırmır?", "options": ["Ümumi bazar riskini", "Tək şirkət riskini", "Tək sektora bağlılığı", "Bir aktivə bağlılığı"], "answer": 0},
    {"q": "Adi səhm alan şəxs adətən nə əldə edir?", "options": ["Şirkətdə mülkiyyət payı", "Sabit faiz ödənişi zəmanəti", "Bank depoziti", "İstiqrazın geri ödəniş tarixi"], "answer": 0},
    {"q": "İnvestisiyanın nominal gəliri 10%, inflyasiya 6% olarsa, real gəlir təxminən neçə faizdir?", "options": ["4%", "6%", "10%", "16%"], "answer": 0},
    {"q": "Müntəzəm olaraq eyni məbləğdə investisiya etmək hansı yanaşmadır?", "options": ["Daimi məbləğlə periodik alış", "Bütün pulu bir gündə yatırmaq", "Leverage tətbiq etmək", "Yalnız qiymət qalxanda almaq"], "answer": 0},
    {"q": "Gözlənilməz xərclər üçün ehtiyat pulda adətən hansı xüsusiyyət önəmlidir?", "options": ["Asan əlçatanlıq", "Yüksək dəyişkənlik", "Uzun müddət satıla bilməmək", "Gəlir zəmanəti"], "answer": 0},
    {"q": "IPO nədir?", "options": ["İstiqrazın ödəmə tarixi", "Şirkətin səhmlərini ilk dəfə ictimaiyyətə təklif etməsi", "Fondun illik komissiyası", "Səhmin qiymətinin enməsi"], "answer": 1},
    {"q": "İkinci bazarda səhm alarkən investor adətən kimdən alır?", "options": ["Başqa investordan", "Mərkəzi bankdan", "Yalnız səhm buraxan şirkətdən", "Sığorta şirkətindən"], "answer": 0},
    {"q": "İstiqrazın ödəmə tarixi nəyi bildirir?", "options": ["Kuponun ilk dəfə elan olunduğu günü", "İstiqrazın birjada siyahıya alındığı günü", "Əsas məbləğin qaytarılmalı olduğu tarixi", "İnvestorun istiqrazı satmalı olduğu günü"], "answer": 2},
    {"q": "İstiqrazın kupon ödənişi nədir?", "options": ["Səhm sahibinə verilən səs hüququ", "İstiqraz üzrə dövri faiz ödənişi", "Fondun idarəetmə haqqı", "İstiqrazın bazar qiyməti"], "answer": 1},
    {"q": "Kredit riski nə deməkdir?", "options": ["Aktivin tez satıla bilməsi", "Valyuta məzənnəsinin dəyişməsi", "Səhm qiymətinin gün ərzində dəyişməsi", "Borcalanın ödənişlərini yerinə yetirməməsi ehtimalı"], "answer": 3},
    {"q": "Şirkətin bazar dəyəri, yəni bazar kapitallaşması adətən necə hesablanır?", "options": ["İllik gəlir bölünsün işçi sayına", "Aktivlər çıxılsın borclar", "Səhm qiyməti vurulsun dövriyyədəki səhm sayına", "Dividend vurulsun faiz dərəcəsinə"], "answer": 2},
    {"q": "Qiymət/gəlir (P/E) əmsalı adətən necə hesablanır?", "options": ["Səhm qiyməti bölünsün səhm başına gəlirə", "Dividend bölünsün işçi sayına", "Borc vurulsun aktivlərə", "Səhm sayı bölünsün bazar qiymətinə"], "answer": 0},
    {"q": "Səhm başına gəlir (EPS) əsasən nəyi göstərir?", "options": ["Şirkətin ümumi borcunu", "Şirkətin xalis mənfəətinin hər səhmə düşən hissəsini", "Səhmin gündəlik ən yüksək qiymətini", "Fondun illik komissiyasını"], "answer": 1},
    {"q": "Aktivi alış qiymətindən baha satdıqda, xərclər nəzərə alınmadan, nə yaranır?", "options": ["Kapital qazancı", "Kupon ödənişi", "Kredit riski", "Bazar kapitallaşması"], "answer": 0},
    {"q": "Aktivi alış qiymətindən ucuz satdıqda, xərclər nəzərə alınmadan, nə yaranır?", "options": ["Dividend", "Kupon gəliri", "Kapital itkisi", "Mürəkkəb faiz"], "answer": 2},
    {"q": "Stop əmri sürətli dəyişən bazarda niyə gözlənilən qiymətdən fərqli icra oluna bilər?", "options": ["Səhm sayı dəyişdiyi üçün", "Qiymət boşluğu və likvidlik azlığına görə", "Dividend elan edildiyi üçün", "İstiqrazın müddəti bitdiyi üçün"], "answer": 1},
    {"q": "Xarici valyutada olan aktivə investisiya edəndə hansı əlavə amil nəticəyə təsir edə bilər?", "options": ["Şirkətin loqosu", "İşçi sayı", "Birjanın yerləşdiyi bina", "Valyuta məzənnəsinin dəyişməsi"], "answer": 3},
    {"q": "Neft və buğda kimi əmtəələrin qiymətinə hansı amil təsir edə bilər?", "options": ["Tələb və təklif", "Səhm sahibinin səs hüququ", "Fondun xalis aktiv dəyəri", "İstiqrazın nominal dəyəri"], "answer": 0},
    {"q": "İnvestisiya üfüqü nədir?", "options": ["Aktivin bir gündəki qiymət aralığı", "Fondun idarəetmə haqqı", "Pulun investisiyada qalmasının planlaşdırıldığı müddət", "Şirkətin işçi sayı"], "answer": 2},
    {"q": "Dəyişkənlik (volatillik) nəyi təsvir edir?", "options": ["İnvestorların sayını", "Qiymətin nə dərəcədə dəyişdiyini", "İstiqrazın ödəmə tarixini", "Şirkətin dividend siyasətini"], "answer": 1},
    {"q": "İki aktivin korrelyasiyası onların nəyi barədə məlumat verir?", "options": ["Qiymətlərinin birlikdə necə dəyişmə meylini", "Hər ikisinin gəlir zəmanətini", "Vergi dərəcəsini", "Sahib olduqları işçi sayını"], "answer": 0},
    {"q": "Aktiv bölgüsü (asset allocation) nədir?", "options": ["Bütün aktivləri satmaq", "Yalnız bir şirkətə yatırım etmək", "Bazar qiymətini proqnozlaşdırmaq", "Vəsaiti müxtəlif aktiv növləri arasında paylamaq"], "answer": 3},
    {"q": "İnvestisiya fondunun prospektində adətən hansı məlumat olur?", "options": ["Gəlirə zəmanət", "Gələcək səhm qiymətləri", "Fondun strategiyası, xərcləri və riskləri", "İnvestorun şəxsi parolu"], "answer": 2},
    {"q": "Fondun xərc əmsalı (expense ratio) nəyi göstərir?", "options": ["Fondun zəmanətli illik gəlirini", "Fondun illik əməliyyat xərclərinin aktivlərə nisbətini", "Səhmlərin sayını", "İstiqrazın kupon tarixini"], "answer": 1},
    {"q": "Dividendin yenidən investisiyası nə deməkdir?", "options": ["Dividend gəliri ilə əlavə aktiv almaq", "Bütün səhmləri satmaq", "Kuponu nağdlaşdırmadan istiqrazı ləğv etmək", "Şirkətin borcunu silmək"], "answer": 0},
    {"q": "Səhm bölünməsi (stock split) zamanı, başqa dəyişiklik olmadıqda, adətən nə baş verir?", "options": ["Şirkətin ümumi dəyəri dərhal ikiqat artır", "İnvestorun payı yox olur", "Səhm sayı və hər səhmə düşən qiymət uyğun nisbətdə dəyişir", "Dividend mütləq artır"], "answer": 2},
    {"q": "Bazar indeksi investora nə üçün istifadə oluna bilər?", "options": ["Gəliri zəmanət etmək", "Portfel nəticəsini müqayisə etmək", "Vergini ləğv etmək", "Şirkətin borcunu qaytarmaq"], "answer": 1},
    {"q": "Fondun xalis aktiv dəyəri (NAV) əsasən nədir?", "options": ["Fondun reklam büdcəsi", "Bir səhmə ödənən dividend", "Fondun gündəlik dövriyyəsi", "Fondun xalis aktivlərinin bir paya düşən dəyəri"], "answer": 3},
    {"q": "Adi səhm sahibinə hansı hüquq verilə bilər?", "options": ["Şirkətin bəzi qərarlarında səsvermə hüququ", "Sabit gəlir zəmanəti", "İstiqrazın vaxtından əvvəl ödənişi", "Vergidən tam azadolma"], "answer": 0},
    {"q": "Bazar əmri (market order) nə etməyə çalışır?", "options": ["Alış üçün maksimum qiyməti əvvəlcədən təyin etməyə", "Yalnız müəyyən tarixdə icra olunmağa", "Əmri mövcud bazar qiymətlərində tez icra etməyə", "Gələcək qiyməti əvvəlcədən bildirməyə"], "answer": 2},
    {"q": "İstiqrazın ödəmə müddətinədək gəlirliliyi (YTM) nəyi təxmin edir?", "options": ["İstiqrazın yalnız kupon dərəcəsini", "İstiqraz cari qiymətdən alınıb ödəmə tarixinədək saxlanarsa mümkün illikləşdirilmiş gəliri", "Emitentin səhmlərinin sayını", "İstiqrazın bazarda satılacağı dəqiq qiyməti"], "answer": 1},
    {"q": "Xalis gəlir ümumi gəlirdən əsasən nə ilə fərqlənir?", "options": ["Xalis gəlirə yalnız inflyasiya daxildir", "Ümumi gəlir həmişə daha aşağı olur", "Xalis gəlir yalnız dividendləri sayır", "Xalis gəlirdə uyğun xərclər və komissiyalar nəzərə alınır"], "answer": 3},
    {"q": "Aktivin bazar dəyəri alış dəyərindən yuxarıdır, amma aktiv hələ satılmayıb. Bu qazanc necə adlanır?", "options": ["Kupon qazancı", "Reallaşmamış qazanc", "Kredit faizi", "Dividend borcu"], "answer": 1},
    {"q": "Riskə dözümlülük nəyi ifadə edir?", "options": ["İnvestorun qiymət dəyişkənliyi və mümkün itkilərə münasibətini", "Aktivin satış sürətini", "Şirkətin bazar kapitallaşmasını", "Fondun xərclərini"], "answer": 0},
    {"q": "Qısa satış (short selling) zamanı investor adətən nə etməyə çalışır?", "options": ["Aktivi alıb uzun müddət saxlamağa", "İstiqraz kuponunu artırmağa", "Borc aldığı aktivi satıb sonradan daha ucuz geri almağa", "Dividendə zəmanət almağa"], "answer": 2},
]

FUN_FACTS = [
    "📊 Şaxələndirmə bəzi riskləri azalda bilər, amma ümumi bazar riskini yox etmir.",
    "💸 Komissiyalar investisiyanın uzunmüddətli xalis nəticəsinə təsir edir.",
    "🛒 İnflyasiya pulun alıcılıq qabiliyyətini zamanla azalda bilər.",
    "📉 Faizlər qalxanda sabit kuponlu mövcud istiqrazların qiyməti adətən enə bilər.",
    "📈 Keçmiş gəlir gələcək qazancı zəmanət etmir.",
]

BONUS_VALUES = [0]

@router.message(Command("quiz"))
async def start_quiz(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    random_questions = random.sample(QUESTIONS, len(QUESTIONS))
    await state.update_data(questions=random_questions, current=0, prev_msg_id=None)
    await send_question(message, state)

async def send_question(message_or_callback, state: FSMContext):
    data = await state.get_data()
    current = data.get("current", 0)
    questions = data.get("questions", [])
    prev_msg_id = data.get("prev_msg_id")

    if prev_msg_id:
        try:
            await message_or_callback.bot.delete_message(message_or_callback.from_user.id, prev_msg_id)
        except:
            pass

    if current >= len(questions):
        await message_or_callback.answer("📊 Test bitdi!")
        await state.clear()
        return

    qdata = questions[current]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"ans_{current}_{i}")] for i, opt in enumerate(qdata["options"])]
    )

    msg = await (message_or_callback.answer if isinstance(message_or_callback, Message) else message_or_callback.message.answer)(
            f"❓ {qdata['q']}", reply_markup=kb
        )
    await state.update_data(prev_msg_id=msg.message_id)

@router.callback_query(F.data.startswith("ans_"))
async def answer_handler(callback: CallbackQuery, state: FSMContext):
    # Safely parse callback data: expected format ans_<qnum>_<chosen>
    try:
        parts = callback.data.split("_")
        if len(parts) != 3:
            raise ValueError("invalid callback format")
        _, qnum_s, chosen_s = parts
        qnum = int(qnum_s)
        chosen = int(chosen_s)
    except Exception:
        await callback.answer("Cavab qəbul edilə bilmədi (keçmiş/yanlış məlumat). Testi yenidən başladın.", show_alert=True)
        return

    data = await state.get_data()
    questions = data.get("questions") or []

    # If questions are missing (state cleared or expired), inform user
    if not questions:
        await callback.answer("Suallar tapılmadı və ya test bitib. /quiz ilə yenidən başlayın.", show_alert=True)
        await state.clear()
        return

    # Validate qnum bounds
    if qnum < 0 or qnum >= len(questions):
        await callback.answer("Bu sual artıq etibarsızdır. Testi yenidən başlatmağı yoxlayın.", show_alert=True)
        await state.clear()
        return

    qitem = questions[qnum]
    options = qitem.get("options", [])
    if chosen < 0 or chosen >= len(options):
        await callback.answer("Seçim etibarsızdır.", show_alert=True)
        return

    correct = qitem.get("answer")
    prev_msg_id = data.get("prev_msg_id")

    if chosen == correct:
        await callback.answer(f"✅ Doğru!\n{random.choice(FUN_FACTS)}", show_alert=True)
    else:
        correct_option = options[correct]
        await callback.answer(
            f"❌ Yanlış! Düzgün cavab: {correct_option}\n{random.choice(FUN_FACTS)}",
            show_alert=True,
        )

    # Try to delete previous question message (best-effort)
    if prev_msg_id:
        try:
            chat_id = callback.message.chat.id if callback.message else callback.from_user.id
            await callback.bot.delete_message(chat_id, prev_msg_id)
        except Exception:
            pass

    # Advance and send next question
    await state.update_data(current=qnum+1)
    await send_question(callback, state)

# ===================== FAST TEST START =====================
@router.callback_query(F.data == "fast_test_start")
async def fast_test_start_callback(callback: CallbackQuery, state: FSMContext):
    random_questions = random.sample(QUESTIONS, len(QUESTIONS))
    await state.update_data(questions=random_questions, current=0, prev_msg_id=None)
    await send_question(callback, state)