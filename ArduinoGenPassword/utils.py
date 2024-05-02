import serial
import time
import hashlib

class ArduinoCommunication:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.ser = serial.Serial(port)
        time.sleep(2)  # Ждем инициализации порта

    def send_phrase(self, phrase):
        self.ser.write(phrase.encode())

    def receive_password(self):
        password = self.ser.readline().decode().strip()
        return password

    def close(self):
        self.ser.close()

def generate_password(phrase):
    hash_object = hashlib.sha512(phrase.encode())
    return hash_object.hexdigest()

# Пример использования
if __name__ == "__main__":
    arduino = ArduinoCommunication()  # Подставьте правильный порт, если он отличается от '/dev/ttyUSB0'

    phrase = input("Введите фразу для генерации пароля: ")
    arduino.send_phrase(phrase)

    password = arduino.receive_password()
    print("Сгенерированный пароль:", password)

    arduino.close()
