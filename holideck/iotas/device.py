#!/usr/bin/python
#
"""
Class implementation for devices for Holiday by MooresCloud
Right now we understand four different classes of devices:
	GPIO by Linux
	Light by MooresCloud
	Holiday by MooresCloud
	EngineRoom Chippendale by MooresCloud
	Hue by Philips
	WeMo by Belkin

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""

__author__ = 'Mark Pesce'
__version__ = '0.01-dev'
__license__ = 'MIT'

import urllib2, json, socket, os.path, os, subprocess, math, time

class GPIO:
	def __init__(self, number, direction):
		"""The GPIO port number is passed as number,
		   The direction is a boolean, where True = out, False = in"""
		self.number = number
		self.base = "/sys/class/gpio/gpio%s/" % number
		self.create()
		self.direction = direction  # True = out, False = in
		self.set_direction(self.direction)
		#print self.base
		return
	
	def get_info(self):
		resp= {}
		resp['device_type'] = 'gpio'
		resp['num'] = self.number
		resp['direction'] = self.get_direction()
		resp['value'] = self.value()
		return resp
	
	def create(self):
		"""Instance the GPIO port in the OS.
		   If it already exists, don't do anything."""
		if os.path.exists("/sys/class/gpio/gpio%s" % self.number):
			return
		else:
			f = open("/sys/class/gpio/export", "w")
			f.write("%s" % self.number)
			f.close()
		
	def get_direction(self):
		dirname = self.base + "direction"
		f = open(dirname, "r")
		d = f.read()
		d = d[:-1]	# Remove line feed thingy maybe
		#print "Direction is %s" % d
		if (d == "in"):
			return False
		else:
			return True

	def set_direction(self, inout):
		dirname = self.base + "direction"
		f = open(dirname, "w")
		if inout == True:
			f.write("out")
		else:
			f.write("in")
		f.close()
		self.direction = inout

	def on(self):
		"""Raises error if direction is not out"""
		if self.direction == True:
			dirname = self.base + "value"
			f = open(dirname, "w")
			f.write("1")
			f.close()
			#cmd = """echo "1" > %s""" % dirname
			#print cmd
			#os.system(cmd)
		else:
			raise Error("Invalid direction")
		return
		
	def off(self):
		"""Raises error if direction is not out"""
		if self.direction == True:
			dirname = self.base + "value"
			f = open(dirname, "w")
			f.write("0")
			f.close()
		else:
			raise Error("Invalid direction")
		return
	
	def value(self):
		dirname = self.base + "value"
		fd = open(dirname, "r")
		val = fd.read()
		fd.close()
		#print "value read is %s" % val
		if val[:1] == "1":
			return True
		else:
			return False

class Holiday:
	def __init__(self, address):
		self.address = address
		self.numleds = 50
		self.pipename = "/run/pipelights.fifo"
		self.leds = []			# Array of LED values. This may actually exist elsewhere eventually.
		try:
			self.pipe = open(self.pipename,"w+")
		except:
			print "Couldn't open the pipe, there's gonna be trouble!"
		ln = 0
		while (ln < self.numleds):
			self.leds.append([0x00, 0x00, 0x00])	# Create and clear an array of RGB LED values
			ln = ln + 1
		return

	def get_devices(self):
		l = { "device_type": "Holiday", "number": 50, "version": 0.1 }
		return [ l ]

	def get_led_value(self, lednum):
		if lednum < self.numleds:
			return self.leds[lednum]
		else:
			raise IndexError("Illegal LED number")


	def set_led_value(self, lednum, value):
		if lednum < self.numleds:
			self.leds[lednum][0] = value[0]
			self.leds[lednum][1] = value[1]
			self.leds[lednum][2] = value[2]
			self.render()
			#print self.leds
			return self.leds[lednum]
		else:
			raise IndexError("Illegal LED number")

	def get_light_values(self):
		return { "lights": self.leds }		

	def set_light_values(self, value):
		ln = 0
		while (ln < self.numleds):
			self.leds[ln][0] = value[0]	# White please
			self.leds[ln][1] = value[1]
			self.leds[ln][2] = value[2]
			ln = ln + 1
		self.render()
		return { "lights": self.leds }	

	def do_setvalues(self, values):
		ln = 0
		while (ln < self.numleds):
			self.leds[ln][0] = values[ln][0]	# White please
			self.leds[ln][1] = values[ln][1]
			self.leds[ln][2] = values[ln][2]
			ln = ln + 1
		self.render()
		return { "lights": self.leds }			

	def gradient(self, begin, end, steps):
		"""Do it the new-fashioned way"""
		steps = float(steps)
		base = [0.0,0.0,0.0]
		base[0] = begin[0]
		base[1] = begin[1]
		base[2] = begin[2]

		incr = [0.0,0.0,0.0]
		incr[0] = float((end[0]-begin[0]) / steps)
		incr[1] = float((end[1]-begin[1]) / steps)
		incr[2] = float((end[2]-begin[2]) / steps)
		print "r-incr %f g-incr %f b-incr %f" % (incr[0],incr[1],incr[2])

		s = 0.0
		gr = [0,0,0]
		while (s < steps):
			gr[0] = int(base[0] + (incr[0] * s))
			gr[1] = int(base[1] + (incr[1] * s))
			gr[2] = int(base[2] + (incr[2] * s))
			self.set_light_values(gr)
			s = s + 1
			time.sleep(.02)
		return { "value": True }

	def nrl(self, data):
		"""Set the NRL team colours based on the passed value"""
		team_num = int(data['team'])
		print "team_num %d" % team_num
		if (team_num < 1) or (team_num > 16):
			return { 'value': False }
		try:
			resp = subprocess.call(['/home/mpesce/sport/nrl', str(team_num)])
		except:
			return { 'value': False }
		return { 'value': True }

	def afl(self, data):
		"""Set the NRL team colours based on the passed value"""
		team_num = int(data['team'])
		if (team_num < 1) or (team_num > 18):
			return { 'value': False }
		try:
			resp = subprocess.call(['/home/mpesce/sport/afl', str(team_num)])
		except:
			return { 'value': False }
		return { 'value': True }

	def render(self):
		"""Render the LED array to the Light"""
		"""This version is safe because it renders to a string in memory"""
		echo = ""
		ln = 0
		while (ln < self.numleds):
			tripval = (self.leds[ln][0] * 65536) + (self.leds[ln][1] * 256) + self.leds[ln][2]
			#echo = echo + "%6X" % tripval + "\\" + "\\" + "x0a"  # magic pixie formatting eh?
			echo = echo + "%6X\n" % tripval
			ln = ln+1
		#print echo
		#os.system("""%s""" % echo)
		self.pipe.write(echo)
		self.pipe.flush()
		#os.system("""%s | /srv/http/cgi-bin/setlights""" % echo)
		return

		
	def on(self):
		return set_light_values([255,255,255])
		
	def off(self):
		return set_light_values([0,0,0])			

