http_methods = (
    "ACL",
    "BASELINE-CONTROL",
    "BIND",
    "CHECKIN",
    "CHECKOUT",
    "CONNECT",
    "COPY",
    "DELETE",
    "GET",
    "HEAD",
    "LABEL",
    "LINK",
    "LOCK",
    "MERGE",
    "MKACTIVITY",
    "MKCALENDAR",
    "MKCOL",
    "MKREDIRECTREF",
    "MKWORKSPACE",
    "MOVE",
    "OPTIONS",
    "ORDERPATCH",
    "PATCH",
    "POST",
    "PRI",
    "PROPFIND",
    "PROPPATCH",
    "PUT",
    "REBIND",
    "REPORT",
    "SEARCH",
    "TRACE",
    "UNBIND",
    "UNCHECKOUT",
    "UNLINK",
    "UNLOCK",
    "UPDATE",
    "UPDATEREDIRECTREF",
    "VERSION-CONTROL",
)


def get_link(line: str) -> str:
    """
    Parse log line
    return url if it found
    return None - url format has been changed
    """
    start = line.find('"') + 1
    end = line.find('"', start)
    url = line[start:end]

    if not any(method in url for method in http_methods):
        return None

    try:
        url = url.split()[1]
    except IndexError:
        return None
    return url


def get_resp_time(line: str) -> float:
    """
    Parse log line
    return float time if it found
    return None - time format has been changed
    """
    time = line.split()[-1]
    time_ = time.replace(".", "")
    if not time_.isnumeric():
        return None
    ftime = float(time)

    return ftime
