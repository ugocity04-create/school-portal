"""
  Verifies user login credentials and sends user role data directly to React frontend 
"""
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

class LoginAPIView(APIView):
  permission_classes = [AllowAny]
  
  def post(self, request):
    username = request.data.get("username")
    password = request.data.get("password")
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
      # Generate secure JWT tokens for session management
      refresh = RefreshToken.for_user(user)
      return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
          "username":user.username,
          "email": user.email,
          "role": user.role,
          "full_name": user.get_full_name()
        }
      }, status=status.HTTP_200_OK)
    
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)