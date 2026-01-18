# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mpu9250.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.label_mpu_acc_x = QLabel(self.centralwidget)
        self.label_mpu_acc_x.setObjectName(u"label_mpu_acc_x")
        self.label_mpu_acc_x.setGeometry(QRect(200, 50, 81, 17))
        self.label_mpu_acc_z = QLabel(self.centralwidget)
        self.label_mpu_acc_z.setObjectName(u"label_mpu_acc_z")
        self.label_mpu_acc_z.setGeometry(QRect(200, 110, 81, 17))
        self.label_mpu_acc_y = QLabel(self.centralwidget)
        self.label_mpu_acc_y.setObjectName(u"label_mpu_acc_y")
        self.label_mpu_acc_y.setGeometry(QRect(200, 80, 81, 17))
        self.checkBox_acc_x = QCheckBox(self.centralwidget)
        self.checkBox_acc_x.setObjectName(u"checkBox_acc_x")
        self.checkBox_acc_x.setGeometry(QRect(60, 50, 91, 22))
        self.checkBox_acc_y = QCheckBox(self.centralwidget)
        self.checkBox_acc_y.setObjectName(u"checkBox_acc_y")
        self.checkBox_acc_y.setGeometry(QRect(60, 80, 91, 22))
        self.checkBox_acc_z = QCheckBox(self.centralwidget)
        self.checkBox_acc_z.setObjectName(u"checkBox_acc_z")
        self.checkBox_acc_z.setGeometry(QRect(60, 110, 91, 22))
        self.label_mpu_angval_y = QLabel(self.centralwidget)
        self.label_mpu_angval_y.setObjectName(u"label_mpu_angval_y")
        self.label_mpu_angval_y.setGeometry(QRect(200, 200, 101, 17))
        self.checkBox_angval_x = QCheckBox(self.centralwidget)
        self.checkBox_angval_x.setObjectName(u"checkBox_angval_x")
        self.checkBox_angval_x.setGeometry(QRect(60, 170, 91, 22))
        self.label_mpu_angval_x = QLabel(self.centralwidget)
        self.label_mpu_angval_x.setObjectName(u"label_mpu_angval_x")
        self.label_mpu_angval_x.setGeometry(QRect(200, 170, 121, 17))
        self.label_mpu_angval_z = QLabel(self.centralwidget)
        self.label_mpu_angval_z.setObjectName(u"label_mpu_angval_z")
        self.label_mpu_angval_z.setGeometry(QRect(200, 230, 101, 17))
        self.checkBox_angval_z = QCheckBox(self.centralwidget)
        self.checkBox_angval_z.setObjectName(u"checkBox_angval_z")
        self.checkBox_angval_z.setGeometry(QRect(60, 230, 91, 22))
        self.checkBox_angval_y = QCheckBox(self.centralwidget)
        self.checkBox_angval_y.setObjectName(u"checkBox_angval_y")
        self.checkBox_angval_y.setGeometry(QRect(60, 200, 91, 22))
        self.label_mpu_mag_y = QLabel(self.centralwidget)
        self.label_mpu_mag_y.setObjectName(u"label_mpu_mag_y")
        self.label_mpu_mag_y.setGeometry(QRect(200, 310, 81, 17))
        self.checkBox_mag_x = QCheckBox(self.centralwidget)
        self.checkBox_mag_x.setObjectName(u"checkBox_mag_x")
        self.checkBox_mag_x.setGeometry(QRect(60, 280, 91, 22))
        self.label_mpu_mag_x = QLabel(self.centralwidget)
        self.label_mpu_mag_x.setObjectName(u"label_mpu_mag_x")
        self.label_mpu_mag_x.setGeometry(QRect(200, 280, 81, 17))
        self.label_mpu_mag_z = QLabel(self.centralwidget)
        self.label_mpu_mag_z.setObjectName(u"label_mpu_mag_z")
        self.label_mpu_mag_z.setGeometry(QRect(200, 340, 81, 17))
        self.checkBox_mag_z = QCheckBox(self.centralwidget)
        self.checkBox_mag_z.setObjectName(u"checkBox_mag_z")
        self.checkBox_mag_z.setGeometry(QRect(60, 340, 91, 22))
        self.checkBox_max_y = QCheckBox(self.centralwidget)
        self.checkBox_max_y.setObjectName(u"checkBox_max_y")
        self.checkBox_max_y.setGeometry(QRect(60, 310, 91, 22))
        self.lineEdit_IP_Address = QLineEdit(self.centralwidget)
        self.lineEdit_IP_Address.setObjectName(u"lineEdit_IP_Address")
        self.lineEdit_IP_Address.setGeometry(QRect(190, 430, 221, 25))
        self.lineEdit_PORT = QLineEdit(self.centralwidget)
        self.lineEdit_PORT.setObjectName(u"lineEdit_PORT")
        self.lineEdit_PORT.setGeometry(QRect(430, 430, 113, 25))
        self.pushButton_start = QPushButton(self.centralwidget)
        self.pushButton_start.setObjectName(u"pushButton_start")
        self.pushButton_start.setGeometry(QRect(80, 430, 94, 25))
        self.pushButton_end = QPushButton(self.centralwidget)
        self.pushButton_end.setObjectName(u"pushButton_end")
        self.pushButton_end.setEnabled(False)
        self.pushButton_end.setGeometry(QRect(80, 480, 94, 25))
        self.label_status = QLabel(self.centralwidget)
        self.label_status.setObjectName(u"label_status")
        self.label_status.setGeometry(QRect(80, 400, 461, 17))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_mpu_acc_x.setText(QCoreApplication.translate("MainWindow", u"mpu_acc_x", None))
        self.label_mpu_acc_z.setText(QCoreApplication.translate("MainWindow", u"mpu_acc_z", None))
        self.label_mpu_acc_y.setText(QCoreApplication.translate("MainWindow", u"mpu_acc_y", None))
        self.checkBox_acc_x.setText(QCoreApplication.translate("MainWindow", u"acc_x", None))
        self.checkBox_acc_y.setText(QCoreApplication.translate("MainWindow", u"acc_y", None))
        self.checkBox_acc_z.setText(QCoreApplication.translate("MainWindow", u"acc_z", None))
        self.label_mpu_angval_y.setText(QCoreApplication.translate("MainWindow", u"mpu_angval_y", None))
        self.checkBox_angval_x.setText(QCoreApplication.translate("MainWindow", u"angval_x", None))
        self.label_mpu_angval_x.setText(QCoreApplication.translate("MainWindow", u"mpu_angval_x", None))
        self.label_mpu_angval_z.setText(QCoreApplication.translate("MainWindow", u"mpu_angval_z", None))
        self.checkBox_angval_z.setText(QCoreApplication.translate("MainWindow", u"angval_z", None))
        self.checkBox_angval_y.setText(QCoreApplication.translate("MainWindow", u"angval_y", None))
        self.label_mpu_mag_y.setText(QCoreApplication.translate("MainWindow", u"mpu_mag_y", None))
        self.checkBox_mag_x.setText(QCoreApplication.translate("MainWindow", u"mag_x", None))
        self.label_mpu_mag_x.setText(QCoreApplication.translate("MainWindow", u"mpu_mag_x", None))
        self.label_mpu_mag_z.setText(QCoreApplication.translate("MainWindow", u"mpu_mag_z", None))
        self.checkBox_mag_z.setText(QCoreApplication.translate("MainWindow", u"mag_z", None))
        self.checkBox_max_y.setText(QCoreApplication.translate("MainWindow", u"mag_y", None))
        self.lineEdit_IP_Address.setText(QCoreApplication.translate("MainWindow", u"IP address", None))
        self.lineEdit_PORT.setText(QCoreApplication.translate("MainWindow", u"PORT", None))
        self.pushButton_start.setText(QCoreApplication.translate("MainWindow", u"START", None))
        self.pushButton_end.setText(QCoreApplication.translate("MainWindow", u"END", None))
        self.label_status.setText(QCoreApplication.translate("MainWindow", u"Unconnected", None))
    # retranslateUi

