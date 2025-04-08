from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import BusinessTrip, Organization
from .serializers import (
    BusinessTripSerializer, BusinessTripDetailSerializer, BusinessTripCreateSerializer,
    OrganizationSerializer, OrganizationDetailSerializer
)
from django.utils import timezone

# Create your views here.

class IsSeniorPermission(permissions.BasePermission):
    """Permission to only allow seniors to do certain actions"""
    def has_permission(self, request, view):
        if view.action in ['create', 'update', 'partial_update', 'destroy', 'close_trip', 'close_organization']:
            return request.user.is_senior
        return True

class BusinessTripViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessTripSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeniorPermission]
    
    def get_queryset(self):
        user = self.request.user
        # Senior sees all trips they lead, members see trips they are part of
        return BusinessTrip.objects.filter(
            Q(senior=user) | Q(members=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BusinessTripCreateSerializer
        if self.action in ['retrieve', 'active_trip']:
            return BusinessTripDetailSerializer
        return BusinessTripSerializer
    
    @action(detail=True, methods=['POST'])
    def close_trip(self, request, pk=None):
        """Close a business trip (mark end date)"""
        trip = self.get_object()
        trip.end_date = timezone.now().date()
        trip.save()
        return Response({'status': 'trip closed'})
    
    @action(detail=False, methods=['GET'])
    def active_trip(self, request):
        """Get active trip for current user"""
        user = request.user
        try:
            trip = BusinessTrip.objects.filter(
                Q(members=user),
                end_date=None
            ).distinct().first()
            
            if not trip:
                return Response({'detail': 'No active trip found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = BusinessTripDetailSerializer(trip)
            return Response(serializer.data)
        except BusinessTrip.DoesNotExist:
            return Response({'detail': 'No active trip found'}, status=status.HTTP_404_NOT_FOUND)

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeniorPermission]
    
    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(
            Q(trip__senior=user) | Q(trip__members=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationSerializer
    
    @action(detail=True, methods=['POST'])
    def close_organization(self, request, pk=None):
        """Close an organization and mark it as completed"""
        organization = self.get_object()
        organization.is_closed = True
        organization.save()
        return Response({'status': 'organization closed'})
