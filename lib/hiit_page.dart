import 'package:flutter/material.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';
import 'package:http/http.dart' as http;
import 'dart:async';


class HIITPage extends StatefulWidget {
   @override
   _HIITPageState createState() => _HIITPageState();
 }


class _HIITPageState extends State<HIITPage> {
  late final YoutubePlayerController _controller;
  bool _isLoading = false;
  String _errorMessage = '';
  String _exerciseCount = '';
  String _formFeedback = '';
  Timer? _exerciseTimer;
  bool _isExercising = false;

  // Video IDs and exercise types
  final List<Map<String, String>> exercises = [
    {"id": "XPU9K9QM7ME", "type": "pushups"},
    {"id": "VtOYc6j5c", "type": "squats"},
    {"id": "vUnqwqqI", "type": "plank"},
    {"id": "op9kVnSso6Q", "type": "tree_pose"},
    {"id": "hHdD5Ksdnmk", "type": "triangle_pose"},
    {"id": "_l3ySVKYVJ8", "type": "yoga"}
  ];
  int currentVideoIndex = 0;

  @override
  void initState() {
    super.initState();
    _controller = YoutubePlayerController(
      params: YoutubePlayerParams(
        showControls: true,
        showFullscreenButton: true,
        strictRelatedVideos: true,
        enableJavaScript: true,
        playsInline: false,
        showVideoAnnotations: false,
      ),
    );
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      await _controller.loadVideoById(videoId: exercises[currentVideoIndex]["id"]!);
    } catch (e) {
      _setError('Failed to load video: $e');
    }
  }

  void _setError(String message) {
    setState(() {
      _errorMessage = message;
    });
  }

  void _startVideo() async {
    // Start the video first
    _controller.playVideo();

    // Then send the request to start the workout
    await _sendStartWorkoutRequest();
  }

  void _stopVideo() {
    _controller.pauseVideo();
  }

  void _nextVideo() {
    if (currentVideoIndex < exercises.length - 1) {
      currentVideoIndex++;
    } else {
      _showWorkoutCompletedDialog();
      return; // Prevent loading the next video if workout is completed
    }
    _initializeVideo();
    // Don't start the video immediately here, wait for user to press start
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,  // Prevent dismissing by tapping outside
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed all exercises.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();  // Pop the dialog
                Navigator.of(context).maybePop();  // Safely try to pop the page
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendStartWorkoutRequest() async {
    String exerciseType = exercises[currentVideoIndex]["type"]!;
    String url = 'http://localhost:5001/$exerciseType';

    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        print('Workout started successfully: $exerciseType');
      } else {
        print('Failed to start workout: ${response.body}');
      }
    } catch (error) {
      print('Error sending request: $error');
    }
  }

  @override
  void dispose() {
    _controller.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('High Interval Strength Training Workouts'),
        backgroundColor: Color.fromARGB(255, 77, 0, 80),
      ),
      body: Container(
        color: Colors.black,
        child: Center(
          child: Column(
            children: [
              Expanded(
                child: Container(
                  padding: EdgeInsets.all(16),
                  child: SizedBox(
                    width: MediaQuery.of(context).size.width * 0.5,
                    height: MediaQuery.of(context).size.height * 0.6,
                    child: YoutubePlayer(
                      controller: _controller,
                      aspectRatio: 16 / 9,
                    ),
                  ),
                ),
              ),
              SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton(
                    onPressed: _startVideo,
                    child: Text('Start'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black,
                      padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                    ),
                  ),
                  SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _stopVideo,
                    child: Text('Stop'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black,
                      padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                    ),
                  ),
                  SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _nextVideo,
                    child: Text('Next'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black,
                      padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 20),
              if (_errorMessage.isNotEmpty)
                Text(
                  _errorMessage,
                  style: TextStyle(color: Colors.red),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

