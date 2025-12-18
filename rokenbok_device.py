import serial
from enum import Enum
import serial.tools.list_ports as list_ports
import threading
import time

class Commands:
    class DeviceCommand(Enum):
        """Enum representing commands associated with a Rokenbok device."""
        PRESS = 0
        RELEASE = 1
        EDIT = 2
        ENABLE = 3
        DISABLE = 4
        RESET = 5

    class ControllerCommand(Enum):
        """Enum representing functions associated with a controller."""
        SELECT = 0
        LEFT_TRIGGER = 1
        SHARE_SWITCH = 2
        IS_16_SEL = 3
        DPAD_UP = 4
        DPAD_DOWN = 5
        DPAD_RIGHT = 6
        DPAD_LEFT = 7
        A = 8
        B = 9
        X = 10
        Y = 11
        RIGHT_TRIGGER = 12
        SELECT_UP = 13
        SELECT_DOWN = 14

    class ControllerIdentifier(Enum):
        """Enum representing identifiers for physical and virtual controllers."""
        PHYSICAL_CONTROLLER_1 = 0
        PHYSICAL_CONTROLLER_2 = 1
        PHYSICAL_CONTROLLER_3 = 2
        PHYSICAL_CONTROLLER_4 = 3
        VIRTUAL_CONTROLLER_1 = 4
        VIRTUAL_CONTROLLER_2 = 5
        VIRTUAL_CONTROLLER_3 = 6
        VIRTUAL_CONTROLLER_4 = 7

    class VehicleKey(Enum):
        """Enum representing vehicles for selection."""
        SELECT_KEY_1 = 0
        SELECT_KEY_2 = 1
        SELECT_KEY_3 = 2
        SELECT_KEY_4 = 3
        SELECT_KEY_5 = 4
        SELECT_KEY_6 = 5
        SELECT_KEY_7 = 6
        SELECT_KEY_8 = 7
        SELECT_KEY_9 = 8
        SELECT_KEY_10 = 9
        SELECT_KEY_11 = 10
        SELECT_KEY_12 = 11
        SELECT_KEY_13 = 12
        SELECT_KEY_14 = 13
        SELECT_KEY_15 = 14
        NO_SELECTION = 15

class SmartPortArduino:
	"""
	Represents the white hub that the controllers connect to and controls all 
	the trucks and devices. Keeps track of the state of everything. This class
	models that hub and interacts with the real hub via an arduino
	"""
	def __init__(self, serial_device=None):
		"""
		PURPOSE: creates a new Rokenbok_Hub
		ARGS:
			serial_device (str): name of the serial port to communicate to the 
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
		self.baudrate = 115200

		#Find serial port if needed
		self.ser_port = None
		if serial_device is None:
			for port in list_ports.comports():
				if 'arduino' in port.description.lower() or 'arduino' in port.manufacturer.lower():
					self.ser_port = port.device
					break
			if self.ser_port is None:
				raise ValueError("Can't find serial port for arduino!")
		else:
			self.ser_port = str(serial_device)

		#Start the serial connection
		self.ser = None
		self.ser_open_time = None
		self.open_serial_con()

		#Start the serial communication thread
		self.ser_thread = None
		self.keep_going = threading.Event()
		self.restart_arduino()

	def __del__(self):
		"""
		PURPOSE: perform any necessary cleanup
		ARGS: none
		RETURNS: none
		NOTES:
		"""
		self.stop()

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

	def cmd(self, button, player, press=True):
		"""
		PURPOSE: performs a command such as pressing or releasing a button on 
				 controller
		ARGS:
			button (ControllerCommand): the button to press or release
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

		if button == Commands.ControllerCommand.DPAD_UP:
			self.ctrl_forward_lock.acquire()
			if press:
				self.ctrl_forward |= mask
			else:
				self.ctrl_forward &= mask
			self.ctrl_forward_lock.release()
		elif button == Commands.ControllerCommand.DPAD_DOWN:
			self.ctrl_back_lock.acquire()
			if press:
				self.ctrl_back |= mask
			else:
				self.ctrl_back &= mask
			self.ctrl_back_lock.release()
		elif button == Commands.ControllerCommand.DPAD_LEFT:
			self.ctrl_left_lock.acquire()
			if press:
				self.ctrl_left |= mask
			else:
				self.ctrl_left &= mask
			self.ctrl_left_lock.release()
		elif button == Commands.ControllerCommand.DPAD_RIGHT:
			self.ctrl_right_lock.acquire()
			if press:
				self.ctrl_right |= mask
			else:
				self.ctrl_right &= mask
			self.ctrl_right_lock.release()
		elif button == Commands.ControllerCommand.A:
			self.ctrl_a_lock.acquire()
			if press:
				self.ctrl_a |= mask
			else:
				self.ctrl_a &= mask
			self.ctrl_a_lock.release()
		elif button == Commands.ControllerCommand.B:
			self.ctrl_b_lock.acquire()
			if press:
				self.ctrl_b |= mask
			else:
				self.ctrl_b &= mask
			self.ctrl_b_lock.release()
		elif button == Commands.ControllerCommand.X:
			self.ctrl_x_lock.acquire()
			if press:
				self.ctrl_x |= mask
			else:
				self.ctrl_x &= mask
			self.ctrl_x_lock.release()
		elif button == Commands.ControllerCommand.Y:
			self.ctrl_y_lock.acquire()
			if press:
				self.ctrl_y |= mask
			else:
				self.ctrl_y &= mask
			self.ctrl_y_lock.release()
		elif button == Commands.ControllerCommand.RIGHT_TRIGGER:
			self.ctrl_slow_lock.acquire()
			if press:
				self.ctrl_slow |= mask
			else:
				self.ctrl_slow &= mask
			self.ctrl_slow_lock.release()
		elif button == Commands.ControllerCommand.SHARE_SWITCH:
			self.ctrl_sharing_lock.acquire()
			if press:
				self.ctrl_sharing |= mask
			else:
				self.ctrl_sharing &= mask
			self.ctrl_sharing_lock.release()

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

if __name__ == "__main__":
	print("Waiting for arduino to reboot")
	rh = SmartPortArduino('COM3')
	time.sleep(6)
	print("Should be running...")

	try:
		while True:
			rh.change_sel(1, 7)
			rh.cmd(Commands.ControllerCommand.DPAD_DOWN, 1, False)
			rh.cmd(Commands.ControllerCommand.DPAD_UP, 1, True)
			time.sleep(5)
			rh.cmd(Commands.ControllerCommand.DPAD_UP, 1, False)
			rh.cmd(Commands.ControllerCommand.DPAD_DOWN, 1, True)
			time.sleep(5)
	except KeyboardInterrupt as e:
		pass

	print("Stopping...")
	rh.stop()
