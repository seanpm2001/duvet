"""A module containing a visual representation of the connection

This is the "View" of the MVC world.
"""
import os
import pickle
from Tkinter import *
from tkFont import *
from ttk import *
import tkMessageBox
import webbrowser

from coverage.parser import CodeParser

from duvet import VERSION, NUM_VERSION
from duvet.widgets import CodeView, FileView


def filename_normalizer(base_path):
    """Generate a fuction that will normalize a full path into a
    display name, by removing a common prefix.

    In most situations, this will be removing the current working
    directory.
    """
    def _normalizer(filename):
        if filename.startswith(base_path) and filename[len(base_path)] == os.sep:
            return filename[len(base_path)+1:]
        else:
            return filename
    return _normalizer


class MainWindow(object):
    def __init__(self, root, options):
        '''
        -----------------------------------------------------
        | main button toolbar                               |
        -----------------------------------------------------
        |       < ma | in content area >                    |
        |            |                                      |
        | File list  | File name                            |
        |            |                                      |
        -----------------------------------------------------
        |     status bar area                               |
        -----------------------------------------------------

        '''

        # Obtain and expand the current working directory.
        base_path = os.path.abspath(os.getcwd())
        self.base_path = os.path.normcase(base_path)

        # Create a filename normalizer based on the CWD.
        self.filename_normalizer = filename_normalizer(self.base_path)

        # Set up dummy coverage data
        self.coverage_data = {'lines': {}}

        # Root window
        self.root = root
        self.root.title('Duvet')
        self.root.geometry('1024x768')

        # Prevent the menus from having the empty tearoff entry
        self.root.option_add('*tearOff', FALSE)
        # Catch the close button
        self.root.protocol("WM_DELETE_WINDOW", self.cmd_quit)
        # Catch the "quit" event.
        self.root.createcommand('exit', self.cmd_quit)

        # Setup the menu
        self._setup_menubar()

        # Set up the main content for the window.
        self._setup_button_toolbar()
        self._setup_main_content()
        self._setup_status_bar()

        # Now configure the weights for the root frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

    ######################################################
    # Internal GUI layout methods.
    ######################################################

    def _setup_menubar(self):
        # Menubar
        self.menubar = Menu(self.root)

        # self.menu_Apple = Menu(self.menubar, name='Apple')
        # self.menubar.add_cascade(menu=self.menu_Apple)

        self.menu_file = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        self.menu_help = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_help, label='Help')

        # self.menu_Apple.add_command(label='Test', command=self.cmd_dummy)

        # self.menu_file.add_command(label='New', command=self.cmd_dummy, accelerator="Command-N")
        # self.menu_file.add_command(label='Close', command=self.cmd_dummy)

        self.menu_help.add_command(label='Open Documentation', command=self.cmd_duvet_docs)
        self.menu_help.add_command(label='Open Duvet project page', command=self.cmd_duvet_page)
        self.menu_help.add_command(label='Open Duvet on GitHub', command=self.cmd_duvet_github)
        self.menu_help.add_command(label='Open BeeWare project page', command=self.cmd_beeware_page)

        # last step - configure the menubar
        self.root['menu'] = self.menubar

    def _setup_button_toolbar(self):
        '''
        The button toolbar runs as a horizontal area at the top of the GUI.
        It is a persistent GUI component
        '''

        # Main toolbar
        self.toolbar = Frame(self.root)
        self.toolbar.grid(column=0, row=0, sticky=(W, E))

        # Buttons on the toolbar
        self.refresh_button = Button(self.toolbar, text='Refresh', command=self.cmd_refresh)
        self.refresh_button.grid(column=0, row=0)

        self.toolbar.columnconfigure(0, weight=0)
        self.toolbar.rowconfigure(0, weight=0)

    def _setup_main_content(self):
        '''
        Sets up the main content area. It is a persistent GUI component
        '''

        # Main content area
        self.content = PanedWindow(self.root, orient=HORIZONTAL)
        self.content.grid(column=0, row=1, sticky=(N, S, E, W))

        # Create subregions of the content
        self._setup_file_tree()
        self._setup_code_area()

        # Set up weights for the left frame's content
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.content.pane(0, weight=1)
        self.content.pane(1, weight=4)

    def _setup_file_tree(self):
        self.file_tree_frame = Frame(self.content)
        self.file_tree_frame.grid(column=0, row=0, sticky=(N, S, E, W))

        self.file_tree = FileView(self.file_tree_frame, normalizer=self.filename_normalizer, root=self.base_path)
        self.file_tree.grid(column=0, row=0, sticky=(N, S, E, W))

        # # The tree's vertical scrollbar
        self.file_tree_scrollbar = Scrollbar(self.file_tree_frame, orient=VERTICAL)
        self.file_tree_scrollbar.grid(column=1, row=0, sticky=(N, S))

        # # Tie the scrollbar to the text views, and the text views
        # # to each other.
        self.file_tree.config(yscrollcommand=self.file_tree_scrollbar.set)
        self.file_tree_scrollbar.config(command=self.file_tree.yview)

        # Setup weights for the "file_tree" tree
        self.file_tree_frame.columnconfigure(0, weight=1)
        self.file_tree_frame.columnconfigure(1, weight=0)
        self.file_tree_frame.rowconfigure(0, weight=1)

        # Handlers for GUI events
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_selected)

        self.content.add(self.file_tree_frame)

    def _setup_code_area(self):
        self.code_frame = Frame(self.content)
        self.code_frame.grid(column=1, row=0, sticky=(N, S, E, W))

        # Label for current file
        self.current_file = StringVar()
        self.current_file_label = Label(self.code_frame, textvariable=self.current_file)
        self.current_file_label.grid(column=0, row=0, sticky=(W, E))

        # Code display area
        self.code = CodeView(self.code_frame)
        self.code.grid(column=0, row=1, sticky=(N, S, E, W))

        # Set up weights for the code frame's content
        self.code_frame.columnconfigure(0, weight=1)
        self.code_frame.rowconfigure(0, weight=0)
        self.code_frame.rowconfigure(1, weight=1)

        self.content.add(self.code_frame)

    def _setup_status_bar(self):
        # Status bar
        self.statusbar = Frame(self.root)
        self.statusbar.grid(column=0, row=2, sticky=(W, E))

        # Coverage summary for currently selected file.
        self.coverage_summary = StringVar()
        self.coverage_summary_label = Label(self.statusbar, textvariable=self.coverage_summary)
        self.coverage_summary_label.grid(column=0, row=0, sticky=(W, E))
        self.coverage_summary.set('No file selected')

        # Main window resize handle
        self.grip = Sizegrip(self.statusbar)
        self.grip.grid(column=1, row=0, sticky=(S, E))

        # Set up weights for status bar frame
        self.statusbar.columnconfigure(0, weight=1)
        self.statusbar.columnconfigure(1, weight=0)
        self.statusbar.rowconfigure(0, weight=0)

    ######################################################
    # Utility methods for controlling content
    ######################################################

    def show_file(self, filename, line=None, breakpoints=None):
        """Show the content of the nominated file.

        If specified, line is the current line number to highlight. If the
        line isn't currently visible, the window will be scrolled until it is.

        breakpoints is a list of line numbers that have current breakpoints.

        If refresh is true, the file will be reloaded and redrawn.
        """
        # Set the filename label for the current file
        self.current_file.set(self.filename_normalizer(filename))

        # Update the code view; this means changing the displayed file
        # if necessary, and updating the current line.
        if filename != self.code.filename:
            self.code.filename = filename

            missing = self.coverage_data['missing'].get(filename, [])
            executed = self.coverage_data['lines'].get(filename, [])

            n_executed = len(executed)
            n_missing = len(missing)

            self.code.highlight_missing(missing)

            self.coverage_summary.set('%s/%s lines executed (%s missing)' % (n_executed, n_executed + n_missing, n_missing))

        self.code.line = line

    def load_coverage(self):
        "Load and display coverage data"
        # Store the old list of files that have coverage data.
        # We do this so we can identify stale data on the tree.
        old_files = set(self.coverage_data['lines'].keys())

        loaded = False
        retry = True
        while not loaded and retry:
            try:
                # Load the new coverage data
                with open('.coverage') as datafile:
                    self.coverage_data = pickle.load(datafile)
                    self.coverage_data['missing'] = {}

                    # Update the coverage display of every file mentioned in the file.
                    for filename, executed in self.coverage_data['lines'].items():
                        node = self.file_tree._nodify(filename)
                        if self.file_tree.exists(node):
                            # self.file_tree.set(node, 'branch_coverage', str(len(lines)))

                            # Compute the coverage percentage
                            parser = CodeParser(filename=filename)
                            statements, excluded = parser.parse_source()
                            exec1 = parser.first_lines(executed)
                            missing = sorted(set(statements) - set(exec1))
                            self.coverage_data['missing'][filename] = missing
                            n_executed = float(len(executed))
                            n_missing = float(len(missing))

                            # Update the column summary
                            coverage = round(n_executed / (n_executed + n_missing) * 100, 1)
                            self.file_tree.set(node, 'coverage', coverage)

                            # Set the color of the tree node based on coverage
                            if coverage < 70.0:
                                self.file_tree.item(node, tags=['file', 'code', 'bad'])
                            elif coverage < 80.0:
                                self.file_tree.item(node, tags=['file', 'code', 'poor'])
                            elif coverage < 90.0:
                                self.file_tree.item(node, tags=['file', 'code', 'ok'])
                            elif coverage < 99.9:
                                self.file_tree.item(node, tags=['file', 'code', 'good'])
                            else:
                                self.file_tree.item(node, tags=['file', 'code', 'perfect'])

                            # We've updated the file, so we know it isn't stale.
                            try:
                                old_files.remove(filename)
                            except KeyError:
                                # File wasn't loaded before; ignore this.
                                pass

                        # Clear out any stale coverage data
                        for filename in old_files:
                            node = self.file_tree._nodify(filename)
                            if self.file_tree.exists(node):
                                self.file_tree.set(node, 'coverage', '')
                                self.file_tree.item(node, tags=['file', 'code'])

                    loaded = True
            except IOError:
                retry = tkMessageBox.askretrycancel(
                    message="Couldn't find coverage data file. Have you generated coverage data? Is the .coverage in your current working directory",
                    title='No coverage data found'
                )
            except Exception, e:
                print type(e), e
                retry = tkMessageBox.askretrycancel(
                    message="Couldn't load coverage data -- data file may be corrupted",
                    title='Problem loading coverage data'
                )

        if not loaded and not retry:
            self.root.quit()

        return loaded

    ######################################################
    # TK Main loop
    ######################################################

    def mainloop(self):
        self.root.mainloop()

    ######################################################
    # TK Command handlers
    ######################################################

    def cmd_quit(self):
        "Quit the program"
        self.root.quit()

    def cmd_refresh(self, event=None):
        "Refresh the coverage data"
        self.load_coverage()

    def cmd_duvet_page(self):
        "Show the Duvet project page"
        webbrowser.open_new('http://pybee.org/duvet')

    def cmd_duvet_github(self):
        "Show the Duvet GitHub repo"
        webbrowser.open_new('http://github.com/pybee/duvet')

    def cmd_duvet_docs(self):
        "Show the Duvet documentation"
        # If this is a formal release, show the docs for that
        # version. otherwise, just show the head docs.
        if len(NUM_VERSION) == 3:
            webbrowser.open_new('http://duvet.readthedocs.org/en/v%s/' % VERSION)
        else:
            webbrowser.open_new('http://duvet.readthedocs.org/')

    def cmd_beeware_page(self):
        "Show the BeeWare project page"
        webbrowser.open_new('http://pybee.org/')

    ######################################################
    # Handlers for GUI actions
    ######################################################

    def on_file_selected(self, event):
        "When a file is selected, highlight the file and line"
        if event.widget.selection():
            filename = event.widget.selection()[0]

            # Display the file in the code view
            if os.path.isfile(filename):
                self.show_file(filename=filename)

