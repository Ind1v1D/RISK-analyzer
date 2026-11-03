// All user-facing UI strings, one flat dictionary per language.
//
// - Keys are identical across languages (checked by `npm run check:i18n`).
// - {placeholders} are filled in by t(key, { name: value }).
// - A value that is an object holds plural forms chosen with Intl.PluralRules
//   from the `count` variable (English/Kazakh: one + other, Russian: one + few +
//   many + other).
//
// To add a language: add an entry to LANGUAGES, copy the `en` block below and
// translate it. Nothing else in the app needs to change.

export const DEFAULT_LANG = 'en'

// Labels are written in each language's own name so people can always find theirs.
export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
  { code: 'kk', label: 'Қазақша' },
]

const en = {
  'meta.title': 'ClauseCheck — spot risky clauses before you sign',

  'nav.home': 'Back to home',
  'nav.howItWorks': 'How it works',
  'nav.example': 'Example',
  'nav.settings': 'Settings',
  'nav.themeToDark': 'Switch to dark theme',
  'nav.themeToLight': 'Switch to light theme',

  'hero.headline': 'Know what you’re signing.',
  'hero.sub':
    'Paste a contract or drop in a file — get a plain-language, clause-by-clause risk review in seconds.',
  'hero.seeExample': 'See Example Analysis',
  'hero.learnHow': 'Learn How It Works',

  'input.placeholder': 'Paste your contract or upload a file…',
  'input.upload': '📎 Upload File',
  'input.paste': '✎ Paste Text',
  'input.dropTitle': 'Drag & drop your contract here',
  'input.dropSub': 'or click to browse — PDF, DOCX, or TXT',
  'input.removeFile': 'Remove file',
  'input.submit': 'Analyze contract',
  'input.errUnsupported': 'Unsupported file — please use a PDF, DOCX, or TXT file.',
  'input.errTooLarge': 'That file is over 10 MB — please upload a smaller one.',

  'loading.title': 'Reviewing your contract…',
  'loading.step1': 'Reading your document…',
  'loading.step2': 'Identifying risky and unclear clauses…',
  'loading.step3': 'Writing plain-language explanations…',
  'loading.hint': 'This can take up to a minute when demand is high.',

  'results.title': 'Analysis results',
  'results.countHigh': '{count} high',
  'results.countMedium': '{count} medium',
  'results.countLow': '{count} low',
  'results.again': 'Analyze another contract',
  'results.docLabel': 'Your contract — flagged clauses highlighted',

  'panel.title': { one: '{count} clause flagged', other: '{count} clauses flagged' },
  'panel.notice': 'AI-generated starting points — not legal advice.',
  'panel.emptyTitle': 'No obvious red flags found.',
  'panel.emptyBody':
    'The AI didn’t flag anything that clearly needs attention — but it can miss things. Consider having a licensed attorney review the document before you sign.',
  'panel.unmatched': {
    one: '{count} flag couldn’t be located in the text but is listed above.',
    other: '{count} flags couldn’t be located in the text but are listed above.',
  },

  'risk.high': 'High risk',
  'risk.medium': 'Medium risk',
  'risk.low': 'Low risk',
  'mark.title': '{risk} — click to view explanation',

  'how.title': 'How it works',
  'how.step1.title': 'Upload or paste.',
  'how.step1.body':
    'PDF, DOCX, or plain text. Your document is processed in memory for this session only — it is never stored.',
  'how.step2.title': 'AI first pass.',
  'how.step2.body':
    'Gemini reviews the contract for clauses that are risky, unclear, or unusually unfavorable, and classifies each by risk level.',
  'how.step3.title': 'Review the flags.',
  'how.step3.body':
    'See highlighted text plus plain-language explanations, then talk to a licensed attorney about what matters for your situation.',
  'how.note':
    'ClauseCheck is a first-pass issue-spotting aid — not legal advice, and not a substitute for a lawyer.',
  'how.close': 'Got it',

  'settings.title': 'Settings',
  'settings.language': 'Interface language',
  'settings.languageHint':
    'The AI’s explanations of flagged clauses will also be written in the selected language. The contract text itself is never changed.',
  'settings.close': 'Done',

  'disclaimer.text':
    '⚠ This tool does not provide legal advice and does not replace a licensed attorney. Flags are AI-generated starting points for your own review.',

  'errors.generic': 'Something went wrong while analyzing the contract.',
  'errors.network':
    'Couldn’t reach the server. Make sure the backend is running and try again.',
}

