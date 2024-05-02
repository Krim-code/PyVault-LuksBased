#!/usr/bin/env python3
import os
import subprocess
import shutil
import random
import hashlib

def prompt_password():
    PASSWORD = input("Enter password: ")
    return hashlib.sha256(PASSWORD.encode()).hexdigest()

def usage():
    print("Usage: vault <new|open|close|resize> <vault>")
    exit(1)

def luks_open(vault, ident):
    PASSWORD = prompt_password()
    subprocess.run(['echo', PASSWORD], stdout=subprocess.PIPE)
    subprocess.run(['sudo', 'cryptsetup', '-q', 'luksOpen', vault, ident], stdout=subprocess.PIPE)

def luks_close(ident):
    subprocess.run(['sudo', 'cryptsetup', '-q', 'luksClose', ident], stdout=subprocess.PIPE)

def run_command(command):
    subprocess.run(command, shell=True, stdout=subprocess.PIPE)

def new(vault):
    if os.path.exists(vault):
        print("File already exists")
        exit(1)
    
    random_str = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=10))
    ident = vault + random_str

    PASSWORD = prompt_password()
    
    with open(vault, 'wb') as f:
        f.write(os.urandom(32*1024*1024))
        
    subprocess.run(['echo', PASSWORD], stdout=subprocess.PIPE)
    subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'luksFormat', vault], stdout=subprocess.PIPE)
    
    luks_open(vault, ident)
    run_command(f'sudo mkfs.ext4 -Fq /dev/mapper/{ident}')
    luks_close(ident)

def open_vault(vault):
    base = os.path.basename(vault)
    if not os.path.exists(base):
        print("You need to be in the same directory as the vault file")
        exit(1)

    if os.path.isdir(base):
        print(f"There already exists a directory {base}")
        exit(1)

    random_str = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=10))
    ident = base + random_str
    newname = '.' + base + '-' + ident

    PASSWORD = prompt_password()

    shutil.move(vault, newname)

    luks_open(newname, ident)
    os.makedirs(base)
    run_command(f'sudo mount /dev/mapper/{ident} {base}')
    os.chown(base, os.getuid(), os.getgid())

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
    run_command(f'sudo umount {opened}')
    shutil.rmtree(opened)
    shutil.move(candidates[0], opened)

def resize_vault(vault):
    if not os.path.exists(vault):
        print("You need to be in the same directory as the vault file")
        exit(1)

    base = os.path.basename(vault)
    ident = base + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=10))
    bak_name = f'.{ident}.bak'

    shutil.copy(vault, bak_name)

    current_size = os.path.getsize(vault)
    print(f"Current: {current_size}")
    increase = input("Expand by: ")

    subprocess.run(['qemu-img', 'resize', '-q', '-f', 'raw', vault, f'+{increase}'], stdout=subprocess.PIPE)

    PASSWORD = prompt_password()
    
    luks_open(vault, ident)
    subprocess.run(['echo', PASSWORD], stdout=subprocess.PIPE)
    subprocess.run(['sudo', 'cryptsetup', '-q', '-d', '-', 'resize', f'/dev/mapper/{ident}'], stdout=subprocess.PIPE)
    subprocess.run(['sudo', 'e2fsck', '-f', f'/dev/mapper/{ident}'], stdout=subprocess.PIPE)
    subprocess.run(['sudo', 'resize2fs', f'/dev/mapper/{ident}'], stdout=subprocess.PIPE)
    luks_close(ident)

    os.remove(bak_name)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        usage()
    if sys.argv[1] == 'new':
        new(sys.argv[2])
    elif sys.argv[1] == 'open':
        open_vault(sys.argv[2])
    elif sys.argv[1] == 'close':
        close_vault(sys.argv[2])
    elif sys.argv[1] == 'resize':
        resize_vault(sys.argv[2])
    else:
        usage()