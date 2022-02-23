from __future__ import print_function

import os

from enigma import eTimer

from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry
from Components.Console import Console
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _, svg_support
from .Softcam import checkconfigdir, getcamcmd, getcamscript, stopcam


class AltCamManager(Screen):
	if svg_support:
		skin = """<screen name="AltCamManager" position="center,center" size="660*f,410*f">
				<widget source="list" render="Listbox" position="10*f,10*f" size="355*f,300*f" \
						enableWrapAround="1" scrollbarMode="showOnDemand">
					<convert type="TemplatedMultiContent">
						{"template": [
							MultiContentEntryText(pos=(65*f,10*f), size=(275*f,40*f), \
								font=0, flags=RT_HALIGN_LEFT, text=0),
							MultiContentEntryPixmapAlphaTest(pos=(5*f,5*f), size=(51*f,40*f), \
								png=1, flags=BT_SCALE),
							MultiContentEntryText(pos=(5*f,25*f), size=(51*f,16*f), \
								font=1, flags=RT_HALIGN_CENTER, text=2)],
						"fonts": [gFont("Regular",24*f), gFont("Regular",12*f)],
						"itemHeight": 50*f}
					</convert>
				</widget>
				<eLabel text="Ecm info" position="385*f,0" size="260*f,35*f" font="Regular;24*f"/>
				<widget name="status" position="385*f,40*f" size="260*f,280*f" font="Regular;16*f"/>
				<panel name="DynamicButtonsTemplate"/>
			</screen>"""
	else:
		skin = """<screen position="center,center" size="630,370" title="SoftCam manager">
				<eLabel position="5,0" size="620,2" backgroundColor="#aaaaaa" />
				<widget source="list" render="Listbox" position="10,15" size="340,300" \
						scrollbarMode="showOnDemand">
					<convert type="TemplatedMultiContent">
						{"template": [
							MultiContentEntryText(pos=(65,10), size=(275,40), \
								font=0, flags=RT_HALIGN_LEFT, text=0),
							MultiContentEntryPixmapAlphaTest(pos=(5,5), \
								size=(51,40), png=1),
							MultiContentEntryText(pos=(5, 25), size=(51,16), font=1, \
								flags=RT_HALIGN_CENTER, text=2),],
						"fonts": [gFont("Regular",26), gFont("Regular",12)],
						"itemHeight": 50}
					</convert>
				</widget>
				<eLabel halign="center" position="390,10" size="210,35" font="Regular;20" \
					text="Ecm info" transparent="1"/>
				<widget name="status" position="360,50" size="320,300" font="Regular;16" \
					halign="left"/>
				<ePixmap position="16,321" size="140,40" pixmap="skin_default/buttons/red.png" \
					transparent="1" alphatest="on"/>
				<ePixmap position="169,321" size="140,40" pixmap="skin_default/buttons/green.png" \
					transparent="1" alphatest="on"/>
				<ePixmap position="322,321" size="140,40" pixmap="skin_default/buttons/yellow.png" \
					transparent="1" alphatest="on"/>
				<ePixmap position="475,321" size="140,40" pixmap="skin_default/buttons/blue.png" \
					transparent="1" alphatest="on"/>
				<widget source="key_red" render="Label" position="12,328" zPosition="2" size="148,30" \
					valign="center" halign="center" font="Regular;22" transparent="1"/>
				<widget source="key_green" render="Label" position="165,328" zPosition="2" size="148,30" \
					valign="center" halign="center" font="Regular;22" transparent="1"/>
				<widget source="key_yellow" render="Label" position="318,328" zPosition="2" size="148,30" \
					valign="center" halign="center" font="Regular;22" transparent="1"/>
				<widget source="key_blue" render="Label" position="471,328" zPosition="2" size="148,30" \
					valign="center" halign="center" font="Regular;22" transparent="1"/>
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("SoftCam manager")
		self.Console = Console()
		self["key_red"] = StaticText(_("Stop"))
		self["key_green"] = StaticText(_("Start"))
		self["key_yellow"] = StaticText(_("Restart"))
		self["key_blue"] = StaticText(_("Setup"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions"], {
				"cancel": self.cancel,
				"ok": self.ok,
				"green": self.start,
				"red": self.stop,
				"yellow": self.restart,
				"blue": self.setup,
				"contextMenu": self.setup})
		self["status"] = Label()
		self["list"] = List([])
		checkconfigdir()
		self.actcam = config.plugins.AltSoftcam.actcam.value
		self.camstartcmd = ""
		self.actcampng = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
				"Extensions/AlternativeSoftCamManager/images/actcam.%s" %
						("svg" if svg_support else "png")))
		self.defcampng = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
				"Extensions/AlternativeSoftCamManager/images/defcam.%s" %
						("svg" if svg_support else "png")))
		self.createinfo()
		self.stoppingTimer = eTimer()
		self.closestopTimer = eTimer()
		self.Timer = eTimer()
		try:
			self.stoppingTimer.timeout.callback.append(self.stopping)
		except AttributeError:  # DreamOS
			self.stoppingTimer_conn = self.stoppingTimer.timeout.connect(self.stopping)
			self.closestopTimer_conn = self.closestopTimer.timeout.connect(self.createinfo)
			self.Timer_conn = self.Timer.timeout.connect(self.listecminfo)
		else:
			self.closestopTimer.timeout.callback.append(self.createinfo)
			self.Timer.callback.append(self.listecminfo)
		self.Timer.start(2000, False)

	def listecminfo(self):
		try:
			self["status"].text = open("/tmp/ecm.info", "r").read()
		except IOError:
			self["status"].text = ""

	def createinfo(self, retval=None):
		self.iscam = False
		self.finish = False
		self.camliststart()
		self.listecminfo()

	def camliststart(self):
		if os.path.exists(config.plugins.AltSoftcam.camdir.value):
			self.softcamlist = os.listdir(config.plugins.AltSoftcam.camdir.value)
			if self.softcamlist:
				self.softcamlist.sort()
				self.iscam = True
				for x in self.softcamlist:
					os.chmod(os.path.join(config.plugins.AltSoftcam.camdir.value, x), 0o755)
				if self.actcam != "none" and getcamscript(self.actcam):
					self.createcamlist()
				else:
					self.Console.ePopen("pidof %s" % self.actcam, self.camactive)
			else:
				self.finish = True
				self["list"].list = []
		else:
			checkconfigdir()
			self.camliststart()

	def camactive(self, result, retval, extra_args):
		if result.strip():
			self.createcamlist()
		else:
			self.actcam = "none"
			self.checkConsole = Console()
			for line in self.softcamlist:
				self.checkConsole.ePopen("pidof %s" % line, self.camactivefromlist, line)
			self.checkConsole.ePopen("echo 1", self.camactivefromlist, "none")

	def camactivefromlist(self, result, retval, extra_args):
		if result.strip():
			self.actcam = extra_args
			self.createcamlist()
		else:
			self.finish = True

	def createcamlist(self):
		camlist = []
		if self.actcam != "none":
			camlist.append((self.actcam, self.actcampng, self.checkcam(self.actcam)))
		for line in self.softcamlist:
			if line != self.actcam:
				camlist.append((line, self.defcampng, self.checkcam(line)))
		self["list"].list = camlist
		self.finish = True

	def checkcam(self, cam):
		cam = cam.title()
		if getcamscript(cam):
			return "Script"
		if cam[:5] in ("Oscam", "Camd3", "Newcs", "Rucam"):
			return cam[:5]
		elif cam[:4] in ("Mcas", "Gbox", "Mpcs", "Mbox"):
			return cam[:4]
		cam = cam[:6]
		if "Cccam" in cam:
			return "CCcam"
		else:
			return cam

	def start(self):
		if self.iscam and self.finish:
			self.camstart = self["list"].getCurrent()[0]
			if self.camstart != self.actcam:
				print("[Alternative SoftCam Manager] Start SoftCam")
				self.camstartcmd = getcamcmd(self.camstart)
				self.session.open(MessageBox,
						_("Starting %s") % self.camstart,
						MessageBox.TYPE_INFO, timeout=3)
				self.stoppingTimer.start(100, True)

	def stop(self):
		if self.iscam and self.actcam != "none" and self.finish:
			stopcam(self.actcam)
			self.session.open(MessageBox,
					_("Stopping %s") % self.actcam,
					MessageBox.TYPE_INFO, timeout=3)
			self.actcam = "none"
			self.closestopTimer.start(1000, True)

	def restart(self):
		if self.iscam and self.actcam != "none" and self.finish:
			print("[Alternative SoftCam Manager] restart SoftCam")
			self.camstart = self.actcam
			if self.camstartcmd == "":
				self.camstartcmd = getcamcmd(self.camstart)
			self.session.open(MessageBox,
					_("Restarting %s") % self.actcam,
					MessageBox.TYPE_INFO, timeout=3)
			self.stoppingTimer.start(100, True)

	def stopping(self):
		stopcam(self.actcam)
		self.actcam = self.camstart
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		if service:
			self.session.nav.stopService()
		self.Console.ePopen(self.camstartcmd)
		print("[Alternative SoftCam Manager] ", self.camstartcmd)
		if service:
			self.session.nav.playService(service)
		self.createinfo()

	def ok(self):
		if self.iscam and self.finish:
			if self["list"].getCurrent()[0] != self.actcam:
				self.start()
			else:
				self.restart()

	def cancel(self):
		if self.finish:
			if config.plugins.AltSoftcam.actcam.value != self.actcam:
				config.plugins.AltSoftcam.actcam.value = self.actcam
			config.plugins.AltSoftcam.save()
			self.close()
		else:  # if list setting not completed as they should
			self.cancelTimer = eTimer()
			try:
				self.cancelTimer.timeout.callback.append(self.setfinish)
			except AttributeError:  # DreamOS
				self.cancelTimer_conn = self.cancelTimer.timeout.get().connect(self.setfinish)
			self.cancelTimer.start(4000, True)

	def setfinish(self):
		self.finish = True
		self.cancel()

	def setup(self):
		if self.finish:
			self.session.openWithCallback(self.createinfo, ConfigEdit)


class ConfigEdit(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("SoftCam path configuration")
		self.skinName = ["ConfigEdit", "Setup"]
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Ok"))
		self["HelpWindow"] = Pixmap()
		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
				"cancel": self.keyCancel,
				"red": self.keyCancel,
				"ok": self.ok,
				"green": self.ok}, -2)
		ConfigListScreen.__init__(self, [], session=session)
		self["config"].list = [getConfigListEntry(_("SoftCam config directory"),
				config.plugins.AltSoftcam.camconfig),
			getConfigListEntry(_("SoftCam directory"),
				config.plugins.AltSoftcam.camdir),
			getConfigListEntry(_("Show 'Restart softcam' in extensions menu"),
				config.plugins.AltSoftcam.restartext)]

	def ok(self):
		msg = []
		if not os.path.exists(config.plugins.AltSoftcam.camconfig.value):
			msg.append("%s " % config.plugins.AltSoftcam.camconfig.value)
		if not os.path.exists(config.plugins.AltSoftcam.camdir.value):
			msg.append("%s " % config.plugins.AltSoftcam.camdir.value)
		if not msg:
			if config.plugins.AltSoftcam.camconfig.value[-1] == "/":
				config.plugins.AltSoftcam.camconfig.value = config.plugins.AltSoftcam.camconfig.value[:-1]
			if config.plugins.AltSoftcam.camdir.value[-1] == "/":
				config.plugins.AltSoftcam.camdir.value = config.plugins.AltSoftcam.camdir.value[:-1]
			self.keySave()
		else:
			current = self["config"].getCurrent()[1]
			if hasattr(current, "help_window"):
				current.help_window.instance.hide()
			self.session.openWithCallback(self.okCallback, MessageBox,
					_("Directory %s does not exist!\nPlease set the correct directory path!")
					% msg, MessageBox.TYPE_INFO, timeout=5)

	def okCallback(self, callback=None):
		current = self["config"].getCurrent()[1]
		if hasattr(current, "help_window"):
			current.help_window.instance.show()
