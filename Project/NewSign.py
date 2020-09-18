import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import MainWindow1
import imap
import Normail
import Lgmail
import WhiteList
import BlackList
import pickle
import Setting
import MyMsg
import WarningBox
import SpecialList
import Associate_List
import os
from PyQt5 import QtCore, QtMultimedia

from socket import *
from PyQt5.QtGui import *

address = '42.159.155.29'
port = 8000
buffsize = 1024
received_mails = {'垃圾邮件': [], '正常邮件': []}  # 存储往期邮件
s = socket(AF_INET, SOCK_STREAM)
flag = 0
finish = 0
if_login = dict()
count = [0]
AThread = Associate_List.AssoThread()


# 获取绝对路径
url_father = os.path.dirname(os.path.abspath(__file__))

# 因为styleSheet里正斜杠才管用，我要把反斜杠转化为正斜杠
os_url = ""
for i in url_father:
    if (i == "\\"):
        os_url = os_url + "/"
    else:
        os_url = os_url + i


################################################
#######创建主窗口
################################################



class BackendThread(QThread):

    def __init__(self, im):
        super().__init__()
        self.im = im
        self.result = list()
        self.im.init()

    update_email = pyqtSignal(dict)

    def run(self):
        global received_mails
        global flag
        global s
        #  连接服务器
        temp = dict()
        temp.update({'功能':'download'})
        temp.update({'用户': self.im.user})
        s.send(str(temp).encode('utf-8'))
        receive = s.recv(buffsize).decode('utf-8')  # 接收结果
        receive = eval(receive)
        if receive['result'] == 'exist':
            black = receive['黑名单'].split()  # 更新本地黑名单
            white = receive['白名单'].split()  # 接收白名单
            special = receive['特别关心'].split()  # 接收特别关心
            associate = receive['关联邮箱'].split()  # 接收关联邮箱
            if black != '0':
                imap.black_list = black
            if white != '0':
                imap.white_list = white
            if special != '0':
                imap.special_list = special
            if associate !='0':
                imap.associate_list = associate
            imap.save_path = receive['路径']
        global finish
        finish = 1
        s.settimeout(30)
        received_mails = self.im.get_all_mails(s)
        s.send(str(dict({'功能':'exit'})).encode('utf-8'))
        s.close()
        # 断开连接
        flag = 1
        while True:
            self.result = self.im.get_new_mail()
            if self.result is not None:
                for each in self.result:
                    if each['垃圾'] == 2:
                        self.update_email.emit(each)
                        received_mails['正常邮件'].append(each)
                    elif each['垃圾'] == 1:
                        self.update_email.emit(each)
                        received_mails['垃圾邮件'].append(each)
                    else:
                        self.update_email.emit(each)
                        received_mails['正常邮件'].append(each)
                    time.sleep(1)
            time.sleep(2)

