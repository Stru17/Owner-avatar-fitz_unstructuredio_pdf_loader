# coding=utf-8
# Copyright 2018-2023 EvaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from ast import literal_eval
from typing import Tuple

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from evadb.catalog.models.association_models import (
    depend_column_and_function_cache,
    depend_function_and_function_cache,
)
from evadb.catalog.models.base_model import BaseModel
from evadb.catalog.models.utils import FunctionCacheCatalogEntry


class FunctionCacheCatalog(BaseModel):
    """The `FunctionCacheCatalog` catalog stores information about the function cache.

    It maintains the following information for each cache entry:
    `_row_id:` An autogenerated identifier for the cache entry.
    `_name:` The name of the cache, also referred to as the unique function signature.
    `_function_id:` `_row_id` of the function in the `FunctionCatalog` for which the cache is built.
    `_args:` A serialized list of `ColumnCatalog` `_row_id`s for each argument of the
    Function. If the argument is a function expression, it stores the string representation
    of the expression tree.
    """

    __tablename__ = "function_cache"

    _name = Column("name", String(128))
    _function_id = Column(
        "function_id",
        Integer,
        ForeignKey("function_catalog._row_id", ondelete="CASCADE"),
    )
    _cache_path = Column("cache_path", String(256))
    _args = Column("args", String(1024))

    __table_args__ = (UniqueConstraint("name", "function_id"), {})

    _col_depends = relationship(
        "ColumnCatalog",
        secondary=depend_column_and_function_cache,
        back_populates="_dep_caches",
        # cascade="all, delete-orphan",
    )

    _function_depends = relationship(
        "FunctionCatalog",
        secondary=depend_function_and_function_cache,
        back_populates="_dep_caches",
        # cascade="all, delete-orphan",
    )

    def __init__(self, name: str, function_id: int, cache_path: str, args: Tuple[str]):
        self._name = name
        self._function_id = function_id
        self._cache_path = cache_path
        self._args = str(args)

    def as_dataclass(self) -> "FunctionCacheCatalogEntry":
        function_depends = [obj._row_id for obj in self._function_depends]
        col_depends = [obj._row_id for obj in self._col_depends]
        return FunctionCacheCatalogEntry(
            row_id=self._row_id,
            name=self._name,
            function_id=self._function_id,
            cache_path=self._cache_path,
            args=literal_eval(self._args),
            function_depends=function_depends,
            col_depends=col_depends,
        )