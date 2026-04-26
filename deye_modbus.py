
import socket
import time
import paho.mqtt.client as mqtt

''' SUN-3.6/5/6/7/7.6/8/10K-SG05LP1-EU
registers:
  186: dc/pv1/power
  187: dc/pv2/power
  109: dc/pv1/voltage
  111: dc/pv2/voltage
  110: dc/pv1/current
  112: dc/pv2/current
  108: day_energy
  96: total_energy
  166: micro_inverter_power
  70: battery/daily_charge
  71: battery/daily_discharge
  72: battery/total_charge
  74: battery/total_discharge
  189: battery/status
  190: battery/power
  183: battery/voltage
  184: battery/soc
  191: battery/current
  182: battery/temperature
  169: ac/total_grid_power
  175: ac/total_power
  150: ac/l1/voltage
  151: ac/l2/voltage
  164: ac/l1/current
  165: ac/l2/current
  173: ac/l1/power
  174: ac/l2/power
  76: ac/daily_energy_bought
  77: ac/daily_energy_sold
  78: ac/total_energy_bought
  81: ac/total_energy_sold
  192: ac/frequency
  90: radiator_temp
  91: ac/temperature
  170: ac/l1/ct/external
  167: ac/l1/ct/internal
  171: ac/l2/ct/external
  168: ac/l2/ct/internal
  # Time of use
  248: timeofuse/enabled
  250: timeofuse/time/1
  251: timeofuse/time/2
  252: timeofuse/time/3
  253: timeofuse/time/4
  254: timeofuse/time/5
  255: timeofuse/time/6
  256: timeofuse/power/1
  257: timeofuse/power/2
  258: timeofuse/power/3
  259: timeofuse/power/4
  260: timeofuse/power/5
  261: timeofuse/power/6
  262: timeofuse/voltage/1
  263: timeofuse/voltage/2
  264: timeofuse/voltage/3
  265: timeofuse/voltage/4
  266: timeofuse/voltage/5
  267: timeofuse/voltage/6
  268: timeofuse/soc/1
  269: timeofuse/soc/2
  270: timeofuse/soc/3
  271: timeofuse/soc/4
  272: timeofuse/soc/5
  273: timeofuse/soc/6
  274: timeofuse/enabled/1
  275: timeofuse/enabled/2
  276: timeofuse/enabled/3
  277: timeofuse/enabled/4
  278: timeofuse/enabled/5
  279: timeofuse/enabled/6
  312: bms/1/charging_voltage
  313: bms/1/discharge_voltage
  314: bms/1/charge_current_limit
  315: bms/1/discharge_current_limit
  316: bms/1/soc
  317: bms/1/voltage
  318: bms/1/current
  319: bms/1/temp
'''

S_ACinU = ''
S_ACGenU = ''
S_ACoutU = ''
S_ACinP = ''
S_ACGenP = ''
S_ACoutP = ''
S_BatT = ''
S_BatU = ''
S_BatSOC = ''
S_PV1P = ''
S_PV2P = ''
S_PV1U = ''
S_PV2U = ''
S_PV1I = ''
S_PV2I = ''
S_PVAllP = ''
S_BatP = ''
S_BatI = ''
S_ACoutF = ''
S_ACinF = ''
S_GreenPower = ''


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


def crc16(data: bytes) -> bytes:
    """Calculates the CRC-16/MODBUS for a given byte string."""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    # Return as little-endian (low byte, then high byte)
    return crc.to_bytes(2, byteorder='little')


def to_signed(unsigned_val, bits):
    # Check if the highest bit (sign bit) is set
    if unsigned_val >= (1 << (bits - 1)):
        return unsigned_val - (1 << bits)
    return unsigned_val