const ru = {
  'meta.title': 'ClauseCheck — найдите рискованные пункты до подписания',

  'nav.home': 'На главную',
  'nav.howItWorks': 'Как это работает',
  'nav.example': 'Пример',
  'nav.settings': 'Настройки',
  'nav.themeToDark': 'Включить тёмную тему',
  'nav.themeToLight': 'Включить светлую тему',

  'hero.headline': 'Знайте, что подписываете.',
  'hero.sub':
    'Вставьте договор или загрузите файл — за считаные секунды получите разбор рисков по каждому пункту простым языком.',
  'hero.seeExample': 'Посмотреть пример анализа',
  'hero.learnHow': 'Узнать, как это работает',

  'input.placeholder': 'Вставьте текст договора или загрузите файл…',
  'input.upload': '📎 Загрузить файл',
  'input.paste': '✎ Вставить текст',
  'input.dropTitle': 'Перетащите договор сюда',
  'input.dropSub': 'или нажмите, чтобы выбрать файл — PDF, DOCX или TXT',
  'input.removeFile': 'Удалить файл',
  'input.submit': 'Проанализировать договор',
  'input.errUnsupported': 'Неподдерживаемый файл — используйте PDF, DOCX или TXT.',
  'input.errTooLarge': 'Файл больше 10 МБ — загрузите файл поменьше.',

  'loading.title': 'Анализируем ваш договор…',
  'loading.step1': 'Читаем документ…',
  'loading.step2': 'Ищем рискованные и неясные пункты…',
  'loading.step3': 'Готовим объяснения простым языком…',
  'loading.hint': 'При высокой нагрузке это может занять до минуты.',

  'results.title': 'Результаты анализа',
  'results.countHigh': 'Высокий: {count}',
  'results.countMedium': 'Средний: {count}',
  'results.countLow': 'Низкий: {count}',
  'results.again': 'Проанализировать другой договор',
  'results.docLabel': 'Ваш договор — отмеченные пункты выделены',

  'panel.title': {
    one: 'Отмечен {count} пункт',
    few: 'Отмечено {count} пункта',
    many: 'Отмечено {count} пунктов',
    other: 'Отмечено {count} пункта',
  },
  'panel.notice': 'Отправные точки, подготовленные ИИ, — не юридическая консультация.',
  'panel.emptyTitle': 'Явных рисков не найдено.',
  'panel.emptyBody':
    'ИИ не отметил ничего, что явно требует внимания, но он может что-то упустить. Перед подписанием стоит показать документ лицензированному юристу.',
  'panel.unmatched': {
    one: '{count} отметку не удалось найти в тексте, но она указана выше.',
    few: '{count} отметки не удалось найти в тексте, но они указаны выше.',
    many: '{count} отметок не удалось найти в тексте, но они указаны выше.',
    other: '{count} отметки не удалось найти в тексте, но они указаны выше.',
  },

  'risk.high': 'Высокий риск',
  'risk.medium': 'Средний риск',
  'risk.low': 'Низкий риск',
  'mark.title': '{risk} — нажмите, чтобы увидеть пояснение',

  'how.title': 'Как это работает',
  'how.step1.title': 'Загрузите или вставьте.',
  'how.step1.body':
    'PDF, DOCX или обычный текст. Документ обрабатывается только в памяти в рамках этой сессии и нигде не сохраняется.',
  'how.step2.title': 'Первичный анализ ИИ.',
  'how.step2.body':
    'Gemini проверяет договор на рискованные, неясные или необычно невыгодные пункты и определяет уровень риска для каждого.',
  'how.step3.title': 'Изучите отметки.',
  'how.step3.body':
    'Просмотрите выделенный текст и пояснения простым языком, а затем обсудите с лицензированным юристом то, что важно именно в вашей ситуации.',
  'how.note':
    'ClauseCheck помогает лишь первично выявить проблемные места — это не юридическая консультация и не замена юристу.',
  'how.close': 'Понятно',

  'settings.title': 'Настройки',
  'settings.language': 'Язык интерфейса',
  'settings.languageHint':
    'Пояснения ИИ к найденным пунктам тоже будут написаны на выбранном языке. Сам текст договора не меняется.',
  'settings.close': 'Готово',

  'disclaimer.text':
    '⚠ Этот инструмент не оказывает юридических консультаций и не заменяет лицензированного юриста. Отметки подготовлены ИИ и служат лишь отправной точкой для вашей собственной проверки.',

  'errors.generic': 'Что-то пошло не так при анализе договора.',
  'errors.network':
    'Не удалось связаться с сервером. Убедитесь, что бэкенд запущен, и повторите попытку.',
}

