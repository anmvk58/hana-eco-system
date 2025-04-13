import uuid

def get_org_bill_code(bill_code):
    return bill_code[:8]


def gen_group_bill_code():
    return str(uuid.uuid4())[:6].upper()

if __name__ == '__main__':
    print(gen_group_bill_code())
    print(get_org_bill_code('HD026075.01'))
    print(get_org_bill_code('HD026075'))
