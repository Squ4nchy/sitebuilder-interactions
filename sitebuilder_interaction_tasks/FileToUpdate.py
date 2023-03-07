from os.path import abspath, join

class FileToUpdate:
    
    '''
    Class to define different files depending on the selected task.
    '''
    files_dict = {}
    current_dir = abspath("")
    
    def __init__(self, journal_shortcode, file_extension):
        self.journal_shortcode = journal_shortcode
        self.file_extension = file_extension
        
        self.original_file_path = join(self.current_dir, "original", f"{self.journal_shortcode}_{self.file_extension}")
        self.new_file_path = join(self.current_dir, "new", f"{self.journal_shortcode}_{self.file_extension}")
        
        self.files_dict[self.journal_shortcode] = self