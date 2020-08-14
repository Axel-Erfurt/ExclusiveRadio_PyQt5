# ExclusiveRadio PyQt5-Version
ExclusiveRadio Tray App for Ubuntu/Mint

play and record [Exclusive Radio](https://exclusive.radio), a Web Radio with 499 Channels. New ones are constantly being added.

![alt text](https://github.com/Axel-Erfurt/ExclusiveRadio_PyQt5/blob/master/screenshot.png)

__Requirements:__
- python3
- PyQt5
- wget

## Usage ##
> python3 ExclusiveRadio.py

It is operated via the context menu of the tray icon or the main window.

- right click on systray icon -> category -> select channel

## Update Channels ##

> python3 exclusive_radio_api_get.py

- creates the file excl_radio.txt in /tmp

- copy/move the file to the ExclusiveRadio folder.

- restart ExclusiveRadio.

## App Download ##
[Linux App 64bit Download](https://www.dropbox.com/s/g8o6h8i740f23r6/ExclusiveRadio64_Qt5.tar.gz?dl=1)

last Update: Aug 14 2020

tested in:

-  Mint 20
- Kubuntu 20.04

extract it and run ExclusiveRadio