def make_request():

    modbus_start_address = 150
    mbsa = modbus_start_address.to_bytes(2, byteorder='big')
    modbus_num_registers = 45
    mbnr = modbus_num_registers.to_bytes(2, byteorder='big')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        data_to_send = bytearray([0x01, 0x03]) # in hex
        data_to_send = data_to_send + mbsa + mbnr # in hex
        crc = crc16(data_to_send)
        data_to_send = data_to_send + crc
        #print(f"data_to_send: {data_to_send.hex()}")
        client_socket.connect((HOST, PORT))
        client_socket.sendall(data_to_send)
        data = client_socket.recv(1024)
        client_socket.close()
    #print(f"Received from server: {data}")
    '''i = 3
    tempstr = ''
    while (i<150):
        m = i
        n = i + 2
        num = int.from_bytes(data[m:n], byteorder='big') 
        tempstr = tempstr + str(num)+' '
        i = i + 2
    print(tempstr)'''


    global S_ACinU 
    n = (150-modbus_start_address)*2
    ACinU = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACinU = str(round(ACinU*0.1, 1))
    print('ACinU '+S_ACinU)
    global S_ACGenU 
    n = (151-modbus_start_address)*2
    ACGenU = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACGenU = str(round(ACGenU*0.1, 1))
    print('ACGenU '+S_ACGenU)
    global S_ACoutU
    n = (157-modbus_start_address)*2
    ACoutU = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACoutU = str(round(ACoutU*0.1, 1))
    print('ACoutU '+S_ACoutU)
    global S_ACinP
    n = (167-modbus_start_address)*2
    ACinP = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACinP = str(round(ACinP*1, 1))
    print('ACinP '+S_ACinP)
    global S_ACGenP
    n = (168-modbus_start_address)*2
    ACGenP = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACGenP = str(round(ACGenP*1, 1))
    print('ACGenP '+S_ACGenP)
    global S_ACoutP
    n = (178-modbus_start_address)*2
    ACoutP = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACoutP = str(round(ACoutP*1, 1))
    print('ACoutP '+S_ACoutP)
    global S_GreenPower
    GreenPower = ACoutP - ACinP
    S_GreenPower = str(round(GreenPower*1, 1))
    print('GreenPower '+S_GreenPower)
    global S_BatT
    n = (182-modbus_start_address)*2
    BatT = int.from_bytes(data[n+3:n+5], byteorder='big') - 1000
    S_BatT = str(round(BatT*0.1, 1))
    print('BatT '+S_BatT)
    global S_BatU
    n = (183-modbus_start_address)*2
    BatU = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_BatU = str(round(BatU*0.01, 1))
    print('BatU '+S_BatU)
    global S_BatSOC
    n = (184-modbus_start_address)*2
    BatSOC = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_BatSOC = str(round(BatSOC*1, 1))
    print('BatSOC '+S_BatSOC)
    global S_PV1P
    n = (186-modbus_start_address)*2
    PV1P = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV1P = str(round(PV1P*1, 1))
    print('PV1P '+S_PV1P)
    global S_PV2P
    n = (187-modbus_start_address)*2
    PV2P = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV2P = str(round(PV2P*1, 1))
    print('PV2P '+S_PV2P)
    global S_PVAllP
    PVAllP = PV1P + PV2P
    S_PVAllP = str(round(PVAllP*1, 1))
    print('PVAllP '+S_PVAllP)
    global S_BatP
    n = (190-modbus_start_address)*2
    BatP = to_signed(int.from_bytes(data[n+3:n+5], byteorder='big'),16)*(-1)
    S_BatP = str(round(BatP*1, 1))
    print('BatP '+S_BatP)
    global S_BatI
    n = (191-modbus_start_address)*2
    BatI = to_signed(int.from_bytes(data[n+3:n+5], byteorder='big'),16)*(-1)
    S_BatI = str(round(BatI*0.01, 1))
    print('BatI '+S_BatI)
    global S_ACoutF
    n = (192-modbus_start_address)*2
    ACoutF = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACoutF = str(round(ACoutF*0.01, 1))
    print('ACoutF '+S_ACoutF)
    global S_ACinF
    n = (193-modbus_start_address)*2
    ACinF = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_ACinF = str(round(ACinF*0.01, 1))
    print('ACinF '+S_ACinF)

    modbus_start_address = 109
    mbsa = modbus_start_address.to_bytes(2, byteorder='big')
    modbus_num_registers = 4
    mbnr = modbus_num_registers.to_bytes(2, byteorder='big')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        data_to_send = bytearray([0x01, 0x03]) # in hex
        data_to_send = data_to_send + mbsa + mbnr # in hex
        crc = crc16(data_to_send)
        data_to_send = data_to_send + crc
        #print(f"data_to_send: {data_to_send.hex()}")
        client_socket.connect((HOST, PORT))
        client_socket.sendall(data_to_send)
        data = client_socket.recv(1024)
        client_socket.close()
    
    global S_PV1U 
    n = (109-modbus_start_address)*2
    PV1U = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV1U = str(round(PV1U*0.1, 1))
    print('PV1U '+S_PV1U)
    global S_PV1I 
    n = (110-modbus_start_address)*2
    PV1I = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV1I = str(round(PV1I*0.1, 1))
    print('PV1I '+S_PV1I)
    global S_PV2U
    n = (111-modbus_start_address)*2
    PV2U = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV2U = str(round(PV2U*0.1, 1))
    print('PV2U '+S_PV2U)
    global S_PV2I
    n = (112-modbus_start_address)*2
    PV2I = int.from_bytes(data[n+3:n+5], byteorder='big')
    S_PV2I = str(round(PV2I*1, 1))
    print('PV2I '+S_PV2I)
   



# Modbus server configuration
HOST = '192.168.0.XX'  # The server's IP address
PORT = 8899        # The port used by the server
req_count = 0

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.username_pw_set(username="login",password="password")
print("Connecting...")
mqttc.connect("192.168.0.XX", 1883, 10) # the mqtt server IP address

# Запускать запрос каждые 2 секунды
while True:
    req_count = req_count + 1
    print(f"req_count: {req_count}")
    make_request()
    time.sleep(2) # Задержка в секундах

    mqttc.publish("deye_6kw/ACinU", S_ACinU)
    mqttc.publish("deye_6kw/ACGenU", S_ACGenU)
    mqttc.publish("deye_6kw/ACoutU", S_ACoutU)
    mqttc.publish("deye_6kw/ACinP", S_ACinP)
    mqttc.publish("deye_6kw/ACGenP", S_ACGenP)
    mqttc.publish("deye_6kw/ACoutP", S_ACoutP)
    mqttc.publish("deye_6kw/BatT", S_BatT)
    mqttc.publish("deye_6kw/BatU", S_BatU)
    mqttc.publish("deye_6kw/BatSOC", S_BatSOC)
    mqttc.publish("deye_6kw/PV1P", S_PV1P)
    mqttc.publish("deye_6kw/PV1U", S_PV1U)
    mqttc.publish("deye_6kw/PV1I", S_PV1I)
    mqttc.publish("deye_6kw/PV2P", S_PV2P)
    mqttc.publish("deye_6kw/PV2U", S_PV2U)
    mqttc.publish("deye_6kw/PV2I", S_PV2I)
    mqttc.publish("deye_6kw/BatP", S_BatP)
    mqttc.publish("deye_6kw/BatI", S_BatI)
    mqttc.publish("deye_6kw/ACoutF", S_ACoutF)
    mqttc.publish("deye_6kw/ACinF", S_ACinF)
    mqttc.publish("deye_6kw/GreenPower", S_GreenPower)
    mqttc.publish("deye_6kw/PVAllP", S_PVAllP)
