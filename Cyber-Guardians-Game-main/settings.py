import pygame
import sys, os

class GameSettings:
    def __init__(self):
        self.screen_width = 900
        self.screen_height = 700
        self.language = None 
        self.show_language_selection = True
        self.reset_game()

    def reset_game(self):
        self.player_speed = 6
        self.bullet_speed = -8
        self.enemy_speed = 1.0
        self.score = 0
        self.last_life_score = 0 
        self.knowledge_points = 0
        self.shields = 3
        self.current_level = 1
        self.game_active = True
        self.show_instructions = True
        self.boss_active = False
        self.victory = False
        self.font_path = "assets/PressStart2P-Regular.ttf"
        self.bg_color = (10, 10, 30)
        self.pending_boss_damage = 0
        
        self.translations = {
            'MK': {
                'hud': "НИВО: {} | ЖИВОТИ: {} | ПОЕНИ: {} | ЗНАЕЊЕ: {}",
                'hud_boss': "НИВО: {} | ЖИВОТИ: {} | ПОЕНИ: {}",
                'start': "ПРИТИСНИ SPACE ЗА СТАРТ",
                'game_over': "ИЗГУБИ? УЧИ ОД ГРЕШКИТЕ! ПРИТИСНИ 'R'!",
                'victory_msg': "ТИ СИ САЈБЕР ХЕРОЈ! СИСТЕМОТ Е БЕЗБЕДЕН!",
                'level_up': "НИВО {} ЗАВРШЕНО! ОДИМЕ ПОНАТАМУ!",
                'press_space': "Притисни SPACE за продолжување",
                'boss_title': "ГЛАВНИОТ ВИРУС НАПАЃА!",
                'boss_desc': ["Погоди го 5 пати за квиз.", "Одговори точно за да го победиш.", "Грешка = губиш живот!"],
                'level_titles': {
                    1: "НИВО 1: ПРВА ЛИНИЈА НА ОДБРАНА", 2: "НИВО 2: ЧУВАРОТ НА ПОРТАТА (БОС)",
                    3: "НИВО 3: ДИГИТАЛНА ЗАМКА", 4: "НИВО 4: ФИШИНГ ПРЕДАТОР (БОС)",
                    5: "НИВО 5: КРАЈНА ЗАШТИТА", 6: "НИВО 6: ГИГАНТСКИ МАЛВЕР (БОС)",
                    7: "НИВО 7: КРАЈНАТА ПРЕСМЕТКА (ФИНАЛЕ)" # Ново ниво
                },
                'level_desc': {
                    1: ["Добредојде, млади Сајбер Чувар!", "Собери 5 токени за знаење.", "БОНУС: На секои 250 поени добиваш +1 живот!", "За собраните знаења притисни 'P'"],
                    2: ["ВНИМАНИЕ! Првиот голем вирус!", "Погоди го 5 пати за квиз.", "Одговори точно на 5 прашања.", "Секоја грешка чини еден живот!", "Пази се од нивните напади!"],
                    3: ["Одлично! Системот станува побрз.", "Собери 10 знаења за VPN и линкови.", "Вирусите сега напаѓаат во групи."],
                    4: ["Фишинг Предаторот сака да те измами!", "Користи го знаењето од Ниво 3.", "10 точни одговори го чистат вирусот."],
                    5: ["Последна фаза на учење!", "Научи за Backup и Ransomware.", "Собери ги последните 15 знаења."],
                    6: ["ВНИМАНИЕ! Гигантскиот Малвер напаѓа!", "Требаат 15 точни одговори за победа.", "Биди многу внимателен!"],
                    7: ["ОВА Е ФИНАЛНАТА БИТКА!", "Најголемиот вирус ги користи сите моќи.", "Одговори на 30 прашања за крајна победа.", "Среќно, Сајбер Хероју!"]
                }
            },
            'EN': {
                'hud': "LEVEL: {} | LIVES: {} | POINTS: {} | KNOWLEDGE: {}",
                'hud_boss': "LEVEL: {} | LIVES: {} | POINTS: {}",
                'start': "PRESS SPACE TO START",
                'game_over': "LOST? LEARN FROM MISTAKES! PRESS 'R'!",
                'victory_msg': "YOU ARE A CYBER HERO! SYSTEM SECURED!",
                'level_up': "LEVEL {} COMPLETED! MOVING ON!",
                'press_space': "Press SPACE to continue",
                'boss_title': "THE MAIN VIRUS ATTACKS!",
                'boss_desc': ["Hit it 5 times for a quiz.", "Answer correctly to win.", "Mistake = lose a life!"],
                'level_titles': {
                    1: "LEVEL 1: FIRST LINE OF DEFENSE", 2: "LEVEL 2: GATE KEEPER (BOSS)",
                    3: "LEVEL 3: DIGITAL TRAP", 4: "LEVEL 4: PHISHING PREDATOR (BOSS)",
                    5: "LEVEL 5: ULTIMATE DEFENSE", 6: "LEVEL 6: GIANT MALWARE (BOSS)",
                    7: "LEVEL 7: THE FINAL SHOWDOWN (FINALE)"
                },
                'level_desc': {
                    1: ["Welcome, young Cyber Guardian!", "Collect 5 knowledge tokens.", "BONUS: Every 250 points gives you +1 life!", "Press 'P' to see collected knowledge."],
                    2: ["WARNING! The first big virus!", "Hit him 5 times for a quiz.", "Answer 5 questions correctly.", "Every mistake costs one life!"],
                    3: ["Great! The system is getting faster.", "Collect 10 tokens for VPN and links.", "Viruses are attacking in swarms."],
                    4: ["The Phishing Predator is here!", "Use knowledge from Level 3.", "10 correct answers will clear the virus."],
                    5: ["Final learning phase!", "Learn about Backup and Ransomware.", "Collect the last 15 tokens."],
                    6: ["WARNING! Giant Malware attacks!", "15 correct answers needed to win.", "Be very careful!"],
                    7: ["THIS IS THE FINAL BATTLE!", "The Ultimate Virus uses all its powers.", "Answer 30 questions for total victory.", "Good luck, Cyber Hero!"]
                }
            },
            'AL': {
                'hud': "NIVELI: {} | JETËT: {} | PIKËT: {} | NJOHURITË: {}",
                'hud_boss': "NIVELI: {} | JETËT: {} | PIKËT: {}",
                'start': "SHTYP SPACE PËR FILLIM",
                'game_over': "HUMBË? MËSO NGA GABIMET! SHTYP 'R'!",
                'victory_msg': "JE NJË HERO KIBERNETIK! SISTEMI I SIGURT!",
                'level_up': "NIVELI {} U KALUA! VAZHDOJMË!",
                'press_space': "Shtyp SPACE për të vazhduar",
                'boss_title': "SULMI I VIRUSIT KRYESOR!",
                'boss_desc': ["Gjuaj 5 herë për kuiz.", "Përgjigju saktë për fitore.", "Gabimi = humb jetë!"],
                'level_titles': {
                    1: "NIVELI 1: LINJA E PARË E MBROJTJES", 2: "NIVELI 2: ROJA E PORTËS (BOSS)",
                    3: "NIVELI 3: KURTHI DIGJITAL", 4: "NIVELI 4: PREDATORI PHISHING (BOSS)",
                    5: "NIVELI 5: MBROJTJA E FUNDIT", 6: "NIVELI 6: MALWARE GJIGANT (BOSS)",
                    7: "NIVELI 7: BALLAFAQIMI FINAL (FINALE)"
                },
                'level_desc': {
                    1: ["Mirësevini, Mbrojtës i ri Kibernetik!", "Mblidhni 5 argumente njohurish.", "BONUS: Çdo 250 pikë ju jep +1 jetë!", "Shtypni 'P' për të parë njohuritë."],
                    2: ["KUJDES! Virusi i parë i madh!", "Gjuaj 5 herë për kuiz.", "Përgjigju saktë në 5 pyetje.", "Çdo gabim ju kushton një jetë!"],
                    3: ["Shkëlqyeshëm! Sistemi po shpejtohet.", "Mblidhni 10 njohuri për VPN.", "Viruset sulmojnë në grupe."],
                    4: ["Predatori Phishing dëshiron t'ju mashtrojë!", "Përdorni njohuritë nga Niveli 3.", "10 përgjigje të sakta fshijnë virusin."],
                    5: ["Faza përfundimtare e mësimit!", "Mësoni për Backup dhe Ransomware.", "Mblidhni 15 njohuritë e fundit."],
                    6: ["KUJDES! Malware Gjigant sulmon!", "Duhen 15 përgjigje të sakta për fitore.", "Tregoni kujdes të shtuar!"],
                    7: ["KJO ËSHTË BETEJA FINALE!", "Virusi i fundit përdor të gjitha fuqitë.", "Përgjigju 30 pyetjeve për fitore totale.", "Suksese, Hero Kibernetik!"]
                }
            },
            'TR': {
                'hud': "SEVİYE: {} | CAN: {} | PUANLAR: {} | BİLGİ: {}",
                'hud_boss': "SEVİYE: {} | CAN: {} | PUANLAR: {}",
                'start': "BAŞLAMAK İÇİN SPACE'E BASIN",
                'game_over': "KAYBETTİN Mİ? HATALARDAN ÖĞREN! 'R'YE BAS!",
                'victory_msg': "SİBER KAHRAMANSIN! SİSTEM GÜVENLİ!",
                'level_up': "SEVİYE {} TAMAMLANDI! DEVAM ET!",
                'press_space': "Devam etmek için SPACE'e basın",
                'boss_title': "ANA VİRÜS SALDIRIYOR!",
                'boss_desc': ["Test için 5 kez vur.", "Kazanmak için doğru cevapla.", "Hata = can kaybı!"],
                'level_titles': {
                    1: "SEVİYE 1: İLK SAVUNMA HATTI", 2: "SEVİYE 2: KAPI KORUYUCUSU (BOSS)",
                    3: "SEVİYE 3: DİJİTAL TUZAK", 4: "SEVİYE 4: PHISHING AVCI (BOSS)",
                    5: "SEVİYE 5: NİHAİ KORUMA", 6: "SEVİYE 6: DEV MALWARE (BOSS)",
                    7: "SEVİYE 7: FİNAL HESAPLAŞMASI (FİNAL)"
                },
                'level_desc': {
                    1: ["Hoş geldin, genç Siber Koruyucu!", "5 bilgi tokeni topla.", "BONUS: Her 250 puan size +1 can verir!", "Bilgileri görmek için 'P' tuşuna basın."],
                    2: ["DİKKAT! İlk büyük virüs!", "Test için 5 kez vur.", "5 soruyu doğru cevapla.", "Her hata bir cana mal olur!"],
                    3: ["Harika! Sistem hızlanıyor.", "VPN için 10 bilgi topla.", "Virüsler sürüler halinde saldırıyor."],
                    4: ["Phishing Avcısı sizi kandırmaya çalışıyor!", "Seviye 3 bilgilerini kullan.", "10 doğru cevap virüsü temizler."],
                    5: ["Son öğrenme aşaması!", "Yedekleme ve Ransomware öğren.", "Son 15 bilgiyi topla."],
                    6: ["DİKKAT! Dev Malware saldırıyor!", "Kazanmak için 15 doğru cevap gerekli.", "Çok dikkatli olun!"],
                    7: ["BU FİNAL SAVAŞI!", "En büyük virüs tüm gücünü kullanıyor.", "Kesin zafer için 30 soruyu cevapla.", "Başarılar, Siber Kahraman!"]
                }
            }
        }

    def next_level(self):
        self.current_level += 1
        self.enemy_speed += 0.8
        self.player_speed += 0.5
        self.boss_active = False
