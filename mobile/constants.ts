export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Language = "hebrew" | "english" | "spanish";

export const LANGUAGES: {
  id: Language;
  label: string;
  flag: string;
  rtl: boolean;
  locale: string;
  ttsCode: string;
}[] = [
  { id: "hebrew",  label: "Hebrew",  flag: "🇮🇱", rtl: true,  locale: "he", ttsCode: "he-IL" },
  { id: "english", label: "English", flag: "🇺🇸", rtl: false, locale: "en", ttsCode: "en-US" },
  { id: "spanish", label: "Spanish", flag: "🇪🇸", rtl: false, locale: "es", ttsCode: "es-ES" },
];

export function getLangConfig(language: Language) {
  return LANGUAGES.find((l) => l.id === language)!;
}

export const DEFAULT_KNOWN_WORDS_HE = [
  "של", "את", "לא", "זה", "על", "עם", "כי", "הוא", "היא", "אני", "אבל", "גם", "כן",
  "יש", "רק", "כבר", "אם", "אז", "מה", "איך", "מי", "למה", "כל", "לי", "לו", "לה",
  "לנו", "לכם", "להם", "אנחנו", "אתה", "את", "הם", "הן", "אנו", "פה", "שם", "כאן",
  "היה", "הייתה", "יהיה", "תהיה", "עכשיו", "היום", "מחר", "אתמול", "תמיד", "אף",
  "עוד", "בוא", "רוצה", "יכול", "יכולה", "צריך", "צריכה", "יודע", "יודעת", "אוהב",
  "אוהבת", "אומר", "אומרת", "רואה", "שומע", "שומעת", "הולך", "הולכת", "בא", "באה",
  "נותן", "נותנת", "לוקח", "לוקחת", "שואל", "שואלת", "עונה", "חושב", "חושבת",
  "מדבר", "מדברת", "כותב", "כותברת", "קורא", "קוראת", "עושה", "יושב", "יושבת",
  "עומד", "עומדת", "אוכל", "אוכלת", "שותה", "ישן", "ישנה", "משחק", "משחקת",
  "עובד", "עובדת", "לומד", "לומדת", "מבין", "מבינה", "מרגיש", "מרגישה", "מחכה",
  "נראה", "נראית", "גדול", "גדולה", "קטן", "קטנה", "טוב", "טובה", "רע", "רעה",
  "יפה", "חדש", "חדשה", "ישן", "ישנה", "ראשון", "ראשונה", "אחרון", "אחרונה",
  "הרבה", "מעט", "קצת", "מאוד", "ממש", "בערך", "כמעט", "בדיוק", "ביחד", "לבד",
  "שוב", "פעם", "פעמים", "אחת", "שתיים", "שלוש", "ארבע", "חמש", "שש", "שבע",
  "שמונה", "תשע", "עשר", "אחד", "שניים", "שלושה", "ארבעה", "חמישה", "שישה",
  "שבעה", "שמונה", "תשעה", "עשרה", "אבא", "אמא", "ילד", "ילדה", "איש", "אישה",
  "חבר", "חברה", "בית", "עבודה", "מכונית", "רחוב", "עיר", "ארץ", "מדינה", "חיים",
  "זמן", "שנה", "חודש", "שבוע", "יום", "שעה", "דקה", "שנייה", "בוקר", "צהריים",
  "ערב", "לילה", "מים", "אוכל", "כסף", "ספר", "מקום", "דבר", "דברים", "מילה",
  "שאלה", "תשובה", "סיפור", "שם", "שמות", "כתובת", "מספר", "עולם", "אנשים",
  "ילדים", "ידיים", "עיניים", "ראש", "לב", "קול", "ים", "שמיים", "שמש", "אוויר",
  "כוח", "אפשרות", "בעיה", "חלום", "רגע", "חלק", "סוג", "צד", "דרך", "פנים",
  "גוף", "נשים", "גברים", "משפחה", "כך", "כזה", "כזאת", "אלה", "אלו", "זו",
  "הזה", "הזאת", "האלה", "אותו", "אותה", "אותם", "אותן", "אחד", "אחרת", "כלום",
  "משהו", "מישהו", "אף אחד", "כולם", "כולן", "כולנו", "שלי", "שלך", "שלו", "שלה",
  "שלנו", "שלכם", "שלהם", "מאין", "לאיפה", "איפה", "מתי", "כמה", "אילו", "עד",
  "מן", "אל", "ב", "ל", "כ", "מ", "ו", "ה", "עם", "בין", "אחרי", "לפני", "תחת",
  "מעל", "מתחת", "ליד", "מול", "סביב", "בגלל", "בשביל", "במקום", "בלי", "חוץ",
  "פלוס", "מינוס", "כי", "אם", "אבל", "למרות", "אחרת", "לכן", "לפיכך", "כלומר",
  "כאשר", "ברגע", "כשם", "ואולם", "בעוד", "ואז", "ולכן", "גם כן", "בנוסף", "בסדר",
  "בטח", "אולי", "בוודאי", "ודאי", "נכון", "אמת", "שקר", "חשוב", "קשה", "קל",
  "חזק", "חלש", "מהר", "לאט", "הרחק", "קרוב", "ארוך", "קצר", "גבוה", "נמוך",
  "עמוק", "רחב", "צר", "שלם", "ריק", "מלא", "פתוח", "סגור", "חם", "קר", "נקי",
  "מלוכלך", "שקט", "רועש", "בטוח", "מסוכן", "פשוט", "מסובך", "אפשרי", "בלתי",
  "נחמד", "מצוין", "נורא", "רגיל", "מיוחד", "להיות", "לעשות", "לדבר", "לומר",
  "לראות", "לשמוע", "לחשוב", "לדעת", "לרצות", "לאהוב", "ללכת", "לבוא", "לתת",
  "לקחת", "לשאול", "לענות", "לכתוב", "לקרוא", "לאכול", "לשתות", "לישון", "לשחק",
  "לעבוד", "ללמוד", "להבין", "להרגיש", "לחכות", "להיראות", "לגור", "לחיות",
  "למות", "לגדול", "להתחיל", "לסיים", "לפתוח", "לסגור", "לזכור", "לשכוח",
  "להביא", "לשלוח", "לקבל", "להחזיר", "לנסוע", "לטוס", "לרוץ", "לשחות", "לשיר",
  "לרקוד", "לבשל", "לקנות", "למכור", "לשלם", "לפגוש", "להכיר", "לבחור",
  "להחליט", "לנסות", "להצליח", "להיכשל", "להפסיק", "להמשיך", "לחזור", "לעזוב",
  "להישאר", "לעזור", "לכעוס", "לשמוח", "לבכות", "לצחוק", "לחייך", "להסכים",
  "לסרב", "לאמר", "להגיד", "לתכנן", "לחשב", "לשנות", "להוסיף", "להוריד",
  "לעלות", "לרדת", "להיכנס", "לצאת", "לפנות", "להסביר", "להראות", "לספר",
  "להגיע", "לחזות", "להכין", "לבנות", "לשבור", "לפתור", "לבקש", "להציע",
  "לקרות", "להתקשר", "לפרגן", "להזמין", "להתחתן", "ללדת", "לגדל", "ללמד",
  "לנהל", "לחגוג", "להתכוון", "לנסוע", "לפגוש", "לפנות", "להתחיל", "לתת",
  "לקרוא", "לכנות", "לדון", "להשוות", "כיתה", "בית ספר", "מורה", "תלמיד",
  "שיעור", "מבחן", "ציון", "אוניברסיטה", "סטודנט", "פרופסור", "רופא", "חולה",
  "בית חולים", "תרופה", "כאב", "בריאות", "מחלה", "משטרה", "חייל", "מלחמה",
  "שלום", "חוק", "ממשלה", "פוליטיקה", "כלכלה", "חברה", "תרבות", "דת", "שפה",
  "מוזיקה", "אמנות", "ספורט", "כדורגל", "קולנוע", "טלוויזיה", "מחשב", "טלפון",
  "אינטרנט", "תוכנה", "אפליקציה", "מסך", "מסרון", "רשת", "תמונה", "וידאו",
  "מוצר", "שירות", "חנות", "מסעדה", "מלון", "תחנה", "רכבת", "אוטובוס", "מטוס",
  "נמל", "כביש", "גשר", "פארק", "גן", "חוף", "הר", "נהר", "יער", "שדה", "פרח",
  "עץ", "חיה", "כלב", "חתול", "ציפור", "דג", "סוס", "פרה", "כבש", "ארנב",
  "אריה", "דוב", "ירוק", "כחול", "אדום", "צהוב", "לבן", "שחור", "כתום", "סגול",
  "חום", "ורוד", "אחת עשרה", "שנים עשר", "עשרים", "שלושים", "ארבעים", "חמישים",
  "מאה", "אלף", "ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת",
  "ראשון", "שני", "שלישי", "רביעי", "חמישי", "ינואר", "פברואר", "מרץ", "אפריל",
  "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר",
  "שלום", "להתראות", "בוקר טוב", "ערב טוב", "לילה טוב", "תודה", "בבקשה",
  "סליחה", "אין בעד מה", "ברוך הבא", "מזל טוב", "או",
];

