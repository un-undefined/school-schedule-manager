info = {
    "year": 2026,
    "school_bounds": [
        "8,25",
        "6,11"
    ],
    "no_school": [
        "9,7",
        "9,21",
        "10,12",
        "10,13",
        "10,21",
        "11,3",
        "11,25",
        "11,26",
        "11,27",
        "12,24",
        "12,25",
        "12,28",
        "12,29",
        "12,30",
        "12,31",
        "1,1",
        "1,18",
        "2,15",
        "2,16",
        "2,17",
        "2,18",
        "2,19",
        "3,26",
        "4,12",
        "4,13",
        "4,14",
        "4,15",
        "4,16",
        "5,31"
    ],
    "short_days": [
        "9,9",
        "11,2",
        "11,19",
        "11,20",
        "11,23",
        "11,24",
        "12,9",
        "12,23",
        "1,13",
        "1,19",
        "1,20",
        "3,10",
        "4,7",
        "6,9",
        "6,10",
        "6,11"
    ]
}

encoding = "0123456789ABCDEFGHIJ"

def encode_dates(d_list):
    total = ""
    for date in d_list:
        d = 31 * int(date.split(",")[0]) + int(date.split(",")[1]) - 31
        total += str(encoding[d // 20] + encoding[d % 20])
    return total

def decode_dates(d_str):
    dates = []
    for i in range(0, len(d_str) // 2):
        base_int = encoding.index(d_str[2 * i]) * 20 + encoding.index(d_str[2 * i + 1]) + 30
        dates.append(str(base_int // 31) + "," + str(base_int % 31 + 1))
    return dates

def encode(d):
    result = ""
    result += "Year:" + str(d["year"]) + ";"
    result += "Limit:" + encode_dates(d["school_bounds"]) + ";"
    result += "NoS:" + encode_dates(d["no_school"]) + ";"
    result += "Short:" + encode_dates(d["short_days"])
    return result

def decode(d_str):
    rawdata = d_str.split(";")
    data = {}
    for item in rawdata:
        s = item.split(":")
        if s[0] == "Year":
            data["year"] = int(s[1])
        elif s[0] == "Limit":
            data["school_bounds"] = decode_dates(s[1])
        elif s[0] == "NoS":
            data["no_school"] = decode_dates(s[1])
        elif s[0] == "Short":
            data["short_days"] = decode_dates(s[1])
    return data

v = encode(info)
print(v)
print(decode(v))
print(info)
print(decode(v) == info)
