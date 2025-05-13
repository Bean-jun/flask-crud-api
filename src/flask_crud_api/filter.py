from flask import request
from sqlalchemy import Select
from flask_crud_api.orm import get_delete_key, get_valid_stmt
from flask_crud_api import utils


class BaseFilter:

    def query_filter(self, stmt: Select, view=None):
        return stmt


class PageFilter(BaseFilter):

    page = "__page"
    page_size = "__page_size"
    disable_page = "__page_disable"
    max_page = 30

    def _get_page_size(self):
        page = int(request.args.get(self.page) or 1)
        page_size = min(
            int(request.args.get(self.page_size) or self.max_page), self.max_page
        )
        return page, page_size

    def query_filter(self, stmt: Select, view=None):
        if self.disable_page in request.args:
            return stmt

        page, page_size = self._get_page_size()
        stmt = stmt.limit(page_size).offset((page - 1) * page_size)
        return stmt


class OrderFilter(BaseFilter):

    order_field_name = "view_order_fields"
    order_field_prefix = "__order_"
    order_model_name = "model"

    def get_default_model(self, view):
        if not hasattr(view, self.order_model_name):
            raise Exception(f"{self.order_model_name} is None")
        model = getattr(view, self.order_model_name)
        return model

    def get_default_order(self, view):
        if not hasattr(view, self.order_field_name):
            return None
        fields = getattr(view, self.order_field_name)
        return fields

    def make_order(self, model, order_fields):
        orders = {}

        for key in request.args.keys():
            if not key.startswith(self.order_field_prefix):
                continue

            for field, order in order_fields:
                if key != field:
                    continue
                request_args = request.args.getlist(field)
                for args in request_args:
                    if order != args:
                        continue

                    if not hasattr(model, field[len(self.order_field_prefix) :]):
                        continue

                    orders[field[len(self.order_field_prefix) :]] = order

        order_by = [getattr(getattr(model, order), orders[order])() for order in orders]
        return order_by

    def query_filter(self, stmt, view=None):
        if view is None:
            return stmt

        order_fields = self.get_default_order(view)
        if not order_fields:
            return stmt

        model = self.get_default_model(view)
        _order = self.make_order(model, order_fields)
        stmt = stmt.order_by(*_order)

        return stmt


class SearchFilter(BaseFilter):

    search_field_name = "view_filter_fields"
    search_model_name = "model"
    between_time_fields = {"create_time", "update_time", "entry_time"}

    def get_default_model(self, view):
        if not hasattr(view, self.search_model_name):
            raise Exception(f"{self.search_model_name} is None")
        model = getattr(view, self.search_model_name)
        return model

    def get_default_filter(self, view):
        if not hasattr(view, self.search_field_name):
            return None
        fields = getattr(view, self.search_field_name)
        return fields

    def make_conditions(self, filter_fields):
        conditions_args = {}
        conditions_ops = {}
        for field, op in filter_fields:
            if field not in request.args:
                continue
            conditions_ops[f"_op_{field}"] = op
            if op == "between":
                start, end = request.args[field].split(",")
                if field in self.between_time_fields:
                    conditions_args[field] = utils.str2datetime(
                        start
                    ), utils.str2datetime(end)
                else:
                    conditions_args[field] = start, end
            else:
                conditions_args[field] = request.args[field]
        return conditions_args, conditions_ops

    def make_filter(self, model, filter_fields, field_prefix=""):
        conditions_args, conditions_ops = self.make_conditions(filter_fields)

        conditions = []
        for field, value in conditions_args.items():
            real_field = field
            if field.startswith(field_prefix):
                real_field = field[len(field_prefix) :]

            if not hasattr(model, real_field):
                continue

            # TODO: 完善的过滤机制
            op = conditions_ops[f"_op_{field}"]
            ooo = getattr(model, real_field)
            if op == "between":
                conditions.append(ooo.between(*value))
            else:
                conditions.append(ooo.op(op)(value))
        return conditions

    def query_filter(self, stmt: Select, view=None):
        if view is None:
            return stmt

        filter_fields = self.get_default_filter(view)
        if not filter_fields:
            return stmt

        model = self.get_default_model(view)
        _filter = self.make_filter(model, filter_fields)
        stmt = stmt.where(*_filter)

        return stmt


class SearchJoinFilter(SearchFilter):

    join_model_field_name = "view_join_model_key"
    search_join_field_name = "view_join_filter_fields"
    search_join_field_prefix = "__join_"
    search_join_model_name = "view_join_model"

    def get_default_join_models(self, view):
        if not hasattr(view, self.search_join_model_name):
            return None
        models = getattr(view, self.search_join_model_name)
        return models

    def get_default_join_keys(self, view):
        if not hasattr(view, self.join_model_field_name):
            return None
        join_keys = getattr(view, self.join_model_field_name)
        return join_keys

    def make_join(self, stmt: Select, model, join_models, join_keys):
        if not all([join_models, join_keys]):
            return stmt

        if len(join_models) != len(join_keys):
            raise Exception("关联条件错误")

        for j_model, j_key in zip(join_models, join_keys):
            left, right = j_key
            stmt = stmt.outerjoin(
                j_model, getattr(j_model, left) == getattr(model, right)
            )
            delete_key = get_delete_key(j_model)
            stmt = get_valid_stmt(delete_key, stmt)
        return stmt

    def get_default_join_filter(self, view):
        if not hasattr(view, self.search_join_field_name):
            return None
        fields = getattr(view, self.search_join_field_name)
        return fields

    def make_join_filter(self, join_models, join_filter_fields):
        conditions = []
        if not all([join_models, join_filter_fields]):
            return conditions

        for j_model, join_filter in zip(join_models, join_filter_fields):
            conditions.extend(
                self.make_filter(j_model, join_filter, self.search_join_field_prefix)
            )

        return conditions

    def query_filter(self, stmt, view=None):
        stmt = super().query_filter(stmt, view)

        join_models = self.get_default_join_models(view)
        if not join_models:
            return stmt

        join_keys = self.get_default_join_keys(view)
        if not join_keys:
            return stmt

        model = self.get_default_model(view)
        # TODO: 按需进行join
        stmt = self.make_join(stmt, model, join_models, join_keys)

        join_filter_fields = self.get_default_join_filter(view)
        if not join_filter_fields:
            return stmt

        _filter = self.make_join_filter(join_models, join_filter_fields)
        stmt = stmt.where(*_filter)

        return stmt
