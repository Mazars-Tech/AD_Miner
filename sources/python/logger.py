class bcolors:

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_debug(info):
    print("%s[+]%s%s" % (bcolors.OKBLUE, info, bcolors.ENDC))


def print_error(info):
    print("%s[!]%s%s" % (bcolors.FAIL, info, bcolors.ENDC))


def print_time(info):
    print("%s[-]%s%s" % (bcolors.WARNING, info, bcolors.ENDC))


def print_success(info):
    print("%s[+]%s%s" % (bcolors.OKGREEN, info, bcolors.ENDC))
