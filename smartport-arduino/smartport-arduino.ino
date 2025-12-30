enum UPDATE_STATE {
  START = 0,
  BEGIN_SYNC,
  END_SYNC,
  UPDATE_SEL_BUT,
  UPDATE_LEFT_TRIG,
  UPDATE_SHARING,
  RESERVED_1,
  IS16SEL,
  UPDATE_FORWARD,
  UPDATE_BACK,
  UPDATE_RIGHT,
  UPDATE_LEFT,
  UPDATE_A,
  UPDATE_B,
  UPDATE_X,
  UPDATE_Y,
  RESERVED_2,
  RESERVED_3,
  UPDATE_RIGHT_TRIG,
  UPDATE_SPARE,
  UPDATE_PRIORITY,
  UPDATE_SEL_0,
  UPDATE_SEL_1,
  UPDATE_SEL_2,
  UPDATE_SEL_3,
  UPDATE_SEL_4,
  UPDATE_SEL_5,
  UPDATE_SEL_6,
  UPDATE_SEL_7,
  END_UPDATE_SEL
};

const byte slave_ready_pin = 7;
const byte sync_byte = 0b10101010;

byte des_forward = 0; //1 to activate
byte des_back = 0;    //1 to activate
byte des_left = 0;    //1 to activate
byte des_right = 0;   //1 to activate
byte des_a = 0;       //1 to activate
byte des_b = 0;       //1 to activate
byte des_x = 0;       //1 to activate
byte des_y = 0;       //1 to activate
byte des_slow = 0;    //1 to activate
byte des_sharing = 0; //1 to allow sharing
byte des_priority = 0; //1 to allow sharing
byte des_sel[8];

byte cur_forward = 0;
byte cur_back = 0;
byte cur_left = 0;
byte cur_right = 0;
byte cur_a = 0;
byte cur_b = 0;
byte cur_x = 0;
byte cur_y = 0;
byte cur_slow = 0;
byte cur_sharing = 0;
byte cur_priority = 0;
byte cur_sel[8];

UPDATE_STATE cur_state = START;

byte handle_msg(byte rec_data);

void setup()
{
  //Used to communicate to host pc
  Serial.begin(115200);
  Serial.setTimeout(1000);
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  //Initialize variables
  for (int ii = 0; ii < 8; ii++) {
    des_sel[ii] = 0xFF;
    cur_sel[ii] = 0xFF;
  }

  //We are the slave in SPI
  pinMode(MISO, OUTPUT);
  //pinMode(MOSI, INPUT);
  pinMode(slave_ready_pin, OUTPUT);

  //Setup SPI
  SPCR |= _BV(SPE);   //turn on SPI in slave mode
  SPCR |= _BV(SPIE);  //turn on interrupts
}

void loop()
{
  //Wait to receive sync bytes
  byte sync_count = 0;
  while (sync_count < 2) {
    if (Serial.available()) {
      if (Serial.read() == sync_byte) {
        sync_count++;
      } else {
        sync_count = 0;
      }
    }
  }
  
  //Wait until serial buffer has all of the bytes
  //we are expecting to read
  while (Serial.available() < 19) {
    //Do nothing
  }
  
  //The serial buffer now has all the bytes we need to read
  des_forward = Serial.read();
  des_back = Serial.read();
  des_left = Serial.read();
  des_right = Serial.read();
  des_a = Serial.read();
  des_b = Serial.read();
  des_x = Serial.read();
  des_y = Serial.read();
  des_slow = Serial.read();
  des_sharing = Serial.read();
  des_priority = Serial.read();
  Serial.readBytes(des_sel, 8);
  /*
  //Send a response
  //Send sync bytes (forward and backward most likely wont
  //be pressed at the same time
  Serial.write(sync_byte);
  Serial.write(sync_byte);
  //Send current state to host pc
  Serial.write(cur_forward);
  Serial.write(cur_back);
  Serial.write(cur_left);
  Serial.write(cur_right);
  Serial.write(cur_a);
  Serial.write(cur_b);
  Serial.write(cur_x);
  Serial.write(cur_y);
  Serial.write(cur_slow);
  Serial.write(cur_sharing);
  Serial.write(cur_sel, 8);
  */
  if (Serial.available() > 1000) {
    digitalWrite(13, HIGH);
  }
}

