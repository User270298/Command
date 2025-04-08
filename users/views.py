from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer, CustomTokenObtainPairSerializer
from django.utils import timezone

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['GET'])
    def me(self, request):
        """Get current user info"""
        user = request.user
        
        # Update last login date
        user.last_login_date = timezone.now()
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['GET'])
    def should_relogin(self, request):
        """Check if user should relogin (inactive for more than 5 days)"""
        should_relogin = request.user.should_relogin()
        return Response({'should_relogin': should_relogin})
    
    @action(detail=False, methods=['GET'])
    def team_members(self, request):
        """Get all users for team selection"""
        users = User.objects.all()
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
