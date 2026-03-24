import sys
import pygame
import os
import random
import math
import pyttsx3
import threading
import queue
import pythoncom
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

LANGUAGE_CODES = {
    "EN": "en",   # English
    "MK": "bg",   # Macedonian → use Bulgarian
    "TR": "tr",   # Turkish
    "AL": "sq",   # Albanian
}

class TTS:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def speak(self, text, lang="EN"):
        self.queue.put((text, lang.upper()))

    def _run(self):
        pythoncom.CoInitialize()
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        lang_voice_map = {}
        for lang_code, prefix in LANGUAGE_CODES.items():
            matched = None
            for v in voices:
                langs = [l.decode('utf-8') if isinstance(l, bytes) else l for l in getattr(v, "languages", [])]
                if any(prefix in l.lower() for l in langs):
                    matched = v
                    break
            lang_voice_map[lang_code] = matched
        default_voice = engine.getProperty('voice') 

        while True:
            text, lang = self.queue.get()
            voice = lang_voice_map.get(lang)
            if not voice and lang != "EN":
                voice = lang_voice_map.get("EN") 
            if voice:
                engine.setProperty('voice', voice.id)
            else:
                engine.setProperty('voice', default_voice)

            engine.say(text)
            engine.runAndWait()
            engine.stop()