class EngineRoom:
	def __init__(self, address):
		self.address = address
		self.numleds = 96
		self.pipename = "/run/pipelights.fifo"
		self.leds = []			# Array of LED values. This may actually exist elsewhere eventually.
		try:
			self.pipe = open(self.pipename,"w+")
		except:
			print "Couldn't open the pipe, there's gonna be trouble!"
		ln = 0
		while (ln < self.numleds):
			self.leds.append([0x00, 0x00, 0x00])	# Create and clear an array of RGB LED values
			ln = ln + 1
		return

	def get_devices(self):
		l = { "device_type": "LEDs", "number": 96, "version": 4.1 }
		return [ l ]

	def get_led_value(self, lednum):
		if lednum < self.numleds:
			return self.leds[lednum]
		else:
			raise IndexError("Illegal LED number")


	def set_led_value(self, lednum, value):
		if lednum < self.numleds:
			self.leds[lednum][0] = value[0]
			self.leds[lednum][1] = value[1]
			self.leds[lednum][2] = value[2]
			self.render()
			#print self.leds
			return self.leds[lednum]
		else:
			raise IndexError("Illegal LED number")

	def get_light_values(self):
		return { "lights": self.leds }		

	def set_light_values(self, value):
		ln = 0
		while (ln < self.numleds):
			self.leds[ln][0] = value[0]	# White please
			self.leds[ln][1] = value[1]
			self.leds[ln][2] = value[2]
			ln = ln + 1
		self.render()
		return { "lights": self.leds }	

	def do_setvalues(self, values):
		ln = 0
		while (ln < self.numleds):
			self.leds[ln][0] = values[ln][0]	# White please
			self.leds[ln][1] = values[ln][1]
			self.leds[ln][2] = values[ln][2]
			ln = ln + 1
		self.render()
		return { "lights": self.leds }			

	def gradient(self, begin, end, steps):
		"""Do it the new-fashioned way"""
		steps = float(steps)
		base = [0.0,0.0,0.0]
		base[0] = begin[0]
		base[1] = begin[1]
		base[2] = begin[2]

		incr = [0.0,0.0,0.0]
		incr[0] = float((end[0]-begin[0]) / steps)
		incr[1] = float((end[1]-begin[1]) / steps)
		incr[2] = float((end[2]-begin[2]) / steps)
		print "r-incr %f g-incr %f b-incr %f" % (incr[0],incr[1],incr[2])

		s = 0.0
		gr = [0,0,0]
		while (s < steps):
			gr[0] = int(base[0] + (incr[0] * s))
			gr[1] = int(base[1] + (incr[1] * s))
			gr[2] = int(base[2] + (incr[2] * s))
			self.set_light_values(gr)
			s = s + 1
			time.sleep(.02)
		return { "value": True }

	def render(self):
		"""Render the LED array to the Light"""
		"""This version is safe because it renders to a string in memory"""
		echo = ""
		ln = 0
		while (ln < self.numleds):
			tripval = (self.leds[ln][0] * 65536) + (self.leds[ln][1] * 256) + self.leds[ln][2]
			#echo = echo + "%6X" % tripval + "\\" + "\\" + "x0a"  # magic pixie formatting eh?
			echo = echo + "%6X\n" % tripval
			ln = ln+1
		#print echo
		#os.system("""%s""" % echo)
		self.pipe.write(echo)
		self.pipe.flush()
		#os.system("""%s | /srv/http/cgi-bin/setlights""" % echo)
		return

		
	def on(self):
		return set_light_values([127,127,127])
		
	def off(self):
		return set_light_values([0,0,0])			

class Device:

	def __init__(self, dev):
		self.dev = dev
		return
		
	def on(self):
		self.dev.on()
		return
	
	def off(self):
		self.dev.off()
		return
		
	def value(self):
		try:
			val = self.dev.value()
		except:
			raise Error("Method does not exist")
		return val
