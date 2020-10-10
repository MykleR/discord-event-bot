from engine.importlib import *
from engine.settings import *
from engine.tools import *
from engine.event import Event, EventData


class EventManager(threading.Thread):
	def __init__(self,bot,loop,events=[]):
		super().__init__()
		self.bot = bot
		if not events:self.events=[]
		else:self.events = events
		self.data = {}
		self.loop = loop
		self.alive = threading.Event()
		self.time = getTodayTime()

	def changeEventTitle(self,event,title):
		if not self.titleExists(title) or event.title==title:
			event.title = title;return True
		return False

	def loadEvents(self,path=DATA_PATH,default=DEFAULT_DATA):
		self.data = readJson(path)
		if not self.data:
			writeJson(path,default)
			self.data = default
		for d in self.data["events"]:
			self.createEvent(d,save=False)

	def saveEvent(self,event,path=DATA_PATH):
		event.saveData()
		if not self.data or not event.data:return
		titles = [e[EventData.DEFAULT_VALUES[0][0]] for e in self.data["events"]]
		if event.title not in titles:
			self.data["events"].append(event.data)
		else:self.data["events"][titles.index(event.title)]=event.data
		writeJson(path,self.data)

	def saveEvents(self,path=DATA_PATH,default=DEFAULT_DATA):
		for event in self.events:
			event.saveData()
		self.data = {"events":[event.data for event in self.events]}
		writeJson(path,self.data)

	def titleExists(self,title):
		for event in self.events:
			if title == event.title:
				return event
		return

	def createEvent(self,data,save=True):
		if not self.titleExists(data['title']):
			new_event = Event(self,data)
			self.events.append(new_event)
			if save:self.saveEvent(new_event)
			self.createTask(new_event.run)
			return new_event

	def removeEvent(self,event):
		if event in self.events:
			self.events.remove(event)
			event.stop()
			event = None
			self.saveEvents()
			return True
		return False

	def listEvent(self):
		return [event.title for event in self.events]

	def createTask(self,task,*args,**kwargs):
		asyncio.run_coroutine_threadsafe(task(*args,**kwargs), self.loop)

	def updateEvent(self,event):self.createTask(event.update)
	def startEvent (self,event):self.createTask(event.start)

	def run(self):
		asyncio.set_event_loop(self.loop)
		self.alive.set()
		while self.alive.isSet():
			self.time = getTodayTime()
			for event in self.events:
				if self.time >= event.date:
					self.startEvent(event)
				elif event.alive.isSet():#UDPATE EMBEDS
					self.updateEvent(event)
					self.saveEvent(event)
			time_left=60-datetime.now().second
			time.sleep(time_left)

	def stop(self,timeout=None):
		self.alive.clear()
		self.saveEvents()
		for event in self.events:event.stop()
		super().join(timeout)
