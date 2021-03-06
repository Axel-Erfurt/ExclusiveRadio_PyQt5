#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import requests
from PyQt5.QtCore import (QUrl, pyqtSignal, Qt, QMimeData, QSize, QPoint, QProcess, 
                            QStandardPaths, QFile, QSettings)
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QSlider, QStatusBar, 
                            QMainWindow, QFileDialog, QMenu, qApp, QAction, QToolButton, 
                             QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QSpacerItem, QSizePolicy, 
                            QMessageBox, QSystemTrayIcon)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import (QIcon, QPixmap, QDesktopServices)

changed = pyqtSignal(QMimeData)
btnwidth = 48
        

class MainWin(QMainWindow):
    def __init__(self):
        super(MainWin, self).__init__()
        self.settings = QSettings("ExclusiveRadio", "settings")
        self.setStyleSheet(mystylesheet(self))
        self.radioNames = []
        self.radiolist = []
        self.channels = []
        self.radiofile = ""
        self.radioStations = ""
        self.rec_name = ""
        self.rec_url = ""
        self.old_meta = ""
        self.notificationsEnabled = True
        
        self.setContentsMargins(5 ,0, 5, 0)
        
        self.wg = QWidget()
        self.layout = QVBoxLayout()

        
        ### combo box
        self.urlCombo = QComboBox()
        
        self.layout1 = QHBoxLayout()
        self.layout1.setContentsMargins(50 ,0, 50, 0)
        self.tIcon = QIcon("logo.png")
        self.headerlogo = QIcon("headerlogo.png")
        self.playIcon = QIcon("media-playback-start.svg")
        self.stopIcon = QIcon("media-playback-stop.svg")
        self.recordIcon = QIcon("media-record.svg")
        self.hideIcon = QIcon("hide.png")
        
        self.outfile = QStandardPaths.standardLocations(QStandardPaths.TempLocation)[0] + "/er_tmp.mp3"
        self.recording_enabled = False
        self.is_recording = False
        
        spc1 = QSpacerItem(6, 10, QSizePolicy.Expanding, QSizePolicy.Maximum)
        
        self.play_btn = QPushButton("", self)
        self.play_btn.setFixedWidth(btnwidth)
        self.play_btn.setIcon(self.playIcon)
        self.layout1.addWidget(self.play_btn)

        self.stop_btn = QPushButton("", self)
        self.stop_btn.setFixedWidth(btnwidth)
        self.stop_btn.setIcon(self.stopIcon)
        self.layout1.addWidget(self.stop_btn)
        ### record
        self.rec_btn = QPushButton("", self)
        self.rec_btn.setFixedWidth(btnwidth)
        self.rec_btn.setIcon(self.recordIcon)
        self.rec_btn.clicked.connect(self.recordRadio)
        self.rec_btn.setToolTip("Record Station")
        self.layout1.addWidget(self.rec_btn)
        ### stop record
        self.stoprec_btn = QPushButton("", self)
        self.stoprec_btn.setFixedWidth(btnwidth)
        self.stoprec_btn.setIcon(self.stopIcon)
        self.stoprec_btn.clicked.connect(self.stop_recording)
        self.stoprec_btn.setToolTip("stop Recording")
        self.layout1.addWidget(self.stoprec_btn)
        ### hide Main Window
        self.hide_btn = QPushButton("", self)
        self.hide_btn.setFixedWidth(btnwidth)
        self.hide_btn.setToolTip("hide Main Window")
        self.hide_btn.setIcon(self.hideIcon)
        self.hide_btn.clicked.connect(self.showMain)
        self.layout1.addWidget(self.hide_btn)        
        
        self.level_sld = QSlider(self)
        self.level_sld.setFixedWidth(310)
        self.level_sld.setToolTip("Volume Slider")
        self.level_sld.setTickPosition(1)
        self.level_sld.setOrientation(Qt.Horizontal)
        self.level_sld.setValue(65)
        self.level_lbl = QLabel(self)
        self.level_lbl.setAlignment(Qt.AlignHCenter)
        self.level_lbl.setText("Volume 65")
        self.layout.addItem(spc1)

        self.layout.addWidget(self.level_sld, Qt.AlignCenter)
        self.layout.addWidget(self.level_lbl, Qt.AlignCenter)
        self.layout.addItem(spc1)
       
        self.layout.addLayout(self.layout1)

        self.player = RadioPlayer(self)
        self.player.metaDataChanged.connect(self.metaDataChanged)
        self.player.error.connect(self.handleError)
        self.play_btn.clicked.connect(self.playRadioStation)
        self.stop_btn.clicked.connect(self.stop_preview)
        self.level_sld.valueChanged.connect(self.set_sound_level)
        self.urlCombo.currentIndexChanged.connect(self.url_changed)
        self.current_station = ""

        self.process = QProcess()
        self.process.started.connect(self.getPID)

        self.wg.setLayout(self.layout)
        self.setCentralWidget(self.wg)

        self.stoprec_btn.setVisible(False)
        self.readStations()

        self.createStatusBar()
        self.setAcceptDrops(True)
        self.setWindowTitle("Exclusive Radio")
        
        self.setWindowIcon(self.tIcon)
        self.stationActs = []

        self.layout.addItem(spc1)
        self.setFixedSize(340, 200)
        self.move(30, 30)

        # Init tray icon
        trayIcon = QIcon(self.tIcon)

        self.trayIcon = QSystemTrayIcon()
        self.trayIcon.setIcon(trayIcon)
        self.trayIcon.show()
        self.trayIcon.activated.connect(self.showMainfromTray)                
        self.geo = self.geometry()
        self.showWinAction = QAction(QIcon.fromTheme("view-restore"), "show Main Window", triggered = self.showMain)
        self.notifAction = QAction(QIcon.fromTheme("dialog-information"), "disable Tray Messages", triggered = self.toggleNotif)
        self.togglePlayerAction = QAction("stop Player", triggered = self.togglePlay)
        self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.recordAction = QAction(QIcon.fromTheme("media-record"), "record channel", triggered = self.recordRadio)
        self.stopRecordAction = QAction(QIcon.fromTheme("media-playback-stop"), "stop Recording", 
                                triggered = self.stop_recording)
        self.findExecutable()
        self.readSettings()
        self.makeTrayMenu()
        self.createWindowMenu()
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("System Tray Icon available")
        else:
            print("System Tray Icon not available")
        if self.player.state() == QMediaPlayer.StoppedState:
            self.togglePlayerAction.setText("start Player")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))            
        elif self.player.state() == QMediaPlayer.PlayingState:
            self.togglePlayerAction.setText("stop Player")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
        
    def showTrayMessage(self, title, message, icon, timeout = 4000):
        self.trayIcon.showMessage(title, message, icon, timeout)
            
    def handleError(self):
        print(f"Fehler: {self.player.errorString()}")
        self.showTrayMessage(f"Error:\n{self.player.errorString()}", self.tIcon, 3000)
        self.statusLabel.setText(f"Fehler:\n{self.player.errorString()}")
           
    def togglePlay(self):          
        if self.togglePlayerAction.text() == "stop Player":
            self.stop_preview()
            self.togglePlayerAction.setText("start Player")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))
        else:
            self.playRadioStation()
            self.togglePlayerAction.setText("stop Recording")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
            
    def createWindowMenu(self):
        self.tb = self.addToolBar("Menu")
        self.tb_menu = QMenu()
        self.tb.setIconSize(QSize(66, 30))
        
        ##### submenus from categories ##########
        b = self.radioStations.splitlines()
        for x in reversed(range(len(b))):
            line = b[x]
            if line == "":
                print(f"empty line {x} removed")
                del(b[x])
               
        i = 0
        for x in range(0, len(b)):
            line = b[x]
            while True:
                if line.startswith("--"):
                    chm = self.tb_menu.addMenu(line.replace("-- ", "").replace(" --", ""))
                    chm.setIcon(self.tIcon)
                    break
                    continue

                elif not line.startswith("--"):
                    chm.addAction(self.stationActs[i])
                    i += 1
                    break
        ####################################
        toolButton = QToolButton()
        toolButton.setIcon(self.headerlogo)
        toolButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolButton.setText("   Channels")
        toolButton.setFixedWidth(180)
        toolButton.setMenu(self.tb_menu)
        toolButton.setPopupMode(QToolButton.InstantPopup)
        self.tb.addWidget(toolButton)
        
        empty = QWidget()
        self.tb.addWidget(empty) 
        self.tb.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tb.setMovable(False)
        self.tb.setAllowedAreas(Qt.TopToolBarArea)
        
    def makeTrayMenu(self):
        self.stationActs = []
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.togglePlayerAction)
        ##### submenus from categories ##########
        b = self.radioStations.splitlines()
        for x in reversed(range(len(b))):
            line = b[x]
            if line == "":
                print(f"empty line {x} removed")
                del(b[x])
               
        i = 0
        for x in range(0, len(b)):
            line = b[x]
            while True:
                if line.startswith("--"):
                    chm = self.tray_menu.addMenu(line.replace("-- ", "").replace(" --", ""))
                    chm.setIcon(self.tIcon)
                    break
                    continue

                elif not line.startswith("--"):
                    menu_line = line.split(",")
                    ch = menu_line[0]
                    self.stationActs.append(QAction(self.tIcon, ch, 
                                                    triggered = self.openTrayStation))
                    self.stationActs[i].setData(str(i))
                    chm.addAction(self.stationActs[i])
                    i += 1
                    break
        ####################################
        self.tray_menu.addSeparator()
        if not self.is_recording:
            if not self.urlCombo.currentText().startswith("--"):
                self.tray_menu.addAction(self.recordAction)
                self.recordAction.setText(f"start recording of channel {self.urlCombo.currentText()}")
        if self.is_recording:
            self.tray_menu.addAction(self.stopRecordAction)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.showWinAction)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.notifAction)
        self.tray_menu.addSeparator()
        exitAction = self.tray_menu.addAction(QIcon.fromTheme("application-exit"), "Exit")
        exitAction.triggered.connect(self.exitApp)
        self.trayIcon.setContextMenu(self.tray_menu)

    def showMain(self):
        if self.isVisible() == False:
            self.showWinAction.setText("hide Main Window")
            self.setVisible(True)
        elif self.isVisible() == True:
            self.showWinAction.setText("show Main Window")
            self.setVisible(False)
            
    def showMainfromTray(self):
        buttons = qApp.mouseButtons()
        if buttons == Qt.LeftButton:
            if self.isVisible() == False:
                self.showWinAction.setText("hide Main Window")
                self.setVisible(True)
            elif self.isVisible() == True:
                self.showWinAction.setText("show Main Window")
                self.setVisible(False)
            
    def toggleNotif(self):
        if self.notifAction.text() == "disable Tray Messages":
            self.notifAction.setText("enable Tray Messages")
            self.notificationsEnabled = False
        elif self.notifAction.text() == "enable Tray Messages":
            self.notifAction.setText("disable Tray Messages")
            self.notificationsEnabled = True
        print(f"Notifications {self.notificationsEnabled}")
        self.metaDataChanged()

    def openTrayStation(self):
        action = self.sender()
        if action:
            ind = action.data()
            name = action.text()     
            self.urlCombo.setCurrentIndex(self.urlCombo.findText(name))
            print(f"swith to Station: {ind} - {self.urlCombo.currentText()}")

    def exitApp(self):
        self.close()
        QApplication.quit()

    def message(self, message):
        QMessageBox.information(
                None, 'Message', message)

    def closeEvent(self, e):
        self.writeSettings()
        print("writing settings ...\nGoodbye ...")
        QApplication.quit()
        

    def readSettings(self):
        print("reading settings ...")
        if self.settings.contains("pos"):
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        else:
            self.move(0, 26)
        if self.settings.contains("lastChannel"):
            lch = self.settings.value("lastChannel")
            self.urlCombo.setCurrentIndex(self.urlCombo.findText(lch))
        if self.settings.contains("notifications"):
            self.notificationsEnabled = self.settings.value("notifications")
            if self.settings.value("notifications") == "false":
                self.notificationsEnabled = False
                self.notifAction.setText("enable Tray Messages")
            else:
                self.notifAction.setText("disable Tray Messages")
                self.notificationsEnabled = True
        if self.settings.contains("windowstate"):
            print(self.settings.value("windowstate"))
            if self.settings.value("windowstate") == "show Main Window":
                self.show()
                self.showWinAction.setText("hide Main Window")
            else:
                self.hide()
                self.showWinAction.setText("show Main Window")
        if self.settings.contains("volume"):
            vol = self.settings.value("volume")
            print(f"set volume to {vol}")
            self.level_sld.setValue(int(vol))
                
    def writeSettings(self):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("index", self.urlCombo.currentIndex())
        self.settings.setValue("lastChannel", self.urlCombo.currentText())
        self.settings.setValue("notifications", self.notificationsEnabled)
        if self.isVisible():
            self.settings.setValue("windowstate", "show Main Window")
        else:
            self.settings.setValue("windowstate", "hide Main Window")
        self.settings.setValue("volume", self.level_sld.value())
        self.settings.sync()

    def readStations(self):
        self.urlCombo.clear()
        self.radiolist = []
        self.channels = []
        dir = os.path.dirname(sys.argv[0])
        self.radiofile = "excl_radio.txt"
        with open(self.radiofile, 'r') as f:
            self.radioStations = f.read()
            f.close()
            for lines in self.radioStations.splitlines():
                mLine = lines.split(",")
                if len(mLine) > 1:
                    if not mLine[0].startswith("--"):
                        self.urlCombo.addItem(self.tIcon, mLine[0],Qt.UserRole - 1)
                        self.radiolist.append(mLine[1])

    def findExecutable(self):
        wget = QStandardPaths.findExecutable("wget")
        if wget != "":
            print(f"found wget at {wget} *** recording available")
            self.statusLabel.setText("Aufnahmen möglich")
            self.showTrayMessage("Note", "found wget\nrecording available", self.tIcon)
            self.recording_enabled = True
        else:
            self.showTrayMessage("Note", "wget not found \nno recording available", self.tIcon)
            print("wget not found \nno recording available")
            self.recording_enabled = False

    def remove_last_line_from_string(self, s):
        return s[:s.rfind('\n')]

    def createStatusBar(self):
        self.statusLabel = QLabel("Info")
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setStyleSheet("color:#73d216;")
        self.statusBar = QStatusBar()
        self.statusBar.setSizeGripEnabled(False)
        self.setStatusBar(self.statusBar)
        self.statusLabel.setText("Welcome to Exclusive Radio")
        self.statusBar.addWidget(self.statusLabel, 1)
        self.home_label = QPushButton()
        self.home_label.setIconSize(QSize(26,26))
        self.home_label.setFixedSize(32, 32)
        self.home_label.setToolTip("vist Exclusive Radio Homepage")
        self.home_label.setIcon(self.tIcon)
        self.home_label.clicked.connect(self.showHomepage)
        self.statusBar.addPermanentWidget(self.home_label)
        
    def showHomepage(self):
        url = QUrl('https://exclusive.radio')
        QDesktopServices.openUrl(url)

        
    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            trackInfo = (self.player.metaData("Title"))
            if trackInfo is None:
                self.statusLabel.setText(f"playing {self.urlCombo.currentText()}")
            new_trackInfo = ""
            new_trackInfo = str(trackInfo)
            if not new_trackInfo == "None":
                self.statusLabel.setText(f"{new_trackInfo.split('-')[0]}\n{new_trackInfo.split('-')[1]}")
            else:
                self.statusLabel.setText(f" playing {self.urlCombo.currentText()}")
            mt = new_trackInfo
            if not mt == "None":
                if self.notificationsEnabled:
                    if not mt == self.old_meta:
                        print(mt)
                        self.showTrayMessage("Exclusive Radio", f"{mt.split('-')[0]}\n{mt.split('-')[1]}", self.tIcon)
                        self.old_meta = mt
                    self.trayIcon.setToolTip(mt)
                else:
                    self.trayIcon.setToolTip(mt)
                    self.old_meta = mt
        else:
            self.statusLabel.setText(f"playing {self.urlCombo}")
        

    def url_changed(self):
        if self.urlCombo.currentIndex() < self.urlCombo.count() - 1:
            if not self.urlCombo.currentText().startswith("--"):
                ind = self.urlCombo.currentIndex()
                self.player.stop()
                url = self.radiolist[ind]
                
                self.current_station = url
                
                self.rec_btn.setVisible(True)
                self.stop_btn.setVisible(True)
                self.play_btn.setVisible(True)
                name = self.urlCombo.currentText()
                print(f"playing {name} from {url}")
                self.playRadioStation()
                if self.togglePlayerAction.text() == "stop Player":
                    self.togglePlayerAction.setText("start Player")
                    self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))
                else:
                    self.togglePlayerAction.setText("stop Player")
                    self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
            else:
                self.rec_btn.setVisible(False)
                self.stop_btn.setVisible(False)
                self.play_btn.setVisible(False)
 
    def playRadioStation(self):
        if self.player.is_on_pause:
            self.set_running_player()
            self.player.start()
            self.stop_btn.setFocus()
            self.togglePlayerAction.setText("stop Recording")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
 
        if not self.current_station:
            return
 
        self.player.set_media(self.current_station)
        self.set_running_player()
        self.player.start()
        if self.is_recording:
            self.recordAction.setText(f"stop recording of {self.rec_name}")
            self.recordAction.setIcon(QIcon.fromTheme("media-playback-stop"))
        else:
            self.recordAction.setText(f"start recording of {self.urlCombo.currentText()}")
            self.recordAction.setIcon(QIcon.fromTheme("media-record"))
        self.statusLabel.setText(f"playing {self.urlCombo.currentText()}")
        self.setWindowTitle(self.urlCombo.currentText())   
 
    def set_running_player(self):
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
 
    def stop_preview(self):
        self.player.finish()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.rec_btn.setEnabled(False)
        self.statusLabel.setText("stopped")
        self.togglePlayerAction.setText("start Player")
        self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))

 
    def set_sound_level(self, level):
        self.player.set_sound_level(level)
        self.level_lbl.setText("Volume " + str(level))
        self.player.setVolume(level)
 
    def update_volume_slider(self, level):
        self.level_lbl.setText("Volume " + str(level))
        self.level_sld.blockSignals(True)
        self.level_sld.setValue(level)
        self.level_lbl.setText("Volume " + str(level))
        self.level_sld.blockSignals(False)

    def recordRadio(self):
        if not self.is_recording:
            self.deleteOutFile()
            self.rec_url = self.current_station
            self.rec_name = self.urlCombo.currentText()
            cmd = ("wget -q "  + self.rec_url + " -O " + self.outfile)
            print(cmd)         
            self.is_recording = True   
            self.process.startDetached(cmd)
            self.recordAction.setText(f"stop recording of {self.rec_name}")
            self.recordAction.setIcon(QIcon.fromTheme("media-playback-stop"))
            self.rec_btn.setVisible(False)
            self.stoprec_btn.setVisible(True)
        else:
            self.stop_recording()

    def stop_recording(self):
        if self.is_recording:
            self.process.close()
            print("stopping recording")
            self.is_recording = False
            QProcess.execute("killall wget")
            self.saveRecord()
            self.stoprec_btn.setVisible(False)
            self.rec_btn.setVisible(True)
            self.recordAction.setText(f"start recording of {self.urlCombo.currentText()}")
            self.recordAction.setIcon(QIcon.fromTheme("media-record"))
        else:
            self.showTrayMessage("Note", "no recording started", self.tIcon)

    def saveRecord(self):
        if not self.is_recording:
            print("saving Audio")
            musicfolder = QStandardPaths.standardLocations(QStandardPaths.MusicLocation)[0]
            recname = self.rec_name.replace("-", " ").replace(" - ", " ") + ".mp3"
            infile = QFile(self.outfile)
            savefile, _ = QFileDialog.getSaveFileName(
                                    None, "Save as...", 
                                    f'{musicfolder}/{recname}',
                                    "Audio (*.mp3)")
            if (savefile != ""):
                if QFile(savefile).exists:
                    QFile(savefile).remove()
                print(f"saving {savefile}")
                if not infile.copy(savefile):
                    QMessageBox.warning(self, "Error",
                        f"File {savefile} {infile.errorString()}") 
                print(f"Prozess-State: {str(self.process.state())}")
                if QFile(self.outfile).exists:
                    print("exists")
                    QFile(self.outfile).remove()


    def deleteOutFile(self):
        if QFile(self.outfile).exists:
            print(f"delete file {self.outfile}") 
            if QFile(self.outfile).remove:
                print(f"{self.outfile} deleted")
            else:  
                print(f"{self.outfile} not deleted")

    def getPID(self):
        print(f"{self.process.pid()} {self.process.processId()}")

 
