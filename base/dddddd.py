


# формируем объекты с источниками (добавляем источники если нужно)
try:
    source_kinoinfo = Source.objects.get(name='Kinoinfo')
except:
    source_kinoinfo = Source.objects.create(name='Kinoinfo', status=1, top=1)

try:
    source_kinoafisha = Source.objects.get(name='Kinoafisha')
except:
    source_kinoafisha = Source.objects.create(name='Kinoafisha', url='http://www.kinoafisha.ru/', url_template='?status=1&id1=', status=1, top=0)

try:
    source_rutracker = Source.objects.get(name='Rutracker')
except:
    source_rutracker = Source.objects.create(name='Rutracker', url='http://rutracker.org/', url_template='forum/viewtopic.php?t=', status=1, top=0)

try:
    source_imdb = Source.objects.get(name='IMdb')
except:
    source_imdb = Source.objects.create(name='IMdb', url='http://www.imdb.com/', url_template='title/tt', status=1, top=0)

try:
    lang_ru = Language.objects.get(name='Русский')
except:
    lang_ru = Language.objects.create(name='Русский')

try:
    lang_en = Language.objects.get(name='English')
except:
    lang_en = Language.objects.create(name='English')


