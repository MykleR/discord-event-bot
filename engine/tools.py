from engine.importlib import *
from engine.settings import *


async def confirm(ctx):
	await ctx.message.add_reaction(COMMAND_VALID_EMOJI)

async def failed(ctx):
	await ctx.message.add_reaction(COMMAND_FAIL_EMOJI)


def rmDoublon(l):
	return list(set(l))

def format_list(l,oneline=True,minwidth=50):
	if oneline:
		return '`'+str(l).replace("[","").replace("]","").replace("'","")+'`'
	else:
		string = "```\n"
		if len(l)==0:
			string+=' '*minwidth
		else:
			for element in l:
				width = minwidth - len(str(element)) if minwidth > len(str(element)) else 0
				string+=str(element)+' '*width+"\n"
		string += "```"
		return string


def readJson(path):
	try:
		with open(path,'r') as f:
			 data = json.load(f)
		return data
	except: return None

def writeJson(path,data):
	try:
		with open(path,'w') as f:
			json.dump(data,f,indent=4,separators=(',', ': '))
		return True
	except: return False

def checkDate(string):
	try:
		date,time = string.split(TD_SEPARATOR) if TD_SEPARATOR in string else ('',string)
		date_infos = date.split(DATE_SEPARATOR) if date else []
		if TIME_SEPARATOR in time:hours,minutes = time.split(TIME_SEPARATOR)
		else:hours,minutes = time,0;time+=':00'
		if len(date_infos)>3:return [None]*4
		for info in date_infos:
			int(info)
			if len(info)>2:return [None]*4
		return date,time,(int(hours),int(minutes)),date_infos
	except:return [None]*4

def utc_to_local(utc_dt,tz=LOCAL_TZ):
	local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)
	return tz.normalize(local_dt) # .normalize might be unnecessary

def string2Date(string,dateformat=DATE_FORMAT,zone=LOCAL_TZ):
	try:return datetime.strptime(string, dateformat)
	except:return

def getTodayTime(format=DATE_FORMAT,zone=LOCAL_TZ):
	return string2Date(utc_to_local(datetime.utcnow()).strftime(format),format,zone)

def getInputDate(string):
	date,time,tinfos,dinfos = checkDate(string)
	if not time or tinfos==None:return
	if len(dinfos)==0:
		return datetime.now().strftime('%d-%m-')+str(abs(datetime.now().year)%100)+TD_SEPARATOR+time
	if len(dinfos)==1:
		return date+datetime.now().strftime('-%m-')+str(abs(datetime.now().year)%100)+TD_SEPARATOR+time
	if len(dinfos)==2:
		return date+DATE_SEPARATOR+str(abs(datetime.now().year)%100)+TD_SEPARATOR+time
	return string
