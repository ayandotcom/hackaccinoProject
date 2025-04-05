import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'services/auth_service.dart';

class TrianglePage extends StatelessWidget {
  final _authService = AuthService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        flexibleSpace: Center(
        child: Text(
          'TRIANGLE POSE',
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
            // Display the image with adjusted size
            SizedBox(height: 200),
            Flexible(
              child: Image.asset(
                'assets/img_triangle_pose.jpg', // Ensure the path is correct
                fit: BoxFit.contain, // This scales the image to fit within its bounds
                height: 250, // Set a fixed height or remove this to scale dynamically
              ),
            ),
            
            SizedBox(height: 20), // Space between image and button

            // Display the Start button
            ElevatedButton(
              onPressed: () {
                _runTrianglePoseScript();
              },
              child: Text(
                'Start',
                style: TextStyle(
                    fontWeight: FontWeight.bold, // Set text to bold
                    fontSize: 18,
                  ),
                ),
               style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white, // Set button background to white
                  foregroundColor: Colors.black, // Set button text color to black
                  padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                  
                ),
            ),
          ],
        ),
        ),
      ),
    );
  }

  // Function to run the Triangle_pose.py script
  void _runTrianglePoseScript() async {
    try {
      final response = await _authService.authenticatedGet('http://localhost:5000/triangle_pose');
      
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