const kk = {
  'meta.title': 'ClauseCheck — қол қоймас бұрын тәуекелді тармақтарды анықтаңыз',

  'nav.home': 'Басты бетке',
  'nav.howItWorks': 'Қалай жұмыс істейді',
  'nav.example': 'Мысал',
  'nav.settings': 'Баптаулар',
  'nav.themeToDark': 'Қараңғы тақырыпқа ауысу',
  'nav.themeToLight': 'Жарық тақырыпқа ауысу',

  'hero.headline': 'Не нәрсеге қол қоятыныңызды біліңіз.',
  'hero.sub':
    'Шарт мәтінін қойыңыз немесе файлды жүктеңіз — бірнеше секундта әр тармақ бойынша жеңіл тілмен жазылған тәуекел талдауын алыңыз.',
  'hero.seeExample': 'Талдау мысалын көру',
  'hero.learnHow': 'Қалай жұмыс істейтінін білу',

  'input.placeholder': 'Шарт мәтінін қойыңыз немесе файл жүктеңіз…',
  'input.upload': '📎 Файл жүктеу',
  'input.paste': '✎ Мәтін қою',
  'input.dropTitle': 'Шартты осы жерге сүйреп әкелңіз',
  'input.dropSub': 'немесе файлды таңдау үшін басыңыз — PDF, DOCX немесе TXT',
  'input.removeFile': 'Файлды жою',
  'input.submit': 'Шартты талдау',
  'input.errUnsupported': 'Қолдау көрсетілмейтін файл — PDF, DOCX немесе TXT пайдаланыңыз.',
  'input.errTooLarge': 'Файл 10 МБ-тан үлкен — кішірек файл жүктеңіз.',

  'loading.title': 'Шартыңыз талданып жатыр…',
  'loading.step1': 'Құжат оқылуда…',
  'loading.step2': 'Тәуекелді және түсініксіз тармақтар анықталуда…',
  'loading.step3': 'Жеңіл тілмен түсіндірмелер жазылуда…',
  'loading.hint': 'Жүктеме жоғары болса, бұл бір минутқа дейін созылуы мүмкін.',

  'results.title': 'Талдау нәтижелері',
  'results.countHigh': 'Жоғары: {count}',
  'results.countMedium': 'Орташа: {count}',
  'results.countLow': 'Төмен: {count}',
  'results.again': 'Басқа шартты талдау',
  'results.docLabel': 'Сіздің шартыңыз — белгіленген тармақтар ерекшеленген',

  'panel.title': { one: '{count} тармақ белгіленді', other: '{count} тармақ белгіленді' },
  'panel.notice': 'ЖИ дайындаған бастапқы белгілер — заңгерлік кеңес емес.',
  'panel.emptyTitle': 'Айқын тәуекелдер табылмады.',
  'panel.emptyBody':
    'ЖИ назар аударуды қажет ететін ештеңе белгілеген жоқ, бірақ ол бірдеңені көзден таса қалдыруы мүмкін. Қол қоймас бұрын құжатты лицензиясы бар заңгерге көрсеткен жөн.',
  'panel.unmatched': {
    one: '{count} белгіні мәтіннен табу мүмкін болмады, бірақ ол жоғарыда көрсетілген.',
    other: '{count} белгіні мәтіннен табу мүмкін болмады, бірақ олар жоғарыда көрсетілген.',
  },

  'risk.high': 'Жоғары тәуекел',
  'risk.medium': 'Орташа тәуекел',
  'risk.low': 'Төмен тәуекел',
  'mark.title': '{risk} — түсініктемені көру үшін басыңыз',

  'how.title': 'Қалай жұмыс істейді',
  'how.step1.title': 'Жүктеңіз немесе қойыңыз.',
  'how.step1.body':
    'PDF, DOCX немесе қарапайым мәтін. Құжат осы сеанс барысында тек жадта өңделеді және еш жерде сақталмайды.',
  'how.step2.title': 'ЖИ-дің алғашқы талдауы.',
  'how.step2.body':
    'Gemini шартты тәуекелді, түсініксіз немесе әдеттен тыс тиімсіз тармақтарға тексеріп, әрқайсысына тәуекел деңгейін береді.',
  'how.step3.title': 'Белгілерді қарап шығыңыз.',
  'how.step3.body':
    'Ерекшеленген мәтін мен жеңіл тілмен жазылған түсіндірмелерді қарап шығыңыз, содан кейін өз жағдайыңызға қатысты маңызды мәселелерді лицензиясы бар заңгермен талқылаңыз.',
  'how.note':
    'ClauseCheck — мәселелерді алдын ала анықтауға арналған құрал. Бұл заңгерлік кеңес емес және заңгердің орнын баспайды.',
  'how.close': 'Түсінікті',

  'settings.title': 'Баптаулар',
  'settings.language': 'Интерфейс тілі',
  'settings.languageHint':
    'Табылған тармақтарға ЖИ түсіндірмелері де таңдалған тілде жазылады. Шарттың өз мәтіні өзгермейді.',
  'settings.close': 'Дайын',

  'disclaimer.text':
    '⚠ Бұл құрал заңгерлік кеңес бермейді және лицензиясы бар заңгердің орнын баспайды. Белгілерді жасанды интеллект дайындаған, олар тек өз тексеруіңізге арналған бастапқы нүкте ғана.',

  'errors.generic': 'Шартты талдау кезінде бірдеңе дұрыс болмады.',
  'errors.network':
    'Серверге қосыла алмадық. Бэкенд іске қосылғанын тексеріп, қайталап көріңіз.',
}

export const translations = { en, ru, kk }
