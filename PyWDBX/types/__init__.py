from PyWDBX.types.WDC3 import parse_wdc3, process_wdc3

def get_parser(sig):
    if sig == b"WDC3":
        return parse_wdc3, process_wdc3
    else:
        raise Exception("Unsupported WDBX file with format "+sig)