from rest_framework import serializers
from .models import BusinessTrip, Organization
from users.serializers import UserSerializer
from django.db.models import Q

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'trip', 'created_date', 'is_closed']
        read_only_fields = ['id', 'created_date']

class OrganizationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'trip', 'created_date', 'is_closed']
        read_only_fields = ['id', 'created_date']

class BusinessTripSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessTrip
        fields = ['id', 'name', 'senior', 'members', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['id', 'start_date', 'is_active']
    
    def get_is_active(self, obj):
        return obj.is_active()

class BusinessTripDetailSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    senior = UserSerializer(read_only=True)
    organizations = OrganizationSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessTrip
        fields = ['id', 'name', 'senior', 'members', 'start_date', 'end_date', 'is_active', 'organizations']
        read_only_fields = ['id', 'start_date', 'is_active']
    
    def get_is_active(self, obj):
        return obj.is_active()

class BusinessTripCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=BusinessTrip.get_available_users(),
        required=False
    )
    organizations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    city = serializers.CharField(required=True)
    
    class Meta:
        model = BusinessTrip
        fields = ['name', 'city', 'members', 'organizations']
    
    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        organizations_data = validated_data.pop('organizations', [])
        senior = self.context['request'].user
        
        # Создаем командировку
        business_trip = BusinessTrip.objects.create(
            senior=senior,
            **validated_data
        )
        
        # Добавляем участников и обновляем их статусы
        for member in members_data:
            business_trip.members.add(member)
            member.status = 'occupied'
            member.save()
        
        # Добавляем старшего как участника
        business_trip.members.add(senior)
        senior.status = 'occupied'
        senior.save()
        
        # Создаем организации
        for org_name in organizations_data:
            Organization.objects.create(
                name=org_name,
                trip=business_trip
            )
        
        return business_trip 