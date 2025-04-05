import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'services/auth_service.dart';

class PlankPage extends StatelessWidget {
  final _authService = AuthService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        flexibleSpace: Center(
        child: Text(
          'PLANK POSE',
           style: TextStyle(
            color: Colors.white,
            letterSpacing: 1.5,
            fontWeight: FontWeight.w600, 
            fontSize: 28,
            ),
        ),
      ),
        backgroundColor: Color.fromARGB(255, 77, 0, 80), // Set AppBar background to black
      ),
      body: Container(
         color: Colors.black, 
         child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            SizedBox(height: 200),
            // Removed the image temporarily
            
            SizedBox(height: 20), // Space between image and button

            // Display the Start button
            ElevatedButton(
              onPressed: () {
                _runPlankPoseScript();
              },
              child: Text(
                'Start',
                style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
               style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                  
                ),
            ),
          ],
        ),
        ),
      ),
    );
  }

  // Function to run the Plank_pose.py script
  void _runPlankPoseScript() async {
    try {
      final response = await _authService.authenticatedGet('http://localhost:5001/plank_pose');
      
      if (response.statusCode == 200) {
        final jsonResponse = jsonDecode(response.body);
        print('STDOUT: ${jsonResponse['stdout']}');
        print('STDERR: ${jsonResponse['stderr']}');
      } else {
        print('Error: ${response.body}');
      }
    } catch (e) {
      print('Error running script: $e');
    }
  }
}