class RadioPlayer(QMediaPlayer):
    def __init__(self, driver):
        super(RadioPlayer, self).__init__()
        self.driver = driver
        self.url = None
        self.auto_sound_level = True
        self.is_running = False
        self.is_on_pause = False
        self.volumeChanged.connect(self.on_volume_changed)
        self.stateChanged.connect(self.on_state_changed)
 
    def set_media(self, media):
        if isinstance(media, QUrl):
            self.url = media
 
        elif isinstance(media, str):
            self.url = QUrl(media)
 
        self.setMedia(QMediaContent(self.url))
 
    def start(self):
        self.is_running = True
        self.is_on_pause = False
        self.play()
 
    def set_on_pause(self):
        self.is_running = False
        self.is_on_pause = True
        self.pause()

 
    def finish(self):
        self.is_running = False
        self.is_on_pause = False
        self.stop()
            
    def set_sound_level(self, level):
        self.auto_sound_level = False
        self.setVolume(level)
 
    def on_volume_changed(self, value):
        if self.auto_sound_level:
            self.update_volume_slider(value)
        self.auto_sound_level = True
 
    def on_state_changed(self, state):
        if not state:
            self.driver.stop_preview()
    

def mystylesheet(self):
    return """
QToolBar
{
height: 20px;
background: #2e3436;
color: #73d216;
font-size: 8pt;
border: 0px;
}
QToolButton
{
background: #2e3436;
color:#8ae234;
}
QToolButton::item
{
background: #2e3436;
color:#8ae234;
}
QPushButton
{
background: #2e3436;
color: #4e9a06;
}
QPushButton::hover
{
background: #4e9a06;
}
QComboBox
{
height: 20px;
background: #2e3436;
color: #eeeeec;
font-size: 8pt;
}
QComboBox::item
{
background: #2e3436;
selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #2e4d25, stop: 1.0 #4e9a06);
selection-color: #fce94f;
}
QStatusBar
{
color: #73d216;
font-size: 8pt;
background: transparent;
}
QStatusBar::item 
{
border: none;
} 
QLabel
{
border: 0px;
color: #c4a000;
font-size: 9pt;
}
QMainWindow
{
background: #2e3436;
}
QSlider::handle:horizontal 
{
background: transparent;
width: 8px;
height: 8px;
border-radius: 4px;
}

QSlider::groove:horizontal {
border: 1px solid #c4a000;;
height: 8px;
background: #2e4d25;
border-radius: 0px;
}
QSlider::sub-page:horizontal {
background: #685c1b;
border: 1px solid #c4a000;
height: 6px;
border-radius: 0px;
}
QSlider::handle:horizontal:hover {
background: #73d216;
border-radius: 4px;
height: 6px;
width: 8px;
}

QSlider::sub-page:horizontal:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:horizontal:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:horizontal:disabled {
background: #eee;
border-radius: 4px;
}
QToolTip { 
font-size: 9pt;
color: #eeeeec; 
background: #685c1b; 
height: 28px;
border: 1px solid #1f3c5d; }
    """    


if __name__ == "__main__":
    app = QApplication([])
    os.chdir(os.path.dirname(sys.argv[0]))
    win = MainWin()
    app.setQuitOnLastWindowClosed(False)
    #win.show()
    sys.exit(app.exec_())
