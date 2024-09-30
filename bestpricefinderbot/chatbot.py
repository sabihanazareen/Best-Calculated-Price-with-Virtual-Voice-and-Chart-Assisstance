from bs4 import BeautifulSoup
import requests
import time
import string
import random

from flask import Flask, render_template,session
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from flask import request
from flask import render_template
from flask import flash
from flask import jsonify

app = Flask(__name__)

english_bot = ChatBot("bot")
english_bot.set_trainer(ChatterBotCorpusTrainer)
english_bot.train("chatterbot.corpus.english")
english_bot.train('chatterbot.corpus.english.greetings')
english_bot.train('chatterbot.corpus.english.conversations')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# for sessions
app.secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 7))

@app.route("/")
def home1():

    return render_template("get.html")

@app.route("/ask", methods=['POST'])
def ask():

	count=0

	if 'count' in session:
		count = session['count']

	print("count \t",0)

	if count==0:
		print("counter:0")
		session['count']=1
		return jsonify({'status': 'OK', 'answer':"please speak Product Name"})

	if count==1:
		print("counter:1")
		session['count']=session['count']+1
		product = (request.form['messageText'])
		session['product'] = product
		return jsonify({'status': 'OK', 'answer':"please speak Seller Names"})

	if count==2:

		def flipkart_scrap(name):
			try:
				name1 = name.replace(" ", "+")
				flipkart_url = f'https://www.flipkart.com/search?q={name1}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=off&as=off'
				res = requests.get(flipkart_url, headers=headers)
				soup = BeautifulSoup(res.text, 'html.parser')
				flipkart_name = soup.select('._4rR01T')[0].getText().strip()
				flipkart_name = flipkart_name.upper()
				if name.upper() in flipkart_name:
					flipkart_price = soup.select('._1_WHN1')[0].getText().strip()
				else:
					flipkart_price = '0'
				return flipkart_price, flipkart_url
			except:
				flipkart_price = '0'
			return flipkart_price, flipkart_url

		def amazon_scrap(name):
			try:
				name1 = name.replace(" ", "-")
				name2 = name.replace(" ", "+")
				amazon_url = f'https://www.amazon.in/{name1}/s?k={name2}'
				res = requests.get(amazon_url, headers=headers)
				soup = BeautifulSoup(res.text, 'html.parser')
				amazon_page = soup.select('.a-color-base.a-text-normal')
				amazon_page_length = int(len(amazon_page))
				for i in range(0, amazon_page_length):
					name = name.upper()
					amazon_name = soup.select('.a-color-base.a-text-normal')[i].getText().strip().upper()
					if name in amazon_name[0:20]:
						amazon_price = soup.select('.a-price-whole')[i].getText().strip().upper()
						break
					else:
						i += 1
						i = int(i)
						if i == amazon_page_length:
							amazon_price = '0'
							break
				return amazon_price, amazon_url
			except:
				amazon_price = '0'
			return amazon_price, amazon_url

		def olx_scrap(name):
			try:
				name1 = name.replace(" ", "-")
				olx_url = f'https://www.olx.in/items/q-{name1}?isSearchCall=true'
				res = requests.get(olx_url, headers=headers)
				soup = BeautifulSoup(res.text, 'html.parser')
				olx_name = soup.select('._2tW1I')
				olx_page_length = len(olx_name)
				for i in range(0, olx_page_length):
					olx_name = soup.select('._2tW1I')[i].getText().strip()
					name = name.upper()
					olx_name = olx_name.upper()
					if name in olx_name:
						olx_price = soup.select('._89yzn')[i].getText().strip()
						break
					else:
						i += 1
						i = int(i)
						if i == olx_page_length:
							olx_price = '0'
							break
				return olx_price, olx_url
			except:
				olx_price = '0'
			return olx_price, olx_url

		def convert(a):
			b = a.replace(" ", '')
			c = b.replace("INR", '')
			d = c.replace(",", '')
			f = d.replace("₹", '')
			g = int(float(f))
			return g

		name = session['product']

		flipkart_price, flipkart_url = flipkart_scrap(name)
		amazon_price, amazon_url = amazon_scrap(name)
		olx_price, olx_url = olx_scrap(name)

		if flipkart_price == '0':
			flipkart_price = int(flipkart_price)
		else:
			flipkart_price = convert(flipkart_price)

		if amazon_price == '0':
			amazon_price = int(amazon_price)
		else:
			amazon_price = convert(amazon_price)

		if olx_price == '0':
			olx_price = int(olx_price)
		else:
			olx_price = convert(olx_price)

		time.sleep(2)

		lst = [flipkart_price, amazon_price, olx_price]

		lst2 = []
		for j in range(0, len(lst)):
			if lst[j] > 0:
				lst2.append(lst[j])

		if len(lst2) == 0:
			session.pop('count', None)
			session.pop('product', None)
			return jsonify({'status': 'OK', 'answer': "No relative product find in all websites...."})
		else:

			message = (request.form['messageText'])
			sellers = message.split()

			result = ""

			print("Sellers \t", sellers)
			print("Product \t", name)

			if "amazon".upper() in (seller.upper() for seller in sellers):
				print("amazon result", amazon_price)
				result = result + str(" amazon price : {0}".format(amazon_price))
			if "olx".upper() in (seller.upper() for seller in sellers):
				print("olx result", olx_price)
				result = result + str(" olx price : {0}".format(olx_price))
			if "flipkart".upper() in (seller.upper() for seller in sellers):
				print("flipkart result", flipkart_price)
				result = result + str(" flipkart price : {0}".format(flipkart_price))

			print(result)
			session.pop('count', None)
			session.pop('product', None)
			return jsonify({'status': 'OK', 'answer': result})

if __name__ == "__main__":
    app.run()