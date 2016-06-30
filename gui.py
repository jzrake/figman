import os
from PySide import QtGui, QtCore



class FileBrowser(QtGui.QWidget):

    class Signals(QtCore.QObject):
        file_changed = QtCore.Signal(str)
        dir_changed = QtCore.Signal(str)


    def __init__(self, parent=None):
        super(FileBrowser, self).__init__(parent)

        model = QtGui.QFileSystemModel()
        model.setReadOnly(True)
        model.setNameFilters(["*.py"])
        model.setNameFilterDisables(False)
        model.directoryLoaded.connect(self.resize_tree_view)
        model.setRootPath(os.getcwd())

        tree_view = QtGui.QTreeView()
        tree_view.setModel(model)
        tree_view.setRootIndex(model.index(os.getcwd()))
        tree_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        tree_view.hideColumn(1)
        tree_view.hideColumn(2)

        selection_model = tree_view.selectionModel()
        selection_model.currentChanged.connect(self.handle_current_changed)

        watcher = QtCore.QFileSystemWatcher()
        watcher.fileChanged.connect(self.current_file_modified)

        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.timer_timed_out)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(tree_view)
        layout.setContentsMargins(0,0,0,0)

        self.setLayout(layout)
        self.model = model
        self.tree_view = tree_view
        self.watcher = watcher
        self.timer = timer
        self.signals = self.Signals()


    def resize_tree_view(self):
        for i in range(4):
            self.tree_view.resizeColumnToContents(i)


    def handle_current_changed(self, index):
        filename = self.model.filePath(index)
        self.current_filename = filename
        for f in self.watcher.files():
            self.watcher.removePath(f)
        if os.path.isfile(filename):
            self.watcher.addPath(filename)
            self.signals.file_changed.emit(filename)
        elif os.path.isdir(filename):
            self.signals.dir_changed.emit(filename)


    def current_file_modified(self):
        if self.timer.isActive():
            pass
        else:
            self.timer.start(250)


    def timer_timed_out(self):
        self.signals.file_changed.emit(self.current_filename)



class PlottingArea(QtGui.QWidget):

    def __init__(self):
        super(PlottingArea, self).__init__()

        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
        from matplotlib.figure import Figure

        fig = Figure()

        canvas = FigureCanvas(fig)
        navbar = NavigationToolbar(canvas, self)

        layout = QtGui.QGridLayout()
        layout.addWidget(canvas, 0, 1, 4, 1)
        layout.addWidget(navbar, 4, 1)
        layout.setContentsMargins(0,0,0,0)

        self.setLayout(layout)

        self.fig = fig
        self.canvas = canvas
        self.navbar = navbar



class MainWindow(QtGui.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(1200, 800)
        self.setWindowTitle("Figman")

        preferred = QtGui.QSizePolicy.Preferred
        maximum = QtGui.QSizePolicy.Maximum
        spL = QtGui.QSizePolicy(maximum, preferred)
        spR = QtGui.QSizePolicy(preferred, preferred)
        spL.setHorizontalStretch(1)
        spR.setHorizontalStretch(2)

        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        font.setPointSize(10)

        file_browser = FileBrowser()
        fig_list = QtGui.QListWidget()
        output_display = QtGui.QTextEdit()
        plotting_area = PlottingArea()

        watcher = QtCore.QFileSystemWatcher()
        watcher.fileChanged.connect(self.load_python_source_file)

        file_browser.setSizePolicy(spL)
        fig_list.setSizePolicy(spL)
        output_display.setSizePolicy(spL)
        plotting_area.setSizePolicy(spR)

        file_browser.signals.file_changed.connect(self.set_python_source_file)
        fig_list.currentItemChanged.connect(self.set_plot_function)

        output_display.setReadOnly(True)
        output_display.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        output_display.setCurrentFont(font)

        columnL = QtGui.QVBoxLayout()
        columnR = QtGui.QVBoxLayout()

        columnL.addWidget(file_browser)
        columnL.addWidget(fig_list)
        columnL.addWidget(output_display)
        columnR.addWidget(plotting_area)

        main_row = QtGui.QHBoxLayout()
        main_row.addLayout(columnL)
        main_row.addLayout(columnR)

        self.setLayout(main_row)

        self.file_browser = file_browser
        self.fig_list = fig_list
        self.output_display = output_display
        self.plotting_area = plotting_area
        self.watcher = watcher


    def set_python_source_file(self, filename):
        for f in self.watcher.files():
            self.watcher.removePath(f)

        self.watcher.addPath(filename)
        self.current_python_source_file = filename
        self.load_python_source_file()


    def set_plot_function(self, item):
        self.current_plot_function = item.plot_function
        self.execute_plot_function()


    def load_python_source_file(self):

        current_item = self.fig_list.currentItem()
        current_item_name = current_item.text() if current_item else ""
        current_item_refreshed = None

        self.fig_list.currentItemChanged.disconnect()
        self.fig_list.clear()

        script_globals = dict()
        script_locals = dict()

        try:
            execfile(self.current_python_source_file, script_globals, script_locals)

            for thing in sorted(script_locals):
                if thing.startswith('fig_'):
                    item = QtGui.QListWidgetItem(thing)
                    item.plot_function = script_locals[thing]
                    self.fig_list.addItem(item)

                    if thing == current_item_name:
                        current_item_refreshed = item

            self.output_display.setPlainText('load succeeded')

        except Exception as e:
            self.output_display.setPlainText(str(e))

        self.fig_list.currentItemChanged.connect(self.set_plot_function)
        self.fig_list.setCurrentItem(current_item_refreshed)


    def execute_plot_function(self):
        fig = self.plotting_area.fig
        fig.clf()
        self.current_plot_function(fig)
        self.plotting_area.canvas.draw()



def run_main():
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    app.exec_()



if __name__ == "__main__":
    run_main()
