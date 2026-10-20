from __future__ import annotations
import re
import unicodedata
from typing import Optional, List, Tuple, Dict, Any, Set

def to_sans_bold_italic(text: str) -> str:
    """Converts ASCII text to Unicode Mathematical Sans-Serif Bold Italic characters.
    Example: 'Now Playing' -> '𝙉𝙤𝙬 𝙋𝙡𝙖𝙮𝙞𝙣𝙜'
    """
    res = []
    for ch in text:
        code = ord(ch)
        if 65 <= code <= 90:    # A-Z
            res.append(chr(code + 0x1D5FB))
        elif 97 <= code <= 122: # a-z
            res.append(chr(code + 0x1D5F5))
        elif 48 <= code <= 57:  # 0-9
            res.append(chr(code + 0x1D7BC))
        else:
            res.append(ch)
    return ''.join(res)


def clean_display_title(title: str) -> str:
    """Cleans noisy metadata, tags, and pipe credits from song titles for a sleek display."""
    if not title:
        return "Unknown Track"
    cleaned = title
    # Remove bracketed labels like [Official Music Video], (Audio Song), etc.
    cleaned = re.sub(r'[\(\[\{].*?(?:official|audio|video|lyrics|hd|4k|remastered|version|ost).*?[\)\]\}]', '', cleaned, flags=re.IGNORECASE)
    # Remove trailing label credits e.g. "Song Name | Movie | Actor | Singer"
    if '|' in cleaned:
        cleaned = cleaned.split('|')[0]
    return ' '.join(cleaned.split()).strip() or title


def normalize_title(title: str) -> str:
    """Normalize song title for strict deduplication."""
    t = unicodedata.normalize("NFKC", str(title or "")).casefold()
    t = re.sub(r'[\(\[].*?[\)\]]', ' ', t)
    t = re.sub(r'[^\w\s]', ' ', t, flags=re.UNICODE)
    return ' '.join(t.split())


DIALOGUE_KEYWORDS = [
    'dialogue', 'dialogues', 'dialog', 'with dialogue', 'with dialogues',
    'dialogue promo', 'dialogue teaser', 'movie scene', 'deleted scene',
    'scene cut', 'intro scene', 'climax scene', 'comedy scene', 'movie clip',
    'film scene', 'fight scene', 'scenes'
]

THEATRICAL_VIDEO_KEYWORDS = [
    'video song', 'full video song', 'full video', 'movie video',
    'film version', 'movie version', 'theatrical version'
]

PURE_AUDIO_KEYWORDS = [
    'official audio', 'audio song', 'original audio', 'album track',
    'studio version', 'original sound track', 'official track',
    'lyric video', 'lyrical video', 'lyrical'
]

NON_MUSIC_KEYWORDS = [
    'trailer', 'teaser', 'interview', 'podcast', 'news', 'live stream', 'reaction',
    'review', 'explained', 'episode', 'documentary', 'shorts', 'behind the scenes',
    'bts', 'making of', 'making video', 'commentary', 'debate', 'talk', 'radio', 'stream',
    'premiere', 'press conference', 'press meet', 'audio launch', 'success meet',
    'fan reaction', 'gameplay', 'walkthrough', 'promo', 'single promo', 'first single promo',
    'glimpse', 'motion poster', 'sneak peek', 'title announcement',
    'parody', 'unboxing', 'tutorial', 'vlog', 'speedrun', 'discussion',
    'jukebox', 'full album', 'all songs', 'compilation', 'mashup', 'top 10', 'top 20', 'top 50',
    'playlist', 'hits collection', 'non stop', 'non-stop', 'audio jukebox', 'video jukebox',
    'all hit songs', 'song collection', 'hits jukebox', 'mega jukebox', 'full audio jukebox',
    '10 hours', '10 hr', '1 hour', '1 hr', 'loop audio'
] + DIALOGUE_KEYWORDS

PREFERRED_CHANNEL_INDICATORS = [
    '- topic', 'vevo', 'official', 'records', 'music', 'audio', 'label',
    'soundtracks', 'studio', 'entertainment'
]

MAJOR_INTERNATIONAL_LABELS = [
    'warner music', 'atlantic records', 'universal music', 'def jam', 'columbia records',
    'interscope', 'republic records', 'rca records', 'epic records', 'ncs', 'spinnin',
    'monstercat', 'sony music', 'virgin music', 'capitol records', 'geffen', 'asylum records',
    'fueled by ramen', 'island records', 'polydor', 'parlophone', 'century media', 'think indie',
    'big hit', 'hybe', 'sm entertainment', 'jyp', 'yg entertainment'
]

