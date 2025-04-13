from datetime import datetime

def get_current_date():
    return int(datetime.now().strftime("%Y%m%d"))