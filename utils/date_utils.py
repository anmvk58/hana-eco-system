from datetime import datetime

def get_current_date():
    return int(datetime.now().strftime("%Y%m%d"))

# 01/01/2018 - 01/15/2018
# m%/%d/%Y - m%/%d/%Y
def get_current_date_for_datepicker():
    return datetime.now().strftime("%m/%d/%Y - %m/%d/%Y")

if __name__ == '__main__':
    print(get_current_date_for_datepicker())