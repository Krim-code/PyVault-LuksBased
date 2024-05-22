#include <Arduino.h>
#include <SHA512.h>

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Ждем соединения
  }
}

void loop() {
  if (Serial.available()) {
    String phrase = Serial.readString(); // Получаем фразу из Python
    String password = generatePassword(phrase); // Генерируем пароль на основе фразы
    Serial.println(password); // Отправляем пароль обратно в Python
  }
}

String generatePassword(String phrase) {
  // Создаем объект хэша SHA-512
  SHA512 sha512;
  uint8_t hash[64]; // 64 байта для хэша
  // Рассчитываем хэш для введенной фразы
  sha512.reset();
  sha512.update(phrase.c_str(), phrase.length());
  sha512.finalize(hash, sizeof(hash)); // Получаем хэш
  // Получаем хэш в виде строки
  String result = "";
  for (int i = 0; i < sizeof(hash); i++) {
    result += String(hash[i], HEX);
  }
  return result;
}