import 'package:flutter/material.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';
import 'dart:convert';
import 'services/auth_service.dart';

class CardioPage extends StatefulWidget {
  @override
  _CardioPageState createState() => _CardioPageState();
}

class _CardioPageState extends State<CardioPage> {
  final _controller = YoutubePlayerController();
  bool _isLoading = false;
  String _errorMessage = '';

  // Video IDs
  final List<String> videoIds = ["XPU9K9QM7ME", "auBLPXO8Fww", "L8fvypPrzzs", "S7HEm-fd534"];
  int currentVideoIndex = 0;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      await _controller.loadVideoById(videoId: videoIds[currentVideoIndex]);
    } catch (e) {
      _setError('Failed to load video: $e');
    }
  }

  void _setError(String message) {
    setState(() {
      _errorMessage = message;
    });
  }

  void _clearError() {
    setState(() {
      _errorMessage = '';
    });
  }

  Future<void> _startVideo() async {
    _clearError();
    setState(() => _isLoading = true);

    try {
      // Start the video first
      await _controller.playVideo();

      // Then send the request to start the workout
      await _sendStartWorkoutRequest();
    } catch (e) {
      _setError('Failed to start workout: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _stopVideo() {
    _controller.pauseVideo();
  }

  Future<void> _nextVideo() async {
    if (currentVideoIndex < videoIds.length - 1) {
      setState(() {
        currentVideoIndex++;
      });
      await _initializeVideo();
    } else {
      _showWorkoutCompletedDialog();
    }
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed this exercise.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context); // Pop dialog
                Navigator.pop(context); // Pop CardioPage
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendStartWorkoutRequest() async {
    try {
      final response = await AuthService.authenticatedGet('/jumpingjacks');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('Workout started successfully: ${data['data']}');
      } else if (response.statusCode == 401) {
        // Handle authentication error
        _setError('Authentication required. Please log in again.');
        Navigator.pushReplacementNamed(context, '/login');
      } else if (response.statusCode == 429) {
        _setError('Rate limit exceeded. Please try again later.');
      } else {
        _setError('Failed to start workout: ${response.body}');
      }
    } catch (e) {
      if (e.toString().contains('Authentication required')) {
        Navigator.pushReplacementNamed(context, '/login');
      } else {
        _setError('Error sending request: $e');
      }
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
        title: Text('Cardio Workouts'),
        backgroundColor: Colors.black,
      ),
      body: Container(
        color: Colors.black,
        child: Center(
          child: Column(
            children: [
              if (_errorMessage.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    _errorMessage,
                    style: TextStyle(color: Colors.red),
                  ),
                ),
              Expanded(
                child: Container(
                  width: 300,
                  height: 200,
                  child: YoutubePlayer(
                    controller: _controller,
                    aspectRatio: 16 / 9,
                  ),
                ),
              ),
              SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton(
                    onPressed: _isLoading ? null : _startVideo,
                    child: _isLoading
                        ? CircularProgressIndicator()
                        : Text('Start'),
                  ),
                  SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _stopVideo,
                    child: Text('Stop'),
                  ),
                  SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _nextVideo,
                    child: Text('Next'),
                  ),
                ],
              ),
              SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
