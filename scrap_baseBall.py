import requests, bs4
import re, os
import string, time, random
from lxml.html import fromstring
import traceback

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ============================= AUXILIAR FUNCTIONS ============================= 

# GLobal variables
proxiesList = []
userAgents = []
proxies = {}
headers = {}

''' These auxiliar functions generate and rotate IP proxy and user agent requests 
    in order to avoid getiting blocked by the server.'''

# The function below returns a fresh list of proxies and userAgents
def GenerateProxiesAndUserAgent(amoutOfProxies=100):

	# Gets avaible proxies at .https://free-proxy-list.net/
	# The function below returns a list of proxies
	def getProxies(amoutOfProxies):
		url = 'https://free-proxy-list.net/'
			
		response = requests.get(url, timeout=5)

		parser = fromstring(response.text)
		
		global proxiesList

		proxiesList = []

		for i in parser.xpath('//tbody/tr')[:amoutOfProxies]:
			# Slicing elite and Https proxies
			if i.xpath('.//td[7][contains(text(),"yes")]') and i.xpath('.//td[5][contains(text(),"elite proxy")]'):
				proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
				proxiesList.append(proxy)

	# Loads an user agent list from a txt file
    # The function below returns a list of user agents
	def loadUserAgentsList():
		global userAgents
		userAgents = []
		os.chdir(os.path.dirname(os.path.abspath(__file__)))
		with open('user_agents.txt') as f:
			userAgents = f.read().splitlines()
		del userAgents[-1]

	getProxies(amoutOfProxies)
	
	global userAgents
	if not(userAgents):
		loadUserAgentsList()

# Selects a random proxy from proxies list
def SelectRandomProxyFromList():
	
	global proxiesList

	# Prevents errors in case proxies list is empty
	while True: 
		try: 
			proxy = random.choice(proxiesList)
			break
		except:
			# Get new proxies
			GenerateProxiesAndUserAgent()
			continue

	return proxy

# Builds random requests parameters
def BuildRequestsParameters():

	global userAgents
	global proxies
	global headers

	proxy = SelectRandomProxyFromList()

	proxies = {"http": 'http://'+proxy,"https":'http://'+ proxy}
	headers = {'User-Agent': random.choice(userAgents)}

# Handles erros that might occur during a request
def ErrorHandlder(errCount):
	if errCount > 20:
		GenerateProxiesAndUserAgent()
		errCount = 0
	BuildRequestsParameters()
	errCount +=1
	return errCount

# Makes a request
def MakeRequest (url):
	
	global proxies
	global headers

	BuildRequestsParameters()
	res = ''
	while True:	
		errCount = 0
		try:
			res = requests.get(url=url, timeout=5, proxies=proxies,headers=headers)
			break
		except requests.exceptions.ReadTimeout:
			errCount = ErrorHandlder(errCount)
			continue
		except:
			errCount = ErrorHandlder(errCount)
			continue
	return res

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# ============================= MAIN FUNCTIONS ============================= 


# Pulls all the player data required.
'''The function below recieves an url that contains
   and returns a list with the player's name, position
   birthday, birth Place and imgUrl''' 
def pullPlayerData(url):

	# Extracts the player position of a bs4.element.ResultSet object
	'''The function below receives a bs4.element.ResultSet object
	   that has all p tags from the player page source. '''
	'''The function returns a string that contains the 
	   player's birth place. '''
	
	def extractPosition(pSoup):
		position = ''
		for pTag in pSoup:
			try:
				pTag.strong.text
				if pTag.strong.text== 'Position:' or pTag.strong.text== 'Positions:':
					position = pTag.text.strip('\nPosition:\n').rstrip().strip('  ')
					break
			except AttributeError:
				continue
		return position

	# Extracts birthday and birth place of a bs4.element.ResultSet object
	'''The function below recieves a bs4.element.ResultSet object
	   that has all span tags of the player page source. '''
	'''The function returns a string that contains the 
	   player's birth place. ''' 
	
	def extractBirthdayAndBirthPlace(spanSoup):
		birthday = '' 
		birthPlace = ''
		stopBirthPlace = False
		stopBirthday = False
		for spanTag in spanSoup:
			for key in spanTag.attrs:

				if key == 'data-birth':
					birthday = spanTag.text.strip().split(',')[0]
					stopBirthday = True

				if spanTag.attrs[key] == 'birthPlace':
					birthPlace = spanTag.text.strip().strip('in ')
					stopBirthPlace = True

				if stopBirthPlace & stopBirthday: break

			if stopBirthPlace & stopBirthday: break

		return birthday, birthPlace

	res = MakeRequest(url)

	# Getting rid of comments
	comm = re.compile("<!--|-->")
	# Making the soup
	soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
	# Breaking tags
	tagDiv = soup.findAll('div', id='info')
	tagSpan = soup.findAll('span')
	tagP = soup.findAll('p')
	tagH1 = soup.findAll('h1')

	# Extracting data
	name = tagH1[0].string
	position = extractPosition(tagP)
	birthday, birthPlace = extractBirthdayAndBirthPlace(tagSpan)
	try:
		imgURL = tagDiv[0].div.div.img.attrs['src']
	except:
		imgURL = ''

	# Gathering data
	responseList = []
	responseList.append(name)
	responseList.append(position)
	responseList.append(birthday)
	responseList.append(birthPlace)
	responseList.append(imgURL)

	return responseList


# Pulls all the player data required.
'''The function below recieves an url that contains
   and returns a list with the player's name, position
   birthday, birth Place and imgUrl''' 
def getData():

	fileHeader = ['Id','Name','Position', 'Birthday','BirthPlace','ImgURL']
	# prints file header
	'''print (';'.join(fileHeader))'''
	playerId = 1
	
	global proxies
	global headers

	BuildRequestsParameters()


	for letter in list(string.ascii_lowercase):
		
		
		url = 'https://www.baseball-reference.com/players/' + letter
		
		res = MakeRequest(url)

		# Getting rid of comments
		comm = re.compile("<!--|-->")
		# Making the soup
		soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
		
		# Breaking tags
		divSoup= soup.findAll('div', id="div_players_")
		pSoup = divSoup[0].findAll('p')

		# Extracting data
		for pTag in pSoup:
			# Building playerURl
			link = letter + pTag.a.attrs['href'].split('/' + letter)[-1]
			playerURL = url + '/' + link

			# pullingData
			playerData = pullPlayerData(playerURL)
			# prints Data without a ID
			print(';'.join(playerData))
			# prints Data with an ID
			'''print(playerId + ';' + ';'.join(playerData))'''
			playerId += 1
	

# Main Funciotn
def main():
	
	GenerateProxiesAndUserAgent()
	getData()

if __name__ == "__main__":
	main()
