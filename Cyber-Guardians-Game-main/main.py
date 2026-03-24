import pygame, sys, random, os
import asyncio


from settings import GameSettings
from entities import Bullet, Enemy, KnowledgeDrop, BossBullet
from ui_manager import *
from player import Player

import sys, os

def resource_path(relative_path):
    # Get the folder of this script
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    pygame.init()
    configs = GameSettings()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("Cyber Guardians")
    clock = pygame.time.Clock()
    bg = LayeredBackgroundBlue(configs)
    f_hud = pygame.font.Font(resource_path(configs.font_path), 14)
    tts = TTS()
    pygame.mixer.music.load(resource_path("assets/ES_Tiger Tracks - Lexica.mp3"))
    pygame.mixer.music.set_volume(0.3)  # 0.0 - 1.0
    pygame.mixer.music.play(-1)  # -1 = infinite loop
    shoot_sfx = pygame.mixer.Sound(resource_path("assets/ES_laser.wav"))
    drop_sfx = pygame.mixer.Sound(resource_path("assets/ES_Token.mp3"))
    enemy_die_sfx = pygame.mixer.Sound(resource_path("assets/ES_enemydeath.wav"))
    extra_life_sfx = pygame.mixer.Sound(resource_path("assets/ES_extralife.wav"))
    player_hit_sfx = pygame.mixer.Sound(resource_path("assets/ES_playerHit.wav"))
    player_hit_sfx.set_volume(0.6)
    extra_life_sfx.set_volume(0.5)
    enemy_die_sfx.set_volume(0.5)
    shoot_sfx.set_volume(0.4)
    drop_sfx.set_volume(0.8)

    paused = False

    # База на знаења
    knowledge_by_lang = {
        'MK': {
            1: [
                "HTTPS ги шифрира податоците меѓу тебе и сајтот.", "Силна лозинка има големи, мали букви и знаци.",
                "2FA додава втор слој на безбедност (код на моб).", "Никогаш не ја кажувај лозинката на непознати.",
                "Јавните Wi-Fi мрежи често не се шифрирани.", "Update на софтверот ги поправа безбедносните дупки.",
                "Секогаш заклучувај го екранот кога не си пред компјутер.",
                "Користи различни лозинки за различни профили.",
                "Провери дали името на сајтот е правилно напишано.",
                "Не кликај на 'Pop-up' реклами што велат дека имаш вирус.",
                "Лозинката треба да има најмалку 12 карактери.", "Името на миленичето е лоша лозинка.",
                "HTTPS е задолжителен за онлајн купување.", "Биометрика (отпечаток) е посигурна од ПИН код.",
                "Никогаш не внесувај лозинка на сомнителни линкови."
            ],
            3: [
                "Phishing е лажна порака што бара твои податоци.", "Провери го емаилот на испраќачот за грешки.",
                "Банките никогаш не бараат лозинка преку емаил.", "VPN ја крие твојата IP адреса од хакери.",
                "Внимавај на пораки што создаваат лажна итност.", "Не отворај 'zip' фајлови од непознати лица.",
                "Phishing може да се случи и преку СМС (Smishing).", "Линковите во Phishing мејловите се лажни.",
                "Секогаш проверувај го URL-то пред да се најавиш.",
                "Антивирусот може да препознае некои Phishing сајтови.",
                "Никогаш не плаќај со картичка на сајт без HTTPS.",
                "Твојот пријател може да биде хакиран и да прати вирус.",
                "Социјален инженеринг е манипулација за крадење шифри.",
                "Внимавај на наградни игри што бараат лични податоци.",
                "Приватниот мод во браузерот не те крие од хакери.",
                "Spear Phishing е напад насочен кон точно одредена личност.",
                "Никогаш не одговарај на спам пораки.", "Чувај ги приватните слики на безбедно место.",
                "Внимавај што споделуваш на социјалните мрежи.",
                "Проверувај ги дозволите на апликациите што ги инсталираш.",
                "Користи инкогнито мод на јавни компјутери.", "Не ги зачувувај лозинките на јавни прелистувачи.",
                "Оневозможи го автоматското поврзување на Wi-Fi.", "Избегнувај полнење телефон на непознати USB порти.",
                "Проверувај ја изјавата за приватност на новите апликации."
            ],
            5: [
                "Backup значи правење копија на вашите фајлови.", "Ransomware ги заклучува фајловите и бара пари.",
                "Malware е секој софтвер што штети на системот.", "Cloud Backup е безбеден начин за чување податоци.",
                "Password Manager ги чува сите твои шифри на едно место.",
                "Тројански коњ се преправа дека е корисна програма.",
                "Keylogger е вирус што снима сè што пишуваш.", "Секогаш скенирај ги USB стиковите пред употреба.",
                "Rootkit му дава на хакерот целосна контрола.", "Ажуриран Windows е многу потежок за хакирање.",
                "Spyware те следи што правиш на интернет.", "Adware ти прикажува досадни и опасни реклами.",
                "Worm (црв) се шири низ мрежата без твоја помош.", "Енкрипција ги прави фајловите нечитливи за хакери.",
                "Најслабата карика во безбедноста е човекот.", "Zero-day напад користи дупка која уште не е откриена.",
                "Firewall го филтрира мрежниот сообраќај.", "DDoS напад го преоптоварува сајтот со сообраќај.",
                "Botnet е мрежа од заразени компјутери под контрола.",
                "Sandboxing е изолирана средина за тестирање вируси.",
                "Digital Signature гарантира автентичност на документ.",
                "Индустриската шпионажа често користи Malware.",
                "Никогаш не исклучувај го антивирусот при инсталација.",
                "Рутерот треба да има силна лозинка за администратор.",
                "WPA3 е најновиот и најбезбеден Wi-Fi стандард.", "IoT уредите се честа мета на хакери.",
                "Секогаш излегувај (Log out) од профилот по користење.",
                "Проверувај ја листата на активни сесии на профилот.",
                "Шифрирај го целиот хард диск за максимална заштита.", "Учи постојано за новите дигитални закани."
            ]
        },
        'EN': {
            1: [
                "HTTPS encrypts data between you and the site.", "A strong password has upper, lower case and symbols.",
                "2FA adds a second layer of security (mobile code).", "Never tell your password to strangers.",
                "Public Wi-Fi networks are often not encrypted.", "Software updates fix security holes.",
                "Always lock your screen when away from the PC.", "Use different passwords for different accounts.",
                "Check if the site name is spelled correctly.", "Don't click Pop-up ads saying you have a virus.",
                "Passwords should have at least 12 characters.", "A pet's name is a bad password.",
                "HTTPS is mandatory for online shopping.", "Biometrics (fingerprint) is more secure than a PIN.",
                "Never enter a password on suspicious links."
            ],
            3: [
                "Phishing is a fake message asking for your data.", "Check the sender's email for errors.",
                "Banks never ask for passwords via email.", "VPN hides your IP address from hackers.",
                "Watch out for messages creating fake urgency.", "Don't open 'zip' files from unknown people.",
                "Phishing can happen via SMS too (Smishing).", "Links in Phishing emails are fake.",
                "Always check the URL before logging in.", "Antivirus can detect some Phishing sites.",
                "Never pay with a card on a site without HTTPS.", "A friend might be hacked and send a virus.",
                "Social engineering is manipulation to steal keys.", "Watch for contests asking for personal data.",
                "Browser Private mode doesn't hide you from hackers.",
                "Spear Phishing is an attack targeted at a specific person.",
                "Never reply to spam messages.", "Keep private photos in a secure place.",
                "Be careful what you share on social networks.", "Check permissions of apps you install.",
                "Use incognito mode on public computers.", "Don't save passwords on public browsers.",
                "Disable automatic Wi-Fi connection.", "Avoid charging your phone on unknown USB ports.",
                "Check the privacy statement of new apps."
            ],
            5: [
                "Backup means making a copy of your files.", "Ransomware locks files and demands money.",
                "Malware is any software that harms the system.", "Cloud Backup is a secure way to store data.",
                "A Password Manager keeps all your keys in one place.",
                "A Trojan horse pretends to be a useful program.",
                "A Keylogger is a virus that records everything you type.", "Always scan USB sticks before use.",
                "A Rootkit gives a hacker full control.", "Updated Windows is much harder to hack.",
                "Spyware tracks what you do on the internet.", "Adware shows you annoying and dangerous ads.",
                "A Worm spreads through the network without your help.",
                "Encryption makes files unreadable for hackers.",
                "The weakest link in security is the human.", "A Zero-day attack uses a hole not yet discovered.",
                "A Firewall filters network traffic.", "A DDoS attack overloads a site with traffic.",
                "A Botnet is a network of infected computers under control.",
                "Sandboxing is an isolated environment for testing viruses.",
                "A Digital Signature guarantees document authenticity.", "Industrial espionage often uses Malware.",
                "Never turn off antivirus during installation.", "Routers should have a strong admin password.",
                "WPA3 is the latest and most secure Wi-Fi standard.", "IoT devices are frequent targets for hackers.",
                "Always Log out of your profile after use.", "Check the list of active sessions on your profile.",
                "Encrypt the entire hard drive for max protection.", "Keep learning about new digital threats."
            ]
        },
        'AL': {
            1: [
                "HTTPS kodon të dhënat mes jush dhe faqes.",
                "Fjalëkalimi i fortë ka shkronja të mëdha, të vogla dhe simbole.",
                "2FA shton një shtresë të dytë sigurie (kod celular).",
                "Asnjëherë mos ua tregoni fjalëkalimin të huajve.",
                "Rrjetet publike Wi-Fi shpesh nuk janë të koduara.",
                "Përditësimet e softuerit rregullojnë vrimat e sigurisë.",
                "Gjithmonë bllokoni ekranin kur jeni larg kompjuterit.",
                "Përdorni fjalëkalime të ndryshme për llogari të ndryshme.",
                "Kontrolloni nëse emri i faqes është shkruar saktë.",
                "Mos klikoni reklama Pop-up që thonë se keni virus.",
                "Fjalëkalimet duhet të kenë të paktën 12 karaktere.",
                "Emri i kafshës shtëpiake është fjalëkalim i keq.",
                "HTTPS është i detyrueshëm për blerjet online.", "Biometrika është më e sigurt se PIN-i.",
                "Asnjëherë mos vendosni fjalëkalim në lidhje të dyshimta."
            ],
            3: [
                "Phishing është një mesazh i rremë që kërkon të dhënat tuaja.",
                "Kontrolloni emailin e dërguesit për gabime.",
                "Bankat kurrë nuk kërkojnë fjalëkalime përmes emailit.", "VPN fsheh adresën tuaj IP nga hakerët.",
                "Kujdes nga mesazhet që krijojnë urgjencë të rreme.", "Mos hapni skedarë 'zip' nga njerëz të panjohur.",
                "Phishing mund të ndodhë edhe përmes SMS (Smishing).", "Linqet në emailat Phishing janë të rremë.",
                "Gjithmonë kontrolloni URL-në para se të identifikoheni.",
                "Antivirusi mund të zbulojë disa faqe Phishing.",
                "Asnjëherë mos paguani me kartë në një faqe pa HTTPS.", "Një mik mund të hakohet dhe të dërgojë virus.",
                "Inxhinieria sociale është manipulim për të vjedhur kodet.",
                "Kujdes nga lojërat shpërblyese që kërkojnë të dhëna personale.",
                "Modaliteti privat i shfletuesit nuk ju fsheh nga hakerët.",
                "Spear Phishing është sulm i synuar ndaj një personi specifik.",
                "Asnjëherë mos u përgjigjni mesazheve spam.", "Ruani fotot private në një vend të sigurt.",
                "Kujdes çfarë ndani në rrjetet sociale.", "Kontrolloni lejet e aplikacioneve që instaloni.",
                "Përdorni modalitetin privat në kompjuterët publikë.",
                "Mos i ruani fjalëkalimet në shfletuesit publikë.",
                "Çaktivizoni lidhjen automatike me Wi-Fi.", "Shmangni karikimin e telefonit në porta USB të panjohura.",
                "Kontrolloni deklaratën e privatësisë së aplikacioneve të reja."
            ],
            5: [
                "Backup do të thotë të bësh një kopje të skedarëve tuaj.",
                "Ransomware bllokon skedarët dhe kërkon para.",
                "Malware është çdo softuer që dëmton sistemin.",
                "Cloud Backup është një mënyrë e sigurt për të ruajtur të dhënat.",
                "Menaxheri i fjalëkalimeve mban të gjitha kodet në një vend.",
                "Kali i Trojës pretendon të jetë një program i dobishëm.",
                "Keylogger është një virus që regjistron gjithçka që shkruani.",
                "Gjithmonë skanoni USB-të para përdorimit.",
                "Një Rootkit i jep hakerit kontroll të plotë.",
                "Windows i përditësuar është shumë më i vështirë për t'u hakuar.",
                "Spyware gjurmon atë që bëni në internet.", "Adware ju tregon reklama bezdisshme dhe të rrezikshme.",
                "Krimbi (Worm) përhapet në rrjet pa ndihmën tuaj.",
                "Enkriptimi i bën skedarët të pallexueshëm për hakerët.",
                "Lidhja më e dobët në siguri është njeriu.",
                "Sulmi Zero-day përdor një vrimë që nuk është zbuluar ende.",
                "Firewall filtron trafikun e rrjetit.", "Sulmi DDoS mbingarkon një faqe me trafik.",
                "Botnet është një rrjet kompjuterësh të infektuar nën kontroll.",
                "Sandboxing është mjedis i izoluar për testimin e viruseve.",
                "Nënshkrimi dixhital garanton vërtetësinë e dokumentit.", "Spiunazhi industrial shpesh përdor Malware.",
                "Asnjëherë mos e fikni antivirusin gjatë instalimit.",
                "Routeri duhet të ketë një fjalëkalim të fortë admini.",
                "WPA3 është standardi më i ri dhe më i sigurt i Wi-Fi.",
                "Pajisjet IoT janë objektiva të shpeshta për hakerët.",
                "Gjithmonë dilni (Log out) nga profili pas përdorimit.",
                "Kontrolloni listën e sesioneve aktive në profilin tuaj.",
                "Enkriptoni gjithë hard diskun për mbrojtje maksimale.",
                "Mësoni vazhdimisht për kërcënimet e reja dixhitale."
            ]
        },
        'TR': {
            1: [
                "HTTPS, siz ve site arasındaki verileri şifreler.",
                "Güçlü şifre büyük, küçük harf ve semboller içerir.",
                "2FA ikinci bir güvenlik katmanı ekler (mobil kod).", "Şifrenizi asla yabancılara söylemeyin.",
                "Genel Wi-Fi ağları genellikle şifrelenmez.", "Yazılım güncellemeleri güvenlik açıklarını kapatır.",
                "Bilgisayar başında değilken ekranı kilitleyin.", "Farklı hesaplar için farklı şifreler kullanın.",
                "Site adının doğru yazılıp yazılmadığını kontrol edin.",
                "Virüs var diyen Pop-up reklamlara tıklamayın.",
                "Şifreler en az 12 karakterden oluşmalıdır.", "Evcil hayvan adı kötü bir şifredir.",
                "Online alışveriş için HTTPS zorunludur.", "Biyometrik veriler PIN kodundan daha güvenlidir.",
                "Şüpheli bağlantılara asla şifre girmeyin."
            ],
            3: [
                "Phishing, verilerinizi isteyen sahte bir mesajdır.",
                "Gönderenin e-postasını hatalar için kontrol edin.",
                "Bankalar asla e-posta yoluyla şifre istemez.", "VPN, IP adresinizi hakerlardan gizler.",
                "Sahte aciliyet yaratan mesajlara dikkat edin.",
                "Tanımadığınız kişilerden gelen 'zip' dosyalarını açmayın.",
                "Phishing SMS yoluyla da olabilir (Smishing).", "Phishing e-postalarındaki bağlantılar sahtedir.",
                "Giriş yapmadan önce her zaman URL'yi kontrol edin.",
                "Antivirüs bazı Phishing sitelerini algılayabilir.",
                "HTTPS olmayan bir sitede asla kartla ödeme yapmayın.", "Bir arkadaşınız hacklenip virüs gönderebilir.",
                "Sosyal mühendislik, şifre çalmak için yapılan manipülasyondur.",
                "Kişisel veri isteyen çekilişlere dikkat edin.",
                "Gizli mod sizi hackerlardan gizlemez.", "Spear Phishing belirli bir kişiyi hedef alan saldırıdır.",
                "Spam mesajlara asla cevap vermeyin.", "Özel fotoğraflarınızı güvenli bir yerde saklayın.",
                "Sosyal ağlarda paylaştıklarınıza dikkat edin.", "Yüklediğiniz uygulamaların izinlerini kontrol edin.",
                "Kamuya açık bilgisayarlarda gizli modu kullanın.", "Şifreleri genel tarayıcılara kaydetmeyin.",
                "Otomatik Wi-Fi bağlantısını devre dışı bırakın.",
                "Telefonunuzu tanınmayan USB portlarında şarj etmeyin.",
                "Yeni uygulamaların gizlilik bildirimini kontrol edin."
            ],
            5: [
                "Yedekleme (Backup), dosyalarınızın bir kopyasını almaktır.",
                "Ransomware dosyaları kilitler ve para ister.",
                "Malware, sisteme zarar veren her türlü yazılımdır.",
                "Bulut yedekleme, veri saklamanın güvenli bir yoludur.",
                "Şifre yöneticisi tüm anahtarlarınızı tek bir yerde tutar.",
                "Truva atı faydalı bir program gibi görünür.",
                "Keylogger, yazdığınız her şeyi kaydeden bir virüstür.", "USB bellekleri kullanmadan önce taratın.",
                "Rootkit, bir hacker'a tam kontrol sağlar.", "Güncel bir Windows'u hacklemek çok daha zordur.",
                "Casus yazılım (Spyware) internette ne yaptığınızı izler.",
                "Adware size sinir bozucu ve tehlikeli reklamlar gösterir.",
                "Solucan (Worm) yardımınız olmadan ağda yayılır.", "Şifreleme, dosyaları hackerlar için okunmaz yapar.",
                "Güvenlikteki en zayıf halka insandır.", "Zero-day saldırısı henüz keşfedilmemiş bir açığı kullanır.",
                "Güvenlik duvarı (Firewall) ağ trafiğini filtreler.", "DDoS saldırısı bir siteyi trafikle çökertir.",
                "Botnet, kontrol altındaki enfekte bilgisayar ağıdır.",
                "Sandboxing, virüs testi için izole edilmiş ortamdır.",
                "Dijital imza, belgenin orijinalliğini garanti eder.",
                "Endüstriyel casuslukta sıkça Malware kullanılır.",
                "Kurulum sırasında antivirüsü asla kapatmayın.",
                "Yönlendiricinin (Router) güçlü bir admin şifresi olmalıdır.",
                "WPA3, en yeni   ve en güvenli Wi-Fi standardıdır.", "IoT cihazları hackerlar için sıkça hedeftir.",
                "Kullandıktan sonra profilinizden her zaman çıkış yapın.",
                "Profilinizdeki aktif oturum listesini kontrol edin.",
                "Maksimum koruma için tüm sabit sürücüyü şifreleyin.",
                "Yeni dijital tehditler hakkında sürekli bilgi edinin."
            ]
        }
    }

    knowledge_pool = []
    collected_lessons = []  # Лекции за тековно ниво
    all_lessons = []  # Сите собрани лекции за финалното резиме

    def refresh_knowledge():
        nonlocal knowledge_pool
        lang = configs.language or 'MK'
        lvl = configs.current_level
        # Прво пробај го избраниот јазик
        pool_source = knowledge_by_lang.get(lang, knowledge_by_lang['MK'])

        # Ако листата за тоа ниво е празна, земи ја од MK како резерва
        current_list = pool_source.get(lvl, [])
        if not current_list and lang != 'MK':
            current_list = knowledge_by_lang['MK'].get(lvl, [])

        knowledge_pool = list(current_list)
        random.shuffle(knowledge_pool)

    def init_game():
        p = Player(configs)
        if configs.current_level % 2 != 0 and configs.current_level < 7:
            refresh_knowledge()
        q_sys = QuizSystem(screen, configs)
        q_sys.load_for_level(configs.current_level)
        return p, pygame.sprite.Group(p), pygame.sprite.Group(), pygame.sprite.Group(), \
            pygame.sprite.Group(), q_sys, None

    player, all_sprites, bullets, enemies, drops, quiz, boss = init_game()
    boss_bullets = pygame.sprite.Group()
    configs.boss_active = False
    SPAWN_ENEMY = pygame.USEREVENT + 1
    ENEMY_SPAWN_MS = 1000
    hit_counter = 0
    msg_timer = 0
    knowledge_msg = ""

    while True:
        dt_ms = clock.tick(60)
        #await asyncio.sleep(0)

        # 1. Избор на јазик
        if configs.show_language_selection:
            draw_language_selection(screen, configs)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    keys = {pygame.K_1: 'MK', pygame.K_2: 'EN', pygame.K_3: 'AL', pygame.K_4: 'TR'}
                    if event.key in keys:
                        configs.language = keys[event.key]
                        configs.show_language_selection = False
                        quiz.load_for_level(configs.current_level)
                        refresh_knowledge()
                        pygame.time.set_timer(SPAWN_ENEMY, ENEMY_SPAWN_MS)
            continue

        bg.update(dt_ms)
        bg.draw(screen)
        lang_ref = configs.translations.get(configs.language or 'MK', configs.translations['EN'])

        # 2. Настани
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                configs.reset_game()
                collected_lessons = []
                all_lessons = []
                player, all_sprites, bullets, enemies, drops, quiz, boss = init_game()
                boss_bullets.empty()
                pygame.time.set_timer(SPAWN_ENEMY, ENEMY_SPAWN_MS)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
                pygame.time.set_timer(SPAWN_ENEMY, 0 if paused else ENEMY_SPAWN_MS)

            if not quiz.active and configs.game_active and not paused:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if not configs.show_instructions:
                        b = Bullet(player.rect.centerx, player.rect.top, configs)
                        bullets.add(b)
                        all_sprites.add(b)
                        shoot_sfx.play()
                if event.type == SPAWN_ENEMY and not configs.boss_active:
                    enemies.add(Enemy(configs, random.random() < (0.2 + configs.current_level * 0.05)))

            quiz.handle_event(event)

        if paused:
            # 1. Затемнување на заднината
            ov = pygame.Surface((900, 700), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            screen.blit(ov, (0, 0))

            # 2. Приказ на сите собрани лекции
            draw_knowledge_summary(screen, configs, all_lessons)

            # 3. Важно: По затворање на резимето (преку SPACE внатре во функцијата),
            # автоматски исклучи ја паузата и врати го тајмерот
            paused = False
            if not configs.boss_active:
                pygame.time.set_timer(SPAWN_ENEMY, ENEMY_SPAWN_MS)
            continue

        if configs.show_instructions:
            draw_detailed_level_intro(screen, configs)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    configs.show_instructions = False
            continue

        # 3. Главна Логика
        if configs.game_active:
            if not quiz.active:
                player.update(pygame.key.get_pressed())
                bullets.update()
                enemies.update()
                drops.update()
                boss_bullets.update()


                # --- НИВОА СО СОБИРАЊЕ (1, 3, 5) ---
                if configs.current_level % 2 != 0 and configs.current_level < 7:

                    if pygame.sprite.spritecollide(player, enemies, True):
                        configs.shields -= 1
                        player_hit_sfx.play()
                    for d in pygame.sprite.spritecollide(player, drops, True):
                        if knowledge_pool:
                            txt = d.text
                            knowledge_msg = txt
                            collected_lessons.append(txt)
                            all_lessons.append(txt)
                            msg_timer = 200
                            configs.knowledge_points += 1
                            drop_sfx.play()
                            tts.speak(knowledge_msg)



                    target_k = 5 if configs.current_level == 1 else 10 if configs.current_level == 3 else 15
                    if configs.knowledge_points >= target_k:
                        draw_knowledge_summary(screen, configs, collected_lessons)
                        configs.next_level()
                        bg.load_for_level(configs.current_level)
                        configs.knowledge_points = 0
                        configs.show_instructions = True
                        knowledge_msg = ""
                        collected_lessons = []
                        player, all_sprites, bullets, enemies, drops, quiz, boss = init_game()
                        quiz.load_for_level(configs.current_level)

                # --- БОС НИВОА (2, 4, 6, 7) ---
                else:
                    if not configs.boss_active:

                        if configs.current_level == 7:
                            draw_knowledge_summary(screen, configs, all_lessons)

                        configs.boss_active = True
                        boss = Boss(configs, configs.current_level)

                    if boss:
                        boss.update(player.rect.centerx)
                        current_time = pygame.time.get_ticks()

                        if current_time - boss.last_shot_time > boss.shoot_interval:
                            boss.last_shot_time = current_time
                            # choose attack based on boss level
                            if configs.current_level == 2:
                                attack_type = "aimed"
                            elif configs.current_level == 4:
                                attack_type = "fast"
                            elif configs.current_level == 6:
                                attack_type = "zigzag"
                            elif configs.current_level == 7:
                                attack_type = random.choice(["fast", "zigzag"])
                            else:
                                attack_type = "aimed"

                            bullet = BossBullet(
                                boss.rect.centerx,
                                boss.rect.bottom,
                                player.rect.centerx,
                                player.rect.centery,
                                attack_type
                            )
                            boss_bullets.add(bullet)
                            shoot_sfx.play()

                        if getattr(configs, "pending_boss_damage", 0) > 0:
                            boss.current_hp -= configs.pending_boss_damage
                            configs.pending_boss_damage = 0

                        if pygame.sprite.spritecollide(boss, bullets, True):
                            # Ако е ниво 7, куршумите само го активираат квизот, но не го убиваат босот
                            if configs.current_level == 7:
                                if boss.current_hp > 500:
                                    pass
                            else:
                                if boss.current_hp > 10: boss.current_hp -= 2  # Стандардна штета за нивоа 2, 4, 6

                            hit_counter += 1
                            if hit_counter >= 5:
                                hit_counter = 0
                                quiz.trigger_random()

                        if pygame.sprite.spritecollide(player, boss_bullets, True):
                            configs.shields -= 1
                            player_hit_sfx.play()

                        # Проверка за победа на квизот
                        limit = 30 if configs.current_level == 7 else 15 if configs.current_level == 6 else 10 if configs.current_level == 4 else 5
                        if quiz.correct_answers_count >= limit: boss.current_hp = 0

                        if boss.current_hp <= 0:
                            if configs.current_level >= 7:
                                configs.victory = True
                                configs.game_active = False
                            else:
                                draw_level_complete(screen, configs)
                                pygame.display.flip()
                                pygame.time.wait(2000)
                                configs.next_level()
                                bg.load_for_level(configs.current_level)
                                configs.show_instructions = True
                                knowledge_msg = ""

                                player, all_sprites, bullets, enemies, drops, quiz, boss = init_game()
                                quiz.load_for_level(configs.current_level)

                # --- УНИШТУВАЊЕ НЕПРИЈАТЕЛИ & БОНУС ЖИВОТ ---
                for b in bullets:
                    hits = pygame.sprite.spritecollide(b, enemies, False)
                    for e in hits:
                        e.hp -= 1
                        b.kill()
                        if e.hp <= 0:
                            enemy_die_sfx.play()
                            if e.is_special and configs.current_level % 2 != 0:
                                drop = KnowledgeDrop(e.rect.centerx, e.rect.centery, knowledge_pool)
                                drops.add(drop)
                                all_sprites.add(drop)
                                configs.score += 30

                            else:
                                configs.score += 10

                            if configs.score // 250 > configs.last_life_score // 250:
                                extra_life_sfx.play()
                                configs.shields += 1
                                configs.last_life_score = (configs.score // 250) * 250
                                knowledge_msg = "BONUS: +1 LIFE!"
                                msg_timer = 150
                            e.kill()

            # 4. Цртање
            all_sprites.draw(screen)
            enemies.draw(screen)
            drops.draw(screen)
            boss_bullets.draw(screen)
            if boss: boss.draw(screen)

            if boss or configs.current_level == 7:
                hud_txt = lang_ref['hud_boss'].format(configs.current_level, configs.shields, configs.score)
            else:
                target_val = 5 if configs.current_level == 1 else 10 if configs.current_level == 3 else 15
                hud_txt = lang_ref['hud'].format(configs.current_level, configs.shields, configs.score,
                                                 f"{configs.knowledge_points}/{target_val}")

            screen.blit(f_hud.render(hud_txt, True, (255, 255, 255)), (20, 20))
            if msg_timer > 0:
                txt_s = f_hud.render(knowledge_msg, True, (255, 215, 0))
                screen.blit(txt_s, (450 - txt_s.get_width() // 2, 610))
                msg_timer -= 1

            quiz.draw()
            if configs.shields <= 0: configs.game_active = False
        else:
            if configs.victory:
                # 1. Прикажи го екранот со честитки и земи го изборот на играчот
                choice = draw_victory_congratulations(screen, configs)

                if choice == "SHOW_SKILLS":
                    # 2. Ако притиснал SPACE, прикажи ги вештините (all_lessons)
                    draw_victory_screen(screen, configs, all_lessons)
                    pygame.quit()
                    sys.exit()
                elif choice == "RESTART":
                    # 3. Рестартирај ја играта
                    configs.reset_game()
                    all_lessons = []
                    collected_lessons = []
                    player, all_sprites, bullets, enemies, drops, quiz, boss = init_game()
                else:
                    # 4. Излези од играта
                    pygame.quit()
                    sys.exit()
            else:
                # Game Over логика
                ov = pygame.Surface((900, 700), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 220))
                screen.blit(ov, (0, 0))
                screen.blit(f_hud.render(lang_ref['game_over'], True, (255, 255, 255)), (150, 350))
        pygame.display.flip()


if __name__ == "__main__":
    main()
