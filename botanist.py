#!/usr/bin/env python
# -*- coding: utf8 -*-
# coding: utf8

import irclib
import ircbot
import random
import os
import pickle
import string
import time
import datetime
import unicodedata
from threading import Timer
from datetime import datetime
from pytz import timezone

def remove_accents(input_str):
	nfkd_form = unicodedata.normalize('NFKD', input_str)
	only_ascii = nfkd_form.encode('ASCII', 'ignore')
	return only_ascii

def is_last_voyel(voyel, input_str):
	for cur_char in reversed(input_str):
		if cur_char in ('a', 'e', 'i', 'o', 'u', 'y'):
			if cur_char == voyel:
				return True
			else:
				return False
	return False

def is_a_voyel(input_str):
	if input_str[-1:] in ('a', 'e', 'i', 'o', 'u', 'y'):
		return True
	return False

def get_vowel():
	a = ""
	while not is_a_voyel(a.lower()):
		a = random.choice(string.ascii_uppercase)	# nice code
	return a

def get_consonant():
	a = ""
	while a == "" or is_a_voyel(a.lower()):
		a = random.choice(string.ascii_uppercase)
	return a



class Bot(ircbot.SingleServerIRCBot):
	chan = "#contreloutre"
	name = "lutralutra"
	master = "zoologist"
	money = "pokétunes".decode("utf8")
	cpt_last_message = 0
	last_message = ""
	last_user = ""
	insults = open('insults.txt').read().splitlines()
	users = []
	players = []
	players_ez = []
	stats ={}
	jokes ={}
	total_msg = 0
	vf_global_mode = False
	vf_q_mode = False
	vf_n_mode = False
	vf_w_mode = False
	vf_ez_mode = False
	vf_ez_ans_mode = False
	vf_answer = ""
	vf_question = ""
	vf_winner = ""
	vf_rq_cpt = 0
	vf_rq_need = 0
	vf_rq_time = 0
	VF_RQ_TIMELAPSE = 5
	items = {'slap': 1, 'kick': 50}
	users_items = {}
  	forbiden_words = []
	dcdl_mode = 0	# 0: not playing, 1: selection, 2: reflection time, 3: answer time
	dcdl_dict = open('frdict.txt').read().splitlines()
	dcdl_tirage = ""
	dcdl_answers = {}
	dcdl_points = {}



	def dcdl_isValidAnswer(self,tirage,ans):
	    s_tirage = list(tirage)
	    s_ans = list(ans)
	    s_tirage.sort()
	    s_ans.sort()
	    pos1 = 0
	    pos2 = 0
	    while pos2 < len(s_ans) and pos1 < len(s_tirage):
	      if s_tirage[pos1] == s_ans[pos2]:
	        pos1 = pos1 + 1		# OK, next letter
	        pos2 = pos2 + 1
	      else:
	        pos1 = pos1 + 1
	    if pos2 < len(s_ans):
	        return 1  # == apprends à jouer
	    # look in dictionary
	    if ans.lower() in self.dcdl_dict:
	      return 0 
	    return 2 # == apprends le francais

	def dcdl_fini(self, serv):
		serv.privmsg(self.chan, "** Fini! **")
		winners = {}
		points = 0
		for player, ans in self.dcdl_answers.iteritems():
			res = self.dcdl_isValidAnswer(self.dcdl_tirage, ans.upper())
			if res == 1:
				serv.privmsg(self.chan, u"Apprends à jouer, " + player)
			elif res == 2:
				if random.random() < 0.9:
					serv.privmsg(self.chan, "'" + ans + "', ce n'est pas un mot " + player)
				else:
					serv.privmsg(self.chan, "Eh non " + player + ", c'est intransitif!")
			else:
				if len(ans) > points:
					winners = [player]
					points = len(ans)
				elif len(ans) == points:
					winners.append(player)
		serv.privmsg(self.chan, "Gagnant-e-(s): ")
		for winner in winners:
			if winner in self.dcdl_points:
				self.dcdl_points[winner] += points
			else:
				self.dcdl_points[winner] = points
			serv.privmsg(self.chan, winner + ", + " + str(points) + " points ("+str(self.dcdl_points[winner])+" points)")
		# check for end-of-game
		final_winner = ""
		final_winner_points = 20
		for player, points in self.dcdl_points.iteritems():
			if points > final_winner_points:
				final_winner_points = points
				final_winner = player
			elif points == final_winner_points and final_winner != "":
				# woops, two winners, reset
				final_winner = ""
		if final_winner != "":
			serv.privmsg(self.chan, "** Gagnant: " + player + " avec " + str(points) + " points")
			serv.privmsg(self.chan, "!togglecollect")
				
			# reset
			self.dcdl_tirage = ""
			self.dcdl_answers = {}
			self.dcdl_points = {}
			self.dcdl_mode = 0
		else:
			# restart
			self.dcdl_begin(serv)

	def dcdl_begin(self, serv):
		self.dcdl_mode = 1
		self.dcdl_tirage = ""
		self.dcdl_answers = {}
		serv.privmsg(self.chan, u"C'est à vous! voyelle ou consonne")

	def dcdl_get_answers(self, serv):
		serv.privmsg(self.chan, u"** Vos réponses (vous avez 5 secondes): **")
		self.dcdl_mode = 3
		Timer(5, self.dcdl_fini, (serv,)).start()

	def start_vf(self, serv):
		if len(self.players) > 1:
			self.vf_global_mode = True
			serv.privmsg(self.chan, "!togglecollect")
			serv.privmsg(self.chan, "Debut de la partie! ("+", ".join(self.players)+")")
			self.vf_rq_need = len(self.players)
			time.sleep(2)
			self.vf_w_mode = False
			self.vf_q_mode = True
			self.say_question(serv)
		elif len(self.players) == 1:
			serv.privmsg(self.chan, "Lol y a personne pour jouer avec toi "+self.players[0]+".")
			serv.mode(self.chan, "-v "+self.players[0])
			self.players = []
		self.vf_w_mode = False

	def add_player(self, user, serv):
		if user not in self.players:
			print "+v "+user
			self.players.append(user)
			serv.mode(self.chan, "+v "+user)
		else:
			serv.privmsg(self.chan, ("T'es déjà dans la liste "+user).decode("utf8"))

	def say_question(self, serv):
		self.vf_rq_cpt = 0
		print "Question! "+str(self.vf_w_mode) + str(self.vf_q_mode) + str(self.vf_n_mode)
		randf = random.choice(os.listdir("questions/"))
		f = open("questions/"+randf, 'r').read().splitlines()
		line = random.choice(f).decode("utf-8")
		self.vf_question = line.split("|")[0]
		self.vf_answer = line.split("|")[1]
		serv.privmsg(self.chan, "** "+self.vf_question)
		self.vf_rq_time = time.time()
		print self.players

	def vf_victory(self, serv):
		serv.privmsg(self.chan, "GG "+self.players[0]+". Voila tes " + str(self.vf_rq_need-1) + " " + self.money+". Partie terminée :)".decode("utf8"))
		self.jokes[self.players[0]] = self.jokes[self.players[0]] + self.vf_rq_need-1
		with open('jokes.txt', 'w') as f:
			pickle.dump(self.jokes, f, 0)
		serv.mode(self.chan, "-v "+self.players[0])
		self.players = []
		self.question = ""
		serv.privmsg(self.chan, "!togglecollect")
		self.vf_global_mode = False

	def __init__(self):
		#Load shit
		if os.path.isfile('stats.txt'):
			with open('stats.txt', 'r') as f:
				self.stats = pickle.load(f)
			self.total_msg = sum(self.stats.values())
		if os.path.isfile('jokes.txt'):
			with open('jokes.txt', 'r') as f:
				self.jokes = pickle.load(f)

		print "Connecting.."
		ircbot.SingleServerIRCBot.__init__(self, [("irc.freenode.com", 6667, "iamabot!")],
				"bemugbot", "J'aime les loutres et les cornichons")
	def on_welcome(self, serv, ev):
		print "Connected!"
		serv.nick(self.name)
		print "Joining channel.."
		serv.join(self.chan)
	def on_endofnames(self, serv, ev):
		Arguments = ev.arguments()
		self.users = self.channels[Arguments[0]].users()
		print "User list received: "
		print self.users
	def on_join(self, serv, ev):
		user = irclib.nm_to_n(ev.source())
		if (user != self.name):
			print "Enter "+user
			self.users.append(user)
	def on_part(self, serv, ev):
		user = irclib.nm_to_n(ev.source())
		print "Part "+user
		self.users.remove(user)
	def on_quit(self, serv, ev):
		user = irclib.nm_to_n(ev.source())
		print "Quit "+user
		if self.vf_global_mode == True:
			if user in self.players: self.players.remove(user)
			self.players_ez.remove(user)
			serv.privmsg(self.chan, u"Quelle tarlouze ce "+user)
		self.users.remove(user)


	def on_pubmsg(self, serv, ev):
		#print str(self.vf_w_mode) + str(self.vf_q_mode) + str(self.vf_n_mode)
		message = ev.arguments()[0].decode('utf8')
		user = irclib.nm_to_n(ev.source())
		
		#Check that you can say that
		for i, word in enumerate(self.forbiden_words):
			if word in message.lower():
				print "Kick "+user+" for "+word
				serv.kick(self.chan, user, 'Ne mentionne pas ce mot sur ce chan pauvre fou')

		if self.vf_q_mode:
			if remove_accents(message.lower()) == remove_accents(self.vf_answer.lower()):
				serv.privmsg(self.chan, "Correct "+user+" ! "+self.vf_answer+".")
				self.vf_winner = user
				if user not in self.players:
					serv.mode(self.chan, "+v "+user)
					self.players.append(user)
					time.sleep(2)
					self.say_question(serv)
				else:
					self.vf_q_mode = False
					self.vf_n_mode = True
					serv.privmsg(self.chan, "Qui c'est qu'on zigouille ?")
				self.vf_rq_cpt = 0
			elif "!question" == message or "!q" == message:
				serv.privmsg(self.chan, "** "+self.vf_question)
			elif "!rq" == message:
				if self.vf_rq_time + self.VF_RQ_TIMELAPSE < time.time():
					self.vf_rq_cpt+=1
					if self.vf_rq_cpt < self.vf_rq_need:
						serv.privmsg(self.chan, str(self.vf_rq_cpt)+"/"+str(self.vf_rq_need)+" rq")
						self.vf_rq_time = time.time()
					else:
						self.vf_rq_cpt = 0
						serv.privmsg(self.chan, "La réponse était '".decode("utf8")+self.vf_answer+"', bande de nazes")
						time.sleep(2)
						self.say_question(serv)
				else:
					time_left = '%.2f' % float(self.vf_rq_time + self.VF_RQ_TIMELAPSE - time.time())
					serv.privmsg(self.chan, time_left + " sec avant de pouvoir !rq")
			elif "!ez" == message:
				if not user in self.players:
					serv.privmsg(self.chan, u"Tu dois être voice pour prendre ce risque "+user)
				else:
					self.vf_q_mode = False
					serv.privmsg(self.chan, user+u"_ sait")
					self.players_ez.append(user)
					self.vf_ez_mode = True

		elif self.vf_ez_mode:
			if "!ez" == message:
				if not user in self.players:
					serv.privmsg(self.chan, u"Tu dois être voice pour prendre ce risque "+user)
				else:
					self.players_ez.append(user)
					if len(self.players_ez) == len(self.players):
						serv.privmsg(self.chan, "Tout le monde sait, on passe")
						self.vf_ez_mode = False
						self.players_ez = []
						time.sleep(2)
						self.vf_q_mode = True
						self.say_question(serv)
					else:
						serv.privmsg(self.chan, user+u"_ sait aussi")
			elif "!bluf" == message:
				self.vf_ez_mode = False
				self.vf_ez_ans_mode = True
				serv.privmsg(self.chan, u"Alors c'est quoi la réponse "+self.players_ez[0]+" ?")
				
		elif self.vf_ez_ans_mode:
			if user == self.players_ez[0]:
				self.players_ez = []
				if remove_accents(message.lower()) == remove_accents(self.vf_answer.lower()):
					serv.privmsg(self.chan, u"Ca va, prend 1 "+self.money+" et zigouille un mec")
					self.jokes[user] = self.jokes[user] + 1
					with open('jokes.txt', 'w') as f:
						pickle.dump(self.jokes, f, 0)
					self.vf_ez_ans_mode = False
					self.vf_winner = user
					self.vf_n_mode = True
				else:
					serv.privmsg(self.chan, u"Ta gueule, c'était '"+self.vf_answer+"'")
					serv.mode(self.chan, "-v "+user)
					self.players.remove(user)
					self.vf_ez_ans_mode = False
					if len(self.players) == 1:
						self.vf_victory(serv)
					else:
						time.sleep(2)
						self.vf_q_mode = True
						self.say_question(serv)


		elif self.vf_n_mode:
			if user == self.vf_winner:
				if message in self.users and message != self.name:
					if message in self.players:
						self.vf_n_mode = False
						serv.mode(self.chan, "-v "+message)
						self.players.remove(message)
						self.players_ez = []
						if len(self.players) == 1:
							self.vf_q_mode = False
							self.vf_victory(serv)
						else:
							self.vf_q_mode = True
							time.sleep(2)
							self.say_question(serv)
					else:
						serv.privmsg(self.chan, message + " il est pas voice, tocard. Prends en un autre")
		elif self.dcdl_mode == 0:
			if message == "!deslettresetdeslettres":
				serv.privmsg(self.chan, "!togglecollect")
				self.dcdl_begin(serv)

		elif self.dcdl_mode == 1:	# letter selection
			if message == "voyelle":
				self.dcdl_tirage = self.dcdl_tirage + get_vowel()
				serv.privmsg(self.chan, "** " + self.dcdl_tirage)
			elif message == "consonne":
				self.dcdl_tirage = self.dcdl_tirage + get_consonant()
				serv.privmsg(self.chan, "** " + self.dcdl_tirage)
			if len(self.dcdl_tirage) == 9:
				self.dcdl_mode = 2		# time to think!
				serv.privmsg(self.chan, u"A vous de réfléchir, vous avez 15 secondes. Gardez votre réponse pour vous.")
				Timer(15, self.dcdl_get_answers, (serv,)).start()
		elif self.dcdl_mode == 3:	# answer time
			self.dcdl_answers[user] = message # save answer for user

		if user in self.stats:
			self.stats[user] += 1
		else:
			self.stats[user] = 1
		self.total_msg += 1

		if "yo" == message:
			print "Saying hello to "+user
			serv.privmsg(self.chan, "yo "+user) #Baby call my name
		if message.startswith("!google ") or message.startswith("!g "):
			if message.startswith("!g "):
				query = message[3:100]
			elif message.startswith("!google "):
				query = message[8:100]
			print "Google request from "+user+" for '"+query+"'"
			query = query.replace(" ", "+")
			serv.privmsg(self.chan,
					"http://www.google.com/search?&sourceid=navclient&btnI=I&q="+query)
		if "!ping" == message:
			serv.privmsg(self.chan, "pong "+user+" ("+st[:-4]+")")
		if "!song" == message or "song?" == message:
			print "Song asked by "+user
			serv.privmsg(self.chan, "Darude - Sandstorm https://goo.gl/uGvNCD")
		if self.name in message or "bot" in message:
			if "ty "+self.name in message:
				print "np "+user
				serv.privmsg(self.chan, "np "+user)
			else:
				if random.random() < random.random(): #what the actual fuck
					serv.privmsg(self.chan, "tg "+random.choice(self.insults).decode("utf8"))
		if "et la marmotte" in message:
			print "Marmotte pour "+user
			serv.privmsg(self.chan, "elle met le chocolat")
			serv.privmsg(self.chan, "dans le papier d'alu")
		if "et la marmote" in message:
			print "Marmote (lol) pour "+user
			serv.privmsg(self.chan, "Y a 2 T a marmotte pd. C'est comme un avion, y a 2 L.")
		if "et ta soeur" in message:
			print "Soeur pour "+user
			serv.privmsg(self.chan, "elle bat le beurre")
		if "!storytime" == message or "!story" == message:
			print "Story time "+user+"?"
			serv.privmsg(self.chan, "story time?!" )
			serv.privmsg(self.chan, " ___ _____ ___  _____   __  _____ ___ __  __ ___ " )
			serv.privmsg(self.chan, "/ __|_   _/ _ \| _ \ \ / / |_   _|_ _|  \/  | __|")
			serv.privmsg(self.chan, "\__ \ | || (_) |   /\ V /    | |  | || |\/| | _| ")
			serv.privmsg(self.chan, "|___/ |_| \___/|_|_\ |_|     |_| |___|_|  |_|___|")
			serv.privmsg(self.chan, "https://goo.gl/k9VQkP")
			for i in self.users:
				serv.action(self.chan, "gives popcorn to "+i)
		if "dead" in message or "ded" in message:
			serv.privmsg(self.chan, "rip in couscous")
		if "vallée".decode('utf8') in message.lower() or "vallee" in message.lower() or "tribu" in message.lower() or "dana" in message.lower():
			serv.privmsg(self.chan, "DANS LA VALLEE OH OH DE DANA, LALILALA")
		if "ls" == message:
			serv.privmsg(self.chan, "wrong shell mofo")
		if message.startswith("!rek"):
			serv.privmsg(self.chan, "☐ Not rekt".decode("utf8"))
			serv.privmsg(self.chan, "☑ Rekt".decode("utf8"))
			serv.privmsg(self.chan, "☑ Really Rekt".decode("utf8"))
			serv.privmsg(self.chan, "☑ Tyrannosaurus Rekt".decode("utf8"))
		if "thatsthejoke" in message:
			serv.privmsg(self.chan, "http://i.imgur.com/U7Ghu2s.jpg")
		if "dead inside" in message:
			serv.privmsg(self.chan, "https://goo.gl/ORpTi1")
		if message.startswith("!tf") or message.startswith("!tableflip"):
			serv.privmsg(self.chan, "(╯°□°）╯︵ ┻━┻".decode("utf8"))
		if message.startswith("!ft") or message.startswith("!fliptable"):
			serv.privmsg(self.chan, "┻━┻ ︵╰ (°□°╰)".decode("utf8"))
		if "!rt" == message or "!respecttables" == message:
			serv.privmsg(self.chan, "┬─┬ノ(ಠ_ಠノ)".decode("utf8"))
		if message.startswith("!lf") or message.startswith("!lennyface"):
			serv.privmsg(self.chan, "( ͡° ͜ʖ ͡° )".decode("utf8"))
		if message.startswith("!fu"):
			serv.privmsg(self.chan, "( ° ͜ʖ͡°)╭∩╮".decode("utf8"))
		if message.startswith("!fm") or message.startswith("!fightme"):
			serv.privmsg(self.chan, "(ง ͠° ͟ل͜ ͡°)ง".decode("utf8"))
		if message == "!sh" or message.startswith("!sf") or message.startswith("!shrug"):
			serv.privmsg(self.chan, "¯\_(ツ)_/¯".decode("utf8"))
		if message == "!f" or message == "!bow":
			serv.privmsg(self.chan, "(シ_ _)シ".decode("utf8"))
		if message.startswith("!badum"):
			serv.privmsg(self.chan, "**BADUM TSSS** http://i.imgur.com/BbgL7x3.gif")
		if "popopo" in message.lower():
			if random.random() < 0.5:
				serv.privmsg(self.chan, "https://goo.gl/QZVh3H")
				#http://i.imgur.com/WxQI4UI.jpg
			else:
				serv.privmsg(self.chan, "http://i.imgur.com/VGR9WNA.gifv")
		if "sandwich" in message.lower():
			serv.privmsg(self.chan, "A quoi le sandwich?!")
		if "à la fraise".decode("utf8") in message.lower() or "a la fraise" in message.lower():
			serv.privmsg(self.chan, "Ah..")
		if "feu".decode("utf8") in message.lower():
			serv.privmsg(self.chan, "CHUI CHAUD CHUI CHAUUUUUUUUD")
		if "!stat" == message.lower():
			for i in self.stats:
				stat = '%.2f' % (float(self.stats[i]) / float(self.total_msg) * 100.0)
				serv.privmsg(self.chan, "_"+i+": "+stat+"%")
		if "!slap" == message:
			serv.action(self.chan, "slaps "+random.choice(self.users))
		if "!meme" == message:
			serv.privmsg(self.chan, "https://imgflip.com/memegenerator")
		if "!renard" == message or "!fox" == message:
			serv.privmsg(self.chan, "https://goo.gl/Cb7f8d")
		if "!fb" == message or "!facebook" == message:
			serv.privmsg(self.chan, "https://i.redd.it/nnlm8zbnydmy.jpg")
		if "!wm" == message or "!watermelon" == message:
			serv.privmsg(self.chan, "http://i.imgur.com/sTUyI.gif")
		if "!fetch" == message:
			serv.privmsg(self.chan, "http://i.imgur.com/PqZSzMr.gifv")
		if message.startswith("!n ") or message.startswith("!nice "):
			if message.startswith("!n "):
				target = message[3:100]
			elif message.startswith("!nice "):
				target = message[6:100]
			if target == user:
				serv.privmsg(self.chan, "Tu crois que je sais pas ce que t'es en train de faire ptite pute")
			else:
				if target in self.users:
					if target in self.jokes:
						self.jokes[target] += 1
					else:
						self.jokes[target] = 1
					serv.privmsg(self.chan, "Good jk _"+ target +" i rate 8/8, "+str(self.jokes[target])+" "+self.money)
					with open('jokes.txt', 'w') as f:
						pickle.dump(self.jokes, f, 0)
				else:
					serv.privmsg(self.chan, "Je le connais pas "+ target)
		if "!money" == message :
			serv.privmsg(self.chan, user+": "+str(self.jokes[user])+" "+self.money)
		if "!allmoney" == message or "!moneyall" == message :
			for i in self.jokes:
				serv.privmsg(self.chan, "_"+i+": "+str(self.jokes[i])+" "+self.money)
		if "!suicide" == message:
			if user == self.master:
				serv.privmsg(self.chan, "Ô monde cruel!")
			else:
				serv.privmsg(self.chan, "Je n'écoute que mon maitre, sale péon".decode("utf8"))
		if message.startswith("!money "):
			self.money = message[7:128]
			serv.privmsg(self.chan, "Changement de monnaie, On paie en "+self.money+" maintenant.")
		if "!github" == message:
			serv.privmsg(self.chan, "https://github.com/bemug/BOTanist")

		if "pirate" in message.lower():
			serv.privmsg(self.chan, "YOU ARE A PIRATE ! http://cristgaming.com/pirate")

		if "canard" in message.lower():
			serv.privmsg(self.chan, "COIN COIN MODAFUCKAH")

		if "!racist" == message:
			serv.privmsg(self.chan, "http://i.imgur.com/xV3sl.gif")

		if message.startswith("!youtube ") or message.startswith("!y "):
			if message.startswith("!y "):
				query = message[3:100]
			elif message.startswith("!youtube "):
				query = message[9:100]
			print "Youtube request from "+user+" for '"+query+"'"
			query = query.replace(" ", "+")
			serv.privmsg(self.chan,"https://www.google.fr/search?q=site%3Ayoutube.com+"+query+"&btnI=I")

		if "chanson?" == message:
			serv.privmsg(self.chan, "A CHAQUE CHANSON")
			serv.privmsg(self.chan, "FAUT Y METTRE FAUT Y METTRE")
			serv.privmsg(self.chan, "A CHAQUE CHANSON")
			serv.privmsg(self.chan, "FAUT Y METTRE SON CANON")

		if "otter" in message.lower() or "loutre" in message.lower():
			if random.random() < 0.3:
				serv.privmsg(self.chan, "YOU OTTERFUCKER https://goo.gl/WYdiop")



		if message.lower().rstrip().endswith('age'):
			if random.random() < 0.5:
				serv.privmsg(self.chan, "MAIS " + message.rstrip().split()[-1].upper() + ", CA RIME AVEC FROMAAAAGE" )

		#shop
		if "!shop" == message:
			serv.privmsg(self.chan, "Bienvenue dans le shop!" )
			for i in self.items:
				serv.privmsg(self.chan, "\t"+ i + ": " + str(self.items[i]) + " " + self.money)
			serv.privmsg(self.chan, "!buy <item> <target> pour acheter. Revenez nous voir bientot!")

		if message.startswith("!buy "):
			for i in self.items:
				if message[5:5+len(i)] == i:
					if (self.jokes[user] >= self.items[i]):
						serv.privmsg(self.chan, "Ca fera " + str(self.items[i]) + " " + self.money + " pour ton " + i)
						self.jokes[user] = self.jokes[user] - self.items[i]
						#UGLY AF!
						if i == 'slap':
							serv.action(self.chan, "slaps "+message[10:100]) #todo check user lol
						elif i == 'kick':
							if not self.vf_n_mode and not self.vf_q_mode and not self.vf_w_mode:
								serv.kick(self.chan, message[10:100], 'Quelqu\'un a payé pour ça'.decode('utf8'))
						with open('jokes.txt', 'w') as f:
							pickle.dump(self.jokes, f, 0)
					else:
						serv.privmsg(self.chan, "T'as pas assez de " + self.money + " casse toi sale pauvre.")

		#voicefaible!
		if "!play" == message:
			if self.vf_n_mode or self.vf_q_mode:
					serv.privmsg(self.chan, "Ca joue deja lol")
			elif self.vf_w_mode:
				self.add_player(user, serv)
			else:
				print "Voicefaible "+user
				self.vf_w_mode = True
				Timer(60, self.start_vf, (serv,)).start()
				serv.privmsg(self.chan, "Nouvelle partie! '!play' pour jouer ("+", ".join(self.users)+").")
				self.add_player(user, serv)

		if "!stopvoicefaible" == message:
			if user == self.master:
				print "Stop Vociefaible "+user
				self.vf_q_mode = False
				self.vf_n_mode = False
				self.vf_w_mode = False
				serv.privmsg(self.chan, "Oh, ok on joue plus alors..")
				for i in self.users:
					serv.mode(self.chan, "-v "+i)
				self.players = []

		#Random shit
		if random.random() < 0.004:
			serv.privmsg(self.chan, "me too thanks")
		if random.random() < 0.004:
			serv.privmsg(self.chan, "go startup?")
      
		if message.endswith('i') and not is_a_voyel(message[:-1]):
			if random.random() < 0.2:
				serv.privmsg(self.chan, "mom's spaghetti")

		if message == self.last_message:
			if user != self.last_user:
				self.cpt_last_message += 1
		else:
			if self.cpt_last_message > 2:
				if user != self.last_user:
					serv.privmsg(self.chan, "C-C-C-C COMBO BREAKER ("+user+")")
				else:
					serv.privmsg(self.chan, "C-C-C-C COMBO NOPED ლ(ಠ益ಠლ) (".decode("utf8")+user+")")
			self.cpt_last_message = 0
		self.last_message = message
		self.last_user = user

		#Savin me
		with open('stats.txt', 'w') as f:
			pickle.dump(self.stats, f, 0)

if __name__ == "__main__":
	Bot().start()
