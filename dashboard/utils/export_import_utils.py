# -*- coding: utf-8 -*-
"""
数据导入导出工具模块，提供Excel和CSV文件的导入导出功能
"""
import io
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import pandas as pd
from django.db import models
from django.db.models import QuerySet
from django.http import HttpResponse
from rest_framework import serializers

logger = logging.getLogger(__name__)


class ExportImportUtils:
    """数据导入导出工具类"""

    @staticmethod
    def export_to_excel(
        queryset: QuerySet,
        serializer_class: Type[serializers.ModelSerializer],
        filename: str = "export_data.xlsx",
        fields: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        sheet_name: str = "Sheet1"
    ) -> HttpResponse:
        """
        将数据导出为Excel文件
        
        Args:
            queryset: 要导出的数据集
            serializer_class: 序列化器类
            filename: 导出的文件名
            fields: 要导出的字段列表，None表示使用序列化器的所有字段
            headers: 自定义表头映射，格式为{"字段名": "显示名称"}
            sheet_name: Excel工作表名称
        
        Returns:
            HttpResponse: 包含Excel文件的HTTP响应
        """
        try:
            # 获取序列化器的字段列表
            serializer_instance = serializer_class()
            serializer_fields = list(serializer_instance.fields.keys())
            
            # 序列化数据
            serializer = serializer_class(queryset, many=True)
            data = serializer.data
            
            # 确定要导出的字段
            if fields:
                # 使用提供的字段列表
                export_fields = [field for field in fields if field in serializer_fields]
            else:
                # 使用序列化器的所有字段
                export_fields = serializer_fields
            
            # 如果没有数据，创建包含表头的空DataFrame
            if not data:
                # 创建只包含表头的空DataFrame
                df = pd.DataFrame(columns=export_fields)
            else:
                # 创建DataFrame
                df = pd.DataFrame(data)
                # 按字段筛选
                df = df[export_fields]
            
            # 重命名表头
            if headers:
                df = df.rename(columns=headers)
            
            # 创建内存中的Excel文件
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            
            # 设置响应
            buffer.seek(0)
            response = HttpResponse(
                buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f"attachment; filename={filename}"
            
            logger.info(f"成功导出Excel文件: {filename}")
            return response
            
        except Exception as e:
            logger.error(f"导出Excel文件失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
    
    @staticmethod
    def export_to_csv(
        queryset: QuerySet,
        serializer_class: Type[serializers.ModelSerializer],
        filename: str = "export_data.csv",
        fields: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        encoding: str = "utf-8-sig",
        delimiter: str = ","
    ) -> HttpResponse:
        """
        将数据导出为CSV文件
        
        Args:
            queryset: 要导出的数据集
            serializer_class: 序列化器类
            filename: 导出的文件名
            fields: 要导出的字段列表，None表示使用序列化器的所有字段
            headers: 自定义表头映射，格式为{"字段名": "显示名称"}
            encoding: 文件编码
            delimiter: 分隔符
        
        Returns:
            HttpResponse: 包含CSV文件的HTTP响应
        """
        try:
            # 序列化数据
            serializer = serializer_class(queryset, many=True)
            data = serializer.data
            
            # 如果没有数据，返回空文件
            if not data:
                df = pd.DataFrame()
            else:
                # 创建DataFrame
                df = pd.DataFrame(data)
                
                # 按字段筛选
                if fields:
                    valid_fields = [field for field in fields if field in df.columns]
                    df = df[valid_fields]
                
                # 重命名表头
                if headers:
                    df = df.rename(columns=headers)
            
            # 创建CSV响应
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f"attachment; filename={filename}"
            
            df.to_csv(
                path_or_buf=response,
                index=False,
                encoding=encoding,
                sep=delimiter
            )
            
            logger.info(f"成功导出CSV文件: {filename}")
            return response
            
        except Exception as e:
            logger.error(f"导出CSV文件失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
    
    @staticmethod
    def import_from_excel(
        file: io.BytesIO,
        model_class: Type[models.Model],
        serializer_class: Type[serializers.ModelSerializer],
        sheet_name: str = "Sheet1",
        fields_mapping: Optional[Dict[str, str]] = None,
        unique_fields: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        从Excel文件导入数据
        
        Args:
            file: Excel文件对象
            model_class: 数据模型类
            serializer_class: 序列化器类
            sheet_name: Excel工作表名称
            fields_mapping: 字段映射，格式为{"Excel列名": "模型字段名"}
            unique_fields: 唯一标识字段，用于更新现有数据
            batch_size: 批量导入的大小
        
        Returns:
            Tuple[int, List[Dict]]: (成功导入的记录数, 错误信息列表)
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file, sheet_name=sheet_name)
            
            # 应用字段映射
            if fields_mapping:
                df = df.rename(columns={v: k for k, v in fields_mapping.items()})
            
            # 转换为字典列表
            data_list = df.to_dict(orient="records")
            
            # 导入数据
            return ExportImportUtils._import_data(
                data_list,
                model_class,
                serializer_class,
                unique_fields,
                batch_size
            )
            
        except Exception as e:
            logger.error(f"从Excel文件导入数据失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return 0, [{"error": str(e)}]
    
    @staticmethod
    def import_from_csv(
        file: io.TextIOWrapper,
        model_class: Type[models.Model],
        serializer_class: Type[serializers.ModelSerializer],
        fields_mapping: Optional[Dict[str, str]] = None,
        unique_fields: Optional[List[str]] = None,
        batch_size: int = 100,
        encoding: str = "utf-8-sig",
        delimiter: str = ","
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        从CSV文件导入数据
        
        Args:
            file: CSV文件对象
            model_class: 数据模型类
            serializer_class: 序列化器类
            fields_mapping: 字段映射，格式为{"CSV列名": "模型字段名"}
            unique_fields: 唯一标识字段，用于更新现有数据
            batch_size: 批量导入的大小
            encoding: 文件编码
            delimiter: 分隔符
        
        Returns:
            Tuple[int, List[Dict]]: (成功导入的记录数, 错误信息列表)
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(file, encoding=encoding, sep=delimiter)
            
            # 应用字段映射
            if fields_mapping:
                df = df.rename(columns={v: k for k, v in fields_mapping.items()})
            
            # 转换为字典列表
            data_list = df.to_dict(orient="records")
            
            # 导入数据
            return ExportImportUtils._import_data(
                data_list,
                model_class,
                serializer_class,
                unique_fields,
                batch_size
            )
            
        except Exception as e:
            logger.error(f"从CSV文件导入数据失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return 0, [{"error": str(e)}]
    
    @staticmethod
    def _import_data(
        data_list: List[Dict[str, Any]],
        model_class: Type[models.Model],
        serializer_class: Type[serializers.ModelSerializer],
        unique_fields: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        导入数据的核心方法
        
        Args:
            data_list: 数据列表
            model_class: 数据模型类
            serializer_class: 序列化器类
            unique_fields: 唯一标识字段，用于更新现有数据
            batch_size: 批量导入的大小
        
        Returns:
            Tuple[int, List[Dict]]: (成功导入的记录数, 错误信息列表)
        """
        success_count = 0
        errors = []
        
        # 处理每一批数据
        for i in range(0, len(data_list), batch_size):
            batch_data = data_list[i:i + batch_size]
            
            for index, data in enumerate(batch_data):
                try:
                    # 去除空值
                    cleaned_data = {k: v for k, v in data.items() if pd.notna(v)}
                    
                    # 如果提供了唯一字段，尝试更新现有记录
                    instance = None
                    if unique_fields:
                        filter_kwargs = {}
                        for field in unique_fields:
                            if field in cleaned_data:
                                filter_kwargs[field] = cleaned_data[field]
                        
                        if filter_kwargs:
                            try:
                                instance = model_class.objects.get(**filter_kwargs)
                            except model_class.DoesNotExist:
                                pass
                    
                    # 使用序列化器验证和保存数据
                    serializer = serializer_class(instance=instance, data=cleaned_data)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        success_count += 1
                except Exception as e:
                    row_num = i + index + 2  # +2 因为Excel行号从1开始，且第一行是表头
                    error_msg = f"第{row_num}行: {str(e)}"
                    errors.append({"row": row_num, "error": error_msg})
                    logger.error(error_msg)
                    logger.debug(traceback.format_exc())
        
        logger.info(f"数据导入完成: 成功{success_count}条，失败{len(errors)}条")
        return success_count, errors


# 创建导出导入工具的单例实例
export_import_utils = ExportImportUtils()