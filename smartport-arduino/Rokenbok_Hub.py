#Imports
import serial
import serial.tools.list_ports as list_ports
import threading
import time
from enum import Enum

################################################################################
class Button(Enum):
	FORWARD = 1
	BACK = 2
	LEFT = 3
	RIGHT = 4
	A = 5
	B = 6
	X = 7
	Y = 8
	SLOW = 9
	SHARING = 10

################################################################################
class Rokenbok_Hub:
	"""
	Represents the white hub that the controllers connect to and controls all 
	the trucks and devices. Keeps track of the state of everything. This class
	models that hub and interacts with the real hub via an arduino
	"""
	############################################################################
	def __init__(self, arduino_port=None, baudrate=115200):
		"""
		PURPOSE: creates a new Rokenbok_Hub
		ARGS:
			arduino_port (str): name of the serial port to communicate to the 
								arduino with. If left at 'None' then it will 
								try to find the correct serial port itself.
			baudrate (int): baudrate to communicate to the arduino with
		RETURNS: new instance of a Rokenbok_Hub
		NOTES:
		"""
		#Bytes represting state of controllers that we can change
		self.ctrl_forward = 0
		self.ctrl_back = 0
		self.ctrl_left = 0
		self.ctrl_right = 0
		self.ctrl_a = 0
		self.ctrl_b = 0
		self.ctrl_x = 0
		self.ctrl_y = 0
		self.ctrl_slow = 0
		self.ctrl_sharing = 0
		self.ctrl_sel = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

		#Locks for state variables allowing for multithreading
		self.ctrl_forward_lock = threading.Lock()
		self.ctrl_back_lock = threading.Lock()
		self.ctrl_left_lock = threading.Lock()
		self.ctrl_right_lock = threading.Lock()
		self.ctrl_a_lock = threading.Lock()
		self.ctrl_b_lock = threading.Lock()
		self.ctrl_x_lock = threading.Lock()
		self.ctrl_y_lock = threading.Lock()
		self.ctrl_slow_lock = threading.Lock()
		self.ctrl_sharing_lock = threading.Lock()
		self.ctrl_sel_lock = threading.Lock()

		#Constants used for communicating with arduino and controlling hub
		self.priority = 0
		self.sync_byte = 0b10101010

		#Used to keep track of the actual current selection and not just what
		#we desire because they could possibly become unsynced
		self.cur_sel = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

		#Save baudrate
		self.baudrate = int(baudrate)

		#Find serial port if needed
		self.ser_port = None
		if arduino_port is None:
			for port in list_ports.comports():
				if 'arduino' in port.description.lower() or 'arduino' in port.manufacturer.lower():
					self.ser_port = port.device
					break
			if self.ser_port is None:
				raise ValueError("Can't find serial port for arduino!")
		else:
			self.ser_port = str(arduino_port)

		#Start the serial connection
		self.ser = None
		self.ser_open_time = None
		self.open_serial_con()

		#Start the serial communication thread
		self.ser_thread = None
		self.keep_going = threading.Event()
		self.restart_arduino()

	############################################################################
	def __del__(self):
		"""
		PURPOSE: perform any necessary cleanup
		ARGS: none
		RETURNS: none
		NOTES:
		"""
		self.stop()

	############################################################################
	def open_serial_con(self):
		"""
		PURPOSE: opens the serial connection with the arduino
		ARGS: none
		RETURNS: none
		NOTES: closes the serial port if it is already open and reopens it (this
			   will restart the arduino), blocks until it can open the serial 
			   port
		"""
		#Close port if already opened
		if self.ser and self.ser.isOpen():
			self.ser.close()
		#Open serial port
		is_open = False
		ser_delay = 2
		while not is_open:
			try:
				self.ser = serial.Serial(port=self.ser_port, baudrate=self.baudrate)
			except serial.serialutil.SerialException as e:
				print("Unable to open serial port '%s'! Trying again in %d second(s)..." % (self.ser_port, ser_delay))
				time.sleep(ser_delay)
			else:
				is_open = self.ser.isOpen()
				self.ser_open_time = time.time()

	############################################################################
	def close_serial_con(self):
		"""
		PURPOSE: closes the serial connection to the arduino
		ARGS: none
		RETURNS: none
		NOTES:
		"""
		if self.ser and self.ser.isOpen():
			self.ser.close()
		self.ser = None

	############################################################################
	def sync_state_arduino(self):
		"""
		PURPOSE: keeps the arduino state and our state in sync which allows us 
				 to pass our state onto the hub, thereby controlling the hub
		ARGS: none
		RETURNS: none
		NOTES: should be run in a seperate thread
		"""
		#Wait at least 5 seconds for arduino to reboot after opening the serial
		#port
		while self.keep_going.is_set() and (time.time() - self.ser_open_time) < 5:
			time.sleep(0.2)

		#Have waited for arduino to reboot so we can start sending it our state
		try:
			self.ser.flush()
			while self.keep_going.is_set():
				to_write = [
					self.sync_byte,
					self.sync_byte,
					self.ctrl_forward,
					self.ctrl_back,
					self.ctrl_left,
					self.ctrl_right,
					self.ctrl_a,
					self.ctrl_b,
					self.ctrl_x,
					self.ctrl_y,
					self.ctrl_slow,
					self.ctrl_sharing,
					self.priority
				]
				to_write = bytes(to_write + self.ctrl_sel)
				self.ser.write(to_write)
				#TODO read current selection
				time.sleep(0.04)
		except Exception as e:
			print("'sync_state_arduino' encountered exception '%s': %s" % (type(e), str(e)))

		#We have either finished gracefully or have exited on an exception, in 
		#case of exception exit, make sure keep_going flag is cleared
		self.keep_going.clear()

	############################################################################
	def restart_arduino(self):
		"""
		PURPOSE: restarts the arduino in case it becomes out of sync with us or 
				 the hub and gets stuck
		ARGS: none
		RETURNS: none
		NOTES: blocks until it can open the serial port
		"""
		print("Restarting arduino...")
		self.keep_going.clear()
		if self.ser_thread:
			self.ser_thread.join()
		self.ser_thread = threading.Thread(target=self.sync_state_arduino)
		self.keep_going.set()

		self.close_serial_con()
		self.open_serial_con()

		self.ser_thread.start()

	############################################################################
	def stop(self):
		"""
		PURPOSE: stops the thread and closes the serial conneciton, used in 
				 preperation to delete object
		ARGS: none
		RETURNS: none
		NOTES:
		"""
		#Release all buttons
		self.ctrl_forward = 0
		self.ctrl_back = 0
		self.ctrl_left = 0
		self.ctrl_right = 0
		self.ctrl_a = 0
		self.ctrl_b = 0
		self.ctrl_x = 0
		self.ctrl_y = 0
		self.ctrl_slow = 0
		self.ctrl_sharing = 0
		self.ctrl_sel = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

		#Give time for buttons to take effect
		time.sleep(0.5)

		#Stop thread
		self.keep_going.clear()
		if self.ser_thread:
			self.ser_thread.join()

		#Close serial connection
		self.close_serial_con()

	############################################################################
	def cmd(self, button, player, press=True):
		"""
		PURPOSE: performs a command such as pressing or releasing a button on 
				 controller
		ARGS:
			button (Button): the button to press or release
			player (int): the player to perform the command (1-8)
			press (bool): True to press the button, False to release it
		RETURNS: none
		NOTES: if an invalid button is given it will be ignored and nothing 
			   will happen. If an invalid player is given it will be ignored 
			   and nothing will happen
		"""
		if player < 1 or player > 8:
			return
		player -= 1

		mask = 1 << player
		if not press:
			if player == 0:
				mask = 0b11111110
			elif player == 1:
				mask = 0b11111101
			elif player == 2:
				mask = 0b11111011
			elif player == 3:
				mask = 0b11110111
			elif player == 4:
				mask = 0b11101111
			elif player == 5:
				mask = 0b11011111
			elif player == 6:
				mask = 0b10111111
			else:
				mask = 0b01111111

		if button == Button.FORWARD:
			self.ctrl_forward_lock.acquire()
			if press:
				self.ctrl_forward |= mask
			else:
				self.ctrl_forward &= mask
			self.ctrl_forward_lock.release()
		elif button == Button.BACK:
			self.ctrl_back_lock.acquire()
			if press:
				self.ctrl_back |= mask
			else:
				self.ctrl_back &= mask
			self.ctrl_back_lock.release()
		elif button == Button.LEFT:
			self.ctrl_left_lock.acquire()
			if press:
				self.ctrl_left |= mask
			else:
				self.ctrl_left &= mask
			self.ctrl_left_lock.release()
		elif button == Button.RIGHT:
			self.ctrl_right_lock.acquire()
			if press:
				self.ctrl_right |= mask
			else:
				self.ctrl_right &= mask
			self.ctrl_right_lock.release()
		elif button == Button.A:
			self.ctrl_a_lock.acquire()
			if press:
				self.ctrl_a |= mask
			else:
				self.ctrl_a &= mask
			self.ctrl_a_lock.release()
		elif button == Button.B:
			self.ctrl_b_lock.acquire()
			if press:
				self.ctrl_b |= mask
			else:
				self.ctrl_b &= mask
			self.ctrl_b_lock.release()
		elif button == Button.X:
			self.ctrl_x_lock.acquire()
			if press:
				self.ctrl_x |= mask
			else:
				self.ctrl_x &= mask
			self.ctrl_x_lock.release()
		elif button == Button.Y:
			self.ctrl_y_lock.acquire()
			if press:
				self.ctrl_y |= mask
			else:
				self.ctrl_y &= mask
			self.ctrl_y_lock.release()
		elif button == Button.SLOW:
			self.ctrl_slow_lock.acquire()
			if press:
				self.ctrl_slow |= mask
			else:
				self.ctrl_slow &= mask
			self.ctrl_slow_lock.release()
		elif button == Button.SHARING:
			self.ctrl_sharing_lock.acquire()
			if press:
				self.ctrl_sharing |= mask
			else:
				self.ctrl_sharing &= mask
			self.ctrl_sharing_lock.release()

	############################################################################
	def change_sel(self, player, des_sel):
		"""
		PURPOSE: changes the selection of a player
		ARGS:
			player (int): player to change selection of (1-8)
			des_sel (int): car to select (1-8)
		RETURNS: (bool) True if able to change, False if not
		NOTES: will return False someone already has that car selected 
			   (including the current player), if an invalid player number is 
			   given it will ignore it and return False, if an invalid selection 
			   number is given the that player will change its selection to 
			   nothing giving up his current car
		"""
		if player < 1 or player > 8:
			return False
		player -= 1

		if des_sel < 1 or des_sel > 8:
			self.ctrl_sel_lock.acquire()
			self.ctrl_sel[player] = 0xFF
			self.ctrl_sel_lock.release()
			return True

		des_sel -= 1
		if des_sel in self.ctrl_sel:
			return False
		else:
			self.ctrl_sel_lock.acquire()
			self.ctrl_sel[player] = des_sel
			self.ctrl_sel_lock.release()
		return True

	############################################################################
	def get_sels(self):
		"""
		PURPOSE: gets the current selection for all players
		ARGS: none
		RETURNS: (list, list) list of current selections according to the 
				 hub and list of desired selections according to us
		NOTES: index n = player n + 1 and selection n is n + 1 on remote, 0xFF 
			   is no selection
		"""
		return (self.cur_sel, self.ctrl_sel)

	############################################################################

################################################################################
if __name__ == "__main__":
	print("Waiting for arduino to reboot")
	rh = Rokenbok_Hub()
	time.sleep(6)
	print("Should be running...")

	try:
		while True:
			rh.change_sel(1, 3)
			rh.cmd(Button.BACK, 1, False)
			rh.cmd(Button.FORWARD, 1, True)
			time.sleep(5)
			rh.cmd(Button.FORWARD, 1, False)
			rh.cmd(Button.BACK, 1, True)
			time.sleep(5)
	except KeyboardInterrupt as e:
		pass

	print("Stopping...")
	rh.stop()







