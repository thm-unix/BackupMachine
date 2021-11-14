#!/usr/bin/python3

import os, sys
import shutil
import json, tarfile
import time
import datetime
from enum import Enum
from collections import deque
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

os.environ['QT_STYLE_OVERRIDE'] = 'fusion'

main_dir = os.path.abspath(__file__)[:-7]
os.chdir(main_dir)


class appInfo(Enum):
    _DEVELOPER = 'thm'
    _APPNAME   = 'Backup Machine'
    _VERSION   = '0.2.2'
    _CONTACT   = 'highsierra.2007@mail.ru'
    _WEBSITE   = 'https://thm-unix.github.io/'


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def setTemplateProgress(self):
        self.useTemplateWindow.progressBar.setValue(self.percentsCompleted)

    def eventHandler(self, form, object, info):
        if form == 'entryPoint':
            if object == 'aboutSoftwarePushButton':
                self.aboutWindow.show()
            elif object == 'exitPushButton':
                exit()
            elif object == 'createNewBackupPushButton':
                self.entryPoint.hide()
                self.createNewBackupWindow.show()
            elif object == 'openBackupPushButton':
                self.entryPoint.hide()
                self.restoreWindow.show()
            elif object == 'useTemplatePushButton':
                self.entryPoint.hide()
                self.useTemplateWindow.templatesListView.clear()
                for template in os.listdir('templates/'):
                    if template[-5:] == '.json':
                        self.useTemplateWindow.templatesListView.addItem(template[:-5])
                self.useTemplateWindow.show()
            elif object == 'settingsPushButton':
                self.entryPoint.hide()

                if self.config['locale'] == 'en':
                    self.settingsWindow.englishLocaleRadioButton.toggle()
                elif self.config['locale'] == 'ru':
                    self.settingsWindow.russianLocalePushButton.toggle()
                else:
                    self.settingsWindow.englishLocaleRadioButton.toggle()

                if self.config['theme'] == 'dark':
                    self.settingsWindow.darkThemeRadioButton.toggle()
                elif self.config['theme'] == 'light':
                    self.settingsWindow.lightThemeRadioButton.toggle()
                else:
                    self.settingsWindow.darkThemeRadioButton.toggle()

                self.settingsWindow.bgrObjectPathLineEdit.setText(self.config['bgrObject'])

                self.settingsWindow.show()
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'createNewBackupWindow':
            if object == 'backPushButton':
                self.createNewBackupWindow.hide()
                self.entryPoint.show()
            elif object == 'addFileToListPushButton':
                queueObjectFilename = QFileDialog.getOpenFileName()
                queueObjectPath = queueObjectFilename[0]
                if not queueObjectPath in self.listItems:
                    self.createNewBackupWindow.specifyFilesManuallyListView.addItem(queueObjectPath)
                    self.listItems += [queueObjectPath]
                else:
                    QMessageBox.information(self, 'Backup Machine', self.txtData['objectExists_msgbox'], QMessageBox.Ok)
            elif object == 'rmFileFromListPushButton':
                if self.createNewBackupWindow.specifyFilesManuallyListView.currentItem():
                    rmElem = self.createNewBackupWindow.specifyFilesManuallyListView.currentItem().text()
                    self.createNewBackupWindow.specifyFilesManuallyListView.clear()
                    self.listItems.pop(self.listItems.index(rmElem))
                    for item in self.listItems:
                        self.createNewBackupWindow.specifyFilesManuallyListView.addItem(item)
                else:
                    QMessageBox.warning(self, 'Backup Machine', self.txtData['notselected_msgbox'], QMessageBox.Ok)
            elif object == 'browsePushButton':
                queueDirectoryName = QFileDialog.getExistingDirectory()
                queueDirectoryPath = queueDirectoryName
                for root, dirs, files in os.walk(queueDirectoryPath):
                    for file in files:
                        currentFile = os.path.join(root, file)
                        print(currentFile)
                        if not currentFile in self.listItems:
                            self.createNewBackupWindow.specifyFilesManuallyListView.addItem(currentFile)
                            self.listItems += [currentFile]
                        else:
                            QMessageBox.warning(self, 'Backup Machine', self.txtData['objectExists_msgbox'], QMessageBox.Ok)
            elif object == 'nextPushButton':
                if self.listItems:
                    self.createNewBackupWindow.hide()
                    self.saveBackupWindow.show()
                    currentDateTime = datetime.datetime.now()
                    self.nameTemplate = str(currentDateTime.year) + '-' + \
                                        str(currentDateTime.month) + '-' + \
                                        str(currentDateTime.day) + '_' + \
                                        str(currentDateTime.hour) + '-' + \
                                        str(currentDateTime.minute) + '-' + \
                                        str(currentDateTime.second) + '.tar'
                    if not self.saveBackupWindow.backupNameLineEdit.text():
                        self.saveBackupWindow.finalNameLabel.setText(self.nameTemplate)
                else:
                    QMessageBox.warning(self, 'Backup Machine', self.txtData['noobjects_msgbox'], QMessageBox.Ok)
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'saveBackupWindow':
            if object == 'backupNameLineEdit':
                self.saveBackupWindow.finalNameLabel.setText(self.saveBackupWindow.backupNameLineEdit.text() + '-' + self.nameTemplate)
            elif object == 'choosePushButton':
                self.backupSaveDirectory = QFileDialog.getExistingDirectory()
                self.backupSavePath = os.path.join(self.backupSaveDirectory, self.saveBackupWindow.finalNameLabel.text())
                self.saveBackupWindow.backupPathLineEdit.setText(self.backupSavePath)
            elif object == 'backPushButton':
                self.saveBackupWindow.hide()
                self.createNewBackupWindow.show()
            elif object == 'startPushButton':
                if self.saveBackupWindow.backupPathLineEdit.text():
                    self.saveBackupWindow.setWindowTitle(self.txtData['pleaseWait'])
                    self.saveBackupWindow.savingBackupTitleLabel.setText(self.txtData['progressTitleLabel'])

                    if self.saveBackupWindow.createNewTemplateCheckBox.isChecked():
                        if not os.path.exists('templates/'):
                            os.mkdir('templates')

                        myTemplate = { "name": self.saveBackupWindow.backupNameLineEdit.text(),
                                       "savepath": self.backupSaveDirectory,
                                       "items": self.listItems}

                        with open('templates/' + self.saveBackupWindow.backupNameLineEdit.text() + '.json', 'w') as templateWriter:
                            json.dump(myTemplate, templateWriter)

                    self.filesQueue = deque()
                    for file in self.listItems:
                        self.filesQueue += [file]

                    #  Backup process
                    self.backupName = self.saveBackupWindow.finalNameLabel.text()
                    self.countItems = len(self.listItems)
                    self.completedItems = 0

                    tarWriter = tarfile.open(self.saveBackupWindow.backupPathLineEdit.text(), 'w')

                    while self.filesQueue:
                        tarWriter.add(self.filesQueue[0])
                        self.completedItems += 1
                        self.filesQueue.popleft()

                        self.percentsCompleted = (self.completedItems * 100) // self.countItems
                        self.saveBackupWindow.progressBar.setValue(self.percentsCompleted)
                        print(str(self.percentsCompleted) + '%')

                    tarWriter.close()
                    print('Process completed.')
                    self.saveBackupWindow.hide()
                    self.completionWindow.show()

                    self.saveBackupWindow.progressBar.setValue(0)

                    self.completionWindow.completedSuccessfullyLabel.setText(self.completionWindow.completedSuccessfullyLabel.text() + self.backupSavePath)
                else:
                    QMessageBox.information(self, 'Backup Machine', self.txtData['nodata_msgbox'], QMessageBox.Ok)
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'completionWindow':
            if object == 'homePushButton':
                self.completionWindow.hide()
                self.entryPoint.show()
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'restoreWindow':
            if object == 'selectPushButton':
                selectedFile = QFileDialog.getOpenFileName()
                self.tarFileToRestorePath = selectedFile[0]
                if self.tarFileToRestorePath:
                    if tarfile.is_tarfile(self.tarFileToRestorePath):
                        self.restoreWindow.tarPathLineEdit.setText(self.tarFileToRestorePath)
                    else:
                        QMessageBox.critical(self, 'Backup Machine', self.txtData['notatar_msgbox'], QMessageBox.Ok)
            elif object == 'browsePushButton':
                self.restoreDirectory = QFileDialog.getExistingDirectory()
                self.restoreWindow.unpackPathLineEdit.setText(self.restoreDirectory)
            elif object == 'backPushButton':
                self.restoreWindow.hide()
                self.entryPoint.show()
            elif object == 'startPushButton':
                if self.restoreWindow.tarPathLineEdit.text() and self.restoreWindow.unpackPathLineEdit.text():
                    self.completedItems = 0

                    self.restoreWindow.restoreTitleLabel.setText(self.txtData['restoreProgressTitleLabel'])
                    self.restoreWindow.setWindowTitle(self.txtData['restorePleaseWait'])

                    tarReader = tarfile.open(self.tarFileToRestorePath)

                    # we still cannot track progress of this process.
                    # the problem is we can't extract one file at one time.
                    tarReader.extractall(self.restoreDirectory)
                    tarReader.close()

                    self.completionWindow.completedSuccessfullyLabel.setText(self.txtData['restoreCompletedSuccessfullyLabel'] + self.restoreDirectory)
                    self.restoreWindow.hide()
                    self.completionWindow.show()
                else:
                    QMessageBox.warning(self, 'Backup Machine', self.txtData['norestoredata_msgbox'], QMessageBox.Ok)
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'useTemplateWindow':
            if object == 'backPushButton':
                self.useTemplateWindow.hide()
                self.entryPoint.show()
            elif object == 'startPushButton':
                if self.useTemplateWindow.templatesListView.currentItem():
                    self.percentsCompleted = 0

                    self.useTemplateWindow.useTemplateTitleLabel.setText(self.txtData['progressTitleLabel'])

                    self.currentTemplateName = self.useTemplateWindow.templatesListView.currentItem().text() + '.json'
                    with open('templates/' + self.currentTemplateName) as templateReader:
                        self.templateData = json.load(templateReader)

                    currentDateTime = datetime.datetime.now()
                    self.nameTemplate = str(currentDateTime.year) + '-' + \
                                        str(currentDateTime.month) + '-' + \
                                        str(currentDateTime.day) + '_' + \
                                        str(currentDateTime.hour) + '-' + \
                                        str(currentDateTime.minute) + '-' + \
                                        str(currentDateTime.second) + '.tar'
                    self.templateBackupFilename = self.templateData['name'] + '-' + self.nameTemplate
                    self.templateBackupPath = self.templateData['savepath']
                    self.templateFilesQueue = deque()
                    self.templateFilesQueue += self.templateData['items']


                    self.completedItems = 0
                    self.templateCountItems = len(self.templateFilesQueue)

                    tarWriter = tarfile.open(os.path.join(self.templateBackupPath, self.templateBackupFilename), 'w')

                    while self.templateFilesQueue:
                        tarWriter.add(self.templateFilesQueue[0])
                        self.completedItems += 1
                        self.templateFilesQueue.popleft()

                        self.percentsCompleted = (self.completedItems * 100) // self.templateCountItems
                        self.useTemplateWindow.progressBar.setValue(self.percentsCompleted)
                        print(str(self.percentsCompleted) + '%')

                    tarWriter.close()
                    print('Process completed.')
                    self.completionWindow.completedSuccessfullyLabel.setText(self.completionWindow.completedSuccessfullyLabel.text() + os.path.join(self.templateBackupPath, self.templateBackupFilename))
                    self.useTemplateWindow.hide()

                    self.useTemplateWindow.progressBar.setValue(0)
                    self.completionWindow.show()
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'settingsWindow':
            if object == 'savePushButton':
                try:
                    # os.rename('config.json', 'config.json.bak')
                    os.remove('config.json')
                except:
                    pass

                if self.settingsWindow.englishLocaleRadioButton.isChecked():
                    selectedLocale = 'us'
                elif self.settingsWindow.russianLocalePushButton.isChecked():
                    selectedLocale = 'ru'
                # ...

                if self.settingsWindow.darkThemeRadioButton.isChecked():
                    selectedTheme = 'dark'
                else:
                    selectedTheme = 'light'

                selectedBgrObject = self.settingsWindow.bgrObjectPathLineEdit.text()

                newConfig = { 'locale': selectedLocale,
                              'theme': selectedTheme,
                              'bgrObject': selectedBgrObject }

                with open('config.json', 'w') as configWriter:
                    json.dump(newConfig, configWriter)

                QMessageBox.information(self, 'Backup Machine', self.txtData['settingssaved_msgbox'], QMessageBox.Ok)
                exit()
            elif object == 'backPushButton':
                self.settingsWindow.hide()
                self.entryPoint.show()
            elif object == 'choosePushButton':
                self.bgrObjectFile = QFileDialog.getOpenFileName()
                self.bgrObjectFilename = self.bgrObjectFile[0]

                self.settingsWindow.bgrObjectPathLineEdit.setText(self.bgrObjectFilename)
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        elif form == 'aboutWindow':
            if object == 'closePushButton':
                self.aboutWindow.hide()
                self.entryPoint.show()
            else:
                print('Unknown object ' + object + ' on form ' + form + ' (report this!)')
        else:
            print('Unknown form: ' + form + ' (report this!)')

    def showCLIMenu(self):
        cmdInput = ''

        print('Welcome to Backup Machine v.' + appInfo._VERSION.value + '!')
        print('1> Create new backup')
        print('2> Restore from backup')
        print('3> Use template')
        print('4> About')
        print('5> Exit\n')

        while not cmdInput in ['1', '2', '3', '4', '5']:
            cmdInput = input('> ')
            self.cliFilesToBackup = []

        if cmdInput == '1':
            cmdInput = ''

            print('Specify files you want to add to the new backup.')
            print('You can add file:             [FILE]/path/to/file')
            print('And you can add a directory:  [DIR]/path/to/dir/')
            print('End with pressing ^C')

            try:
                while True:
                    cmdInput = input('> ')
                    if cmdInput.startswith('[FILE]') and len(cmdInput[6:]) > 0 and \
                       os.path.exists(cmdInput[6:]) and os.path.isfile(cmdInput[6:]):
                        self.cliFilesToBackup += [cmdInput[6:]]
                    elif cmdInput.startswith('[DIR]') and len(cmdInput[5:]) > 0 and \
                       os.path.exists(cmdInput[5:]) and os.path.isdir(cmdInput[5:]):
                        for file in os.scandir(cmdInput[5:]):
                            self.cliFilesToBackup += [file.path]
                    else:
                        print('Incorrect path!')
            except KeyboardInterrupt:
                if len(self.cliFilesToBackup) > 0:
                    pass
                else:
                    print('No files were added.')
                    print()
                    self.showCLIMenu()

            cmdInput = ''
            while cmdInput == '':
                cmdInput = input('Specify name of the backup: ')

            cliBackupName = cmdInput
            '''currentDateTime = datetime.datetime.now()
            nameTemplate = str(currentDateTime.year) + '-' + \
                           str(currentDateTime.month) + '-' + \
                           str(currentDateTime.day) + '_' + \
                           str(currentDateTime.hour) + '-' + \
                           str(currentDateTime.minute) + '-' + \
                           str(currentDateTime.second) + '.tar
            cliBackupFilename = cmdInput'''

            cmdInput = ''
            while cmdInput == '' or not(os.path.exists(cmdInput)):
                cmdInput = input('Where to save the backup (directory): ')
            cmdInput = cmdInput if cmdInput[-1] == '/' else cmdInput + '/'

            self.cliBackupPath = cmdInput

            cmdInput = ''
            while not cmdInput in ['y', 'Y', 'n', 'N']:
                cmdInput = input('Do you want to create a template for this backup? (y/n): ')[0]


            cliTemplateData = {
                'name': cliBackupName,
                'savepath': self.cliBackupPath,
                'items': self.cliFilesToBackup
            }
            cliTemplatePath = 'templates/temp.json'

            with open(cliTemplatePath, 'w') as cliTemplateWriter:
                json.dump(cliTemplateData, cliTemplateWriter)


            if cmdInput in ['y', 'Y']:
                shutil.copyfile('templates/temp.json', 'templates/' + cliBackupName + '.json')

            self.useTemplateCLI('temp')
            os.remove('templates/temp.json')

            print()
            self.showCLIMenu()

        elif cmdInput == '2':
            cmdInput = ''
            while cmdInput == '' or not(os.path.exists(cmdInput)) or \
                not(os.path.isfile(cmdInput)):
                cmdInput = input('Specify path to *.tar backup: ')

            cliTarFilename = cmdInput

            cmdInput = ''
            while cmdInput == '' or not(os.path.exists(cmdInput)) or \
                not(os.path.isdir(cmdInput)):
                cmdInput = input('Where to unpack *.tar: ')

            cliUnpackPath = cmdInput

            cliTarReader = tarfile.open(cliTarFilename)

            # we still cannot track progress of this process.
            # the problem is we can't extract one file at one time.
            cliTarReader.extractall(cliUnpackPath)
            cliTarReader.close()

            print('Process completed.')
            print()

            self.showCLIMenu()


        elif cmdInput == '3':
            templates = [template[:-5] for template in os.listdir('templates/') if template != 'TEMPLATES_DIRECTORY']
            if len(templates) > 0:
                print('Please select the template:')
                for i in range(0, len(templates)):
                    print(str(i+1) + '> ' + templates[i])
                print('0> Back')

                cmdInput = ''
                while not cmdInput in [str(j) for j in range(0, len(templates)+1)]:
                    cmdInput = input('> ')

                if cmdInput == '0':
                    print()
                    self.showCLIMenu()
                else:
                    self.useTemplateCLI(templates[int(cmdInput)-1])

                print()
                self.showCLIMenu()

            else:
                print('No templates found.\n')
                self.showCLIMenu()


        elif cmdInput == '4':
            print(('Backup Machine v.' + appInfo._VERSION.value).center(32))
            print('Developer: thm'.center(32))
            print('highsierra.2007@mail.ru'.center(32))
            print('https://thm-unix.github.io'.center(32))
            print()
            self.showCLIMenu()

        elif cmdInput == '5':
            exit()


    def useTemplateCLI(self, templatePath):
        templatePath = 'templates/' + templatePath + '.json'
        if os.path.exists(templatePath):
            with open(templatePath) as templateReader:
                templateData = json.load(templateReader)

            currentDateTime = datetime.datetime.now()
            nameTemplate = str(currentDateTime.year) + '-' + \
                           str(currentDateTime.month) + '-' + \
                           str(currentDateTime.day) + '_' + \
                           str(currentDateTime.hour) + '-' + \
                           str(currentDateTime.minute) + '-' + \
                           str(currentDateTime.second) + '.tar'
            templateBackupFilename = templateData['name'] + '-' + nameTemplate
            templateBackupPath = templateData['savepath']
            templateFilesQueue = deque()
            templateFilesQueue += templateData['items']

            completedItems = 0
            templateCountItems = len(templateFilesQueue)

            tarWriter = tarfile.open(os.path.join(templateBackupPath, templateBackupFilename), 'w')

            while templateFilesQueue:
                tarWriter.add(templateFilesQueue[0])
                completedItems += 1
                templateFilesQueue.popleft()

                percentsCompleted = (completedItems * 100) // templateCountItems
                print(str(percentsCompleted) + '%')

            tarWriter.close()
            print('Process completed.')
        else:
            print('No such template.')

    def init(self):
        myArgs = sys.argv
        # print('Args: ' + ' '.join(myArgs))

        if '-service' in myArgs:
            if '-template' in myArgs:
                if (len(myArgs)-1) == (myArgs.index('-template')+1):
                    self.useTemplateCLI(myArgs[myArgs.index('-template')+1])
                    exit()
                else:
                    print('Incorrect usage of arguments.')
                    exit()
            else:
                print('Lack of arguments.')
                exit()

        if '-cli' in myArgs:
            self.showCLIMenu()

        # Read config.json
        try:
            with open('config.json', 'r') as configReader:
                self.config = json.load(configReader)
        except:  # failsafe
            QMessageBox.critical(self, 'Backup Machine', 'Bad syntax or absence of config.json. Using failsafe configuration.', QMessageBox.Ok)
            self.config = { 'theme': 'light',
                            'locale': 'en',
                            'bgrObject': 'assets/background.jpg' }


        # Read QSS
        try:
            self.lightQSS = open('styles/light.qss').read()
            self.darkQSS = open('styles/dark.qss').read()
        except:
            QMessageBox.critical(self, 'Backup Machine', 'Stylesheets are absent. Using failsafe stylesheet.', QMessageBox.Ok)
            self.lightQSS = 'QWidget { background-color: #e5e5e5; color: #000000; }  QLabel { color: #000000; }  QLabel#appNameLabel { font-size: 20px; }  QLabel#appVersionLabel { font-size: 15px; }  QPushButton,QCheckBox { color: #000000; }  QLineEdit,QListWidget { background-color: #d5d5d5; color: #000000; }'


        # Set *.ui files
        try:
            self.entryPoint = uic.loadUi('ui/entrypoint.ui')
            self.aboutWindow = uic.loadUi('ui/about.ui')
            self.createNewBackupWindow = uic.loadUi('ui/createnewbackup.ui')
            self.saveBackupWindow = uic.loadUi('ui/savebackup.ui')
            self.completionWindow = uic.loadUi('ui/completion.ui')
            self.restoreWindow = uic.loadUi('ui/restore.ui')
            self.useTemplateWindow = uic.loadUi('ui/usetemplate.ui')
            self.settingsWindow = uic.loadUi('ui/settings.ui')
        except:
            QMessageBox.critical(self, 'Backup Machine', 'Interface files are absent/corrupted. Please download software again.', QMessageBox.Ok)
            exit()

        # Background
        if os.path.exists(self.config['bgrObject']):
            myBgr = QPixmap(self.config['bgrObject'])
        else:
            if os.path.exists('assets/background.jpg'):
                myBgr = QPixmap('assets/background.jpg')
        try:
            self.entryPoint.bgrObject.setPixmap(myBgr)
            self.createNewBackupWindow.bgrObject.setPixmap(myBgr)
            self.saveBackupWindow.bgrObject.setPixmap(myBgr)
            self.completionWindow.bgrObject.setPixmap(myBgr)
            self.restoreWindow.bgrObject.setPixmap(myBgr)
            self.useTemplateWindow.bgrObject.setPixmap(myBgr)
            self.settingsWindow.bgrObject.setPixmap(myBgr)
            self.aboutWindow.bgrObject.setPixmap(myBgr)
        except:
            pass


        # Set icon
        try:
            self.darkIcon = QPixmap('assets/dark_icon.png')
            self.lightIcon = QPixmap('assets/light_icon.png')

            if self.config['theme'] == 'dark':
                self.aboutWindow.appIconLabel.setPixmap(self.lightIcon)
            else:
                self.aboutWindow.appIconLabel.setPixmap(self.darkIcon)
        except:
            pass


        # QSS
        if self.config['theme'] == 'dark':
            self.entryPoint.setStyleSheet(self.darkQSS)
            self.aboutWindow.setStyleSheet(self.darkQSS)
            self.createNewBackupWindow.setStyleSheet(self.darkQSS)
            self.saveBackupWindow.setStyleSheet(self.darkQSS)
            self.completionWindow.setStyleSheet(self.darkQSS)
            self.restoreWindow.setStyleSheet(self.darkQSS)
            self.useTemplateWindow.setStyleSheet(self.darkQSS)
            self.settingsWindow.setStyleSheet(self.darkQSS)
        else:
            self.entryPoint.setStyleSheet(self.lightQSS)
            self.aboutWindow.setStyleSheet(self.lightQSS)
            self.createNewBackupWindow.setStyleSheet(self.lightQSS)
            self.saveBackupWindow.setStyleSheet(self.lightQSS)
            self.completionWindow.setStyleSheet(self.lightQSS)
            self.restoreWindow.setStyleSheet(self.lightQSS)
            self.useTemplateWindow.setStyleSheet(self.lightQSS)
            self.settingsWindow.setStyleSheet(self.lightQSS)


        # Set language
        try:
            localePath = 'locales/' + self.config['locale'] + '.json'
            with open(localePath) as localeReader:
                self.txtData = json.load(localeReader)
        except:
            QMessageBox.critical(self, 'Backup Machine', 'Bad locale. Using us.', QMessageBox.Ok)
            try:
                with open('locales/us.json') as localeReader:
                    self.txtData = json.load(localeReader)
            except:  # failsafe
                QMessageBox.critical(self, 'Backup Machine', 'Default locale is corrupted. Using embedded locale.', QMessageBox.Ok)
                self.txtData = {
                  "titleLabel": "Backup Machine: main page",
                  "descriptionLabel": "Welcome to the Backup Machine wizard! To start backing up your files, select one of actions",
                  "createNewBackupPushButton": "Create new backup",
                  "openBackupPushButton": "Restore from backup",
                  "useTemplatePushButton": "Use template",
                  "aboutSoftwarePushButton": "About",
                  "settingsPushButton": "Settings",
                  "exitPushButton": "Exit",
                  "developerLabel": "Developer: ",
                  "createBackupTitleLabel": "Backup Machine: creating new backup",
                  "filesListLabel": "List of files:",
                  "allFilesFromDirectoryRadioButton": "All files from directory",
                  "browsePushButton": "Browse",
                  "nextPushButton": "Next",
                  "backPushButton": "Back",
                  "savingBackupTitleLabel": "Backup Machine: saving backup",
                  "backupNameLabel": "Backup name:",
                  "backupPathLabel": "Backup path:",
                  "choosePushButton": "Choose",
                  "createNewTemplateCheckBox": "Create a template?",
                  "startPushButton": "Start",
                  "progressTitleLabel": "Backup Machine: backup is in progress",
                  "pleaseWait": "Please wait... Backup is in progress.",
                  "completionTitleLabel": "Backup Machine: process completion",
                  "completedSuccessfullyLabel": "Backup process was completed successfully! Now your backup is avaliable at: ",
                  "homePushButton": "Home",
                  "restoreTitleLabel": "Backup Machine: restore from backup",
                  "selectTarLabel": "Select *.tar file:",
                  "whereToUnpackLabel": "Where to unpack?",
                  "selectPushButton": "Select",
                  "restoreProgressTitleLabel": "Backup Machine: restore in progress",
                  "restorePleaseWait": "Please wait... Restore is in progress",
                  "restoreCompletedSuccessfullyLabel": "Restore process was completed successfully! Now your restored files are avaliable at: ",
                  "useTemplateTitleLabel": "Backup Machine: use template",
                  "selectTemplateLabel": "Please select one of avaliable templates",
                  "settingsTitleLabel": "Backup Machine: settings",
                  "languageGroupBox": "Language",
                  "yourLocaleLabel": "(here can be your locale)",
                  "themeGroupBox": "Theme",
                  "darkThemeRadioButton": "Dark",
                  "lightThemeRadioButton": "Light",
                  "bgrObjectLabel": "Background file:",
                  "savePushButton": "Save",
                  "objectExists_msgbox": "This object is already in list.",
                  "notselected_msgbox": "You have not selected the item.",
                  "noobjects_msgbox": "You have not added objects.",
                  "completed_msgbox": "Process completed.",
                  "notatar_msgbox": "The file you specified is not a *.tar file or is corrupted.",
                  "nodata_msgbox": "You have not specified *.tar file and/or restore directory.",
                  "settingssaved_msgbox": "New settings will take effect after restart of Backup Machine.",
                  "closePushButton": "Close"
                  }

        # entryPoint
        self.entryPoint.titleLabel.setText(self.txtData['titleLabel'])
        self.entryPoint.descriptionLabel.setText(self.txtData['descriptionLabel'])
        self.entryPoint.createNewBackupPushButton.setText(self.txtData['createNewBackupPushButton'])
        self.entryPoint.openBackupPushButton.setText(self.txtData['openBackupPushButton'])
        self.entryPoint.useTemplatePushButton.setText(self.txtData['useTemplatePushButton'])
        self.entryPoint.settingsPushButton.setText(self.txtData['settingsPushButton'])
        self.entryPoint.aboutSoftwarePushButton.setText(self.txtData['aboutSoftwarePushButton'])
        self.entryPoint.exitPushButton.setText(self.txtData['exitPushButton'])

        # about
        self.aboutWindow.developerLabel.setText(self.txtData['developerLabel'])

        # createNewBackupWindow
        self.createNewBackupWindow.createBackupTitleLabel.setText(self.txtData['createBackupTitleLabel'])
        self.createNewBackupWindow.filesListLabel.setText(self.txtData['filesListLabel'])
        self.createNewBackupWindow.browsePushButton.setText(self.txtData['browsePushButton'])
        self.createNewBackupWindow.nextPushButton.setText(self.txtData['nextPushButton'])
        self.createNewBackupWindow.backPushButton.setText(self.txtData['backPushButton'])

        # saveBackupWindow
        self.saveBackupWindow.savingBackupTitleLabel.setText(self.txtData['savingBackupTitleLabel'])
        self.saveBackupWindow.backupNameLabel.setText(self.txtData['backupNameLabel'])
        self.saveBackupWindow.backupPathLabel.setText(self.txtData['backupPathLabel'])
        self.saveBackupWindow.choosePushButton.setText(self.txtData['choosePushButton'])
        self.saveBackupWindow.createNewTemplateCheckBox.setText(self.txtData['createNewTemplateCheckBox'])
        self.saveBackupWindow.backPushButton.setText(self.txtData['backPushButton'])
        self.saveBackupWindow.startPushButton.setText(self.txtData['startPushButton'])

        # completionWindow
        self.completionWindow.completionTitleLabel.setText(self.txtData['completionTitleLabel'])
        self.completionWindow.completedSuccessfullyLabel.setText(self.txtData['completedSuccessfullyLabel'])
        self.completionWindow.homePushButton.setText(self.txtData['homePushButton'])

        # restoreWindow
        self.restoreWindow.restoreTitleLabel.setText(self.txtData['restoreTitleLabel'])
        self.restoreWindow.selectTarLabel.setText(self.txtData['selectTarLabel'])
        self.restoreWindow.whereToUnpackLabel.setText(self.txtData['whereToUnpackLabel'])
        self.restoreWindow.selectPushButton.setText(self.txtData['selectPushButton'])
        self.restoreWindow.browsePushButton.setText(self.txtData['browsePushButton'])
        self.restoreWindow.backPushButton.setText(self.txtData['backPushButton'])
        self.restoreWindow.startPushButton.setText(self.txtData['startPushButton'])

        # useTemplateWindow
        self.useTemplateWindow.useTemplateTitleLabel.setText(self.txtData['useTemplateTitleLabel'])
        self.useTemplateWindow.selectTemplateLabel.setText(self.txtData['selectTemplateLabel'])
        self.useTemplateWindow.backPushButton.setText(self.txtData['backPushButton'])
        self.useTemplateWindow.startPushButton.setText(self.txtData['startPushButton'])

        # settingsWindow
        self.settingsWindow.settingsTitleLabel.setText(self.txtData['settingsTitleLabel'])
        self.settingsWindow.languageGroupBox.setTitle(self.txtData['languageGroupBox'])
        self.settingsWindow.yourLocaleLabel.setText(self.txtData['yourLocaleLabel'])
        self.settingsWindow.themeGroupBox.setTitle(self.txtData['themeGroupBox'])
        self.settingsWindow.darkThemeRadioButton.setText(self.txtData['darkThemeRadioButton'])
        self.settingsWindow.lightThemeRadioButton.setText(self.txtData['lightThemeRadioButton'])
        self.settingsWindow.bgrObjectLabel.setText(self.txtData['bgrObjectLabel'])
        self.settingsWindow.choosePushButton.setText(self.txtData['choosePushButton'])
        self.settingsWindow.savePushButton.setText(self.txtData['savePushButton'])
        self.settingsWindow.backPushButton.setText(self.txtData['backPushButton'])

        # aboutWindow
        self.aboutWindow.closePushButton.setText(self.txtData['closePushButton'])


        # Set About window
        self.aboutWindow.appNameLabel.setText(appInfo._APPNAME.value)
        self.aboutWindow.appVersionLabel.setText('v.' + appInfo._VERSION.value)
        self.aboutWindow.developerLabel.setText(self.aboutWindow.developerLabel.text() + appInfo._DEVELOPER.value)
        self.aboutWindow.emailLabel.setText(appInfo._CONTACT.value)
        self.aboutWindow.githubLabel.setText(appInfo._WEBSITE.value)


        # Set events

        # entryPoint
        self.entryPoint.aboutSoftwarePushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'aboutSoftwarePushButton', ''))
        self.entryPoint.exitPushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'exitPushButton', ''))
        self.entryPoint.createNewBackupPushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'createNewBackupPushButton', ''))
        self.entryPoint.openBackupPushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'openBackupPushButton', ''))
        self.entryPoint.useTemplatePushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'useTemplatePushButton', ''))
        self.entryPoint.settingsPushButton.clicked.connect(lambda: self.eventHandler('entryPoint', 'settingsPushButton', ''))

        # createNewBackupWindow
        self.createNewBackupWindow.backPushButton.clicked.connect(lambda: self.eventHandler('createNewBackupWindow', 'backPushButton', ''))
        self.createNewBackupWindow.addFileToListPushButton.clicked.connect(lambda: self.eventHandler('createNewBackupWindow', 'addFileToListPushButton', ''))
        self.createNewBackupWindow.rmFileFromListPushButton.clicked.connect(lambda: self.eventHandler('createNewBackupWindow', 'rmFileFromListPushButton', ''))
        self.createNewBackupWindow.browsePushButton.clicked.connect(lambda: self.eventHandler('createNewBackupWindow', 'browsePushButton', ''))
        self.createNewBackupWindow.nextPushButton.clicked.connect(lambda: self.eventHandler('createNewBackupWindow', 'nextPushButton', ''))

        # saveBackupWindow
        self.saveBackupWindow.backupNameLineEdit.textChanged.connect(lambda: self.eventHandler('saveBackupWindow', 'backupNameLineEdit', ''))
        self.saveBackupWindow.choosePushButton.clicked.connect(lambda: self.eventHandler('saveBackupWindow', 'choosePushButton', ''))
        self.saveBackupWindow.backPushButton.clicked.connect(lambda: self.eventHandler('saveBackupWindow', 'backPushButton', ''))
        self.saveBackupWindow.startPushButton.clicked.connect(lambda: self.eventHandler('saveBackupWindow', 'startPushButton', ''))

        # completionWindow
        self.completionWindow.homePushButton.clicked.connect(lambda: self.eventHandler('completionWindow', 'homePushButton', ''))

        # restoreWindow
        self.restoreWindow.selectPushButton.clicked.connect(lambda: self.eventHandler('restoreWindow', 'selectPushButton', ''))
        self.restoreWindow.browsePushButton.clicked.connect(lambda: self.eventHandler('restoreWindow', 'browsePushButton', ''))
        self.restoreWindow.backPushButton.clicked.connect(lambda: self.eventHandler('restoreWindow', 'backPushButton', ''))
        self.restoreWindow.startPushButton.clicked.connect(lambda: self.eventHandler('restoreWindow', 'startPushButton', ''))

        # useTemplateWindow
        self.useTemplateWindow.backPushButton.clicked.connect(lambda: self.eventHandler('useTemplateWindow', 'backPushButton', ''))
        self.useTemplateWindow.startPushButton.clicked.connect(lambda: self.eventHandler('useTemplateWindow', 'startPushButton', ''))

        # settingsWindow
        self.settingsWindow.savePushButton.clicked.connect(lambda: self.eventHandler('settingsWindow', 'savePushButton', ''))
        self.settingsWindow.backPushButton.clicked.connect(lambda: self.eventHandler('settingsWindow', 'backPushButton', ''))
        self.settingsWindow.choosePushButton.clicked.connect(lambda: self.eventHandler('settingsWindow', 'choosePushButton', ''))

        # aboutWindow
        self.aboutWindow.closePushButton.clicked.connect(lambda: self.eventHandler('aboutWindow', 'closePushButton', ''))


        # Variables
        self.listItems = []

        self.entryPoint.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
