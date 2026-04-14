# -*-coding:utf-8 -*-

"""
# Description: field data source metadata for form designer
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from flow_engine.utils.form_runtime_util import build_field_data_source_metadata_payload

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询字段数据源元数据失败"
    response_schema = schemas.FieldDataSourceMetadataRespSchema
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return schemas.FieldDataSourceMetadataRespSchema(
            **build_field_data_source_metadata_payload(),
        )
