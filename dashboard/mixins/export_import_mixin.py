# -*- coding: utf-8 -*-
"""
导出导入功能混入类，提供Excel和CSV格式的数据导入导出功能
"""
import logging
import traceback
from typing import Any, Dict, List, Optional, Type, Union

from django.db.models import Model, QuerySet
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from dashboard.utils.export_import_utils import export_import_utils

logger = logging.getLogger(__name__)


class ExportImportMixin:
    """导出导入功能混入类"""

    @action(detail=False, methods=['get'], url_path='export-excel')
    def export_excel(self, request):
        """
        导出数据为Excel格式
        
        URL参数:
            fields: 要导出的字段列表，用逗号分隔
            filename: 导出的文件名
            sheet_name: Excel工作表名称
        
        Returns:
            HttpResponse: 包含Excel文件的响应
        """
        try:
            # 获取查询参数
            fields_str = request.query_params.get('fields', None)
            filename = request.query_params.get('filename', f'{self.operation_module}_export.xlsx')
            sheet_name = request.query_params.get('sheet_name', 'Sheet1')
            
            # 解析字段列表
            fields = fields_str.split(',') if fields_str else None
            
            # 获取过滤后的查询集
            queryset = self.filter_queryset(self.get_queryset())
            
            # 获取表头映射
            headers = self.get_export_headers()
            
            # 调用导出工具
            return export_import_utils.export_to_excel(
                queryset=queryset,
                serializer_class=self.get_serializer_class(),
                filename=filename,
                fields=fields,
                headers=headers,
                sheet_name=sheet_name
            )
            
        except Exception as e:
            logger.error(f"Excel导出失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return Response(
                {'error': f'Excel导出失败: {str(e)}'},
                status=500
            )
    
    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        """
        导出数据为CSV格式
        
        URL参数:
            fields: 要导出的字段列表，用逗号分隔
            filename: 导出的文件名
            encoding: 文件编码
            delimiter: 分隔符
        
        Returns:
            HttpResponse: 包含CSV文件的响应
        """
        try:
            # 获取查询参数
            fields_str = request.query_params.get('fields', None)
            filename = request.query_params.get('filename', f'{self.operation_module}_export.csv')
            encoding = request.query_params.get('encoding', 'utf-8-sig')
            delimiter = request.query_params.get('delimiter', ',')
            
            # 解析字段列表
            fields = fields_str.split(',') if fields_str else None
            
            # 获取过滤后的查询集
            queryset = self.filter_queryset(self.get_queryset())
            
            # 获取表头映射
            headers = self.get_export_headers()
            
            # 调用导出工具
            return export_import_utils.export_to_csv(
                queryset=queryset,
                serializer_class=self.get_serializer_class(),
                filename=filename,
                fields=fields,
                headers=headers,
                encoding=encoding,
                delimiter=delimiter
            )
            
        except Exception as e:
            logger.error(f"CSV导出失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return Response(
                {'error': f'CSV导出失败: {str(e)}'},
                status=500
            )
    
    @action(detail=False, methods=['post'], url_path='import-excel')
    def import_excel(self, request):
        """
        从Excel文件导入数据
        
        Form Data:
            file: Excel文件
            sheet_name: Excel工作表名称
            batch_size: 批量导入的大小
        
        Returns:
            Response: 导入结果
        """
        try:
            # 检查文件是否存在
            if 'file' not in request.FILES:
                return Response(
                    {'error': '请上传Excel文件'},
                    status=400
                )
            
            # 获取文件和参数
            file = request.FILES['file']
            sheet_name = request.data.get('sheet_name', 'Sheet1')
            batch_size = int(request.data.get('batch_size', 100))
            
            # 获取字段映射和唯一字段
            fields_mapping = self.get_import_fields_mapping()
            unique_fields = self.get_unique_import_fields()
            
            # 调用导入工具
            success_count, errors = export_import_utils.import_from_excel(
                file=file,
                model_class=self.queryset.model,
                serializer_class=self.get_serializer_class(),
                sheet_name=sheet_name,
                fields_mapping=fields_mapping,
                unique_fields=unique_fields,
                batch_size=batch_size
            )
            
            # 返回结果
            return self.success_response({
                'success_count': success_count,
                'error_count': len(errors),
                'errors': errors
            }, message="Excel数据导入完成")
            
        except Exception as e:
            logger.error(f"Excel导入失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return self.error_response(
                message=f'Excel导入失败: {str(e)}',
                code=500
            )
    
    @action(detail=False, methods=['post'], url_path='import-csv')
    def import_csv(self, request):
        """
        从CSV文件导入数据
        
        Form Data:
            file: CSV文件
            encoding: 文件编码
            delimiter: 分隔符
            batch_size: 批量导入的大小
        
        Returns:
            Response: 导入结果
        """
        try:
            # 检查文件是否存在
            if 'file' not in request.FILES:
                return Response(
                    {'error': '请上传CSV文件'},
                    status=400
                )
            
            # 获取文件和参数
            file = request.FILES['file']
            encoding = request.data.get('encoding', 'utf-8-sig')
            delimiter = request.data.get('delimiter', ',')
            batch_size = int(request.data.get('batch_size', 100))
            
            # 获取字段映射和唯一字段
            fields_mapping = self.get_import_fields_mapping()
            unique_fields = self.get_unique_import_fields()
            
            # 调用导入工具
            success_count, errors = export_import_utils.import_from_csv(
                file=file,
                model_class=self.queryset.model,
                serializer_class=self.get_serializer_class(),
                fields_mapping=fields_mapping,
                unique_fields=unique_fields,
                batch_size=batch_size,
                encoding=encoding,
                delimiter=delimiter
            )
            
            # 返回结果
            return Response({
                'success_count': success_count,
                'error_count': len(errors),
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"CSV导入失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return Response(
                {'error': f'CSV导入失败: {str(e)}'},
                status=500
            )
    
    def get_export_headers(self) -> Optional[Dict[str, str]]:
        """
        获取导出时使用的表头映射
        子类可以重写此方法来自定义表头
        
        Returns:
            Dict[str, str]: 字段名到显示名称的映射
        """
        # 默认返回None，使用字段名作为表头
        return None
    
    def get_import_fields_mapping(self) -> Optional[Dict[str, str]]:
        """
        获取导入时使用的字段映射
        子类可以重写此方法来自定义字段映射
        
        Returns:
            Dict[str, str]: 文件列名到模型字段名的映射
        """
        # 默认返回None，使用相同的字段名
        return None
    
    def get_unique_import_fields(self) -> Optional[List[str]]:
        """
        获取用于判断唯一性的字段列表
        子类可以重写此方法来定义哪些字段用于判断记录的唯一性
        
        Returns:
            List[str]: 唯一标识字段列表
        """
        # 默认返回None，不进行更新操作
        return None
    
    @action(detail=False, methods=['get'], url_path='template-download')
    def template_download(self, request):
        """
        下载导入模板
        
        URL参数:
            filename: 模板文件名
            sheet_name: Excel工作表名称
        
        Returns:
            HttpResponse: 包含Excel模板文件的响应
        """
        try:
            # 获取查询参数，完全使用前端传入的文件名，仅保留简单默认值
            filename = request.query_params.get('filename', '模板.xlsx')
            sheet_name = request.query_params.get('sheet_name', 'Sheet1')
            
            # 获取表头映射
            headers = self.get_export_headers()
            
            # 调用导出工具，使用空查询集生成模板
            return export_import_utils.export_to_excel(
                queryset=self.get_queryset().none(),  # 空查询集，只生成表头
                serializer_class=self.get_serializer_class(),
                filename=filename,
                headers=headers,
                sheet_name=sheet_name
            )
            
        except Exception as e:
            logger.error(f"模板下载失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return Response(
                {'error': f'模板下载失败: {str(e)}'},
                status=500
            )