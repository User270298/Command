from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.http import FileResponse, JsonResponse
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from rest_framework.exceptions import ValidationError
from .models import EquipmentRecord

from .models import MeasurementType, EquipmentRecord
from .serializers import (
    MeasurementTypeSerializer, EquipmentRecordSerializer, EquipmentRecordDetailSerializer
)
from trips.models import Organization, BusinessTrip

class IsSeniorForReportsPermission(permissions.BasePermission):
    """Permission to only allow seniors to access reports"""
    def has_permission(self, request, view):
        if view.action in ['generate_user_report', 'generate_organization_report', 'export_excel']:
            return request.user.is_senior
        return True

class MeasurementTypeViewSet(viewsets.ModelViewSet):
    queryset = MeasurementType.objects.all()
    serializer_class = MeasurementTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class EquipmentRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeniorForReportsPermission]
    
    def get_queryset(self):
        user = self.request.user
        organization_id = self.request.query_params.get('organization', None)
        
        # Base queryset
        queryset = EquipmentRecord.objects.select_related(
            'organization', 'measurement_type', 'user'
        )
        
        # Filter by organization if specified
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
            
        # If user is not a senior, only show their records
        if not user.is_senior:
            queryset = queryset.filter(user=user)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EquipmentRecordDetailSerializer
        return EquipmentRecordSerializer
    
    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            raise ValidationError(str(e))
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            raise ValidationError(str(e))
    
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception as e:
            raise ValidationError(str(e))
    
    @action(detail=False, methods=['GET'])
    def by_organization(self, request):
        """Get equipment records for a specific organization"""
        organization_id = request.query_params.get('organization', None)
        if not organization_id:
            return Response(
                {'detail': 'Organization ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            queryset = self.get_queryset().filter(organization_id=organization_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['GET'])
    def by_user(self, request):
        """Get equipment records for a specific user"""
        user_id = request.query_params.get('user', None)
        if not user_id:
            user_id = request.user.id
        
        try:
            queryset = self.get_queryset().filter(user_id=user_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['POST'])
    def generate_user_report(self, request):
        """Generate PDF report for a user's equipment records"""
        user_id = request.data.get('user_id')
        organization_id = request.data.get('organization_id')
        
        if not user_id or not organization_id:
            return Response({'detail': 'User ID and Organization ID are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's equipment records for this organization
        records = EquipmentRecord.objects.filter(
            user_id=user_id,
            organization_id=organization_id
        )
        
        if not records:
            return Response({'detail': 'No records found for this user in this organization'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Create a PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Get user info and organization info
        user = records.first().user
        organization = records.first().organization
        
        # Create data for the table
        elements = []
        elements.append(Paragraph(f"Отчет по настройке оборудования", styles['Title']))
        elements.append(Paragraph(f"Сотрудник: {user.get_full_name() or user.username}", styles['Normal']))
        elements.append(Paragraph(f"Организация: {organization.name}", styles['Normal']))
        elements.append(Paragraph(f"Дата отчета: {timezone.now().strftime('%d.%m.%Y')}", styles['Normal']))
        
        # Group by measurement type
        measurement_types = MeasurementType.objects.filter(
            equipment_records__in=records
        ).distinct()
        
        for m_type in measurement_types:
            elements.append(Paragraph(f"\n{m_type.name}", styles['Heading2']))
            
            type_records = records.filter(measurement_type=m_type)
            
            # Create table data
            data = [['Наименование', 'Тип прибора', 'Номер прибора', 'Количество', 'Техника', 'Статус', 'Примечание']]
            
            for record in type_records:
                data.append([
                    record.name,
                    record.device_type,
                    record.serial_number or '',
                    str(record.quantity),
                    record.tech_name,
                    record.status,
                    record.notes or ''
                ])
            
            # Create the table
            table = Table(data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Add a summary
            elements.append(Paragraph(f"Всего приборов: {type_records.count()}", styles['Normal']))
            elements.append(Paragraph(f"Общее количество: {sum(r.quantity for r in type_records)}", styles['Normal']))
        
        # Generate the PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename=f'report_{user.username}_{organization.name}.pdf')
    
    @action(detail=False, methods=['POST'])
    def generate_organization_report(self, request):
        """Generate PDF report for an entire organization"""
        organization_id = request.data.get('organization_id')
        
        if not organization_id:
            return Response({'detail': 'Organization ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get all records for this organization
        records = EquipmentRecord.objects.filter(organization_id=organization_id)
        
        if not records:
            return Response({'detail': 'No records found for this organization'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Create a PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Get organization info
        organization = records.first().organization
        
        # Create data for the report
        elements = []
        elements.append(Paragraph(f"Отчет по настройке оборудования", styles['Title']))
        elements.append(Paragraph(f"Организация: {organization.name}", styles['Normal']))
        elements.append(Paragraph(f"Дата отчета: {timezone.now().strftime('%d.%m.%Y')}", styles['Normal']))
        
        # Group by user first
        users = records.values_list('user', flat=True).distinct()
        
        for user_id in users:
            user_records = records.filter(user_id=user_id)
            user = user_records.first().user
            
            elements.append(Paragraph(f"\nСотрудник: {user.get_full_name() or user.username}", styles['Heading2']))
            
            # Group by measurement type for each user
            for m_type in MeasurementType.objects.filter(equipment_records__in=user_records).distinct():
                elements.append(Paragraph(f"{m_type.name}", styles['Heading3']))
                
                type_records = user_records.filter(measurement_type=m_type)
                
                # Create table data
                data = [['Наименование', 'Тип прибора', 'Номер прибора', 'Количество', 'Техника', 'Статус', 'Примечание']]
                
                for record in type_records:
                    data.append([
                        record.name,
                        record.device_type,
                        record.serial_number or '',
                        str(record.quantity),
                        record.tech_name,
                        record.status,
                        record.notes or ''
                    ])
                
                # Create and style the table
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
                
                # Add a summary
                elements.append(Paragraph(f"Всего приборов: {type_records.count()}", styles['Normal']))
                elements.append(Paragraph(f"Общее количество: {sum(r.quantity for r in type_records)}", styles['Normal']))
        
        # Generate the PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename=f'report_{organization.name}.pdf')
    
    @action(detail=False, methods=['POST'])
    def export_excel(self, request):
        """Export all records for an organization to Excel"""
        organization_id = request.data.get('organization_id')
        
        if not organization_id:
            return Response({'detail': 'Organization ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response({'detail': 'Organization not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Get all records for this organization
        records = EquipmentRecord.objects.filter(organization_id=organization_id)
        
        if not records:
            return Response({'detail': 'No records found for this organization'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Create an Excel file
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Create a DataFrame by measurement type
        measurement_types = MeasurementType.objects.filter(
            equipment_records__in=records
        ).distinct()
        
        for m_type in measurement_types:
            type_records = records.filter(measurement_type=m_type)
            
            # Create a DataFrame for this measurement type
            data = []
            for record in type_records:
                data.append({
                    'Наименование': record.name,
                    'Тип прибора': record.device_type,
                    'Номер прибора': record.serial_number or '',
                    'Количество': record.quantity,
                    'Техника': record.tech_name,
                    'Статус': record.status,
                    'Примечание': record.notes or '',
                    'Сотрудник': record.user.get_full_name() or record.user.username
                })
            
            if data:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=m_type.name[:31], index=False)  # Excel limits sheet names to 31 chars
                
                # Format the sheet
                worksheet = writer.sheets[m_type.name[:31]]
                worksheet.set_column('A:G', 18)  # Set column width
        
        # Save the Excel file
        writer.save()
        output.seek(0)
        
        # Close the organization after generating the Excel
        organization.is_closed = True
        organization.save()
        
        return FileResponse(output, as_attachment=True, filename=f'equipment_{organization.name}.xlsx')

def autocomplete_name(request):
    q = request.GET.get('term', '')
    results = list(EquipmentRecord.objects.filter(name__icontains=q).values_list('name', flat=True).distinct()[:10])
    return JsonResponse(results, safe=False)

def autocomplete_device_type(request):
    q = request.GET.get('term', '')
    results = list(EquipmentRecord.objects.filter(device_type__icontains=q).values_list('device_type', flat=True).distinct()[:10])
    return JsonResponse(results, safe=False)

def autocomplete_tech_name(request):
    q = request.GET.get('term', '')
    results = list(EquipmentRecord.objects.filter(tech_name__icontains=q).values_list('tech_name', flat=True).distinct()[:10])
    return JsonResponse(results, safe=False)

def autocomplete_notes(request):
    q = request.GET.get('term', '')
    results = list(EquipmentRecord.objects.exclude(notes__isnull=True).exclude(notes__exact='').filter(notes__icontains=q).values_list('notes', flat=True).distinct()[:10])
    return JsonResponse(results, safe=False)