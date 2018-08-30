#-*- coding: utf-8 -*-
import time
import datetime

# Возвращает время, за которое была выполнениа функция
def timer(func):
	def wrapper():
		global t1
		t1 = time.time()
		global start_time
		start_time = datetime.datetime.now().strftime('%H:%M:%S') # На всякий случай берет текущую дату. Не используется
		res = func()
		time_over = time.time() - t1
		return time_over
	return wrapper