export const DEFAULT_KNOWN_WORDS_EN = [
  "I", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
  "am", "is", "are", "was", "were", "be", "been", "being",
  "have", "has", "had", "do", "does", "did", "will", "would", "can", "could",
  "should", "may", "might", "must", "shall",
  "go", "come", "see", "know", "want", "like", "love", "need", "think", "feel",
  "say", "tell", "ask", "get", "give", "take", "make", "let", "put", "run",
  "eat", "drink", "sleep", "work", "walk", "talk", "read", "write", "play",
  "buy", "sell", "pay", "open", "close", "start", "stop", "help", "try",
  "learn", "understand", "remember", "forget", "live", "die", "grow", "look",
  "hear", "find", "leave", "stay", "keep", "bring", "send", "call", "meet",
  "house", "home", "car", "street", "city", "country", "world", "life",
  "time", "year", "month", "week", "day", "hour", "morning", "afternoon",
  "evening", "night", "water", "food", "money", "book", "word", "name",
  "man", "woman", "child", "boy", "girl", "person", "people", "friend",
  "family", "mother", "father", "brother", "sister", "son", "daughter",
  "good", "bad", "big", "small", "new", "old", "first", "last", "right",
  "long", "short", "high", "low", "hot", "cold", "happy", "sad", "tired",
  "yes", "no", "maybe", "please", "thank", "sorry", "hello", "hi", "bye",
  "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
  "red", "blue", "green", "yellow", "white", "black", "gray",
  "here", "there", "now", "today", "tomorrow", "yesterday", "always", "never",
  "very", "more", "most", "much", "many", "some", "few", "all", "no", "any",
  "the", "a", "an", "and", "or", "but", "if", "because", "when", "where",
  "who", "what", "why", "how", "which", "that", "this", "these", "those",
  "my", "your", "his", "her", "its", "our", "their",
  "in", "on", "at", "to", "from", "with", "for", "of", "by", "about",
  "up", "down", "out", "into", "over", "after", "before", "between",
];

