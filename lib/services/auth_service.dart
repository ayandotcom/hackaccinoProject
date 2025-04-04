import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences.dart';

class AuthService {
  static const String baseUrl = 'https://10.81.32.74:5001';  // Update with your HTTPS URL
  static const String tokenKey = 'auth_token';
  
  static Future<String?> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        headers: {
          'Authorization': 'Basic ${base64Encode(utf8.encode('$username:$password'))}',
        },
      );

      if (response.statusCode == 200) {
        final token = jsonDecode(response.body)['token'];
        await _saveToken(token);
        return token;
      }
      return null;
    } catch (e) {
      print('Login error: $e');
      return null;
    }
  }

  static Future<void> logout() async {
    await _removeToken();
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(tokenKey);
  }

  static Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(tokenKey, token);
  }

  static Future<void> _removeToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(tokenKey);
  }

  static Future<Map<String, String>> getAuthHeaders() async {
    final token = await getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // Secure HTTP client for making authenticated requests
  static Future<http.Response> authenticatedGet(String endpoint) async {
    final headers = await getAuthHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
    );
    
    if (response.statusCode == 401) {
      // Token expired or invalid
      await logout();
      throw Exception('Authentication required');
    }
    
    return response;
  }

  static Future<http.Response> authenticatedPost(String endpoint, {Map<String, dynamic>? body}) async {
    final headers = await getAuthHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
    
    if (response.statusCode == 401) {
      await logout();
      throw Exception('Authentication required');
    }
    
    return response;
  }
} 