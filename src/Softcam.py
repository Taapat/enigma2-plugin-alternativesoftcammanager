from __future__ import print_function

import os

from Components.config import config
from Components.Console import Console


def getcamcmd(cam):
	camname = cam.lower()
	camdir = config.plugins.AltSoftcam.camdir.value
	camconfig = config.plugins.AltSoftcam.camconfig.value
	if getcamscript(camname):
		return "%s/%s start" % (camdir, cam)
	elif "oscam" in camname:
		return "%s/%s -bc %s/" % (camdir, cam, camconfig)
	elif "wicard" in camname:
		return "ulimit -s 512; %s/%s -d -c %s/wicardd.conf" % (camdir, cam, camconfig)
	elif "camd3" in camname:
		return "%s/%s %s/camd3.config" % (camdir, cam, camconfig)
	elif "mbox" in camname:
		return "%s/%s %s/mbox.cfg" % (camdir, cam, camconfig)
	elif "mpcs" in camname:
		return "%s/%s -c %s/" % (camdir, cam, camconfig)
	elif "newcs" in camname:
		return "%s/%s -C %s/newcs.conf" % (camdir, cam, camconfig)
	elif "vizcam" in camname:
		return "%s/%s -b -c %s/" % (camdir, cam, camconfig)
	return "%s/%s" % (camdir, cam)


def getcamscript(cam):
	cam = cam.lower()
	if cam[-3:] == ".sh" or cam[:7] == "softcam" or cam[:10] == "cardserver":
		return True


def stopcam(cam):
	if getcamscript(cam):
		cmd = "%s/%s stop" % (config.plugins.AltSoftcam.camdir.value, cam)
	else:
		cmd = "killall -15 %s" % cam
	print("[Alternative SoftCam Manager] stopping", cam)
	Console().ePopen(cmd)
	try:
		os.remove("/tmp/ecm.info")
	except OSError:
		pass


def checkconfigdir():
	def createdir(dir_list):
		new_dir = ""
		for line in dir_list[1:].split("/"):
			new_dir += "/%s" % line
			if not os.path.exists(new_dir):
				try:
					os.mkdir(new_dir)
				except OSError as e:
					print("[Alternative SoftCam Manager] Failed to mkdir", e)
					break

	if not os.path.exists(config.plugins.AltSoftcam.camconfig.value):
		createdir("/var/keys")
		config.plugins.AltSoftcam.camconfig.value = "/var/keys"
		config.plugins.AltSoftcam.camconfig.save()
	if not os.path.exists(config.plugins.AltSoftcam.camdir.value):
		createdir("/var/emu")
		config.plugins.AltSoftcam.camdir.value = "/var/emu"
		config.plugins.AltSoftcam.camdir.save()
