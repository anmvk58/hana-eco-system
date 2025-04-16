import uuid
import re

def get_org_bill_code(bill_code):
    return bill_code[:8]


def gen_group_bill_code():
    return str(uuid.uuid4())[:6].upper()


def extract_duplicate_bill(keyword, message):
    keyword = "Duplicate entry '"
    start_index = message.find(keyword)

    if start_index == -1:
        return None

    start_index += len(keyword)
    return message[start_index:start_index+8]

if __name__ == '__main__':
    print(gen_group_bill_code())
    print(get_org_bill_code('HD026075.01'))
    print(get_org_bill_code('HD026075'))
