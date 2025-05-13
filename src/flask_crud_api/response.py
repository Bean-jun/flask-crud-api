def _response(data, msg, code):
    return {
        "data": data,
        "msg": msg,
        "code": code,
    }


def ok_response(data, msg="ok"):
    return _response(data, msg, 200)


def bad_response(data, msg="bad"):
    return _response(data, msg, 400)