export const DEFAULT_KNOWN_WORDS_ES = [
  "yo", "tú", "él", "ella", "nosotros", "ellos", "ellas", "me", "te", "le",
  "nos", "les", "usted", "ustedes",
  "ser", "estar", "tener", "hacer", "ir", "venir", "ver", "saber", "poder",
  "querer", "decir", "dar", "hablar", "comer", "beber", "dormir", "trabajar",
  "caminar", "correr", "leer", "escribir", "pensar", "sentir", "necesitar",
  "comprar", "vender", "pagar", "abrir", "cerrar", "empezar", "terminar",
  "ayudar", "esperar", "intentar", "aprender", "entender", "recordar",
  "olvidar", "vivir", "morir", "crecer", "escuchar", "encontrar", "dejar",
  "quedar", "traer", "llamar", "conocer", "buscar", "llegar", "salir",
  "casa", "coche", "calle", "ciudad", "país", "mundo", "vida", "tiempo",
  "año", "mes", "semana", "día", "hora", "mañana", "tarde", "noche",
  "agua", "comida", "dinero", "libro", "palabra", "nombre", "pregunta",
  "respuesta", "historia", "hombre", "mujer", "niño", "niña", "persona",
  "gente", "amigo", "amiga", "familia", "madre", "padre", "hermano",
  "hermana", "hijo", "hija",
  "bueno", "malo", "grande", "pequeño", "nuevo", "viejo", "primero",
  "último", "largo", "corto", "alto", "bajo", "caliente", "frío",
  "feliz", "triste", "cansado",
  "sí", "no", "tal vez", "por favor", "gracias", "perdón", "hola", "adiós",
  "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
  "rojo", "azul", "verde", "amarillo", "blanco", "negro",
  "aquí", "allí", "ahora", "hoy", "mañana", "ayer", "siempre", "nunca",
  "muy", "más", "menos", "mucho", "poco", "todo", "nada", "algo", "alguien",
  "bien", "mal", "también", "solo", "ya",
  "el", "la", "los", "las", "un", "una", "unos", "unas",
  "y", "o", "pero", "si", "porque", "cuando", "donde", "quién", "qué",
  "por qué", "cómo", "cuál", "este", "ese", "aquel", "esto", "eso",
  "mi", "tu", "su", "nuestro", "vuestro",
  "en", "de", "a", "con", "para", "por", "sin", "sobre", "entre",
  "después", "antes", "durante",
];

export const DEFAULT_KNOWN_WORDS: Record<Language, string[]> = {
  hebrew: DEFAULT_KNOWN_WORDS_HE,
  english: DEFAULT_KNOWN_WORDS_EN,
  spanish: DEFAULT_KNOWN_WORDS_ES,
};

export const STORAGE_KEY = (language: Language) => `knownWords_${language}`;