byte handle_msg(byte rec_data)
{
  switch (cur_state) {
    case START:
      switch (rec_data) {
        case 0xC6:
          cur_state = BEGIN_SYNC;
          return 0x81;
          break;
        case 0xC3:
          cur_state = UPDATE_SEL_BUT;
          return 0x80;
          break;
        case 0xC4:
          cur_state = UPDATE_SEL_0;
          return 0x80;
          break;
        default:
          cur_state = START;
          return 0x00;
          break;
      }
      break;
    case BEGIN_SYNC:
      cur_state = END_SYNC;
      return 0x0D;
      break;
    case END_SYNC:
      cur_state = START;
      return 0x00;
      break;
    case UPDATE_SEL_BUT:
      cur_state = UPDATE_LEFT_TRIG;
      //Don't need anyone to use select button we will
      //select the number in a different portion
      return 0;
      break;
    case UPDATE_LEFT_TRIG:
      cur_state = UPDATE_SHARING;
      //Don't need left trigger because that snaps back
      //to the last selected vehicle, but again we will
      //handle that in a different portion
      return 0;
      break;
    case UPDATE_SHARING:
      cur_state = RESERVED_1;
      cur_sharing = rec_data;
      return des_sharing;
      break;
    case RESERVED_1:
      //Just send back what you get
      cur_state = IS16SEL;
      return rec_data;
      break;
    case IS16SEL:
      //Don't know what this is, send back all ones
      cur_state = UPDATE_FORWARD;
      return 0xFF;
      break;
    case UPDATE_FORWARD:
      cur_state = UPDATE_BACK;
      cur_forward = rec_data;
      return des_forward;
      break;
    case UPDATE_BACK:
      cur_state = UPDATE_RIGHT;
      cur_back = rec_data;
      return des_back;
      break;
    case UPDATE_RIGHT:
      cur_state = UPDATE_LEFT;
      cur_right = rec_data;
      return des_right;
      break;
    case UPDATE_LEFT:
      cur_state = UPDATE_A;
      cur_left = rec_data;
      return des_left;
      break;
    case UPDATE_A:
      cur_state = UPDATE_B;
      cur_a = rec_data;
      return des_a;
      break;
    case UPDATE_B:
      cur_state = UPDATE_X;
      cur_b = rec_data;
      return des_b;
      break;
    case UPDATE_X:
      cur_state = UPDATE_Y;
      cur_x = rec_data;
      return des_x;
      break;
    case UPDATE_Y:
      cur_state = RESERVED_2;
      cur_y = rec_data;
      return des_y;
      break;
    case RESERVED_2:
      cur_state = RESERVED_3;
      return rec_data;
      break;
    case RESERVED_3:
      cur_state = UPDATE_RIGHT_TRIG;
      return rec_data;
      break;
    case UPDATE_RIGHT_TRIG:
      cur_state = UPDATE_SPARE;
      cur_slow = rec_data;
      return des_slow;
      break;
    case UPDATE_SPARE:
      cur_state = UPDATE_PRIORITY;
      return rec_data;
      break;
    case UPDATE_PRIORITY:
      cur_state = START;
      cur_priority = rec_data;
      return des_priority;
      break;
    case UPDATE_SEL_0:
      cur_state = UPDATE_SEL_1;
      cur_sel[0] = rec_data;
      return des_sel[0];
      break;
    case UPDATE_SEL_1:
      cur_state = UPDATE_SEL_2;
      cur_sel[1] = rec_data;
      return des_sel[1];
      break;
    case UPDATE_SEL_2:
      cur_state = UPDATE_SEL_3;
      cur_sel[2] = rec_data;
      return des_sel[2];
      break;
    case UPDATE_SEL_3:
      cur_state = UPDATE_SEL_4;
      cur_sel[3] = rec_data;
      return des_sel[3];
      break;
    case UPDATE_SEL_4:
      cur_state = UPDATE_SEL_5;
      cur_sel[4] = rec_data;
      return des_sel[4];
      break;
    case UPDATE_SEL_5:
      cur_state = UPDATE_SEL_6;
      cur_sel[5] = rec_data;
      return des_sel[5];
      break;
    case UPDATE_SEL_6:
      cur_state = UPDATE_SEL_7;
      cur_sel[6] = rec_data;
      return des_sel[6];
      break;
    case UPDATE_SEL_7:
      cur_state = END_UPDATE_SEL;
      cur_sel[7] = rec_data;
      return des_sel[7];
      break;
    case END_UPDATE_SEL:
      cur_state = START;
      return 0x00;
      break;
    default:
      cur_state = START;
      return 0x00;
      break;
  }
}

ISR(SPI_STC_vect)
{
  //Indicate we are not ready for a new byte yet
  digitalWrite(slave_ready_pin, HIGH);
  byte rec_data = SPDR;
  SPDR = handle_msg(rec_data);
  //Inidcate we are now ready for a new byte
  digitalWrite(slave_ready_pin, LOW);
}
