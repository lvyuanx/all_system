import operator

class SafeEvaluator:
    """安全 JSONLogic 解释器"""
    OPS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "and": lambda *args: all(args),
        "or": lambda *args: any(args),
        "not": lambda x: not x,
        "in": lambda x, y: x in y,
        "contains": lambda x, y: y in x if hasattr(x, "__contains__") else False,
        "empty": lambda x: x in (None, "", [], {}, ()),
        "not_empty": lambda x: x not in (None, "", [], {}, ()),
        "startswith": lambda x, y: str(x).startswith(str(y)),
        "endswith": lambda x, y: str(x).endswith(str(y)),
    }

    def __init__(self, context: dict):
        self.context = context

    def _get_var(self, path: str):
        parts = path.split(".")
        value = self.context
        for p in parts:
            if isinstance(value, dict):
                value = value.get(p)
            else:
                value = getattr(value, p, None)
            if value is None:
                break
        return value

    def eval_expr(self, expr):
        if isinstance(expr, (bool, int, float, str)):
            return expr
        if isinstance(expr, dict):
            for op, vals in expr.items():
                if op == "var":
                    return self._get_var(vals)
                func = self.OPS.get(op)
                if not func:
                    raise ValueError(f"Unsupported operator: {op}")
                if not isinstance(vals, list):
                    vals = [vals]
                args = [self.eval_expr(v) for v in vals]
                return func(*args)
        raise ValueError(f"Invalid expression: {expr}")
