import os

from watchdog.events import PatternMatchingEventHandler as Handler


class TempPakFileHandler(Handler):
    """A Watchdog handler that maintains a list of files to be written out to
    the target pak file.
    """

    def __init__(self, context, working_directory, files, verbose=False, **kwargs):
        super().__init__(**kwargs)
        self.context = context
        self.working_directory = working_directory
        self.files = files
        self.verbose = verbose

    def on_modified(self, event):
        self.context["dirty"] = True

        if self.verbose:
            print(
                "{0} modified".format(
                    os.path.relpath(event.src_path, self.working_directory)
                )
            )

        rel_path = os.path.relpath(event.src_path, self.working_directory)
        with open(event.src_path, "rb") as file:
            self.files[rel_path] = file.read()

    def on_created(self, event):
        self.context["dirty"] = True

        if self.verbose:
            print(
                "{0} created".format(
                    os.path.relpath(event.src_path, self.working_directory)
                )
            )

        rel_path = os.path.relpath(event.src_path, self.working_directory)

        with open(event.src_path, "rb") as file:
            self.files[rel_path] = file.read()

    def on_deleted(self, event):
        self.context["dirty"] = True

        if self.verbose:
            print(
                "{0} deleted".format(
                    os.path.relpath(event.src_path, self.working_directory)
                )
            )

        rel_path = os.path.relpath(event.src_path, self.working_directory)
        self.files.pop(rel_path, None)

    def on_moved(self, event):
        self.context["dirty"] = True

        if self.verbose:
            print(
                "{0} moved".format(
                    os.path.relpath(event.src_path, self.working_directory)
                )
            )

        rel_src_path = os.path.relpath(event.src_path, self.working_directory)
        rel_dest_path = os.path.relpath(event.dest_path, self.working_directory)

        self.files[rel_dest_path] = self.files.pop(rel_src_path, None)
