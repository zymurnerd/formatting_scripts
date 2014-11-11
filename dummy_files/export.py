class Export(object):
    def __init__(self, parent, path, export_item, export_info = None, export_stream = None):
        self.path = path
        self.export_item = export_item
        self.export_info = export_info
        self.export_stream = export_stream
        self.parent = parent

    def open_path(self):
        raise NotImplementedError

    def close_path(self):
        raise NotImplementedError

    def export(self):
        raise NotImplementedError

    def _create_progress_dialog(self):
        raise NotImplementedError