def draw_language_selection(screen, settings):
    screen.fill((10, 20, 50))
    font = pygame.font.Font(resource_path(settings.font_path), 20)
    options = [("1. МАКЕДОНСКИ", 'MK'), ("2. ENGLISH", 'EN'), ("3. SHQIP", 'AL'), ("4. TÜRKÇE", 'TR')]
    title = font.render("CHOOSE LANGUAGE / ИЗБЕРИ ЈАЗИК", True, (207, 212, 242))
    screen.blit(title, (450 - title.get_width() // 2, 200))
    for i, (text, code) in enumerate(options):
        txt = font.render(text, True, (0, 255, 255))
        screen.blit(txt, (450 - txt.get_width() // 2, 300 + i * 60))

def draw_detailed_level_intro(screen, settings):
    lang = settings.language or 'MK'
    lvl = settings.current_level
    overlay = pygame.Surface((900, 700), pygame.SRCALPHA)
    overlay.fill((0, 0, 40, 230))
    screen.blit(overlay, (0, 0))
    panel_w, panel_h = 700, 500
    panel_x, panel_y = (900 - panel_w) // 2, (700 - panel_h) // 2
    pygame.draw.rect(screen, (207, 212, 242), (panel_x, panel_y, panel_w, panel_h), border_radius=20)
    pygame.draw.rect(screen, (0, 255, 255), (panel_x, panel_y, panel_w, panel_h), width=5, border_radius=20)
    font_title = pygame.font.Font(resource_path(settings.font_path), 20)
    font_text = pygame.font.Font(resource_path(settings.font_path), 14)
    title_str = settings.translations[lang]['level_titles'].get(lvl, "")
    title_surf = font_title.render(title_str, True, (0, 0, 100))
    screen.blit(title_surf, (450 - title_surf.get_width() // 2, panel_y + 40))
    lines = settings.translations[lang]['level_desc'].get(lvl, [])
    for i, line in enumerate(lines):
        txt_surf = font_text.render(line, True, (40, 40, 40))
        screen.blit(txt_surf, (450 - txt_surf.get_width() // 2, panel_y + 130 + i * 50))
    space_str = settings.translations[lang]['press_space']
    screen.blit(font_text.render(space_str, True, (150, 0, 0)),
                (450 - font_text.size(space_str)[0] // 2, panel_y + panel_h - 40))

class LayeredBackgroundBlue():
    def __init__(self, settings, folder="assets/layered", size=(900, 700)):
        self.settings = settings
        self.folder = folder
        self.size = size
        self.t = 0.0
        self.load_for_level(settings.current_level)

    def load_for_level(self, level):
        self.stars = pygame.Surface(self.size, pygame.SRCALPHA)

        if level in (1, 2, 7):
            self.back = pygame.transform.smoothscale(
                pygame.image.load(resource_path(os.path.join(self.folder, "blue-back.png"))).convert(),
                self.size
            )
            self.stars = pygame.transform.smoothscale(
                pygame.image.load(resource_path(os.path.join(self.folder, "blue-stars.png"))).convert_alpha(),
                self.size
            )

        elif level in (3, 4):
            self.back = pygame.transform.smoothscale(
                pygame.image.load(resource_path(os.path.join(self.folder, "greenbg.jpeg"))).convert(),
                self.size
            )

        elif level in (5, 6):
            self.back = pygame.transform.smoothscale(
                pygame.image.load(resource_path(os.path.join(self.folder, "redbg.jpeg"))).convert(),
                self.size
            )

        self.props = [
            {"img": pygame.image.load(resource_path(os.path.join(self.folder, "prop-planet-big.png"))).convert_alpha(),
             "pos": (650, 90), "spd": 0.35, "amp": 8},
            {"img": pygame.image.load(resource_path(os.path.join(self.folder, "asteroid-1.png"))).convert_alpha(),
             "pos": (820, 360), "spd": 0.9, "amp": 4}
        ]

    def update(self, dt_ms):
        self.t += dt_ms / 1000.0

    def draw(self, screen):
        screen.blit(self.back, (0, 0))
        screen.blit(self.stars, (0, int(math.sin(self.t * 0.5) * 2)))
        for p in self.props:
            y = p["pos"][1] + math.sin(self.t * p["spd"]) * p["amp"]
            screen.blit(p["img"], (p["pos"][0], int(y)))


class QuizSystem:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        self.active = False
        self.questions_pool = []
        self.used_questions = []
        self.current_q = None
        self.correct_answers_count = 0
        self.showing_feedback = False
        self.correct = False
        self.questions_map = {2: 1, 4: 2, 6: 3, 7: "final"} # Ниво 7 користи сите прашања
        self.all_questions = {
            'MK': {
                1: [  # 15 прашања за Ниво 2
                    {"q": "Што прави HTTPS?", "o": ["Шифрира податоци", "Забрзува нет"], "c": 0,
                     "e": "HTTPS е клуч за приватност."},
                    {"q": "Добра лозинка содржи?", "o": ["Име на милениче", "Букви и знаци"], "c": 1,
                     "e": "Комплексноста е заштита."},
                    {"q": "Што е 2FA?", "o": ["Двоен слој заштита", "Вид екран"], "c": 0,
                     "e": "Бара дополнителен код на моб."},
                    {"q": "Кој треба да ја знае твојата шифра?", "o": ["Само јас", "Најдобриот другар"], "c": 0,
                     "e": "Лозинката е лична тајна."},
                    {"q": "Јавен Wi-Fi е најчесто?", "o": ["Небезбеден", "Најбрз"], "c": 0,
                     "e": "Податоците не се шифрирани."},
                    {"q": "Што поправа софтверскиот Update?", "o": ["Дупки во безбедноста", "Боја на икони"], "c": 0,
                     "e": "Ги крпи пропустите за хакери."},
                    {"q": "Заклучуваш екран кога?", "o": ["Стануваш од компјутер", "Само кога спиеш"], "c": 0,
                     "e": "Никогаш не оставај отворен пристап."},
                    {"q": "Дали е добро да имаш иста шифра секаде?", "o": ["Не, користи различни", "Да, полесно е"],
                     "c": 0, "e": "Ако една падне, другите се безбедни."},
                    {"q": "Проверуваш име на сајт за?", "o": ["Печатни грешки", "Убав дизајн"], "c": 0,
                     "e": "Лажните сајтови имаат слични имиња."},
                    {"q": "Pop-up вели имаш вирус. Што правиш?", "o": ["Игнорирај/Затвори", "Кликни веднаш"], "c": 0,
                     "e": "Тоа е често измама за вирус."},
                    {"q": "Колку карактери е силна лозинка?", "o": ["Најмалку 12", "Максимум 6"], "c": 0,
                     "e": "Подолга лозинка е потешка за кршење."},
                    {"q": "Името на мачката е добра шифра?", "o": ["Не, лоша е", "Да, супер е"], "c": 0,
                     "e": "Личните имиња се лесни за погодување."},
                    {"q": "Дали HTTPS е задолжителен за плаќање?", "o": ["Да, секогаш", "Не, не мора"], "c": 0,
                     "e": "HTTPS гарантира безбедно плаќање."},
                    {"q": "Што е посигурно од ПИН код?", "o": ["Биометрика", "Роденден"], "c": 0,
                     "e": "Отпечатокот е уникатен за тебе."},
                    {"q": "Каде не внесуваш лозинка?", "o": ["На сомнителни линкови", "На официјални сајтови"], "c": 0,
                     "e": "Чувај ги податоците од измамници."}
                ],
                2: [  # 25 прашања за Ниво 4
                    {"q": "Што е Phishing?", "o": ["Лажна порака за податоци", "Спорт"], "c": 0,
                     "e": "Измама за крадење лозинки."},
                    {"q": "Што проверуваш кај испраќачот?", "o": ["Емаил адресата", "Сликата"], "c": 0,
                     "e": "Името може лесно да се лажира."},
                    {"q": "Банка бара шифра преку емаил?", "o": ["Никогаш", "Често"], "c": 0,
                     "e": "Банките не бараат тајни податоци вака."},
                    {"q": "Што крие VPN?", "o": ["IP адресата", "Името на РС"], "c": 0,
                     "e": "VPN те прави анонимен за хакери."},
                    {"q": "Итна порака 'делувај веднаш' е?", "o": ["Знак за измама", "Секогаш важна"], "c": 0,
                     "e": "Хакерите користат лажна итност."},
                    {"q": "Отвораш 'zip' од непознати?", "o": ["Не, никогаш", "Да, ако е интересно"], "c": 0,
                     "e": "Може да содржи скриен Malware."},
                    {"q": "Smishing е Phishing преку?", "o": ["СМС порака", "Телефонски повик"], "c": 0,
                     "e": "Текстуалните пораки се нова мета."},
                    {"q": "Линковите во Phishing мејл се?", "o": ["Лажни и опасни", "Секогаш точни"], "c": 0,
                     "e": "Те водат до заземени страници."},
                    {"q": "Што проверуваш пред најава?", "o": ["URL адресата", "Рекламите"], "c": 0,
                     "e": "Провери дали е вистинскиот домен."},
                    {"q": "Антивирусот помага при Phishing?", "o": ["Да, блокира некои", "Не, воопшто"], "c": 0,
                     "e": "Модерните програми препознаваат измами."},
                    {"q": "Плаќаш на сајт без HTTPS?", "o": ["Не, опасно е", "Да, нема врска"], "c": 0,
                     "e": "Податоците од картичката можат да се украдат."},
                    {"q": "Твој пријател праќа чуден вирус?", "o": ["Можеби е хакиран", "Верувај му"], "c": 0,
                     "e": "Хакерите праќаат вируси од туѓи профили."},
                    {"q": "Што е социјален инженеринг?", "o": ["Манипулација на луѓе", "Програмирање"], "c": 0,
                     "e": "Лажење за да се добијат шифри."},
                    {"q": "Наградна игра бара матичен број?", "o": ["Измама е, бегај", "Пополни сè"], "c": 0,
                     "e": "Личните податоци не се за игри."},
                    {"q": "Private Mode те крие од хакери?", "o": ["Не", "Да"], "c": 0,
                     "e": "Само не чува историја на твојот РС."},
                    {"q": "Што е Spear Phishing?", "o": ["Напад на одредена личност", "Напад на сите"], "c": 0,
                     "e": "Многу прецизен и опасен напад."},
                    {"q": "Одговараш на спам пораки?", "o": ["Не, ги бришам", "Да, за забава"], "c": 0,
                     "e": "Одговарањето потврдува дека мејлот е активен."},
                    {"q": "Каде чуваш приватни слики?", "o": ["На безбедно/шифрирано", "На јавен облак"], "c": 0,
                     "e": "Приватноста мора да биде приоритет."},
                    {"q": "Внимаваш што објавуваш на мрежи?", "o": ["Да, многу", "Не, сè објавувам"], "c": 0,
                     "e": "Објавите откриваат многу за тебе."},
                    {"q": "Проверуваш дозволи на апликации?", "o": ["Да, пред инсталација", "Никогаш"], "c": 0,
                     "e": "Апликациите често бараат премногу пристап."},
                    {"q": "Инкогнито мод користиш на?", "o": ["Јавни компјутери", "Дома"], "c": 0,
                     "e": "Спречува другите да ја видат твојата сесија."},
                    {"q": "Ги зачувуваш лозинките во Chrome на факултет?", "o": ["Не, никако", "Да"], "c": 0,
                     "e": "Следниот корисник може да ти влезе во профил."},
                    {"q": "Wi-Fi се поврзува сам. Тоа е?", "o": ["Ризично", "Одлично"], "c": 0,
                     "e": "Можеш да се поврзеш на хакерска мрежа."},
                    {"q": "Полниш телефон на јавно USB?", "o": ["Избегнувам", "Секогаш"], "c": 0,
                     "e": "Постои ризик од Juice Jacking (крадење податоци)."},
                    {"q": "Ја читаш политиката за приватност?", "o": ["Треба да ја знам", "Досадно е"], "c": 0,
                     "e": "Таму пишува кој ги користи твоите податоци."}
                ],
                3: [  # 30 прашања за Ниво 6
                    {"q": "Што е Ransomware?", "o": ["Вирус за уцена", "Подарок"], "c": 0,
                     "e": "Ги заклучува фајловите за пари."},
                    {"q": "Backup помага при Ransomware?", "o": ["Да, ги враќа фајловите", "Не"], "c": 0,
                     "e": "Резервната копија е единствен спас."},
                    {"q": "Malware е кратенка за?", "o": ["Штетен софтвер", "Добар софтвер"], "c": 0,
                     "e": "Секој програм што прави штета."},
                    {"q": "Cloud Backup е безбеден?", "o": ["Да, на сервери", "Не"], "c": 0,
                     "e": "Податоците се чуваат надвор од твојот уред."},
                    {"q": "Што прави Password Manager?", "o": ["Чува лозинки безбедно", "Ги краде"], "c": 0,
                     "e": "Најдобар начин за менаџирање шифри."},
                    {"q": "Тројански коњ е?", "o": ["Маскиран вирус", "Игра"], "c": 0,
                     "e": "Изгледа корисно, но е опасно."},
                    {"q": "Што снима Keylogger?", "o": ["Сè што пишуваш", "Слики"], "c": 0,
                     "e": "Ги краде лозинките додека ги внесуваш."},
                    {"q": "Скенираш USB пред употреба?", "o": ["Да, задолжително", "Не"], "c": 0,
                     "e": "USB е најчест преносител на Malware."},
                    {"q": "Rootkit му дава на хакерот?", "o": ["Целосна контрола", "Ништо"], "c": 0,
                     "e": "Најтежок вирус за откривање."},
                    {"q": "Ажуриран Windows е?", "o": ["Потежок за хакирање", "Побавен"], "c": 0,
                     "e": "Сигурносните закрпи се пресудни."},
                    {"q": "Што прави Spyware?", "o": ["Те следи тајно", "Те штити"], "c": 0,
                     "e": "Снима активност и праќа до хакери."},
                    {"q": "Adware служи за?", "o": ["Досадни реклами", "Игри"], "c": 0,
                     "e": "Може да те пренасочи на опасни сајтови."},
                    {"q": "Worm (црв) се шири?", "o": ["Автоматски низ мрежа", "Само со клик"], "c": 0,
                     "e": "Не му треба човечка помош за ширење."},
                    {"q": "Енкрипција ги прави фајловите?", "o": ["Нечитливи за други", "Помали"], "c": 0,
                     "e": "Само ти со клуч можеш да ги отвориш."},
                    {"q": "Најслаба карика во безбедноста?", "o": ["Човекот", "Компјутерот"], "c": 0,
                     "e": "Луѓето најлесно се лажат со манипулација."},
                    {"q": "Zero-day напад е?", "o": ["Непозната закана", "Стар вирус"], "c": 0,
                     "e": "Напад за кој уште нема лек."},
                    {"q": "Што е Firewall?", "o": ["Филтер за сообраќај", "Вид антивирус"], "c": 0,
                     "e": "Одлучува што смее да влезе во мрежата."},
                    {"q": "DDoS напад го прави сајтот?", "o": ["Недостапен", "Побрз"], "c": 0,
                     "e": "Го преоптоварува со лажни барања."},
                    {"q": "Botnet е мрежа од?", "o": ["Заразени уреди", "Паметни луѓе"], "c": 0,
                     "e": "Хакерот ги користи за масовни напади."},
                    {"q": "Што е Sandboxing?", "o": ["Безбедна тест зона", "Игра"], "c": 0,
                     "e": "Изолира вирус за да не се рашири."},
                    {"q": "Digital Signature гарантира?", "o": ["Оригиналност", "Боја"], "c": 0,
                     "e": "Потврдува дека документот не е менуван."},
                    {"q": "Индустриска шпионажа користи?", "o": ["Malware", "Телефони"], "c": 0,
                     "e": "Крадење тајни од големи компании."},
                    {"q": "Го исклучуваш антивирусот за инсталација?", "o": ["Никогаш", "Да"], "c": 0,
                     "e": "Многу пиратски програми вака заразуваат."},
                    {"q": "Силна лозинка на рутер е?", "o": ["Задолжителна", "Неважна"], "c": 0,
                     "e": "Спречува соседи и хакери да ти влезат во мрежа."},
                    {"q": "Кој Wi-Fi е најнов и најбезбеден?", "o": ["WPA3", "WEP"], "c": 0,
                     "e": "WPA3 нуди најдобра заштита денес."},
                    {"q": "IoT (Smart) уредите се?", "o": ["Честа мета на напади", "100% безбедни"], "c": 0,
                     "e": "Имаат слаба вградена заштита."},
                    {"q": "Секогаш правиш Log out?", "o": ["Да, секогаш", "Не"], "c": 0,
                     "e": "Ја затвораш активната сесија за другите."},
                    {"q": "Проверуваш активни сесии на профил?", "o": ["Да, за упад", "Не"], "c": 0,
                     "e": "Види дали некој друг е најавен на твојот FB/Mail."},
                    {"q": "Шифрирање на хард диск?", "o": ["Максимална заштита", "Непотребно"], "c": 0,
                     "e": "Дури и да ти го украдат РС, нема да читаат податоци."},
                    {"q": "Учењето за дигитални закани е?", "o": ["Постојан процес", "Еднократно"], "c": 0,
                     "e": "Светот се менува, мора да бидеш во тек."}
                ],
                "final": [
    {"q": "Што е 'Juice Jacking'?", "o": ["Кражба преку јавно USB", "Брзо полнење"], "c": 0, "e": "Јавните USB порти можат да пренесат вируси."},
    {"q": "Што е 'Digital Footprint'?", "o": ["Трага на интернет", "Големина на податок"], "c": 0, "e": "Сè што објавуваш останува засекогаш."},
    {"q": "Што е 'Zero-Day' напад?", "o": ["Напад на непозната дупка", "Стар вирус"], "c": 0, "e": "Тоа е напад пред да се направи поправка."},
    {"q": "Што значи 'Encryption'?", "o": ["Шифрирање податоци", "Бришење"], "c": 0, "e": "Ги прави податоците нечитливи за хакери."},
    {"q": "Што е '2FA'?", "o": ["Лозинка + дополнителен код", "Две лозинки"], "c": 0, "e": "Дополнителен слој на безбедност."},
    {"q": "Кој Wi-Fi е најбезбеден?", "o": ["WPA3", "WEP"], "c": 0, "e": "WPA3 е најновиот безбедносен стандард."},
    {"q": "Што е 'Social Engineering'?", "o": ["Манипулација на луѓе", "Програмирање"], "c": 0, "e": "Лажење за да се добијат тајни."},
    {"q": "Што е 'Spyware'?", "o": ["Вирус што те следи", "Антивирус"], "c": 0, "e": "Снима активност без твое знаење."},
    {"q": "Што е 'Keylogger'?", "o": ["Снима секоја буква", "Програм за музика"], "c": 0, "e": "Ги краде лозинките додека ги пишуваш."},
    {"q": "Што е 'Botnet'?", "o": ["Мрежа на заразени РС", "Вид на интернет"], "c": 0, "e": "Се користи за масовни напади."},
    {"q": "Што е 'Firewall'?", "o": ["Мрежен филтер", "Хард диск"], "c": 0, "e": "Го филтрира сообраќајот кон твојот РС."},
    {"q": "Што е 'DDoS'?", "o": ["Напад за преоптоварување", "Брз интернет"], "c": 0, "e": "Го урива сајтот со премногу сообраќај."},
    {"q": "Што е 'Trojan'?", "o": ["Маскиран вирус", "Игра"], "c": 0, "e": "Изгледа корисно, но е опасно."},
    {"q": "Што е 'Rootkit'?", "o": ["Вирус со целосна контрола", "Поправка"], "c": 0, "e": "Дава администраторски пристап на хакерот."},
    {"q": "Што е 'Sandboxing'?", "o": ["Изолирана тест зона", "Вид игра"], "c": 0, "e": "Го изолира вирусот за да не се рашири."},
    {"q": "Што е 'Ransomware'?", "o": ["Вирус за откуп", "Вид реклама"], "c": 0, "e": "Ги заклучува фајловите за пари."},
    {"q": "Што е 'Password Manager'?", "o": ["Сеф за лозинки", "Вирус"], "c": 0, "e": "Ги чува твоите лозинки шифрирани."},
    {"q": "Дали 'Incognito' те крие?", "o": ["Не од хакери", "Да, целосно"], "c": 0, "e": "Само не ја чува локалната историја."},
    {"q": "Што е 'Spear Phishing'?", "o": ["Насочен напад", "Напад на сите"], "c": 0, "e": "Напад врз точно одредена личност."},
    {"q": "Што е 'Pharming'?", "o": ["Пренасочување сајтови", "Земјоделство"], "c": 0, "e": "Те носи на лажен сајт без да знаеш."},
    {"q": "Што е 'SQL Injection'?", "o": ["Напад на база", "Вирус на диск"], "c": 0, "e": "Вметнување опасен код во базите."},
    {"q": "Што е 'Brute Force'?", "o": ["Погодување лозинки", "Вид процесор"], "c": 0, "e": "Обид со милиони комбинации."},
    {"q": "Што е 'Man-in-the-Middle'?", "o": ["Пресретнување пораки", "Игра"], "c": 0, "e": "Хакер што ги чита твоите пораки."},
    {"q": "Што е 'Malware'?", "o": ["Штетен софтвер", "Добар програм"], "c": 0, "e": "Секој програм што му штети на РС."},
    {"q": "Што е 'Patch'?", "o": ["Поправка на софтвер", "Слика"], "c": 0, "e": "Ги крпи безбедносните дупки."},
    {"q": "Што е 'Backup'?", "o": ["Резервна копија", "Бришење"], "c": 0, "e": "Те спасува ако изгубиш податоци."},
    {"q": "Што е 'Cookie'?", "o": ["Податок за сесија", "Вирус"], "c": 0, "e": "Ги памти твоите поставки на сајтот."},
    {"q": "Што е 'VPN'?", "o": ["Приватна мрежа", "Брз нет"], "c": 0, "e": "Создава безбеден тунел за податоците."},
    {"q": "Што е 'Whaling'?", "o": ["Напад на директори", "Лов"], "c": 0, "e": "Phishing на многу важни личности."},
    {"q": "Што е 'Honey Pot'?", "o": ["Замка за хакери", "Мед"], "c": 0, "e": "Лажен систем што ги мами хакерите."},
    {"q": "Што е 'Dark Web'?", "o": ["Скриен дел од нет", "Нет без боја"], "c": 0, "e": "Дел кој не се наоѓа на Google."},
    {"q": "Што е 'Biometrics'?", "o": ["Отпечаток/Лице", "Мерење"], "c": 0, "e": "Користење на телото за најава."},
    {"q": "Што е 'Spam'?", "o": ["Непосакувана пошта", "Вирус"], "c": 0, "e": "Масовни пораки со реклами или измами."},
    {"q": "Што е 'IoT'?", "o": ["Паметни уреди", "Процесор"], "c": 0, "e": "Предмети поврзани на интернет."},
    {"q": "Што е 'White Hat'?", "o": ["Етички хакер", "Опасен хакер"], "c": 0, "e": "Хакер што помага во заштитата."},
    {"q": "Што е 'Black Hat'?", "o": ["Злонамерен хакер", "Почетник"], "c": 0, "e": "Хакер што краде за своја корист."},
    {"q": "Што е 'Clickjacking'?", "o": ["Лажни копчиња", "Брзо кликање"], "c": 0, "e": "Те мами да кликнеш на скриен линк."},
    {"q": "Што е 'Malvertising'?", "o": ["Опасни реклами", "Вести"], "c": 0, "e": "Ширење вируси преку реклами."},
    {"q": "Што е 'Data Breach'?", "o": ["Протекување податоци", "Бришење"], "c": 0, "e": "Кога приватни податоци стануваат јавни."},
    {"q": "Лоша лозинка е?", "o": ["Роденден", "Комбинација знаци"], "c": 0, "e": "Лесните податоци брзо се погодуваат."},
    {"q": "Што прави антивирусот?", "o": ["Скенира и чисти", "Брише фајлови"], "c": 0, "e": "Бара и отстранува штетен код."},
    {"q": "Кој е најголем ризик?", "o": ["Човечка грешка", "Слаб компјутер"], "c": 0, "e": "Луѓето најлесно се манипулираат."},
    {"q": "Што е 'Shoulder Surfing'?", "o": ["Гледање преку рамо", "Вид сурфање"], "c": 0, "e": "Крадење шифра со гледање додека ја пишуваш."},
    {"q": "Што е 'Cold Wallet'?", "o": ["Офлајн крипто сеф", "Студен паричник"], "c": 0, "e": "Најбезбеден начин за чување крипто."},
    {"q": "Што е 'Script Kiddie'?", "o": ["Аматер хакер", "Дете што пишува"], "c": 0, "e": "Користи туѓи алатки без знаење."},
    {"q": "Што е 'Logic Bomb'?", "o": ["Код што чека настан", "Експлозив"], "c": 0, "e": "Вирус кој се активира во одредено време."},
    {"q": "Што е 'Bug'?", "o": ["Грешка во код", "Инсект"], "c": 0, "e": "Пропуст кој може да биде опасен."},
    {"q": "Што е 'Phreaking'?", "o": ["Хакирање телефони", "Страв"], "c": 0, "e": "Манипулација на телефонски мрежи."},
    {"q": "Што е 'Exploit'?", "o": ["Искористување дупка", "Поправка"], "c": 0, "e": "Алатка за влез преку пропуст."},
    {"q": "Дигитална безбедност е?", "o": ["Постојана грижа", "Еднократна задача"], "c": 0, "e": "Секогаш треба да бидеш внимателен."}
]
            },
            'EN': {
                1: [  # 15 Questions for Level 2
                    {"q": "What does HTTPS do?", "o": ["Encrypts data", "Speeds up net"], "c": 0,
                     "e": "HTTPS is key for privacy."},
                    {"q": "A strong password has?", "o": ["Pet's name", "Letters and symbols"], "c": 1,
                     "e": "Complexity is protection."},
                    {"q": "What is 2FA?", "o": ["Second layer of security", "Screen type"], "c": 0,
                     "e": "Requires a mobile code."},
                    {"q": "Who should know your password?", "o": ["Only me", "Best friend"], "c": 0,
                     "e": "Passwords are personal secrets."},
                    {"q": "Public Wi-Fi is usually?", "o": ["Insecure", "The fastest"], "c": 0,
                     "e": "Data is not encrypted."},
                    {"q": "What do software updates fix?", "o": ["Security holes", "Icon colors"], "c": 0,
                     "e": "They patch hacker exploits."},
                    {"q": "Lock your screen when?", "o": ["Leaving the PC", "Only when sleeping"], "c": 0,
                     "e": "Never leave open access."},
                    {"q": "Is one password for all sites good?", "o": ["No, use different ones", "Yes, it's easier"],
                     "c": 0, "e": "Keeps other accounts safe."},
                    {"q": "Check a site name for?", "o": ["Typos", "Nice design"], "c": 0,
                     "e": "Fake sites use similar names."},
                    {"q": "Pop-up says 'virus found'. Action?", "o": ["Ignore/Close", "Click now"], "c": 0,
                     "e": "It's often a virus scam."},
                    {"q": "Length of a strong password?", "o": ["At least 12", "Max 6"], "c": 0,
                     "e": "Longer is harder to crack."},
                    {"q": "Is a cat's name a good password?", "o": ["No, it's weak", "Yes, it's great"], "c": 0,
                     "e": "Personal names are easy to guess."},
                    {"q": "Is HTTPS mandatory for payments?", "o": ["Yes, always", "No, not needed"], "c": 0,
                     "e": "HTTPS ensures safe payments."},
                    {"q": "What is more secure than a PIN?", "o": ["Biometrics", "Birthday"], "c": 0,
                     "e": "Fingerprints are unique to you."},
                    {"q": "Where to NEVER enter a password?", "o": ["On suspicious links", "Official sites"], "c": 0,
                     "e": "Keep data away from scammers."}
                ],
                2: [  # 25 Questions for Level 4
                    {"q": "What is Phishing?", "o": ["Fake message for data", "A sport"], "c": 0,
                     "e": "Scam to steal passwords."},
                    {"q": "Check what in the sender?", "o": ["Email address", "Picture"], "c": 0,
                     "e": "Names can be easily faked."},
                    {"q": "Does a bank ask for PIN via email?", "o": ["Never", "Often"], "c": 0,
                     "e": "Banks don't request secrets this way."},
                    {"q": "What does a VPN hide?", "o": ["IP address", "PC Name"], "c": 0,
                     "e": "VPN makes you anonymous to hackers."},
                    {"q": "Urgent 'act now' message is?", "o": ["Scam sign", "Always important"], "c": 0,
                     "e": "Hackers use fake urgency."},
                    {"q": "Open 'zip' from strangers?", "o": ["No, never", "Yes, if interesting"], "c": 0,
                     "e": "Can contain hidden Malware."},
                    {"q": "Smishing is Phishing via?", "o": ["SMS message", "Phone call"], "c": 0,
                     "e": "Text messages are a new target."},
                    {"q": "Links in Phishing emails are?", "o": ["Fake and dangerous", "Always correct"], "c": 0,
                     "e": "They lead to malicious pages."},
                    {"q": "Check what before logging in?", "o": ["URL address", "Ads"], "c": 0,
                     "e": "Verify the real domain."},
                    {"q": "Does antivirus help with Phishing?", "o": ["Yes, blocks some", "No, not at all"], "c": 0,
                     "e": "Modern programs detect scams."},
                    {"q": "Pay on a site without HTTPS?", "o": ["No, it's dangerous", "Yes, it's fine"], "c": 0,
                     "e": "Card data can be stolen."},
                    {"q": "Friend sends a weird link?", "o": ["Maybe hacked", "Trust them"], "c": 0,
                     "e": "Hackers use stolen profiles."},
                    {"q": "What is social engineering?", "o": ["Manipulating people", "Programming"], "c": 0,
                     "e": "Lying to get passwords."},
                    {"q": "Contest asks for ID number?", "o": ["Scam, run", "Fill it all"], "c": 0,
                     "e": "Personal data isn't for games."},
                    {"q": "Private Mode hides from hackers?", "o": ["No", "Yes"], "c": 0,
                     "e": "Only hides history on your PC."},
                    {"q": "What is Spear Phishing?", "o": ["Targeted attack", "Attack on everyone"], "c": 0,
                     "e": "A very precise and dangerous attack."},
                    {"q": "Reply to spam messages?", "o": ["No, delete them", "Yes, for fun"], "c": 0,
                     "e": "Confirms your email is active."},
                    {"q": "Where to store private photos?", "o": ["Secure/Encrypted", "Public cloud"], "c": 0,
                     "e": "Privacy must be a priority."},
                    {"q": "Mind what you post on socials?", "o": ["Yes, very much", "No, I post all"], "c": 0,
                     "e": "Posts reveal a lot about you."},
                    {"q": "Check app permissions?", "o": ["Yes, before install", "Never"], "c": 0,
                     "e": "Apps often ask for too much access."},
                    {"q": "Incognito mode is for?", "o": ["Public computers", "Home"], "c": 0,
                     "e": "Prevents others from seeing sessions."},
                    {"q": "Save passwords in public Chrome?", "o": ["No, never", "Yes"], "c": 0,
                     "e": "Next user can enter your profile."},
                    {"q": "Wi-Fi connects automatically. Risk?", "o": ["Risky", "Great"], "c": 0,
                     "e": "Could be a hacker's network."},
                    {"q": "Charge phone at public USB?", "o": ["Avoid", "Always"], "c": 0,
                     "e": "Risk of Juice Jacking data theft."},
                    {"q": "Read the privacy policy?", "o": ["I should know it", "It's boring"], "c": 0,
                     "e": "It says who uses your data."}
                ],
                3: [  # 30 Questions for Level 6
                    {"q": "What is Ransomware?", "o": ["Extortion virus", "A gift"], "c": 0,
                     "e": "Locks files for money."},
                    {"q": "Backup helps with Ransomware?", "o": ["Yes, restores files", "No"], "c": 0,
                     "e": "Backup is the only salvation."},
                    {"q": "Malware stands for?", "o": ["Harmful software", "Good software"], "c": 0,
                     "e": "Any program that does harm."},
                    {"q": "Is Cloud Backup safe?", "o": ["Yes, on servers", "No"], "c": 0,
                     "e": "Data is stored off your device."},
                    {"q": "What does a Password Manager do?", "o": ["Stores keys safely", "Steals them"], "c": 0,
                     "e": "Best way to manage passwords."},
                    {"q": "A Trojan horse is?", "o": ["Disguised virus", "A game"], "c": 0,
                     "e": "Looks useful but is dangerous."},
                    {"q": "Keylogger records what?", "o": ["Everything you type", "Pictures"], "c": 0,
                     "e": "Steals keys as you enter them."},
                    {"q": "Scan USB before use?", "o": ["Yes, mandatory", "No"], "c": 0,
                     "e": "USB is a top Malware carrier."},
                    {"q": "A Rootkit gives a hacker?", "o": ["Full control", "Nothing"], "c": 0,
                     "e": "Hardest virus to detect."},
                    {"q": "Is updated Windows better?", "o": ["Harder to hack", "Slower"], "c": 0,
                     "e": "Security patches are vital."},
                    {"q": "What does Spyware do?", "o": ["Tracks you secretly", "Protects you"], "c": 0,
                     "e": "Sends activity to hackers."},
                    {"q": "Adware is used for?", "o": ["Annoying ads", "Games"], "c": 0,
                     "e": "Can redirect to dangerous sites."},
                    {"q": "Does a Worm spread?", "o": ["Automatically on net", "Only by click"], "c": 0,
                     "e": "No human help needed to spread."},
                    {"q": "Encryption makes files?", "o": ["Unreadable to others", "Smaller"], "c": 0,
                     "e": "Only you with the key can open."},
                    {"q": "Weakest link in security?", "o": ["Humans", "Computers"], "c": 0,
                     "e": "People are easiest to manipulate."},
                    {"q": "What is a Zero-day attack?", "o": ["Unknown threat", "Old virus"], "c": 0,
                     "e": "An attack with no current cure."},
                    {"q": "What is a Firewall?", "o": ["Traffic filter", "Type of AV"], "c": 0,
                     "e": "Decides what enters the network."},
                    {"q": "DDoS attack makes a site?", "o": ["Unavailable", "Faster"], "c": 0,
                     "e": "Overloads it with fake requests."},
                    {"q": "A Botnet is a network of?", "o": ["Infected devices", "Smart people"], "c": 0,
                     "e": "Hacker uses them for mass attacks."},
                    {"q": "What is Sandboxing?", "o": ["Safe test zone", "A game"], "c": 0,
                     "e": "Isolates a virus from spreading."},
                    {"q": "Digital Signature guarantees?", "o": ["Originality", "Color"], "c": 0,
                     "e": "Confirms document wasn't changed."},
                    {"q": "Industrial espionage uses?", "o": ["Malware", "Phones"], "c": 0,
                     "e": "Stealing secrets from companies."},
                    {"q": "Turn off AV for install?", "o": ["Never", "Yes"], "c": 0,
                     "e": "Pirated software infects this way."},
                    {"q": "Strong router password is?", "o": ["Mandatory", "Unimportant"], "c": 0,
                     "e": "Stops neighbors and hackers."},
                    {"q": "Newest and safest Wi-Fi?", "o": ["WPA3", "WEP"], "c": 0,
                     "e": "WPA3 offers best current protection."},
                    {"q": "IoT (Smart) devices are?", "o": ["Frequent targets", "100% safe"], "c": 0,
                     "e": "They have weak built-in security."},
                    {"q": "Always Log out?", "o": ["Yes, always", "No"], "c": 0, "e": "Closes the session for others."},
                    {"q": "Check active sessions?", "o": ["Yes, for intrusion", "No"], "c": 0,
                     "e": "See if others are in your FB/Mail."},
                    {"q": "Hard drive encryption?", "o": ["Max protection", "Unneeded"], "c": 0,
                     "e": "Stops data theft even if PC is stolen."},
                    {"q": "Learning digital security is?", "o": ["Ongoing process", "One-time"], "c": 0,
                     "e": "World changes, stay updated."}
                ],
                "final": [
                    {"q": "What is 'Juice Jacking'?", "o": ["Theft via public USB", "Fast charging"], "c": 0,
                     "e": "Public USB ports can transfer viruses."},
                    {"q": "What is 'Digital Footprint'?", "o": ["Online trail", "Data size"], "c": 0,
                     "e": "Everything you post stays forever."},
                    {"q": "What is a 'Zero-Day' attack?", "o": ["Unknown vulnerability", "Old virus"], "c": 0,
                     "e": "Attack before a patch exists."},
                    {"q": "What is 'Encryption'?", "o": ["Scrambling data", "Deleting"], "c": 0,
                     "e": "Makes data unreadable for hackers."},
                    {"q": "What is '2FA'?", "o": ["Password + code", "Two passwords"], "c": 0,
                     "e": "An extra layer of security."},
                    {"q": "Safest Wi-Fi?", "o": ["WPA3", "WEP"], "c": 0, "e": "WPA3 is the latest security standard."},
                    {"q": "What is 'Social Engineering'?", "o": ["Manipulating people", "Programming"], "c": 0,
                     "e": "Lying to get secret info."},
                    {"q": "What is 'Spyware'?", "o": ["Tracking virus", "Antivirus"], "c": 0,
                     "e": "Records activity without consent."},
                    {"q": "What is 'Keylogger'?", "o": ["Records keystrokes", "Music player"], "c": 0,
                     "e": "Steals passwords as you type."},
                    {"q": "What is a 'Botnet'?", "o": ["Infected PC network", "Internet type"], "c": 0,
                     "e": "Used for massive attacks."},
                    {"q": "What is a 'Firewall'?", "o": ["Traffic filter", "Hard drive"], "c": 0,
                     "e": "Filters traffic to your PC."},
                    {"q": "What is 'DDoS'?", "o": ["Overload attack", "Fast internet"], "c": 0,
                     "e": "Crashes sites with high traffic."},
                    {"q": "What is a 'Trojan'?", "o": ["Disguised virus", "Game"], "c": 0,
                     "e": "Looks useful but is harmful."},
                    {"q": "What is a 'Rootkit'?", "o": ["Full control virus", "Repair kit"], "c": 0,
                     "e": "Gives admin access to hackers."},
                    {"q": "What is 'Sandboxing'?", "o": ["Isolated test zone", "Game type"], "c": 0,
                     "e": "Prevents virus spreading."},
                    {"q": "What is 'Ransomware'?", "o": ["Extortion virus", "Ad type"], "c": 0,
                     "e": "Locks files for money."},
                    {"q": "What is a 'Password Manager'?", "o": ["Password vault", "Virus"], "c": 0,
                     "e": "Stores passwords encrypted."},
                    {"q": "Does 'Incognito' hide you?", "o": ["Not from hackers", "Yes, fully"], "c": 0,
                     "e": "Only hides history locally."},
                    {"q": "What is 'Spear Phishing'?", "o": ["Targeted attack", "Mass attack"], "c": 0,
                     "e": "Attack on a specific person."},
                    {"q": "What is 'Pharming'?", "o": ["Site redirection", "Farming"], "c": 0,
                     "e": "Takes you to a fake site secretly."},
                    {"q": "What is 'SQL Injection'?", "o": ["Database attack", "Disk virus"], "c": 0,
                     "e": "Injecting malicious code in DBs."},
                    {"q": "What is 'Brute Force'?", "o": ["Guessing passwords", "Processor type"], "c": 0,
                     "e": "Million-combination attempt."},
                    {"q": "What is 'Man-in-the-Middle'?", "o": ["Intercepting messages", "Game"], "c": 0,
                     "e": "Hacker reading your messages."},
                    {"q": "What is 'Malware'?", "o": ["Harmful software", "Good program"], "c": 0,
                     "e": "Any program harming a PC."},
                    {"q": "What is a 'Patch'?", "o": ["Software fix", "Picture"], "c": 0, "e": "Fixes security holes."},
                    {"q": "What is 'Backup'?", "o": ["Data copy", "Deleting"], "c": 0,
                     "e": "Saves you from data loss."},
                    {"q": "What is a 'Cookie'?", "o": ["Session data", "Virus"], "c": 0,
                     "e": "Remembers site settings."},
                    {"q": "What is a 'VPN'?", "o": ["Private network", "Fast net"], "c": 0,
                     "e": "Creates a secure data tunnel."},
                    {"q": "What is 'Whaling'?", "o": ["CEO attack", "Hunting"], "c": 0,
                     "e": "Phishing targeted at VIPs."},
                    {"q": "What is a 'Honey Pot'?", "o": ["Hacker trap", "Honey"], "c": 0,
                     "e": "Decoy system to trick hackers."},
                    {"q": "What is 'Dark Web'?", "o": ["Hidden web part", "Colorless web"], "c": 0,
                     "e": "Parts not indexed by Google."},
                    {"q": "What is 'Biometrics'?", "o": ["Fingerprint/Face", "Weighting"], "c": 0,
                     "e": "Using body for login."},
                    {"q": "What is 'Spam'?", "o": ["Unwanted mail", "Virus"], "c": 0,
                     "e": "Mass ads or scam messages."},
                    {"q": "What is 'IoT'?", "o": ["Smart devices", "Processor"], "c": 0,
                     "e": "Objects connected to internet."},
                    {"q": "What is 'White Hat'?", "o": ["Ethical hacker", "Harmful hacker"], "c": 0,
                     "e": "Hacker who helps security."},
                    {"q": "What is 'Black Hat'?", "o": ["Malicious hacker", "Beginner"], "c": 0,
                     "e": "Hacker stealing for gain."},
                    {"q": "What is 'Clickjacking'?", "o": ["Fake buttons", "Fast clicking"], "c": 0,
                     "e": "Tricks you to click hidden links."},
                    {"q": "What is 'Malvertising'?", "o": ["Harmful ads", "News"], "c": 0,
                     "e": "Virus spread via ads."},
                    {"q": "What is a 'Data Breach'?", "o": ["Data leak", "Deleting"], "c": 0,
                     "e": "Private data becoming public."},
                    {"q": "A bad password is?", "o": ["Birthday", "Symbol combination"], "c": 0,
                     "e": "Easy data is guessed quickly."},
                    {"q": "What does antivirus do?", "o": ["Scan and clean", "Delete files"], "c": 0,
                     "e": "Finds and removes harmful code."},
                    {"q": "Biggest risk?", "o": ["Human error", "Weak PC"], "c": 0,
                     "e": "Humans are easiest to manipulate."},
                    {"q": "What is 'Shoulder Surfing'?", "o": ["Watching over shoulder", "Surfing"], "c": 0,
                     "e": "Stealing password by watching."},
                    {"q": "What is a 'Cold Wallet'?", "o": ["Offline crypto vault", "Cold bag"], "c": 0,
                     "e": "Safest way to store crypto."},
                    {"q": "What is a 'Script Kiddie'?", "o": ["Amateur hacker", "Child"], "c": 0,
                     "e": "Uses tools without knowledge."},
                    {"q": "What is a 'Logic Bomb'?", "o": ["Code waiting for event", "Explosive"], "c": 0,
                     "e": "Virus triggered by time/event."},
                    {"q": "What is a 'Bug'?", "o": ["Coding error", "Insect"], "c": 0,
                     "e": "A flaw that can be dangerous."},
                    {"q": "What is 'Phreaking'?", "o": ["Phone hacking", "Fear"], "c": 0,
                     "e": "Manipulating phone networks."},
                    {"q": "What is an 'Exploit'?", "o": ["Using a flaw", "Fixing"], "c": 0,
                     "e": "Tool for entry via security hole."},
                    {"q": "Digital security is?", "o": ["Constant care", "One-time task"], "c": 0,
                     "e": "You must always be careful."}
                ]
            },
            'AL': {
                1: [  # 15 Pyetje për Nivelin 2
                    {"q": "Çfarë bën HTTPS?", "o": ["Kodon të dhënat", "Përshpejton netin"], "c": 0,
                     "e": "HTTPS është kyç për privatësinë."},
                    {"q": "Fjalëkalimi i fortë ka?", "o": ["Emrin e maces", "Shkronja dhe simbole"], "c": 1,
                     "e": "Kompleksiteti është mbrojtje."},
                    {"q": "Çfarë është 2FA?", "o": ["Shtresë e dytë sigurie", "Lloj ekrani"], "c": 0,
                     "e": "Kërkon një kod celular."},
                    {"q": "Kush duhet ta dijë kodin tuaj?", "o": ["Vetëm unë", "Shoku i ngushtë"], "c": 0,
                     "e": "Kodet janë sekrete personale."},
                    {"q": "Wi-Fi publik është zakonisht?", "o": ["I pasigurt", "Më i shpejti"], "c": 0,
                     "e": "Të dhënat nuk kodohen."},
                    {"q": "Çfarë rregullojnë update-et?", "o": ["Vrimat e sigurisë", "Ngjyrat"], "c": 0,
                     "e": "Mbyllin rrugët për hakerët."},
                    {"q": "Blloko ekranin kur?", "o": ["Largohesh nga PC", "Vetëm kur fle"], "c": 0,
                     "e": "Mos lejo qasje të hapur."},
                    {"q": "Një kod për të gjitha faqet?", "o": ["Jo, përdor të ndryshëm", "Po, është më lehtë"], "c": 0,
                     "e": "Mbron llogaritë e tjera."},
                    {"q": "Kontrollo emrin e faqes për?", "o": ["Gabime shtypi", "Dizajn të bukur"], "c": 0,
                     "e": "Faqet false kanë emra të ngjashëm."},
                    {"q": "Pop-up thotë 'ke virus'. Veprimi?", "o": ["Injoroje/Mbylle", "Kliko tani"], "c": 0,
                     "e": "Shpesh është mashtrim virusi."},
                    {"q": "Gjatësia e një kodi të fortë?", "o": ["Të paktën 12", "Maksimum 6"], "c": 0,
                     "e": "Më i gjatë = më i vështirë."},
                    {"q": "Emri i maces është kod i mirë?", "o": ["Jo, është i dobët", "Po, është super"], "c": 0,
                     "e": "Emrat personalë gjehen lehtë."},
                    {"q": "A është HTTPS detyrim për pagesa?", "o": ["Po, gjithmonë", "Jo, s'duhet"], "c": 0,
                     "e": "HTTPS garanton pagesa të sigurta."},
                    {"q": "Çfarë është më e sigurt se PIN-i?", "o": ["Biometrika", "Ditëlindja"], "c": 0,
                     "e": "Shenjat e gishtave janë unike."},
                    {"q": "Ku mos vendosni KURRË fjalëkalim?", "o": ["Në linqe të dyshimta", "Në faqe zyrtare"], "c": 0,
                     "e": "Ruani të dhënat nga mashtruesit."}
                ],
                2: [  # 25 Pyetje për Nivelin 4
                    {"q": "Çfarë është Phishing?", "o": ["Mesazh i rremë", "Sport"], "c": 0,
                     "e": "Mashtrim për vjedhje kodesh."},
                    {"q": "Çfarë kontrollon te dërguesi?", "o": ["Adresën email", "Foton"], "c": 0,
                     "e": "Emrat mund të falsifikohen lehtë."},
                    {"q": "Banka kërkon PIN me email?", "o": ["Asnjëherë", "Shpesh"], "c": 0,
                     "e": "Bankat nuk kërkojnë sekrete kështu."},
                    {"q": "Çfarë fsheh VPN-ja?", "o": ["Adresën IP", "Emrin e PC-së"], "c": 0,
                     "e": "VPN ju bën anonim për hakerët."},
                    {"q": "Mesazhi 'vepro tani' është?", "o": ["Shenjë mashtrimi", "Gjithmonë me rëndësi"], "c": 0,
                     "e": "Hakerët përdorin urgjencë false."},
                    {"q": "Hap 'zip' nga të panjohur?", "o": ["Jo, asnjëherë", "Po, po qe interesant"], "c": 0,
                     "e": "Mund të ketë Malware të fshehur."},
                    {"q": "Smishing është Phishing me?", "o": ["Mesazh SMS", "Telefonatë"], "c": 0,
                     "e": "SMS-të janë shënjestra e re."},
                    {"q": "Linqet në emailat Phishing janë?", "o": ["Të rremë dhe rrezik", "Gjithmonë saktë"], "c": 0,
                     "e": "Ju dërgojnë në faqe dashakeqe."},
                    {"q": "Çfarë kontrollon para login-it?", "o": ["Adresën URL", "Reklamat"], "c": 0,
                     "e": "Verifikoni domenin e vërtetë."},
                    {"q": "Antivirusi ndihmon me Phishing?", "o": ["Po, bllokon disa", "Jo, aspak"], "c": 0,
                     "e": "Programet moderne zbulojnë mashtrime."},
                    {"q": "Paguaj në faqe pa HTTPS?", "o": ["Jo, rrezik", "Po, s'ka gjë"], "c": 0,
                     "e": "Të dhënat e kartës vidhen."},
                    {"q": "Miku dërgon një link të çuditshëm?", "o": ["Ndoshta i hakuar", "Besoja"], "c": 0,
                     "e": "Hakerët përdorin profile të vjedhura."},
                    {"q": "Inxhinieria sociale?", "o": ["Manipulim njerëzish", "Programim"], "c": 0,
                     "e": "Gënjeshtër për të marrë kodet."},
                    {"q": "Loja kërkon numrin e ID-së?", "o": ["Mashtrim, ik", "Plotesoje"], "c": 0,
                     "e": "Të dhënat personale s'janë lojë."},
                    {"q": "Private Mode fsheh nga hakerët?", "o": ["Jo", "Po"], "c": 0,
                     "e": "Vetëm fsheh historinë në PC-në tuaj."},
                    {"q": "Çfarë është Spear Phishing?", "o": ["Sulm i synuar", "Sulm ndaj të gjithëve"], "c": 0,
                     "e": "Sulm shumë preciz dhe i rrezikshëm."},
                    {"q": "Përgjigju mesazheve spam?", "o": ["Jo, fshiji", "Po, për qejf"], "c": 0,
                     "e": "Konfirmon që emaili është aktiv."},
                    {"q": "Ku ruhen fotot private?", "o": ["Vendi sigurt/koduar", "Cloud publik"], "c": 0,
                     "e": "Privatësia duhet prioritizuar."},
                    {"q": "Kujdes çfarë poston në rrjete?", "o": ["Po, shumë", "Jo, postoj gjithçka"], "c": 0,
                     "e": "Postimet zbulojnë shumë për ju."},
                    {"q": "Kontrollo lejet e aplikacioneve?", "o": ["Po, para instalimit", "Asnjëherë"], "c": 0,
                     "e": "Apps kërkojnë shumë qasje."},
                    {"q": "Incognito mode përdoret në?", "o": ["PC publike", "Shtëpi"], "c": 0,
                     "e": "Nuk lejon të tjerët të shohin sesionet."},
                    {"q": "Ruaj kodet në Chrome publik?", "o": ["Jo, asnjëherë", "Po"], "c": 0,
                     "e": "Tjetri mund të hyjë në profilin tuaj."},
                    {"q": "Wi-Fi lidhet vetë. Rrezik?", "o": ["I rrezikshëm", "Super"], "c": 0,
                     "e": "Mund të jetë rrjet hakerësh."},
                    {"q": "Kariko telin në USB publike?", "o": ["Shmange", "Gjithmonë"], "c": 0,
                     "e": "Rrezik vjedhjeje Juice Jacking."},
                    {"q": "Lexo politikën e privatësisë?", "o": ["Duhet ta dij", "Është e mërzitshme"], "c": 0,
                     "e": "Tregon kush përdor të dhënat tuaja."}
                ],
                3: [  # 30 Pyetje për Nivelin 6
                    {"q": "Çfarë është Ransomware?", "o": ["Virus shantazhi", "Dhuratë"], "c": 0,
                     "e": "Bllokon skedarët për para."},
                    {"q": "Backup ndihmon Ransomware?", "o": ["Po, kthen skedarët", "Jo"], "c": 0,
                     "e": "Backup është shpëtimi i vetëm."},
                    {"q": "Malware do të thotë?", "o": ["Softuer i dëmshëm", "Softuer i mirë"], "c": 0,
                     "e": "Çdo program që bën dëm."},
                    {"q": "Cloud Backup i sigurt?", "o": ["Po, në serverë", "Jo"], "c": 0,
                     "e": "Të dhënat ruhen jashtë pajisjes."},
                    {"q": "Çfarë bën Password Manager?", "o": ["Ruan kodet sigurt", "I vjedh"], "c": 0,
                     "e": "Mënyra më e mirë për kodet."},
                    {"q": "Kali i Trojës është?", "o": ["Virus i maskuar", "Lojë"], "c": 0,
                     "e": "Duket i dobishëm por është i keq."},
                    {"q": "Keylogger regjistron?", "o": ["Gjithçka që shkruan", "Foto"], "c": 0,
                     "e": "Vjedh kodet gjatë shkrimit."},
                    {"q": "Skano USB para përdorimit?", "o": ["Po, detyrim", "Jo"], "c": 0,
                     "e": "USB është bartësi kryesor i Malware."},
                    {"q": "Rootkit i jep hakerit?", "o": ["Kontroll të plotë", "Asgjë"], "c": 0,
                     "e": "Virusi më i vështirë për t'u gjetur."},
                    {"q": "Windows i përditësuar?", "o": ["Më i vështirë hakuar", "Më i ngadaltë"], "c": 0,
                     "e": "Pjesët e sigurisë janë jetike."},
                    {"q": "Çfarë bën Spyware?", "o": ["Të ndjek fshehurazi", "Të mbron"], "c": 0,
                     "e": "Dërgon aktivitetin te hakerët."},
                    {"q": "Adware shërben për?", "o": ["Reklama bezdisshme", "Lojëra"], "c": 0,
                     "e": "Mund të të çojë në faqe rrezik."},
                    {"q": "A shpërndahet Worm-i?", "o": ["Vetvetiu në rrjet", "Vetëm me klik"], "c": 0,
                     "e": "Nuk duhet ndihmë njeriu."},
                    {"q": "Enkriptimi i bën skedarët?", "o": ["Të palexueshëm", "Më të vegj"], "c": 0,
                     "e": "Vetëm ju me çelës i shihni."},
                    {"q": "Lidhja më e dobët?", "o": ["Njerëzit", "Kompjuterët"], "c": 0,
                     "e": "Njerëzit manipulohen më lehtë."},
                    {"q": "Zero-day attack është?", "o": ["Rrezik i panjohur", "Virus i vjetër"], "c": 0,
                     "e": "Sulm pa ilaç momental."},
                    {"q": "Çfarë është Firewall?", "o": ["Filtër trafiku", "Lloj AV"], "c": 0,
                     "e": "Vendos kush hyn në rrjet."},
                    {"q": "Sulmi DDoS e bën faqen?", "o": ["Të paqasshme", "Më të shpejtë"], "c": 0,
                     "e": "E mbingarkon me kërkesa false."},
                    {"q": "Botnet është rrjet me?", "o": ["Pajisje të infektuara", "Njerëz smart"], "c": 0,
                     "e": "Përdoret për sulme masive."},
                    {"q": "Sandboxing është?", "o": ["Zonë prove sigurt", "Lojë"], "c": 0,
                     "e": "Izolon virusin mos hapet."},
                    {"q": "Digital Signature garanton?", "o": ["Origjinalitetin", "Ngjyrën"], "c": 0,
                     "e": "Konfirmon që skedari s'ka ndryshuar."},
                    {"q": "Spiunazhi industrial?", "o": ["Malware", "Celularë"], "c": 0,
                     "e": "Vjedhje sekretesh nga firmat."},
                    {"q": "Fik AV për instalim?", "o": ["Asnjëherë", "Po"], "c": 0,
                     "e": "Programet pirate infektojnë kështu."},
                    {"q": "Kodi i router-it duhet?", "o": ["I fortë", "S'ka rëndësi"], "c": 0,
                     "e": "Ndalon fqinjët dhe hakerët."},
                    {"q": "Wi-Fi më i ri?", "o": ["WPA3", "WEP"], "c": 0, "e": "WPA3 ofron mbrojtjen më të mirë."},
                    {"q": "Pajisjet IoT janë?", "o": ["Shpesh shënjestra", "100% sigurt"], "c": 0,
                     "e": "Kanë siguri të dobët të brendshme."},
                    {"q": "Bëj gjithmonë Log out?", "o": ["Po, gjithmonë", "Jo"], "c": 0,
                     "e": "Mbyll sesionin për të tjerët."},
                    {"q": "Kontrollo active sessions?", "o": ["Po, për hyrje", "Jo"], "c": 0,
                     "e": "Shih nëse dikush hyri në FB/Email."},
                    {"q": "Hard drive encryption?", "o": ["Mbrojtje maksimale", "E kotë"], "c": 0,
                     "e": "Ndalon vjedhjen edhe po u mor PC-ja."},
                    {"q": "Mësimi për sigurinë është?", "o": ["Proces i vazhdueshëm", "Një herë"], "c": 0,
                     "e": "Bota ndryshon, mbetu i informuar."}
                ],
                "final": [
                    {"q": "Çfarë është 'Juice Jacking'?", "o": ["Vjedhje me USB publike", "Karikim"], "c": 0,
                     "e": "Portat USB publike mund të kalojnë viruse."},
                    {"q": "Çfarë është 'Gjurma Dixhitale'?", "o": ["Gjurmë në internet", "Madhësi e të dhënave"],
                     "c": 0, "e": "Çdo gjë që postoni mbetet përgjithmonë."},
                    {"q": "Çfarë është sulmi 'Zero-Day'?", "o": ["Sulm në vrimë të panjohur", "Virus i vjetër"], "c": 0,
                     "e": "Sulm para se të bëhet riparimi."},
                    {"q": "Çfarë do të thotë 'Enkriptim'?", "o": ["Kodikim i të dhënave", "Fshirje"], "c": 0,
                     "e": "I bën të dhënat të palexueshme për hakerat."},
                    {"q": "Çfarë është '2FA'?", "o": ["Fjalëkalim + kod", "Dy fjalëkalime"], "c": 0,
                     "e": "Një shtresë shtesë sigurie."},
                    {"q": "Wi-Fi më i sigurt?", "o": ["WPA3", "WEP"], "c": 0, "e": "WPA3 është standardi më i ri."},
                    {"q": "Çfarë është 'Inxhinieria Sociale'?", "o": ["Manipulim njerëzish", "Programim"], "c": 0,
                     "e": "Gënjeshtër për të marrë sekrete."},
                    {"q": "Çfarë është 'Spyware'?", "o": ["Virus që ju ndjek", "Antivirus"], "c": 0,
                     "e": "Regjistron aktivitetin pa dijeni."},
                    {"q": "Çfarë është 'Keylogger'?", "o": ["Regjistron çdo shkronjë", "Program muzikor"], "c": 0,
                     "e": "Vjedh fjalëkalimet gjatë shkrimit."},
                    {"q": "Çfarë është 'Botnet'?", "o": ["Rrjet pajisjesh infektuar", "Lloj interneti"], "c": 0,
                     "e": "Përdoret për sulme masive."},
                    {"q": "Çfarë është 'Firewall'?", "o": ["Filtër trafiku", "Hard disk"], "c": 0,
                     "e": "Filtron trafikun drejt PC tuaj."},
                    {"q": "Çfarë është 'DDoS'?", "o": ["Sulm mbingarkese", "Internet i shpejtë"], "c": 0,
                     "e": "Rëzon faqet me trafik të lartë."},
                    {"q": "Çfarë është 'Trojan'?", "o": ["Virus i maskuar", "Lojë"], "c": 0,
                     "e": "Duket i dobishëm por është i rrezikshëm."},
                    {"q": "Çfarë është 'Rootkit'?", "o": ["Virus me kontroll të plotë", "Riparim"], "c": 0,
                     "e": "I jep hakerit qasje admini."},
                    {"q": "Çfarë është 'Sandboxing'?", "o": ["Zonë prove izoluar", "Lojë"], "c": 0,
                     "e": "Izolon virusin mos hapet."},
                    {"q": "Çfarë është 'Ransomware'?", "o": ["Virus shantazhi", "Reklamë"], "c": 0,
                     "e": "Bllokon skedarët për para."},
                    {"q": "Çfarë është 'Menaxheri i Kodit'?", "o": ["Vendi sigurt i kodeve", "Virus"], "c": 0,
                     "e": "Ruan fjalëkalimet e enkriptuara."},
                    {"q": "A ju fsheh 'Incognito'?", "o": ["Jo nga hakerat", "Po, plotësisht"], "c": 0,
                     "e": "Fsheh vetëm historinë lokale."},
                    {"q": "Çfarë është 'Spear Phishing'?", "o": ["Sulm i synuar", "Sulm masiv"], "c": 0,
                     "e": "Sulm ndaj një personi specifik."},
                    {"q": "Çfarë është 'Pharming'?", "o": ["Ridrejtim faqesh", "Bujqësi"], "c": 0,
                     "e": "Ju dërgon në faqe false pa dijeni."},
                    {"q": "Çfarë është 'SQL Injection'?", "o": ["Sulm në databazë", "Virus disku"], "c": 0,
                     "e": "Injektim kodi në baza të dhënash."},
                    {"q": "Çfarë është 'Brute Force'?", "o": ["Gjetje kodesh", "Lloj procesori"], "c": 0,
                     "e": "Provë me miliona kombinime."},
                    {"q": "Çfarë është 'Man-in-the-Middle'?", "o": ["Ndërhyrje mesazhesh", "Lojë"], "c": 0,
                     "e": "Haker që lexon mesazhet tuaja."},
                    {"q": "Çfarë është 'Malware'?", "o": ["Softuer i dëmshëm", "Program i mirë"], "c": 0,
                     "e": "Çdo program që dëmton PC-në."},
                    {"q": "Çfarë është 'Patch'?", "o": ["Riparim softueri", "Foto"], "c": 0,
                     "e": "Mbyll vrimat e sigurisë."},
                    {"q": "Çfarë është 'Backup'?", "o": ["Kopje rezervë", "Fshirje"], "c": 0,
                     "e": "Ju shpëton nëse humbni të dhënat."},
                    {"q": "Çfarë është 'Cookie'?", "o": ["Të dhëna sesioni", "Virus"], "c": 0,
                     "e": "Kujton cilësimet në faqe."},
                    {"q": "Çfarë është 'VPN'?", "o": ["Rrjet privat", "Net i shpejtë"], "c": 0,
                     "e": "Krijon tunel të sigurt të dhënash."},
                    {"q": "Çfarë është 'Whaling'?", "o": ["Sulm ndaj drejtorëve", "Gjueti"], "c": 0,
                     "e": "Phishing ndaj personave VIP."},
                    {"q": "Çfarë është 'Honey Pot'?", "o": ["Kurth hakerash", "Mjaltë"], "c": 0,
                     "e": "Sistem fals për të mashtruar hakerat."},
                    {"q": "Çfarë është 'Dark Web'?", "o": ["Pjesë fshehur e netit", "Net pa ngjyra"], "c": 0,
                     "e": "Pjesë që nuk gjenden në Google."},
                    {"q": "Çfarë është 'Biometrika'?", "o": ["Shenjë gishtash/Fytyrë", "Matje"], "c": 0,
                     "e": "Përdorimi i trupit për hyrje."},
                    {"q": "Çfarë është 'Spam'?", "o": ["Postë padëshiruar", "Virus"], "c": 0,
                     "e": "Mesazhe masive me reklama."},
                    {"q": "Çfarë është 'IoT'?", "o": ["Pajisje smart", "Procesor"], "c": 0,
                     "e": "Objekte të lidhura në internet."},
                    {"q": "Çfarë është 'White Hat'?", "o": ["Haker etik", "Haker i dëmshëm"], "c": 0,
                     "e": "Haker që ndihmon në siguri."},
                    {"q": "Çfarë është 'Black Hat'?", "o": ["Haker dashakeq", "Fillestar"], "c": 0,
                     "e": "Haker që vjedh për përfitim."},
                    {"q": "Çfarë është 'Clickjacking'?", "o": ["Butona false", "Klikim shpejtë"], "c": 0,
                     "e": "Ju mashtron të klikoni linqe fshehur."},
                    {"q": "Çfarë është 'Malvertising'?", "o": ["Reklama rrezikshme", "Lajme"], "c": 0,
                     "e": "Përhapje virusesh me reklama."},
                    {"q": "Çfarë është vjedhja e të dhënave?", "o": ["Rrjedhje të dhënash", "Fshirje"], "c": 0,
                     "e": "Kur të dhënat private bëhen publike."},
                    {"q": "Fjalëkalim i keq është?", "o": ["Ditëlindja", "Kombinim shenjash"], "c": 0,
                     "e": "Të dhënat e thjeshta gjehen shpejt."},
                    {"q": "Çfarë bën antivirusi?", "o": ["Skanon dhe pastron", "Fshin skedarë"], "c": 0,
                     "e": "Gjen dhe heq kodin e dëmshëm."},
                    {"q": "Rreziku më i madh?", "o": ["Gabimi njerëzor", "PC i dobët"], "c": 0,
                     "e": "Njerëzit manipulohen më lehtë."},
                    {"q": "Çfarë është 'Shoulder Surfing'?", "o": ["Shikim mbi shpatull", "Sërfim"], "c": 0,
                     "e": "Vjedhje kodi duke shikuar shkrimin."},
                    {"q": "Çfarë është 'Cold Wallet'?", "o": ["Vendi offline i kripteve", "Kuletë ftohtë"], "c": 0,
                     "e": "Mënyra më e sigurt për kripto."},
                    {"q": "Çfarë është 'Script Kiddie'?", "o": ["Haker amator", "Fëmijë"], "c": 0,
                     "e": "Përdor vegla pa dijeni."},
                    {"q": "Çfarë është 'Logic Bomb'?", "o": ["Kod që pret ngjarje", "Eksploziv"], "c": 0,
                     "e": "Virus që aktivizohet me kohë/ngjarje."},
                    {"q": "Çfarë është 'Bug'?", "o": ["Gabim në kod", "Insekt"], "c": 0,
                     "e": "Një anomali që mund të jetë rrezik."},
                    {"q": "Çfarë është 'Phreaking'?", "o": ["Hakim telefonash", "Frikë"], "c": 0,
                     "e": "Manipulim i rrjeteve telefonike."},
                    {"q": "Çfarë është 'Exploit'?", "o": ["Përdorim i vrimës", "Riparim"], "c": 0,
                     "e": "Vegël për hyrje nga vrima e sigurisë."},
                    {"q": "Siguria dixhitale është?", "o": ["Kujdes i vazhdueshëm", "Detyrë një herë"], "c": 0,
                     "e": "Duhet të jeni gjithmonë vigjilentë."}
                ]
            },
            'TR': {
                1: [  # Seviye 2 için 15 Soru
                    {"q": "HTTPS ne yapar?", "o": ["Veriyi şifreler", "Neti hızlandırır"], "c": 0,
                     "e": "HTTPS gizlilik için anahtardır."},
                    {"q": "Güçlü şifrede ne olur?", "o": ["Evcil hayvan adı", "Harf ve semboller"], "c": 1,
                     "e": "Karmaşıklık korumadır."},
                    {"q": "2FA nedir?", "o": ["İkinci güvenlik katmanı", "Ekran türü"], "c": 0,
                     "e": "Mobil kod gerektirir."},
                    {"q": "Şifrenizi kim bilmeli?", "o": ["Sadece ben", "En iyi arkadaş"], "c": 0,
                     "e": "Şifreler kişisel sırdır."},
                    {"q": "Genel Wi-Fi nasıldır?", "o": ["Güvensiz", "En hızlı"], "c": 0, "e": "Veriler şifrelenmez."},
                    {"q": "Güncellemeler neyi çözer?", "o": ["Güvenlik açıkları", "Renkleri"], "c": 0,
                     "e": "Hacker yollarını kapatır."},
                    {"q": "Ekranı ne zaman kitle?", "o": ["PC'den ayrılınca", "Sadece uyurken"], "c": 0,
                     "e": "Açık erişim bırakmayın."},
                    {"q": "Tek şifre her yer için iyi mi?", "o": ["Hayır, farklı kullan", "Evet, kolay olur"], "c": 0,
                     "e": "Diğer hesapları korur."},
                    {"q": "Site adında neye bakılır?", "o": ["Yazım hataları", "Tasarım"], "c": 0,
                     "e": "Sahte siteler benzer ad kullanır."},
                    {"q": "Pop-up 'virüs' diyor. Eylem?", "o": ["Yoksay/Kapat", "Hemen tıkla"], "c": 0,
                     "e": "Genelde virüs tuzağıdır."},
                    {"q": "Güçlü şifre uzunluğu?", "o": ["En az 12", "Maks 6"], "c": 0,
                     "e": "Uzun olanın kırılması zordur."},
                    {"q": "Kedi adı iyi şifre mi?", "o": ["Hayır, zayıf", "Evet, harika"], "c": 0,
                     "e": "Kişisel adlar kolay tahmin edilir."},
                    {"q": "Ödeme için HTTPS şart mı?", "o": ["Evet, her zaman", "Hayır, gerekmez"], "c": 0,
                     "e": "HTTPS güvenli ödeme sağlar."},
                    {"q": "PIN'den daha güvenli olan?", "o": ["Biyometri", "Doğum günü"], "c": 0,
                     "e": "Parmak izi size özeldir."},
                    {"q": "Şifreyi nereye girmemeli?", "o": ["Şüpheli linklere", "Resmi sitelere"], "c": 0,
                     "e": "Verileri dolandırıcılardan koru."}
                ],
                2: [  # Seviye 4 için 25 Soru
                    {"q": "Phishing nedir?", "o": ["Sahte mesaj tuzağı", "Spor"], "c": 0,
                     "e": "Şifre çalma dolandırıcılığı."},
                    {"q": "Gönderende neye bakılır?", "o": ["E-posta adresi", "Resim"], "c": 0,
                     "e": "İsimler kolayca sahtelenebilir."},
                    {"q": "Banka e-postayla PIN ister mi?", "o": ["Asla", "Sıkça"], "c": 0,
                     "e": "Bankalar sırları böyle istemez."},
                    {"q": "VPN neyi gizler?", "o": ["IP adresi", "PC Adı"], "c": 0,
                     "e": "VPN sizi hackerlara anonim yapar."},
                    {"q": "Acil 'şimdi yap' mesajı?", "o": ["Tuzak belirtisi", "Hep önemli"], "c": 0,
                     "e": "Hackerlar sahte aciliyet kullanır."},
                    {"q": "Yabancıdan 'zip' açılır mı?", "o": ["Hayır, asla", "Evet, ilginçse"], "c": 0,
                     "e": "Gizli Malware içerebilir."},
                    {"q": "Smishing nedir?", "o": ["SMS ile Phishing", "Telefon araması"], "c": 0,
                     "e": "SMS'ler yeni hedef."},
                    {"q": "Phishing linkleri nasıldır?", "o": ["Sahte ve tehlikeli", "Hep doğru"], "c": 0,
                     "e": "Zararlı sayfalara götürür."},
                    {"q": "Girişten önce neye bakılır?", "o": ["URL adresi", "Reklamlar"], "c": 0,
                     "e": "Gerçek alanı doğrulayın."},
                    {"q": "Antivirüs Phishing'i engeller mi?", "o": ["Evet, bazılarını", "Hayır, asla"], "c": 0,
                     "e": "Modern programlar tuzakları anlar."},
                    {"q": "HTTPS'siz sitede ödeme?", "o": ["Hayır, tehlikeli", "Evet, sorun yok"], "c": 0,
                     "e": "Kart verileri çalınabilir."},
                    {"q": "Arkadaş garip link attı?", "o": ["Hacklenmiş olabilir", "Güven"], "c": 0,
                     "e": "Çalınmış profiller kullanılır."},
                    {"q": "Sosyal mühendislik nedir?", "o": ["İnsan manipülasyonu", "Programlama"], "c": 0,
                     "e": "Yalanla şifre alma."},
                    {"q": "Çekiliş T.C. no istiyor?", "o": ["Tuzak, kaç", "Hepsini doldur"], "c": 0,
                     "e": "Kişisel veriler oyun değildir."},
                    {"q": "Gizli Mod hackerlardan korur mu?", "o": ["Hayır", "Evet"], "c": 0,
                     "e": "Sadece PC'de geçmişi gizler."},
                    {"q": "Spear Phishing nedir?", "o": ["Hedefli saldırı", "Genel saldırı"], "c": 0,
                     "e": "Çok hassas ve tehlikeli bir saldırı."},
                    {"q": "Spam mesajlara cevap verilir mi?", "o": ["Hayır, sil", "Evet, eğlenceye"], "c": 0,
                     "e": "E-postanın aktif olduğunu onaylar."},
                    {"q": "Özel fotolar nerede saklanır?", "o": ["Güvenli/Şifreli", "Genel bulut"], "c": 0,
                     "e": "Gizlilik öncelik olmalı."},
                    {"q": "Sosyal medya paylaşımları?", "o": ["Dikkat edilmeli", "Her şeyi atarım"], "c": 0,
                     "e": "Paylaşımlar sizin hakkınızda çok şey söyler."},
                    {"q": "Uygulama izinleri?", "o": ["Yüklemeden önce bak", "Asla bakmam"], "c": 0,
                     "e": "Aplikasyonlar çok erişim ister."},
                    {"q": "Gizli mod nerede kullanılır?", "o": ["Genel PC'lerde", "Evde"], "c": 0,
                     "e": "Başkalarının oturumu görmesini engeller."},
                    {"q": "Genel Chrome'da şifre kaydet?", "o": ["Hayır, asla", "Evet"], "c": 0,
                     "e": "Sonraki kullanıcı profilinize girebilir."},
                    {"q": "Wi-Fi kendiliğinden bağlandı?", "o": ["Riskli", "Harika"], "c": 0,
                     "e": "Hacker ağı olabilir."},
                    {"q": "Genel USB'de şarj et?", "o": ["Kaçınırım", "Her zaman"], "c": 0,
                     "e": "Juice Jacking veri hırsızlığı riski."},
                    {"q": "Gizlilik politikasını oku?", "o": ["Bilmem gerekir", "Sıkıcı"], "c": 0,
                     "e": "Verileri kimin kullandığını yazar."}
                ],
                3: [  # Seviye 6 için 30 Soru
                    {"q": "Ransomware nedir?", "o": ["Fidye virüsü", "Hediye"], "c": 0,
                     "e": "Dosyaları para için kilitler."},
                    {"q": "Backup fidye için çözüm mü?", "o": ["Evet, veriyi kurtarır", "Hayır"], "c": 0,
                     "e": "Yedekleme tek kurtuluştur."},
                    {"q": "Malware neyin kısaltması?", "o": ["Zararlı yazılım", "İyi yazılım"], "c": 0,
                     "e": "Zarar veren her program."},
                    {"q": "Bulut yedekleme güvenli mi?", "o": ["Evet, sunucularda", "Hayır"], "c": 0,
                     "e": "Veri cihaz dışında saklanır."},
                    {"q": "Şifre Yöneticisi ne yapar?", "o": ["Şifreleri saklar", "Onları çalar"], "c": 0,
                     "e": "Şifre yönetimi için en iyi yol."},
                    {"q": "Truva Atı (Trojan) nedir?", "o": ["Maskeli virüs", "Oyun"], "c": 0,
                     "e": "Faydalı görünür ama kötüdür."},
                    {"q": "Keylogger neyi kaydeder?", "o": ["Yazılan her şeyi", "Resimleri"], "c": 0,
                     "e": "Yazarken şifreleri çalar."},
                    {"q": "USB'yi taratmalı mı?", "o": ["Evet, şart", "Hayır"], "c": 0,
                     "e": "USB en büyük Malware taşıyıcısıdır."},
                    {"q": "Rootkit hacker'a ne verir?", "o": ["Tam kontrol", "Hiçbir şey"], "c": 0,
                     "e": "Tespit edilmesi en zor virüstür."},
                    {"q": "Güncel Windows iyi mi?", "o": ["Zor hacklenir", "Yavaştır"], "c": 0,
                     "e": "Güvenlik yamaları hayatidir."},
                    {"q": "Spyware ne yapar?", "o": ["Gizlice izler", "Korur"], "c": 0,
                     "e": "Hackerlara etkinliklerinizi atar."},
                    {"q": "Adware ne için kullanılır?", "o": ["Sinir bozucu reklam", "Oyun"], "c": 0,
                     "e": "Tehlikeli sitelere yönlendirebilir."},
                    {"q": "Solucan (Worm) yayılır mı?", "o": ["Net üzerinden kendi", "Sadece tıkla"], "c": 0,
                     "e": "Yayılmak için insan yardımı gerekmez."},
                    {"q": "Şifreleme dosyaları ne yapar?", "o": ["Okunamaz hale getirir", "Küçültür"], "c": 0,
                     "e": "Sadece anahtarı olan açabilir."},
                    {"q": "En zayıf halka?", "o": ["İnsanlar", "Bilgisayarlar"], "c": 0,
                     "e": "İnsanlar manipülasyona açıktır."},
                    {"q": "Zero-day saldırısı nedir?", "o": ["Bilinmeyen tehdit", "Eski virüs"], "c": 0,
                     "e": "Henüz çözümü olmayan saldırı."},
                    {"q": "Güvenlik Duvarı nedir?", "o": ["Trafik filtresi", "AV türü"], "c": 0,
                     "e": "Ağa kimin gireceğine karar verir."},
                    {"q": "DDoS saldırısı siteyi ne yapar?", "o": ["Erişilemez", "Daha hızlı"], "c": 0,
                     "e": "Sahte isteklerle aşırı yükler."},
                    {"q": "Botnet nedir?", "o": ["Zombi cihaz ağı", "Zeki insanlar"], "c": 0,
                     "e": "Kitlesel saldırılar için kullanılır."},
                    {"q": "Sandboxing nedir?", "o": ["Güvenli test alanı", "Oyun"], "c": 0,
                     "e": "Virüsün yayılmasını izole eder."},
                    {"q": "Dijital İmza neyi garanti eder?", "o": ["Orijinallik", "Renk"], "c": 0,
                     "e": "Belgenin değişmediğini kanıtlar."},
                    {"q": "Endüstriyel casusluk?", "o": ["Malware", "Telefon"], "c": 0,
                     "e": "Şirket sırlarını çalmak."},
                    {"q": "Kurulumda AV kapatılır mı?", "o": ["Asla", "Evet"], "c": 0,
                     "e": "Korsan yazılımlar böyle bulaşır."},
                    {"q": "Router şifresi nasıl olmalı?", "o": ["Güçlü", "Önemsiz"], "c": 0,
                     "e": "Komşuları ve hackerları durdurur."},
                    {"q": "En yeni Wi-Fi standardı?", "o": ["WPA3", "WEP"], "c": 0,
                     "e": "WPA3 en iyi güncel korumayı sunar."},
                    {"q": "IoT cihazları nasıldır?", "o": ["Sık hedeflerdir", "%100 güvenli"], "c": 0,
                     "e": "Dahili güvenlikleri zayıftır."},
                    {"q": "Her zaman çıkış (Log out) yap?", "o": ["Evet, her zaman", "Hayır"], "c": 0,
                     "e": "Oturumu başkalarına kapatır."},
                    {"q": "Aktif oturumları kontrol et?", "o": ["Evet, sızma için", "Hayır"], "c": 0,
                     "e": "Başkası hesabınızda mı görün."},
                    {"q": "Disk şifreleme?", "o": ["Maks koruma", "Gereksiz"], "c": 0,
                     "e": "PC çalınsa bile veriyi korur."},
                    {"q": "Dijital güvenlik eğitimi?", "o": ["Sürekli süreç", "Bir seferlik"], "c": 0,
                     "e": "Dünya değişiyor, güncel kalın."}
                ],
                "final": [
                    {"q": "Juice Jacking nedir?", "o": ["Genel USB ile hırsızlık", "Hızlı şarj"], "c": 0,
                     "e": "Genel USB portları virüs bulaştırabilir."},
                    {"q": "Dijital Ayak İzi nedir?", "o": ["İnternetteki iz", "Veri boyutu"], "c": 0,
                     "e": "Paylaştığınız her şey sonsuza dek kalır."},
                    {"q": "Sıfır Gün (Zero-Day) nedir?", "o": ["Bilinmeyen açık", "Eski virüs"], "c": 0,
                     "e": "Yama çıkmadan yapılan saldırıdır."},
                    {"q": "Şifreleme (Encryption) nedir?", "o": ["Veriyi kodlama", "Silme"], "c": 0,
                     "e": "Verileri hakerlar için okunmaz yapar."},
                    {"q": "2FA nedir?", "o": ["Şifre + ek kod", "İki şifre"], "c": 0,
                     "e": "Ek bir güvenlik katmanıdır."},
                    {"q": "En güvenli Wi-Fi?", "o": ["WPA3", "WEP"], "c": 0,
                     "e": "WPA3 en yeni güvenlik standardıdır."},
                    {"q": "Sosyal Mühendislik nedir?", "o": ["İnsan manipülasyonu", "Programlama"], "c": 0,
                     "e": "Sırları almak için yalan söyleme."},
                    {"q": "Spyware nedir?", "o": ["İzleyen virüs", "Antivirüs"], "c": 0,
                     "e": "İzinsiz aktivite kaydeder."},
                    {"q": "Keylogger nedir?", "o": ["Tuş kaydeder", "Müzik çalar"], "c": 0,
                     "e": "Yazarken şifreleri çalar."},
                    {"q": "Botnet nedir?", "o": ["Zombi cihaz ağı", "İnternet türü"], "c": 0,
                     "e": "Kitlesel saldırılar için kullanılır."},
                    {"q": "Güvenlik Duvarı nedir?", "o": ["Trafik filtresi", "Hard disk"], "c": 0,
                     "e": "PC'nize gelen trafiği filtreler."},
                    {"q": "DDoS nedir?", "o": ["Aşırı yükleme", "Hızlı internet"], "c": 0,
                     "e": "Siteyi sahte trafikle çökertir."},
                    {"q": "Trojan nedir?", "o": ["Maskeli virüs", "Oyun"], "c": 0,
                     "e": "Yararlı görünür ama tehlikelidir."},
                    {"q": "Rootkit nedir?", "o": ["Tam kontrol virüsü", "Tamir seti"], "c": 0,
                     "e": "Hacker'a admin yetkisi verir."},
                    {"q": "Sandboxing nedir?", "o": ["İzole test alanı", "Oyun"], "c": 0,
                     "e": "Virüs yayılımını engeller."},
                    {"q": "Ransomware nedir?", "o": ["Fidye virüsü", "Reklam"], "c": 0,
                     "e": "Dosyaları para için kilitler."},
                    {"q": "Şifre Yöneticisi nedir?", "o": ["Şifre kasası", "Virüs"], "c": 0,
                     "e": "Şifreleri kodlu saklar."},
                    {"q": "Gizli Mod korur mu?", "o": ["Hackerlardan değil", "Evet, tam"], "c": 0,
                     "e": "Sadece geçmişi yerel gizler."},
                    {"q": "Spear Phishing nedir?", "o": ["Hedefli saldırı", "Genel saldırı"], "c": 0,
                     "e": "Belirli bir kişiye yapılan saldırı."},
                    {"q": "Pharming nedir?", "o": ["Site yönlendirme", "Tarım"], "c": 0,
                     "e": "Sizi gizlice sahte siteye götürür."},
                    {"q": "SQL Injection nedir?", "o": ["Veritabanı saldırısı", "Disk virüsü"], "c": 0,
                     "e": "Veritabanına zararlı kod ekleme."},
                    {"q": "Brute Force nedir?", "o": ["Şifre deneme", "İşlemci türü"], "c": 0,
                     "e": "Milyonlarca kombinasyon denemesi."},
                    {"q": "Aradaki Adam saldırısı?", "o": ["Mesaj yakalama", "Oyun"], "c": 0,
                     "e": "Hacker'ın mesajları okuması."},
                    {"q": "Malware nedir?", "o": ["Zararlı yazılım", "İyi program"], "c": 0,
                     "e": "PC'ye zarar veren her program."},
                    {"q": "Yama (Patch) nedir?", "o": ["Yazılım tamiri", "Resim"], "c": 0,
                     "e": "Güvenlik açıklarını kapatır."},
                    {"q": "Yedekleme (Backup) nedir?", "o": ["Veri kopyası", "Silme"], "c": 0,
                     "e": "Veri kaybından kurtarır."},
                    {"q": "Çerez (Cookie) nedir?", "o": ["Oturum verisi", "Virüs"], "c": 0,
                     "e": "Site ayarlarını hatırlar."},
                    {"q": "VPN nedir?", "o": ["Özel ağ", "Hızlı net"], "c": 0, "e": "Güvenli veri tüneli oluşturur."},
                    {"q": "Whaling nedir?", "o": ["Yönetici saldırısı", "Avlanma"], "c": 0,
                     "e": "VIP kişilere yapılan Phishing."},
                    {"q": "Honey Pot nedir?", "o": ["Hacker tuzağı", "Bal"], "c": 0,
                     "e": "Hacker'ı kandıran sahte sistem."},
                    {"q": "Dark Web nedir?", "o": ["Gizli web kısmı", "Renksiz web"], "c": 0,
                     "e": "Google'da çıkmayan kısımlar."},
                    {"q": "Biyometri nedir?", "o": ["Parmak izi/Yüz", "Ölçüm"], "c": 0,
                     "e": "Giriş için vücudu kullanma."},
                    {"q": "Spam nedir?", "o": ["İstenmeyen posta", "Virüs"], "c": 0,
                     "e": "Toplu reklam veya tuzak mesajlar."},
                    {"q": "IoT nedir?", "o": ["Akıllı cihazlar", "İşlemci"], "c": 0, "e": "İnternete bağlı nesneler."},
                    {"q": "Beyaz Şapka nedir?", "o": ["Etik hacker", "Zararlı hacker"], "c": 0,
                     "e": "Güvenliğe yardım eden hacker."},
                    {"q": "Siyah Şapka nedir?", "o": ["Kötü niyetli hacker", "Yeni"], "c": 0,
                     "e": "Çıkarları için çalan hacker."},
                    {"q": "Clickjacking nedir?", "o": ["Sahte butonlar", "Hızlı tık"], "c": 0,
                     "e": "Gizli linke tıklatmayı sağlar."},
                    {"q": "Malvertising nedir?", "o": ["Zararlı reklamlar", "Haber"], "c": 0,
                     "e": "Reklamla virüs yayma."},
                    {"q": "Veri İhlali nedir?", "o": ["Veri sızıntısı", "Silme"], "c": 0,
                     "e": "Özel verilerin halka açılması."},
                    {"q": "Kötü şifre nedir?", "o": ["Doğum günü", "Sembollü"], "c": 0,
                     "e": "Basit veriler hemen tahmin edilir."},
                    {"q": "Antivirüs ne yapar?", "o": ["Tarar ve temizler", "Dosya siler"], "c": 0,
                     "e": "Zararlı kodu bulur ve kaldırır."},
                    {"q": "En büyük risk?", "o": ["İnsan hatası", "Zayıf PC"], "c": 0,
                     "e": "İnsanları manipüle etmek kolaydır."},
                    {"q": "Shoulder Surfing nedir?", "o": ["Omuzdan bakma", "Sörf"], "c": 0,
                     "e": "Yazarken şifreyi izleyerek çalma."},
                    {"q": "Soğuk Cüzdan nedir?", "o": ["Çevrimdışı kripto", "Soğuk çanta"], "c": 0,
                     "e": "Kripto için en güvenli yol."},
                    {"q": "Script Kiddie nedir?", "o": ["Amatör hacker", "Çocuk"], "c": 0,
                     "e": "Bilmeden hazır araç kullanır."},
                    {"q": "Logic Bomb nedir?", "o": ["Olay bekleyen kod", "Patlayıcı"], "c": 0,
                     "e": "Belli zamanda tetiklenen virüs."},
                    {"q": "Bug nedir?", "o": ["Kod hatası", "Böcek"], "c": 0, "e": "Tehlikeli olabilecek bir hata."},
                    {"q": "Phreaking nedir?", "o": ["Telefon hackleme", "Korku"], "c": 0,
                     "e": "Telefon hatlarını manipüle etme."},
                    {"q": "Exploit nedir?", "o": ["Açık kullanma", "Tamir"], "c": 0,
                     "e": "Güvenlik açığından giriş aracı."},
                    {"q": "Dijital güvenlik?", "o": ["Sürekli dikkat", "Tek seferlik"], "c": 0,
                     "e": "Her zaman dikkatli olmalısınız."}
                ]
            }

        }

    def load_for_level(self, level):
        lang = self.settings.language or 'MK'
        q_idx = self.questions_map.get(level, 1)
        if q_idx == "final":
            full_pool = []
            for i in [1, 2, 3]: full_pool.extend(self.all_questions.get(lang, {}).get(i, []))
        else:
            full_pool = self.all_questions.get(lang, {}).get(q_idx, [])
        if not full_pool: full_pool = self.all_questions.get('MK', {}).get(q_idx if q_idx != "final" else 1, [])
        self.questions_pool = list(full_pool); random.shuffle(self.questions_pool)
        self.used_questions = []; self.active = False; self.correct_answers_count = 0

    def trigger_random(self):
        avail = [q for q in self.questions_pool if q not in self.used_questions]
        if not avail: self.used_questions = []; avail = self.questions_pool
        if avail:
            self.current_q = random.choice(avail)
            self.used_questions.append(self.current_q)
            self.active = True; self.showing_feedback = False

    def _check(self, idx):
        self.correct = (idx == self.current_q["c"])
        if self.correct:
            self.correct_answers_count += 1
            # МАТЕМАТИЧКА КОРЕКЦИЈА ЗА НИВО 7
            if self.settings.current_level == 7:
                # 3000 HP / 30 прашања = ТОЧНО 100 штета по прашање
                self.settings.pending_boss_damage = 100
            else:
                self.settings.pending_boss_damage = 10
        else:
            self.settings.shields = max(0, self.settings.shields - 1)
        self.showing_feedback = True

    def draw(self):
        if not self.active: return
        ov = pygame.Surface((900, 700), pygame.SRCALPHA); ov.fill((0, 0, 0, 240)); self.screen.blit(ov, (0, 0))
        font = pygame.font.Font(resource_path(self.settings.font_path), 16)
        pygame.draw.rect(self.screen, (207, 212, 242), (100, 150, 700, 420), border_radius=15)
        lang = self.settings.language or 'MK'
        correct_labels = {'MK': "ТОЧНИ", 'EN': "CORRECT", 'AL': "TË SAKTA", 'TR': "DOĞRU"}
        info_labels = {'MK': "ИНФО:", 'EN': "INFO:", 'AL': "INFO:", 'TR': "BİLGİ:"}
        status_labels = {'MK': ("ТОЧНО!", "ГРЕШНО!"), 'EN': ("CORRECT!", "WRONG!"), 'AL': ("E SAKTË!", "GABIM!"), 'TR': ("DOĞRU!", "YANLIŞ!")}
        label = correct_labels.get(lang, "CORRECT"); info_text = info_labels.get(lang, "INFO:")
        c_status, w_status = status_labels.get(lang, ("CORRECT!", "WRONG!"))
        limit = 30 if self.settings.current_level == 7 else 15 if self.settings.current_level == 6 else 10 if self.settings.current_level == 4 else 5
        prog = f"{label}: {self.correct_answers_count}/{limit}"
        self.screen.blit(font.render(prog, True, (0, 0, 150)), (130, 170))
        if not self.showing_feedback:
            draw_text_wrapped(self.screen, self.current_q["q"], 130, 210, 640, font, (0, 0, 0))
            for i, opt in enumerate(self.current_q["o"]):
                r = pygame.Rect(130, 320 + i * 80, 640, 60); pygame.draw.rect(self.screen, (100, 150, 255), r, border_radius=10)
                self.screen.blit(font.render(f"{i + 1}. {opt}", True, (255, 255, 255)), (150, 335 + i * 80))
        else:
            color = (0, 150, 0) if self.correct else (200, 0, 0)
            self.screen.blit(font.render(c_status if self.correct else w_status, True, color), (130, 210))
            self.screen.blit(font.render(info_text, True, (0, 0, 0)), (130, 250))
            draw_text_wrapped(self.screen, self.current_q["e"], 130, 290, 640, font, (30, 30, 30))
            cont = self.settings.translations[lang]['press_space']
            self.screen.blit(font.render(cont, True, (150, 0, 0)), (130, 520))

    def handle_event(self, event):
        if not self.active: return
        if self.showing_feedback and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: self.active = False
        elif not self.showing_feedback and event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(len(self.current_q.get("o", []))):
                if pygame.Rect(130, 320 + i * 80, 640, 60).collidepoint(event.pos): self._check(i)

def draw_text_wrapped(screen, text, x, y, max_w, font, color):
    words = text.split(' '); line = ""; curr_y = y
    for word in words:
        if font.size(line + word)[0] < max_w: line += word + " "
        else: screen.blit(font.render(line, True, color), (x, curr_y)); curr_y += font.get_linesize() + 5; line = word + " "
    screen.blit(font.render(line, True, color), (x, curr_y)); return curr_y

class Boss(pygame.sprite.Sprite):
    def __init__(self, settings, level=1):
        super().__init__()
        self.settings = settings
        self.level = level
        self.target_y = 80
        self.max_hp = 100 if level == 2 else 200 if level == 4 else 300 if level == 6 else 3000
        self.current_hp = self.max_hp
        self.t = 0.0
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_interval = 3000

        try:
            img = pygame.image.load(resource_path(os.path.join('assets', 'monster4.png'))).convert_alpha() if level==2 else pygame.image.load(resource_path(os.path.join('assets', 'monster1.png'))).convert_alpha() if level==4 else pygame.image.load(resource_path(os.path.join('assets', 'monster2.png'))).convert_alpha() if level==6 else pygame.image.load(resource_path(os.path.join('assets', 'monster3.png'))).convert_alpha()
            self.image = pygame.transform.scale(img, (180, 180))
        except: self.image = pygame.Surface((150, 150)); self.image.fill((150, 0, 0))
        self.rect = self.image.get_rect(center=(450, -100))

    # Во ui_manager.py, Boss.update
    def update(self, player_x):
        if self.rect.y < self.target_y:
            self.rect.y += 2
        else:
            # Екстремна брзина за финалната битка
            speed_factor = 0.08 if self.level == 7 else 0.02 + (self.level - 2) * 0.01
            self.t += speed_factor
            amplitude = 250 if self.level == 7 else 200 + (self.level * 10)
            self.rect.x = 360 + math.sin(self.t) * amplitude

    def draw(self, screen):
        screen.blit(self.image, self.rect); pygame.draw.rect(screen, (50, 50, 50), (300, 50, 300, 15))
        pygame.draw.rect(screen, (255, 0, 0), (300, 50, (max(0, self.current_hp) / self.max_hp) * 300, 15))

def draw_knowledge_summary(screen, settings, knowledge_list):
    lang = settings.language or 'MK'
    pages = [knowledge_list[i:i + 16] for i in range(0, len(knowledge_list), 16)]
    if not pages: pages = [[]]
    for p_idx, current_page in enumerate(pages):
        overlay = pygame.Surface((900, 700), pygame.SRCALPHA); overlay.fill((0, 20, 60, 245)); screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (207, 212, 242), (30, 30, 840, 640), border_radius=15)
        pygame.draw.rect(screen, (0, 237, 255), (30, 30, 840, 640), width=5, border_radius=15)
        font_t = pygame.font.Font(resource_path(settings.font_path), 18);
        font_s = pygame.font.Font(resource_path(settings.font_path), 9)
        summary_titles = {'MK': "РЕЗИМЕ НА ЗНАЕЊЕТО", 'EN': "KNOWLEDGE SUMMARY", 'AL': "PËRMBLEDHJA E NJOHURIVE", 'TR': "BİLGİ ÖZETİ"}
        title_text = f"{summary_titles.get(lang, 'KNOWLEDGE SUMMARY')} ({p_idx+1}/{len(pages)})"
        title_surf = font_t.render(title_text, True, (0, 0, 100))
        screen.blit(title_surf, (450 - title_surf.get_width() // 2, 50))
        for i, lesson in enumerate(current_page):
            col, row = i // 8, i % 8
            x, y_pos = (65 if col == 0 else 465), 110 + row * 65
            pygame.draw.circle(screen, (0, 237, 255), (x - 15, y_pos + 5), 4)
            draw_text_wrapped(screen, lesson, x, y_pos, 360, font_s, (30, 30, 30))
        space_txt = settings.translations[lang]['press_space']
        screen.blit(font_s.render(space_txt, True, (200, 0, 0)), (450 - font_s.size(space_txt)[0] // 2, 645))
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: waiting = False
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

def draw_victory_screen(screen, settings):
    screen.fill((0, 40, 0)); f = pygame.font.Font(resource_path(settings.font_path), 20)
    msg = settings.translations[settings.language]['victory_msg']
    screen.blit(f.render(msg, True, (255, 255, 0)), (450 - f.size(msg)[0] // 2, 350))

def draw_level_complete(screen, settings):
    lang = settings.language or 'MK'
    msg = settings.translations[lang].get('level_up', "LEVEL COMPLETE").format(settings.current_level)
    font = pygame.font.Font(resource_path(settings.font_path), 22)
    txt_surf = font.render(msg, True, (0, 255, 0))
    screen.blit(txt_surf, (450 - txt_surf.get_width() // 2, 350))


def draw_victory_screen(screen, settings, all_lessons):
    lang = settings.language or 'MK'
    pages = [all_lessons[i:i + 12] for i in range(0, len(all_lessons), 12)]
    if not pages: pages = [[]]

    for p_idx, current_page in enumerate(pages):
        screen.fill((0, 40, 0))
        f_title = pygame.font.Font(resource_path(settings.font_path), 22)
        f_text = pygame.font.Font(resource_path(settings.font_path), 10)

        msg = settings.translations[lang]['victory_msg']
        title_surf = f_title.render(msg, True, (255, 255, 0))
        screen.blit(title_surf, (450 - title_surf.get_width() // 2, 50))


        sub_titles = {
            'MK': "ЛИСТА НА ТВОИТЕ САЈБЕР ВЕШТИНИ:",
            'EN': "YOUR CYBER SKILLS LIST:",
            'AL': "LISTA E SHKATHTËSIVE TUAJA KIBERNETIKE:",
            'TR': "SİBER YETENEK LİSTENİZ:"
        }

        sub_label = sub_titles.get(lang, '')
        if len(pages) > 1:
            sub_text = f"{sub_label} ({p_idx + 1}/{len(pages)})"
        else:
            sub_text = sub_label

        sub_surf = f_text.render(sub_text, True, (255, 255, 255))
        screen.blit(sub_surf, (450 - sub_surf.get_width() // 2, 100))

        for i, lesson in enumerate(current_page):
            y_pos = 150 + i * 40
            # Се користи draw_text_wrapped за долгите реченици
            draw_text_wrapped(screen, f"• {lesson}", 100, y_pos, 700, f_text, (200, 255, 200))

        exit_msg = settings.translations[lang]['press_space']
        exit_surf = f_text.render(exit_msg, True, (255, 255, 255))
        screen.blit(exit_surf, (450 - exit_surf.get_width() // 2, 650))

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

def draw_victory_congratulations(screen, settings):
    lang = settings.language or 'MK'
    screen.fill((0, 50, 0))
    f_big = pygame.font.Font(resource_path(settings.font_path), 20) # Малку помал фонт за да собере
    f_small = pygame.font.Font(resource_path(settings.font_path), 14)

    msg = settings.translations[lang]['victory_msg']
    title_surf = f_big.render(msg, True, (255, 255, 0))
    title_rect = title_surf.get_rect(center=(450, 200))
    screen.blit(title_surf, title_rect)

    options = {
        'MK': ["Притисни SPACE за знаења", "Притисни 'R' за рестарт", "Притисни ESC за излез"],
        'EN': ["Press SPACE for knowledge", "Press 'R' to restart", "Press ESC to exit"],
        'AL': ["Shtyp SPACE për njohuritë", "Shtyp 'R' për restart", "Shtyp ESC për dalje"],
        'TR': ["Bilgi için SPACE'e bas", "Yeniden başlatmak için 'R'ye bas", "Çıkmak için ESC'ye bas"]
    }

    lines = options.get(lang, options['EN'])
    for i, line in enumerate(lines):
        txt_surf = f_small.render(line, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=(450, 400 + i * 60))
        screen.blit(txt_surf, txt_rect)

    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return "SHOW_SKILLS"
                if event.key == pygame.K_r: return "RESTART"
                if event.key == pygame.K_ESCAPE: return "QUIT"
