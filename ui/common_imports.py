from tkinter import dialog
from dotenv import load_dotenv
# import sys, os, re, json, getpass, base64, requests
from datetime import datetime
# PyQt5
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLineEdit, QDateEdit, QMessageBox, QLabel, QRadioButton, QButtonGroup,
    QShortcut, QListWidgetItem, QGraphicsOpacityEffect, QProgressDialog,QDialog, QVBoxLayout, QListWidget, QPushButton,
       QInputDialog,QTableWidget, QTableWidgetItem,QHeaderView
)
from PyQt5.QtCore import QDate, QTimer, Qt, QSize, QPropertyAnimation,QThread, pyqtSignal,QObject

from PyQt5.QtGui import QKeySequence,QColor

# Exchange
# from exchangelib import FolderCollection, Credentials, Account, DELEGATE, Configuration,Q
# from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
import warnings
import urllib3