class MainWindow(QMainWindow, MainWindow1.Ui_MainWindow):
    windowList = []

    def __init__(self, im, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_father = os.path.dirname(os.path.abspath(__file__))
        self.setupUi(self)
        self.setWindowTitle('主界面')
        self.im = im
        self.m_flag = False
        self.m_Position = 0
        self.backend = None
        self.printAction1 = None
        self.printAction2 = None
        self.printMenu = None
        url = self.url_father+'\\pickle\\extra_list.pkl'
        pickle_file = open(url, 'rb')
        Lgmail.extra_list = pickle.load(pickle_file)
        self.setFixedSize(self.width(), self.height())
        self.setStyleSheet('''
                            QWidget{
                                    border-radius:15px;
                                    border:none;}''')

        self.url_1 = QtCore.QUrl.fromLocalFile(r"music/1.wav")
        self.url_2 = QtCore.QUrl.fromLocalFile(r"music/2.wav")
        self.url_3 = QtCore.QUrl.fromLocalFile(r"music/3.wav")
        self.content_1 = QtMultimedia.QMediaContent(self.url_1)
        self.content_2 = QtMultimedia.QMediaContent(self.url_2)
        self.content_3 = QtMultimedia.QMediaContent(self.url_3)
        self.player_1 = QtMultimedia.QMediaPlayer()
        self.player_2 = QtMultimedia.QMediaPlayer()
        self.player_3 = QtMultimedia.QMediaPlayer()
        self.player_1.setMedia(self.content_1)
        self.player_2.setMedia(self.content_2)
        self.player_3.setMedia(self.content_3)
        self.player_1.setVolume(50.0)
        self.player_2.setVolume(50.0)
        self.player_3.setVolume(50.0)

        # 添加设置按钮
        self.setting = QPushButton(self)
        self.setting.setGeometry(470, 365, 25, 25)
        self.setting.clicked.connect(lambda: self.onBtn_Setting(self.im.user))
        self.setting.setStyleSheet('''
                                    QPushButton{
                                        border-image:url(''' + os_url + '''/images/set1.png);}
                                    QPushButton:hover{
                                        border-image:url(''' + os_url + '''/images/set.png);}
                                    ''')


        # 添加最小化按钮
        self.pushButton_min = QPushButton(self)
        self.pushButton_min.setGeometry(416, 10, 15, 15)
        self.pushButton_min.setToolTip('最小化')
        self.pushButton_min.setObjectName("pushButton_min")
        self.pushButton_min.setStyleSheet('''
                                                        QPushButton{
                                                            border-image:url(''' + os_url + '''/images/graymin.png);}
                                                        QPushButton:hover{
                                                            border-image:url(''' + os_url + '''/images/redmin.png);}
                                                        ''')
        self.tray = QSystemTrayIcon(self)  # 创建系统托盘对象
        self.icon = QIcon(os_url + '/images/nlogo.png')  # 创建图标
        self.tray.setIcon(self.icon)  # 设置系统托盘图标

        # 添加注销按钮
        self.pushButton_logout = QPushButton(self)
        self.pushButton_logout.setGeometry(QRect(442, 9, 17, 17))
        self.pushButton_logout.setToolTip('注销')
        self.pushButton_logout.setObjectName("pushButton_logout")
        self.pushButton_logout.setStyleSheet('''
                                                QPushButton{
                                                    border-image:url(''' + os_url + '''/images/graylogout.png);}
                                                QPushButton:hover{
                                                    border-image:url(''' + os_url + '''/images/redlogout.png);}
                                                            ''')

        # 添加关闭按钮
        self.pushButton_close = QPushButton(self)
        self.pushButton_close.setGeometry(QRect(470, 10, 15, 15))
        self.pushButton_close.setToolTip('退出')
        self.pushButton_close.setObjectName("pushButton_close")
        self.pushButton_close.setStyleSheet('''
                                                 QPushButton{
                                                    border-image:url(''' + os_url + '''/images/grayclose.png);}
                                                QPushButton:hover{
                                                    border-image:url(''' + os_url + '''/images/redclose.png);}
                                                            ''')

        # 绑定按钮监听事件
        self.pushButton_min.clicked.connect(self.minimized)
        self.pushButton_logout.clicked.connect(self.on_printAction1_triggered)
        self.pushButton_close.clicked.connect(self.on_printAction2_triggered)

        # 创建菜单栏
        # self.createMenus()
        # 后台监控邮件
        self.initMonitor()
        self.normailBtn.clicked.connect(self.onBtn_Normail)
        self.lgmailBtn.clicked.connect(self.onBtn_Lgmail)
        self.whiteBtn.clicked.connect(self.onBtn_WhiteList)
        self.blackBtn.clicked.connect(self.onBtn_BlackList)
        self.c.clicked.connect(self.onBtn_Special)
        self.conBtn.clicked.connect(self.onBtn_Associate)
    def minimized(self):
        # self.showMinimized()
        self.hide()

        self.tray.show()
        self.tray.activated[QSystemTrayIcon.ActivationReason].connect(self.TuoPanEvent)  # 设置托盘点击事件处理函数
        self.tray_menu = QMenu(QApplication.desktop())  # 创建菜单
        self.RestoreAction = QAction(u'还原 ', self, triggered=self.show)  # 添加一级菜单动作选项(还原主窗口)
        self.QuitAction = QAction(u'退出 ', self, triggered=qApp.quit)  # 添加一级菜单动作选项(退出程序)
        self.tray_menu.addAction(self.RestoreAction)  # 为菜单添加动作
        self.tray_menu.addAction(self.QuitAction)
        self.tray.setContextMenu(self.tray_menu)

    def TuoPanEvent(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.show()

    def onBtn_Setting(self, str):
        if finish == 1:
            set = Setting.SettingUi(str, self.theme)
            set.sureBtn.clicked.connect(lambda: self.setBackground(set.combox.currentIndex()))
            set.exec()
        else:
            reply = WarningBox.WarningBox('初始化未完成')
            reply.show()

    def setBackground(self, x):
        pal = self.palette()
        self.theme = x
        if x == 1:
            icon = QPixmap(os_url + "/images/background2.jpg")
        elif x == 0:
            icon = QPixmap(os_url + "/images/3.jpg")
        url = self.url_father+'\\pickle\\theme.pkl'
        pickle_file = open(url, 'wb')
        pickle.dump(x, pickle_file)
        pickle_file.close()
        pal.setBrush(self.backgroundRole(), QBrush(icon.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(pal)


    def initMonitor(self):
        self.backend = BackendThread(self.im)
        self.backend.update_email.connect(self.handleDisplay)
        self.backend.start()

    def handleDisplay(self, content):
        topic = content['主题']
        send = content['发件人']
        send_time = content['时间']
        if content['垃圾'] == 1:
            ip = content['IP地址']
            message = ('您收到1封来自'+ send[:20] +'\n发往\n'+content['收件人']+ '的垃圾邮件\n' + '主题：' + topic[:20] +
                       '\n' + 'ip地址：' + ip + '\n' + '时间：' + send_time + '\n')
            if Setting.pop[1] == 1:
                self.player_2.play()
        elif content['垃圾'] == 2:
            message = ('您收到1封来自'+send[:20]+'\n发往'+content['收件人']+'的特别关心邮件\n' + '主题：' + topic[:20] +
                        '\n' + '时间：' + send_time + '\n')
            if Setting.pop[1] == 1:
                self.player_3.play()
        else:
            message = ('您收到1封来自' + send[:20] +'\n发往'+content['收件人']+ '的正常邮件\n' + '主题：' + topic[:20] +
                       '\n' + '时间：' + send_time + '\n')
            if Setting.pop[1] == 1:
                self.player_1.play()
        if Setting.pop[0] == 1:
            self.temp = MyMsg.MymessageBox(message, content)
            self.temp.show()

    def createMenus(self):
        self.pushButton_logout.clicked.connect(self.on_printAction1_triggered)
        self.pushButton_close.clicked.connect(self.on_printAction2_triggered)

    def onBtn_Normail(self):
        global received_mails
        if flag == 1:
            normail = Normail.NormailUi(self.im, received_mails, self.theme)
            normail.exec()
        else:
            reply = WarningBox.WarningBox('往期邮件扫描未完成')
            reply.exec()

    def onBtn_Lgmail(self):
        global received_mails
        if flag == 1:
            lgmail = Lgmail.LgmailUi(self.im, Lgmail.extra_list, received_mails, self.theme)
            lgmail.exec()
        else:
            reply = WarningBox.WarningBox('往期邮件扫描未完成')
            reply.exec()

    def onBtn_Special(self):
        global received_mails
        if finish == 1:
            bdialog = SpecialList.SpecialListUi(self.im, received_mails, self.theme)
            bdialog.exec()
        else:
            reply = WarningBox.WarningBox('初始化未完成')
            reply.exec()

    def onBtn_WhiteList(self):
        if finish == 1:
            wdialog = WhiteList.WhiteListUi(self.theme)
            wdialog.exec()
        else:
            reply = WarningBox.WarningBox('初始化未完成')
            reply.exec()

    def onBtn_BlackList(self):
        if finish == 1:
            bdialog = BlackList.BlackListUi(self.theme)
            bdialog.exec()
        else:
            reply = WarningBox.WarningBox('初始化未完成')
            reply.exec()

    def onBtn_Associate(self):
        global if_login
        global count
        global AThread1
        global AThread2
        if finish == 1:
            bdialog = Associate_List.AssociateListUi(if_login, count, AThread,self.theme)
            bdialog.exec()
        else:
            reply = WarningBox.WarningBox('初始化未完成')
            reply.exec()

    def update_user(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((address, port))
        temp = dict()
        temp.update({'功能':'update'})
        temp.update({'用户':self.im.user})
        white = " ".join(imap.white_list)
        black = " ".join(imap.black_list)
        special = " ".join(imap.special_list)
        associate = " ".join(imap.associate_list)
        path = imap.save_path
        temp.update({'白名单': white})
        temp.update({'黑名单': black})
        temp.update({'路径': path})
        temp.update({'特别关心': special})
        temp.update({'关联邮箱': associate})
        s.send(str(temp).encode('utf-8'))
        temp = dict()
        temp.update({'功能':'exit'})
        time.sleep(0.3)
        s.send(str(temp).encode('utf-8'))
        global finish
        global received_mails
        finish = 0
        received_mails['正常邮件'].clear()
        received_mails['垃圾邮件'].clear()

    # 动作一：注销
    def on_printAction1_triggered(self):
        global flag
        if flag == 1:
            flag = 0
            global received_mails
            received_mails['正常邮件'].clear()
            received_mails['垃圾邮件'].clear()
            self.update_user()
            self.backend.terminate()
            self.close()
            dialog = Logindialog(mode=1)
            if dialog.exec_() == QDialog.Accepted:
                the_window = MainWindow(self.im)
                self.windowList.append(the_window)  # 这句一定要写，不然无法重新登录
                the_window.show()
        else:
            reply = WarningBox.WarningBox('初始化未完成,无法正常退出')
            reply.exec()
    # 动作二：退出
    def on_printAction2_triggered(self):
        if flag == 1:

            self.backend.terminate()
            self.update_user()
            self.close()
        else:
            reply = WarningBox.WarningBox('初始化未完成,无法正常退出')
            reply.exec()
    # 关闭界面触发事件
    def closeEvent(self, event):
        pass

################################################
#######对话框
################################################


class Logindialog(QDialog):
    def __init__(self, mode=0, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.url_father = os.path.dirname(os.path.abspath(__file__))
        self.im = imap.Imapmail()
        self.m_flag = False
        self.m_Position = 0
        self.mode = mode
        self.setWindowTitle('登录界面')
        self.resize(520, 300)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 设置界面控件
        self.frame = QFrame(self)
        self.frame.resize(400, 300)
        self.frame.move(110, 0)

        self.setWindowOpacity(0.9)  # 设置窗口透明度 yy


        self.lineEdit_account = QLineEdit(self.frame)
        self.lineEdit_account.setPlaceholderText("请输入账号")
        self.lineEdit_account.setGeometry(40, 80, 221, 30)

        # yy
        op = QGraphicsOpacityEffect()  # 控件透明度
        op.setOpacity(0.8)
        self.lineEdit_account.setGraphicsEffect(op)

        self.lineEdit_password = QLineEdit(self.frame)
        self.lineEdit_password.setPlaceholderText("请输入密码")
        self.lineEdit_password.setEchoMode(QLineEdit.Password)
        self.lineEdit_password.setGeometry(40, 120, 221, 30)

        # yy
        op = QGraphicsOpacityEffect()  # 控件透明度
        op.setOpacity(0.8)
        self.lineEdit_password.setGraphicsEffect(op)

        # Times New Roman
        self.lineEdit_account.setStyleSheet('''
                    QLineEdit{
                        color:#4F4F4F;
                        font-family:"Segoe UI";
                        border:solid;
                        background:white;
                        border-radius:10px;
                        padding:2px 4px;}
                        ''')

        self.lineEdit_password.setStyleSheet('''
                    QLineEdit{
                        color:#4F4F4F;
                        border:solid;
                        background:white;
                        border-radius:10px;}
                        ''')

        self.checkBox_remeberpassword = QCheckBox(self.frame)
        self.checkBox_remeberpassword.setGeometry(40, 165, 20, 20)
        self.password = QLabel("记住密码", self.frame)
        self.password.setGeometry(68, 164, 80, 20)


        self.checkBox_autologin = QCheckBox(self.frame)
        self.checkBox_autologin.setGeometry(160, 165, 20, 20)
        self.autologin = QLabel("自动登录", self.frame)
        self.autologin.setGeometry(188, 164, 80, 20)

        self.checkBox_remeberpassword.setStyleSheet('''
                        QCheckBox{
                            font-family:"STXihei";
                            font-size: 10.5pt;
                            color: #9C9C9C;}
                        QCheckBox::indicator { 
                            width: 20px;
                            height: 20px;}
                        QCheckBox::indicator::checked{
                            image:url(''' + os_url + '''/images/checked.png);}
                        QCheckBox::indicator::unchecked{
                            image:url(''' + os_url + '''/images/unchecked.png);}
                        ''')
        self.password.setStyleSheet('''
                        QLabel{
                            font-family:"STXihei";
                            font-size: 10.5pt;
                            color: #9C9C9C;}''')

        self.checkBox_autologin.setStyleSheet('''
                        QCheckBox{
                            font-family:"STXihei";
                            font-size: 10.5pt;
                            color: #9C9C9C;}
                        QCheckBox::indicator { 
                            width: 20px;
                            height: 20px;}
                        QCheckBox::indicator::checked{
                            image:url(''' + os_url + '''/images/checked.png);}
                        QCheckBox::indicator::unchecked{
                            image:url(''' + os_url + '''/images/unchecked.png);}
                        ''')
        self.autologin.setStyleSheet('''
                                QLabel{
                                    font-family:"STXihei";
                                    font-size: 10.5pt;
                                    color: #9C9C9C;}''')

        # 关闭按钮
        self.pushButton_close = QPushButton(self)
        self.pushButton_close.setGeometry(QRect(495, 10, 15, 15))
        self.pushButton_close.setToolTip('退出')
        self.pushButton_close.setObjectName("pushButton_close")
        self.pushButton_close.setStyleSheet('''
                                 QPushButton{
                                    border-image:url(''' + os_url + '''/images/grayclose.png);}
                                QPushButton:hover{
                                    border-image:url(''' + os_url + '''/images/redclose.png);}
                                            ''')
        # yy 最小化按钮
        self.pushButton_min = QPushButton(self)
        self.pushButton_min.setGeometry(465, 10, 15, 15)
        self.pushButton_min.setToolTip('最小化')
        self.pushButton_min.setObjectName("pushButton_min")
        self.pushButton_min.setStyleSheet('''
                                                QPushButton{
                                                    border-image:url(''' + os_url + '''/images/graymin.png);}
                                                QPushButton:hover{
                                                    border-image:url(''' + os_url + '''/images/redmin.png);}
                                                ''')

        self.pushButton_enter = QPushButton(self.frame)
        self.pushButton_enter.setText("确定")
        self.pushButton_enter.setGeometry(40, 200, 101, 31)

        stlsheet = '''QPushButton
                                             {text-align : center;
                                             background-color : white;
                                             font: bold;
                                             font-family: 幼圆;
                                             border-color: gray;
                                             border-width: 2px;
                                             border-radius: 10px;
                                             padding: 6px;
                                             height : 14px;
                                             border-style: outset;
                                             font : 14px;}
                                             QPushButton:pressed
                                             {text-align : center;
                                             background-color : light gray;
                                             font: bold;
                                             border-color: gray;
                                             border-width: 2px;
                                             border-radius: 10px;
                                             padding: 6px;
                                             height : 14px;
                                             border-style: outset;
                                             font : 14px;}'''

        # yy
        self.pushButton_enter.setStyleSheet(stlsheet)
        op = QGraphicsOpacityEffect()  # 控件透明度
        op.setOpacity(0.8)
        self.pushButton_enter.setGraphicsEffect(op)

        self.pushButton_quit = QPushButton(self.frame)
        self.pushButton_quit.setText("取消")
        self.pushButton_quit.setGeometry(160, 200, 101, 31)

        # yy
        self.pushButton_quit.setStyleSheet(stlsheet)
        op = QGraphicsOpacityEffect()  # 控件透明度
        op.setOpacity(0.8)
        self.pushButton_quit.setGraphicsEffect(op)

        # 绑定按钮事件
        self.pushButton_enter.clicked.connect(self.on_pushButton_enter_clicked)
        self.pushButton_quit.clicked.connect(QCoreApplication.instance().quit)
        self.pushButton_close.clicked.connect(QCoreApplication.instance().quit)
        self.pushButton_min.clicked.connect(self.minimized)

        # 初始化登录信息
        self.init_login_info()

        # 自动登录
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.goto_autologin)
        self.timer.setSingleShot(True)
        self.timer.start(1000)

        url = self.url_father+'\\pickle\\theme.pkl'
        pickle_file = open(url, 'rb')
        self.theme = pickle.load(pickle_file)
        pickle_file.close()

    def minimized(self):
        self.showMinimized()

    # 登录界面背景 yy
    def paintEvent(self, event):  # set background_img
        painter = QPainter(self)
        painter.drawRect(self.rect())
        # pixmap = QPixmap("images/gray/3.jpg")  # 换成自己的图片的相对路径
        if self.theme == 1:
            pixmap = QPixmap(os_url + "/images/background1.jpg")
        elif self.theme == 0:
            pixmap = QPixmap(os_url + "/images/3.jpg")
        painter.drawPixmap(self.rect(), pixmap)

    # 自动登录
    def goto_autologin(self):
        if self.checkBox_autologin.isChecked() == True and self.mode == 0:
            self.on_pushButton_enter_clicked()

    # 验证登录信息
    def on_pushButton_enter_clicked(self):
        global s
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(5)
        if_connect = 0
        try:
            s.connect((address, port))
            if_connect = 1
        except BaseException as e:
            print(e)
            if_connect = 0
        finally:
            if if_connect == 1:
                self.im.user = self.lineEdit_account.text()
                self.im.password = self.lineEdit_password.text()
                self.im.server_address = 'imap.' + self.im.user.split('@')[-1]  # 邮箱地址
                if self.im.user.split('@')[-1] in ['163.com', 'qq.com', '126.com']:
                    self.im.client()
                    e = self.im.login()
                    if e == 0:
                        reply = WarningBox.WarningBox('账号或密码输入错误')
                        reply.exec()
                        s.send(str(dict({'功能':'exit'})).encode('utf-8'))
                    else:
                        self.save_login_info()
                        # 通过验证，关闭对话框并返回1
                        self.accept()
                else:
                    reply = WarningBox.WarningBox('邮箱格式不正确')
                    reply.exec()
                    s.send(str(dict({'功能': 'exit'})).encode('utf-8'))
            else:
                reply = WarningBox.WarningBox('连接服务器失败')
                reply.exec()
    def get_imap(self):
        return self.im

    # 保存登录信息
    def save_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)  # 方法1：使用配置文件
        settings.setValue("account", self.lineEdit_account.text())
        settings.setValue("password", self.lineEdit_password.text())
        settings.setValue("remeberpassword", self.checkBox_remeberpassword.isChecked())
        settings.setValue("autologin", self.checkBox_autologin.isChecked())

    # 初始化登录信息
    def init_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)  # 方法1：使用配置文件
        the_account = settings.value("account")
        the_password = settings.value("password")
        the_remeberpassword = settings.value("remeberpassword")
        the_autologin = settings.value("autologin")
        self.lineEdit_account.setText(the_account)
        if the_remeberpassword == "true" or the_remeberpassword == True:
            self.checkBox_remeberpassword.setChecked(True)
            self.lineEdit_password.setText(the_password)

        if the_autologin == "true" or the_autologin == True:
            self.checkBox_autologin.setChecked(True)

    #  鼠标拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = Logindialog(mode=0)
    im = dialog.get_imap()
    if dialog.exec_()== QDialog.Accepted:
        the_window = MainWindow(im)
        the_window.paintEngine()
        the_window.show()
        sys.exit(app.exec_())
