import os

from Components.config import config
from Components.Console import Console


def getcamcmd(cam):
	camname = cam.lower()
	if getcamscript(camname):
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " start"
	elif "oscam" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " -bc " + \
			config.plugins.AltSoftcam.camconfig.value + "/"
	elif "wicard" in camname:
		return "ulimit -s 512; " + config.plugins.AltSoftcam.camdir.value + \
		"/" + cam + " -d -c " + config.plugins.AltSoftcam.camconfig.value + \
		"/wicardd.conf"
	elif "camd3" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " " + \
			config.plugins.AltSoftcam.camconfig.value + "/camd3.config"
	elif "mbox" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " " + \
			config.plugins.AltSoftcam.camconfig.value + "/mbox.cfg"
	elif "mpcs" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " -c " + \
			config.plugins.AltSoftcam.camconfig.value
	elif "newcs" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " -C " + \
			config.plugins.AltSoftcam.camconfig.value + "/newcs.conf"
	elif "vizcam" in camname:
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " -b -c " + \
			config.plugins.AltSoftcam.camconfig.value + "/"
	elif "rucam" in camname:
		if not os.path.exists("/proc/sparkid"):
			if os.path.exists("/lib/modules/encrypt.ko"):
				Console().ePopen("insmod /lib/modules/encrypt.ko")
			else:
				for version in os.listdir("/lib/modules"):
					if os.path.exists("/lib/modules/%s/extra/encrypt/encrypt.ko" % version):
						Console().ePopen("modprobe encrypt")
			sparkid = config.plugins.AltSoftcam.camconfig.value + "/sparkid"
			if os.path.exists(sparkid):
				cmd = "cat " + sparkid + " > /proc/sparkid"
				from time import sleep
				sleep(2)
				Console().ePopen(cmd)
		return config.plugins.AltSoftcam.camdir.value + "/" + cam + " -b"
	return config.plugins.AltSoftcam.camdir.value + "/" + cam


def getcamscript(cam):
	cam = cam.lower()
	if cam[-3:] == ".sh" or cam[:7] == "softcam" or cam[:10] == "cardserver":
		return True
	return False


def stopcam(cam):
	if getcamscript(cam):
		cmd = config.plugins.AltSoftcam.camdir.value + "/" + cam + " stop"
	else:
		cmd = "killall -15 " + cam
	print "[Alternative SoftCam Manager] stopping", cam
	Console().ePopen(cmd)
	try:
		os.remove("/tmp/ecm.info")
	except:
		pass


def __createdir(list):
	dir = ""
	for line in list[1:].split("/"):
		dir += "/" + line
		if not os.path.exists(dir):
			try:
				os.mkdir(dir)
			except:
				print "[Alternative SoftCam Manager] Failed to mkdir", dir


def checkconfigdir():
	if not os.path.exists(config.plugins.AltSoftcam.camconfig.value):
		__createdir("/var/keys")
		config.plugins.AltSoftcam.camconfig.value = "/var/keys"
		config.plugins.AltSoftcam.camconfig.save()
	if not os.path.exists(config.plugins.AltSoftcam.camdir.value):
		__createdir("/var/emu")
		config.plugins.AltSoftcam.camdir.value = "/var/emu"
		config.plugins.AltSoftcam.camdir.save()
