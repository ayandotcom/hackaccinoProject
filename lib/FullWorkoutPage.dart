import 'package:flutter/material.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';

class FullWorkoutPage extends StatefulWidget {
  @override
  _FullWorkoutPageState createState() => _FullWorkoutPageState();
}

class _FullWorkoutPageState extends State<FullWorkoutPage> {
  String message = "You have to do 10 Jumping Jacks, 10 Pushups, 10 Squats";
  bool isWorkoutStarted = false;
  bool isLoading = false;
  String currentExercise = "";
  int currentReps = 0;

  @override
  void initState() {
    super.initState();
    _startWorkoutSequence();
  }

  void _startWorkoutSequence() {
    Timer(Duration(seconds: 2), () {
      setState(() {
        message = "Get ready to start your workout!";
      });
      Timer(Duration(seconds: 2), () {
        setState(() {
          isWorkoutStarted = true;
          message = "Starting exercises...";
        });
        executeExercises();
      });
    });
  }

  Future<void> executeExercises() async {
    setState(() {
      isLoading = true;
    });

    try {
      // Jumping Jacks
      setState(() {
        currentExercise = "Jumping Jacks";
        message = "Starting Jumping Jacks...";
      });

      var response = await http.get(Uri.parse('http://localhost:5001/jumpingjacks'));
      var data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        setState(() {
          message = "Doing Jumping Jacks: ${data['result'] ?? 'In progress...'}";
        });
        await Future.delayed(Duration(seconds: 3));
      } else {
        setState(() {
          message = "Error with Jumping Jacks: ${data['error'] ?? 'Unknown error'}";
        });
        await Future.delayed(Duration(seconds: 2));
      }

      // Pushups
      setState(() {
        currentExercise = "Pushups";
        message = "Starting Pushups...";
      });

      response = await http.get(Uri.parse('http://localhost:5001/pushups'));
      data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        setState(() {
          message = "Doing Pushups: ${data['result'] ?? 'In progress...'}";
        });
        await Future.delayed(Duration(seconds: 3));
      } else {
        setState(() {
          message = "Error with Pushups: ${data['error'] ?? 'Unknown error'}";
        });
        await Future.delayed(Duration(seconds: 2));
      }

      // Squats
      setState(() {
        currentExercise = "Squats";
        message = "Starting Squats...";
      });

      response = await http.get(Uri.parse('http://localhost:5001/squats'));
      data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        setState(() {
          message = "Doing Squats: ${data['result'] ?? 'In progress...'}";
        });
        await Future.delayed(Duration(seconds: 3));
      } else {
        setState(() {
          message = "Error with Squats: ${data['error'] ?? 'Unknown error'}";
        });
        await Future.delayed(Duration(seconds: 2));
      }

      // Workout completed
      setState(() {
        message = "Workout completed!";
        currentExercise = "";
      });
      
      // Show completion dialog
      _showWorkoutCompletedDialog();

    } catch (e) {
      setState(() {
        message = "Error during workout: $e";
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed all exercises.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();  // Pop dialog
                Navigator.of(context).maybePop();  // Try to pop page
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        flexibleSpace: Center(
          child: Text(
            'FULL BODY WORKOUT',
            style: TextStyle(
              color: Colors.white,
              letterSpacing: 1.5,
              fontWeight: FontWeight.w600, 
              fontSize: 28,
            ),
          ),
        ),
        backgroundColor: Color.fromARGB(255, 77, 0, 80),
      ),
      body: Container(
        color: Colors.black,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isLoading) 
                CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              SizedBox(height: 20),
              if (currentExercise.isNotEmpty)
                Text(
                  currentExercise,
                  style: TextStyle(
                    fontSize: 28,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              SizedBox(height: 20),
              Text(
                message,
                style: TextStyle(
                  fontSize: 24,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

