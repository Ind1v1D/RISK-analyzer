"""User-facing backend messages in every supported UI language.

The frontend sends its current language as `lang` (en / ru / kk). Anything the
user can read — validation errors, AI failures — is looked up here, so error
banners match the interface language. Unknown languages fall back to English.
"""

SUPPORTED_LANGS = ("en", "ru", "kk")
DEFAULT_LANG = "en"

# Used in the Gemini prompt ("write explanations in <name>").
LANGUAGE_NAMES = {"en": "English", "ru": "Russian", "kk": "Kazakh"}

MESSAGES: dict[str, dict[str, str]] = {
    # ---- main.py ---------------------------------------------------------
    "file_too_large": {
        "en": "That file is over 10 MB — please upload a smaller one.",
        "ru": "Файл больше 10 МБ — загрузите файл поменьше.",
        "kk": "Файл 10 МБ-тан үлкен — кішірек файл жүктеңіз.",
    },
    "no_input": {
        "en": "Provide a file or paste some contract text first.",
        "ru": "Сначала загрузите файл или вставьте текст договора.",
        "kk": "Алдымен файл жүктеңіз немесе шарт мәтінін қойыңыз.",
    },
    "too_long": {
        "en": "That document is too long for this MVP ({length:,} characters; "
        "limit {limit:,}). Try a shorter document.",
        "ru": "Документ слишком длинный для этой версии MVP ({length:,} символов; "
        "лимит — {limit:,}). Попробуйте документ покороче.",
        "kk": "Құжат осы MVP үшін тым ұзын ({length:,} таңба; шектеу — {limit:,}). "
        "Қысқарақ құжатты қолданып көріңіз.",
    },
    "sample_missing": {
        "en": "Sample contract not found.",
        "ru": "Пример договора не найден.",
        "kk": "Үлгі шарт табылмады.",
    },
    # ---- extraction.py ---------------------------------------------------
    "unsupported_type": {
        "en": "Unsupported file type '.{ext}' — please upload a PDF, DOCX, or TXT file.",
        "ru": "Неподдерживаемый тип файла «.{ext}» — загрузите PDF, DOCX или TXT.",
        "kk": "Қолдау көрсетілмейтін файл түрі «.{ext}» — PDF, DOCX немесе TXT жүктеңіз.",
    },
    "no_text": {
        "en": "We couldn't read any text from that file. If it's a scanned or "
        "image-based document, try pasting the text instead.",
        "ru": "Не удалось прочитать текст из файла. Если это скан или документ-изображение, "
        "попробуйте вставить текст вручную.",
        "kk": "Файлдан мәтінді оқи алмадық. Егер бұл сканерленген немесе сурет түріндегі "
        "құжат болса, мәтінді қолмен қойып көріңіз.",
    },
    "pdf_unreadable": {
        "en": "We couldn't read that PDF ({error}). Try re-saving it, or paste the text instead.",
        "ru": "Не удалось прочитать этот PDF ({error}). Попробуйте пересохранить его "
        "или вставьте текст вручную.",
        "kk": "Бұл PDF файлын оқи алмадық ({error}). Қайта сақтап көріңіз немесе "
        "мәтінді қолмен қойыңыз.",
    },
    "pdf_no_pages": {
        "en": "That PDF appears to have no readable pages.",
        "ru": "В этом PDF, похоже, нет читаемых страниц.",
        "kk": "Бұл PDF-те оқуға болатын беттер жоқ сияқты.",
    },
    "docx_unreadable": {
        "en": "We couldn't read that DOCX file ({error}). Try re-saving it, or paste the text instead.",
        "ru": "Не удалось прочитать этот DOCX-файл ({error}). Попробуйте пересохранить его "
        "или вставьте текст вручную.",
        "kk": "Бұл DOCX файлын оқи алмадық ({error}). Қайта сақтап көріңіз немесе "
        "мәтінді қолмен қойыңыз.",
    },
    "bad_encoding": {
        "en": "That text file uses an encoding we couldn't read.",
        "ru": "Этот текстовый файл использует кодировку, которую не удалось прочитать.",
        "kk": "Бұл мәтіндік файл біз оқи алмайтын кодтауды пайдаланады.",
    },
    # ---- analysis.py -----------------------------------------------------
    "missing_api_key": {
        "en": "The analysis service is not configured yet. Please try again later.",
        "ru": "Сервис анализа ещё не настроен. Повторите попытку позже.",
        "kk": "Талдау қызметі әлі бапталмаған. Кейінірек қайталап көріңіз.",
    },
    "ai_failed": {
        "en": "The AI service couldn't process this document right now. Please try again in a few minutes.",
        "ru": "Сервис ИИ сейчас не смог обработать документ. Повторите попытку через несколько минут.",
        "kk": "ЖИ қызметі қазір бұл құжатты өңдей алмады. Бірнеше минуттан кейін қайталап көріңіз.",
    },
    "ai_quota": {
        "en": "The AI service has reached its usage quota. Please try again later.",
        "ru": "Достигнут лимит запросов к сервису ИИ. Повторите попытку позже.",
        "kk": "ЖИ қызметінің сұрау лимиті таусылды. Кейінірек қайталап көріңіз.",
    },
    "rate_limited": {
        "en": "You're sending requests too quickly. Please wait a moment and try again.",
        "ru": "Слишком много запросов. Немного подождите и повторите попытку.",
        "kk": "Сұраулар тым жиі. Біраз күтіп, қайталап көріңіз.",
    },
    "server_busy": {
        "en": "The server is busy analyzing other documents. Please try again in a minute.",
        "ru": "Сервер занят анализом других документов. Повторите попытку через минуту.",
        "kk": "Сервер қазір басқа құжаттарды талдаумен бос емес. Бір минуттан кейін қайталап көріңіз.",
    },
    "text_too_short": {
        "en": "That text is too short to analyze — please paste the full contract.",
        "ru": "Текст слишком короткий для анализа — вставьте договор целиком.",
        "kk": "Мәтін талдау үшін тым қысқа — шарттың толық мәтінін қойыңыз.",
    },
    "pdf_encrypted": {
        "en": "That PDF is password-protected. Remove the password and upload it again, or paste the text instead.",
        "ru": "Этот PDF защищён паролем. Снимите защиту и загрузите файл снова или вставьте текст вручную.",
        "kk": "Бұл PDF құпиясөзбен қорғалған. Құпиясөзді алып тастап, қайта жүктеңіз немесе мәтінді қолмен қойыңыз.",
    },
    "ai_empty": {
        "en": "The AI returned an empty response. Please try again.",
        "ru": "ИИ вернул пустой ответ. Повторите попытку.",
        "kk": "ЖИ бос жауап қайтарды. Қайталап көріңіз.",
    },
    "ai_unreadable": {
        "en": "The AI returned output we couldn't read. Please try again.",
        "ru": "ИИ вернул ответ, который не удалось прочитать. Повторите попытку.",
        "kk": "ЖИ оқи алмайтын жауап қайтарды. Қайталап көріңіз.",
    },
}


def normalize_lang(lang: str | None) -> str:
    """Return a supported language code, falling back to English."""
    code = (lang or "").strip().lower()[:2]
    return code if code in SUPPORTED_LANGS else DEFAULT_LANG


def msg(key: str, lang: str = DEFAULT_LANG, **params) -> str:
    """Look up message `key` in `lang` (English fallback) and fill {params}."""
    variants = MESSAGES[key]
    template = variants.get(normalize_lang(lang)) or variants[DEFAULT_LANG]
    return template.format(**params)
