from models import HTTPModel, UserModel
from flask_crud_api.orm import Orm

orm = Orm()


def hook_http_model_user(dic, exclude=None, key="uid"):
    stmt = orm.get_queryset(UserModel).where(UserModel.pk == dic[key])
    user = orm.execute_one_or_none(stmt)
    dic["user_data"] = {}
    if not user:
        return dic

    dic["user_data"] = user.to_dict(exclude)
    return dic


def hook_http_model_user_no_N_ADD_ONE(
    dic,
    exclude=None,
    key1=UserModel.__name__,
    key2=HTTPModel.__name__,
):
    if key1 not in dic or key2 not in dic:
        return dic

    result = dic[key2]
    result["user_data"] = dic[key1]
    return result
