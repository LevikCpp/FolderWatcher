import pyads
import os
import math
import pathlib
import datetime

# def __init__(self, path: str):
#         try:
#             res: os.stat_result = os.stat(path)
#         except FileNotFoundError as e:
#             raise MetaDataError(f"Can't read stats for '{path}': {str(e)}")

#         self.name = pathlib.Path(path).name
#         self.created = res.st_birthtime
#         self.last_modified = res.st_mtime
#         self.last_accessed = res.st_atime
#         self.size = res.st_size
#         self.permissions = res.st_mode
#         self.owner = res.st_uid

#     def __str__(self):
#         return "%s[%s]" % (
#             type(self).__name__,
#             ", ".join("%s=%s" % item for item in vars(self).items()),

class filenode:
    def __init__(self, path):
        try:
            stats: os.stat_result = os.stat(path)
        except FileNotFoundError as err:
            raise OsStatError(f"Can't read stats for '{path}': {str(err)}")

        self.path = path
        self.name = pathlib.Path(path).name
        self.size = stats.st_size
        
        # Что-то делать
        ads = pyads.ADS(path)
        self.has_ads = False
        if ads.has_streams > 0:
            self.has_ads = True
            self.is_ads = False

        self.__stats = stats
    
    def get_size(self):
        if self.size == 0:
            return '0 B'
        
        size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
        i = int(math.floor(math.log(self.size, 1024)))
        p = math.pow(1024, i)
        size = round(self.size / p, 2)
        
        return f'{size} {size_name[i]}'

    def get_type(self):
        def is_shortcut(file_path):
            return file_path.endswith('.lnk')

        if os.path.is_file(self):
            return 'FILE'
        if os.path.is_dir(self):
            return 'DIR'
        if os.is_shortcut(self):
            return 'LNK'

    def get_date(self):
        def format_time(timestamp):
            now = datetime.now()
            time_check = datetime.fromtimestamp(timestamp)
            #time_str = time_check.strftime('%d-%m-%Y %H:%M:%S')

            if time_check.date() == now.date():
                return f'Today {time_check.strftime('%H:%M:%S')}'
            elif time_check.date() == (now - timedelta(days=1)).date():
                return f'Yesterday {time_check.strftime('%H:%M:%S')}'
            else:
                return time_check.strftime('%d-%m-%Y %H:%M:%S')

        # mtime - last modification, atime - last access, birthtime
        return format_time(self.__stats.st_mtime), format_time(self.__stats.st_atime), format_time(self.__stats.st_birthtime)
    
    # darshi: directory, archived, read-only, systemic, hiden, not indexed
    def get_attrib(self):
        attributes = ['-', '-', '-', '-', '-', '-']
        
        if self.type == 'DIR':
            attributes[0] = 'd'
        
        file_attrs = os.stat(self.path).st_file_attributes
        # Архивный файл
        if file_attrs & os.FILE_ATTRIBUTE_ARCHIVE:
            attributes[1] = 'a'
        # Файл только для чтения
        if file_attrs & os.FILE_ATTRIBUTE_READONLY:
            attributes[2] = 'r'
        # Системный файл
        if file_attrs & os.FILE_ATTRIBUTE_SYSTEM:
            attributes[3] = 's'
        # Скрытый файл
        if file_attrs & os.FILE_ATTRIBUTE_HIDDEN:
            attributes[4] = 'h'
        # Файл не индексируется для поиска
        if file_attrs & os.FILE_ATTRIBUTE_NOT_CONTENT_INDEXED:
            attributes[5] = 'i'

        return ''.join(attributes)
        