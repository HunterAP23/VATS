# Native Libraries
import logging as lg
import os
import sys

# Levels:
# 0 -> DEBUG
# 1 -> INFO
# 2 -> WARNING
# 3 -> ERROR
# 4 -> CRITICAL
# class EK_Logger(lg.Logger):
#     def __init__(self, debug=False, debugdev=False):
#         self.debug = debug
#         self.debugdev = debugdev
#
#         if self.debug or self.debugdev:
#             return super(EK_Logger, self).__init__(lg.DEBUG)
#         else:
#             return super(EK_Logger, self).__init__(lg.INFO)
#
#     def debug(self, message, *args, **kwargs):
#         msg = "{0} {1}: {2}".format(time.asctime(), "DEBUG", message)
#         return super(EK_Logger, self).debug(message, *args, **kwargs)
#
#     def info(self, message, *args, **kwargs):
#         msg = "{0} {1}: {2}".format(time.asctime(), "INFO", message)
#         return super(EK_Logger, self).info(message, *args, **kwargs)
#
#     def warning(self, message, *args, **kwargs):
#         msg = "{0} {1}: {2}".format(time.asctime(), "WARNING", message)
#         return super(EK_Logger, self).warning(message, *args, **kwargs)
#
#     def error(self, message, *args, **kwargs):
#         msg = "{0} {1}: {2}".format(time.asctime(), "ERROR", message)
#         return super(EK_Logger, self).error(message, *args, **kwargs)
#
#     def critical(self, message, *args, **kwargs):
#         msg = "{0} {1}: {2}".format(time.asctime(), "CRITCAL", message)
#         return super(EK_Logger, self).info(message, *args, **kwargs)


def write_log(level, message, the_log=None):
    if the_log is None:
        print(message)
    elif level == 0:
        the_log.debug(message)
    elif level == 1:
        the_log.info(message)
    elif level == 2:
        the_log.warning(message)
    elif level == 3:
        the_log.error(message)
    elif level == 4:
        the_log.critical(message)


def log_debug(message, the_log=None):
    write_log(0, message, the_log)


def log_info(message, the_log=None):
    write_log(1, message, the_log)


def log_warn(message, the_log=None):
    write_log(2, message, the_log)


def log_err(message, the_log=None):
    write_log(3, message, the_log)


def log_crit(message, the_log=None):
    write_log(4, message, the_log)


def create_log(debug=False, debugdev=False):
    log_name = r""
    tmp_path = "/".join(os.path.realpath(__file__).split("/")[:-1])
    if debug or debugdev:
        log_name = r"{0}/log.log".format(tmp_path)
    else:
        log_name = r"{0}/log.log".format(tmp_path)
    if os.path.exists(log_name):
        perms = int(oct(os.stat(log_name).st_mode)[-3:])
        if int(perms) != 777:
            print("The {0} item does not have octal 777 permissions.".format(log_name))
            print("Attempting to change permissions of {0} to 777.".format(log_name))
            try:
                os.chmod(log_name, 0o777)
                print("Gave {0} 777 permissions.".format(log_name))
            except Exception as e:
                print("Error occurred when changing permission of {0} to 777.".format(log_name))
                print("Exception({0}): {1}".format(e.errno, e.strerror))
    else:
        open(log_name, "a").close()

    # lg.setLoggerClass(EK_Logger)
    my_log = lg.getLogger()

    c_handler = lg.StreamHandler(sys.stdout)
    f_handler = lg.FileHandler(log_name)

    if debug or debugdev:
        c_handler.setLevel(lg.DEBUG)
        f_handler.setLevel(lg.DEBUG)
    else:
        c_handler.setLevel(lg.INFO)
        f_handler.setLevel(lg.INFO)

    c_format = lg.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    f_format = lg.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    my_log.addHandler(c_handler)
    my_log.addHandler(f_handler)

    my_log.setLevel(lg.NOTSET)

    return my_log
