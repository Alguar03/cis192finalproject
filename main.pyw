import operator
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time
from analyzer import Analyzer
from crawler import Crawler


class MyWindow(QWidget):
    '''Is the main window for our program'''
    def __init__(self, element_list, header, *args):
        QWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(100, 100, 800, 750)
        self.setWindowTitle(\
        "Monetize IT - By Andrew Staniforth, Connie Wu, and Fred Wang")
        self.button = QPushButton("Start")
        self.button.clicked.connect(self.start_analyzing)
        label = QLabel("SORRY, NO README FOUND :(")
        label.setAlignment(Qt.AlignHCenter)

        try:
            openfile = open("desc.txt", "r")
            label = QLabel(openfile.read())
            openfile.close()
            readmefont = label.font()
            readmefont.setPointSize(8)
            label.setFont(readmefont)
            label.setAlignment(Qt.AlignLeft)
            label.setWordWrap(True)

        except:
            pass
        welcome = QLabel("Welcome to Monetize IT!")
        welcome.setAlignment(Qt.AlignHCenter)
        font = welcome.font()
        font.setBold(True)
        font.setPointSize(20)
        welcome.setFont(font)

        self.header = header
        self.mydata = element_list
        # create table
        self.tmodel = MyTableModel(self, self.mydata, self.header)
        self.tview = QTableView()
        table = self.createTable()
        #Allows autosorting by score
        self.cb = QCheckBox('Automatically Sort By Score (Cannot be' +
                            'changed after you start analyzing)', self)
        self.cb.toggle()
        self.sort = True
        self.cb.stateChanged.connect(self.autosort)

        # use vbox layout
        layout = QVBoxLayout()
        layout.addWidget(welcome)
        layout.addWidget(table)
        layout.addWidget(self.button)
        layout.addWidget(self.cb)
        line = QLabel()
        line.setFrameStyle(QFrame.HLine | QFrame.Plain)
        line.setLineWidth(2)
        layout.addWidget(line)
        layout.addWidget(label)

        self.setLayout(layout)

    def createTable(self):
        # create table view
        tview = QTableView()
        # set table model
        #tmodel = MyTableModel(self, self.mydata, self.header)
        tview.setModel(self.tmodel)

        # set minimum size of table
        tview.setMinimumSize(450, 300)
        # hide grid
        tview.setShowGrid(True)
        tview.setAlternatingRowColors(True)
        # set font
        font = QFont("Courier New", 8)
        tview.setFont(font)
        # hide vertical header
        vh = tview.verticalHeader()
        vh.setVisible(False)
        # set horizontal header properties
        hh = tview.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setResizeMode(3)
        # set column width to fit contents
        #tview.resizeColumnsToContents()
        # set all row heights
        nrows = len(self.mydata)
        ncols = len(self.header)
        for row in range(nrows):
            tview.setRowHeight(row, 18)
        # enable sorting
        tview.setSortingEnabled(True)
        tview.resizeColumnsToContents()
        return tview

    def start_analyzing(self):
        self.cb.setEnabled(False)
        self.threads = []
        downloader_caller = DownloadCaller(self.tmodel, self.tview, self.sort)
        self.threads.append(downloader_caller)
        downloader_caller.start()

    def autosort(self, state):
        if state == Qt.Checked:
            self.sort = True
        else:
            self.sort = False


class DownloadCaller(QThread):
    ''' Starts a thread that starts the crawler and analyzer threads'''
    def __init__(self, model, tview, sort):
        QThread.__init__(self)
        openfile = open("top_sites.txt", 'r')
        self.urls = openfile.readlines()
        self.urls.reverse()
        openfile.close()
        self.model = model
        self.tview = tview
        self.threads = []
        self.sort = sort

    def run(self):
        for url in self.urls:
            downloader = DownloadThread(url, self.model, self.tview, self.sort)
            self.threads.append(downloader)
            downloader.start()
            #time.sleep(2)


class DownloadThread(QThread):
    ''' Starts threads for each site's crawler and analyzer threads'''
    def __init__(self, url, model, tview, sort):
        QThread.__init__(self)
        self.url = url
        self.model = model
        self.tview = tview
        self.sort = sort
        try:
            c = Crawler()
            self.html_name, self.url_name = c.crawler(self.url, 1)
            print self.url_name
        except:
            self.html_name = None
            self.url_name = None

    def run(self):
        if self.html_name is not None or self.url_name is not None:
            a = Analyzer(self.html_name, self.url_name)
            #print self.url
            if a.getUniqueVisitors() > 0:
                total_ads, number_of_lines = a.getAds()
                self.model.mydata = self.model.mydata + \
                [(self.url, number_of_lines, total_ads, a.unique_visitors,\
                (float(a.unique_visitors) / float(a.getVisits())), \
                a.getScore())]
                #self.tview.resizeColumnsToContents()
                if self.sort:
                    print self.sort
                    self.model.sort(5, Qt.DescendingOrder)
                self.model.emit(SIGNAL("layoutChanged()"))


class MyTableModel(QAbstractTableModel):
    ''' Is the model for the table in the GUI'''
    def __init__(self, parent, mydata, header, *args):
        """
        mydata is list of tuples
        header is list of strings
        tuple length has to match header length
        """
        QAbstractTableModel.__init__(self, parent, *args)
        self.mydata = mydata
        self.header = header

    def rowCount(self, parent):
        return len(self.mydata)

    def columnCount(self, parent):
        if len(self.mydata) > 0:
            return len(self.mydata[0])
        else:
            return 0

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.mydata[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.header[col])
        return QVariant()

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mydata = sorted(self.mydata,
            key=operator.itemgetter(col))
        if order != Qt.DescendingOrder:
            self.mydata.reverse()
        self.emit(SIGNAL("layoutChanged()"))


if __name__ == "__main__":
    header = ['URL', 'Lines in Source', '# Ads', 'Unique Visits',\
              'Retention Rate', 'Score']
    # a list of (name, age, weight) tuples
    data_list = []

    #data_list= data_list+ [('Michel', 'Sargnagel', '21', '175')]
    app = QApplication([])
    splash_pix = QPixmap('SPLASH.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    time.sleep(5)
    win = MyWindow(data_list, header)
    win.show()
    splash.finish(win)
    app.exec_()

