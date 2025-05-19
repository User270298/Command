from rest_framework import serializers
from .models import MeasurementType, EquipmentRecord
from users.serializers import UserSerializer

class MeasurementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = ['id', 'name']
        read_only_fields = ['id']

class EquipmentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentRecord
        fields = [
            'id', 'organization', 'measurement_type', 
            'name', 'device_type', 'serial_number', 'quantity', 
            'tech_name', 'status', 'notes', 'date_created'
        ]
        read_only_fields = ['id', 'date_created']
        extra_kwargs = {
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
            'serial_number': {'required': False, 'allow_blank': True, 'allow_null': True}
        }
    
    def validate(self, data):
        # Validate organization
        if not data.get('organization'):
            raise serializers.ValidationError({'organization': 'Организация обязательна'})
            
        # Validate measurement type
        if not data.get('measurement_type'):
            raise serializers.ValidationError({'measurement_type': 'Тип измерения обязателен'})
            
        # Validate name
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'Наименование обязательно'})
            
        # Validate device type
        if not data.get('device_type'):
            raise serializers.ValidationError({'device_type': 'Тип прибора обязателен'})
            
        # Validate quantity
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError({'quantity': 'Количество должно быть больше 0'})
            
        # Validate tech name
        if not data.get('tech_name'):
            raise serializers.ValidationError({'tech_name': 'Техническое наименование обязательно'})
            
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        try:
            # Check if user has permission to create records for this organization
            organization = validated_data['organization']
            if not user.is_senior and user not in organization.trip.members.all() and user != organization.trip.senior:
                raise serializers.ValidationError('У вас нет прав для создания записей в этой организации')
                
            return EquipmentRecord.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError(f'Ошибка при создании записи: {str(e)}')
    
    def update(self, instance, validated_data):
        try:
            # Check if user has permission to update this record
            user = self.context['request'].user
            if not user.is_senior and instance.user != user:
                raise serializers.ValidationError('У вас нет прав для редактирования этой записи')
                
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            raise serializers.ValidationError(f'Ошибка при обновлении записи: {str(e)}')

class EquipmentRecordDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    measurement_type = MeasurementTypeSerializer(read_only=True)
    
    class Meta:
        model = EquipmentRecord
        fields = [
            'id', 'user', 'organization', 'measurement_type', 
            'name', 'device_type', 'serial_number', 'quantity', 
            'tech_name', 'status', 'notes', 'date_created'
        ]
        read_only_fields = ['id', 'user', 'date_created'] 