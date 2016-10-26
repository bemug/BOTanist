#!/usr/bin/env python
# -*- coding: utf8 -*-

import irclib
import ircbot
import random
import os
import pickle
import time
import unicodedata
from threading import Timer

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


class Bot(ircbot.SingleServerIRCBot):
	chan = "#contreloutre"
	name = "BOTanist"
	money = "pokétunes".decode("utf8")
	cpt_last_message = 0
	last_message = ""
	last_user = ""
	insults = open('insults.txt').read().splitlines()
	users = []
	players = []
	stats ={}
	jokes ={}
	total_msg = 0
	vf_q_mode = False
	vf_n_mode = False
	vf_w_mode = False
	vf_answer = ""
	vf_question = ""
	vf_winner = ""
	vf_rq_cpt = 0
	vf_rq_time = 0
	VF_RQ_MAX = 3
	VF_RQ_TIMELAPSE = 5
	rand_game_is_on = False
	rand_game_bet = 1
	rand_game_players = []
	
	def create_rand_game(self, user, args, serv):
		try: 
			rand_game_bet = int(args)
			if self.jokes[user] < self.rand_game_bet:
				serv.privmsg(self.chan, "Lol tu es bien trop pauvre pour lancer une partie avec une mise si grosse "+user+" (pas du tout ctb jajaja)")
			else:
				self.rand_game_is_on = True
				self.rand_game_players = []
				self.rand_game_players.append(user)
				Timer(60, self.play_rand_game, (serv,)).start()
				serv.privmsg(self.chan, "Faites vos jeux ! La mise est a "+self.rand_game_bet+", '!rand' pour jouer ("+", ".join(self.users)+"), 60 secondes avant le tirage.")
		except ValueError:
			rand_game_bet = 1
			serv.privmsg(self.chan, "C'est pas un nombre ca: "+args+" ... petit con va !")
			
	def join_rand_game(self, user, serv):
		if user not in self.rand_game_players:
			if self.jokes[user] < self.rand_game_bet:
				serv.privmsg(self.chan, "Lol tu es bien trop pauvre pour te permettre de jouer avec nous "+user)
			else:
				self.rand_game_players.append(user)
				serv.privmsg(self.chan, user+" rejoins la partie ! Lui au moins il a des ballz.")
		else:
			serv.privmsg(self.chan, ("T'es déjà dans la liste des joueurs "+user).decode("utf8"))
	
	def play_rand_game(self, serv):
		serv.privmsg(self.chan, "Let's go !!!")
		max = -1
		gagnant = self.rand_game_players[0]
		nbr_joueurs = 0
		for i in self.rand_game_players:
			nbr_joueurs = nbr_joueurs + 1
			score = 100 * random.random()
			if score > max:
				max = score
				gagnant = i
				serv.privmsg(self.chan, ("_"+i+" lance les dés et obtient un "+score+" ! Il prend la tête !!").decode("utf8"))
			else:
				serv.privmsg(self.chan, ("_"+i+" lance les dés et obtient un "+score+" ... Quel gros naze").decode("utf8"))
			time.sleep(1)
		prize = (nbr_joueurs - 1) * self.rand_game_bet
		for i in self.rand_game_players:
			if i == gagnant:
				self.jokes[i] += prize
				serv.privmsg(self.chan, ("_"+i+" gagne donc "+prize+" "+self.money+" !").decode("utf8"))
			else:
				self.jokes[i] -= self.rand_game_bet
				serv.privmsg(self.chan, ("_"+i+" perd donc "+self.rand_game_bet+" "+self.money+" (ahah dtc noob)").decode("utf8"))
		self.rand_game_is_on = False

	def start_vf(self, serv):
		if len(self.players) > 1:
			serv.privmsg(self.chan, "Debut de la partie! ("+", ".join(self.players)+")")
			self.vf_w_mode = False
			self.vf_q_mode = True
			time.sleep(2)
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
		print "Question! "+str(self.vf_w_mode) + str(self.vf_q_mode) + str(self.vf_n_mode)
		randf = random.choice(os.listdir("questions/"))
		f = open("questions/"+randf, 'r').read().splitlines()
		line = random.choice(f).decode("utf-8")
		self.vf_question = line.split("|")[0]
		self.vf_answer = line.split("|")[1]
		serv.privmsg(self.chan, self.vf_question)
		self.vf_rq_time = time.time()
		print self.players

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
		serv.nick("BOTanist")
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
		self.users.remove(user)


	def on_pubmsg(self, serv, ev):
		#print str(self.vf_w_mode) + str(self.vf_q_mode) + str(self.vf_n_mode)
		message = ev.arguments()[0].decode('utf8')
		user = irclib.nm_to_n(ev.source())

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
				serv.privmsg(self.chan, self.vf_question)
			elif "!rq" == message:
				if self.vf_rq_time + self.VF_RQ_TIMELAPSE < time.time():
					self.vf_rq_cpt+=1
					if self.vf_rq_cpt < self.VF_RQ_MAX:
						serv.privmsg(self.chan, str(self.vf_rq_cpt)+"/"+str(self.VF_RQ_MAX)+" rq")
						self.vf_rq_time = time.time()
					else:
						self.vf_rq_cpt = 0
						serv.privmsg(self.chan, "La réponse était '".decode("utf8")+self.vf_answer+"', bande de nazes")
						time.sleep(2)
						self.say_question(serv)
				else:
					time_left = '%.2f' % float(self.vf_rq_time + self.VF_RQ_TIMELAPSE - time.time())
					serv.privmsg(self.chan, time_left + " sec avant de pouvoir !rq")

		elif self.vf_n_mode:
			if user == self.vf_winner:
				if message in self.users and message != self.name:
					if message in self.players:
						self.vf_n_mode = False
						serv.mode(self.chan, "-v "+message)
						self.players.remove(message)
						if len(self.players) == 1:
							self.vf_q_mode = False
							serv.privmsg(self.chan, "GG "+self.players[0])
							serv.mode(self.chan, "-v "+self.players[0])
							serv.privmsg(self.chan, "Partie terminée :)".decode("utf8"))
							self.players = []
						else:
							self.vf_q_mode = True
							time.sleep(2)
							self.say_question(serv)
					else:
						serv.privmsg(self.chan, message + " il est pas voice, tocard. Prends en un autre")

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
		if "!song" == message or "song?" == message:
			print "Song asked by "+user
			serv.privmsg(self.chan, "Darude - Sandstorm")
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
		if "story time" in message:
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
			serv.privmsg(self.chan, "DANS LA VALLEE OH OH DE DANA")
			serv.privmsg(self.chan, "LALILALA")
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
		if "popopo" in message.lower() or "oooo" in message.lower():
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
		if "!jokes" == message or "!joke" == message:
			for i in self.jokes:
				serv.privmsg(self.chan, "_"+i+": "+str(self.jokes[i])+" "+self.money)
		if "!suicide" == message:
			serv.privmsg(self.chan, "Ô monde cruel!")
		if message.startswith("!money "):
			self.money = message[7:30]
		if "!github" == message:
			serv.privmsg(self.chan, "https://github.com/bemug/BOTanist")

		if "canard" in message.lower():
			serv.privmsg(self.chan, "COIN COIN MODAFUCKAH")

		if message.lower().rstrip().endswith('age'):
			serv.privmsg(self.chan, "MAIS " + message.rstrip().split()[-1].upper() + ", CA RIME AVEC FROMAAAAGE" )

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
				
		#join rand game		
		if "!rand" == message:
			if not self.rand_game_is_on:
				serv.privmsg(self.chan, "En fait, s'tu veux, la y'a genre ... aucune partie en cours..., utilise !rand <bet> pour lancer une partie !")
			else:
				print "RandGameJoin "+user
				self.join_rand_game(user,serv)
		
		#create rand game
		if message.startswith("!rand "):
			if self.rand_game_is_on:
				serv.privmsg(self.chan, "Il y'a deja une partie en cours, peux-tu patienter un peu sale merde ??? Ou bien si tu veux la rejoindre, c'est juste !rand")
			else:
				print "RandGameCreate "+user
				args = message[6:100]
				self.create_rand_game(user,args,serv)
				
		if "!stopvoicefaible" == message:
			print "Stop Vociefaible "+user
			self.vf_q_mode = False
			self.vf_n_mode = False
			self.vf_w_mode = False
			serv.privmsg(self.chan, "Oh, ok on joue plus alors..")
			for i in self.users:
				serv.mode(self.chan, "-v "+i)
			self.players = []

		#Random shit
		if random.random() < 0.005:
			serv.privmsg(self.chan, "me too thanks")
		if random.random() < 0.005:
			serv.privmsg(self.chan, "go startup?")
		if random.random() < 0.1:
			if is_last_voyel('i', message) or is_last_voyel('y', message):
				serv.privmsg(self.chan, "Mom's Spaghetti")


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