UNWANTED_EDIT_KEYWORDS = [
    'slowed', 'reverb', 'sped up', 'speed up', 'speedup', 'pitched', 'pitch shifted',
    'bass boosted', 'bassboost', 'boosted', 'nightcore', '8d audio', '8d music',
    'ringtone', 'status video', 'whatsapp status', 'shorts', '#shorts', 'dance class',
    'dance cover', 'dance choreography', 'beginners class', 'bhangra performance',
    'interval bgm', 'interval theme', 'scene bgm', 'entry bgm', 'mass bgm', 'climax bgm',
    'bgm cut', 'bgm cuts', 'movie bgm', 'film bgm', 'theme bgm', 'bgm status',
    'audio cut', 'audio cuts', 'audio rip', 'sound rip', 'hd bgm', 'hd sounds', 'bgm only'
]

LANGUAGE_VERSION_PATTERNS: Dict[str, re.Pattern] = {
    "tamil": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:tamil(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?|tamizh|thamizh)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "telugu": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:telugu(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "hindi": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:hindi(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "malayalam": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:malayalam(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "kannada": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:kannada(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "punjabi": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:punjabi(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "english": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:english(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "korean": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:korean(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
    "japanese": re.compile(
        r'(?:[\(\[\{/\-_|]\s*(?:from\s+[\'"]?.*?[\'"]?\s+)?|\b)(?:japanese(?:\s+(?:version|audio|track|song|soundtrack|ost|lyric\s+video|video\s+song|lyrical|dubbed))?)(?:\b|[\)\]\}/-_|])',
        re.IGNORECASE
    ),
}

REGIONAL_CHANNEL_PATTERNS: Dict[str, re.Pattern] = {
    "tamil": re.compile(
        r'\b(saregama tamil|t-series tamil|think music tamil|sony music tamil|noise and grains|sun tv|sun pictures|kalaignar tv|divo tamil|trendmusic tamil)\b',
        re.IGNORECASE
    ),
    "telugu": re.compile(
        r'\b(aditya music|saregama telugu|t-series telugu|mango music|madhura audio|sony music telugu)\b',
        re.IGNORECASE
    ),
    "malayalam": re.compile(
        r'\b(muzik247|saina music|satyam audios|goodwill entertainments|saregama malayalam|think music malayalam|sony music malayalam)\b',
        re.IGNORECASE
    ),
    "kannada": re.compile(
        r'\b(anand audio|jhankar music|a2 music|saregama kannada|t-series kannada)\b',
        re.IGNORECASE
    ),
    "hindi": re.compile(
        r'\b(t-series(?!.*(?:tamil|telugu|kannada|malayalam))|zee music company|zee music|sony music india|yrf|tips official|tips music)\b',
        re.IGNORECASE
    ),
    "punjabi": re.compile(
        r'\b(speed records|geet mp3)\b',
        re.IGNORECASE
    ),
}

SOUTH_MULTI_REGIONAL_LABELS: re.Pattern = re.compile(
    r'\b(sony music south|think music|think indie|saregama south|lahari music south|lahari music|trendmusic|divo)\b',
    re.IGNORECASE
)

PAN_INDIAN_ARTISTS: Set[str] = {
    "pritam", "anirudh", "anirudh ravichander", "ar rahman", "a.r. rahman", "rahman",
    "sid sriram", "shreya ghoshal", "vijay prakash", "chinmayi", "karthik", "haricharan",
    "naresh iyer", "spb", "s. p. balasubrahmanyam", "chithra", "k. s. chithra",
    "ravi basrur", "m.m. keeravani", "keeravani", "devi sri prasad", "dsp",
    "thaman", "thaman s", "s. thaman", "santhosh narayanan", "sa na", "gv prakash", "gvprakash", "g. v. prakash kumar",
    "badshah", "armaan malik", "jonita gandhi", "neeti mohan", "benny dayal"
}

PRIMARY_ARTIST_BASE_LANGUAGE: Dict[str, str] = {
    "anirudh": "tamil",
    "anirudh ravichander": "tamil",
    "ar rahman": "tamil",
    "a.r. rahman": "tamil",
    "rahman": "tamil",
    "gv prakash": "tamil",
    "gvprakash": "tamil",
    "g.v. prakash": "tamil",
    "g. v. prakash kumar": "tamil",
    "gv prakash kumar": "tamil",
    "yuvan": "tamil",
    "yuvan shankar raja": "tamil",
    "u1": "tamil",
    "harris jayaraj": "tamil",
    "harris": "tamil",
    "santhosh narayanan": "tamil",
    "sa na": "tamil",
    "dhee": "tamil",
    "pradeep kumar": "tamil",
    "hiphop tamizha": "tamil",
    "hip hop tamizha": "tamil",
    "dhanush": "tamil",
    "ilayaraja": "tamil",
    "ilaiyaraaja": "tamil",
    "deva": "tamil",
    "vidyasagar": "tamil",
    "stephen zechariah": "tamil",
    "sean roldan": "tamil",
    "sam cs": "tamil",
    "sam c.s.": "tamil",
    "ghibran": "tamil",
    "leon james": "tamil",
    "karthik": "tamil",
    "haricharan": "tamil",
    "sid sriram": "tamil",
    "dsp": "telugu",
    "devi sri prasad": "telugu",
    "thaman": "telugu",
    "thaman s": "telugu",
    "s. thaman": "telugu",
    "m.m. keeravani": "telugu",
    "keeravani": "telugu",
    "ram miriyala": "telugu",
    "anurag kulkarni": "telugu",
    "pritam": "hindi",
    "arijit singh": "hindi",
    "arijit": "hindi",
    "badshah": "hindi",
    "armaan malik": "hindi",
    "sachin-jigar": "hindi",
    "amit trivedi": "hindi",
    "vishal-shekhar": "hindi",
    "vishal dadlani": "hindi",
    "shekhar ravjiani": "hindi",
    "shankar-ehsaan-loy": "hindi",
    "sonu nigam": "hindi",
    "shaan": "hindi",
    "kk": "hindi",
    "sunidhi chauhan": "hindi",
    "alka yagnik": "hindi",
    "kumar sanu": "hindi",
    "udit narayan": "hindi",
    "sushin shyam": "malayalam",
    "hesham abdul wahab": "malayalam",
    "jakes bejoy": "malayalam",
    "shaan rahman": "malayalam",
    "ravi basrur": "kannada",
    "charan raj": "kannada",
    "arjun janya": "kannada"
}

TAMIL_EXCLUSIVE_MARKERS = [
    # Movies / Soundtracks
    "singari", "singari sarakku", "arasan", "arasan theme", "dude", "dragon", "vidaamuyarchi", "coolie", "bachelor", "youth", "lover", "good bad ugly", "amaran", "raayan",
    "goat", "the greatest of all time", "vettaiyan", "kanguva", "jailer", "leo", "master", "varisu", "beast",
    "vikram", "kaithi", "thuppakki", "ghilli", "mankatha", "billa", "petta", "darbar", "viswasam", "vedalam",
    "aarambam", "vaaranam aayiram", "vinnaithaandi varuvaayaa", "ayan", "singam", "soorarai pottru", "jai bhim",
    "asuran", "karnan", "vada chennai", "vadachennai", "pudhupettai", "viduthalai", "mark antony", "maanaadu",
    "doctor", "don", "remo", "sivaji", "enthiran", "kabali", "kaala", "roja", "bombay", "minsaara kanavu",
    "pachaikili muthucharam", "minnale", "alaipayuthey", "7g rainbow colony", "pariyerum perumal", "irugapatru",
    "joe", "parking", "chithha", "por thozhil", "ayalaan", "captain miller", "captainmiller", "kottukkaali",
    "meiyazhagan", "vazhai", "lubber pandhu", "bloody beggar", "brother", "dada", "love today", "thiruchitrambalam",
    "ponniyin selvan", "ps1", "ps2", "sardar", "cobra", "valimai", "annatthe", "jagame thandhiram", "pattas",
    "bigil", "ngk", "sarkar", "seethakaathi", "96", "pyaar prema kaadhal", "irumbu thirai", "thaanaa serndha koottam",
    "mersal", "velaikkaran", "vikram vedha", "vip", "vip 2", "naanum rowdy dhaan", "thani oruvan", "anegan",
    "kaththi", "jigarthanda", "veeram", "maryan", "viswaroopam", "nanban", "mayakkam enna", "ko", "aadukalam",
    # Artists / Composers
    "sai abhyankkar", "paal dabba", "sublahshini", "dhibu ninan thomas", "kapil kapilan", "deepthi suresh",
    "g. v. prakash kumar", "gv prakash kumar", "g.v. prakash", "gvprakash", "gv prakash", "vishnu edavan",
    "pradeep ranganathan", "pradeep kumar", "dhee", "santhosh narayanan", "sa na", "sean roldan", "sam cs", "sam c.s.",
    "ghibran", "justin prabhakaran", "nivas k prasanna", "govind vasantha", "kaber vasuki", "arivu", "anthony daasan",
    "velmurugan", "anthakudi ilayaraja", "stephen zechariah", "leon james", "ofro", "tenma", "ilayaraja", "ilaiyaraaja",
    "deva", "vidyasagar", "harris jayaraj", "yuvan", "yuvan shankar raja", "u1", "hiphop tamizha", "hip hop tamizha",
    # Song Titles & Core Words
    "oorum blood", "oorum", "ooru", "oorin", "oorla", "oorukku", "mutta kalakki", "kalakki", "paththavaikkum",
    "pathikichu", "adiye", "vazhithunaiye", "vizhi veekura", "unakkul naane", "unakkul", "naane", "nenje", "nenjukkul",
    "nenjin", "nenjam", "uyire", "uyir", "uyirin", "uyirum", "anbe", "anbae", "kadhal", "kaadhal", "kadhale", "kadhalae",
    "kadhalin", "kanmani", "kannazhaga", "kannukulla", "kannil", "kanna", "kannae", "kannamma", "marakkuma", "varuvaya",
    "varuvayaa", "rathinamo", "adipoli", "aaruyire", "azhagiya", "azhagu", "thiruvizha", "vaathi", "rowdy", "chellame",
    "chinna", "periya", "kanave", "kanavu", "thanimaye", "katchi sera", "aasai", "aasa", "aasa kooda", "kooda",
    "muthal", "mudhal", "unakku", "enakku", "unaku", "enaku", "unnodu", "ennodu", "enodu", "adhigaaram", "siriki",
    "illaiye", "illai", "vazhi", "vazhkai", "amma", "appa", "thaaye", "hukum", "badass", "naa ready", "naaready",
    "lokiverse", "pathala pathala", "hunter", "fire song", "manasilaayo", "spark", "matta", "chinna chinna kangal",
    "hey minnale", "adangaatha asuran", "water packet", "usure", "po nee po", "why this kolaveri", "kolaveri",
    "rowdy baby", "arabic kuthu", "halamithi habibo", "jolly o gymkhana", "marana mass", "ullaallaa",
    "kaadhal sadugudu", "pachai nirame", "munbe vaa", "new york nagaram", "theethiriyaai", "thee thiriyaai", "thee",
    "thiri", "thiriyaai", "pesamale", "pesum", "pesatha", "pesu", "dhaan", "thaan", "mavandaa", "kadavule",
    "thaniyae", "thaniyaga", "vaada", "poda", "therinjiko", "purinjiko", "solladha", "pesadha", "koodave"
]

TELUGU_EXCLUSIVE_MARKERS = [
    # Movies / Soundtracks
    "geetha govindam", "geetha govindham", "ala vaikunthapurramuloo", "devara", "pushpa", "pushpa 2", "kalki",
    "salaar", "guntur kaaram", "gang leader", "magadheera", "indra", "varsham", "aaru (telugu)", "arya", "arya 2",
    "rangasthalam", "sarileru neekevvaru", "bharat ane nenu", "attarintiki daredi", "mirchi", "eega", "baahubali",
    "hi nanna", "kushi", "sita ramam", "dasara", "hanuman", "tillu square", "lucky baskhar", "saripodhaa sanivaaram",
    "game changer", "sankranthiki vasthunam", "thandel", "hushaaru", "ninnu kori", "uppena", "fidaa", "mca",
    "maharshi", "srimanthudu", "janatha garage", "temper", "naanaku prematho", "aravinda sametha", "race gurram",
    "julayi", "bheeshma", "brochevarevarura", "agent sai srinivasa athreya", "baby", "mad", "dj tillu", "duvvada jagannadham",
    # Artists / Composers
    "ram miriyala", "anurag kulkarni", "mangli", "saicharan", "lipsika", "ramya behara", "sahithi chaganti",
    "geetha madhuri", "hema chandra", "karunya", "dhanunjay", "srikrishna", "chandrabose", "ramajogayya sastry",
    "ananta sriram", "bhaskarabhatla", "sirivennela", "sitaramasastri", "veturi", "thaman", "thaman s", "s. thaman",
    "devi sri prasad", "dsp", "m.m. keeravani", "keeravani", "bheems ceciroleo", "chaitan bharadwaj", "mickey j meyer", "vivek sagar",
    # Song Titles & Core Words
    "inkem inkem", "inkem", "samajavaragamana", "undiporaadhey", "adiga adiga", "adiga", "hoyna hoyna", "hoyna",
    "ghallu ghallu", "nuvvostanante", "choododde nannu", "choododde", "srivalli", "oo antava", "saami saami", "ey bidda",
    "kumkumala", "butta bomma", "saranga dariya", "fear song", "chuttamalle", "daavudi", "ayudha pooja",
    "all hail the tiger", "pushpa pushpa", "sooseki", "kissik", "peelings", "bhairava anthem", "ta takkara",
    "theme of kalki", "garam garam", "ullaasam", "dhoom dhaam",
    "dum masala", "kurchi madathapetti", "kurchi", "sooreede", "srimathi garu", "jaragandi", "raa macha macha", "cheppave chirugali",
    "cheppave", "telusuna", "prema", "priyathama", "manasa", "kalala", "gundellona", "o rendu prema", "kaatuka kanule",
    "preminche", "nannu", "ninnu", "naaku", "neeku", "manasuna", "gundello", "kallalo", "ekkada", "ikkada", "vachadu",
    "poyadu", "ochesave", "kallalona", "pedavulu", "pilichave", "vennela", "chirunavve", "nee choopu", "nee sneham",
    "gunde", "choodu", "choosi", "raave", "pilla", "pori", "ammaayi", "abbayi", "chiranjeevi", "balakrishna", "nagarjuna",
    "venkatesh", "mahesh babu", "allu arjun", "prabhas", "jr ntr", "ram charan", "pawan kalyan", "nani", "vijay deverakonda"
]

HINDI_EXCLUSIVE_MARKERS = [
    # Movies / Soundtracks
    "jawan", "pathaan", "dunki", "animal", "fighter", "stree 2", "brahmastra", "kabir singh", "rockstar", "tamasha",
    "yeh jawaani hai deewani", "yjhd", "ae dil hai mushkil", "adhm", "raanjhanaa", "atrangi re", "chhichhore", "war",
    "dhoom", "bajirao mastani", "padmaavat", "gully boy", "kalank", "kesari", "raazi", "shershaah", "bhediya",
    "tu jhoothi main makkaar", "tjmm", "zara hatke zara bachke", "zhzb", "satyaprem ki katha", "rocky aur rani",
    "sam bahadur", "crew", "bad newz", "bhool bhulaiyaa", "singham again", "kedarnath", "bareilly ki barfi",
    # Artists / Composers
    "arijit singh", "arijit", "jubin nautiyal", "neha kakkar", "tony kakkar", "vishal mishra", "sachin-jigar",
    "amit trivedi", "vishal-shekhar", "sonu nigam", "shaan", "kk", "sunidhi chauhan", "alka yagnik", "kumar sanu",
    "udit narayan", "darshan raval", "jasleen royal", "tulsi kumar", "dhvani bhanushali", "stebin ben",
    # Song Titles & Core Words
    "kesariya", "chaleya", "apna bana le", "zinda banda", "faraatta", "tum hi ho", "tum se hi", "channa mereya",
    "raataan lambiyan", "gerua", "shayad", "pal pal dil ke paas", "arjan vailly", "satranga", "pehle bhi main",
    "jhoome jo", "besharam rang", "lutt putt gaya", "aaj ki raat", "sher khul gaye", "o maahi", "deva deva",
    "lut gaye", "tere vaaste", "phir aur kya chahiye", "khairiyat", "hawayein", "tera ban jaunga",
    "tujhe kitna chahne lage", "ghungroo", "dil diyan gallan", "swag se swagat", "bekhayali", "pachtaoge",
    "tera yaar hoon main", "kal ho naa ho", "kabira", "pehla nasha", "dilbar", "garmi"
]

MALAYALAM_EXCLUSIVE_MARKERS = [
    # Movies / Soundtracks
    "premam", "hridayam", "manjummel boys", "avesham", "aavesham", "kumbalangi nights", "bangalore days", "charlie",
    "lucifer", "arm", "kishkindha kaandam", "bramayugam", "varshangalkku shesham", "turbo", "guruvayoor ambalanadayil",
    "rdx", "romancham", "bheeshma parvam", "kurup", "minnal murali", "drishyam",
    # Artists / Composers
    "sushin shyam", "hesham abdul wahab", "shaan rahman", "jakes bejoy", "deepak dev", "vineeth sreenivasan",
    "ks harisankar", "job kurian", "sooraj santhosh", "vijay yesudas", "mg sreekumar",
    # Song Titles & Core Words
    "darshana", "manickya malaraya poovi", "aaradhike", "kannil pettole", "neeyilla", "pavizha mazha", "jeevamshamayi",
    "alare", "malare", "jaada", "illuminati", "kotha raja", "parudeesa", "kuthanthram", "thamburan", "aaranu"
]

KANNADA_EXCLUSIVE_MARKERS = [
    # Movies / Soundtracks
    "kgf", "kgf 2", "kantara", "charlie 777", "777 charlie", "vikrant rona", "yuva", "mufti", "tagaru", "james",
    "ui", "martin", "max", "bagheera", "sapta sagaradaache ello", "sse", "kaatera", "robert", "kurukshetra", "pogaru",
    # Artists / Composers
    "charan raj", "arjun janya", "sanjith hegde", "raghu dixit", "vasuki vaibhav", "v harikrishna", "gurukiran",
    # Song Titles & Core Words
    "singara siriye", "belakina kavithe", "sulthana", "toofan", "mehabooba", "salaam rocky bhai"
]

LANGUAGES: Dict[str, Dict[str, Any]] = {
    "tamil": {
        "flag": "🇮🇳", "name": "Tamil", "unicode": (0x0B80, 0x0BFF),
        "keywords": [
            "tamil", "kollywood", "tamizh", "thamizh", "tanglish",
            "oorum blood", "oorum", "ooru", "oorin", "oorla", "oorukku", "captain miller", "captainmiller",
            "hukum", "badass", "naa ready", "naaready", "lokiverse", "pathala pathala", "hunter", "fire song",
            "manasilaayo", "spark", "matta", "chinna chinna kangal", "the greatest of all time", "amarana",
            "hey minnale", "saiyyan", "adangaatha asuran", "water packet", "usure", "po nee po",
            "why this kolaveri", "kolaveri", "rowdy baby", "arabic kuthu", "halamithi habibo", "jolly o gymkhana",
            "marana mass", "ullaallaa", "kaadhal sadugudu", "pachai nirame", "munbe vaa", "new york nagaram",
            "anirudh", "ar rahman", "a.r. rahman", "rahman", "yuvan", "yuvan shankar raja", "u1",
            "harris jayaraj", "harris", "santhosh narayanan", "sa na", "hiphop tamizha", "hip hop tamizha",
            "gana", "kuthu", "dhanush", "thalapathy", "thala", "sid sriram", "pradeep kumar", "dhee",
            "gvprakash", "gv prakash", "siva kartikeyan", "sivakarthikeyan", "vijay", "ajith", "kamal haasan",
            "rajinikanth", "rajini", "think music", "think indie", "sony music south", "lahari music south",
            "saregama tamil", "saregama south", "sun tv", "sun pictures", "divo", "trendmusic", "noise and grains",
            "siri xander", "sai abhyankkar", "sai smriti", "saurav srisan", "jonita gandhi", "adesh krishna",
            "adarsh krishnan", "vidya lakshmi", "stephen zechariah", "sean roldan", "sam cs", "sam c.s.",
            "ghibran", "justin prabhakaran", "nivas k prasanna", "govind vasantha", "kaber vasuki", "arivu",
            "paal dabba", "sublahshini", "chinmayi", "karthik", "haricharan", "naresh iyer", "vijay prakash",
            "anthony daasan", "velmurugan", "anthakudi ilayaraja", "ilayaraja", "ilaiyaraaja", "spb",
            "chithra", "swarnalatha", "sujatha", "deva", "vidyasagar", "leon james", "ofro", "tenma",
            "theethiriyaai", "thee thiriyaai", "thee", "thiri", "thiriyaai",
            "pesamale", "pesum", "pesatha", "pesu", "kadhal", "kaadhal", "kadhale", "kadhalae", "kanmani",
            "kannazhaga", "kannukulla", "kannil", "kanna", "kannae", "kannamma", "marakkuma", "varuvaya",
            "varuvayaa", "rathinamo", "devaloka", "adipoli", "aaruyire", "nenje", "nenjukkul", "nenjin",
            "uyire", "uyir", "anbe", "anbae", "azhagiya", "azhagu", "thiruvizha", "vaathi", "rowdy",
            "chellame", "chinna", "periya", "kanave", "kanavu", "thanimaye", "katchi sera", "aasai", "aasa", "aasa kooda", "kooda",
            "muthal", "mudhal", "enakku", "unakku", "unaku", "enaku", "unnodu", "enodu", "adhigaaram", "siriki",
            "illaiye", "illai", "vazhi", "vazhkai", "amma", "appa", "thaaye", "kannan", "theri", "beast",
            "jailer", "leo", "master", "varisu", "vikram", "kaithi", "thuppakki", "ghilli", "mankatha", "billa",
            "petta", "darbar", "viswasam", "vedalam", "aarambam", "vaaranam aayiram", "vinnaithaandi",
            "ayan", "singam", "soorarai pottru", "jai bhim", "asuran", "karnan", "vadachennai", "pudhupettai",
            "amaran", "viduthalai", "raayan", "kanguva", "goat", "vettaiyan"
        ]
    },
    "malayalam": {
        "flag": "🇮🇳", "name": "Malayalam", "unicode": (0x0D00, 0x0D7F),
        "keywords": [
            "malayalam", "mollywood", "sushin shyam", "shaan rahman", "jakes bejoy", "deepak dev",
            "heshem abdul wahab", "hesham abdul wahab", "hesam", "vineeth sreenivasan", "premam",
            "hridhyam", "hridayam", "manjummel", "avesham", "faasil", "dulquer", "mohanlal", "mammootty",
            "saina music", "muzik247", "satyam audios", "goodwill entertainments", "darshana",
            "aaradhike", "kannil pettole", "neeyilla", "pavizha mazha", "jeevamshamayi", "alare", "malare"
        ]
    },
    "hindi": {
        "flag": "🇮🇳", "name": "Hindi", "unicode": (0x0900, 0x097F),
        "keywords": [
            "hindi", "bollywood", "arijit singh", "pritam", "shreya ghoshal", "badshah", "armaan malik",
            "atif aslam", "neha kakkar", "jubin nautiyal", "vishal mishra", "vishal-shekhar", "vishal dadlani",
            "sachin-jigar", "amit trivedi",
            "t-series", "zeemusic", "zee music", "sony music india", "yrf", "tips official",
            "pathaan", "jhoome jo", "jhoome jo pathaan", "besharam rang",
            "jawan", "chaleya", "zinda banda", "faraatta", "animal", "arjan vailly", "satranga", "pehle bhi main",
            "stree 2", "aaj ki raat", "fighter", "sher khul gaye", "dunki", "lutt putt gaya", "o maahi",
            "kesariya", "apna bana le", "tum hi ho", "tum se hi", "channa mereya",
            "raataan lambiyan", "kal ho naa ho", "gerua", "tera ban jaunga", "shayad", "pal pal dil ke paas",
            "pehla nasha", "kabira", "hawayein", "deva deva", "lut gaye"
        ]
    },
    "telugu": {
        "flag": "🇮🇳", "name": "Telugu", "unicode": (0x0C00, 0x0C7F),
        "keywords": [
            "telugu", "tollywood", "dsp", "devi sri prasad", "thaman", "thaman s", "anurag kulkarni",
            "sid sriram telugu", "ram miriyala", "aditya music", "lahari music", "allu arjun", "prabhas",
            "mahesh babu", "jr ntr", "ram charan", "t-series telugu", "mango music", "sony music south",
            "devara", "fear song", "chuttamalle", "daavudi", "ayudha pooja", "all hail the tiger",
            "pushpa", "pushpa 2", "pushpa pushpa", "sooseki", "kissik", "peelings", "srivalli", "oo antava", "saami saami", "ey bidda",
            "kalki", "bhairava anthem", "ta takkara", "guntur kaaram", "dum masala", "kurchi madathapetti", "kurchi",
            "salaar", "sooreede", "lucky baskhar", "srimathi garu", "game changer", "jaragandi", "hanuman", "tillu square",
            "kumkumala", "butta bomma", "samajavaragamana", "saranga dariya",
            "cheppave chirugali", "telusuna", "prema", "priyathama", "manasa", "kalala",
            "gundellona", "o rendu prema", "kaatuka kanule", "salaar telugu"
        ]
    },
    "kannada": {
        "flag": "🇮🇳", "name": "Kannada", "unicode": (0x0C80, 0x0CFF),
        "keywords": [
            "kannada", "sandalwood", "ravi basrur", "charan raj", "arjun janya", "vijay prakash",
            "sanjith hegde", "kgf", "kantara", "yash", "puneeth rajkumar", "darshan", "sudeep",
            "anand audio", "jhankar music", "a2 music", "singara siriye", "belakina kavithe"
        ]
    },
    "english": {
        "flag": "🌐", "name": "English", "unicode": None,
        "keywords": [
            "english", "pop", "ed sheeran", "taylor swift", "the weeknd", "drake", "billie eilish",
            "justin bieber", "dualipa", "brunomars", "eminem", "coldplay", "alan walker", "post malone",
            "rihanna", "adele", "maroon 5", "charlie puth", "shawn mendes", "olivia rodrigo",
            "sabrina carpenter", "travis scott", "kendrick lamar", "sza", "ariana grande", "katy perry"
        ]
    },
    "punjabi": {
        "flag": "🇮🇳", "name": "Punjabi", "unicode": (0x0A00, 0x0A7F),
        "keywords": [
            "punjabi", "ap dhillon", "diljit dosanjh", "karan aujla", "shubh", "sidhu moose wala",
            "gurinder gill", "amrit maan", "jassi gill", "b praak", "speed records", "geet mp3"
        ]
    },
    "korean": {
        "flag": "🇰🇷", "name": "Korean", "unicode": (0xAC00, 0xD7A3),
        "keywords": [
            "k-pop", "kpop", "bts", "blackpink", "newjeans", "stray kids", "twice", "jungkook",
            "exo", "seventeen", "aespa", "le sserafim", "itzy", "iu"
        ]
    },
    "japanese": {
        "flag": "🇯🇵", "name": "Japanese", "unicode": (0x3040, 0x30FF),
        "keywords": [
            "j-pop", "jpop", "anime", "yoasobi", "kenshi yonezu", "lisa", "ado", "aimer",
            "vaundy", "radwimps", "one ok rock", "official hige dandism"
        ]
    }
}

MOODS: Dict[str, Dict[str, Any]] = {
    "love": {
        "emoji": "❤️", "name": "Love", "synonyms": ["romantic", "melody", "kadhal", "pyar", "premam"],
        "keywords": ["love", "romantic", "romance", "kadhal", "kaadhal", "pyar", "ishq", "premam", "priyam", "mohabbat", "duet", "crush", "feel good love", "propose", "heart"]
    },
    "sad": {
        "emoji": "💔", "name": "Sad", "synonyms": ["emotional", "soga", "dard", "dukham"],
        "keywords": ["sad", "emotional", "crying", "soga", "sogam", "dard", "dukham", "tears", "pain", "alone", "feeling sad", "depressed", "broken", "grief", "sadness"]
    },
    "mass": {
        "emoji": "🔥", "name": "Mass", "synonyms": ["energetic", "kuthu", "banger", "bgm"],
        "keywords": ["mass", "energetic", "kuthu", "marana mass", "banger", "energy", "bgm mass", "elevation", "hype", "power", "theri", "beast", "vikram mass", "jailer mass", "leo mass", "fast beat", "power song"]
    },
    "party": {
        "emoji": "🎉", "name": "Party", "synonyms": ["dance", "club", "celebration", "dj"],
        "keywords": ["party", "club", "celebration", "dj", "remix party", "nightclub", "festival", "dance party", "edm", "house party", "pub"]
    },
    "melody": {
        "emoji": "😌", "name": "Melody", "synonyms": ["chill", "soulful", "soft", "peaceful"],
        "keywords": ["melody", "chill", "soulful", "soft", "acoustic", "peaceful", "relax", "lullaby", "unplugged", "soothing", "slow melody", "sweet melody", "breeze"]
    },
    "breakup": {
        "emoji": "🥀", "name": "Breakup", "synonyms": ["heartbreak", "pirivu", "bewafa", "pain"],
        "keywords": ["breakup", "break up", "heartbreak", "pirivu", "thozhvi", "bewafa", "betrayal", "cheated", "alone breakup", "sad love", "broken heart", "farewell"]
    },
    "dance": {
        "emoji": "🕺", "name": "Dance", "synonyms": ["fast beat", "groove", "folk dance", "kuthu"],
        "keywords": ["dance", "beat", "groove", "fast beat", "dappan kuthu", "folk dance", "bhangra", "disco", "club dance", "hook step"]
    }
}

def is_verified_music_channel(uploader: str, artist: str = "") -> bool:
    """Returns True if the channel belongs to a verified record label, artist channel, or official Topic release."""
    up_low = str(uploader or "").strip().lower()
    if not up_low:
        return False
    # Immediate disqualification: channels with unofficial keywords, edits, cuts, or fan BGM rips
    for kw in ['bgm', 'sounds', 'sound', 'ringtone', 'ringtones', 'edits', 'editz', 'editzz', 'reupload', 'fan made', 'fanmade', 'audio rip', 'movie cut', 'scene cut', 'status', 'cuts']:
        if re.search(r'\b' + re.escape(kw) + r'\b', up_low):
            return False
    if up_low.endswith('- topic') or ' - topic' in up_low:
        return True
    if 'vevo' in up_low:
        return True
    for pat in REGIONAL_CHANNEL_PATTERNS.values():
        if pat.search(up_low):
            return True
    for lbl in MAJOR_INTERNATIONAL_LABELS:
        if lbl in up_low:
            return True
    if artist:
        a_low = str(artist).strip().lower()
        if a_low and (a_low == up_low or a_low in up_low or up_low in a_low):
            return True
    return False

AUDIO_FILTERS = {
    "clear": "",
    "none": "",
    "8d": "apulsator=hz=0.125",
    "bassboost": "bass=g=7,dynaudnorm=f=200",
    "nightcore": "asetrate=48000*1.25,aresample=48000,atempo=1.0",
    "vaporwave": "asetrate=48000*0.85,aresample=48000,atempo=1.0",
    "soft": "lowpass=f=3000",
    "treblebass": "bass=g=5,treble=g=5",
}
