import importlib

def import_from_path(path: str):
    """
    根据路径字符串导入对象或模块
    格式:
      - module.submodule           -> 返回模块
      - module.submodule:object    -> 返回模块里的对象（类/函数/变量）
    """
    if ":" in path:
        module_path, attr_name = path.split(":", 1)
        module = importlib.import_module(module_path)
        return getattr(module, attr_name, None)
    else:
        return importlib.import_module(path)