#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil
import random
import string
import hashlib

def prompt_password():
    password = input("Enter password: ")
    return hashlib.sha256(password.encode()).hexdigest()

def usage():
    print("Usage: vault <new|open|close|resize> <vault>")
    sys.exit(1)

def luks_open(vault, ident, password):
    subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'luksOpen', vault, ident], input=password.encode())

def luks_close(ident):
    subprocess.run(['sudo', 'cryptsetup', '-q', 'luksClose', ident])

def new_vault(vault):
    if os.path.exists(vault):
        print("File already exists")
        sys.exit(1)

   

    ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    password = prompt_password()

    with open(vault, 'wb') as f:
        f.truncate(32 * 1024 * 1024)

    subprocess.run(['cryptsetup', '-q', '-d', '-', 'luksFormat', vault], input=password.encode())
    luks_open(vault, ident, password)
    subprocess.run(['sudo', 'mkfs.ext4', '-Fq', '/dev/mapper/' + ident])
    luks_close(ident)

def open_vault(vault):
    base = os.path.basename(vault)
    if not os.path.exists(vault):
        print("You need to be in the same directory as the vault file")
        sys.exit(1)

    if os.path.isdir(base):
        print("There already exists a directory", base)
        sys.exit(1)

    ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    newname = "." + base + "-" + ident

    password = prompt_password()

    shutil.move(vault, newname)

    luks_open(newname, ident, password)
    os.mkdir(vault)
    subprocess.run(['sudo', 'mount', '/dev/mapper/' + ident, vault])
    subprocess.run(['sudo', 'chown', os.getlogin(), vault])

def close_vault(vault):
    base = os.path.basename(vault)
    if not os.path.isdir(base):
        print("You need to be in the same directory as the opened vault")
        exit(1)

    opened = base
    candidates = list(filter(lambda x: x.startswith(f'.{opened}-'), os.listdir()))
    
    if len(candidates) > 1:
        print("Multiple vaults with the same name are opened")
        exit(1)
    
    ident = candidates[0].split('-')[1]
    luks_close(ident)
    subprocess.run(['sudo', 'umount', opened])
    shutil.rmtree(opened)
    shutil.move(candidates[0], opened)

def resize_vault(vault):
    if not os.path.exists(vault):
        print("You need to be in the same directory as the vault file")
        sys.exit(1)

    ident = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    subprocess.run(['cp', vault, '.' + ident + '.bak'])

    current_size = os.path.getsize(vault)
    print("Current:", current_size)
    increase = int(input("Expand by: "))

    subprocess.run(['qemu-img', 'resize', '-q', '-f', 'raw', vault, '+' + str(increase)])

    password = prompt_password()
    luks_open(vault, ident, password)

    subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'resize', '/dev/mapper/' + ident])
    subprocess.run(['sudo', 'e2fsck', '-f', '/dev/mapper/' + ident])
    subprocess.run(['sudo', 'resize2fs', '/dev/mapper/' + ident])

    luks_close(ident)
    os.remove('.' + ident + '.bak')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()

    command = sys.argv[1]
    vault = sys.argv[2]

    if command == "new":
        new_vault(vault)
    elif command == "open":
        open_vault(vault)
    elif command == "close":
        close_vault(vault)
    elif command == "resize":
        resize_vault(vault)
    else:
        usage()
