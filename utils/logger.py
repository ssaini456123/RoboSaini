from datetime import datetime

color_cyan = "\033[96m"
color_yellow = "\033[93m"
color_red = "\u001b[31m"
color_reset = "\033[0m"
color_purple = "\033[0;35m"
color_green = "\033[0;32m"
color_pink = "\033[38;5;206m"

text_type_bold = "\033[1m"


def timeNow():
    currentTime = datetime.now()
    timeFmt = "{}:{}:{}".format(
        currentTime.hour, currentTime.minute, currentTime.second
    )
    return timeFmt


def logF(msg):
    now = timeNow()
    print(
        "{}[{}] {}-- {}LOG:{} {}".format(
            color_cyan, now, color_reset, color_green, color_reset, msg, color_reset
        )
    )


def logErr(msg):
    now = timeNow()
    print(
        "{}{}[{}] -- ERROR:{}{} {}".format(
            text_type_bold, color_red, now, color_reset, color_pink, msg, color_reset
        )
    )
