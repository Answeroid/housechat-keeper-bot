help_msg = ''' 
Щоб переглянути список сусідів:

<b>по обраному будинку</b>
Тисни:
<code>Дивитись сусідів 👫 ➡ Будинок ➡ Показати всіх в цьому будинку 🏠</code>\n

<b>по обраному під\'їзду</b>
Тисни:
<code>Дивитись сусідів 👫 ➡ Будинок ➡ Під\'їзд</code>\n

<b>по своєму будинку</b>
Тисни: <code>'Мій будинок 🏠'</code>

<b>по своєму під\'їзду</b>
Тисни: <code>'Мій під\'їзд 🔢'</code>

Щоб додати або змінити свої дані:

Тисни: <code>Змінити свої дані ✏</code>,
і вибери свої <i>будинок, під\'їзд, поверх, квартиру</i>\n

Виключні ситуації:
Якщо бажаєте додати більше однієї квартири, напишіть про це <a href="tg://user?id=422485737">сюди</a>
'''

about_msg = '''
Привіт!

Я бот, який допомогає формувати список мешканців ЖК Перемога. Його можна переглянути та зв'язатися зі своїм сусідом.

Службові команди:
/start - головне меню
/help - опис функціоналу
/about - про бота

З пропозиціями та зауваженнями звертайтесь <a href="tg://user?id=422485737">сюди</a>.
'''

building_msg = '''
💠 Почтовый индекс и полный адрес

61174, Пр. Победы д. 85/87/89

💠 Комендант 

Светлана Юрьевна
☎ +38057-764-81-47
График работы: ПН-ПТ 8.30-16.00
Перерыв: 12:00-13:00
Находится на первом этаже 4-го подъезда 89-го дома

💠 Почта

УкрПочта отделение №174 - пр. Победы, 75а
Нова Почта №53 (до 30 кг) - пр. Победы, 65г (ост. Школьная)
МистЭкспресс - пр. Победы 70а (ост. Солнечная)

💠 ЖЭК ЖС-1

📞 +38057-338-30-67
ул. Целиноградская, 42
Прием граждан: ПН, ЧТ 13:00-17:00

💠 Аварийная горлифта

☎ +38067-542-60-21

💠 Интернет-провайдеры/кабельное ТВ

👉 <a href="https://maxnet.ua/">Макснет</a>
👉 <a href="https://www.untc.ua/">UNTC</a>

💠 Поликлиники

💉 14 детская - пр. Людвіга Свободи, 48-В, 
☎ +38057 725-03-99
☎ +38057 725-03-85

💉 <a href="http://8pol.city.kharkov.ua/">8 поликлиника</a> - пр. Победы, 53, 
☎ +38057 725-11-40
☎ +38057 725-11-41
 
💉 <a href="https://cab.mcplus.com.ua/">Вызов врача на дом или запись на прием</a>

💠 Мы на карте

👉 <a href="https://www.google.com/maps/place/%D0%BF%D1%80%D0%BE%D1%81%D0%BF.+%D0%9F%D0%BE%D0%B1%D0%B5%D0%B4%D1%8B,+85,+%D0%A5%D0%B0%D1%80%D1%8C%D0%BA%D0%BE%D0%B2,+%D0%A5%D0%B0%D1%80%D1%8C%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B0%D1%8F+%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D1%8C,+61000/@50.0704593,36.2092955,17z/data=!3m1!4b1!4m5!3m4!1s0x4127a43aea3b016f:0xbdcdffe331b57988!8m2!3d50.0704593!4d36.2114842">Гугл</a>
👉 <a href="https://2gis.ua/kharkov/geo/15481759374266615?queryState=center%2F36.211313%2C50.070421%2Fzoom%2F17">2Гис</a>
'''

greeting_msg = '''
Вітаю {}! Давайте знайомитись,
додайтесь до списку сусідів в @peremogy_susid_bot.
'''

house_85 = {
    'section_1': [i for i in range(1, 10)] + ['8-9'],
    'section_2': [i for i in range(1, 10)] + ['8-9'],
    'section_3': [i for i in range(1, 10)] + ['8-9'],
    'section_4': [i for i in range(1, 10)] + ['8-9'],
    'section_5': [i for i in range(1, 10)] + ['8-9'],
    'section_6': [i for i in range(1, 10)] + ['8-9'],
}

house_87 = {
    'section_1': [i for i in range(1, 10)] + ['8-9'],
    'section_2': [i for i in range(1, 10)] + ['8-9'],
}

house_89 = {
    'section_1': [i for i in range(1, 10)] + ['8-9'],
    'section_2': [i for i in range(1, 10)] + ['8-9'],
    'section_3': [i for i in range(1, 10)] + ['8-9'],
    'section_4': [i for i in range(1, 10)] + ['8-9'],
    'section_5': [i for i in range(1, 10)] + ['8-9'],
    'section_6': [i for i in range(1, 10)] + ['8-9'],
}

houses_arr = {
    'house_85': house_85,
    'house_87': house_87,
    'house_89': house_89,
}