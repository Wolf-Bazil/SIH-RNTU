/**
 * UI chrome strings. The advisory text itself is generated in the user's
 * language by the backend, so only labels live here.
 *
 * Languages without an entry fall back to English rather than showing a
 * half-translated interface.
 */
const STRINGS = {
  en: {
    subtitle: 'Oceanic Risk & Cyclone Advisory System',
    live: 'LIVE', degraded: 'NO FEED', connecting: 'CONNECTING',
    station: 'Station', conditions: 'Live Sea State', indices: 'Derived Indices',
    alerts: 'Alert Feed', ask: 'Ask ORCA', why: 'Why this score',
    observed: 'Observed', sources: 'Sources', noAlerts: 'Monitoring. No alerts raised.',
    askPlaceholder: 'e.g. is it safe to fish off Nagapattinam today?',
    askButton: 'Get advisory', asking: 'Analysing…',
    sst: 'Sea Surface Temp', waves: 'Wave Height', wind: 'Wind Speed',
    pressure: 'Pressure', gusts: 'Gusts', rain: 'Rainfall', period: 'Wave Period',
    hazard: 'Hazard Index', ciPfz: 'Critical Index', pfz: 'Fishing Zone',
    trend: 'Trend', outlook: '24h Outlook', peakWind: 'Peak wind', peakRain: 'Peak rain',
    refresh: 'Refresh', noData: 'No data',
  },
  hi: {
    subtitle: 'समुद्री जोखिम एवं चक्रवात सलाह प्रणाली',
    live: 'लाइव', degraded: 'फ़ीड नहीं', connecting: 'जुड़ रहा है',
    station: 'स्टेशन', conditions: 'समुद्र की स्थिति', indices: 'गणना सूचकांक',
    alerts: 'चेतावनियाँ', ask: 'ORCA से पूछें', why: 'यह स्कोर क्यों',
    observed: 'अवलोकन', sources: 'स्रोत', noAlerts: 'निगरानी जारी। कोई चेतावनी नहीं।',
    askPlaceholder: 'जैसे, क्या आज नागपट्टिनम में मछली पकड़ना सुरक्षित है?',
    askButton: 'सलाह लें', asking: 'विश्लेषण…',
    sst: 'सतही तापमान', waves: 'लहर ऊँचाई', wind: 'हवा गति',
    pressure: 'दबाव', gusts: 'झोंके', rain: 'वर्षा', period: 'लहर अवधि',
    hazard: 'जोखिम सूचकांक', ciPfz: 'क्रिटिकल सूचकांक', pfz: 'मत्स्य क्षेत्र',
    trend: 'रुझान', outlook: '24 घंटे पूर्वानुमान', peakWind: 'अधिकतम हवा', peakRain: 'अधिकतम वर्षा',
    refresh: 'रिफ़्रेश', noData: 'डेटा नहीं',
  },
  ta: {
    subtitle: 'கடல் அபாய மற்றும் புயல் ஆலோசனை அமைப்பு',
    live: 'நேரலை', degraded: 'தரவு இல்லை', connecting: 'இணைக்கிறது',
    station: 'நிலையம்', conditions: 'கடல் நிலை', indices: 'கணக்கிடப்பட்ட குறியீடுகள்',
    alerts: 'எச்சரிக்கைகள்', ask: 'ORCA-விடம் கேளுங்கள்', why: 'இந்த மதிப்பெண் ஏன்',
    observed: 'கண்காணிப்பு', sources: 'ஆதாரங்கள்', noAlerts: 'கண்காணிப்பில். எச்சரிக்கை இல்லை.',
    askPlaceholder: 'எ.கா. இன்று நாகப்பட்டினத்தில் மீன்பிடி பாதுகாப்பானதா?',
    askButton: 'ஆலோசனை பெறு', asking: 'பகுப்பாய்வு…',
    sst: 'கடல் மேற்பரப்பு வெப்பம்', waves: 'அலை உயரம்', wind: 'காற்று வேகம்',
    pressure: 'அழுத்தம்', gusts: 'சூறைக்காற்று', rain: 'மழை', period: 'அலை காலம்',
    hazard: 'அபாயக் குறியீடு', ciPfz: 'முக்கியக் குறியீடு', pfz: 'மீன்பிடி மண்டலம்',
    trend: 'போக்கு', outlook: '24 மணி நேர கணிப்பு', peakWind: 'உச்ச காற்று', peakRain: 'உச்ச மழை',
    refresh: 'புதுப்பி', noData: 'தரவு இல்லை',
  },
  bn: {
    subtitle: 'সামুদ্রিক ঝুঁকি ও ঘূর্ণিঝড় পরামর্শ ব্যবস্থা',
    live: 'লাইভ', degraded: 'ফিড নেই', connecting: 'সংযুক্ত হচ্ছে',
    station: 'স্টেশন', conditions: 'সমুদ্রের অবস্থা', indices: 'নির্ণীত সূচক',
    alerts: 'সতর্কতা', ask: 'ORCA-কে জিজ্ঞাসা করুন', why: 'এই স্কোর কেন',
    observed: 'পর্যবেক্ষণ', sources: 'উৎস', noAlerts: 'পর্যবেক্ষণ চলছে। কোনো সতর্কতা নেই।',
    askPlaceholder: 'যেমন, আজ কি সমুদ্রে মাছ ধরা নিরাপদ?',
    askButton: 'পরামর্শ নিন', asking: 'বিশ্লেষণ…',
    sst: 'সমুদ্র পৃষ্ঠের তাপ', waves: 'ঢেউয়ের উচ্চতা', wind: 'বাতাসের গতি',
    pressure: 'চাপ', gusts: 'দমকা হাওয়া', rain: 'বৃষ্টি', period: 'ঢেউয়ের সময়কাল',
    hazard: 'ঝুঁকি সূচক', ciPfz: 'ক্রিটিক্যাল সূচক', pfz: 'মৎস্য অঞ্চল',
    trend: 'প্রবণতা', outlook: '২৪ ঘণ্টার পূর্বাভাস', peakWind: 'সর্বোচ্চ বাতাস', peakRain: 'সর্বোচ্চ বৃষ্টি',
    refresh: 'রিফ্রেশ', noData: 'তথ্য নেই',
  },
}

export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'mr', label: 'मराठी' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
]

export function useT(lang) {
  const table = STRINGS[lang] || STRINGS.en
  return (key) => table[key] ?? STRINGS.en[key] ?? key
}
