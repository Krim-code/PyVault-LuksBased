# VaultManager

![1716422116335](images/README/1716422116335.png)

VaultManager is a Python utility for managing encrypted vaults using LUKS (Linux Unified Key Setup) and communicating with an Arduino device to generate secure passwords. This tool allows you to create, open, close, and resize encrypted vaults, ensuring the security of your sensitive data.

## Features

* **Create new encrypted vaults**: Initialize and format new LUKS encrypted partitions.
* **Open existing vaults**: Decrypt and mount existing LUKS encrypted partitions.
* **Close vaults**: Unmount and close encrypted partitions, ensuring data security.
* **Resize vaults**: Increase the size of existing LUKS encrypted partitions.
* **Arduino integration**: Communicate with an Arduino device to generate secure passwords based on user input.

## Prerequisites

* Python 3.x
* `cryptsetup` installed on your Linux system
* `serial` module for Python (`pyserial`)
* Arduino device with the corresponding script

## Usage

### Command-Line Interface

The VaultManager utility can be used via the command line with the following syntax:

```
python vault_manager.py <new|open|close|resize> <vault> [directory]
```

* `<new|open|close|resize>`: The command to execute (create, open, close, or resize a vault).
* `<vault>`: The name of the vault file.
* `[directory]`: (Optional) The directory where the vault is located or will be created. Defaults to the current working directory.

### Examples

#### Creating a New Vault

```
python vault_manager.py new my_vault
```

This command creates a new LUKS encrypted vault named `my_vault` in the current directory.

#### Opening an Existing Vault

```
python vault_manager.py open my_vault
```

This command opens and mounts the existing vault `my_vault`.

#### Closing a Vault

```
python vault_manager.py close my_vault
```

This command unmounts and closes the vault `my_vault`.

#### Resizing a Vault

```
python vault_manager.py resize my_vault
```

This command resizes the existing vault `my_vault`, expanding its size by the specified amount.
