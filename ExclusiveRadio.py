#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import requests
from PyQt5.QtCore import (Qt, QUrl, pyqtSignal, Qt, QMimeData, QSize, QPoint, QProcess, 
                            QStandardPaths, QFile, QDir, QSettings, QEvent, QByteArray)
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QSlider, QStatusBar, 
                            QMainWindow, QFileDialog, QMenu, qApp, QAction, 
                             QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QSpacerItem, QSizePolicy, 
                            QMessageBox, QSystemTrayIcon, QInputDialog)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import (QIcon, QPixmap)

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
        self.imagelist = []
        self.radiofile = ""
        self.radioStations = ""
        self.rec_name = ""
        self.rec_url = ""
        self.old_meta = ""
        self.notificationsEnabled = True
        self.wg = QWidget()
        self.er_label = QLabel("Image")
        self.er_label.setScaledContents(False)
        self.er_label.setFixedSize(225, 150)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10 ,6, 10, 6)
        self.layout1 = QHBoxLayout()
        self.tIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "logo.png"))
        self.headerlogo = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "headerlogo.png"))
        self.playIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "media-playback-start.svg"))
        self.stopIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "media-playback-stop.svg"))
        self.recordIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "media-record.svg"))
        self.hideIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "hide.png"))
        
        self.outfile = QStandardPaths.standardLocations(QStandardPaths.TempLocation)[0] + "/er_tmp.mp3"
        self.recording_enabled = False
        self.is_recording = False
        ### combo box
        self.urlCombo = QComboBox(self)
        self.urlCombo.setFixedWidth(220)

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
        
        spc1 = QSpacerItem(6, 10, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.level_sld = QSlider(self)
        self.level_sld.setTickPosition(1)
        self.level_sld.setOrientation(Qt.Horizontal)
        self.level_sld.setValue(65)
        self.level_lbl = QLabel(self)
        self.level_lbl.setAlignment(Qt.AlignHCenter)
        self.level_lbl.setText("Volume 65")
        self.layout.addWidget(self.urlCombo, 0, Qt.AlignCenter)
        self.layout.addLayout(self.layout1)
        self.layout.addItem(spc1)
        self.layout.addWidget(self.level_sld)
        self.layout.addWidget(self.level_lbl)

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


        self.setFixedSize(460, 330)
        self.move(30, 30)

        # Init tray icon
        trayIcon = QIcon(self.tIcon)

        self.trayIcon = QSystemTrayIcon()
        self.trayIcon.setIcon(trayIcon)
        self.trayIcon.show()
                        
        self.geo = self.geometry()
        self.showWinAction = QAction(QIcon.fromTheme("view-restore"), "show Main Window", triggered = self.showMain)
        self.notifAction = QAction(QIcon.fromTheme("dialog-information"), "disable Tray Messages", triggered = self.toggleNotif)
        self.togglePlayerAction = QAction("stop Recording", triggered = self.togglePlay)
        self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.recordAction = QAction(QIcon.fromTheme("media-record"), "record channel", triggered = self.recordRadio)
        self.stopRecordAction = QAction(QIcon.fromTheme("media-playback-stop"), "stop Recording", 
                                triggered = self.stop_recording)
        self.findExecutable()
        self.readSettings()
        self.makeTrayMenu()
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("System Tray Icon available")
        else:
            print("System Tray Icon not available")
        if self.player.state() == QMediaPlayer.StoppedState:
            self.togglePlayerAction.setText("start Player")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))            
        elif self.player.state() == QMediaPlayer.PlayingState:
            self.togglePlayerAction.setText("stop Recording")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.er_label.setFixedHeight(150)
        self.er_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.er_label, 0, Qt.AlignCenter)      
  
        weblabel = QLabel()
        weblabel.setText('<a href=\"https://exclusive.radio\"><p style="color:#c4a000">Exclusive Radio Homepage</p></a>')
        weblabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        weblabel.setOpenExternalLinks(True)
        weblabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(weblabel)  
        
    def showTrayMessage(self, title, message, icon, timeout = 4000):
        self.trayIcon.showMessage(title, message, icon, timeout)
            
    def handleError(self):
        print("Fehler: " + self.player.errorString())
        self.showTrayMessage("Error", self.player.errorString(), self.tIcon, 3000)
        self.statusBar.showMessage(f"Fehler:\n{self.player.errorString()}")
           
    def togglePlay(self):          
        if self.togglePlayerAction.text() == "stop Recording":
            self.stop_preview()
            self.togglePlayerAction.setText("start Player")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))
        else:
            self.playRadioStation()
            self.togglePlayerAction.setText("stop Recording")
            self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-stop"))

    def getURLfromPLS(self, inURL):
        print("untersuche", inURL)
        t = ""
        if "&" in inURL:
            inURL = inURL.partition("&")[0]
        response = requests.get(inURL)
        print(response.text)
        if "http" in response.text:
            html = response.text.splitlines()
            if len(html) > 3:
                if "http" in str(html[1]):
                    t = str(html[1])
                elif "http" in str(html[2]):
                    t = str(html[2])
                elif "http" in str(html[3]):
                    t = str(html[3])
            elif len(html) > 2:
                if "http" in str(html[1]):
                    t = str(html[1])
                elif "http" in str(html[2]):
                    t = str(html[2])
            else:
                t = str(html[0])
            url = t.partition("=")[2].partition("'")[0]
            return (url)
        else:
           self.lbl.setText("bad formatted playlist") 

    def getURLfromM3U(self, inURL):
        print("detecting", inURL)
        response = requests.get(inURL)
        html = response.text.splitlines()
        if "#EXTINF" in str(html):
            url = str(html[1]).partition("http://")[2].partition('"')[0]
            url = f"http://{url}"
        else:
            if len(html) > 1:
                url = str(html[1])
            else:
                url = str(html[0])
        print(url)
        return(url)
        
    def makeTrayMenu(self):
        self.stationActs = []
        menuSectionIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "radio_bg.png"))
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.togglePlayerAction)
        #self.tray_menu.setStyleSheet("font-size: 7pt;")
        ##### submenus from categories ##########
        b = self.radioStations.splitlines()
        for x in reversed(range(len(b))):
            line = b[x]
            if line == "":
                print("empty line", x, "removed")
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
                    data = menu_line[1]
                    if len(menu_line) > 2:
                        image = menu_line[2]
                    self.stationActs.append(QAction(self.tIcon, ch, triggered = self.openTrayStation))
                    self.stationActs[i].setData(str(i))
                    chm.addAction(self.stationActs[i])
                    i += 1
                    break
        ####################################
        self.tray_menu.addSeparator()
        if not self.is_recording:
            if not self.urlCombo.currentText().startswith("--"):
                self.tray_menu.addAction(self.recordAction)
                self.recordAction.setText("%s %s: %s" % ("start recording of", "channel", self.urlCombo.currentText()))
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
        if self.isVisible() ==False:
            self.showWinAction.setText("hide Main Window")
            self.setVisible(True)
        elif self.isVisible() ==True:
            self.showWinAction.setText("show Main Window")
            self.setVisible(False)
            
    def toggleNotif(self):
        if self.notifAction.text() == "disable Tray Messages":
            self.notifAction.setText("enable Tray Messages")
            self.notificationsEnabled = False
        elif self.notifAction.text() == "enable Tray Messages":
            self.notifAction.setText("disable Tray Messages")
            self.notificationsEnabled = True
        print("Notifications", self.notificationsEnabled )
        self.metaDataChanged()

    def openTrayStation(self):
        action = self.sender()
        if action:
            ind = action.data()
            name = action.text()     
            self.urlCombo.setCurrentIndex(self.urlCombo.findText(name))
            print("%s %s %s" % ("swith to Station:", ind, self.urlCombo.currentText()))

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
            print("set volume to", vol)
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
        menuSectionIcon = QIcon(os.path.join(os.path.dirname(sys.argv[0]), "radio_bg.png"))
        self.urlCombo.clear()
        self.radiolist = []
        self.channels = []
        self.imagelist = []
        dir = os.path.dirname(sys.argv[0])
        self.radiofile = os.path.join(dir, "excl_radio.txt")
        with open(self.radiofile, 'r') as f:
            self.radioStations = f.read()
            f.close()
            newlist = [list(x) for x in self.radioStations.splitlines()]
            for lines in self.radioStations.splitlines():
                mLine = lines.split(",")
                if not mLine[0].startswith("--"):
                    self.urlCombo.addItem(self.tIcon, mLine[0],Qt.UserRole - 1)
                    self.radiolist.append(mLine[1])
                    self.imagelist.append(mLine[2])          

    def findExecutable(self):
        wget = QStandardPaths.findExecutable("wget")
        if wget != "":
            print("%s %s %s" % ("found wget at ", wget, " *** recording available"))
            self.statusBar.showMessage("Aufnahmen möglich")
            self.showTrayMessage("Note", "found wget\nrecording available", self.tIcon)
            self.recording_enabled = True
        else:
            self.showTrayMessage("Note", "wget not found \nno recording available", self.tIcon)
            print("wget not found \nno recording available")
            self.recording_enabled = False

    def remove_last_line_from_string(self, s):
        return s[:s.rfind('\n')]

    def createStatusBar(self):
        self.statusBar = QStatusBar()
        self.statusBar.setSizeGripEnabled(False)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Welcome to Exclusive Radio")
        pixmap = QPixmap(self.headerlogo.pixmap(64))
        statuslabel = QLabel()
        statuslabel.setMargin(3)
        statuslabel.setPixmap(pixmap)
        self.statusBar.addPermanentWidget(statuslabel)

        
    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            trackInfo = (self.player.metaData("Title"))
            description = (self.player.metaData("Description"))
            comment = (self.player.metaData("Comment"))
            if trackInfo is None:
                self.statusBar.showMessage("%s %s" % ("playing", self.urlCombo.currentText()))
            new_trackInfo = ""
            new_trackInfo = str(trackInfo)
            if len(new_trackInfo) > 200:
                new_trackInfo = str(new_trackInfo).partition('{"title":"')[2].partition('","')[0].replace('\n', " ")[:200]
            if not new_trackInfo == "None":
                self.statusBar.showMessage(new_trackInfo)
            else:
                self.statusBar.showMessage("%s %s" % ("playing", self.urlCombo.currentText()))
            mt = (f"Titel:{new_trackInfo}\nBeschreibung:{description}\nKommentar:: {comment}")
            if description == None:
                mt = (f"Titel:{new_trackInfo}\nKommentar: {comment}")
            if comment == None:
                mt = (f"Titel:{new_trackInfo}\nKommentar: {description}")
            if description == None and comment == None:
                mt = (f"{new_trackInfo}")
            if not mt == "None":
                if self.notificationsEnabled:
                    if not mt == self.old_meta:
                        print(mt)
                        self.showTrayMessage("Exclusive Radio", mt, self.tIcon)
                        self.old_meta = mt
                    self.trayIcon.setToolTip(mt)
                else:
                    self.trayIcon.setToolTip(mt)
                    self.old_meta = mt
        else:
            self.statusBar.showMessage("%s %s" % ("playing", self.urlCombo))
        

    def url_changed(self):
        if self.urlCombo.currentIndex() < self.urlCombo.count() - 1:
            if not self.urlCombo.currentText().startswith("--"):
                ind = self.urlCombo.currentIndex()
                
                image = self.imagelist[ind]
                print("Image URL:", image)
                response = requests.get(image)
                data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                self.er_label.setPixmap(pixmap)
                url = self.radiolist[ind]
                #print(url)
                
                if url.endswith(".m3u"):
                    url = self.getURLfromM3U(url)
                if url.endswith(".pls"):
                    url = self.getURLfromPLS(url)
                
                self.current_station = url
                self.player.stop()
                self.rec_btn.setVisible(True)
                self.stop_btn.setVisible(True)
                self.play_btn.setVisible(True)
                name = self.urlCombo.currentText()
                print(f"playing {name} from {url}")
                self.playRadioStation()
                if self.togglePlayerAction.text() == "stop Recording":
                    self.togglePlayerAction.setText("start Player")
                    self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))
                else:
                    self.togglePlayerAction.setText("stop Recording")
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
            self.recordAction.setText("%s %s: %s" % ("start recording", "of", self.urlCombo.currentText()))
            self.recordAction.setIcon(QIcon.fromTheme("media-record"))
        self.statusBar.showMessage("%s %s" % ("playing", self.urlCombo.currentText()))
        self.setWindowTitle(self.urlCombo.currentText())   
 
    def set_running_player(self):
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
 
    def pause_preview(self):
        self.player.set_on_pause()
        self.play_btn.setEnabled(True)
        self.rec_btn.setEnabled(False)
        self.play_btn.setFocus(True)
        self.statusBar.showMessage("Pause")
 
    def stop_preview(self):
        self.player.finish()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.rec_btn.setEnabled(False)
        self.statusBar.showMessage("stopped")
        self.togglePlayerAction.setText("start Player")
        self.togglePlayerAction.setIcon(QIcon.fromTheme("media-playback-start"))

 
    def set_sound_level(self, level):
        self.player.set_sound_level(level)
        self.level_lbl.setText("Volume " + str(level))
        self.player.setVolume(level)
 
    def update_volume_slider(self, level):
        self.level_lbl.setText("Volume " + str(level))
        self.level_sld.blockSignals(True)
        self.level_sld.setValue(value)
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
            self.recordAction.setText("%s %s: %s" % ("start recording", "of", self.urlCombo.currentText()))
            self.recordAction.setIcon(QIcon.fromTheme("media-record"))
        else:
            self.showTrayMessage("Note", "no recording started", self.tIcon)

    def saveRecord(self):
        if not self.is_recording:
            print("saving Audio")
            musicfolder = QStandardPaths.standardLocations(QStandardPaths.MusicLocation)[0]
            recname = self.rec_name.replace("-", " ").replace(" - ", " ") + ".mp3"
            infile = QFile(self.outfile)
            path, _ = QFileDialog.getSaveFileName(
                                    None, "Save as...", 
                                    f'{musicfolder}/{recname}',
                                    "Audio (*.mp3)")
            if (path != ""):
                savefile = path
                if QFile(savefile).exists:
                    QFile(savefile).remove()
                print("%s %s" % ("saving", savefile))
                if not infile.copy(savefile):
                    QMessageBox.warning(self, "Error",
                        "File %s:\n%s." % (path, infile.errorString())) 
                print("%s %s" % ("Prozess-State: ", str(self.process.state())))
                if QFile(self.outfile).exists:
                    print("exists")
                    QFile(self.outfile).remove()


    def deleteOutFile(self):
        if QFile(self.outfile).exists:
            print("%s %s" % ("delete file", self.outfile)) 
            if QFile(self.outfile).remove:
                print("%s %s" % (self.outfile, "deleted"))  
            else:  
                print("%s %s" % (self.outfile, "not deleted"))

    def getPID(self):
        print("%s %s" % (self.process.pid(), self.process.processId()))

 
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
width: 18px;
}

QSlider::groove:horizontal {
border: 1px solid #555753;;
height: 4px;
background: #2e4d25;
border-radius: 0px;
}
QSlider::sub-page:horizontal {
background: #685c1b;
border: 0px solid #c4a000;
height: 4px;
border-radius: 0px;
}
QSlider::handle:horizontal:hover {
background: #73d216;
border-radius: 0px;
height: 6px;
width: 14px;
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
    win = MainWin()
    app.setQuitOnLastWindowClosed(False)
    #win.show()
    sys.exit(app.exec_())
