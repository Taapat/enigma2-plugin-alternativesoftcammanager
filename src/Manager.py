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

from . import _
from Softcam import checkconfigdir, getcamcmd, getcamscript, stopcam


class AltCamManager(Screen):
	skin = """
		<screen position="center,center" size="630,370" title="SoftCam manager">
			<eLabel position="5,0" size="620,2" backgroundColor="#aaaaaa" />
			<widget source="list" render="Listbox" position="10,15" size="340,300" \
				scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{
					"template": [MultiContentEntryText(pos=(65, 10), size=(275, 40), \
							font=0, flags=RT_HALIGN_LEFT, text=0),
						MultiContentEntryPixmapAlphaTest(pos=(5, 5), \
							size=(51, 40), png=1),
						MultiContentEntryText(pos=(5, 25), size=(51, 16), font=1, \
							flags=RT_HALIGN_CENTER, text=2),],
					"fonts": [gFont("Regular", 26), gFont("Regular", 12)],
					"itemHeight": 50
				}
				</convert>
			</widget>
			<eLabel halign="center" position="390,10" size="210,35" font="Regular;20" \
				text="Ecm info" transparent="1" />
			<widget name="status" position="360,50" size="320,300" font="Regular;16" \
				halign="left" />
			<ePixmap position="16,321" size="140,40" pixmap="skin_default/buttons/red.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="169,321" size="140,40" pixmap="skin_default/buttons/green.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="322,321" size="140,40" pixmap="skin_default/buttons/yellow.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="475,321" size="140,40" pixmap="skin_default/buttons/blue.png" \
				transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="12,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_green" render="Label" position="165,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_yellow" render="Label" position="318,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_blue" render="Label" position="471,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("SoftCam manager"))
		self.Console = Console()
		self["key_red"] = StaticText(_("Stop"))
		self["key_green"] = StaticText(_("Start"))
		self["key_yellow"] = StaticText(_("Restart"))
		self["key_blue"] = StaticText(_("Setup"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.ok,
				"green": self.start,
				"red": self.stop,
				"yellow": self.restart,
				"blue": self.setup
			})
		self["status"] = Label()
		self["list"] = List([])
		checkconfigdir()
		self.actcam = config.plugins.AltSoftcam.actcam.value
		self.camstartcmd = ""
		self.actcampng = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
			"Extensions/AlternativeSoftCamManager/images/actcam.png"))
		self.defcampng = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
			"Extensions/AlternativeSoftCamManager/images/defcam.png"))
		self.stoppingTimer = eTimer()
		self.stoppingTimer.timeout.get().append(self.stopping)
		self.closestopTimer = eTimer()
		self.closestopTimer.timeout.get().append(self.closestop)
		self.createinfo()
		self.Timer = eTimer()
		self.Timer.callback.append(self.listecminfo)
		self.Timer.start(2000, False)

	def listecminfo(self):
		try:
			self["status"].setText(open("/tmp/ecm.info", "r").read())
		except:
			self["status"].setText("")

	def createinfo(self):
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
					os.chmod(os.path.join(config.plugins.AltSoftcam.camdir.value, x) , 0755)
				if self.actcam != "none" and getcamscript(self.actcam):
					self.createcamlist()
				else:
					self.Console.ePopen("pidof %s" % self.actcam, self.camactive)
			else:
				self.finish = True
				self["list"].setList([])
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
		self["list"].setList(camlist)
		self.finish = True

	def checkcam(self, cam):
		cam = cam.lower()
		if getcamscript(cam):
			return "Script"
		elif "oscam" in cam:
			return "Oscam"
		elif "mgcamd" in cam:
			return "Mgcamd"
		elif "wicard" in cam:
			return "Wicard"
		elif "camd3" in cam:
			return "Camd3"
		elif "mcas" in cam:
			return "Mcas"
		elif "cccam" in cam:
			return "CCcam"
		elif "gbox" in cam:
			return "Gbox"
		elif "mpcs" in cam:
			return "Mpcs"
		elif "mbox" in cam:
			return "Mbox"
		elif "newcs" in cam:
			return "Newcs"
		elif "vizcam" in cam:
			return "Vizcam"
		elif "rucam" in cam:
			return "Rucam"
		else:
			return cam[:6]

	def start(self):
		if self.iscam and self.finish:
			self.camstart = self["list"].getCurrent()[0]
			if self.camstart != self.actcam:
				print "[Alternative SoftCam Manager] Start SoftCam"
				self.camstartcmd = getcamcmd(self.camstart)
				msg = _("Starting %s") % self.camstart
				self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
				self.stoppingTimer.start(100, False)

	def stop(self):
		if self.iscam and self.actcam != "none" and self.finish:
			stopcam(self.actcam)
			msg  = _("Stopping %s") % self.actcam
			self.actcam = "none"
			self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
			self.closestopTimer.start(1000, False)

	def closestop(self):
		self.closestopTimer.stop()
		self.mbox.close()
		self.createinfo()

	def restart(self):
		if self.iscam and self.actcam != "none" and self.finish:
			print "[Alternative SoftCam Manager] restart SoftCam"
			self.camstart = self.actcam
			if self.camstartcmd == "":
				self.camstartcmd = getcamcmd(self.camstart)
			msg = _("Restarting %s") % self.actcam
			self.mbox = self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
			self.stoppingTimer.start(100, False)

	def stopping(self):
		self.stoppingTimer.stop()
		stopcam(self.actcam)
		self.actcam = self.camstart
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		if service:
			self.session.nav.stopService()
		self.Console.ePopen(self.camstartcmd)
		print "[Alternative SoftCam Manager] ", self.camstartcmd
		if self.mbox:
			self.mbox.close()
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
			self.cancelTimer.timeout.get().append(self.setfinish)
			self.cancelTimer.start(4000, False)

	def setfinish(self):
		self.cancelTimer.stop()
		self.finish = True
		self.cancel()

	def setup(self):
		if self.finish:
			self.session.openWithCallback(self.createinfo, ConfigEdit)


class ConfigEdit(Screen, ConfigListScreen):
	skin = """
		<screen name="ConfigEdit" position="center,center" size="500,200" \
			title="SoftCam path configuration">
			<eLabel position="5,0" size="490,2" backgroundColor="#aaaaaa" />
			<widget name="config" position="20,20" size="460,75" zPosition="1" \
				scrollbarMode="showOnDemand" />
			<ePixmap position="100,143" size="140,40" pixmap="skin_default/buttons/red.png" \
				transparent="1" alphatest="on" />
			<ePixmap position="270,143" size="140,40" pixmap="skin_default/buttons/green.png" \
				transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="100,150" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_green" render="Label" position="270,150" zPosition="2" size="140,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget name="HelpWindow" position="400,480" size="1,1" zPosition="5" \
					pixmap="skin_default/vkey_icon.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("SoftCam path configuration"))
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Ok"))
		self["HelpWindow"] = Pixmap()
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"red": self.cancel,
				"ok": self.ok,
				"green": self.ok,
			}, -2)
		configlist = []
		ConfigListScreen.__init__(self, configlist, session=session)
		configlist.append(getConfigListEntry(_("SoftCam config directory"),
			config.plugins.AltSoftcam.camconfig))
		configlist.append(getConfigListEntry(_("SoftCam directory"),
			config.plugins.AltSoftcam.camdir))
		configlist.append(getConfigListEntry(_("Show 'Restart softcam' in extensions menu"),
			config.plugins.AltSoftcam.restartext))
		self["config"].setList(configlist)

	def ok(self):
		msg = [ ]
		if not os.path.exists(config.plugins.AltSoftcam.camconfig.value):
			msg.append("%s " % config.plugins.AltSoftcam.camconfig.value)
		if not os.path.exists(config.plugins.AltSoftcam.camdir.value):
			msg.append("%s " % config.plugins.AltSoftcam.camdir.value)
		if msg == [ ]:
			if config.plugins.AltSoftcam.camconfig.value[-1] == "/":
				config.plugins.AltSoftcam.camconfig.value = \
					config.plugins.AltSoftcam.camconfig.value[:-1]
			if config.plugins.AltSoftcam.camdir.value[-1] == "/":
				config.plugins.AltSoftcam.camdir.value = \
					config.plugins.AltSoftcam.camdir.value[:-1]
			config.plugins.AltSoftcam.save()
			self.close()
		else:
			self.mbox = self.session.open(MessageBox,
				_("Directory %s does not exist!\nPlease set the correct directory path!")
				% msg, MessageBox.TYPE_INFO, timeout = 5)

	def cancel(self, answer = None):
		if answer is None:
			if self["config"].isChanged():
				self.session.openWithCallback(self.cancel, MessageBox,
					_("Really close without saving settings?"))
			else:
				self.close()
		elif answer:
			config.plugins.AltSoftcam.camconfig.cancel()
			config.plugins.AltSoftcam.camdir.cancel()
			self.close()

