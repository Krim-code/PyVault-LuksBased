#!/usr/bin/env python3
import os
import subprocess
import shutil
import random
import string
import hashlib
import sys
from ArduinoGenPassword.utils import ArduinoCommunication

class VaultManager:
    def __init__(self, directory="."):
        self.directory = directory

    def prompt_password(self):

        phrase = input("Enter password: ")
        arduino = ArduinoCommunication()  # Подставьте правильный порт, если он отличается от '/dev/ttyUSB0'

        arduino.send_phrase(phrase)

        password = arduino.receive_password()

        arduino.close()
        return password

    def new_vault(self, vault):
        vault_path = os.path.join(self.directory, vault)
        if os.path.exists(vault_path):
            print("File already exists")
            return

        ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        password = self.prompt_password()

        with open(vault_path, 'wb') as f:
            f.truncate(32 * 1024 * 1024)

        subprocess.run(['cryptsetup', '-q', '-d', '-', 'luksFormat', vault_path], input=password.encode())
        self.luks_open(vault_path, ident, password)
        subprocess.run(['sudo', 'mkfs.ext4', '-Fq', '/dev/mapper/' + ident])
        self.luks_close(ident)

    def open_vault(self, vault):
        vault_path = os.path.join(self.directory, vault)
        base = os.path.basename(vault_path)
        if not os.path.exists(vault_path):
            print("Vault file not found in the specified directory")
            return

        if os.path.isdir(os.path.join(self.directory, base)):
            print("There already exists a directory", base)
            return

        ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        newname = "." + base + "-" + ident

        password = self.prompt_password()

        shutil.move(vault_path, os.path.join(self.directory, newname))

        self.luks_open(os.path.join(self.directory, newname), ident, password)
        os.mkdir(os.path.join(self.directory, base))
        subprocess.run(['sudo', 'mount', '/dev/mapper/' + ident, os.path.join(self.directory, base)])
        subprocess.run(['sudo', 'chown', os.getlogin(), os.path.join(self.directory, base)])

    def close_vault(self, vault):
        vault_path = os.path.join(self.directory, vault)
        base = os.path.basename(vault_path)
        if not os.path.isdir(os.path.join(self.directory, base)):
            print("Opened vault directory not found in the specified directory")
            return

        opened = base
        candidates = list(filter(lambda x: x.startswith(f'.{opened}-'), os.listdir(self.directory)))
        
        if len(candidates) > 1:
            print("Multiple vaults with the same name are opened")
            return

        ident = candidates[0].split('-')[1]
        if self.disk_in_use(opened):
            print("Some processes are still using files on the disk. Attempting to kill them.")
            self.kill_processes(opened)
            # Проверяем еще раз, используют ли еще процессы диск
            if self.disk_in_use(opened):
                print("Some processes are still using files on the disk. Please close them first.")
                return

        self.luks_close(ident)
        subprocess.run(['sudo', 'umount' , os.path.join(self.directory, opened)])
        # Удаляем устройство с диска
        subprocess.run(['sudo', 'dmsetup', 'remove', ident])

        # Удаляем соответствующий файл в /dev/mapper

        shutil.rmtree(os.path.join(self.directory, opened))
        shutil.move(os.path.join(self.directory, candidates[0]), os.path.join(self.directory, opened))


    def disk_in_use(self, directory):
        result = subprocess.run(['sudo', 'lsof', '-a', '+D', directory], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            print(result.stdout)
            return True  # Если процессы используют файлы на диске, возвращаем True
        else:
            return False  # Если нет процессов, использующих файлы на диске, возвращаем False # Если нет процессов, использующих файлы на диске, возвращаем False

    def kill_processes(self, directory):
        result = subprocess.run(['sudo', 'lsof', '-t', '+D', directory], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['sudo', 'kill', pid])

    def resize_vault(self, vault):
        vault_path = os.path.join(self.directory, vault)
        if not os.path.exists(vault_path):
            print("Vault file not found in the specified directory")
            return

        ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        subprocess.run(['cp', vault_path, os.path.join(self.directory, '.' + ident + '.bak')])

        current_size = os.path.getsize(vault_path)
        print("Current:", current_size)
        increase = int(input("Expand by: "))

        subprocess.run(['qemu-img', 'resize', '-q', '-f', 'raw', vault_path, '+' + str(increase)])

        password = self.prompt_password()
        self.luks_open(vault_path, ident, password)

        subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'resize', '/dev/mapper/' + ident])
        subprocess.run(['sudo', 'e2fsck', '-f', '/dev/mapper/' + ident])
        subprocess.run(['sudo', 'resize2fs', '/dev/mapper/' + ident])

        self.luks_close(ident)
        os.remove(os.path.join(self.directory, '.' + ident + '.bak'))

    def luks_open(self, vault, ident, password):
        subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'luksOpen', vault, ident], input=password.encode())

    def luks_close(self, ident):
        subprocess.run(['sudo', 'cryptsetup', '-q', 'luksClose', ident])

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: vault <new|open|close|resize> <vault> [directory]")
        sys.exit(1)

    command = sys.argv[1]
    vault = sys.argv[2]
    directory = os.getcwd() if len(sys.argv) == 3 else sys.argv[3]

    vault_manager = VaultManager(directory)

    if command == "new":
        vault_manager.new_vault(vault)
    elif command == "open":
        vault_manager.open_vault(vault)
    elif command == "close":
        vault_manager.close_vault(vault)
    elif command == "resize":
        vault_manager.resize_vault(vault)
    else:
        print("Invalid command")
        sys.exit(1)
